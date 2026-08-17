"""
subsidy_matcher.py — Match eligible schemes and estimate benefits.

Purpose
-------
Given a factory that passed eligibility checks, load policy JSON and the
canonical financial-support records in subsidies.json, compute benefit
estimates, deduplicate, and rank by comparable benefit value.

Financial parameters are NEVER duplicated here — they are always read from
subsidies.json via central_policies.json financial_support_reference.

Benefit formulas follow central_policies.json financial_calculation_rules:
- capital_subsidy: min(eligible_cost * rate, cap)
- interest_subvention: eligible_loan * rate (annual, first-year equivalent)
- credit_guarantee: benefit_inr = 0 (financing enabler, not CAPEX cash)
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

from decision_engine.policy.eligibility import (
    STATUS_ELIGIBLE,
    STATUS_CONDITIONALLY_ELIGIBLE,
    STATUS_INSUFFICIENT_DATA,
    STATUS_NOT_ELIGIBLE,
    EligibilitySummary,
    SchemeEligibility,
)
from models.factory import Factory


_PROJECT_ROOT = Path(__file__).resolve().parents[2]
_CENTRAL_POLICIES_PATH = (
    _PROJECT_ROOT / "knowledge-base" / "policies" / "central_policies.json"
)
_STATE_POLICIES_PATH = (
    _PROJECT_ROOT / "knowledge-base" / "policies" / "state_policies.json"
)
_SUBSIDIES_PATH = (
    _PROJECT_ROOT / "knowledge-base" / "finance" / "subsidies.json"
)

# SUB_SIDBI_MSE_GIFT duplicates SUB_MSE_GIFT — never stack both.
_DUPLICATE_SUBSIDY_IDS = {"SUB_SIDBI_MSE_GIFT"}

# State scheme_id → (rate_key path in state JSON, cap_inr, benefit_type)
_TN_SCHEME_CONFIG: dict[str, dict[str, Any]] = {
    "TN_CAPITAL_SUBSIDY": {
        "rate_percent": 25,
        "maximum_inr": 15_000_000,
        "benefit_type": "capital_subsidy",
        "eligible_cost_basis": "project_cost_inr",
        "source": "state_policies.json Tamil Nadu.manufacturing_incentives.capital_subsidy",
    },
    "TN_CLEAN_TECHNOLOGY_SUBSIDY": {
        "rate_percent": 25,
        "maximum_inr": 1_000_000,
        "benefit_type": "capital_subsidy",
        "eligible_cost_basis": "project_cost_inr",
        "source": (
            "state_policies.json Tamil Nadu.manufacturing_incentives."
            "additional_clean_technology_subsidy"
        ),
    },
}


@dataclass
class SchemeBenefit:
    """One scheme with an estimated financial benefit for ranking."""

    scheme_id: str
    display_name: str
    eligibility_status: str
    benefit_type: str
    benefit_inr: float
    capex_reduction_inr: float
    annual_financing_benefit_inr: float
    eligible_cost_inr: float
    calculation_notes: str
    source_ids: list[str] = field(default_factory=list)
    verification_required: bool = False
    financial_support_reference: Optional[str] = None


@dataclass
class SubsidyMatchResult:
    """Ranked eligible schemes with benefit estimates."""

    eligible_schemes: list[SchemeBenefit]
    ineligible_schemes: list[SchemeEligibility]
    insufficient_data_schemes: list[SchemeEligibility]
    estimated_total_benefit_inr: float
    warnings: list[str] = field(default_factory=list)
    # False when multiple schemes are summed — no numeric combined ceiling
    # is documented in the policy KB (see _combined_subsidy_ceiling_status).
    combined_subsidy_ceiling_checked: bool = False
    combined_subsidy_ceiling_note: str = ""


def _load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Policy data file not found: {path}")
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def _param_value(entity: dict[str, Any], key: str) -> Optional[float]:
    params = entity.get("parameters", {})
    entry = params.get(key)
    if not entry:
        return None
    value = entry.get("value")
    if value is None:
        return None
    return float(value)


def _param_source(entity: dict[str, Any], key: str) -> Optional[str]:
    params = entity.get("parameters", {})
    entry = params.get(key)
    if not entry:
        return None
    return entry.get("source_id")


class SubsidyMatcher:
    """
    Loads policy KB files and estimates benefits for eligible schemes.
    """

    def __init__(
        self,
        central_path: Optional[Path] = None,
        state_path: Optional[Path] = None,
        subsidies_path: Optional[Path] = None,
    ) -> None:
        self._central = _load_json(central_path or _CENTRAL_POLICIES_PATH)
        self._state = _load_json(state_path or _STATE_POLICIES_PATH)
        self._subsidies = _load_json(subsidies_path or _SUBSIDIES_PATH)
        self._entities = self._subsidies.get("entities", {})
        self._policies = self._central.get("policies", {})

    def _combined_subsidy_ceiling_status(
        self,
        eligible_count: int,
    ) -> tuple[bool, str]:
        """
        Report whether estimated_total_benefit_inr was checked against a
        documented combined-subsidy ceiling.

        KB source check (central_policies.json, state_policies.json):
        - central_policies.json policy_engine_rules.no_double_counting_rule:
          procedural — do not auto-stack without explicit convergence permission.
        - state_policies.json benefit_convergence_rules.same_cost_component:
          procedural — do not claim same cost twice unless stacking permitted.
        - state_policies.json critical_rules.do_not_double_count_central_and_state_benefits:
          procedural flag only.
        - Tamil Nadu manufacturing_incentives.capital_subsidy and
          additional_clean_technology_subsidy: per-scheme rate_percent and
          maximum_inr only; no combined total cap or reduced eligible base
          for the second scheme documented in the KB.

        No numeric combined-subsidy ceiling (% of project cost) or
        machine-checkable TN stacking rule exists in the KB — do not invent one.
        """
        if eligible_count <= 1:
            return (
                True,
                "Single eligible scheme with benefit estimate; "
                "combined-subsidy ceiling check not applicable.",
            )

        note = (
            "estimated_total_benefit_inr sums per-scheme benefit_inr without "
            "applying a combined-subsidy ceiling. The knowledge base documents "
            "procedural convergence rules only "
            "(central_policies.json policy_engine_rules.no_double_counting_rule; "
            "state_policies.json benefit_convergence_rules.same_cost_component) "
            "but no numeric total-subsidy cap and no Tamil Nadu rule defining "
            "whether capital_subsidy and additional_clean_technology_subsidy "
            "may stack on the same eligible plant-and-machinery base. "
            "Do not treat this total as a verified claimable amount."
        )
        return False, note

    def _subsidy_entity(self, ref: str) -> Optional[dict[str, Any]]:
        if ref in _DUPLICATE_SUBSIDY_IDS:
            return None
        return self._entities.get(ref)

    def _eligible_loan_adeetie(self, factory: Factory) -> float:
        """
        Raw data → method → value:
        loan_amount_inr from factory; cap at 75% of project_cost_inr
        (eligibility_rules.json ADEETIE maximum_debt_funding_percent).
        """
        if factory.loan_amount_inr is None:
            return 0.0
        debt_cap = 0.75 * factory.project_cost_inr
        return min(factory.loan_amount_inr, debt_cap)

    def _benefit_adeetie(self, factory: Factory) -> SchemeBenefit:
        ref = self._policies["ADEETIE"]["financial_support_reference"]
        entity = self._subsidy_entity(ref)
        if entity is None:
            raise ValueError(f"Missing subsidy entity {ref}")

        if factory.msme_classification == "medium":
            rate = _param_value(entity, "interest_subvention_medium")
            source = _param_source(entity, "interest_subvention_medium")
        else:
            rate = _param_value(entity, "interest_subvention_micro_small")
            source = _param_source(entity, "interest_subvention_micro_small")

        eligible_loan = self._eligible_loan_adeetie(factory)
        # annual_interest_support = eligible_loan * rate%
        # (central_policies.json financial_calculation_rules.interest_subvention)
        annual_benefit = eligible_loan * (rate or 0.0) / 100.0

        notes = (
            f"eligible_loan = min(loan_amount_inr={factory.loan_amount_inr}, "
            f"0.75 × project_cost_inr={factory.project_cost_inr}) "
            f"= {eligible_loan:.0f}; "
            f"annual_interest_support = {eligible_loan:.0f} × {rate}% "
            f"= {annual_benefit:.0f} INR/year "
            f"(SUB_ADEETIE, not a CAPEX subsidy)."
        )
        return SchemeBenefit(
            scheme_id="ADEETIE",
            display_name=entity.get("display_name", "ADEETIE"),
            eligibility_status=STATUS_ELIGIBLE,
            benefit_type="interest_subvention",
            benefit_inr=annual_benefit,
            capex_reduction_inr=0.0,
            annual_financing_benefit_inr=annual_benefit,
            eligible_cost_inr=eligible_loan,
            calculation_notes=notes,
            source_ids=[source] if source else [],
            financial_support_reference=ref,
        )

    def _benefit_mse_gift(self, factory: Factory) -> SchemeBenefit:
        ref = self._policies["MSE_GIFT"]["financial_support_reference"]
        entity = self._subsidy_entity(ref)
        if entity is None:
            raise ValueError(f"Missing subsidy entity {ref}")

        rate = _param_value(entity, "interest_subvention")
        max_loan = _param_value(entity, "maximum_term_loan")
        source = _param_source(entity, "interest_subvention")

        loan = factory.loan_amount_inr or 0.0
        eligible_loan = min(loan, max_loan or loan)
        annual_benefit = eligible_loan * (rate or 0.0) / 100.0

        notes = (
            f"eligible_loan = min(loan_amount_inr={loan}, "
            f"maximum_term_loan={max_loan}) = {eligible_loan:.0f}; "
            f"annual_interest_support = {eligible_loan:.0f} × {rate}% "
            f"= {annual_benefit:.0f} INR/year (SUB_MSE_GIFT)."
        )
        return SchemeBenefit(
            scheme_id="MSE_GIFT",
            display_name=entity.get("display_name", "MSE-GIFT"),
            eligibility_status=STATUS_CONDITIONALLY_ELIGIBLE,
            benefit_type="interest_subvention",
            benefit_inr=annual_benefit,
            capex_reduction_inr=0.0,
            annual_financing_benefit_inr=annual_benefit,
            eligible_cost_inr=eligible_loan,
            calculation_notes=notes,
            source_ids=[source] if source else [],
            verification_required=True,
            financial_support_reference=ref,
        )

    def _benefit_mse_spice(self, factory: Factory) -> SchemeBenefit:
        ref = self._policies["MSE_SPICE"]["financial_support_reference"]
        entity = self._subsidy_entity(ref)
        if entity is None:
            raise ValueError(f"Missing subsidy entity {ref}")

        rate = _param_value(entity, "capital_subsidy_pct")
        cap = _param_value(entity, "maximum_subsidy")
        source = _param_source(entity, "capital_subsidy_pct")

        eligible_cost = factory.project_cost_inr
        raw = eligible_cost * (rate or 0.0) / 100.0
        benefit = min(raw, cap or raw)

        notes = (
            f"policy_benefit = min(project_cost_inr={eligible_cost:.0f} "
            f"× {rate}%, cap={cap:.0f}) = {benefit:.0f} INR "
            f"(SUB_MSE_SPICE capital subsidy on eligible P&M)."
        )
        return SchemeBenefit(
            scheme_id="MSE_SPICE",
            display_name=entity.get("display_name", "MSE-SPICE"),
            eligibility_status=STATUS_ELIGIBLE,
            benefit_type="capital_subsidy",
            benefit_inr=benefit,
            capex_reduction_inr=benefit,
            annual_financing_benefit_inr=0.0,
            eligible_cost_inr=eligible_cost,
            calculation_notes=notes,
            source_ids=[source] if source else [],
            financial_support_reference=ref,
        )

    def _benefit_zed(self, factory: Factory) -> SchemeBenefit:
        ref = self._policies["ZED"]["financial_support_reference"]
        entity = self._subsidy_entity(ref)
        if entity is None:
            raise ValueError(f"Missing subsidy entity {ref}")

        rate = _param_value(entity, "certification_subsidy_bronze")
        source = _param_source(entity, "certification_subsidy_bronze")
        bronze_param = entity.get("parameters", {}).get(
            "certification_subsidy_bronze", {}
        )
        summary = bronze_param.get("research", {}).get("summary", "")
        # Base cost INR 10,000 is documented in SUB_ZED research.summary
        # (not a separate parameters.value field).
        if "10,000" not in summary and "10000" not in summary:
            raise ValueError(
                "SUB_ZED bronze base cost not found in research.summary"
            )
        base_cost = 10_000.0
        benefit = base_cost * (rate or 0.0) / 100.0

        notes = (
            f"ZED certification support only: {base_cost:.0f} × {rate}% "
            f"= {benefit:.0f} INR — not applied to energy-transition CAPEX "
            f"(central_policies.json ZED.important_limitations)."
        )
        _ = factory
        return SchemeBenefit(
            scheme_id="ZED",
            display_name=entity.get("display_name", "ZED"),
            eligibility_status=STATUS_ELIGIBLE,
            benefit_type="certification_support",
            benefit_inr=benefit,
            capex_reduction_inr=0.0,
            annual_financing_benefit_inr=0.0,
            eligible_cost_inr=base_cost,
            calculation_notes=notes,
            source_ids=[source] if source else [],
            financial_support_reference=ref,
        )

    def _benefit_cgtmse(self, factory: Factory) -> SchemeBenefit:
        ref = self._policies["CGTMSE"]["financial_support_reference"]
        entity = self._subsidy_entity(ref)
        if entity is None:
            raise ValueError(f"Missing subsidy entity {ref}")

        coverage_block = entity.get("parameters", {}).get(
            "guarantee_coverage", {}
        )
        coverage = float(
            coverage_block.get("general", {}).get("coverage_pct", 75)
        )
        source = coverage_block.get("source_id", "SRC_CGTMSE")
        flags = factory.special_category
        if flags:
            if flags.women_owned:
                coverage = float(
                    coverage_block.get("women_entrepreneurs", {}).get(
                        "coverage_pct", 90
                    )
                )
            elif flags.sc_st_owned:
                coverage = float(
                    coverage_block.get("sc_st", {}).get("coverage_pct", 85)
                )
            elif flags.pwd_owned:
                coverage = float(
                    coverage_block.get("pwd", {}).get("coverage_pct", 85)
                )
            elif flags.transgender_owned:
                coverage = float(
                    coverage_block.get("transgender", {}).get(
                        "coverage_pct", 85
                    )
                )

        loan = factory.loan_amount_inr or 0.0
        notes = (
            f"CGTMSE guarantee coverage {coverage}% on eligible loan "
            f"{loan:.0f} INR — credit guarantee, NOT a CAPEX cash subsidy "
            f"(eligibility_rules.json CGTMSE.financial_model_treatment)."
        )
        return SchemeBenefit(
            scheme_id="CGTMSE",
            display_name=entity.get("display_name", "CGTMSE"),
            eligibility_status=STATUS_CONDITIONALLY_ELIGIBLE,
            benefit_type="credit_guarantee",
            benefit_inr=0.0,
            capex_reduction_inr=0.0,
            annual_financing_benefit_inr=0.0,
            eligible_cost_inr=loan,
            calculation_notes=notes,
            source_ids=[source],
            verification_required=True,
            financial_support_reference=ref,
        )

    def _benefit_tn_state(
        self,
        scheme_id: str,
        factory: Factory,
        eligibility: SchemeEligibility,
    ) -> SchemeBenefit:
        cfg = _TN_SCHEME_CONFIG[scheme_id]
        rate = cfg["rate_percent"]
        cap = cfg["maximum_inr"]
        eligible_cost = factory.project_cost_inr
        raw = eligible_cost * rate / 100.0
        benefit = min(raw, cap)

        notes = (
            f"policy_benefit = min({cfg['eligible_cost_basis']}="
            f"{eligible_cost:.0f} × {rate}%, cap={cap:.0f}) "
            f"= {benefit:.0f} INR ({cfg['source']})."
        )
        return SchemeBenefit(
            scheme_id=scheme_id,
            display_name=scheme_id.replace("_", " "),
            eligibility_status=eligibility.status,
            benefit_type=cfg["benefit_type"],
            benefit_inr=benefit,
            capex_reduction_inr=benefit,
            annual_financing_benefit_inr=0.0,
            eligible_cost_inr=eligible_cost,
            calculation_notes=notes,
            source_ids=["state_policies.json"],
            financial_support_reference=None,
        )

    def _build_benefit(
        self,
        scheme_id: str,
        factory: Factory,
        eligibility: SchemeEligibility,
    ) -> Optional[SchemeBenefit]:
        builders = {
            "ADEETIE": self._benefit_adeetie,
            "MSE_GIFT": self._benefit_mse_gift,
            "MSE_SPICE": self._benefit_mse_spice,
            "ZED": self._benefit_zed,
            "CGTMSE": self._benefit_cgtmse,
        }
        if scheme_id in builders:
            benefit = builders[scheme_id](factory)
            benefit.eligibility_status = eligibility.status
            benefit.verification_required = eligibility.verification_required
            return benefit
        if scheme_id in _TN_SCHEME_CONFIG:
            return self._benefit_tn_state(scheme_id, factory, eligibility)
        return None

    def match(
        self,
        factory: Factory,
        eligibility: EligibilitySummary,
    ) -> SubsidyMatchResult:
        """
        Match subsidies for schemes marked eligible or conditionally_eligible.
        Rank by benefit_inr descending.
        """
        eligible_benefits: list[SchemeBenefit] = []
        ineligible: list[SchemeEligibility] = []
        insufficient: list[SchemeEligibility] = []
        warnings: list[str] = list(eligibility.warnings)

        for scheme_id, check in eligibility.schemes.items():
            if check.status == STATUS_NOT_ELIGIBLE:
                ineligible.append(check)
                continue
            if check.status == STATUS_INSUFFICIENT_DATA:
                insufficient.append(check)
                continue
            if check.status not in (
                STATUS_ELIGIBLE,
                STATUS_CONDITIONALLY_ELIGIBLE,
            ):
                continue

            try:
                benefit = self._build_benefit(scheme_id, factory, check)
            except (ValueError, KeyError) as exc:
                warnings.append(
                    f"Could not estimate benefit for {scheme_id}: {exc}"
                )
                insufficient.append(
                    SchemeEligibility(
                        scheme_id=scheme_id,
                        status=STATUS_INSUFFICIENT_DATA,
                        reason=str(exc),
                        verification_required=True,
                    )
                )
                continue

            if benefit is None:
                insufficient.append(check)
                continue
            eligible_benefits.append(benefit)

        # Deduplicate: if MSE-GIFT present, drop SIDBI duplicate (not built)
        ranked = sorted(
            eligible_benefits,
            key=lambda b: (b.benefit_inr, b.scheme_id),
            reverse=True,
        )
        total = sum(b.benefit_inr for b in ranked)
        ceiling_checked, ceiling_note = self._combined_subsidy_ceiling_status(
            len(ranked)
        )
        if not ceiling_checked:
            warnings.append(ceiling_note)

        return SubsidyMatchResult(
            eligible_schemes=ranked,
            ineligible_schemes=ineligible,
            insufficient_data_schemes=insufficient,
            estimated_total_benefit_inr=total,
            warnings=warnings,
            combined_subsidy_ceiling_checked=ceiling_checked,
            combined_subsidy_ceiling_note=ceiling_note,
        )

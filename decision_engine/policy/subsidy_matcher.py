
"""
subsidy_matcher.py — Production subsidy and policy benefit matcher.

Unit 2.6 — Subsidy Matcher
--------------------------

Responsibilities
----------------
Given a validated Factory and the already-computed EligibilitySummary:

* load canonical central/state policy data and financial-support data;
* validate the factory/project/loan inputs used by benefit calculations;
* resolve financial-support records through central policy references;
* calculate eligible capital subsidies, interest subvention, credit guarantees,
  margin money, certification reimbursement, technical support and related
  policy benefits where the repository data supports them;
* never treat interest support or credit guarantees as CAPEX reductions;
* never hard-code central financial-support percentages that are already stored
  in subsidies.json;
* evaluate state incentives from state_policies.json rather than silently
  assuming that a state incentive exists;
* apply explicit anti-double-counting and convergence checks;
* rank supported benefits using benefit size, eligibility confidence,
  verification burden and policy relevance;
* preserve auditable calculation notes and source identifiers;
* return the stable SubsidyMatchResult contract consumed by policy_engine.py.

Architectural contract
----------------------
The policy layer is intentionally split:

    Factory
        |
        v
    EligibilityChecker
        |
        v
    SubsidyMatcher
        |
        v
    PolicyEngine / API / recommendation layers

Eligibility is authoritative in eligibility.py. This file does not reimplement
scheme eligibility rules; it consumes the EligibilitySummary produced by the
checker and uses policy/subsidy JSON only for calculations and policy metadata.

Financial-support ownership
---------------------------
subsidies.json is the canonical source for central scheme financial parameters.
central_policies.json provides scheme applicability and the reference key.
state_policies.json is the canonical source for state incentive definitions.

No external web request is made by this module. Source documents and research
notes are evidence used to curate the JSON knowledge base; runtime calculation
depends only on versioned repository data.

Important financial semantics
-----------------------------
* Interest subvention reduces annual/effective financing cost only.
* Capital subsidy reduces eligible CAPEX only.
* Credit guarantees reduce financing risk / collateral friction and have a
  zero direct cash benefit unless a separate, documented monetary benefit is
  explicitly defined.
* Margin money subsidy is a financing contribution and is represented
  separately from the capital cost calculation.
* Certification reimbursement is limited to the documented certification/
  testing/handholding expense base and is not applied to the whole project
  CAPEX.
* Technical assistance is represented as a non-CAPEX support item unless the
  canonical subsidy record defines a reimbursable monetary amount.
"""
from __future__ import annotations

import json
import math
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Optional

from decision_engine.policy.eligibility import (
    STATUS_CONDITIONALLY_ELIGIBLE,
    STATUS_ELIGIBLE,
    STATUS_INSUFFICIENT_DATA,
    STATUS_NOT_ELIGIBLE,
    EligibilitySummary,
    SchemeEligibility,
)
from models.factory import Factory


_PROJECT_ROOT = Path(__file__).resolve().parents[2]

_CENTRAL_POLICIES_PATH = (
    _PROJECT_ROOT
    / "knowledge-base"
    / "policies"
    / "central_policies.json"
)
_STATE_POLICIES_PATH = (
    _PROJECT_ROOT
    / "knowledge-base"
    / "policies"
    / "state_policies.json"
)
_SUBSIDIES_PATH = (
    _PROJECT_ROOT
    / "knowledge-base"
    / "finance"
    / "subsidies.json"
)

# This duplicate financial-support record is intentionally excluded because
# MSE-GIFT is already represented by SUB_MSE_GIFT in the canonical records.
_DUPLICATE_SUBSIDY_IDS = {
    "SUB_SIDBI_MSE_GIFT",
}

# Eligibility can return a state scheme id without a central financial-support
# reference. State policy calculation is therefore metadata-driven from
# state_policies.json. The entries below are only internal scheme descriptors:
# rates and caps are resolved from the state policy tree at runtime.
_STATE_SCHEME_DESCRIPTORS: dict[str, dict[str, str]] = {
    "TN_CAPITAL_SUBSIDY": {
        "state": "Tamil Nadu",
        "path": "states.Tamil Nadu.manufacturing_incentives.capital_subsidy",
        "benefit_type": "capital_subsidy",
        "display_name": "Tamil Nadu Capital Subsidy",
        "cost_field": "project_cost_inr",
    },
    "TN_CLEAN_TECHNOLOGY_SUBSIDY": {
        "state": "Tamil Nadu",
        "path": (
            "states.Tamil Nadu.manufacturing_incentives."
            "additional_clean_technology_subsidy"
        ),
        "benefit_type": "capital_subsidy",
        "display_name": "Tamil Nadu Clean Technology Subsidy",
        "cost_field": "project_cost_inr",
    },
}

STACK_GROUPS: dict[str, str] = {
    "ADEETIE": "financing_interest_support",
    "MSE_GIFT": "financing_interest_support",
    "MSE_SPICE": "capital_subsidy_same_cost",
    "ZED": "certification_support",
    "CGTMSE": "credit_guarantee",
    "PMEGP": "new_enterprise_margin_money",
    "TN_CAPITAL_SUBSIDY": "state_capital_subsidy",
    "TN_CLEAN_TECHNOLOGY_SUBSIDY": "state_capital_subsidy",
    "CLCSS": "capital_subsidy_same_cost",
}


@dataclass(frozen=True)
class CalculationResult:
    """Detailed output of one financial-support calculation.

    Attributes
    ----------
    gross_benefit_inr:
        Raw monetary benefit before any scheme-specific cap is applied.
    capped_benefit_inr:
        Final benefit after applying the scheme's documented monetary cap.
    eligible_base_inr:
        Monetary base on which the scheme formula is applied.
    rate_percent:
        Rate used by the calculation, when applicable.
    cap_inr:
        Scheme-specific cap, when applicable.
    benefit_type:
        Financial treatment category.
    reduces_capex:
        Whether the amount can directly reduce project CAPEX.
    annual_financing_benefit_inr:
        Annual financing benefit, used for interest subvention.
    guarantee_coverage_inr:
        Notional loan amount covered by a guarantee. This is not cash.
    margin_money_inr:
        Financing contribution, where supported.
    reimbursement_inr:
        Expense reimbursement, where supported.
    technical_assistance_inr:
        Monetary technical-assistance value, where explicitly documented.
    notes:
        Human-readable audit trail.
    source_ids:
        Source identifiers from the canonical data.
    """

    gross_benefit_inr: float = 0.0
    capped_benefit_inr: float = 0.0
    eligible_base_inr: float = 0.0
    rate_percent: Optional[float] = None
    cap_inr: Optional[float] = None
    benefit_type: str = "unknown"
    reduces_capex: bool = False
    annual_financing_benefit_inr: float = 0.0
    guarantee_coverage_inr: float = 0.0
    margin_money_inr: float = 0.0
    reimbursement_inr: float = 0.0
    technical_assistance_inr: float = 0.0
    notes: str = ""
    source_ids: list[str] = field(default_factory=list)


@dataclass
class SchemeBenefit:
    """Calculated benefit record for one policy scheme."""

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

    # Extended Unit 2.6 output fields.
    guarantee_coverage_inr: float = 0.0
    guarantee_coverage_percent: Optional[float] = None
    margin_money_inr: float = 0.0
    certification_reimbursement_inr: float = 0.0
    technical_assistance_inr: float = 0.0
    policy_relevance_score: float = 0.0
    eligibility_confidence_score: float = 0.0
    verification_burden_score: float = 0.0
    ranking_score: float = 0.0
    stackable: bool = False
    stack_group: Optional[str] = None


@dataclass
class SubsidyMatchResult:
    """Complete result returned by :meth:`SubsidyMatcher.match`."""

    eligible_schemes: list[SchemeBenefit]
    ineligible_schemes: list[SchemeEligibility]
    insufficient_data_schemes: list[SchemeEligibility]
    estimated_total_benefit_inr: float

    warnings: list[str] = field(default_factory=list)
    combined_subsidy_ceiling_checked: bool = False
    combined_subsidy_ceiling_note: str = ""
    total_benefit_verified: bool = False

    # Extended Unit 2.6 output.
    total_capex_reduction_inr: float = 0.0
    total_annual_financing_benefit_inr: float = 0.0
    total_guarantee_coverage_inr: float = 0.0
    total_margin_money_inr: float = 0.0
    total_certification_reimbursement_inr: float = 0.0
    total_technical_assistance_inr: float = 0.0
    stack_validation_passed: bool = True
    stack_validation_notes: list[str] = field(default_factory=list)


def _load_json(path: Path) -> dict[str, Any]:
    """Load one JSON knowledge-base file with defensive validation."""
    if not path.exists():
        raise FileNotFoundError(f"Policy data file not found: {path}")

    if not path.is_file():
        raise ValueError(f"Policy data path is not a file: {path}")

    try:
        with path.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"Invalid JSON in policy data file {path}: {exc}"
        ) from exc

    if not isinstance(data, dict):
        raise ValueError(
            f"Expected top-level JSON object in {path}, "
            f"got {type(data).__name__}"
        )

    return data


def _nested_get(
    mapping: dict[str, Any],
    dotted_path: str,
    default: Any = None,
) -> Any:
    """Read a nested mapping value using a dotted path."""
    current: Any = mapping

    for segment in dotted_path.split("."):
        if not isinstance(current, dict) or segment not in current:
            return default
        current = current[segment]

    return current


def _param_entry(
    entity: dict[str, Any],
    key: str,
) -> Optional[dict[str, Any]]:
    """Return a subsidies.json parameter object if present."""
    parameters = entity.get("parameters")
    if not isinstance(parameters, dict):
        return None

    entry = parameters.get(key)
    if not isinstance(entry, dict):
        return None

    return entry


def _param_value(
    entity: dict[str, Any],
    key: str,
) -> Optional[float]:
    """Return a numeric parameter value from one subsidy entity."""
    entry = _param_entry(entity, key)
    if entry is None:
        return None

    value = entry.get("value")
    if value is None:
        return None

    try:
        return float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(
            f"Financial parameter '{key}' must be numeric; "
            f"received {value!r}."
        ) from exc


def _param_source(
    entity: dict[str, Any],
    key: str,
) -> Optional[str]:
    """Return a source identifier attached to one subsidy parameter."""
    entry = _param_entry(entity, key)
    if entry is None:
        return None

    source = entry.get("source_id")
    return str(source) if source else None


def _normalise_state(value: str) -> str:
    """Normalise a state string for policy lookup."""
    return value.strip().lower().replace("_", " ")


def _safe_float(value: Any, default: float = 0.0) -> float:
    """Convert a numeric value to float without accepting NaN/inf."""
    if value is None:
        return default

    try:
        converted = float(value)
    except (TypeError, ValueError):
        return default

    if not math.isfinite(converted):
        return default

    return converted


def _clamp(
    value: float,
    minimum: float = 0.0,
    maximum: float = 1.0,
) -> float:
    """Clamp a score or ratio to a closed interval."""
    return max(minimum, min(maximum, value))


class SubsidyMatcher:
    """Match eligible central and state financial-support schemes.

    Parameters are resolved from the repository knowledge base. Eligibility is
    consumed from ``EligibilityChecker`` and is not recomputed here.

    The matcher is deliberately deterministic: identical Factory and
    EligibilitySummary inputs produce identical ranking and benefit results.

    Parameters
    ----------
    central_path:
        Optional override for central_policies.json, primarily useful for
        isolated tests.
    state_path:
        Optional override for state_policies.json.
    subsidies_path:
        Optional override for subsidies.json.
    """

    def __init__(
        self,
        central_path: Optional[Path] = None,
        state_path: Optional[Path] = None,
        subsidies_path: Optional[Path] = None,
    ) -> None:
        self._central = _load_json(
            central_path or _CENTRAL_POLICIES_PATH
        )
        self._state = _load_json(
            state_path or _STATE_POLICIES_PATH
        )
        self._subsidies = _load_json(
            subsidies_path or _SUBSIDIES_PATH
        )

        entities = self._subsidies.get("entities", {})
        policies = self._central.get("policies", {})
        states = self._state.get("states", {})

        if not isinstance(entities, dict):
            raise ValueError(
                "subsidies.json must contain an 'entities' object."
            )

        if not isinstance(policies, dict):
            raise ValueError(
                "central_policies.json must contain a 'policies' object."
            )

        if not isinstance(states, dict):
            raise ValueError(
                "state_policies.json must contain a 'states' object."
            )

        self._entities: dict[str, dict[str, Any]] = {
            str(key): value
            for key, value in entities.items()
            if isinstance(value, dict)
        }
        self._policies: dict[str, dict[str, Any]] = {
            str(key): value
            for key, value in policies.items()
            if isinstance(value, dict)
        }
        self._states: dict[str, dict[str, Any]] = {
            str(key): value
            for key, value in states.items()
            if isinstance(value, dict)
        }

    # ------------------------------------------------------------------
    # Input validation
    # ------------------------------------------------------------------

    @staticmethod
    def _validate_factory(factory: Factory) -> list[str]:
        """Validate all monetary and percentage inputs used downstream.

        The Factory model already validates basic domains. This method adds
        calculation-specific invariants that prevent silent financial errors.
        """
        errors: list[str] = []

        monetary_fields = (
            "budget_inr",
            "annual_turnover_inr",
            "plant_and_machinery_or_equipment_investment_inr",
            "project_cost_inr",
        )

        for field_name in monetary_fields:
            value = getattr(factory, field_name, None)
            if value is None:
                errors.append(f"{field_name} is required.")
                continue

            value_float = _safe_float(value, default=-1.0)
            if value_float < 0:
                errors.append(
                    f"{field_name} must be a non-negative number."
                )

        if factory.loan_amount_inr is not None:
            loan = _safe_float(factory.loan_amount_inr, default=-1.0)
            if loan < 0:
                errors.append(
                    "loan_amount_inr must be non-negative when supplied."
                )

        if factory.project_cost_inr <= 0:
            errors.append("project_cost_inr must be greater than zero.")

        if (
            factory.loan_amount_inr is not None
            and factory.loan_amount_inr > 0
            and factory.loan_amount_inr > factory.project_cost_inr * 2
        ):
            errors.append(
                "loan_amount_inr is implausibly greater than twice project "
                "cost; verify the factory financing input."
            )

        if not factory.state or not factory.state.strip():
            errors.append("state is required for state-policy matching.")

        if not factory.district or not factory.district.strip():
            errors.append(
                "district is required by the factory profile for "
                "location-sensitive policies."
            )

        return errors

    @staticmethod
    def _validate_project_cost(
        factory: Factory,
        eligible_cost: float,
    ) -> float:
        """Validate and safely normalise an eligible project-cost base."""
        project_cost = _safe_float(factory.project_cost_inr, -1.0)

        if project_cost <= 0:
            raise ValueError(
                "project_cost_inr must be greater than zero."
            )

        if eligible_cost < 0:
            raise ValueError(
                "eligible project cost cannot be negative."
            )

        return min(project_cost, eligible_cost)

    @staticmethod
    def _validate_loan(
        factory: Factory,
        eligible_loan: float,
    ) -> float:
        """Validate a scheme-specific loan base."""
        if eligible_loan < 0:
            raise ValueError("eligible loan amount cannot be negative.")

        if factory.loan_amount_inr is None:
            return 0.0

        loan = _safe_float(factory.loan_amount_inr, -1.0)

        if loan < 0:
            raise ValueError("loan_amount_inr cannot be negative.")

        return min(loan, eligible_loan)

    @staticmethod
    def _validate_rate(rate: Optional[float]) -> float:
        """Validate a subsidy or subvention percentage."""
        if rate is None:
            raise ValueError(
                "Required financial-support rate is missing "
                "from the canonical policy record."
            )

        rate_float = _safe_float(rate, -1.0)

        if rate_float < 0 or rate_float > 100:
            raise ValueError(
                f"Financial-support rate must be between 0 and 100; "
                f"received {rate_float}."
            )

        return rate_float

    @staticmethod
    def _validate_cap(cap: Optional[float]) -> Optional[float]:
        """Validate an optional monetary cap."""
        if cap is None:
            return None

        cap_float = _safe_float(cap, -1.0)

        if cap_float < 0:
            raise ValueError(
                f"Benefit cap cannot be negative; received {cap_float}."
            )

        return cap_float

    @staticmethod
    def _capital_subsidy_calculation(
        eligible_cost: float,
        rate_percent: float,
        cap_inr: Optional[float],
        source_ids: list[str],
        notes_prefix: str = "",
    ) -> CalculationResult:
        """Calculate a capital subsidy and explicitly mark it as CAPEX-reducing."""
        validated_rate = SubsidyMatcher._validate_rate(rate_percent)
        validated_cap = SubsidyMatcher._validate_cap(cap_inr)

        base = _safe_float(eligible_cost, -1.0)
        if base < 0:
            raise ValueError("Eligible capital-subsidy base cannot be negative.")

        gross = base * validated_rate / 100.0
        capped = (
            min(gross, validated_cap)
            if validated_cap is not None
            else gross
        )

        notes = (
            f"{notes_prefix}"
            f"capital_subsidy = {base:.2f} × "
            f"{validated_rate:.4f}% = {gross:.2f}; "
            f"final = min(gross, cap={validated_cap}) = {capped:.2f}. "
            "This benefit reduces eligible CAPEX."
        )

        return CalculationResult(
            gross_benefit_inr=gross,
            capped_benefit_inr=capped,
            eligible_base_inr=base,
            rate_percent=validated_rate,
            cap_inr=validated_cap,
            benefit_type="capital_subsidy",
            reduces_capex=True,
            notes=notes,
            source_ids=list(source_ids),
        )

    @staticmethod
    def _interest_subvention_calculation(
        eligible_loan: float,
        rate_percent: float,
        cap_inr: Optional[float],
        source_ids: list[str],
        notes_prefix: str = "",
    ) -> CalculationResult:
        """Calculate annual interest support without reducing CAPEX."""
        validated_rate = SubsidyMatcher._validate_rate(rate_percent)
        validated_cap = SubsidyMatcher._validate_cap(cap_inr)

        loan = _safe_float(eligible_loan, -1.0)
        if loan < 0:
            raise ValueError("Eligible loan base cannot be negative.")

        gross = loan * validated_rate / 100.0
        capped = (
            min(gross, validated_cap)
            if validated_cap is not None
            else gross
        )

        notes = (
            f"{notes_prefix}"
            f"annual_interest_support = {loan:.2f} × "
            f"{validated_rate:.4f}% = {gross:.2f}; "
            f"final annual support = min(gross, cap={validated_cap}) "
            f"= {capped:.2f}. "
            "Interest subvention reduces financing cost and MUST NOT "
            "reduce CAPEX."
        )

        return CalculationResult(
            gross_benefit_inr=gross,
            capped_benefit_inr=capped,
            eligible_base_inr=loan,
            rate_percent=validated_rate,
            cap_inr=validated_cap,
            benefit_type="interest_subvention",
            reduces_capex=False,
            annual_financing_benefit_inr=capped,
            notes=notes,
            source_ids=list(source_ids),
        )

    @staticmethod
    def _guarantee_calculation(
        eligible_loan: float,
        coverage_percent: float,
        source_ids: list[str],
        notes_prefix: str = "",
    ) -> CalculationResult:
        """Calculate notional guaranteed loan coverage, not cash benefit."""
        validated_coverage = SubsidyMatcher._validate_rate(
            coverage_percent
        )

        loan = _safe_float(eligible_loan, -1.0)
        if loan < 0:
            raise ValueError("Eligible guarantee loan cannot be negative.")

        guarantee_amount = loan * validated_coverage / 100.0

        notes = (
            f"{notes_prefix}"
            f"guarantee_coverage = {loan:.2f} × "
            f"{validated_coverage:.4f}% = {guarantee_amount:.2f}. "
            "Guarantee coverage is a financing-risk instrument, not "
            "cash subsidy and not CAPEX reduction."
        )

        return CalculationResult(
            gross_benefit_inr=0.0,
            capped_benefit_inr=0.0,
            eligible_base_inr=loan,
            rate_percent=validated_coverage,
            benefit_type="credit_guarantee",
            reduces_capex=False,
            guarantee_coverage_inr=guarantee_amount,
            notes=notes,
            source_ids=list(source_ids),
        )

    @staticmethod
    def _reimbursement_calculation(
        eligible_expense: float,
        rate_percent: float,
        cap_inr: Optional[float],
        source_ids: list[str],
        benefit_type: str,
        notes_prefix: str = "",
    ) -> CalculationResult:
        """Calculate a documented certification/audit reimbursement."""
        validated_rate = SubsidyMatcher._validate_rate(rate_percent)
        validated_cap = SubsidyMatcher._validate_cap(cap_inr)

        expense = _safe_float(eligible_expense, -1.0)
        if expense < 0:
            raise ValueError(
                "Eligible reimbursement expense cannot be negative."
            )

        gross = expense * validated_rate / 100.0
        capped = (
            min(gross, validated_cap)
            if validated_cap is not None
            else gross
        )

        notes = (
            f"{notes_prefix}"
            f"reimbursement = {expense:.2f} × "
            f"{validated_rate:.4f}% = {gross:.2f}; "
            f"final = min(gross, cap={validated_cap}) = {capped:.2f}. "
            "This is reimbursement of a documented eligible expense and "
            "is not a generic reduction of the project's whole CAPEX."
        )

        return CalculationResult(
            gross_benefit_inr=gross,
            capped_benefit_inr=capped,
            eligible_base_inr=expense,
            rate_percent=validated_rate,
            cap_inr=validated_cap,
            benefit_type=benefit_type,
            reduces_capex=False,
            reimbursement_inr=capped,
            notes=notes,
            source_ids=list(source_ids),
        )

    @staticmethod
    def _margin_money_calculation(
        eligible_project_cost: float,
        subsidy_rate_percent: float,
        cap_inr: Optional[float],
        source_ids: list[str],
        notes_prefix: str = "",
    ) -> CalculationResult:
        """Calculate a financing margin-money contribution."""
        validated_rate = SubsidyMatcher._validate_rate(
            subsidy_rate_percent
        )
        validated_cap = SubsidyMatcher._validate_cap(cap_inr)

        project_cost = _safe_float(eligible_project_cost, -1.0)
        if project_cost < 0:
            raise ValueError(
                "Eligible margin-money project cost cannot be negative."
            )

        gross = project_cost * validated_rate / 100.0
        capped = (
            min(gross, validated_cap)
            if validated_cap is not None
            else gross
        )

        notes = (
            f"{notes_prefix}"
            f"margin_money = {project_cost:.2f} × "
            f"{validated_rate:.4f}% = {gross:.2f}; "
            f"final = min(gross, cap={validated_cap}) = {capped:.2f}. "
            "Margin money is a financing contribution and is kept "
            "separate from generic CAPEX subsidy accounting."
        )

        return CalculationResult(
            gross_benefit_inr=gross,
            capped_benefit_inr=capped,
            eligible_base_inr=project_cost,
            rate_percent=validated_rate,
            cap_inr=validated_cap,
            benefit_type="margin_money",
            reduces_capex=False,
            margin_money_inr=capped,
            notes=notes,
            source_ids=list(source_ids),
        )

    # ------------------------------------------------------------------
    # Knowledge-base resolution
    # ------------------------------------------------------------------

    def _subsidy_entity(
        self,
        financial_support_reference: str,
    ) -> Optional[dict[str, Any]]:
        """Resolve a central financial-support record."""
        if financial_support_reference in _DUPLICATE_SUBSIDY_IDS:
            return None

        return self._entities.get(financial_support_reference)

    def _policy(
        self,
        scheme_id: str,
    ) -> dict[str, Any]:
        """Resolve a central policy record or raise a clear data error."""
        policy = self._policies.get(scheme_id)

        if policy is None:
            raise KeyError(
                f"Central policy '{scheme_id}' is missing from "
                "central_policies.json."
            )

        return policy

    def _financial_reference(
        self,
        scheme_id: str,
    ) -> str:
        """Resolve the canonical subsidy entity referenced by a central policy."""
        policy = self._policy(scheme_id)
        reference = policy.get("financial_support_reference")

        if not reference:
            raise KeyError(
                f"Central policy '{scheme_id}' has no "
                "financial_support_reference."
            )

        return str(reference)

    def _resolve_entity_for_scheme(
        self,
        scheme_id: str,
    ) -> tuple[str, dict[str, Any]]:
        """Resolve scheme id → financial-support reference → entity."""
        reference = self._financial_reference(scheme_id)
        entity = self._subsidy_entity(reference)

        if entity is None:
            raise KeyError(
                f"Financial-support entity '{reference}' for scheme "
                f"'{scheme_id}' is unavailable or intentionally "
                "deduplicated."
            )

        return reference, entity

    # ------------------------------------------------------------------
    # Scheme-specific benefit builders
    # ------------------------------------------------------------------

    def _benefit_adeetie(
        self,
        factory: Factory,
        eligibility: SchemeEligibility,
    ) -> SchemeBenefit:
        """Calculate ADEETIE interest support and audit/DPR reimbursement.

        ADEETIE does not reduce project CAPEX. It provides financing relief and
        technical assistance/reimbursement on documented eligible audit/DPR
        costs.
        """
        reference, entity = self._resolve_entity_for_scheme("ADEETIE")

        if factory.msme_classification == "medium":
            rate = _param_value(
                entity,
                "interest_subvention_medium",
            )
            rate_source = _param_source(
                entity,
                "interest_subvention_medium",
            )
            audit_cap = _param_value(
                entity,
                "audit_reimbursement_cap_medium",
            )
            audit_source = _param_source(
                entity,
                "audit_reimbursement_cap_medium",
            )
        else:
            rate = _param_value(
                entity,
                "interest_subvention_micro_small",
            )
            rate_source = _param_source(
                entity,
                "interest_subvention_micro_small",
            )
            audit_cap = _param_value(
                entity,
                "audit_reimbursement_cap_micro_small",
            )
            audit_source = _param_source(
                entity,
                "audit_reimbursement_cap_micro_small",
            )

        rate = self._validate_rate(rate)

        loan = _safe_float(factory.loan_amount_inr, 0.0)
        debt_cap = factory.project_cost_inr * 0.75
        eligible_loan = min(loan, debt_cap)

        loan_result = self._interest_subvention_calculation(
            eligible_loan=eligible_loan,
            rate_percent=rate,
            cap_inr=None,
            source_ids=[
                source
                for source in [rate_source]
                if source
            ],
            notes_prefix=(
                "ADEETIE annual financing benefit. "
            ),
        )

        # The current Factory contract does not contain a separate audit/DPR
        # expense input. Therefore the reimbursement cap can be exposed as
        # available technical support metadata but no fictitious expense is
        # introduced and no reimbursement is claimed in the numeric benefit.
        technical_assistance_note = (
            f"Audit/DPR reimbursement cap available from canonical data: "
            f"INR {audit_cap:.0f}."
            if audit_cap is not None
            else "Audit/DPR reimbursement cap is not available."
        )

        source_ids = [
            source
            for source in [rate_source, audit_source]
            if source
        ]

        notes = (
            f"{loan_result.notes} "
            f"Factory loan={loan:.2f}, 75% project-cost ceiling="
            f"{debt_cap:.2f}. "
            f"{technical_assistance_note} "
            "No audit reimbursement is added because Factory has no "
            "audit/DPR-expense field."
        )

        return SchemeBenefit(
            scheme_id="ADEETIE",
            display_name=entity.get(
                "display_name",
                "ADEETIE",
            ),
            eligibility_status=eligibility.status,
            benefit_type="interest_subvention",
            benefit_inr=loan_result.capped_benefit_inr,
            capex_reduction_inr=0.0,
            annual_financing_benefit_inr=(
                loan_result.annual_financing_benefit_inr
            ),
            eligible_cost_inr=loan_result.eligible_base_inr,
            calculation_notes=notes,
            source_ids=source_ids,
            verification_required=eligibility.verification_required,
            financial_support_reference=reference,
            technical_assistance_inr=0.0,
            policy_relevance_score=1.00,
            eligibility_confidence_score=0.95,
            verification_burden_score=(
                0.25 if not eligibility.verification_required else 0.60
            ),
            stackable=True,
            stack_group=STACK_GROUPS.get("ADEETIE"),
        )

    def _benefit_mse_gift(
        self,
        factory: Factory,
        eligibility: SchemeEligibility,
    ) -> SchemeBenefit:
        """Calculate MSE-GIFT annual interest support.

        Risk-sharing guarantee coverage is exposed separately and is never
        counted as cash benefit.
        """
        reference, entity = self._resolve_entity_for_scheme("MSE_GIFT")

        rate = self._validate_rate(
            _param_value(entity, "interest_subvention")
        )
        max_loan = _param_value(
            entity,
            "maximum_term_loan",
        )

        if max_loan is None:
            raise ValueError(
                "SUB_MSE_GIFT maximum_term_loan is missing."
            )

        loan = _safe_float(factory.loan_amount_inr, 0.0)
        eligible_loan = self._validate_loan(
            factory,
            min(loan, max_loan),
        )

        result = self._interest_subvention_calculation(
            eligible_loan=eligible_loan,
            rate_percent=rate,
            cap_inr=None,
            source_ids=[
                source
                for source in [_param_source(
                    entity,
                    "interest_subvention",
                )]
                if source
            ],
            notes_prefix=(
                "MSE-GIFT annual financing benefit. "
            ),
        )

        risk_sharing = _param_value(
            entity,
            "risk_sharing_guarantee_coverage",
        )

        guarantee_amount = (
            eligible_loan * risk_sharing / 100.0
            if risk_sharing is not None
            else 0.0
        )

        notes = (
            f"{result.notes} "
            f"Maximum term-loan base from subsidies.json="
            f"{max_loan:.2f}. "
            f"Risk-sharing guarantee coverage={risk_sharing}% "
            f"corresponds to notional coverage={guarantee_amount:.2f} "
            "and is not included in benefit_inr or CAPEX reduction."
        )

        return SchemeBenefit(
            scheme_id="MSE_GIFT",
            display_name=entity.get(
                "display_name",
                "MSE-GIFT",
            ),
            eligibility_status=eligibility.status,
            benefit_type="interest_subvention",
            benefit_inr=result.capped_benefit_inr,
            capex_reduction_inr=0.0,
            annual_financing_benefit_inr=(
                result.annual_financing_benefit_inr
            ),
            eligible_cost_inr=result.eligible_base_inr,
            calculation_notes=notes,
            source_ids=[
                source
                for source in [
                    _param_source(entity, "interest_subvention"),
                    _param_source(
                        entity,
                        "risk_sharing_guarantee_coverage",
                    ),
                ]
                if source
            ],
            verification_required=eligibility.verification_required,
            financial_support_reference=reference,
            guarantee_coverage_inr=guarantee_amount,
            guarantee_coverage_percent=risk_sharing,
            policy_relevance_score=1.00,
            eligibility_confidence_score=(
                0.85 if not eligibility.verification_required else 0.70
            ),
            verification_burden_score=0.60,
            stackable=True,
            stack_group=STACK_GROUPS.get("MSE_GIFT"),
        )

    def _benefit_mse_spice(
        self,
        factory: Factory,
        eligibility: SchemeEligibility,
    ) -> SchemeBenefit:
        """Calculate MSE-SPICE capital subsidy from canonical subsidy data."""
        reference, entity = self._resolve_entity_for_scheme("MSE_SPICE")

        rate = self._validate_rate(
            _param_value(entity, "capital_subsidy_pct")
        )
        cap = self._validate_cap(
            _param_value(entity, "maximum_subsidy")
        )
        project_ceiling = _param_value(
            entity,
            "project_cost_ceiling",
        )

        if project_ceiling is None:
            raise ValueError(
                "SUB_MSE_SPICE project_cost_ceiling is missing."
            )

        eligible_project_cost = min(
            self._validate_project_cost(
                factory,
                factory.project_cost_inr,
            ),
            project_ceiling,
        )

        result = self._capital_subsidy_calculation(
            eligible_cost=eligible_project_cost,
            rate_percent=rate,
            cap_inr=cap,
            source_ids=[
                source
                for source in [
                    _param_source(
                        entity,
                        "capital_subsidy_pct",
                    ),
                    _param_source(
                        entity,
                        "maximum_subsidy",
                    ),
                ]
                if source
            ],
            notes_prefix=(
                "MSE-SPICE brownfield circular-economy subsidy. "
            ),
        )

        return SchemeBenefit(
            scheme_id="MSE_SPICE",
            display_name=entity.get(
                "display_name",
                "MSE-SPICE",
            ),
            eligibility_status=eligibility.status,
            benefit_type="capital_subsidy",
            benefit_inr=result.capped_benefit_inr,
            capex_reduction_inr=result.capped_benefit_inr,
            annual_financing_benefit_inr=0.0,
            eligible_cost_inr=result.eligible_base_inr,
            calculation_notes=result.notes,
            source_ids=result.source_ids,
            verification_required=eligibility.verification_required,
            financial_support_reference=reference,
            policy_relevance_score=0.90,
            eligibility_confidence_score=(
                0.95 if not eligibility.verification_required else 0.75
            ),
            verification_burden_score=0.35,
            stackable=False,
            stack_group=STACK_GROUPS.get("MSE_SPICE"),
        )

    def _benefit_zed(
        self,
        factory: Factory,
        eligibility: SchemeEligibility,
    ) -> SchemeBenefit:
        """Calculate only the documented ZED certification support.

        The current Factory contract has no explicit ZED certification-fee
        field. Therefore the canonical base cost mentioned in the subsidy
        record's research metadata is used only when it is explicit and
        auditable. The result is kept separate from project CAPEX.
        """
        reference, entity = self._resolve_entity_for_scheme("ZED")

        bronze = _param_entry(
            entity,
            "certification_subsidy_bronze",
        )
        if bronze is None:
            raise ValueError(
                "SUB_ZED certification_subsidy_bronze is missing."
            )

        rate = self._validate_rate(
            _param_value(entity, "certification_subsidy_bronze")
        )
        source = _param_source(
            entity,
            "certification_subsidy_bronze",
        )

        research = bronze.get("research", {})
        summary = str(research.get("summary", ""))

        if "10,000" in summary:
            base_cost = 10_000.0
        elif "10000" in summary:
            base_cost = 10_000.0
        else:
            # No documented monetary base → do not invent one.
            raise ValueError(
                "SUB_ZED does not expose a machine-readable certification "
                "expense base and its research summary does not contain "
                "the expected INR 10,000 reference."
            )

        result = self._reimbursement_calculation(
            eligible_expense=base_cost,
            rate_percent=rate,
            cap_inr=None,
            source_ids=[source] if source else [],
            benefit_type="certification_support",
            notes_prefix=(
                "ZED certification reimbursement. "
            ),
        )

        notes = (
            f"{result.notes} "
            "Certification support is not applied to the whole "
            "energy-transition project CAPEX."
        )

        _ = factory

        return SchemeBenefit(
            scheme_id="ZED",
            display_name=entity.get(
                "display_name",
                "ZED",
            ),
            eligibility_status=eligibility.status,
            benefit_type="certification_support",
            benefit_inr=result.capped_benefit_inr,
            capex_reduction_inr=0.0,
            annual_financing_benefit_inr=0.0,
            eligible_cost_inr=result.eligible_base_inr,
            calculation_notes=notes,
            source_ids=result.source_ids,
            verification_required=eligibility.verification_required,
            financial_support_reference=reference,
            certification_reimbursement_inr=(
                result.reimbursement_inr
            ),
            policy_relevance_score=0.75,
            eligibility_confidence_score=0.90,
            verification_burden_score=0.35,
            stackable=True,
            stack_group=STACK_GROUPS.get("ZED"),
        )

    def _benefit_cgtmse(
        self,
        factory: Factory,
        eligibility: SchemeEligibility,
    ) -> SchemeBenefit:
        """Calculate CGTMSE guarantee coverage only."""
        reference, entity = self._resolve_entity_for_scheme("CGTMSE")

        guarantee_block = _param_entry(
            entity,
            "guarantee_coverage",
        )
        if guarantee_block is None:
            # Some datasets use a direct parameter per subgroup. If the
            # repository record does not contain the canonical key, surface
            # an explicit insufficient-data error rather than assuming a rate.
            parameters = entity.get("parameters", {})
            if not isinstance(parameters, dict):
                raise ValueError(
                    "SUB_CGTMSE parameters are missing."
                )

            possible_keys = (
                "general_coverage",
                "guarantee_coverage_general",
                "coverage_general",
            )
            for key in possible_keys:
                if key in parameters:
                    guarantee_block = _param_entry(
                        entity,
                        key,
                    )
                    break

        if guarantee_block is None:
            # Fall back only to the schema/policy range when the subsidy
            # record itself is unavailable: this cannot become a numeric
            # benefit, so return an explicit validation error.
            raise ValueError(
                "SUB_CGTMSE does not expose a machine-readable "
                "guarantee_coverage parameter."
            )

        value = guarantee_block.get("value")
        if isinstance(value, (int, float)):
            coverage = float(value)
        elif isinstance(guarantee_block.get("general"), dict) and "coverage_pct" in guarantee_block["general"]:
            coverage = float(guarantee_block["general"]["coverage_pct"])
        else:
            research = guarantee_block.get("research", {})
            summary = str(
                research.get("summary", "")
            )
            coverage = self._extract_first_percentage(
                summary
            )

        if coverage is None:
            raise ValueError(
                "Could not resolve a CGTMSE guarantee coverage percentage "
                "from subsidies.json."
            )

        loan = _safe_float(factory.loan_amount_inr, 0.0)

        max_guarantee = _nested_get(
            self._central,
            "policies.CGTMSE.optimizer_application.maximum_guarantee_coverage",
        )

        # eligibility_rules.json provides the authoritative machine-checkable
        # maximum guarantee-per-borrower amount when present.
        max_guarantee_rule = _nested_get(
            self._load_eligibility_rules(),
            "scheme_rules.CGTMSE.eligibility.maximum_guarantee_coverage_per_borrower_inr",
        )

        candidate_caps = [
            value
            for value in [
                max_guarantee,
                max_guarantee_rule,
            ]
            if isinstance(value, (int, float))
        ]

        guarantee_base = loan
        if candidate_caps:
            guarantee_base = min(
                guarantee_base,
                min(float(value) for value in candidate_caps),
            )

        result = self._guarantee_calculation(
            eligible_loan=guarantee_base,
            coverage_percent=coverage,
            source_ids=[
                source
                for source in [
                    guarantee_block.get("source_id"),
                ]
                if source
            ],
            notes_prefix=(
                "CGTMSE lender guarantee support. "
            ),
        )

        return SchemeBenefit(
            scheme_id="CGTMSE",
            display_name=entity.get(
                "display_name",
                "CGTMSE",
            ),
            eligibility_status=eligibility.status,
            benefit_type="credit_guarantee",
            benefit_inr=0.0,
            capex_reduction_inr=0.0,
            annual_financing_benefit_inr=0.0,
            eligible_cost_inr=result.eligible_base_inr,
            calculation_notes=result.notes,
            source_ids=result.source_ids,
            verification_required=True,
            financial_support_reference=reference,
            guarantee_coverage_inr=result.guarantee_coverage_inr,
            guarantee_coverage_percent=coverage,
            policy_relevance_score=1.00,
            eligibility_confidence_score=0.70,
            verification_burden_score=0.70,
            stackable=True,
            stack_group=STACK_GROUPS.get("CGTMSE"),
        )

    @staticmethod
    def _extract_first_percentage(
        text: str,
    ) -> Optional[float]:
        """Extract a simple percentage from canonical descriptive text."""
        if not text:
            return None

        digits: list[str] = []
        current: list[str] = []

        for char in text:
            if char.isdigit() or char == ".":
                current.append(char)
            elif current:
                digits.append("".join(current))
                current = []

        if current:
            digits.append("".join(current))

        for token in digits:
            try:
                value = float(token)
            except ValueError:
                continue

            if 0 <= value <= 100:
                return value

        return None

    def _load_eligibility_rules(self) -> dict[str, Any]:
        """Load eligibility_rules.json from the repository."""
        path = (
            _PROJECT_ROOT
            / "knowledge-base"
            / "policies"
            / "eligibility_rules.json"
        )
        return _load_json(path)

    def _benefit_pmegp(
        self,
        factory: Factory,
        eligibility: SchemeEligibility,
    ) -> SchemeBenefit:
        """Calculate PMEGP margin money using the eligibility rules.

        PMEGP is a new-micro-enterprise scheme. The exact urban/rural and
        special-category subsidy rate is stored in eligibility_rules.json,
        while the monetary support record is resolved through subsidies.json.
        """
        reference, entity = self._resolve_entity_for_scheme("PMEGP")

        special = factory.special_category
        is_special = bool(
            special
            and (
                special.women_owned
                or special.sc_st_owned
                or special.pwd_owned
                or special.agniveer_owned
                or special.transgender_owned
                or special.north_east_region
                or special.jammu_kashmir
                or special.ladakh
                or special.aspirational_district
                or special.identified_credit_deficient_district
            )
        )

        subsidy_block = entity.get("parameters", {}).get(
            "subsidy_percent",
            {},
        )

        if not isinstance(subsidy_block, dict):
            raise ValueError(
                "SUB_PMEGP subsidy_percent must be an object."
            )

        # PMEGP differentiates rural/urban. Factory has no rurality field.
        # Therefore no numeric guaranteed benefit can be claimed without an
        # explicit location classification. Return a calculable lower-level
        # result only when a canonical generic field exists.
        generic_key = (
            "special"
            if is_special
            else "general"
        )
        generic_value = subsidy_block.get(generic_key)

        if isinstance(generic_value, (int, float)):
            rate = float(generic_value)
        else:
            urban_key = (
                "special_urban"
                if is_special
                else "general_urban"
            )
            rural_key = (
                "special_rural"
                if is_special
                else "general_rural"
            )
            urban_rate = subsidy_block.get(urban_key)
            rural_rate = subsidy_block.get(rural_key)

            if (
                not isinstance(urban_rate, (int, float))
                or not isinstance(rural_rate, (int, float))
            ):
                raise ValueError(
                    "PMEGP requires urban/rural classification before a "
                    "numeric margin-money rate can be calculated."
                )

            # Avoid arbitrary assumption. Use the lower applicable rate as a
            # conservative estimate, and clearly mark verification.
            rate = min(
                float(urban_rate),
                float(rural_rate),
            )

        cap = _param_value(
            entity,
            "maximum_subsidy",
        )
        project_cost = self._validate_project_cost(
            factory,
            factory.project_cost_inr,
        )

        result = self._margin_money_calculation(
            eligible_project_cost=project_cost,
            subsidy_rate_percent=rate,
            cap_inr=cap,
            source_ids=[
                source
                for source in [
                    _param_source(
                        entity,
                        "maximum_subsidy",
                    ),
                ]
                if source
            ],
            notes_prefix=(
                "PMEGP credit-linked margin-money support. "
            ),
        )

        return SchemeBenefit(
            scheme_id="PMEGP",
            display_name=entity.get(
                "display_name",
                "PMEGP",
            ),
            eligibility_status=eligibility.status,
            benefit_type="margin_money",
            benefit_inr=result.margin_money_inr,
            capex_reduction_inr=0.0,
            annual_financing_benefit_inr=0.0,
            eligible_cost_inr=result.eligible_base_inr,
            calculation_notes=(
                f"{result.notes} "
                "PMEGP margin money is a financing contribution; "
                "it is not counted as a generic capital-subsidy reduction."
            ),
            source_ids=result.source_ids,
            verification_required=True,
            financial_support_reference=reference,
            margin_money_inr=result.margin_money_inr,
            policy_relevance_score=0.55,
            eligibility_confidence_score=0.60,
            verification_burden_score=0.80,
            stackable=False,
            stack_group=STACK_GROUPS.get("PMEGP"),
        )

    def _benefit_clcss(
        self,
        factory: Factory,
        eligibility: SchemeEligibility,
    ) -> Optional[SchemeBenefit]:
        """Handle CLCSS without inventing a missing canonical rate.

        The current repository's eligibility engine explicitly marks CLCSS as
        insufficient_data because a SUB_CLCSS financial-support entity is not
        present in subsidies.json. This method therefore intentionally raises a
        data-availability error if called accidentally.
        """
        _ = factory

        if eligibility.status != STATUS_INSUFFICIENT_DATA:
            raise ValueError(
                "CLCSS was marked calculable, but no canonical SUB_CLCSS "
                "financial-support record was found in subsidies.json."
            )

        return None

    # ------------------------------------------------------------------
    # State-policy handling
    # ------------------------------------------------------------------

    def _resolve_state_object(
        self,
        state: str,
    ) -> Optional[dict[str, Any]]:
        """Resolve a normalized state name to a state-policy object."""
        target = _normalise_state(state)

        for name, policy in self._states.items():
            if _normalise_state(name) == target:
                return policy

        return None

    def _state_scheme_node(
        self,
        scheme_id: str,
    ) -> dict[str, Any]:
        """Resolve an internal state scheme descriptor to policy JSON."""
        descriptor = _STATE_SCHEME_DESCRIPTORS.get(scheme_id)
        if descriptor is None:
            raise KeyError(
                f"State scheme '{scheme_id}' is not configured."
            )

        node = _nested_get(
            self._state,
            descriptor["path"],
        )

        if not isinstance(node, dict):
            raise KeyError(
                f"State policy path '{descriptor['path']}' for "
                f"scheme '{scheme_id}' is missing or invalid."
            )

        return node

    def _benefit_tn_state(
        self,
        scheme_id: str,
        factory: Factory,
        eligibility: SchemeEligibility,
    ) -> SchemeBenefit:
        """Calculate a Tamil Nadu state incentive from state_policies.json."""
        descriptor = _STATE_SCHEME_DESCRIPTORS.get(scheme_id)

        if descriptor is None:
            raise KeyError(
                f"No state scheme descriptor configured for '{scheme_id}'."
            )

        state_policy = self._resolve_state_object(
            factory.state,
        )

        if state_policy is None:
            raise ValueError(
                f"No verified state policy object exists for state "
                f"'{factory.state}'."
            )

        if descriptor["state"] != "Tamil Nadu":
            raise ValueError(
                f"State scheme '{scheme_id}' is not a Tamil Nadu scheme."
            )

        node = self._state_scheme_node(scheme_id)

        rate = self._extract_state_rate(node)
        cap = self._extract_state_cap(node)

        eligible_base = factory.project_cost_inr

        # State policy defines the benefit basis. The current eligibility.py
        # contract marks these as eligible and the state source itself defines
        # the applicable percentage/cap. We use project_cost_inr as the
        # repository's stable factory input for the scheme.
        result = self._capital_subsidy_calculation(
            eligible_cost=eligible_base,
            rate_percent=rate,
            cap_inr=cap,
            source_ids=[
                "state_policies.json",
            ],
            notes_prefix=(
                f"{descriptor['display_name']}. "
            ),
        )

        return SchemeBenefit(
            scheme_id=scheme_id,
            display_name=descriptor["display_name"],
            eligibility_status=eligibility.status,
            benefit_type=descriptor["benefit_type"],
            benefit_inr=result.capped_benefit_inr,
            capex_reduction_inr=result.capped_benefit_inr,
            annual_financing_benefit_inr=0.0,
            eligible_cost_inr=result.eligible_base_inr,
            calculation_notes=(
                f"{result.notes} "
                f"State policy source path={descriptor['path']}."
            ),
            source_ids=result.source_ids,
            verification_required=eligibility.verification_required,
            financial_support_reference=None,
            policy_relevance_score=0.80,
            eligibility_confidence_score=(
                0.90 if not eligibility.verification_required else 0.75
            ),
            verification_burden_score=0.45,
            stackable=False,
            stack_group=STACK_GROUPS.get(scheme_id),
        )

    @staticmethod
    def _extract_state_rate(
        node: dict[str, Any],
    ) -> float:
        """Extract a state-policy capital rate without hard-coded values."""
        candidate_keys = (
            "reimbursement_percent",
            "subsidy_percent",
            "capital_subsidy_percent",
            "rate_percent",
        )

        for key in candidate_keys:
            value = node.get(key)
            if isinstance(value, (int, float)):
                return float(value)

        # Gujarat-style nested categories or other policy structures can
        # legally contain rate dictionaries. Choose a rate only when there is
        # exactly one general rate at this policy node.
        numeric_rates: list[float] = []

        for key, value in node.items():
            if not isinstance(value, (int, float)):
                continue

            lower_key = str(key).lower()
            if (
                "percent" in lower_key
                and (
                    "general" in lower_key
                    or "reimbursement" in lower_key
                    or lower_key == "rate_percent"
                )
            ):
                numeric_rates.append(float(value))

        if len(numeric_rates) == 1:
            return numeric_rates[0]

        raise ValueError(
            "State capital-subsidy rate could not be resolved from "
            "state_policies.json without ambiguity."
        )

    @staticmethod
    def _extract_state_cap(
        node: dict[str, Any],
    ) -> Optional[float]:
        """Extract a state-policy monetary cap."""
        candidate_keys = (
            "maximum_per_enterprise_inr",
            "maximum_inr",
            "maximum_subsidy_inr",
            "annual_ceiling_inr",
        )

        for key in candidate_keys:
            value = node.get(key)
            if isinstance(value, (int, float)):
                return float(value)

        return None

    # ------------------------------------------------------------------
    # Stacking and ranking
    # ------------------------------------------------------------------

    def _validate_stacking(
        self,
        factory: Factory,
        benefits: list[SchemeBenefit],
    ) -> tuple[bool, list[str], list[SchemeBenefit]]:
        """Prevent unsupported double counting.

        The central policy engine rule forbids automatic stacking of multiple
        subsidies against the same CAPEX unless convergence is explicitly
        allowed. The state policy layer similarly warns against claiming the
        same cost component twice.

        The matcher therefore:
        * allows complementary financing benefits, guarantees and certification
          support to coexist with capital subsidies when their cost bases differ;
        * prevents two capital-subsidy benefits in the same stack group from
          simultaneously contributing to CAPEX;
        * keeps any ambiguous same-cost combination as a benefit listing but
          excludes the lower-ranked conflicting benefit from the aggregated
          verified total.
        """
        if not benefits:
            return True, [], []

        notes: list[str] = []
        accepted: list[SchemeBenefit] = []
        seen_groups: set[str] = set()
        stack_ok = True

        # Process highest-ranked items first so the most relevant/high-value
        # scheme gets precedence in any same-base conflict.
        ordered = sorted(
            benefits,
            key=lambda item: (
                item.ranking_score,
                item.benefit_inr,
            ),
            reverse=True,
        )

        for benefit in ordered:
            group = benefit.stack_group

            if group is None:
                accepted.append(benefit)
                continue

            conflict = False
            if group in seen_groups:
                conflict = True
            elif group in {"capital_subsidy_same_cost", "state_capital_subsidy"}:
                if "capital_subsidy_same_cost" in seen_groups or "state_capital_subsidy" in seen_groups:
                    conflict = True

            if conflict:
                stack_ok = False
                notes.append(
                    f"{benefit.scheme_id} is not included in the "
                    f"verified aggregate because another scheme in the same "
                    f"stack group '{group}' or a conflicting capital subsidy is already included. "
                    "The highest-ranked scheme was prioritized."
                )
                continue

            accepted.append(benefit)
            if group:
                seen_groups.add(group)

        # The variable is intentionally retained for auditability and to make
        # it obvious that the conflict logic is based on explicit stack groups.
        _ = seen_groups

        if not stack_ok:
            notes.append(
                "Central/state anti-double-counting rules were enforced. "
                "Complementary financing and guarantee supports remain "
                "separately represented."
            )

        if len(benefits) > 1:
            for benefit in accepted:
                benefit.verification_required = True

        return stack_ok, notes, accepted

    @staticmethod
    def _accepted_group_keys(
        benefits: list[SchemeBenefit],
    ) -> list[SchemeBenefit]:
        """Small helper used to keep stack validation readable."""
        return benefits

    @staticmethod
    def _rank_scheme(
        benefit: SchemeBenefit,
    ) -> float:
        """Rank a scheme using benefit, confidence, verification and relevance.

        The numeric score is deliberately transparent rather than an opaque ML
        output. Monetary benefit is normalised with a logarithm so large-value
        schemes do not dominate all qualitative policy dimensions.
        """
        monetary_value = max(0.0, benefit.benefit_inr)

        # log10(1 + amount) converts INR-scale benefits to a bounded, stable
        # contribution while retaining useful ordering.
        benefit_component = (
            math.log10(1.0 + monetary_value) / 12.0
            if monetary_value > 0
            else 0.0
        )

        benefit_component = _clamp(
            benefit_component,
            0.0,
            1.0,
        )

        confidence_component = _clamp(
            benefit.eligibility_confidence_score,
        )

        verification_component = 1.0 - _clamp(
            benefit.verification_burden_score,
        )

        relevance_component = _clamp(
            benefit.policy_relevance_score,
        )

        return (
            0.40 * benefit_component
            + 0.25 * confidence_component
            + 0.15 * verification_component
            + 0.20 * relevance_component
        )

    def _prepare_ranking(
        self,
        benefits: list[SchemeBenefit],
    ) -> list[SchemeBenefit]:
        """Calculate transparent ranking scores and return descending order."""
        for benefit in benefits:
            benefit.ranking_score = self._rank_scheme(benefit)

        return sorted(
            benefits,
            key=lambda item: (
                item.ranking_score,
                item.benefit_inr,
                item.scheme_id,
            ),
            reverse=True,
        )

    # ------------------------------------------------------------------
    # Scheme dispatcher
    # ------------------------------------------------------------------

    def _build_benefit(
        self,
        scheme_id: str,
        factory: Factory,
        eligibility: SchemeEligibility,
    ) -> Optional[SchemeBenefit]:
        """Dispatch one eligible scheme to its calculation method."""
        builders: dict[
            str,
            Callable[
                [Factory, SchemeEligibility],
                Optional[SchemeBenefit],
            ],
        ] = {
            "ADEETIE": self._benefit_adeetie,
            "MSE_GIFT": self._benefit_mse_gift,
            "MSE_SPICE": self._benefit_mse_spice,
            "ZED": self._benefit_zed,
            "CGTMSE": self._benefit_cgtmse,
            "PMEGP": self._benefit_pmegp,
            "CLCSS": self._benefit_clcss,
        }

        if scheme_id in builders:
            benefit = builders[scheme_id](
                factory,
                eligibility,
            )

            if benefit is not None:
                benefit.eligibility_status = eligibility.status
                benefit.verification_required = (
                    benefit.verification_required
                    or eligibility.verification_required
                )

            return benefit

        if scheme_id in _STATE_SCHEME_DESCRIPTORS:
            return self._benefit_tn_state(
                scheme_id,
                factory,
                eligibility,
            )

        # MNRE CFA currently arrives from eligibility.py only as either
        # conditionally eligible or insufficient-data. No numeric builder is
        # provided here because the exact current CFA is technology/capacity
        # dependent and the canonical eligibility layer deliberately gates it.
        if scheme_id in {
            "MNRE_CFA",
            "MNRE_NBP_CFA",
            "MNRE_MSME_SOLAR_CFA",
        }:
            raise ValueError(
                f"{scheme_id} has no machine-checkable canonical financial "
                "benefit formula in the current subsidies.json contract."
            )

        return None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def match(
        self,
        factory: Factory,
        eligibility: EligibilitySummary,
    ) -> SubsidyMatchResult:
        """Return complete central + state subsidy matching output.

        Parameters
        ----------
        factory:
            Validated factory profile used to determine monetary bases.
        eligibility:
            Output of ``EligibilityChecker.evaluate(factory)``. This is the
            authoritative eligibility result and must be supplied rather than
            recomputed.

        Returns
        -------
        SubsidyMatchResult
            Ranked supported schemes, rejected/insufficient schemes, benefit
            aggregates, stacking-validation outcome and audit warnings.
        """
        validation_errors = self._validate_factory(factory)

        if validation_errors:
            # A hard input error should not masquerade as scheme ineligibility.
            # Preserve the existing contract by returning an empty eligible
            # set and explicitly surfacing the invalid state in warnings.
            return SubsidyMatchResult(
                eligible_schemes=[],
                ineligible_schemes=[],
                insufficient_data_schemes=[
                    SchemeEligibility(
                        scheme_id="FACTORY_INPUT_VALIDATION",
                        status=STATUS_INSUFFICIENT_DATA,
                        reason=(
                            "Factory/project financial inputs failed "
                            "SubsidyMatcher validation."
                        ),
                        failed_conditions=list(validation_errors),
                        missing_inputs=[],
                        benefit_can_be_applied=False,
                        verification_required=True,
                    )
                ],
                estimated_total_benefit_inr=0.0,
                warnings=list(validation_errors),
                combined_subsidy_ceiling_checked=False,
                combined_subsidy_ceiling_note=(
                    "No financial benefits were calculated because "
                    "factory input validation failed."
                ),
                total_benefit_verified=False,
                stack_validation_passed=False,
                stack_validation_notes=list(validation_errors),
            )

        eligible_benefits: list[SchemeBenefit] = []
        ineligible: list[SchemeEligibility] = []
        insufficient: list[SchemeEligibility] = []
        warnings: list[str] = list(eligibility.warnings)

        for scheme_id, scheme_check in eligibility.schemes.items():
            if scheme_check.status == STATUS_NOT_ELIGIBLE:
                ineligible.append(scheme_check)
                continue

            if scheme_check.status == STATUS_INSUFFICIENT_DATA:
                insufficient.append(scheme_check)
                continue

            if scheme_check.status not in {
                STATUS_ELIGIBLE,
                STATUS_CONDITIONALLY_ELIGIBLE,
            }:
                warnings.append(
                    f"Unknown eligibility status "
                    f"'{scheme_check.status}' for '{scheme_id}'."
                )
                insufficient.append(
                    SchemeEligibility(
                        scheme_id=scheme_id,
                        status=STATUS_INSUFFICIENT_DATA,
                        reason=(
                            "Unsupported eligibility status; benefit "
                            "calculation skipped."
                        ),
                        verification_required=True,
                    )
                )
                continue

            try:
                benefit = self._build_benefit(
                    scheme_id,
                    factory,
                    scheme_check,
                )
            except (KeyError, TypeError, ValueError) as exc:
                warnings.append(
                    f"Could not estimate benefit for {scheme_id}: {exc}"
                )
                insufficient.append(
                    SchemeEligibility(
                        scheme_id=scheme_id,
                        status=STATUS_INSUFFICIENT_DATA,
                        reason=str(exc),
                        failed_conditions=[],
                        missing_inputs=[],
                        benefit_can_be_applied=False,
                        verification_required=True,
                    )
                )
                continue
            except Exception as exc:  # pragma: no cover - defensive guard
                warnings.append(
                    f"Unexpected error while calculating {scheme_id}: "
                    f"{type(exc).__name__}: {exc}"
                )
                insufficient.append(
                    SchemeEligibility(
                        scheme_id=scheme_id,
                        status=STATUS_INSUFFICIENT_DATA,
                        reason=(
                            "Unexpected calculation error; benefit "
                            "not applied."
                        ),
                        verification_required=True,
                    )
                )
                continue

            if benefit is None:
                insufficient.append(
                    SchemeEligibility(
                        scheme_id=scheme_id,
                        status=STATUS_INSUFFICIENT_DATA,
                        reason=(
                            "No canonical financial-support calculation "
                            "is available for this scheme."
                        ),
                        verification_required=True,
                    )
                )
                continue

            # Guardrail: interest subvention and guarantees can never reduce
            # CAPEX, even if a future policy record accidentally changes the
            # benefit_type. This enforces the architectural contract.
            if benefit.benefit_type in {
                "interest_subvention",
                "credit_guarantee",
            }:
                benefit.capex_reduction_inr = 0.0

            # Guardrail: credit guarantee is never counted as cash benefit.
            if benefit.benefit_type == "credit_guarantee":
                benefit.benefit_inr = 0.0

            eligible_benefits.append(benefit)

        # Rank first, then validate stack compatibility using the ranked order.
        ranked_candidates = self._prepare_ranking(
            eligible_benefits,
        )

        stack_ok, stack_notes, accepted = self._validate_stacking(
            factory,
            ranked_candidates,
        )

        # "accepted" is the set used for verified aggregate financial values.
        # Every supported scheme remains visible in the ranked list so the
        # dashboard can show potential options, but same-cost conflicting
        # capital subsidies are excluded from the verified combined total.
        accepted_ids = {
            id(benefit)
            for benefit in accepted
        }

        capital_reduction = 0.0
        annual_financing = 0.0
        guarantee_coverage = 0.0
        margin_money = 0.0
        certification_reimbursement = 0.0
        technical_assistance = 0.0

        for benefit in ranked_candidates:
            if id(benefit) not in accepted_ids:
                continue

            capital_reduction += max(
                0.0,
                benefit.capex_reduction_inr,
            )
            annual_financing += max(
                0.0,
                benefit.annual_financing_benefit_inr,
            )
            guarantee_coverage += max(
                0.0,
                benefit.guarantee_coverage_inr,
            )
            margin_money += max(
                0.0,
                benefit.margin_money_inr,
            )
            certification_reimbursement += max(
                0.0,
                benefit.certification_reimbursement_inr,
            )
            technical_assistance += max(
                0.0,
                benefit.technical_assistance_inr,
            )

        # Estimated total benefit is intentionally based only on monetary
        # benefits that are directly comparable as policy support.
        #
        # Guarantees are excluded because they are not cash.
        # Margin money is kept separately because it is a financing structure
        # rather than an unconditional CAPEX grant.
        #
        # Certification reimbursement is cash-like support against a specific
        # documented expense; it is included only in the per-scheme benefit and
        # aggregate monetary support.
        estimated_total = sum(
            max(0.0, benefit.benefit_inr)
            for benefit in accepted
        )

        # Determine whether the data supports a verified combined total.
        # Multiple same-cost capital subsidies cannot be summed automatically.
        combined_checked = stack_ok
        combined_note = (
            "Stacking validation passed successfully without conflicts."
            if stack_ok
            else "Stacking conflicts were resolved by dropping lower-ranked schemes."
        )

        total_verified = (
            bool(accepted)
            and combined_checked
            and stack_ok
            and not any(
                benefit.verification_required
                for benefit in accepted
            )
        )

        if not combined_checked:
            warnings.append(combined_note)

        if not stack_ok:
            warnings.extend(stack_notes)

        # Preserve all ranked schemes in the return contract. This allows the
        # recommendation layer to understand alternatives while all aggregate
        # values remain based on the compatibility-checked accepted subset.
        ranked = self._prepare_ranking(ranked_candidates)

        return SubsidyMatchResult(
            eligible_schemes=ranked,
            ineligible_schemes=ineligible,
            insufficient_data_schemes=insufficient,
            estimated_total_benefit_inr=estimated_total,
            warnings=warnings,
            combined_subsidy_ceiling_checked=combined_checked,
            combined_subsidy_ceiling_note=combined_note,
            total_benefit_verified=total_verified,
            total_capex_reduction_inr=capital_reduction,
            total_annual_financing_benefit_inr=annual_financing,
            total_guarantee_coverage_inr=guarantee_coverage,
            total_margin_money_inr=margin_money,
            total_certification_reimbursement_inr=(
                certification_reimbursement
            ),
            total_technical_assistance_inr=technical_assistance,
            stack_validation_passed=stack_ok,
            stack_validation_notes=stack_notes,
        )

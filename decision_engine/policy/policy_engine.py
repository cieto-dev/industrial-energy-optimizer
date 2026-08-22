"""
policy_engine.py — Policy evaluation + finance orchestration.

Purpose
-------
Single entry point for the policy layer:

    Factory
        ↓
    EligibilityChecker
        ↓
    SubsidyMatcher
        ↓
    PolicyFinanceSummary
        ↓
    PolicyEvaluationResult

Design rules
------------
- Preserve the existing PolicyEvaluationResult contract.
- Preserve EligibilityChecker and SubsidyMatcher responsibilities.
- Do not duplicate policy/finance parameters here.
- Finance values are derived only from matched scheme benefits.
- Do not treat financing enablers such as guarantees as direct CAPEX cash.
- Keep estimates clearly distinguishable from verified claims.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

from decision_engine.policy.eligibility import (
    EligibilityChecker,
    EligibilitySummary,
    SchemeEligibility,
)
from decision_engine.policy.subsidy_matcher import (
    SchemeBenefit,
    SubsidyMatcher,
)
from models.factory import Factory, Quantity, SpecialCategory


@dataclass
class PolicyFinanceSummary:
    """
    Financial summary derived from eligible policy schemes.

    This is intentionally a separate layer from policy eligibility.

    The summary distinguishes:
    - direct CAPEX reduction
    - annual financing support
    - financing/guarantee support
    - total estimated direct benefit
    - estimated net CAPEX

    No claim is made that all benefits are stackable.
    """

    gross_capex_inr: float
    capital_subsidy_inr: float = 0.0
    annual_interest_support_inr: float = 0.0
    guarantee_support_inr: float = 0.0
    tax_incentive_inr: float = 0.0
    cluster_support_inr: float = 0.0
    other_direct_benefit_inr: float = 0.0
    estimated_total_direct_benefit_inr: float = 0.0
    estimated_net_capex_inr: float = 0.0

    direct_benefit_verified: bool = False
    stacking_verified: bool = False

    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "gross_capex_inr": self.gross_capex_inr,
            "capital_subsidy_inr": self.capital_subsidy_inr,
            "annual_interest_support_inr": self.annual_interest_support_inr,
            "guarantee_support_inr": self.guarantee_support_inr,
            "tax_incentive_inr": self.tax_incentive_inr,
            "cluster_support_inr": self.cluster_support_inr,
            "other_direct_benefit_inr": self.other_direct_benefit_inr,
            "estimated_total_direct_benefit_inr": (
                self.estimated_total_direct_benefit_inr
            ),
            "estimated_net_capex_inr": self.estimated_net_capex_inr,
            "direct_benefit_verified": self.direct_benefit_verified,
            "stacking_verified": self.stacking_verified,
            "notes": list(self.notes),
        }


@dataclass
class PolicyEvaluationResult:
    """Full policy engine output for one Factory."""

    factory_id: str
    state: str
    udyam_registered: bool
    msme_classification: str
    derived_msme_classification: str
    eligible: bool
    eligible_schemes: list[SchemeBenefit]
    ineligible_schemes: list[SchemeEligibility]
    insufficient_data_schemes: list[SchemeEligibility]
    estimated_total_benefit_inr: float

    combined_subsidy_ceiling_checked: bool = False
    combined_subsidy_ceiling_note: str = ""
    warnings: list[str] = field(default_factory=list)

    eligibility_summary: Optional[EligibilitySummary] = None

    # Existing matcher-level verification flag.
    total_benefit_verified: bool = False

    # New finance summary.
    finance_summary: Optional[PolicyFinanceSummary] = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "factory_id": self.factory_id,
            "state": self.state,
            "udyam_registered": self.udyam_registered,
            "msme_classification": self.msme_classification,
            "derived_msme_classification": self.derived_msme_classification,
            "eligible": self.eligible,
            "estimated_total_benefit_inr": self.estimated_total_benefit_inr,
            "combined_subsidy_ceiling_checked": (
                self.combined_subsidy_ceiling_checked
            ),
            "combined_subsidy_ceiling_note": (
                self.combined_subsidy_ceiling_note
            ),
            "total_benefit_verified": self.total_benefit_verified,
            "warnings": list(self.warnings),
            "finance_summary": (
                self.finance_summary.to_dict()
                if self.finance_summary is not None
                else None
            ),
            "eligible_schemes": [
                {
                    "scheme_id": s.scheme_id,
                    "display_name": s.display_name,
                    "eligibility_status": s.eligibility_status,
                    "benefit_type": s.benefit_type,
                    "benefit_inr": s.benefit_inr,
                    "capex_reduction_inr": s.capex_reduction_inr,
                    "annual_financing_benefit_inr": (
                        s.annual_financing_benefit_inr
                    ),
                    "eligible_cost_inr": s.eligible_cost_inr,
                    "calculation_notes": s.calculation_notes,
                    "source_ids": list(s.source_ids),
                    "verification_required": s.verification_required,
                    "financial_support_reference": (
                        s.financial_support_reference
                    ),
                }
                for s in self.eligible_schemes
            ],
            "ineligible_schemes": [
                {
                    "scheme_id": s.scheme_id,
                    "status": s.status,
                    "reason": s.reason,
                    "failed_conditions": list(s.failed_conditions),
                }
                for s in self.ineligible_schemes
            ],
            "insufficient_data_schemes": [
                {
                    "scheme_id": s.scheme_id,
                    "status": s.status,
                    "reason": s.reason,
                    "missing_inputs": list(s.missing_inputs),
                }
                for s in self.insufficient_data_schemes
            ],
        }


class PolicyEngine:
    """
    Orchestrates eligibility, subsidy matching and financial aggregation.

    Public API for:
    - backend/apis/policy_api.py
    - scripts/run_pipeline.py
    """

    def __init__(
        self,
        checker: Optional[EligibilityChecker] = None,
        matcher: Optional[SubsidyMatcher] = None,
    ) -> None:
        self._checker = checker or EligibilityChecker()
        self._matcher = matcher or SubsidyMatcher()

    @staticmethod
    def _build_finance_summary(
        factory: Factory,
        eligible_schemes: list[SchemeBenefit],
        estimated_total_benefit_inr: float,
        total_benefit_verified: bool,
    ) -> PolicyFinanceSummary:
        """
        Aggregate scheme-level financial benefits into a finance summary.

        Important:
        - Capital subsidy reduces gross CAPEX.
        - Interest support is an annual financing benefit, NOT a CAPEX
          reduction.
        - Guarantee support is treated as a financing enabler, NOT cash.
        - Unknown/unsupported benefit types are kept in other_direct_benefit.
        """

        gross_capex = float(factory.project_cost_inr or 0.0)

        capital_subsidy = 0.0
        annual_interest_support = 0.0
        guarantee_support = 0.0
        tax_incentive = 0.0
        cluster_support = 0.0
        other_direct_benefit = 0.0

        notes: list[str] = []

        for scheme in eligible_schemes:
            benefit_type = (scheme.benefit_type or "").strip().lower()

            if benefit_type == "capital_subsidy":
                capital_subsidy += max(
                    float(scheme.capex_reduction_inr or 0.0),
                    0.0,
                )

            elif benefit_type == "interest_subvention":
                annual_interest_support += max(
                    float(scheme.annual_financing_benefit_inr or 0.0),
                    0.0,
                )

            elif benefit_type == "credit_guarantee":
                # A guarantee improves financing access; it is not cash
                # that should be subtracted from CAPEX.
                guarantee_support += max(
                    float(scheme.benefit_inr or 0.0),
                    0.0,
                )

            elif benefit_type == "tax_incentive":
                tax_incentive += max(
                    float(scheme.benefit_inr or 0.0),
                    0.0,
                )

            elif benefit_type == "cluster_support":
                cluster_support += max(
                    float(scheme.benefit_inr or 0.0),
                    0.0,
                )

            else:
                other_direct_benefit += max(
                    float(scheme.capex_reduction_inr or 0.0),
                    0.0,
                )

        # Only explicitly CAPEX-reducing benefits reduce net CAPEX.
        estimated_net_capex = max(
            gross_capex - capital_subsidy,
            0.0,
        )

        notes.append(
            "Net CAPEX subtracts only directly identified capital "
            "subsidies; annual interest support and guarantees are "
            "reported separately."
        )

        if eligible_schemes:
            notes.append(
                "Scheme stacking is not assumed unless the policy knowledge "
                "base explicitly verifies that stacking is permitted."
            )
        else:
            notes.append(
                "No eligible financial schemes were matched."
            )

        if not total_benefit_verified:
            notes.append(
                "Estimated policy benefits are not treated as a verified "
                "claimable combined amount."
            )

        return PolicyFinanceSummary(
            gross_capex_inr=gross_capex,
            capital_subsidy_inr=capital_subsidy,
            annual_interest_support_inr=annual_interest_support,
            guarantee_support_inr=guarantee_support,
            tax_incentive_inr=tax_incentive,
            cluster_support_inr=cluster_support,
            other_direct_benefit_inr=other_direct_benefit,
            estimated_total_direct_benefit_inr=max(
                float(estimated_total_benefit_inr or 0.0),
                0.0,
            ),
            estimated_net_capex_inr=estimated_net_capex,
            direct_benefit_verified=total_benefit_verified,
            stacking_verified=False,
            notes=notes,
        )

    def evaluate(self, factory: Factory) -> PolicyEvaluationResult:
        eligibility = self._checker.evaluate(factory)
        match_result = self._matcher.match(factory, eligibility)

        finance_summary = self._build_finance_summary(
            factory=factory,
            eligible_schemes=match_result.eligible_schemes,
            estimated_total_benefit_inr=(
                match_result.estimated_total_benefit_inr
            ),
            total_benefit_verified=match_result.total_benefit_verified,
        )

        return PolicyEvaluationResult(
            factory_id=factory.factory_id,
            state=factory.state,
            udyam_registered=factory.udyam_registered,
            msme_classification=factory.msme_classification,
            derived_msme_classification=eligibility.derived_msme_category,
            eligible=len(match_result.eligible_schemes) > 0,
            eligible_schemes=match_result.eligible_schemes,
            ineligible_schemes=match_result.ineligible_schemes,
            insufficient_data_schemes=match_result.insufficient_data_schemes,
            estimated_total_benefit_inr=(
                match_result.estimated_total_benefit_inr
            ),
            combined_subsidy_ceiling_checked=(
                match_result.combined_subsidy_ceiling_checked
            ),
            combined_subsidy_ceiling_note=(
                match_result.combined_subsidy_ceiling_note
            ),
            warnings=list(match_result.warnings),
            eligibility_summary=eligibility,
            total_benefit_verified=match_result.total_benefit_verified,
            finance_summary=finance_summary,
        )


def tamil_nadu_textile_small_udyam_factory() -> Factory:
    """
    Gate factory profile: Udyam-registered small textile MSME in Tamil Nadu.

    Used by tests/test_policy.py for ROADMAP Sprint 3.3 gate assertions.
    """

    return Factory(
        factory_id="POLICY_GATE_TN_T1",
        name="TN Textile MSME Policy Gate",
        industry="textile",
        state="Tamil Nadu",
        district="Coimbatore",
        production_per_day=Quantity(value=500, unit="kg/day"),
        operating_hours_per_day=16,
        current_fuel="coal",
        fuel_consumption=Quantity(value=2000, unit="kg/day"),
        electricity_consumption_kwh_day=800,
        required_process_temperature_c=200,
        roof_area_sqm=1200,
        budget_inr=25_000_000,
        grid_reliability_pct=85,
        msme_classification="small",
        udyam_registered=True,
        udyam_number="UDYAM-TN-00-1234567",
        annual_turnover_inr=45_000_000,
        plant_and_machinery_or_equipment_investment_inr=30_000_000,
        project_type="energy_efficiency",
        project_cost_inr=20_000_000,
        loan_amount_inr=15_000_000,
        existing_or_new_project="existing",
        brownfield_or_greenfield="brownfield",
        cluster_name="Coimbatore Textile Cluster",
        cluster_is_adeetie_identified=True,
        annual_energy_savings_percent=14,
        special_category=SpecialCategory(women_owned=False),
    )
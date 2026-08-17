"""
policy_engine.py — Policy evaluation orchestrator (Sprint 3.3).

Purpose
-------
Single entry point for the policy layer:

    Factory → EligibilityChecker → SubsidyMatcher → PolicyEvaluationResult

Does not know HTTP, JSON file paths at call sites, or FastAPI.
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
    SubsidyMatchResult,
)
from models.factory import Factory, Quantity, SpecialCategory


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
    warnings: list[str] = field(default_factory=list)
    eligibility_summary: Optional[EligibilitySummary] = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "factory_id": self.factory_id,
            "state": self.state,
            "udyam_registered": self.udyam_registered,
            "msme_classification": self.msme_classification,
            "derived_msme_classification": self.derived_msme_classification,
            "eligible": self.eligible,
            "estimated_total_benefit_inr": self.estimated_total_benefit_inr,
            "warnings": list(self.warnings),
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
    Orchestrates eligibility checking and subsidy matching.

    Public API for backend/apis/policy_api.py (Sprint 3.6) and
    scripts/run_pipeline.py (Sprint 3.5).
    """

    def __init__(
        self,
        checker: Optional[EligibilityChecker] = None,
        matcher: Optional[SubsidyMatcher] = None,
    ) -> None:
        self._checker = checker or EligibilityChecker()
        self._matcher = matcher or SubsidyMatcher()

    def evaluate(self, factory: Factory) -> PolicyEvaluationResult:
        eligibility = self._checker.evaluate(factory)
        match_result = self._matcher.match(factory, eligibility)

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
            warnings=match_result.warnings,
            eligibility_summary=eligibility,
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

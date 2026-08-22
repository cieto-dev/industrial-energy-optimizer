
"""
finance_result.py — Unified Policy & Finance result objects.

Unit 2.5
--------

This module defines the stable output contract between:

    Policy eligibility
        ↓
    Subsidy / financing matching
        ↓
    Finance calculations
        ↓
    Optimizer / dashboard / reporting

Design principles
-----------------
1. Capital subsidies may reduce effective CAPEX.
2. Interest subventions reduce financing cost, not CAPEX.
3. Credit guarantees are financing enablers, not cash benefits.
4. Tax incentives are represented separately and are not silently
   converted into CAPEX reductions.
5. Cluster / policy support is represented as a non-cash or conditional
   benefit unless the source explicitly provides a monetary amount.
6. Unverified or conditional benefits must never be presented as
   guaranteed savings.
7. Every monetary benefit must preserve its source and calculation basis.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional


# ---------------------------------------------------------------------------
# Benefit categories
# ---------------------------------------------------------------------------

BENEFIT_TYPE_CAPITAL_SUBSIDY = "capital_subsidy"
BENEFIT_TYPE_INTEREST_SUBVENTION = "interest_subvention"
BENEFIT_TYPE_CREDIT_GUARANTEE = "credit_guarantee"
BENEFIT_TYPE_TAX_INCENTIVE = "tax_incentive"
BENEFIT_TYPE_CLUSTER_SUPPORT = "cluster_support"
BENEFIT_TYPE_CERTIFICATION_SUPPORT = "certification_support"
BENEFIT_TYPE_OTHER = "other"


# ---------------------------------------------------------------------------
# Eligibility status
# ---------------------------------------------------------------------------

STATUS_ELIGIBLE = "eligible"
STATUS_CONDITIONALLY_ELIGIBLE = "conditionally_eligible"
STATUS_INSUFFICIENT_DATA = "insufficient_data"
STATUS_NOT_ELIGIBLE = "not_eligible"


# ---------------------------------------------------------------------------
# Scheme benefit
# ---------------------------------------------------------------------------


@dataclass
class FinanceBenefit:
    """
    Normalised financial/policy benefit for one scheme.

    This deliberately keeps different benefit mechanisms separate so that
    downstream economics cannot accidentally subtract an interest subsidy
    or guarantee from project CAPEX.
    """

    scheme_id: str
    display_name: str

    eligibility_status: str

    benefit_type: str

    # Monetary values
    benefit_inr: float = 0.0
    capex_reduction_inr: float = 0.0
    annual_financing_benefit_inr: float = 0.0
    tax_benefit_inr: float = 0.0

    # Financing/risk support
    guarantee_coverage_percent: Optional[float] = None
    supported_loan_amount_inr: float = 0.0

    # Non-monetary / conditional policy support
    cluster_support: bool = False
    eligibility_confirmed: bool = False

    # Auditability
    eligible_cost_inr: float = 0.0
    calculation_notes: str = ""
    source_ids: list[str] = field(default_factory=list)

    verification_required: bool = False

    financial_support_reference: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        """Return JSON/API-safe representation."""
        return {
            "scheme_id": self.scheme_id,
            "display_name": self.display_name,
            "eligibility_status": self.eligibility_status,
            "benefit_type": self.benefit_type,
            "benefit_inr": self.benefit_inr,
            "capex_reduction_inr": self.capex_reduction_inr,
            "annual_financing_benefit_inr": self.annual_financing_benefit_inr,
            "tax_benefit_inr": self.tax_benefit_inr,
            "guarantee_coverage_percent": self.guarantee_coverage_percent,
            "supported_loan_amount_inr": self.supported_loan_amount_inr,
            "cluster_support": self.cluster_support,
            "eligibility_confirmed": self.eligibility_confirmed,
            "eligible_cost_inr": self.eligible_cost_inr,
            "calculation_notes": self.calculation_notes,
            "source_ids": list(self.source_ids),
            "verification_required": self.verification_required,
            "financial_support_reference": self.financial_support_reference,
        }


# ---------------------------------------------------------------------------
# Policy eligibility summary
# ---------------------------------------------------------------------------


@dataclass
class PolicyEligibilitySummary:
    """
    Compact representation of factory-level policy eligibility.
    """

    udyam_registered: bool

    declared_msme_classification: str
    derived_msme_classification: str

    classification_consistent: bool

    eligible_scheme_count: int = 0
    conditional_scheme_count: int = 0
    insufficient_data_scheme_count: int = 0
    ineligible_scheme_count: int = 0

    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "udyam_registered": self.udyam_registered,
            "declared_msme_classification": (
                self.declared_msme_classification
            ),
            "derived_msme_classification": (
                self.derived_msme_classification
            ),
            "classification_consistent": self.classification_consistent,
            "eligible_scheme_count": self.eligible_scheme_count,
            "conditional_scheme_count": self.conditional_scheme_count,
            "insufficient_data_scheme_count": (
                self.insufficient_data_scheme_count
            ),
            "ineligible_scheme_count": self.ineligible_scheme_count,
            "warnings": list(self.warnings),
        }


# ---------------------------------------------------------------------------
# Unified finance result
# ---------------------------------------------------------------------------


@dataclass
class PolicyFinanceResult:
    """
    Unified Unit 2.5 output.

    This object is designed to be consumed by:

    - economics
    - optimizer
    - recommendation/explanation layer
    - API
    - dashboard
    - reporting

    Monetary semantics
    ------------------
    project_capex_inr:
        Original pathway CAPEX.

    capital_subsidy_inr:
        Verified/eligible capital subsidy that may reduce CAPEX.

    effective_capex_inr:
        project_capex_inr - capital_subsidy_inr

    annual_interest_support_inr:
        Annual financing benefit from interest subvention.

    annual_tax_benefit_inr:
        Annual/year-one tax benefit where explicitly quantified.

    total_cashflow_benefit_inr:
        Does NOT blindly sum unrelated categories. It is intentionally
        conservative and only contains benefits that have a clearly defined
        monetary interpretation.

    financing_supported_loan_inr:
        Amount of debt for which a scheme may provide financing support.

    """

    factory_id: str
    state: str

    project_capex_inr: float

    # Policy / scheme matches
    benefits: list[FinanceBenefit] = field(default_factory=list)

    # Eligibility overview
    eligibility: Optional[PolicyEligibilitySummary] = None

    # Derived monetary outputs
    capital_subsidy_inr: float = 0.0
    effective_capex_inr: float = 0.0

    annual_interest_support_inr: float = 0.0
    annual_tax_benefit_inr: float = 0.0

    financing_supported_loan_inr: float = 0.0

    # Non-cash support indicators
    credit_guarantee_available: bool = False
    cluster_support_available: bool = False

    # Confidence / auditability
    benefit_total_verified: bool = False
    verification_required: bool = False

    warnings: list[str] = field(default_factory=list)

    def calculate_effective_capex(self) -> float:
        """
        Calculate effective CAPEX after capital subsidies only.

        Interest support, credit guarantees, cluster support and tax
        incentives are deliberately excluded from this subtraction.
        """
        subsidy = max(0.0, self.capital_subsidy_inr)

        self.effective_capex_inr = max(
            0.0,
            self.project_capex_inr - subsidy,
        )

        return self.effective_capex_inr

    def recalculate(self) -> None:
        """Recalculate all aggregate finance fields from benefits."""

        capital_subsidy = 0.0
        annual_interest_support = 0.0
        annual_tax_benefit = 0.0
        supported_loan = 0.0

        guarantee_available = False
        cluster_support_available = False

        any_verification_required = False

        for benefit in self.benefits:

            # Only fully eligible benefits may be treated as immediately
            # claimable by the finance layer.
            if benefit.eligibility_status == STATUS_ELIGIBLE:

                capital_subsidy += max(
                    0.0,
                    benefit.capex_reduction_inr,
                )

                annual_interest_support += max(
                    0.0,
                    benefit.annual_financing_benefit_inr,
                )

                annual_tax_benefit += max(
                    0.0,
                    benefit.tax_benefit_inr,
                )

                supported_loan += max(
                    0.0,
                    benefit.supported_loan_amount_inr,
                )

                if benefit.guarantee_coverage_percent is not None:
                    guarantee_available = True

                if benefit.cluster_support:
                    cluster_support_available = True

            if (
                benefit.eligibility_status
                == STATUS_CONDITIONALLY_ELIGIBLE
                or benefit.verification_required
            ):
                any_verification_required = True

        self.capital_subsidy_inr = capital_subsidy
        self.annual_interest_support_inr = annual_interest_support
        self.annual_tax_benefit_inr = annual_tax_benefit

        self.financing_supported_loan_inr = supported_loan

        self.credit_guarantee_available = guarantee_available
        self.cluster_support_available = cluster_support_available

        self.verification_required = any_verification_required

        self.calculate_effective_capex()

    def to_dict(self) -> dict[str, Any]:
        """
        Return stable JSON-safe representation for API/dashboard/reporting.
        """
        return {
            "factory_id": self.factory_id,
            "state": self.state,
            "project_capex_inr": self.project_capex_inr,

            "eligibility": (
                self.eligibility.to_dict()
                if self.eligibility is not None
                else None
            ),

            "benefits": [
                benefit.to_dict()
                for benefit in self.benefits
            ],

            "capital_subsidy_inr": self.capital_subsidy_inr,
            "effective_capex_inr": self.effective_capex_inr,

            "annual_interest_support_inr": (
                self.annual_interest_support_inr
            ),
            "annual_tax_benefit_inr": (
                self.annual_tax_benefit_inr
            ),

            "financing_supported_loan_inr": (
                self.financing_supported_loan_inr
            ),

            "credit_guarantee_available": (
                self.credit_guarantee_available
            ),
            "cluster_support_available": (
                self.cluster_support_available
            ),

            "benefit_total_verified": self.benefit_total_verified,
            "verification_required": self.verification_required,

            "warnings": list(self.warnings),
        }


# ---------------------------------------------------------------------------
# Helper constructors
# ---------------------------------------------------------------------------


def build_policy_eligibility_summary(
    *,
    udyam_registered: bool,
    declared_msme_classification: str,
    derived_msme_classification: str,
    scheme_results: list[Any],
    warnings: Optional[list[str]] = None,
) -> PolicyEligibilitySummary:
    """
    Convert existing EligibilityChecker results into the unified summary.

    `scheme_results` can contain existing SchemeEligibility-like objects
    exposing a `.status` attribute.
    """

    eligible = 0
    conditional = 0
    insufficient = 0
    ineligible = 0

    for result in scheme_results:
        status = getattr(result, "status", None)

        if status == STATUS_ELIGIBLE:
            eligible += 1
        elif status == STATUS_CONDITIONALLY_ELIGIBLE:
            conditional += 1
        elif status == STATUS_INSUFFICIENT_DATA:
            insufficient += 1
        elif status == STATUS_NOT_ELIGIBLE:
            ineligible += 1

    return PolicyEligibilitySummary(
        udyam_registered=udyam_registered,
        declared_msme_classification=declared_msme_classification,
        derived_msme_classification=derived_msme_classification,
        classification_consistent=(
            declared_msme_classification
            == derived_msme_classification
        ),
        eligible_scheme_count=eligible,
        conditional_scheme_count=conditional,
        insufficient_data_scheme_count=insufficient,
        ineligible_scheme_count=ineligible,
        warnings=list(warnings or []),
    )

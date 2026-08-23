from pydantic import BaseModel, Field
from typing import List, Any, Optional
from datetime import datetime


class EvidenceSummary(BaseModel):
    confidence_pct: float = Field(
        ...,
        ge=0,
        le=100,
    )

    evidence_strength: str
    source_count: int = Field(
        ...,
        ge=0,
    )

    research_quality: str
    field_validation: str

    missing_citations: List[str] = Field(
        default_factory=list
    )

    broken_references: List[str] = Field(
        default_factory=list
    )

    invalid_datasets: List[str] = Field(
        default_factory=list
    )

    unsupported_recommendations: List[str] = Field(
        default_factory=list
    )

    untraceable_parameters: List[str] = Field(
        default_factory=list
    )

    field_results: List[
        dict[str, Any]
    ] = Field(
        default_factory=list
    )

    scoring_factors: dict[
        str,
        float,
    ] = Field(
        default_factory=dict
    )


class RejectedScenarioExplanation(BaseModel):
    scenario_id: str

    technology_sequence: List[str]

    reason: str

    rank: int

    composite_score: float

    key_weakness: str


class PolicyBenefitSummary(BaseModel):
    eligible_schemes: List[str]

    estimated_total_benefit_inr: float

    total_benefit_verified: bool = False

    disclaimer: str = (
        "Estimated combined benefit — subject to manual "
        "verification against scheme-specific convergence rules."
    )


class SensitivityCase(BaseModel):
    label: str = Field(
        ...,
        description=(
            "Best case, Expected, or Worst case"
        ),
    )

    payback_years: Optional[float] = Field(
        None,
        description=(
            "Deterministic simple payback under this scenario."
        ),
    )

    annual_savings_inr: Optional[float] = None

    annual_carbon_cost_inr: float = 0.0

    factors: dict[
        str,
        float,
    ] = Field(
        default_factory=dict
    )

    viable: bool


class SensitivityAnalysis(BaseModel):
    """
    Full Task 3.4 sensitivity result.

    Combines deterministic planning scenarios with the
    Monte Carlo uncertainty distribution.
    """

    best_case: SensitivityCase

    expected_case: SensitivityCase

    worst_case: SensitivityCase

    payback_range_years: tuple[
        Optional[float],
        Optional[float],
    ]

    payback_p10_years: float

    payback_p50_years: float

    payback_p90_years: float

    spread_ratio: float

    top_risk_factors: List[str]

    risk_interpretation: str

    dominant_factor: Optional[str] = None

    carbon_price_is_scenario_assumption: bool = True


class Explanation(BaseModel):
    why_selected: List[str]

    why_others_rejected: List[
        RejectedScenarioExplanation
    ]

    policy_benefits: PolicyBenefitSummary

    sensitivity_notes: SensitivityAnalysis


class Recommendation(BaseModel):
    factory_id: str

    factory_name: str

    industry: str

    state: str

    recommended_scenario_id: str

    recommended_technology_sequence: List[str]

    capex_total_inr: float

    annual_opex_inr: float

    payback_range_years: tuple[
        float,
        float,
    ]

    co2_reduction_pct: float

    fossil_fuel_reduction_pct: float

    composite_score: float

    objective_scores: dict[
        str,
        float,
    ]

    recommended_is_cheapest: bool

    explanation: Explanation

    evidence_summary: EvidenceSummary

    generated_at: datetime = Field(
        default_factory=datetime.utcnow
    )

    model_version: str = "1.1"
from pydantic import BaseModel, Field
from typing import List, Any, Optional
from datetime import datetime
from decimal import Decimal


class RejectedScenarioExplanation(BaseModel):
    """Detailed explanation for why a non-recommended scenario was rejected."""

    scenario_id: str = Field(..., description="ID of the rejected scenario")
    technology_sequence: List[str] = Field(
        ..., description="Technologies in the rejected pathway"
    )
    reason: str = Field(..., description="Primary reason for rejection")
    rank: int = Field(..., description="Final rank in MCDA scoring")
    composite_score: float = Field(..., description="Overall MCDA score")
    key_weakness: str = Field(
        ..., description="Specific weakness (e.g., 'higher cost', 'lower emissions reduction')"
    )


class PolicyBenefitSummary(BaseModel):
    """Summary of policy benefits for the recommended scenario."""

    eligible_schemes: List[str] = Field(
        ..., description="IDs of eligible financing schemes"
    )
    estimated_total_benefit_inr: float = Field(
        ..., description="Sum of individual scheme benefits"
    )
    total_benefit_verified: bool = Field(
        default=False,
        description="Whether total is verified against combined-subsidy ceiling",
    )
    disclaimer: str = Field(
        default="Estimated combined benefit — subject to manual verification against scheme-specific convergence rules; individual scheme benefits are independently sourced, their combined stackability is not.",
        description="Disclaimer text when total_benefit_verified is False",
    )


class SensitivityAnalysis(BaseModel):
    """Reliability engine sensitivity analysis results."""

    payback_p10_years: float = Field(
        ..., description="Optimistic payback (10th percentile)"
    )
    payback_p50_years: float = Field(..., description="Median payback (50th percentile)")
    payback_p90_years: float = Field(
        ..., description="Adverse payback (90th percentile)"
    )
    spread_ratio: float = Field(
        ..., description="Payback uncertainty spread (P90-P10)/P50"
    )
    top_risk_factors: List[str] = Field(
        ..., description="Top drivers of payback variability (tornado ranking)"
    )
    risk_interpretation: str = Field(
        ..., description="Plain-language interpretation of risk level"
    )


class Explanation(BaseModel):
    """Comprehensive explanation for the recommendation."""

    why_selected: List[str] = Field(
        ..., description="Reasons for choosing the recommended pathway"
    )
    why_others_rejected: List[RejectedScenarioExplanation] = Field(
        ..., description="Detailed reasons for rejecting alternatives"
    )
    policy_benefits: PolicyBenefitSummary = Field(
        ..., description="Summary of applicable policy benefits"
    )
    sensitivity_notes: SensitivityAnalysis = Field(
        ..., description="Reliability and sensitivity analysis results"
    )


class Recommendation(BaseModel):
    """
    Complete recommendation report for industrial energy transition.

    Integrates outputs from:
    - Optimizer (3.2): MCDA ranking and scenario selection
    - Policy Engine (3.3): Eligibility and benefit estimation
    - Reliability Engine (3.1): Payback uncertainty and risk analysis
    """

    factory_id: str = Field(..., description="Factory identifier")
    factory_name: str = Field(..., description="Factory name")
    industry: str = Field(..., description="Industry sector")
    state: str = Field(..., description="State location")

    recommended_scenario_id: str = Field(
        ..., description="ID of the recommended pathway"
    )
    recommended_technology_sequence: List[str] = Field(
        ..., description="Technologies in the recommended pathway"
    )

    # Economic Summary
    capex_total_inr: float = Field(..., description="Total capital expenditure (INR)")
    annual_opex_inr: float = Field(..., description="Annual operating expenditure (INR)")
    payback_range_years: tuple[float, float] = Field(
        ..., description="Simple payback range [low, high] years"
    )

    # Environmental Summary
    co2_reduction_pct: float = Field(
        ..., description="CO2 emissions reduction percentage"
    )
    fossil_fuel_reduction_pct: float = Field(
        ..., description="Fossil fuel consumption reduction percentage"
    )

    # MCDA Summary
    composite_score: float = Field(..., description="Overall MCDA score")
    objective_scores: dict[str, float] = Field(
        ..., description="Individual objective scores (cost, emissions, risk)"
    )
    recommended_is_cheapest: bool = Field(
        ..., description="Whether recommended is also the least-cost option"
    )

    # Complete Explanation
    explanation: Explanation = Field(..., description="Full recommendation explanation")

    # Metadata
    generated_at: datetime = Field(
        default_factory=datetime.utcnow, description="Report generation timestamp"
    )
    model_version: str = Field(default="1.0", description="Recommendation model version")
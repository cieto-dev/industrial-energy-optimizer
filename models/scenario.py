"""
Scenario Domain Model.

Represents a candidate industrial energy-transition pathway evaluated
for a specific factory.

Maps to docs/DOMAIN_MODEL.md §4 and docs/DECISION_ENGINE_ARCHITECTURE.md.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, model_validator


class RejectedTechnology(BaseModel):
    """
    Technology rejected during scenario generation or feasibility screening.

    Supports deterministic explainability ("Why not X?").
    """

    model_config = ConfigDict(
        extra="ignore",
        populate_by_name=True,
    )

    technology_id: str = Field(
        ...,
        description="Canonical technology ID of the rejected technology.",
    )

    reason: str = Field(
        ...,
        description=(
            "Engineering reason why the technology was rejected or filtered."
        ),
    )


class ObjectiveScores(BaseModel):
    """
    Multi-criteria decision scores for a scenario.
    """

    model_config = ConfigDict(
        extra="ignore",
        populate_by_name=True,
    )

    cost: float = Field(
        default=0.5,
        ge=0,
        description=(
            "Cost objective score "
            "(higher = better economics / lower CapEx & OpEx)."
        ),
    )

    emissions: float = Field(
        default=0.5,
        ge=0,
        description=(
            "Emissions objective score "
            "(higher = greater decarbonization)."
        ),
    )

    risk: float = Field(
        default=0.5,
        ge=0,
        description=(
            "Risk objective score "
            "(higher = lower operational / supply risk)."
        ),
    )


class Scenario(BaseModel):
    """
    Candidate technology pathway applied to a Factory.
    """

    model_config = ConfigDict(
        extra="ignore",
        populate_by_name=True,
    )

    scenario_id: str = Field(
        ...,
        description="Unique identifier for the candidate scenario.",
    )

    factory_id: str = Field(
        ...,
        description="Factory to which this scenario belongs.",
    )

    technology_sequence: list[str] = Field(
        ...,
        description=(
            "Ordered sequence of canonical technology IDs."
        ),
    )

    capex_total_inr: float = Field(
        ...,
        ge=0,
        description="Total capital expenditure for the scenario.",
    )

    annual_opex_inr: float = Field(
        ...,
        ge=0,
        description="Annual operating expenditure for the scenario.",
    )

    fossil_fuel_reduction_pct: float = Field(
        ...,
        ge=0,
        le=100,
        description="Reduction in fossil-fuel use as a percentage.",
    )

    co2_reduction_pct: float = Field(
        ...,
        ge=0,
        le=100,
        description="CO2 reduction as a percentage.",
    )

    payback_years: tuple[float, float] = Field(
        ...,
        description=(
            "Estimated payback period as "
            "[low_years, high_years] uncertainty range."
        ),
    )

    reliability_score_pct: float = Field(
        ...,
        ge=0,
        le=100,
        description="Scenario reliability score as a percentage.",
    )

    financing_eligible_schemes: list[str] = Field(
        ...,
        description=(
            "Policy or financing scheme IDs potentially applicable."
        ),
    )

    rejected_technologies: list[RejectedTechnology] = Field(
        ...,
        description=(
            "Technologies rejected during scenario screening."
        ),
    )

    objective_scores: ObjectiveScores = Field(
        ...,
        description=(
            "Cost, emissions, and risk scores used by the MCDA ranking."
        ),
    )

    @model_validator(mode="after")
    def validate_payback_range(self) -> "Scenario":
        low, high = self.payback_years

        if low < 0 or high < 0:
            raise ValueError(
                "payback_years cannot contain negative values."
            )

        if low > high:
            raise ValueError(
                "payback_years low value cannot exceed high value."
            )

        return self


# Compatibility aliases
ScenarioOption = Scenario
TransitionScenario = Scenario
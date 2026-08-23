"""
Scenario Playground API.

Task 3.7
--------
POST /scenario-playground/evaluate

Changes:
- biomass price
- electricity tariff
- subsidy
- budget
- carbon price

and re-ranks the already feasible pathways.

The endpoint deliberately does not create new technical feasibility.
Technical constraints continue to come from the existing pipeline.
"""

from __future__ import annotations

from typing import Any, Dict, List, Mapping, Optional

from fastapi import APIRouter, HTTPException  # pyright: ignore[reportMissingImports]
from pydantic import BaseModel, Field

from digital_twin.scenario_engine import (
    PathwayScenarioBasis,
    ScenarioInputs,
    ScenarioPlaygroundEngine,
)


router = APIRouter(
    prefix="/scenario-playground",
    tags=["Scenario Playground"],
)


# ---------------------------------------------------------------------------
# API contracts
# ---------------------------------------------------------------------------


class ScenarioInputRequest(BaseModel):
    biomass_price_inr_per_kg: float = Field(
        ...,
        ge=0,
    )

    electricity_tariff_inr_per_kwh: float = Field(
        ...,
        ge=0,
    )

    subsidy_pct: float = Field(
        ...,
        ge=0,
        le=100,
    )

    budget_inr: float = Field(
        ...,
        ge=0,
    )

    carbon_price_inr_per_tco2: float = Field(
        ...,
        ge=0,
    )


class PathwayInputRequest(BaseModel):
    scenario_id: str = Field(
        ...,
        min_length=1,
    )

    technology_sequence: List[str] = Field(
        ...,
        min_length=1,
    )

    base_capex_inr: float = Field(
        ...,
        ge=0,
    )

    base_annual_opex_inr: float = Field(
        ...,
        ge=0,
    )

    base_biomass_kg_year: float = Field(
        default=0.0,
        ge=0,
    )

    base_electricity_kwh_year: float = Field(
        default=0.0,
        ge=0,
    )

    annual_co2_tonnes: float = Field(
        default=0.0,
        ge=0,
    )

    feasible: bool = True

    technical_score: Optional[float] = None
    financial_score: Optional[float] = None
    resource_score: Optional[float] = None
    policy_score: Optional[float] = None
    risk_score_value: Optional[float] = None
    technology_maturity: Optional[float] = None
    implementation_complexity: Optional[float] = None
    supply_reliability: Optional[float] = None
    electricity_dependence: Optional[float] = None
    biomass_dependence: Optional[float] = None
    carbon_reduction: Optional[float] = None
    confidence_score: Optional[float] = None

    spread_ratio: Optional[float] = None
    risk_tier: Optional[str] = None
    reliability_score_pct: Optional[float] = None

    co2_reduction_pct: float = 0.0

    extra: Dict[str, Any] = Field(
        default_factory=dict,
    )


class ScenarioPlaygroundRequest(BaseModel):
    scenario: ScenarioInputRequest

    pathways: List[PathwayInputRequest] = Field(
        ...,
        min_length=1,
    )

    weights: Optional[Dict[str, float]] = None


# ---------------------------------------------------------------------------
# API
# ---------------------------------------------------------------------------


_ENGINE = ScenarioPlaygroundEngine()


def _to_domain_pathway(
    pathway: PathwayInputRequest,
) -> PathwayScenarioBasis:
    """
    Convert API pathway payload into the engine contract.
    """

    return PathwayScenarioBasis(
        scenario_id=pathway.scenario_id,
        technology_sequence=pathway.technology_sequence,

        base_capex_inr=pathway.base_capex_inr,
        base_annual_opex_inr=pathway.base_annual_opex_inr,

        base_biomass_kg_year=pathway.base_biomass_kg_year,
        base_electricity_kwh_year=(
            pathway.base_electricity_kwh_year
        ),

        annual_co2_tonnes=pathway.annual_co2_tonnes,

        feasible=pathway.feasible,

        technical_score=pathway.technical_score,
        financial_score=pathway.financial_score,
        resource_score=pathway.resource_score,
        policy_score=pathway.policy_score,
        risk_score_value=pathway.risk_score_value,
        technology_maturity=pathway.technology_maturity,
        implementation_complexity=(
            pathway.implementation_complexity
        ),
        supply_reliability=pathway.supply_reliability,
        electricity_dependence=pathway.electricity_dependence,
        biomass_dependence=pathway.biomass_dependence,
        carbon_reduction=pathway.carbon_reduction,
        confidence_score=pathway.confidence_score,

        spread_ratio=pathway.spread_ratio,
        risk_tier=pathway.risk_tier,
        reliability_score_pct=(
            pathway.reliability_score_pct
        ),

        extra={
            **pathway.extra,
            "co2_reduction_pct": pathway.co2_reduction_pct,
        },
    )


@router.post(
    "/evaluate",
    summary="Run a digital-twin economic scenario",
)
def evaluate_scenario(
    request: ScenarioPlaygroundRequest,
) -> Dict[str, Any]:
    """
    Evaluate the supplied scenario and return an updated recommendation.

    The frontend should submit the currently feasible pathways from the
    existing optimization pipeline.

    This guarantees that the playground cannot accidentally turn a
    technically infeasible technology into a feasible one merely because
    its economics changed.
    """

    try:
        scenario = ScenarioInputs(
            biomass_price_inr_per_kg=(
                request.scenario.biomass_price_inr_per_kg
            ),

            electricity_tariff_inr_per_kwh=(
                request.scenario.electricity_tariff_inr_per_kwh
            ),

            subsidy_pct=(
                request.scenario.subsidy_pct
            ),

            budget_inr=(
                request.scenario.budget_inr
            ),

            carbon_price_inr_per_tco2=(
                request.scenario.carbon_price_inr_per_tco2
            ),
        )

        pathways = [
            _to_domain_pathway(pathway)
            for pathway in request.pathways
        ]

        if len(pathways) == 0:
            raise HTTPException(
                status_code=422,
                detail="At least one pathway is required.",
            )

        result = _ENGINE.rank(
            pathways=pathways,
            scenario=scenario,
            weights=request.weights,
        )

        return result

    except HTTPException:
        raise

    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail={
                "message": "Scenario evaluation failed.",
                "error": str(exc),
            },
        ) from exc
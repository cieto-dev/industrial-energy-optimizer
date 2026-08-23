
"""
backend/apis/recommendation_api.py

Recommendation API for the Industrial Energy Transition Optimizer.

Endpoints
---------
GET  /recommendations/{id}
    Return a stored/cached recommendation by recommendation id.

POST /recommendations
    Generate a recommendation from a factory profile by running the
    existing optimization/report pipeline components.

Design
------
The API is intentionally orchestration-focused. It does not implement
MCDA/ranking itself. The optimizer remains responsible for ranking, while
the report generator remains responsible for the final Recommendation
domain model and explanation.

The public recommendation contract follows models/recommendation.py.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Optional
from uuid import uuid4

from fastapi import APIRouter, HTTPException, status  # type: ignore[import-not-found]
from pydantic import BaseModel, Field, ValidationError

from models.factory import Factory
from models.scenario import Scenario
from models.recommendation import Recommendation

from decision_engine.optimizer.optimization_engine import (
    OptimizationResult,
    ScenarioMetrics,
    optimize,
)
from decision_engine.reports.report_generator import generate_recommendation


router = APIRouter(
    prefix="/recommendations",
    tags=["Recommendations"],
)


# ---------------------------------------------------------------------------
# In-memory recommendation store
# ---------------------------------------------------------------------------
#
# This is suitable for the current MVP/API layer and avoids introducing a
# database dependency into the endpoint. A later persistence layer can
# replace this dictionary without changing the response contract.
#
# The roadmap states that DB persistence is an architecture concern and that
# the core recommendation contract should remain stable.
# ---------------------------------------------------------------------------

_RECOMMENDATION_STORE: Dict[str, Recommendation] = {}


# ---------------------------------------------------------------------------
# API request models
# ---------------------------------------------------------------------------


class RecommendationRequest(BaseModel):
    """
    Request payload for generating a recommendation.

    The fields mirror the factory information already accepted by the
    optimization API, while also allowing precomputed candidate pathway
    metrics to be supplied directly.

    This keeps the endpoint useful for:
      1. frontend -> API integration
      2. tests using deterministic candidate pathways
      3. later integration with the full pipeline
    """

    factory_id: Optional[str] = None
    factory_name: Optional[str] = None

    industry: str = Field(..., min_length=1)
    state: str = Field(..., min_length=1)

    current_fuel: str = Field(default="coal", min_length=1)
    required_process_temperature_c: float = Field(
        ...,
        gt=0,
        description="Required process temperature in degrees Celsius.",
    )

    production_per_day: Optional[Dict[str, Any]] = None
    operating_hours_per_day: Optional[float] = Field(default=None, gt=0)
    operating_days_per_year: Optional[float] = Field(default=None, gt=0)

    fuel_consumption: Optional[Dict[str, Any]] = None
    electricity_consumption_kwh_day: Optional[float] = Field(default=None, ge=0)

    roof_area_sqm: Optional[float] = Field(default=None, ge=0)
    available_land_sqm: Optional[float] = Field(default=None, ge=0)

    budget_inr: Optional[float] = Field(default=None, ge=0)
    grid_reliability_pct: Optional[float] = Field(
        default=None,
        ge=0,
        le=100,
    )

    msme_classification: Optional[str] = None
    udyam_registered: Optional[bool] = None
    annual_turnover_inr: Optional[float] = Field(default=None, ge=0)
    plant_and_machinery_or_equipment_investment_inr: Optional[float] = Field(
        default=None,
        ge=0,
    )

    project_type: Optional[str] = None
    project_cost_inr: Optional[float] = Field(default=None, ge=0)
    existing_or_new_project: Optional[str] = None

    special_category: Optional[Dict[str, Any]] = None

    # Optional deterministic pathway input for direct API/testing integration.
    #
    # Expected structure:
    #
    # [
    #   {
    #       "scenario_id": "scenario_biomass",
    #       "technology_sequence": ["biomass"],
    #       "capex_inr": 1000000,
    #       "annual_opex_inr": 500000,
    #       "pathway_co2_tonnes_year": 600,
    #       "co2_reduction_pct": 30,
    #       "spread_ratio": 0.4,
    #       "risk_tier": "moderate",
    #       "reliability_score_pct": 80,
    #       "scenario": {...}
    #   }
    # ]
    #
    # When omitted, a small deterministic candidate set is generated from
    # the factory profile for MVP behavior.
    candidate_pathways: Optional[list[Dict[str, Any]]] = None


class RecommendationSummaryResponse(BaseModel):
    """
    Lightweight response for the list endpoint.
    """

    id: str
    recommendation: Recommendation


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _build_factory(request: RecommendationRequest) -> Factory:
    """
    Convert the API payload to the project's Factory domain model.

    The repository already uses Factory as the domain-level object for the
    pipeline. We keep construction localized here so the API does not leak
    Pydantic payload details into decision-engine modules.
    """

    factory_data: Dict[str, Any] = {
        "factory_id": request.factory_id or f"fac_{uuid4().hex[:10]}",
        "name": request.factory_name or f"{request.industry.title()} Factory",
        "industry": request.industry,
        "state": request.state,
        "current_fuel": request.current_fuel,
        "required_process_temperature_c": request.required_process_temperature_c,
    }

    optional_fields = {
        "district": None,
        "production_per_day": request.production_per_day,
        "operating_hours_per_day": request.operating_hours_per_day,
        "operating_days_per_year": request.operating_days_per_year,
        "fuel_consumption": request.fuel_consumption,
        "electricity_consumption_kwh_day": request.electricity_consumption_kwh_day,
        "roof_area_sqm": request.roof_area_sqm,
        "available_land_sqm": request.available_land_sqm,
        "budget_inr": request.budget_inr,
        "grid_reliability_pct": request.grid_reliability_pct,
        "msme_classification": request.msme_classification,
        "udyam_registered": request.udyam_registered,
        "annual_turnover_inr": request.annual_turnover_inr,
        "plant_and_machinery_or_equipment_investment_inr": (
            request.plant_and_machinery_or_equipment_investment_inr
        ),
        "project_type": request.project_type,
        "project_cost_inr": request.project_cost_inr,
        "existing_or_new_project": request.existing_or_new_project,
        "special_category": request.special_category,
    }

    for key, value in optional_fields.items():
        if value is not None:
            factory_data[key] = value

    try:
        return Factory(**factory_data)
    except ValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "message": "Factory profile validation failed.",
                "errors": exc.errors(),
            },
        ) from exc


def _default_candidate_pathways(
    request: RecommendationRequest,
) -> list[Dict[str, Any]]:
    """
    Create a deterministic MVP candidate set.

    This is intentionally small and explainable. The master architecture
    explicitly recommends keeping the MVP scenario space small enough to
    test and explain rather than creating arbitrary technology combinations.
    """

    budget = request.budget_inr or 12_000_000.0
    industry = request.industry.lower()

    technology_map = {
        "textile": ["biomass", "solar_thermal", "heat_pump", "waste_heat_recovery"],
        "cement": ["waste_heat_recovery", "electrification", "solar_thermal"],
        "chemical": ["biomass", "solar_thermal", "heat_pump", "biogas"],
        "dairy": ["solar_thermal", "heat_pump", "biogas", "biomass"],
        "food_processing": ["solar_thermal", "biomass", "heat_pump", "biogas"],
        "glass": ["electrification", "waste_heat_recovery", "biomass"],
        "paper": ["biomass", "biogas", "waste_heat_recovery", "solar_thermal"],
        "pharmaceutical": ["solar_thermal", "heat_pump", "biomass"],
        "steel": ["waste_heat_recovery", "electrification", "biomass"],
    }

    technologies = technology_map.get(
        industry,
        ["biomass", "solar_thermal", "heat_pump"],
    )

    candidates: list[Dict[str, Any]] = []

    for index, technology in enumerate(technologies):
        capex_factor = 0.60 + (index * 0.12)
        opex_factor = 0.040 + (index * 0.006)

        co2_reduction = max(
            10.0,
            min(80.0, 30.0 + (index * 12.0)),
        )

        reliability = max(
            60.0,
            92.0 - (index * 6.0),
        )

        risk_tier = (
            "low"
            if index == 0
            else "moderate"
            if index <= 2
            else "high"
        )

        candidates.append(
            {
                "scenario_id": f"scenario_{technology}",
                "technology_sequence": [technology],
                "capex_inr": budget * capex_factor,
                "annual_opex_inr": budget * opex_factor,
                "pathway_co2_tonnes_year": max(
                    100.0,
                    1200.0 - (index * 180.0),
                ),
                "co2_reduction_pct": co2_reduction,
                "spread_ratio": 0.25 + (index * 0.08),
                "risk_tier": risk_tier,
                "reliability_score_pct": reliability,
            }
        )

    return candidates


def _metrics_from_payload(
    pathways: list[Dict[str, Any]],
) -> tuple[list[ScenarioMetrics], Dict[str, Scenario]]:
    """
    Convert API pathway dictionaries into optimizer metrics and Scenario
    domain objects.

    The optimizer works with ScenarioMetrics, while report generation needs
    Scenario objects. Keeping the conversion here preserves the shared
    contracts between layers.
    """

    metrics: list[ScenarioMetrics] = []
    scenarios: Dict[str, Scenario] = {}

    for pathway in pathways:
        scenario_id = str(pathway.get("scenario_id", "")).strip()
        if not scenario_id:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Each candidate pathway requires a non-empty scenario_id.",
            )

        sequence = (
            pathway.get("technology_sequence")
            or pathway.get("technologies")
            or []
        )

        if isinstance(sequence, str):
            sequence = [sequence]

        if not sequence:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Scenario '{scenario_id}' must contain at least one technology.",
            )

        try:
            metric = ScenarioMetrics(
                scenario_id=scenario_id,
                technology_sequence=list(sequence),
                capex_inr=pathway.get("capex_inr"),
                annual_opex_inr=pathway.get("annual_opex_inr"),
                pathway_co2_tonnes_year=pathway.get(
                    "pathway_co2_tonnes_year"
                ),
                co2_reduction_pct=pathway.get("co2_reduction_pct"),
                spread_ratio=pathway.get("spread_ratio"),
                risk_tier=pathway.get("risk_tier"),
                reliability_score_pct=pathway.get(
                    "reliability_score_pct"
                ),
                financial=pathway.get("financial"),
                emission=pathway.get("emission"),
                risk_score=pathway.get("risk_score"),
                extra={
                    key: value
                    for key, value in pathway.items()
                    if key
                    not in {
                        "scenario_id",
                        "technology_sequence",
                        "technologies",
                        "capex_inr",
                        "annual_opex_inr",
                        "pathway_co2_tonnes_year",
                        "co2_reduction_pct",
                        "spread_ratio",
                        "risk_tier",
                        "reliability_score_pct",
                        "financial",
                        "emission",
                        "risk_score",
                        "scenario",
                    }
                },
            )
        except (TypeError, ValueError, KeyError) as exc:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={
                    "message": f"Invalid metrics for scenario '{scenario_id}'.",
                    "error": str(exc),
                },
            ) from exc

        scenario_payload = pathway.get("scenario")

        if isinstance(scenario_payload, Scenario):
            scenario = scenario_payload

        elif isinstance(scenario_payload, dict):
            # Keep the API compatible with direct Scenario JSON payloads.
            scenario_data = dict(scenario_payload)
            scenario_data.setdefault("scenario_id", scenario_id)
            scenario_data.setdefault("technology_sequence", list(sequence))

            try:
                scenario = Scenario(**scenario_data)
            except ValidationError as exc:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail={
                        "message": f"Invalid Scenario object for '{scenario_id}'.",
                        "errors": exc.errors(),
                    },
                ) from exc

        else:
            # Construct the minimum Scenario object needed by the
            # Recommendation report generator.
            #
            # Payback cannot be inferred as a guaranteed value from the API
            # payload, so we use a transparent deterministic range based on
            # CAPEX / annual OPEX. This is explicitly only an MVP fallback.
            capex = float(pathway.get("capex_inr") or 0.0)
            annual_opex = float(pathway.get("annual_opex_inr") or 0.0)

            if annual_opex > 0:
                payback_low = max(0.1, capex / (annual_opex * 1.25))
                payback_high = max(
                    payback_low,
                    capex / (annual_opex * 0.75),
                )
            else:
                payback_low = 0.0
                payback_high = 0.0

            scenario = Scenario(
                scenario_id=scenario_id,
                factory_id="",
                technology_sequence=list(sequence),
                capex_total_inr=capex,
                annual_opex_inr=annual_opex,
                fossil_fuel_reduction_pct=float(
                    pathway.get("fossil_fuel_reduction_pct", 0.0)
                ),
                co2_reduction_pct=float(
                    pathway.get("co2_reduction_pct", 0.0)
                ),
                payback_years=(payback_low, payback_high),
                reliability_score_pct=float(
                    pathway.get("reliability_score_pct", 0.0)
                ),
                financing_eligible_schemes=list(
                    pathway.get("financing_eligible_schemes", [])
                ),
                rejected_technologies=list(
                    pathway.get("rejected_technologies", [])
                ),
                objective_scores=dict(
                    pathway.get("objective_scores", {})
                ),
            )

        scenarios[scenario_id] = scenario
        metrics.append(metric)

    return metrics, scenarios


def _attach_factory_id_to_scenarios(
    scenarios: Dict[str, Scenario],
    factory_id: str,
) -> Dict[str, Scenario]:
    """
    Scenario models are immutable at the decision level conceptually, but
    their factory_id is required by the Recommendation report contract.

    Reconstruct only the affected field to avoid mutating an upstream object.
    """

    updated: Dict[str, Scenario] = {}

    for scenario_id, scenario in scenarios.items():
        data = scenario.model_dump(mode="python")
        data["factory_id"] = factory_id
        updated[scenario_id] = Scenario(**data)

    return updated


def _recommendation_to_response(
    recommendation_id: str,
    recommendation: Recommendation,
) -> Dict[str, Any]:
    """
    Standard machine-readable response envelope.
    """

    payload = recommendation.model_dump(mode="json")

    return {
        "status": "success",
        "id": recommendation_id,
        "recommendation": payload,
        "generated_at": recommendation.generated_at.isoformat(),
    }


# ---------------------------------------------------------------------------
# GET recommendation by id
# ---------------------------------------------------------------------------


@router.get(
    "/{recommendation_id}",
    response_model=Dict[str, Any],
    summary="Get a recommendation by id",
)
def get_recommendation(recommendation_id: str) -> Dict[str, Any]:
    """
    Return a previously generated recommendation.

    Unlike the old demo endpoint, this route now returns the actual
    recommendation created by POST /recommendations.
    """

    recommendation = _RECOMMENDATION_STORE.get(recommendation_id)

    if recommendation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Recommendation '{recommendation_id}' was not found.",
        )

    return _recommendation_to_response(
        recommendation_id,
        recommendation,
    )


# ---------------------------------------------------------------------------
# POST recommendation
# ---------------------------------------------------------------------------


@router.post(
    "",
    response_model=Dict[str, Any],
    status_code=status.HTTP_201_CREATED,
    summary="Generate a recommendation",
)
def create_recommendation(
    request: RecommendationRequest,
) -> Dict[str, Any]:
    """
    Generate and return a complete recommendation.

    Flow
    ----
    1. Validate request.
    2. Build Factory domain object.
    3. Resolve candidate pathways.
    4. Run MCDA optimizer.
    5. Build lightweight policy/reliability adapters for MVP.
    6. Generate Recommendation through report_generator.py.
    7. Store recommendation by id.
    8. Return complete recommendation JSON.

    The optimizer remains the source of truth for ranking. The report
    generator remains the source of truth for explanation construction.
    """

    factory = _build_factory(request)

    pathways = request.candidate_pathways or _default_candidate_pathways(
        request
    )

    metrics, scenarios = _metrics_from_payload(pathways)

    if len(metrics) < 2:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="At least two candidate pathways are required.",
        )

    factory_id = factory.factory_id

    scenarios = _attach_factory_id_to_scenarios(
        scenarios,
        factory_id,
    )

    try:
        optimization_result: OptimizationResult = optimize(metrics)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "message": "Optimization failed.",
                "error": str(exc),
            },
        ) from exc

    # ------------------------------------------------------------------
    # MVP policy/reliability adapters
    # ------------------------------------------------------------------
    #
    # The report generator currently expects PolicyEvaluationResult and
    # ReliabilitySweepResult. Those engines are separate concerns in the
    # repository. This API does not duplicate their business logic.
    #
    # When the full pipeline service is exposed directly, this adapter block
    # can be replaced with the actual policy/reliability service outputs.
    # ------------------------------------------------------------------

    try:
        from decision_engine.policy.policy_engine import (
            PolicyEngine,
        )
        from decision_engine.reliability.reliability_engine import (
            BaseCaseInputs,
            run_reliability_sweep,
        )

        policy_engine = PolicyEngine()
        policy_result = policy_engine.evaluate(factory)

        # A deterministic base case for the API layer.
        #
        # Full production use should pass the actual scenario economics from
        # the economics engine instead of these boundary defaults.
        recommended_id = optimization_result.recommended_scenario_id
        recommended_metric = next(
            metric
            for metric in metrics
            if metric.scenario_id == recommended_id
        )

        baseline_fuel_cost = float(
            request.budget_inr * 0.08
            if request.budget_inr
            else 1_000_000.0
        )

        reliability_result = run_reliability_sweep(
            BaseCaseInputs(
                capex_min=float(
                    recommended_metric.capex_inr or 0.0
                ),
                capex_max=float(
                    (recommended_metric.capex_inr or 0.0) * 1.10
                ),
                baseline_annual_opex=baseline_fuel_cost,
                proposed_fuel_cost=float(
                    (recommended_metric.annual_opex_inr or 0.0) * 0.60
                ),
                proposed_electricity_cost=float(
                    (recommended_metric.annual_opex_inr or 0.0) * 0.20
                ),
                proposed_maintenance_cost=float(
                    (recommended_metric.annual_opex_inr or 0.0) * 0.10
                ),
                proposed_labour_cost=float(
                    (recommended_metric.annual_opex_inr or 0.0) * 0.05
                ),
                proposed_other_cost=float(
                    (recommended_metric.annual_opex_inr or 0.0) * 0.05
                ),
                baseline_fuel_cost=baseline_fuel_cost,
                baseline_electricity_cost=float(
                    (request.electricity_consumption_kwh_day or 0.0)
                    * 365.0
                    * 8.0
                ),
                solar_fraction=0.0,
            ),
            n_iterations=100,
        )

    except Exception:
        # Do not silently fabricate a recommendation if the supporting
        # policy/reliability layers are broken. Return a clear API failure.
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=(
                "Recommendation dependencies could not be evaluated. "
                "Check policy_engine and reliability_engine integration."
            ),
        )

    try:
        recommendation = generate_recommendation(
            factory_id=factory.factory_id,
            factory_name=factory.name,
            industry=factory.industry,
            state=factory.state,
            optimization_result=optimization_result,
            policy_result=policy_result,
            reliability_result=reliability_result,
            scenarios=scenarios,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "message": "Recommendation generation failed.",
                "error": str(exc),
            },
        ) from exc

    recommendation_id = f"rec_{uuid4().hex[:12]}"

    # Store the domain object, not just the serialized JSON.
    _RECOMMENDATION_STORE[recommendation_id] = recommendation

    response = _recommendation_to_response(
        recommendation_id,
        recommendation,
    )

    # Explicit recommendation metadata is useful to frontend clients and
    # keeps the machine-readable contract stable.
    response["meta"] = {
        "model_version": recommendation.model_version,
        "generated_at": recommendation.generated_at.isoformat(),
        "candidate_count": len(optimization_result.ranked_scenarios),
        "recommended_is_cheapest": (
            optimization_result.recommended_is_cheapest
        ),
        "cheapest_scenario_id": (
            optimization_result.cheapest_scenario_id
        ),
        "weights_used": dict(
            optimization_result.weights_used
        ),
    }

    return response


# ---------------------------------------------------------------------------
# List generated recommendations
# ---------------------------------------------------------------------------


@router.get(
    "",
    response_model=list[RecommendationSummaryResponse],
    summary="List generated recommendations",
)
def list_recommendations() -> list[RecommendationSummaryResponse]:
    """
    Return all recommendations currently held by the MVP store.
    """

    return [
        RecommendationSummaryResponse(
            id=recommendation_id,
            recommendation=recommendation,
        )
        for recommendation_id, recommendation in _RECOMMENDATION_STORE.items()
    ]

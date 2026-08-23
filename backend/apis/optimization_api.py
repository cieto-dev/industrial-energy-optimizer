
"""
optimization_api.py

End-to-end API orchestration for the Industrial Energy Transition Optimizer.

Pipeline
--------
User
  ↓
API
  ↓
Knowledge Repository
  ↓
Biomass Engine
  ↓
Technology Engine
  ↓
Constraint / Feasibility Engine
  ↓
Finance Engine
  ↓
Tariff Engine
  ↓
Scenario Generator
  ↓
MCDA / Optimizer
  ↓
Recommendation
  ↓
Evidence
  ↓
Dashboard response

Important
---------
This module is an orchestrator.

It must NOT:
- fabricate financial results,
- duplicate knowledge-base data,
- bypass technical feasibility checks,
- invent evidence,
- silently treat unavailable engines as successful,
- replace MCDA with cheapest-cost sorting.

Where a downstream engine does not yet exist in the repository, the API
returns an explicit status rather than manufacturing a result.
"""

from __future__ import annotations

from datetime import datetime, timezone
from importlib import import_module
from typing import Any, Dict, List, Mapping, Optional, Sequence

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, ConfigDict, Field, model_validator

from knowledge_runtime import KnowledgeRepository


router = APIRouter(
    prefix="/optimization",
    tags=["Optimization"],
)


# ---------------------------------------------------------------------------
# Request models
# ---------------------------------------------------------------------------


class FactoryProfileRequest(BaseModel):
    """
    HTTP contract for a factory optimization request.

    The model deliberately keeps optional engineering/economic fields
    flexible because different frontend versions may provide different
    levels of detail.
    """

    model_config = ConfigDict(extra="allow")

    factory_id: Optional[str] = None
    name: Optional[str] = None

    industry: str = Field(..., min_length=1)
    state: str = Field(..., min_length=1)
    district: Optional[str] = None

    current_fuel: str = Field(..., min_length=1)

    required_process_temperature_c: float = Field(..., ge=0)

    production_per_day: Optional[Dict[str, Any]] = None
    operating_hours_per_day: Optional[float] = Field(default=None, gt=0)
    operating_days_per_year: Optional[float] = Field(
        default=None,
        gt=0,
    )

    fuel_consumption: Optional[Dict[str, Any]] = None

    electricity_consumption_kwh_day: Optional[float] = Field(
        default=None,
        ge=0,
    )

    roof_area_sqm: Optional[float] = Field(default=None, ge=0)
    available_land_sqm: Optional[float] = Field(default=None, ge=0)

    budget_inr: Optional[float] = Field(default=None, ge=0)

    grid_capacity_kw: Optional[float] = Field(default=None, ge=0)
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

    # Optional engineering signals used by the technology/constraint layers.
    biomass_supply_available: Optional[bool] = None
    biomass_available: Optional[bool] = None
    biomass_supply_reliable: Optional[bool] = None
    available_biomass_kg_day: Optional[float] = Field(default=None, ge=0)

    solar_resource_available: Optional[bool] = None
    recoverable_waste_heat: Optional[bool] = None
    electricity_available: Optional[bool] = None

    steam_required: Optional[bool] = None
    required_pressure_bar: Optional[float] = Field(default=None, ge=0)
    process_pressure_bar: Optional[float] = Field(default=None, ge=0)

    direct_heating_required: Optional[bool] = None
    indirect_heating_required: Optional[bool] = None

    additional_grid_capacity_kw: Optional[float] = Field(
        default=None,
        ge=0,
    )


class OptimizationPreferences(BaseModel):
    """
    Optional user/team preferences for MCDA.

    We deliberately keep this explicit rather than letting the API invent
    hidden weights.
    """

    weights: Optional[Dict[str, float]] = None
    minimum_scenarios: int = Field(default=3, ge=1, le=10)
    maximum_scenarios: int = Field(default=5, ge=1, le=10)
    include_biomass_scenarios: bool = True


class OptimizationRequest(BaseModel):
    factory: FactoryProfileRequest
    preferences: OptimizationPreferences = Field(
        default_factory=OptimizationPreferences
    )

    @model_validator(mode="before")
    @classmethod
    def wrap_raw_factory(cls, data: Any) -> Any:
        if isinstance(data, dict) and "factory" not in data:
            return {"factory": data, "preferences": {}}
        return data


# ---------------------------------------------------------------------------
# Generic helpers
# ---------------------------------------------------------------------------


def _model_dump(model: BaseModel) -> Dict[str, Any]:
    """Support both Pydantic v1 and v2 style model dumping."""
    if hasattr(model, "model_dump"):
        return model.model_dump()
    return model.dict()


def _utc_now() -> str:
    """Return a timezone-aware UTC timestamp."""
    return datetime.now(timezone.utc).isoformat()


def _normalise(value: Any) -> str:
    """Normalize identifiers for comparison."""
    return str(value).strip().lower().replace("-", "_").replace(" ", "_")


def _safe_float(value: Any) -> Optional[float]:
    """Convert numeric values safely."""
    if value is None:
        return None

    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _as_dict(value: Any) -> Dict[str, Any]:
    """Return a defensive dictionary representation."""
    if isinstance(value, Mapping):
        return dict(value)

    if hasattr(value, "to_dict"):
        result = value.to_dict()
        if isinstance(result, Mapping):
            return dict(result)

    if hasattr(value, "model_dump"):
        result = value.model_dump()
        if isinstance(result, Mapping):
            return dict(result)

    if hasattr(value, "__dict__"):
        return dict(value.__dict__)

    return {}


def _flatten_evidence(
    value: Any,
    *,
    seen: Optional[set[str]] = None,
) -> List[Dict[str, Any]]:
    """
    Collect evidence records recursively from engine outputs.

    This does not invent evidence. It only preserves evidence objects
    already returned by the knowledge repository or downstream engines.
    """

    if seen is None:
        seen = set()

    evidence: List[Dict[str, Any]] = []

    if isinstance(value, Mapping):
        for key, item in value.items():
            normalized_key = _normalise(key)

            if normalized_key in {
                "evidence",
                "evidence_items",
                "evidence_records",
                "sources",
                "source_records",
            }:
                if isinstance(item, list):
                    for record in item:
                        if isinstance(record, Mapping):
                            record_copy = dict(record)
                            fingerprint = repr(sorted(record_copy.items()))

                            if fingerprint not in seen:
                                seen.add(fingerprint)
                                evidence.append(record_copy)

                elif isinstance(item, Mapping):
                    record_copy = dict(item)
                    fingerprint = repr(sorted(record_copy.items()))

                    if fingerprint not in seen:
                        seen.add(fingerprint)
                        evidence.append(record_copy)

            evidence.extend(
                _flatten_evidence(
                    item,
                    seen=seen,
                )
            )

    elif isinstance(value, list):
        for item in value:
            evidence.extend(
                _flatten_evidence(
                    item,
                    seen=seen,
                )
            )

    return evidence


def _engine_status(
    *,
    name: str,
    status: str,
    details: Optional[str] = None,
) -> Dict[str, Any]:
    result: Dict[str, Any] = {
        "engine": name,
        "status": status,
    }

    if details:
        result["details"] = details

    return result


# ---------------------------------------------------------------------------
# Runtime engine discovery
# ---------------------------------------------------------------------------


def _load_optional_callable(
    candidates: Sequence[tuple[str, str]],
) -> Optional[Any]:
    """
    Load the first available callable from a list of module/function pairs.

    This allows Unit 2.13 to integrate existing modules without forcing
    placeholder implementations for layers that are not yet finished.
    """

    for module_name, attribute_name in candidates:
        try:
            module = import_module(module_name)
            candidate = getattr(module, attribute_name, None)

            if callable(candidate):
                return candidate

        except (ImportError, ModuleNotFoundError, AttributeError):
            continue

    return None


def _load_optional_class(
    candidates: Sequence[tuple[str, str]],
) -> Optional[type]:
    """Load the first available class from candidate modules."""

    for module_name, attribute_name in candidates:
        try:
            module = import_module(module_name)
            candidate = getattr(module, attribute_name, None)

            if isinstance(candidate, type):
                return candidate

        except (ImportError, ModuleNotFoundError, AttributeError):
            continue

    return None


# ---------------------------------------------------------------------------
# Knowledge Repository
# ---------------------------------------------------------------------------


def _build_knowledge_context(
    repo: KnowledgeRepository,
    factory: Mapping[str, Any],
) -> Dict[str, Any]:
    """
    Retrieve the knowledge required for the optimization request.

    This function is intentionally conservative:
    missing optional KB items are recorded rather than fabricated.
    """

    industry_id = str(factory["industry"])
    state_id = str(factory["state"])

    context: Dict[str, Any] = {
        "industry": None,
        "biomass": None,
        "tariffs": None,
        "technologies": None,
        "emission_factors": None,
        "grid_factors": None,
        "evidence": [],
    }

    errors: List[str] = []

    # Industry profile.
    try:
        context["industry"] = repo.get_industry(industry_id)
    except Exception as exc:
        errors.append(f"industry: {exc}")

    # Biomass Atlas.
    try:
        context["biomass"] = repo.get_biomass()
    except Exception as exc:
        errors.append(f"biomass: {exc}")

    # State tariff records.
    try:
        context["tariffs"] = repo.get_tariff(
            state_id=state_id,
        )
    except Exception as exc:
        errors.append(f"tariffs: {exc}")

    # Technology profiles.
    try:
        context["technologies"] = repo.get_technology()
    except Exception as exc:
        errors.append(f"technologies: {exc}")

    # Emission factors.
    try:
        context["emission_factors"] = repo.get_emission_factor()
    except Exception as exc:
        errors.append(f"emission_factors: {exc}")

    # Grid factors.
    try:
        context["grid_factors"] = repo.get_grid_factor()
    except Exception as exc:
        errors.append(f"grid_factors: {exc}")

    context["knowledge_errors"] = errors
    context["evidence"] = _flatten_evidence(context)

    return context


# ---------------------------------------------------------------------------
# Technology assessment
# ---------------------------------------------------------------------------


def _run_technology_filter(
    factory: Mapping[str, Any],
) -> Dict[str, Any]:
    """
    Use the existing technical technology-filter engine.

    The engine is loaded dynamically so the API remains import-safe when a
    development branch temporarily lacks an optional module.
    """

    filter_function = _load_optional_callable(
        [
            (
                "decision_engine.technology.technology_filter",
                "filter_technologies",
            ),
            (
                "decision_engine.technology.technology_filter",
                "screen_technologies",
            ),
            (
                "decision_engine.technology.technology_filter",
                "assess_technologies",
            ),
        ]
    )

    if filter_function is None:
        return {
            "status": "not_available",
            "feasible": [],
            "rejected": [],
            "message": (
                "No callable technology-filter entry point was found."
            ),
        }

    try:
        result = filter_function(factory)

        if isinstance(result, Mapping):
            return dict(result)

        if isinstance(result, list):
            return {
                "status": "success",
                "feasible": result,
                "rejected": [],
            }

        return {
            "status": "success",
            "feasible": [],
            "rejected": [],
            "raw_result": result,
        }

    except TypeError:
        # Some implementations expose a class-based API instead.
        technology_engine_cls = _load_optional_class(
            [
                (
                    "decision_engine.technology.technology_engine",
                    "TechnologyEngine",
                ),
            ]
        )

        if technology_engine_cls is None:
            raise

        engine = technology_engine_cls()

        for method_name in (
            "filter_technologies",
            "screen_technologies",
            "assess",
            "evaluate",
        ):
            method = getattr(engine, method_name, None)

            if callable(method):
                return _as_dict(method(factory))

        raise


# ---------------------------------------------------------------------------
# Biomass layer
# ---------------------------------------------------------------------------


def _run_biomass_engine(
    factory: Mapping[str, Any],
) -> Dict[str, Any]:
    """
    Run biomass-specific engineering logic when the request/industry calls
    for a biomass pathway.

    The API does not force biomass into the candidate list when technical
    inputs do not support it.
    """

    biomass_engine_cls = _load_optional_class(
        [
            (
                "decision_engine.biomass.biomass_engine",
                "BiomassEngine",
            ),
        ]
    )

    if biomass_engine_cls is None:
        return _engine_status(
            name="biomass_engine",
            status="not_available",
            details="BiomassEngine class was not found.",
        )

    try:
        engine = biomass_engine_cls()

        heat_demand = factory.get("heat_demand_kwh_day")

        if heat_demand is None:
            # The baseline layer is authoritative for useful heat.
            # Do not manufacture demand here.
            return _engine_status(
                name="biomass_engine",
                status="awaiting_baseline",
                details=(
                    "Useful heat demand is not present in the factory "
                    "request, so biomass quantity calculations are deferred "
                    "to the baseline-aware integration layer."
                ),
            )

        temperature = factory["required_process_temperature_c"]

        result: Dict[str, Any] = {}

        if hasattr(engine, "check_feasibility"):
            result["feasibility"] = engine.check_feasibility(
                heat_demand_kwh_day=float(heat_demand),
                process_temperature_c=float(temperature),
                industry=factory.get("industry"),
                current_fuel=factory.get("current_fuel"),
                biomass_available=(
                    factory.get("biomass_supply_available")
                    if factory.get("biomass_supply_available") is not None
                    else (
                        factory.get("biomass_available")
                        if factory.get("biomass_available") is not None
                        else True
                    )
                ),
                biomass_supply_reliable=(
                    factory.get("biomass_supply_reliable")
                    if factory.get("biomass_supply_reliable") is not None
                    else True
                ),
                available_biomass_kg_day=(
                    factory.get("available_biomass_kg_day")
                ),
            )

        if hasattr(engine, "calculate"):
            result["calculation"] = engine.calculate(
                heat_demand_kwh_day=float(heat_demand),
                process_temperature_c=float(temperature),
                industry=factory.get("industry"),
                current_fuel=factory.get("current_fuel"),
            )

        if not result:
            return _engine_status(
                name="biomass_engine",
                status="available_no_compatible_entrypoint",
                details=(
                    "BiomassEngine exists, but no compatible public "
                    "calculation method was found for the current request."
                ),
            )

        return {
            "engine": "biomass_engine",
            "status": "success",
            **result,
        }

    except Exception as exc:
        return {
            "engine": "biomass_engine",
            "status": "error",
            "error": str(exc),
        }


# ---------------------------------------------------------------------------
# Constraint / feasibility layer
# ---------------------------------------------------------------------------


def _run_constraint_layer(
    factory: Mapping[str, Any],
    feasible_technologies: List[Any],
) -> Dict[str, Any]:
    """
    Run scenario/technology feasibility modules when implemented.

    The technology_filter is already the primary technical gate. Additional
    feasibility modules can refine the scenario set without changing the API
    contract.
    """

    feasibility_function = _load_optional_callable(
        [
            (
                "decision_engine.scenario.scenario_feasibility",
                "check_scenario_feasibility",
            ),
            (
                "decision_engine.scenario.scenario_feasibility",
                "validate_scenario_feasibility",
            ),
        ]
    )

    if feasibility_function is None:
        return {
            "status": "not_available",
            "feasible": feasible_technologies,
            "rejected": [],
            "message": (
                "No standalone scenario feasibility entry point was found; "
                "technology-level feasibility remains authoritative."
            ),
        }

    try:
        result = feasibility_function(
            factory=factory,
            technologies=feasible_technologies,
        )

        return (
            dict(result)
            if isinstance(result, Mapping)
            else {
                "status": "success",
                "result": result,
            }
        )

    except TypeError:
        # Try a positional-compatible form.
        result = feasibility_function(
            factory,
            feasible_technologies,
        )

        return (
            dict(result)
            if isinstance(result, Mapping)
            else {
                "status": "success",
                "result": result,
            }
        )


# ---------------------------------------------------------------------------
# Scenario generation
# ---------------------------------------------------------------------------


def _run_scenario_generator(
    feasible_technologies: List[Any],
    factory: Mapping[str, Any],
    preferences: OptimizationPreferences,
) -> Dict[str, Any]:
    generator = _load_optional_callable(
        [
            (
                "decision_engine.scenario.scenario_generator",
                "generate_scenarios",
            ),
        ]
    )

    if generator is None:
        return {
            "status": "not_available",
            "scenarios": [],
            "message": "Scenario generator was not found.",
        }

    try:
        result = generator(
            feasible_technologies,
            industry=factory.get("industry"),
            minimum_scenarios=preferences.minimum_scenarios,
            maximum_scenarios=preferences.maximum_scenarios,
            include_biomass_scenarios=preferences.include_biomass_scenarios,
        )

        return (
            dict(result)
            if isinstance(result, Mapping)
            else {
                "status": "success",
                "scenarios": result if isinstance(result, list) else [],
            }
        )

    except TypeError:
        # Compatibility with simpler generator functions.
        result = generator(
            feasible_technologies,
            minimum_scenarios=preferences.minimum_scenarios,
            maximum_scenarios=preferences.maximum_scenarios,
        )

        return (
            dict(result)
            if isinstance(result, Mapping)
            else {
                "status": "success",
                "scenarios": result if isinstance(result, list) else [],
            }
        )


# ---------------------------------------------------------------------------
# Finance / tariff layer
# ---------------------------------------------------------------------------


def _run_finance_engine(
    factory: Mapping[str, Any],
    scenarios: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Attempt to enrich scenarios with the repository's economics layer.

    No fallback numeric estimates are fabricated here.
    """

    economics_engine_cls = _load_optional_class(
        [
            (
                "decision_engine.economics.economics_engine",
                "EconomicsEngine",
            ),
        ]
    )

    if economics_engine_cls is None:
        return {
            "status": "not_available",
            "scenarios": scenarios,
            "message": (
                "Economics engine is not available. "
                "CAPEX/OPEX/payback must not be fabricated by the API."
            ),
        }

    try:
        engine = economics_engine_cls()

        enriched: List[Dict[str, Any]] = []

        for scenario in scenarios:
            record = dict(scenario)

            for method_name in (
                "evaluate",
                "calculate",
                "analyse",
                "analyze",
            ):
                method = getattr(engine, method_name, None)

                if callable(method):
                    try:
                        economics = method(
                            factory=factory,
                            scenario=record,
                        )
                    except TypeError:
                        economics = method(
                            factory,
                            record,
                        )

                    if isinstance(economics, Mapping):
                        record["finance"] = dict(economics)

                    break

            enriched.append(record)

        return {
            "status": "success",
            "scenarios": enriched,
        }

    except Exception as exc:
        return {
            "status": "error",
            "scenarios": scenarios,
            "error": str(exc),
        }


def _run_tariff_layer(
    repo: KnowledgeRepository,
    factory: Mapping[str, Any],
    scenarios: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Attach tariff context from the centralized knowledge repository.

    Tariff records are evidence-backed repository data; this function does
    not reinterpret third-party tariff estimates as authoritative values.
    """

    state_id = factory.get("state")

    try:
        tariffs = repo.get_tariff(
            state_id=str(state_id),
        )
    except Exception as exc:
        return {
            "status": "error",
            "scenarios": scenarios,
            "error": str(exc),
        }

    return {
        "status": "success",
        "tariffs": tariffs,
        "scenarios": scenarios,
    }


# ---------------------------------------------------------------------------
# Optimization / MCDA
# ---------------------------------------------------------------------------


def _scenario_to_optimizer_metrics(
    scenarios: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    Convert scenario records into the shared optimizer contract.

    Only existing numeric fields are propagated.
    """

    metrics: List[Dict[str, Any]] = []

    for index, scenario in enumerate(scenarios):
        technologies = (
            scenario.get("technology_sequence")
            or scenario.get("technologies")
            or []
        )

        finance = scenario.get("finance") or {}

        emissions = scenario.get("emissions") or scenario.get(
            "environmental"
        ) or {}

        reliability = scenario.get("reliability") or scenario.get(
            "risk"
        ) or {}

        scenario_id = scenario.get("scenario_id")

        if not scenario_id:
            scenario_id = f"scenario_{index + 1}"

        metric: Dict[str, Any] = {
            "scenario_id": str(scenario_id),
            "technology_sequence": list(technologies),
        }

        field_map = {
            "capex_inr": (
                scenario.get("capex_inr"),
                finance.get("capex_inr"),
                finance.get("capex"),
            ),
            "annual_opex_inr": (
                scenario.get("annual_opex_inr"),
                finance.get("annual_opex_inr"),
                finance.get("opex_inr"),
                finance.get("annual_opex"),
            ),
            "pathway_co2_tonnes_year": (
                scenario.get("pathway_co2_tonnes_year"),
                emissions.get("pathway_co2_tonnes_year"),
                emissions.get("co2_tonnes_year"),
                emissions.get("annual_co2_tonnes"),
            ),
            "co2_reduction_pct": (
                scenario.get("co2_reduction_pct"),
                emissions.get("co2_reduction_pct"),
            ),
            "spread_ratio": (
                scenario.get("spread_ratio"),
                reliability.get("spread_ratio"),
            ),
            "risk_tier": (
                scenario.get("risk_tier"),
                reliability.get("risk_tier"),
            ),
            "reliability_score_pct": (
                scenario.get("reliability_score_pct"),
                reliability.get("reliability_score_pct"),
                reliability.get("score_pct"),
            ),
            "risk_score": (
                scenario.get("risk_score"),
                reliability.get("risk_score"),
            ),
        }

        for field_name, options in field_map.items():
            selected = next(
                (
                    option
                    for option in options
                    if option is not None
                ),
                None,
            )

            if selected is not None:
                metric[field_name] = selected

        # Preserve the full scenario for downstream explanation.
        metric["extra"] = scenario

        metrics.append(metric)

    return metrics


def _run_optimizer(
    scenarios: List[Dict[str, Any]],
    preferences: OptimizationPreferences,
) -> Dict[str, Any]:
    optimize_function = _load_optional_callable(
        [
            (
                "decision_engine.optimizer.optimization_engine",
                "optimize",
            ),
        ]
    )

    if optimize_function is None:
        return {
            "status": "not_available",
            "message": "Optimization engine was not found.",
        }

    candidates = _scenario_to_optimizer_metrics(scenarios)

    # Do not manufacture financial metrics simply to satisfy MCDA.
    required_count = sum(
        1
        for candidate in candidates
        if any(
            key in candidate
            for key in (
                "capex_inr",
                "annual_opex_inr",
                "pathway_co2_tonnes_year",
                "co2_reduction_pct",
                "risk_score",
                "reliability_score_pct",
            )
        )
    )

    if required_count < 2:
        return {
            "status": "awaiting_finance_impact",
            "message": (
                "At least two scenarios do not yet contain enough numeric "
                "cost/emissions/risk inputs for MCDA. No synthetic metrics "
                "were generated."
            ),
            "candidates": candidates,
        }

    try:
        result = optimize(
            candidates,
            weights=preferences.weights,
        )

        return {
            "status": "success",
            "result": _as_dict(result),
            "candidates": candidates,
        }

    except Exception as exc:
        return {
            "status": "error",
            "error": str(exc),
            "candidates": candidates,
        }


# ---------------------------------------------------------------------------
# Recommendation / explanation
# ---------------------------------------------------------------------------


def _build_recommendation(
    optimization: Dict[str, Any],
    scenarios: List[Dict[str, Any]],
) -> Dict[str, Any]:
    if optimization.get("status") != "success":
        return {
            "status": "pending",
            "reason": optimization.get(
                "message",
                "Optimization did not produce a recommendation.",
            ),
        }

    result = optimization.get("result") or {}

    recommended_id = result.get("recommended_scenario_id")

    ranked = result.get("ranked_scenarios") or []

    recommended = next(
        (
            row
            for row in ranked
            if row.get("scenario_id") == recommended_id
        ),
        None,
    )

    source_scenario = next(
        (
            scenario
            for scenario in scenarios
            if scenario.get("scenario_id") == recommended_id
        ),
        None,
    )

    if recommended is None:
        return {
            "status": "error",
            "reason": (
                "Optimizer returned a recommendation ID that could not "
                "be matched to a ranked scenario."
            ),
        }

    return {
        "status": "success",
        "scenario_id": recommended_id,
        "technology_sequence": recommended.get(
            "technology_sequence",
            [],
        ),
        "composite_score": recommended.get(
            "composite_score"
        ),
        "objective_scores": recommended.get(
            "objective_scores",
            {},
        ),
        "is_cheapest": recommended.get(
            "is_cheapest"
        ),
        "rank_reason": recommended.get(
            "rank_reason"
        ),
        "scenario": source_scenario,
        "optimizer_explanation": result.get(
            "why_not_always_cheapest"
        ),
    }


# ---------------------------------------------------------------------------
# Evidence / dashboard serialization
# ---------------------------------------------------------------------------


def _build_evidence_package(
    *,
    knowledge: Dict[str, Any],
    biomass: Dict[str, Any],
    technology: Dict[str, Any],
    constraints: Dict[str, Any],
    finance: Dict[str, Any],
    tariffs: Dict[str, Any],
    scenarios: Dict[str, Any],
    optimization: Dict[str, Any],
    recommendation: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Build a machine-readable evidence package.

    Evidence is gathered from returned engine/repository payloads only.
    """

    combined = {
        "knowledge": knowledge,
        "biomass": biomass,
        "technology": technology,
        "constraints": constraints,
        "finance": finance,
        "tariffs": tariffs,
        "scenarios": scenarios,
        "optimization": optimization,
        "recommendation": recommendation,
    }

    evidence = _flatten_evidence(combined)

    return {
        "count": len(evidence),
        "items": evidence,
        "traceability_status": (
            "supported"
            if evidence
            else "no_embedded_evidence_records_returned"
        ),
    }


def _build_dashboard_payload(
    *,
    request: OptimizationRequest,
    knowledge: Dict[str, Any],
    biomass: Dict[str, Any],
    technology: Dict[str, Any],
    constraints: Dict[str, Any],
    finance: Dict[str, Any],
    tariffs: Dict[str, Any],
    scenarios: Dict[str, Any],
    optimization: Dict[str, Any],
    recommendation: Dict[str, Any],
    evidence: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Final UI-facing payload.

    The dashboard receives both the concise recommendation and the full
    machine-readable trace so it can display 'why', evidence, rejected
    options and engine status.
    """

    factory = _model_dump(request.factory)

    ranked = []
    optimizer_result = optimization.get("result") or {}

    for row in optimizer_result.get("ranked_scenarios", []) or []:
        ranked.append(row)

    return {
        "factory": factory,
        "recommendation": recommendation,
        "ranked_pathways": ranked,
        "technology_assessment": technology,
        "constraint_assessment": constraints,
        "finance": finance,
        "tariffs": tariffs,
        "scenario_generation": scenarios,
        "biomass": biomass,
        "knowledge_context": knowledge,
        "evidence": evidence,
        "engine_status": {
            "knowledge_repository": "success",
            "biomass_engine": biomass.get("status", "unknown"),
            "technology_engine": technology.get("status", "unknown"),
            "constraint_engine": constraints.get("status", "unknown"),
            "finance_engine": finance.get("status", "unknown"),
            "tariff_engine": tariffs.get("status", "unknown"),
            "scenario_generator": scenarios.get("status", "unknown"),
            "mcda_optimizer": optimization.get("status", "unknown"),
            "recommendation": recommendation.get("status", "unknown"),
            "evidence": evidence.get("traceability_status", "unknown"),
        },
    }


# ---------------------------------------------------------------------------
# Main endpoint
# ---------------------------------------------------------------------------


@router.post("/optimize")
def run_optimization(request: OptimizationRequest) -> Dict[str, Any]:
    """
    Run the complete available optimization pipeline.

    The endpoint is intentionally truthful about incomplete backend layers:
    it returns intermediate data and explicit engine statuses rather than
    fabricating missing results.
    """

    try:
        factory = _model_dump(request.factory)
        preferences = request.preferences

        repo = KnowledgeRepository()

        # ---------------------------------------------------------------
        # 1. Knowledge Repository
        # ---------------------------------------------------------------

        knowledge = _build_knowledge_context(
            repo,
            factory,
        )

        # ---------------------------------------------------------------
        # 2. Biomass Engine
        # ---------------------------------------------------------------

        biomass = _run_biomass_engine(factory)

        # ---------------------------------------------------------------
        # 3. Technology Engine / filter
        # ---------------------------------------------------------------

        technology = _run_technology_filter(factory)

        feasible_technologies = list(
            technology.get("feasible", [])
            or technology.get("technologies", [])
            or []
        )

        # Preserve raw technology results for explainability.
        technology["candidate_count"] = len(
            feasible_technologies
        )

        # ---------------------------------------------------------------
        # 4. Constraint Engine
        # ---------------------------------------------------------------

        constraints = _run_constraint_layer(
            factory,
            feasible_technologies,
        )

        constraint_feasible = constraints.get(
            "feasible"
        )

        if isinstance(constraint_feasible, list):
            feasible_technologies = constraint_feasible

        # ---------------------------------------------------------------
        # 5. Scenario Generator
        # ---------------------------------------------------------------

        scenario_result = _run_scenario_generator(
            feasible_technologies,
            factory,
            preferences,
        )

        scenarios_list = list(
            scenario_result.get("scenarios", [])
            or []
        )

        # ---------------------------------------------------------------
        # 6. Finance
        # ---------------------------------------------------------------

        finance = _run_finance_engine(
            factory,
            scenarios_list,
        )

        scenarios_after_finance = list(
            finance.get("scenarios", scenarios_list)
            or []
        )

        # ---------------------------------------------------------------
        # 7. Tariff Engine / tariff context
        # ---------------------------------------------------------------

        tariff_result = _run_tariff_layer(
            repo,
            factory,
            scenarios_after_finance,
        )

        scenarios_after_tariff = list(
            tariff_result.get(
                "scenarios",
                scenarios_after_finance,
            )
            or []
        )

        # ---------------------------------------------------------------
        # 8. MCDA / Optimization
        # ---------------------------------------------------------------

        optimization = _run_optimizer(
            scenarios_after_tariff,
            preferences,
        )

        # ---------------------------------------------------------------
        # 9. Recommendation
        # ---------------------------------------------------------------

        recommendation = _build_recommendation(
            optimization,
            scenarios_after_tariff,
        )

        # ---------------------------------------------------------------
        # 10. Evidence
        # ---------------------------------------------------------------

        evidence = _build_evidence_package(
            knowledge=knowledge,
            biomass=biomass,
            technology=technology,
            constraints=constraints,
            finance=finance,
            tariffs=tariff_result,
            scenarios=scenario_result,
            optimization=optimization,
            recommendation=recommendation,
        )

        # ---------------------------------------------------------------
        # 11. Dashboard response
        # ---------------------------------------------------------------

        dashboard = _build_dashboard_payload(
            request=request,
            knowledge=knowledge,
            biomass=biomass,
            technology=technology,
            constraints=constraints,
            finance=finance,
            tariffs=tariff_result,
            scenarios=scenario_result,
            optimization=optimization,
            recommendation=recommendation,
            evidence=evidence,
        )

        return {
            "status": "success",
            "message": "Optimization pipeline executed.",
            "factory_id": (
                request.factory.factory_id
                or f"fac_{_normalise(request.factory.industry)}"
            ),
            "generated_at": _utc_now(),
            "pipeline": [
                "user",
                "api",
                "knowledge_repository",
                "biomass_engine",
                "technology_engine",
                "constraint_engine",
                "finance_engine",
                "tariff_engine",
                "scenario_generator",
                "mcda",
                "recommendation",
                "evidence",
                "dashboard",
            ],
            "dashboard": dashboard,
        }

    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail={
                "message": "Invalid optimization request.",
                "error": str(exc),
            },
        ) from exc

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail={
                "message": "Optimization pipeline failed.",
                "error": str(exc),
            },
        ) from exc


@router.get("/pipeline-status")
def get_pipeline_status() -> Dict[str, Any]:
    """
    Return the runtime availability of major orchestration layers.

    Useful for dashboard health checks and integration debugging.
    """

    checks = {
        "knowledge_repository": (
            _load_optional_class(
                [
                    (
                        "knowledge_runtime.repository",
                        "KnowledgeRepository",
                    )
                ]
            )
            is not None
        ),
        "biomass_engine": (
            _load_optional_class(
                [
                    (
                        "decision_engine.biomass.biomass_engine",
                        "BiomassEngine",
                    )
                ]
            )
            is not None
        ),
        "technology_engine": (
            _load_optional_callable(
                [
                    (
                        "decision_engine.technology.technology_filter",
                        "filter_technologies",
                    ),
                    (
                        "decision_engine.technology.technology_filter",
                        "screen_technologies",
                    ),
                ]
            )
            is not None
        ),
        "scenario_generator": (
            _load_optional_callable(
                [
                    (
                        "decision_engine.scenario.scenario_generator",
                        "generate_scenarios",
                    )
                ]
            )
            is not None
        ),
        "optimizer": (
            _load_optional_callable(
                [
                    (
                        "decision_engine.optimizer.optimization_engine",
                        "optimize",
                    )
                ]
            )
            is not None
        ),
        "economics_engine": (
            _load_optional_class(
                [
                    (
                        "decision_engine.economics.economics_engine",
                        "EconomicsEngine",
                    )
                ]
            )
            is not None
        ),
    }

    return {
        "status": "success",
        "checked_at": _utc_now(),
        "engines": checks,
    }


from __future__ import annotations

import json
import math
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Iterable, Mapping, MutableMapping, Optional, Sequence

# ---------------------------------------------------------------------------
# Optional project imports (reuse existing engines when present)
# ---------------------------------------------------------------------------

try:
    from decision_engine.biomass.biomass_engine import (
        DEFAULT_MAX_DISTANCE_KM,
        assess_factory_biomass,
        assessment_to_dict,
        build_biomass_result,
    )
except ImportError:  # pragma: no cover - defensive for isolated unit tests
    DEFAULT_MAX_DISTANCE_KM = 150.0
    assess_factory_biomass = None  # type: ignore[assignment]
    assessment_to_dict = None  # type: ignore[assignment]
    build_biomass_result = None  # type: ignore[assignment]

try:
    from decision_engine.technology.industry_constraint_engine import (
        IndustryConstraintEngine,
    )
except ImportError:  # pragma: no cover
    IndustryConstraintEngine = None  # type: ignore[misc, assignment]

try:
    from decision_engine.economics.payback import calculate_payback
except ImportError:  # pragma: no cover
    calculate_payback = None  # type: ignore[assignment]

try:
    from decision_engine.economics.opex import calculate_annual_savings
except ImportError:  # pragma: no cover
    calculate_annual_savings = None  # type: ignore[assignment]

try:
    from decision_engine.scenario.scenario_filter import (
        load_technology_rules,
        _has_explicit_incompatibility,
        _industry_is_allowed,
        _rule_for_technology,
    )
except ImportError:  # pragma: no cover
    load_technology_rules = None  # type: ignore[assignment]
    _has_explicit_incompatibility = None  # type: ignore[assignment]
    _industry_is_allowed = None  # type: ignore[assignment]
    _rule_for_technology = None  # type: ignore[assignment]


# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parents[2]

TARIFF_JSON_PATH = (
    BASE_DIR / "datasets" / "converted" / "electricity_tariffs.json"
)
TECHNOLOGY_RULES_PATH = (
    BASE_DIR / "knowledge-base" / "constraints" / "technology_rules.json"
)
INDUSTRY_CONSTRAINTS_PATH = (
    BASE_DIR / "knowledge-base" / "constraints" / "industry_constraints.json"
)

# Biomass technologies that require resource filtering
BIOMASS_TECHNOLOGY_MARKERS: frozenset[str] = frozenset(
    {
        "biomass",
        "biomass_boiler",
        "biomass_furnace",
        "biomass_gasifier",
        "biomass_cogeneration",
        "tech_biomass",
        "tech_biomass_boiler",
    }
)

# Electric technologies that require state tariff data
ELECTRIC_TECHNOLOGY_MARKERS: frozenset[str] = frozenset(
    {
        "electric_boiler",
        "electric_furnace",
        "heat_pump",
        "induction_furnace",
        "resistance_furnace",
        "electric_arc_furnace",
        "plasma_technology",
        "solar_pv",  # grid interaction / net metering still needs tariff context
        "battery",
        "battery_storage",
        "energy_storage",
        "tech_electric_boiler",
        "tech_heat_pump",
        "tech_induction",
    }
)

# Default finance thresholds (overridable via config on the factory/scenario)
DEFAULT_MAX_PAYBACK_YEARS: float = 7.0
DEFAULT_MIN_ANNUAL_SAVINGS_INR: float = 0.0

# Biomass pass thresholds aligned with Biomass Intelligence Engine semantics
MIN_BIOMASS_SUITABILITY: float = 0.55
MIN_SUPPLY_RELIABILITY: float = 0.40
MAX_BIOMASS_RISK_INDEX: float = 0.75
MIN_ACCEPTABLE_RECOMMENDATIONS: frozenset[str] = frozenset(
    {
        "recommended",
        "conditionally recommended",
        "review",
    }
)


# ---------------------------------------------------------------------------
# Result dataclasses
# ---------------------------------------------------------------------------


@dataclass
class StageResult:
    """Standard result envelope for one filter stage."""

    passed: bool
    reasons: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    metrics: dict[str, Any] = field(default_factory=dict)
    evidence: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "passed": self.passed,
            "reasons": list(self.reasons),
            "warnings": list(self.warnings),
            "metrics": dict(self.metrics),
            "evidence": list(self.evidence),
        }


@dataclass
class FilterConfig:
    """Configurable thresholds for financial and biomass filters."""

    max_payback_years: float = DEFAULT_MAX_PAYBACK_YEARS
    min_annual_savings_inr: float = DEFAULT_MIN_ANNUAL_SAVINGS_INR
    max_biomass_distance_km: float = DEFAULT_MAX_DISTANCE_KM
    min_biomass_suitability: float = MIN_BIOMASS_SUITABILITY
    min_supply_reliability: float = MIN_SUPPLY_RELIABILITY
    max_biomass_risk_index: float = MAX_BIOMASS_RISK_INDEX
    require_tariff_for_electric: bool = True


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _normalize(value: Optional[Any]) -> str:
    if value is None:
        return ""
    return (
        str(value)
        .strip()
        .lower()
        .replace("-", "_")
        .replace(" ", "_")
    )


def _as_dict(obj: Any) -> dict[str, Any]:
    if obj is None:
        return {}
    if isinstance(obj, dict):
        return dict(obj)
    if hasattr(obj, "model_dump"):
        return dict(obj.model_dump())
    if hasattr(obj, "dict"):
        return dict(obj.dict())
    if hasattr(obj, "__dict__"):
        return {
            k: v
            for k, v in vars(obj).items()
            if not k.startswith("_")
        }
    return {}


def _get(obj: Any, *keys: str, default: Any = None) -> Any:
    """Safe nested getter supporting dicts and attribute objects."""
    current: Any = obj
    for key in keys:
        if current is None:
            return default
        if isinstance(current, Mapping):
            current = current.get(key, default)
        else:
            current = getattr(current, key, default)
        if current is default and default is not None:
            return default
    return current


def _technology_sequence(scenario: Any) -> list[str]:
    raw = _get(scenario, "technology_sequence")
    if raw is None:
        raw = _get(scenario, "technologies")
    if raw is None:
        return []
    sequence: list[str] = []
    for item in raw:
        if isinstance(item, str) and item.strip():
            sequence.append(item.strip())
        elif isinstance(item, Mapping):
            tid = (
                item.get("technology_id")
                or item.get("id")
                or item.get("technology")
            )
            if isinstance(tid, str) and tid.strip():
                sequence.append(tid.strip())
    return sequence


def _is_biomass_technology(technology_id: str) -> bool:
    norm = _normalize(technology_id)
    if norm in BIOMASS_TECHNOLOGY_MARKERS:
        return True
    return any(marker in norm for marker in ("biomass",))


def _is_electric_technology(technology_id: str) -> bool:
    norm = _normalize(technology_id)
    if norm in ELECTRIC_TECHNOLOGY_MARKERS:
        return True
    electric_tokens = (
        "electric",
        "heat_pump",
        "induction",
        "resistance",
        "arc_furnace",
        "plasma",
        "battery",
        "solar_pv",
    )
    return any(token in norm for token in electric_tokens)


def _scenario_requires_biomass(scenario: Any) -> bool:
    return any(_is_biomass_technology(t) for t in _technology_sequence(scenario))


def _scenario_requires_tariff(scenario: Any) -> bool:
    return any(_is_electric_technology(t) for t in _technology_sequence(scenario))


def _safe_float(value: Any) -> Optional[float]:
    if value is None:
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if math.isnan(number) or math.isinf(number):
        return None
    return number


def _load_json(path: Path) -> Any:
    if not path.exists():
        raise FileNotFoundError(f"Required dataset not found: {path}")
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


# ---------------------------------------------------------------------------
# Tariff dataset access (no hardcoding)
# ---------------------------------------------------------------------------

_TARIFF_CACHE: Optional[list[dict[str, Any]]] = None


def _load_tariff_records() -> list[dict[str, Any]]:
    global _TARIFF_CACHE
    if _TARIFF_CACHE is not None:
        return _TARIFF_CACHE

    raw = _load_json(TARIFF_JSON_PATH)
    records: list[dict[str, Any]] = []

    if isinstance(raw, list):
        records = [r for r in raw if isinstance(r, Mapping)]
    elif isinstance(raw, Mapping):
        # Support shapes: {"tariffs": [...]}, {"states": {...}}, or flat map
        if "tariffs" in raw and isinstance(raw["tariffs"], list):
            records = [r for r in raw["tariffs"] if isinstance(r, Mapping)]
        elif "data" in raw and isinstance(raw["data"], list):
            records = [r for r in raw["data"] if isinstance(r, Mapping)]
        else:
            # Flatten state → category → tariff objects
            for state_key, state_val in raw.items():
                if isinstance(state_val, list):
                    for item in state_val:
                        if isinstance(item, Mapping):
                            row = dict(item)
                            row.setdefault("state", state_key)
                            records.append(row)
                elif isinstance(state_val, Mapping):
                    for cat_key, cat_val in state_val.items():
                        if isinstance(cat_val, Mapping):
                            row = dict(cat_val)
                            row.setdefault("state", state_key)
                            row.setdefault("consumer_category", cat_key)
                            records.append(row)
                        elif isinstance(cat_val, list):
                            for item in cat_val:
                                if isinstance(item, Mapping):
                                    row = dict(item)
                                    row.setdefault("state", state_key)
                                    row.setdefault("consumer_category", cat_key)
                                    records.append(row)

    _TARIFF_CACHE = records
    return records


def _match_tariff(
    state: str,
    consumer_category: Optional[str] = None,
) -> Optional[dict[str, Any]]:
    """
    Locate a tariff record for the factory state (and optional category).

    Rejects silently (returns None) when no match exists — callers must reject
    the scenario rather than invent rates.
    """
    records = _load_tariff_records()
    state_norm = _normalize(state)
    category_norm = _normalize(consumer_category) if consumer_category else ""

    state_matches: list[dict[str, Any]] = []
    for row in records:
        row_state = _normalize(
            row.get("state")
            or row.get("State")
            or row.get("state_name")
            or row.get("discom_state")
        )
        if row_state == state_norm:
            state_matches.append(row)

    if not state_matches:
        return None

    if category_norm:
        for row in state_matches:
            row_cat = _normalize(
                row.get("consumer_category")
                or row.get("category")
                or row.get("tariff_category")
                or row.get("consumer_type")
            )
            if row_cat and (
                category_norm in row_cat or row_cat in category_norm
            ):
                return row
            # Common industrial labels
            if category_norm in ("industrial", "ht_industrial", "lt_industrial"):
                if any(
                    token in row_cat
                    for token in ("industrial", "ht", "lt_industry", "industry")
                ):
                    return row

    # Prefer industrial category when category not supplied
    for row in state_matches:
        row_cat = _normalize(
            row.get("consumer_category")
            or row.get("category")
            or row.get("tariff_category")
            or ""
        )
        if "industrial" in row_cat or row_cat in ("ht", "lt_industrial"):
            return row

    # Last resort: first state match (still real data, not invented)
    return state_matches[0]


def _extract_energy_charge(tariff: Mapping[str, Any]) -> Optional[float]:
    candidates = (
        "energy_charge_inr_per_kwh",
        "energy_charge",
        "energy_rate",
        "unit_rate",
        "rate_inr_per_kwh",
        "energy_charge_rs_per_kwh",
        "average_energy_charge",
        "energy_charge_inr_kwh",
    )
    for key in candidates:
        value = _safe_float(tariff.get(key))
        if value is not None and value >= 0:
            return value
    # Nested structures
    energy = tariff.get("energy_charges") or tariff.get("energy")
    if isinstance(energy, Mapping):
        for key in ("rate", "value", "inr_per_kwh", "rs_per_kwh"):
            value = _safe_float(energy.get(key))
            if value is not None and value >= 0:
                return value
    if isinstance(energy, (int, float)):
        return float(energy)
    return None


def _extract_demand_charge(tariff: Mapping[str, Any]) -> Optional[float]:
    candidates = (
        "demand_charge_inr_per_kva",
        "demand_charge_inr_per_kw",
        "demand_charge",
        "fixed_demand_charge",
        "demand_rate",
    )
    for key in candidates:
        value = _safe_float(tariff.get(key))
        if value is not None and value >= 0:
            return value
    demand = tariff.get("demand_charges") or tariff.get("demand")
    if isinstance(demand, Mapping):
        for key in ("rate", "value", "inr_per_kva", "inr_per_kw"):
            value = _safe_float(demand.get(key))
            if value is not None and value >= 0:
                return value
    if isinstance(demand, (int, float)):
        return float(demand)
    return None


# ---------------------------------------------------------------------------
# 1. Biomass pathway filter
# ---------------------------------------------------------------------------


def filter_biomass_pathway(
    scenario: Any,
    factory: Any,
    *,
    config: Optional[FilterConfig] = None,
    required_biomass_tons: Optional[float] = None,
) -> dict[str, Any]:
    """
    Filter biomass-dependent scenarios using the Biomass Intelligence Engine.

    Passes automatically (with evidence note) when the scenario has no biomass
    technologies.

    Rejects when:
        - atlas has no district records
        - annual availability insufficient for required demand
        - transport distance exceeds threshold
        - supply reliability too low
        - recommendation is "Not Recommended"
        - suitability / risk thresholds fail
    """
    cfg = config or FilterConfig()
    reasons: list[str] = []
    warnings: list[str] = []
    evidence: list[str] = []
    metrics: dict[str, Any] = {}

    if not _scenario_requires_biomass(scenario):
        return StageResult(
            passed=True,
            reasons=["Scenario does not include biomass technologies; biomass filter skipped."],
            warnings=[],
            metrics={"biomass_required": False},
            evidence=["biomass_filter:not_applicable"],
        ).to_dict()

    if assess_factory_biomass is None:
        return StageResult(
            passed=False,
            reasons=[
                "Biomass Intelligence Engine is unavailable; cannot validate "
                "biomass pathway without inventing data."
            ],
            warnings=[],
            metrics={"biomass_required": True},
            evidence=["biomass_engine:unavailable"],
        ).to_dict()

    state = _get(factory, "state")
    district = _get(factory, "district")
    if not state or not district:
        return StageResult(
            passed=False,
            reasons=[
                "Factory state and district are required for biomass "
                "availability assessment."
            ],
            warnings=[],
            metrics={"biomass_required": True},
            evidence=["factory:missing_location"],
        ).to_dict()

    try:
        assessments = assess_factory_biomass(factory)
    except (ValueError, FileNotFoundError, OSError) as exc:
        return StageResult(
            passed=False,
            reasons=[f"Biomass assessment failed: {exc}"],
            warnings=[],
            metrics={"biomass_required": True},
            evidence=["biomass_engine:error"],
        ).to_dict()

    if not assessments:
        return StageResult(
            passed=False,
            reasons=[
                f"No biomass records found in the Atlas for "
                f"{district}, {state}. Biomass pathway rejected."
            ],
            warnings=[],
            metrics={
                "biomass_required": True,
                "available": False,
                "state": state,
                "district": district,
            },
            evidence=[
                "biomass_atlas:no_records",
                "source:National Biomass Atlas (SSS-NIBE / MNRE)",
            ],
        ).to_dict()

    top = assessments[0]
    top_dict = (
        assessment_to_dict(top)
        if assessment_to_dict is not None
        else asdict(top)
    )

    metrics.update(
        {
            "biomass_required": True,
            "available": True,
            "recommended_biomass": top.biomass_type,
            "recommended_crop": top.crop,
            "annual_availability_tons": top.annual_availability_tons,
            "availability_level": top.availability_level,
            "transport_distance_km": top_dict.get("transport_distance_km"),
            "supply_reliability_score": top.supply_reliability_score,
            "biomass_risk_index": top.biomass_risk_index,
            "suitability_score": top.suitability_score,
            "recommendation": top.recommendation,
            "delivered_cost_inr_per_ton": top.delivered_cost_inr_per_ton,
        }
    )
    evidence.append("source:National Biomass Atlas (SSS-NIBE / MNRE)")
    evidence.append(
        "source:MNRE/GIZ Decarbonizing MSMEs – Biomass for Green Steam & Heat"
    )
    evidence.extend(list(top.reasons))
    warnings.extend(list(top.warnings))

    # --- Availability volume check ---
    demand = required_biomass_tons
    if demand is None:
        demand = _safe_float(
            _get(scenario, "required_biomass_tons")
            or _get(scenario, "biomass_demand_tons")
            or _get(scenario, "metrics", "required_biomass_tons")
        )
    if demand is not None and demand > 0:
        metrics["required_biomass_tons"] = demand
        if top.annual_availability_tons < demand:
            reasons.append(
                f"Annual biomass availability "
                f"({top.annual_availability_tons:.0f} t) is below required "
                f"demand ({demand:.0f} t)."
            )

    # --- Transport distance ---
    distance = _safe_float(top_dict.get("transport_distance_km"))
    if distance is not None and distance > cfg.max_biomass_distance_km:
        reasons.append(
            f"Transport distance {distance:.1f} km exceeds maximum "
            f"acceptable {cfg.max_biomass_distance_km:.0f} km."
        )
    elif distance is None:
        warnings.append(
            "Factory coordinates missing; transport distance could not be "
            "verified against the distance threshold."
        )

    # --- Supply reliability ---
    if top.supply_reliability_score < cfg.min_supply_reliability:
        reasons.append(
            f"Supply reliability score {top.supply_reliability_score:.3f} "
            f"is below minimum {cfg.min_supply_reliability:.2f}."
        )

    # --- Suitability / recommendation / risk ---
    if top.suitability_score < cfg.min_biomass_suitability:
        reasons.append(
            f"Biomass suitability score {top.suitability_score:.3f} "
            f"is below minimum {cfg.min_biomass_suitability:.2f}."
        )

    if top.biomass_risk_index > cfg.max_biomass_risk_index:
        reasons.append(
            f"Biomass risk index {top.biomass_risk_index:.3f} exceeds "
            f"maximum acceptable {cfg.max_biomass_risk_index:.2f}."
        )

    rec_norm = _normalize(top.recommendation).replace("_", " ")
    if rec_norm not in MIN_ACCEPTABLE_RECOMMENDATIONS and "not recommended" in rec_norm:
        reasons.append(
            f"Biomass engine recommendation is '{top.recommendation}'."
        )

    if top.availability_level == "Unavailable":
        reasons.append("Biomass availability level is Unavailable.")

    passed = len(reasons) == 0
    if passed:
        reasons.append(
            f"Biomass pathway accepted: {top.biomass_type} "
            f"({top.crop}) with suitability {top.suitability_score:.3f}."
        )

    return StageResult(
        passed=passed,
        reasons=reasons,
        warnings=warnings,
        metrics=metrics,
        evidence=evidence,
    ).to_dict()


# ---------------------------------------------------------------------------
# 2. Electricity tariff filter
# ---------------------------------------------------------------------------


def filter_tariff(
    scenario: Any,
    factory: Any,
    *,
    config: Optional[FilterConfig] = None,
    consumer_category: Optional[str] = None,
) -> dict[str, Any]:
    """
    Ensure electricity tariff data exists for electric pathways.

    Never hardcodes tariffs. Rejects when tariff data is unavailable for the
    factory state / consumer category.
    """
    cfg = config or FilterConfig()
    reasons: list[str] = []
    warnings: list[str] = []
    evidence: list[str] = []
    metrics: dict[str, Any] = {"tariff_required": False}

    if not _scenario_requires_tariff(scenario):
        return StageResult(
            passed=True,
            reasons=[
                "Scenario does not include electric technologies; "
                "tariff filter skipped."
            ],
            warnings=[],
            metrics=metrics,
            evidence=["tariff_filter:not_applicable"],
        ).to_dict()

    metrics["tariff_required"] = True
    state = _get(factory, "state")
    if not state:
        return StageResult(
            passed=False,
            reasons=["Factory state is required to resolve electricity tariff."],
            warnings=[],
            metrics=metrics,
            evidence=["factory:missing_state"],
        ).to_dict()

    category = consumer_category or _get(
        factory, "consumer_category"
    ) or _get(factory, "tariff_category") or "industrial"

    try:
        tariff = _match_tariff(str(state), str(category) if category else None)
    except FileNotFoundError as exc:
        return StageResult(
            passed=False,
            reasons=[str(exc)],
            warnings=[],
            metrics=metrics,
            evidence=["tariff_dataset:missing"],
        ).to_dict()

    if tariff is None:
        return StageResult(
            passed=False,
            reasons=[
                f"No electricity tariff found for state '{state}' "
                f"(category '{category}'). Electric pathway rejected."
            ],
            warnings=[],
            metrics={
                **metrics,
                "state": state,
                "consumer_category": category,
            },
            evidence=["tariff_dataset:no_match"],
        ).to_dict()

    energy_charge = _extract_energy_charge(tariff)
    demand_charge = _extract_demand_charge(tariff)

    if energy_charge is None:
        return StageResult(
            passed=False,
            reasons=[
                f"Tariff record for '{state}' lacks a usable energy charge. "
                "Cannot evaluate electric pathway without inventing rates."
            ],
            warnings=[],
            metrics={
                **metrics,
                "state": state,
                "consumer_category": category,
                "tariff_record_keys": sorted(str(k) for k in tariff.keys()),
            },
            evidence=["tariff_dataset:missing_energy_charge"],
        ).to_dict()

    # Annual electricity cost from factory baseline when available
    kwh_day = _safe_float(_get(factory, "electricity_consumption_kwh_day"))
    days = _safe_float(_get(factory, "operating_days_per_year")) or 300.0
    annual_kwh: Optional[float] = None
    annual_energy_cost: Optional[float] = None
    if kwh_day is not None:
        annual_kwh = kwh_day * days
        annual_energy_cost = annual_kwh * energy_charge

    metrics.update(
        {
            "state": state,
            "consumer_category": category,
            "energy_charge_inr_per_kwh": energy_charge,
            "demand_charge": demand_charge,
            "annual_electricity_kwh": annual_kwh,
            "annual_energy_cost_inr": annual_energy_cost,
            "tariff_source_fields": {
                k: tariff.get(k)
                for k in (
                    "state",
                    "consumer_category",
                    "category",
                    "discom",
                    "voltage_level",
                    "effective_from",
                )
                if k in tariff
            },
        }
    )
    evidence.append(f"tariff_dataset:{TARIFF_JSON_PATH.name}")
    evidence.append(f"matched_state:{state}")

    if demand_charge is None:
        warnings.append(
            "Demand charge not present in matched tariff record; "
            "energy charge alone was used for screening."
        )

    reasons.append(
        f"Tariff resolved for {state} "
        f"(energy charge {energy_charge} INR/kWh)."
    )

    return StageResult(
        passed=True,
        reasons=reasons,
        warnings=warnings,
        metrics=metrics,
        evidence=evidence,
    ).to_dict()


# ---------------------------------------------------------------------------
# 3. Industry rules filter
# ---------------------------------------------------------------------------


def filter_industry_rules(
    scenario: Any,
    factory: Any,
    *,
    config: Optional[FilterConfig] = None,
) -> dict[str, Any]:
    """
    Validate industry compatibility, temperature, steam/fuel alignment.

    Reuses IndustryConstraintEngine and technology_rules.json when available.
    Rejects incompatible pathways rather than inventing compatibility.
    """
    reasons: list[str] = []
    warnings: list[str] = []
    evidence: list[str] = []
    metrics: dict[str, Any] = {}

    industry = _get(factory, "industry")
    sequence = _technology_sequence(scenario)
    process_temp = _safe_float(
        _get(factory, "required_process_temperature_c")
    )
    current_fuel = _get(factory, "current_fuel")

    metrics["industry"] = industry
    metrics["technology_sequence"] = sequence
    metrics["required_process_temperature_c"] = process_temp
    metrics["current_fuel"] = current_fuel

    if not sequence:
        return StageResult(
            passed=False,
            reasons=["Scenario has an empty technology_sequence."],
            warnings=[],
            metrics=metrics,
            evidence=["scenario:empty_sequence"],
        ).to_dict()

    if not industry:
        return StageResult(
            passed=False,
            reasons=["Factory industry is required for industry rule filtering."],
            warnings=[],
            metrics=metrics,
            evidence=["factory:missing_industry"],
        ).to_dict()

    # --- Technology rules: explicit incompatibility + industry allow-list ---
    tech_rules: Optional[dict[str, Any]] = None
    if load_technology_rules is not None:
        try:
            tech_rules = load_technology_rules()
        except (OSError, json.JSONDecodeError, ValueError) as exc:
            warnings.append(f"Could not load technology_rules.json: {exc}")
    else:
        try:
            tech_rules = _load_json(TECHNOLOGY_RULES_PATH)
            if not isinstance(tech_rules, dict):
                tech_rules = None
        except (OSError, json.JSONDecodeError, FileNotFoundError) as exc:
            warnings.append(f"Could not load technology_rules.json: {exc}")

    if tech_rules and _has_explicit_incompatibility is not None:
        incompatible, detail = _has_explicit_incompatibility(
            tuple(sequence),
            tech_rules,
        )
        if incompatible:
            reasons.append(detail)

    if tech_rules and _industry_is_allowed is not None:
        allowed, detail = _industry_is_allowed(
            tuple(sequence),
            str(industry),
            tech_rules,
        )
        if not allowed:
            reasons.append(detail)

    # Temperature limits from technology rules when present
    if tech_rules and process_temp is not None and _rule_for_technology is not None:
        for tech_id in sequence:
            rule = _rule_for_technology(tech_id, tech_rules)
            if not rule:
                continue
            max_temp = _safe_float(
                rule.get("max_process_temperature_c")
                or rule.get("max_temperature_c")
                or _get(rule, "temperature", "max_c")
            )
            min_temp = _safe_float(
                rule.get("min_process_temperature_c")
                or rule.get("min_temperature_c")
                or _get(rule, "temperature", "min_c")
            )
            if max_temp is not None and process_temp > max_temp:
                reasons.append(
                    f"Technology '{tech_id}' max temperature "
                    f"{max_temp:.0f}°C is below required process "
                    f"temperature {process_temp:.0f}°C."
                )
            if min_temp is not None and process_temp < min_temp:
                reasons.append(
                    f"Technology '{tech_id}' min temperature "
                    f"{min_temp:.0f}°C exceeds required process "
                    f"temperature {process_temp:.0f}°C."
                )

            # Fuel compatibility list when declared
            fuels = rule.get("compatible_fuels") or rule.get("fuels")
            if isinstance(fuels, list) and current_fuel:
                fuel_norm = _normalize(current_fuel)
                allowed_fuels = {_normalize(f) for f in fuels}
                # Replacement technologies may intentionally switch fuel;
                # only reject when rule explicitly lists baseline fuel constraints
                # and marks replacement_requires_compatible_baseline.
                if rule.get("requires_compatible_baseline_fuel") and fuel_norm not in allowed_fuels:
                    reasons.append(
                        f"Technology '{tech_id}' is incompatible with "
                        f"baseline fuel '{current_fuel}'."
                    )

            evidence.append(f"technology_rules:{tech_id}")

    # --- Industry constraint engine (explainability + hard allow flags) ---
    if IndustryConstraintEngine is not None:
        try:
            engine = IndustryConstraintEngine()
            per_tech: list[dict[str, Any]] = []
            for tech_id in sequence:
                result = engine.evaluate(str(industry), tech_id)
                per_tech.append(result)
                classification = _normalize(result.get("classification"))
                allowed = bool(result.get("allowed", result.get("feasible", False)))
                if not allowed and classification not in ("not_defined",):
                    # not_defined is soft: prior technical screening may still apply
                    reasons.append(
                        result.get("reason")
                        or (
                            f"Industry '{industry}' does not allow "
                            f"technology '{tech_id}' "
                            f"(classification={classification})."
                        )
                    )
                elif classification == "not_defined":
                    warnings.append(
                        f"No industry-specific rule for '{tech_id}' in "
                        f"'{industry}'; relying on technology_rules / prior screening."
                    )
                if result.get("source"):
                    evidence.append(str(result["source"]))
            metrics["industry_evaluations"] = [
                {
                    "technology": r.get("technology"),
                    "classification": r.get("classification"),
                    "allowed": r.get("allowed"),
                    "feasible": r.get("feasible"),
                }
                for r in per_tech
            ]
            evidence.append("industry_constraints.json")
        except (OSError, ValueError, KeyError) as exc:
            warnings.append(f"IndustryConstraintEngine error: {exc}")
    else:
        warnings.append(
            "IndustryConstraintEngine unavailable; industry checks limited "
            "to technology_rules.json."
        )

    # Steam / utility mismatch from scenario metadata when present
    steam_required = _get(scenario, "steam_required")
    steam_available = _get(factory, "steam_available")
    if steam_required is True and steam_available is False:
        reasons.append(
            "Scenario requires steam utility but factory reports steam unavailable."
        )

    utility_required = _get(scenario, "required_utilities") or []
    if isinstance(utility_required, (list, tuple)):
        available_utilities = _get(factory, "available_utilities") or []
        if available_utilities:
            avail_set = {_normalize(u) for u in available_utilities}
            for util in utility_required:
                if _normalize(util) not in avail_set:
                    reasons.append(
                        f"Required utility '{util}' is not available at the factory."
                    )

    passed = len(reasons) == 0
    if passed:
        reasons.append(
            f"All technologies in sequence are compatible with industry "
            f"'{industry}' under current rules."
        )

    return StageResult(
        passed=passed,
        reasons=reasons,
        warnings=warnings,
        metrics=metrics,
        evidence=evidence,
    ).to_dict()


# ---------------------------------------------------------------------------
# 4. Financial feasibility filter
# ---------------------------------------------------------------------------


def filter_financial_feasibility(
    scenario: Any,
    factory: Any,
    *,
    config: Optional[FilterConfig] = None,
    policy_output: Optional[Mapping[str, Any]] = None,
) -> dict[str, Any]:
    """
    Financial feasibility using existing scenario/factory financial fields.

    Uses CapEx, annual cost, baseline cost, savings, payback, and budget from
    repository inputs. Does NOT invent costs.

    Policy notes (consumed only, never recomputed):
        - Interest subvention is NOT a capital subsidy.
        - Credit guarantee is NOT CapEx reduction.
    """
    cfg = config or FilterConfig()
    reasons: list[str] = []
    warnings: list[str] = []
    evidence: list[str] = []
    metrics: dict[str, Any] = {}

    capex = _safe_float(
        _get(scenario, "capex_total_inr")
        or _get(scenario, "capex")
        or _get(scenario, "capex_estimate")
        or _get(scenario, "financials", "capex_total_inr")
    )
    annual_opex = _safe_float(
        _get(scenario, "annual_opex_inr")
        or _get(scenario, "proposed_annual_opex")
        or _get(scenario, "financials", "annual_opex_inr")
    )
    baseline_opex = _safe_float(
        _get(scenario, "baseline_annual_opex")
        or _get(scenario, "baseline_opex_inr")
        or _get(factory, "baseline_annual_opex")
        or _get(scenario, "financials", "baseline_annual_opex")
    )
    annual_savings = _safe_float(
        _get(scenario, "annual_savings_inr")
        or _get(scenario, "annual_savings")
        or _get(scenario, "financials", "annual_savings_inr")
    )
    budget = _safe_float(
        _get(factory, "budget_inr")
        or _get(scenario, "budget_inr")
    )

    # Payback may be a scalar or [low, high] range on the Scenario model
    payback_years = _get(scenario, "payback_years")
    payback_low: Optional[float] = None
    payback_high: Optional[float] = None
    if isinstance(payback_years, (list, tuple)) and len(payback_years) >= 1:
        payback_low = _safe_float(payback_years[0])
        if len(payback_years) >= 2:
            payback_high = _safe_float(payback_years[1])
    else:
        payback_low = _safe_float(payback_years)
        payback_high = _safe_float(
            _get(scenario, "payback_max_years")
            or _get(scenario, "financials", "payback_max_years")
        )

    # Derive savings if both opex sides present and savings missing
    if annual_savings is None and baseline_opex is not None and annual_opex is not None:
        if calculate_annual_savings is not None:
            annual_savings = float(
                calculate_annual_savings(
                    baseline_annual_opex=baseline_opex,
                    proposed_annual_opex=annual_opex,
                )
            )
        else:
            annual_savings = baseline_opex - annual_opex
        evidence.append("annual_savings:derived_from_opex")

    # Derive payback if missing but capex + savings available
    if payback_low is None and capex is not None and annual_savings is not None:
        if calculate_payback is not None:
            pb = calculate_payback(
                capex_min=capex,
                capex_max=capex,
                annual_savings=annual_savings,
            )
            payback_low = _safe_float(pb.get("payback_min_years"))
            payback_high = _safe_float(pb.get("payback_max_years"))
            evidence.append("payback:derived_via_economics.payback")
        elif annual_savings > 0:
            payback_low = capex / annual_savings
            payback_high = payback_low
            evidence.append("payback:simple_capex_over_savings")

    # Capital subsidy from policy (ONLY explicit capital subsidy fields)
    capital_subsidy = 0.0
    if policy_output:
        for key in (
            "capital_subsidy_inr",
            "capex_subsidy_inr",
            "eligible_capital_subsidy_inr",
            "total_capital_subsidy_inr",
        ):
            val = _safe_float(policy_output.get(key))
            if val is not None and val > 0:
                capital_subsidy += val
        # Explicitly ignore non-CapEx instruments
        for ignored in (
            "interest_subvention",
            "interest_subvention_inr",
            "interest_subsidy",
            "credit_guarantee",
            "credit_guarantee_amount",
            "cgfmse_cover",
        ):
            if ignored in policy_output and policy_output[ignored]:
                warnings.append(
                    f"Policy field '{ignored}' is not applied as CapEx reduction "
                    "(interest subvention / credit guarantee are not capital subsidies)."
                )
                evidence.append(f"policy:ignored_non_capex:{ignored}")

    effective_capex = capex
    if capex is not None and capital_subsidy > 0:
        effective_capex = max(0.0, capex - capital_subsidy)
        evidence.append("policy:capital_subsidy_applied")

    metrics.update(
        {
            "capex_total_inr": capex,
            "effective_capex_inr": effective_capex,
            "capital_subsidy_inr": capital_subsidy,
            "annual_opex_inr": annual_opex,
            "baseline_annual_opex_inr": baseline_opex,
            "annual_savings_inr": annual_savings,
            "payback_years_low": payback_low,
            "payback_years_high": payback_high,
            "budget_inr": budget,
            "max_payback_years": cfg.max_payback_years,
        }
    )

    # Mandatory input checks
    missing: list[str] = []
    if capex is None:
        missing.append("capex_total_inr")
    if annual_savings is None and (baseline_opex is None or annual_opex is None):
        missing.append("annual_savings_inr (or baseline + proposed opex)")
    if missing:
        return StageResult(
            passed=False,
            reasons=[
                "Missing mandatory financial inputs: " + ", ".join(missing)
            ],
            warnings=warnings,
            metrics=metrics,
            evidence=evidence + ["finance:missing_inputs"],
        ).to_dict()

    # Negative / insufficient savings
    assert annual_savings is not None  # for type checkers
    if annual_savings <= cfg.min_annual_savings_inr:
        reasons.append(
            f"Annual savings {annual_savings:.2f} INR do not exceed "
            f"minimum threshold {cfg.min_annual_savings_inr:.2f} INR."
        )

    # Budget
    if budget is not None and effective_capex is not None:
        if effective_capex > budget:
            reasons.append(
                f"Effective CapEx {effective_capex:.2f} INR exceeds "
                f"factory budget {budget:.2f} INR."
            )
    elif budget is None:
        warnings.append(
            "Factory budget_inr not supplied; budget constraint not applied."
        )

    # Payback threshold — use conservative (higher) bound when available
    payback_for_check = payback_high if payback_high is not None else payback_low
    if payback_for_check is None:
        if annual_savings <= 0:
            reasons.append(
                "Payback cannot be computed because annual savings are non-positive."
            )
        else:
            reasons.append("Payback period is unavailable; cannot confirm feasibility.")
    elif payback_for_check > cfg.max_payback_years:
        reasons.append(
            f"Payback {payback_for_check:.2f} years exceeds maximum "
            f"allowed {cfg.max_payback_years:.2f} years."
        )

    # Financing availability flag from scenario / policy if present
    financing_required = _get(scenario, "financing_required")
    financing_available = _get(scenario, "financing_available")
    schemes = _get(scenario, "financing_eligible_schemes") or []
    if financing_required is True:
        if financing_available is False:
            reasons.append("Required project financing is marked unavailable.")
        elif not schemes and financing_available is not True:
            warnings.append(
                "Financing required but no eligible schemes listed on scenario."
            )

    passed = len(reasons) == 0
    if passed:
        reasons.append(
            "Financial feasibility checks passed "
            f"(savings={annual_savings:.2f}, "
            f"payback={payback_for_check}, "
            f"effective_capex={effective_capex})."
        )
        evidence.append("finance:repository_inputs_only")

    return StageResult(
        passed=passed,
        reasons=reasons,
        warnings=warnings,
        metrics=metrics,
        evidence=evidence,
    ).to_dict()


# ---------------------------------------------------------------------------
# Compatibility stage (consume prior screening / policy; do not recompute)
# ---------------------------------------------------------------------------


def _filter_compatibility(
    scenario: Any,
    factory: Any,
    *,
    policy_output: Optional[Mapping[str, Any]] = None,
) -> dict[str, Any]:
    """
    Lightweight compatibility gate.

    Consumes prior technology/policy screening flags on the scenario.
    Does not recalculate policy eligibility.
    """
    reasons: list[str] = []
    warnings: list[str] = []
    evidence: list[str] = []
    metrics: dict[str, Any] = {}

    sequence = _technology_sequence(scenario)
    if not sequence:
        reasons.append("Missing technology_sequence on scenario.")

    # Honour explicit prior rejection markers
    prior_rejected = _get(scenario, "technically_feasible")
    if prior_rejected is False:
        reasons.append(
            "Scenario marked technically_feasible=False by prior screening."
        )

    policy_eligible = _get(scenario, "policy_eligible")
    if policy_eligible is False:
        warnings.append(
            "Scenario marked policy_eligible=False; proceeding with finance "
            "using zero capital subsidy unless policy_output overrides."
        )

    if policy_output is not None:
        metrics["policy_output_present"] = True
        evidence.append("policy:consumed_not_recalculated")
        if policy_output.get("eligible") is False:
            warnings.append(
                "Policy engine reported ineligible; capital subsidy treated as zero."
            )
    else:
        metrics["policy_output_present"] = False

    metrics["technology_sequence"] = sequence
    metrics["factory_id"] = _get(factory, "factory_id") or _get(scenario, "factory_id")

    passed = len(reasons) == 0
    if passed:
        reasons.append("Compatibility gate passed (structure + prior flags).")

    return StageResult(
        passed=passed,
        reasons=reasons,
        warnings=warnings,
        metrics=metrics,
        evidence=evidence,
    ).to_dict()


# ---------------------------------------------------------------------------
# 5. Complete scenario filter (pipeline)
# ---------------------------------------------------------------------------


def filter_complete_scenario(
    scenario: Any,
    factory: Any,
    *,
    config: Optional[FilterConfig] = None,
    policy_output: Optional[Mapping[str, Any]] = None,
    required_biomass_tons: Optional[float] = None,
    consumer_category: Optional[str] = None,
) -> dict[str, Any]:
    """
    Run the full Part-4 filter pipeline on one scenario.

    Returns the required output envelope::

        {
            "feasible": bool,
            "filter_stages": {
                "compatibility": {...},
                "biomass": {...},
                "tariff": {...},
                "industry_rules": {...},
                "finance": {...},
            },
            "rejection_reasons": [],
            "warnings": [],
            "evidence": [],
        }
    """
    cfg = config or FilterConfig()
    stages: dict[str, dict[str, Any]] = {}
    rejection_reasons: list[str] = []
    all_warnings: list[str] = []
    all_evidence: list[str] = []

    def _absorb(name: str, result: dict[str, Any]) -> bool:
        stages[name] = result
        all_warnings.extend(result.get("warnings") or [])
        all_evidence.extend(result.get("evidence") or [])
        if not result.get("passed", False):
            for reason in result.get("reasons") or []:
                rejection_reasons.append(f"[{name}] {reason}")
            return False
        return True

    # Ordered pipeline — stop early on hard failure but still record stages
    ok = _absorb(
        "compatibility",
        _filter_compatibility(
            scenario,
            factory,
            policy_output=policy_output,
        ),
    )

    if ok:
        ok = _absorb(
            "biomass",
            filter_biomass_pathway(
                scenario,
                factory,
                config=cfg,
                required_biomass_tons=required_biomass_tons,
            ),
        )
    else:
        stages["biomass"] = StageResult(
            passed=False,
            reasons=["Skipped due to earlier stage failure."],
        ).to_dict()

    if ok:
        ok = _absorb(
            "tariff",
            filter_tariff(
                scenario,
                factory,
                config=cfg,
                consumer_category=consumer_category,
            ),
        )
    else:
        stages.setdefault(
            "tariff",
            StageResult(
                passed=False,
                reasons=["Skipped due to earlier stage failure."],
            ).to_dict(),
        )

    if ok:
        ok = _absorb(
            "industry_rules",
            filter_industry_rules(
                scenario,
                factory,
                config=cfg,
            ),
        )
    else:
        stages.setdefault(
            "industry_rules",
            StageResult(
                passed=False,
                reasons=["Skipped due to earlier stage failure."],
            ).to_dict(),
        )

    if ok:
        ok = _absorb(
            "finance",
            filter_financial_feasibility(
                scenario,
                factory,
                config=cfg,
                policy_output=policy_output,
            ),
        )
    else:
        stages.setdefault(
            "finance",
            StageResult(
                passed=False,
                reasons=["Skipped due to earlier stage failure."],
            ).to_dict(),
        )

    # Ensure all stage keys exist even on early exit paths
    for key in ("compatibility", "biomass", "tariff", "industry_rules", "finance"):
        stages.setdefault(
            key,
            StageResult(
                passed=False,
                reasons=["Stage not evaluated."],
            ).to_dict(),
        )

    feasible = ok and all(
        stages[k].get("passed") for k in stages
    )

    # Attach envelope onto a shallow scenario copy when dict-like
    result: dict[str, Any] = {
        "feasible": feasible,
        "filter_stages": stages,
        "rejection_reasons": rejection_reasons,
        "warnings": all_warnings,
        "evidence": all_evidence,
    }

    if isinstance(scenario, MutableMapping):
        enriched = dict(scenario)
        enriched.update(result)
        return enriched

    result["scenario_id"] = _get(scenario, "scenario_id")
    result["technology_sequence"] = _technology_sequence(scenario)
    return result


# ---------------------------------------------------------------------------
# 6. Batch filter
# ---------------------------------------------------------------------------


def filter_all_scenarios(
    scenarios: Iterable[Any],
    factory: Any,
    *,
    config: Optional[FilterConfig] = None,
    policy_output: Optional[Mapping[str, Any]] = None,
    required_biomass_tons: Optional[float] = None,
    consumer_category: Optional[str] = None,
    only_feasible: bool = False,
) -> list[dict[str, Any]]:
    """
    Apply ``filter_complete_scenario`` to every scenario.

    Parameters
    ----------
    only_feasible:
        When True, return only scenarios with feasible=True.
    """
    cfg = config or FilterConfig()
    results: list[dict[str, Any]] = []

    for scenario in scenarios:
        filtered = filter_complete_scenario(
            scenario,
            factory,
            config=cfg,
            policy_output=policy_output,
            required_biomass_tons=required_biomass_tons,
            consumer_category=consumer_category,
        )
        if only_feasible and not filtered.get("feasible"):
            continue
        results.append(filtered)

    return results


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

__all__ = [
    "FilterConfig",
    "StageResult",
    "filter_biomass_pathway",
    "filter_tariff",
    "filter_industry_rules",
    "filter_financial_feasibility",
    "filter_complete_scenario",
    "filter_all_scenarios",
]
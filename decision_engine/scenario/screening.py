# `decision_engine/scenario/scenario_generator.py`
from __future__ import annotations

from dataclasses import dataclass, field
from itertools import combinations
import importlib
from pathlib import Path
from typing import Any, Iterable, Mapping, Optional


# ============================================================================
# Repository paths
# ============================================================================

BASE_DIR = Path(__file__).resolve().parents[2]

POLICY_FILE = (
    BASE_DIR
    / "knowledge-base"
    / "policies"
    / "state_policies.json"
)

BUDGET_FILE = (
    BASE_DIR
    / "knowledge-base"
    / "constraints"
    / "budget.json"
)


# ============================================================================
# Generic normalization helpers
# ============================================================================


def normalize(value: Any) -> str:
    """Normalize identifiers into the repository's canonical style."""

    if value is None:
        return ""

    return (
        str(value)
        .strip()
        .lower()
        .replace("-", "_")
        .replace(" ", "_")
    )


def to_float(value: Any) -> Optional[float]:
    """Safely convert a value to float."""

    if value is None or value == "":
        return None

    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def to_bool(value: Any) -> Optional[bool]:
    """Convert common boolean representations to bool."""

    if isinstance(value, bool):
        return value

    if value is None:
        return None

    if isinstance(value, (int, float)):
        return bool(value)

    normalized = normalize(value)

    if normalized in {"true", "yes", "y", "1", "available", "supported"}:
        return True

    if normalized in {
        "false",
        "no",
        "n",
        "0",
        "unavailable",
        "unsupported",
    }:
        return False

    return None


def normalize_list(values: Any) -> list[str]:
    """Normalize an iterable into unique identifiers."""

    if values is None:
        return []

    if isinstance(values, str):
        values = [values]

    result: list[str] = []

    try:
        iterator = iter(values)
    except TypeError:
        return []

    for value in iterator:
        normalized = normalize(value)

        if normalized and normalized not in result:
            result.append(normalized)

    return result


# ============================================================================
# Technology extraction
# ============================================================================


TECHNOLOGY_ALIASES: dict[str, str] = {
    "heatpump": "heat_pump",
    "heat-pump": "heat_pump",
    "electricboiler": "electric_boiler",
    "electric-boiler": "electric_boiler",
    "biomass": "biomass_boiler",
    "biomass_boiler": "biomass_boiler",
    "solarthermal": "solar_thermal",
    "solarpv": "solar_pv",
    "thermalstorage": "thermal_storage",
    "whr": "waste_heat_recovery",
    "waste_heat": "waste_heat_recovery",
    "induction": "induction_furnace",
    "resistance": "resistance_furnace",
    "eaf": "electric_arc_furnace",
    "electric_arc": "electric_arc_furnace",
    "plasma": "plasma_technology",
}


def canonical_technology_id(item: Any) -> str:
    """
    Extract and canonicalize a technology ID.

    Supported input forms:
        "heat_pump"
        {"technology_id": "heat_pump"}
        {"id": "heat_pump"}
        {"technology": "heat_pump"}
        {"technology_name": "heat_pump"}
    """

    if isinstance(item, str):
        raw_id = item.strip()

    elif isinstance(item, Mapping):
        raw_value = (
            item.get("technology_id")
            or item.get("id")
            or item.get("technology")
            or item.get("technology_name")
        )

        if not isinstance(raw_value, str):
            raise ValueError(
                f"Unable to determine technology ID from: {item!r}"
            )

        raw_id = raw_value.strip()

    else:
        raise ValueError(
            f"Unsupported technology input: {item!r}"
        )

    if not raw_id:
        raise ValueError(
            f"Technology ID cannot be empty: {item!r}"
        )

    normalized = normalize(raw_id)

    return TECHNOLOGY_ALIASES.get(
        normalized,
        normalized,
    )


def technology_type(item: Any) -> str:
    """Infer a technology type from explicit metadata or ID."""

    if isinstance(item, Mapping):
        explicit = (
            item.get("technology_type")
            or item.get("type")
            or item.get("fuel_type")
            or item.get("resource_type")
        )

        if isinstance(explicit, str) and explicit.strip():
            return normalize(explicit)

    technology_id = canonical_technology_id(item)

    if "biomass" in technology_id:
        return "biomass"

    if "biogas" in technology_id:
        return "biogas"

    if (
        technology_id in {
            "heat_pump",
            "electric_boiler",
            "electric_furnace",
            "electric_heater",
            "induction_furnace",
            "resistance_furnace",
            "electric_arc_furnace",
            "plasma_technology",
        }
    ):
        return "electrification"

    if "solar" in technology_id:
        return "solar"

    if "thermal_storage" in technology_id:
        return "storage"

    if "waste_heat" in technology_id:
        return "waste_heat_recovery"

    return "other"


def technology_record(item: Any) -> dict[str, Any]:
    """
    Normalize a technology input while preserving its metadata.
    """

    technology_id = canonical_technology_id(item)

    if isinstance(item, Mapping):
        record = dict(item)
    else:
        record = {}

    record["technology_id"] = technology_id
    record.setdefault(
        "technology_type",
        technology_type(item),
    )

    return record


def normalize_feasible_technologies(
    feasible_technologies: Iterable[Any],
) -> list[dict[str, Any]]:
    """
    Normalize and deduplicate technology records.

    This helper remains intentionally permissive because older callers
    may pass strings or partially structured dictionaries.
    """

    normalized: list[dict[str, Any]] = []
    seen: set[str] = set()

    for item in feasible_technologies:
        try:
            record = technology_record(item)
        except ValueError:
            continue

        technology_id = record["technology_id"]

        if technology_id in seen:
            continue

        seen.add(technology_id)
        normalized.append(record)

    return normalized


# ============================================================================
# Screening result models
# ============================================================================


@dataclass
class ScreeningDecision:
    """Transparent decision for a single technology."""

    technology_id: str
    allowed: bool
    classification: str
    reasons: list[str] = field(default_factory=list)
    passed_checks: list[str] = field(default_factory=list)
    failed_checks: list[str] = field(default_factory=list)
    evidence: dict[str, Any] = field(default_factory=dict)
    source_provenance: list[Any] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert the decision into the project's dictionary style."""

        return {
            "technology": self.technology_id,
            "technology_id": self.technology_id,
            "allowed": self.allowed,
            "feasible": self.allowed,
            "classification": self.classification,
            "reasons": list(self.reasons),
            "passed_checks": list(self.passed_checks),
            "failed_checks": list(self.failed_checks),
            "evidence": dict(self.evidence),
            "source_provenance": list(self.source_provenance),
        }


# ============================================================================
# Existing project-engine adapters
# ============================================================================


class _ExistingEngineAdapter:
    """
    Adapter around the repository's current technical engines.

    This intentionally uses the current project modules rather than
    reproducing the same engineering rules inside the scenario generator.
    """

    def __init__(self) -> None:
        self._technology_filter = None
        self._industry_engine = None

        self._load_modules()

    def _load_modules(self) -> None:
        """Import existing modules safely."""

        try:
            self._technology_filter = importlib.import_module(
                "decision_engine.technology.technology_filter"
            )
        except Exception:
            self._technology_filter = None

        try:
            industry_module = importlib.import_module(
                "decision_engine.technology.industry_constraint_engine"
            )

            engine_class = getattr(
                industry_module,
                "IndustryConstraintEngine",
                None,
            )

            if engine_class is not None:
                try:
                    self._industry_engine = engine_class()
                except Exception:
                    self._industry_engine = None

        except Exception:
            self._industry_engine = None

    def technical_screen(
        self,
        technology: str,
        factory: Mapping[str, Any],
    ) -> dict[str, Any]:
        """
        Reuse the existing Unit 2.3 technology filter.

        If the legacy engine is unavailable, return an explicit
        "screening_unavailable" result rather than silently declaring
        the technology feasible.
        """

        if self._technology_filter is None:
            return {
                "technology": technology,
                "feasible": False,
                "checks": {},
                "reasons": [
                    "Technical screening engine is unavailable."
                ],
                "screening_error": True,
            }

        evaluate = getattr(
            self._technology_filter,
            "evaluate_technology",
            None,
        )

        if not callable(evaluate):
            return {
                "technology": technology,
                "feasible": False,
                "checks": {},
                "reasons": [
                    "Technical screening function is unavailable."
                ],
                "screening_error": True,
            }

        try:
            result = evaluate(
                technology=technology,
                factory=factory,
            )
        except Exception as exc:
            return {
                "technology": technology,
                "feasible": False,
                "checks": {},
                "reasons": [
                    (
                        f"Technical screening failed for "
                        f"'{technology}': {exc}"
                    )
                ],
                "screening_error": True,
            }

        if not isinstance(result, Mapping):
            return {
                "technology": technology,
                "feasible": False,
                "checks": {},
                "reasons": [
                    (
                        f"Technical screening returned an invalid "
                        f"result for '{technology}'."
                    )
                ],
                "screening_error": True,
            }

        return dict(result)

    def industry_screen(
        self,
        industry: str,
        technology: str,
        technical_result: Mapping[str, Any],
    ) -> dict[str, Any]:
        """
        Reuse the existing Unit 2.4 industry constraint engine.
        """

        if self._industry_engine is None:
            return {
                "allowed": False,
                "classification": "screening_unavailable",
                "reasons": [
                    "Industry constraint engine is unavailable."
                ],
                "operational_constraints": [],
                "cluster_recommendations": [],
            }

        try:
            result = self._industry_engine.evaluate(
                industry=industry,
                technology=technology,
                technical_feasible=technical_result.get("feasible"),
                technical_reasons=technical_result.get(
                    "reasons",
                    [],
                ),
            )
        except Exception as exc:
            return {
                "allowed": False,
                "classification": "screening_error",
                "reasons": [
                    (
                        f"Industry screening failed for "
                        f"'{technology}': {exc}"
                    )
                ],
                "operational_constraints": [],
                "cluster_recommendations": [],
            }

        if not isinstance(result, Mapping):
            return {
                "allowed": False,
                "classification": "screening_error",
                "reasons": [
                    (
                        f"Industry screening returned an invalid "
                        f"result for '{technology}'."
                    )
                ],
                "operational_constraints": [],
                "cluster_recommendations": [],
            }

        return dict(result)


# ============================================================================
# Knowledge-data loading
# ============================================================================


def _load_json_file(path: Path) -> Optional[dict[str, Any]]:
    """
    Load a JSON object.

    Missing or invalid optional data is represented by None so that the
    caller can apply a strict policy where the data is required.
    """

    if not path.exists():
        return None

    try:
        import json

        with path.open("r", encoding="utf-8") as file:
            value = json.load(file)

        if isinstance(value, dict):
            return value

    except Exception:
        return None

    return None


def load_policy_data() -> Optional[dict[str, Any]]:
    """Load verified state-policy data."""

    return _load_json_file(POLICY_FILE)


def load_budget_data() -> Optional[dict[str, Any]]:
    """Load repository financial/tariff metadata."""

    return _load_json_file(BUDGET_FILE)


# ============================================================================
# Factory extraction
# ============================================================================


def extract_industry(factory: Mapping[str, Any]) -> str:
    return normalize(
        factory.get("industry")
        or factory.get("industry_id")
        or factory.get("sector")
    )


def extract_state(factory: Mapping[str, Any]) -> str:
    return str(
        factory.get("state")
        or factory.get("state_name")
        or ""
    ).strip()


def extract_district(factory: Mapping[str, Any]) -> str:
    return str(
        factory.get("district")
        or factory.get("district_name")
        or ""
    ).strip()


def extract_temperature(factory: Mapping[str, Any]) -> Optional[float]:
    fields = (
        "required_process_temperature_c",
        "process_temperature_c",
        "process_temperature",
        "temperature_c",
        "temperature",
    )

    for field in fields:
        value = to_float(factory.get(field))

        if value is not None:
            return value

    return None


def extract_budget(factory: Mapping[str, Any]) -> Optional[float]:
    fields = (
        "budget_inr",
        "available_budget_inr",
        "capex_budget_inr",
        "investment_budget_inr",
    )

    for field in fields:
        value = to_float(factory.get(field))

        if value is not None:
            return value

    return None


def extract_grid_capacity(factory: Mapping[str, Any]) -> Optional[float]:
    fields = (
        "grid_capacity_kw",
        "available_grid_capacity_kw",
        "sanctioned_load_kw",
    )

    for field in fields:
        value = to_float(factory.get(field))

        if value is not None:
            return value

    return None


def extract_existing_load(factory: Mapping[str, Any]) -> float:
    fields = (
        "existing_electrical_load_kw",
        "current_electrical_load_kw",
        "peak_electrical_load_kw",
    )

    for field in fields:
        value = to_float(factory.get(field))

        if value is not None:
            return max(0.0, value)

    return 0.0


def extract_additional_grid_capacity(
    factory: Mapping[str, Any],
) -> float:
    fields = (
        "additional_grid_capacity_kw",
        "grid_upgrade_capacity_kw",
        "available_upgrade_capacity_kw",
    )

    for field in fields:
        value = to_float(factory.get(field))

        if value is not None:
            return max(0.0, value)

    return 0.0


def extract_roof_area(factory: Mapping[str, Any]) -> Optional[float]:
    fields = (
        "roof_area_m2",
        "roof_area_sqm",
        "available_roof_area_m2",
        "available_space_m2",
    )

    for field in fields:
        value = to_float(factory.get(field))

        if value is not None:
            return value

    return None


def extract_current_fuel(factory: Mapping[str, Any]) -> str:
    return normalize(
        factory.get("current_fuel")
        or factory.get("fuel")
        or factory.get("primary_fuel")
    )


# ============================================================================
# Resource evidence
# ============================================================================


def _explicit_resource_value(
    factory: Mapping[str, Any],
    technology: Mapping[str, Any],
    names: Iterable[str],
) -> Optional[bool]:
    """
    Return the first explicitly supplied resource boolean.

    Factory input has priority, then technology result metadata.
    """

    for name in names:

        if name in factory:
            return to_bool(factory.get(name))

        if name in technology:
            return to_bool(technology.get(name))

    return None


def biomass_supply_status(
    factory: Mapping[str, Any],
    technology_result: Mapping[str, Any],
) -> tuple[Optional[bool], str]:
    """
    Determine whether biomass supply is explicitly demonstrated.

    Accepted signals:
        biomass_supply_available
        biomass_available
        available_biomass
        surplus_biomass_tonnes
        biomass_availability
        biomass_assessment

    Important:
        Missing data is NOT interpreted as "available".
    """

    status = _explicit_resource_value(
        factory,
        technology_result,
        (
            "biomass_supply_available",
            "biomass_available",
            "fuel_available",
            "resource_available",
        ),
    )

    if status is not None:
        return status, "explicit_availability_flag"

    numeric_fields = (
        "available_biomass_tonnes",
        "annual_biomass_tonnes",
        "surplus_biomass_tonnes",
    )

    for field in numeric_fields:

        if field in factory:
            numeric = to_float(factory.get(field))

            if numeric is not None:
                return (
                    numeric > 0,
                    field,
                )

        if field in technology_result:
            numeric = to_float(
                technology_result.get(field)
            )

            if numeric is not None:
                return (
                    numeric > 0,
                    field,
                )

    assessment = technology_result.get(
        "biomass_assessment"
    )

    if isinstance(assessment, Mapping):

        explicit = (
            assessment.get("supply_available")
            or assessment.get("biomass_available")
            or assessment.get("available")
        )

        parsed = to_bool(explicit)

        if parsed is not None:
            return (
                parsed,
                "biomass_assessment",
            )

    return None, "not_available"


def solar_resource_status(
    factory: Mapping[str, Any],
    technology_result: Mapping[str, Any],
) -> tuple[Optional[bool], str]:

    status = _explicit_resource_value(
        factory,
        technology_result,
        (
            "solar_resource_available",
            "solar_available",
        ),
    )

    if status is not None:
        return status, "explicit_solar_flag"

    return None, "not_available"


def waste_heat_status(
    factory: Mapping[str, Any],
    technology_result: Mapping[str, Any],
) -> tuple[Optional[bool], str]:

    status = _explicit_resource_value(
        factory,
        technology_result,
        (
            "recoverable_waste_heat",
            "waste_heat_available",
            "waste_heat_source_available",
        ),
    )

    if status is not None:
        return status, "explicit_waste_heat_flag"

    numeric_fields = (
        "recoverable_waste_heat_kw",
        "waste_heat_available_kw",
        "recoverable_heat_kw",
    )

    for field in numeric_fields:

        if field in factory:
            numeric = to_float(factory.get(field))

            if numeric is not None:
                return (
                    numeric > 0,
                    field,
                )

    return None, "not_available"


# ============================================================================
# Candidate capacity / cost extraction
# ============================================================================


def extract_required_power_kw(
    factory: Mapping[str, Any],
    technology_id: str,
    technology_result: Mapping[str, Any],
) -> Optional[float]:
    """
    Extract technology-specific power requirement.

    No generic or invented power requirement is assumed.
    """

    technology_power_map = factory.get(
        "technology_required_power_kw"
    )

    if isinstance(technology_power_map, Mapping):

        mapped = to_float(
            technology_power_map.get(technology_id)
        )

        if mapped is not None:
            return max(0.0, mapped)

    fields = (
        "required_power_kw",
        "electrical_load_kw",
        "required_electrical_capacity_kw",
    )

    for field in fields:

        value = to_float(
            technology_result.get(field)
        )

        if value is not None:
            return max(0.0, value)

    return None


def extract_project_capex(
    technology_record_data: Mapping[str, Any],
) -> Optional[float]:
    """
    Extract a single candidate CapEx estimate only when the input already
    provides one.

    We do not invent midpoint values here.
    """

    direct_fields = (
        "capex_inr",
        "estimated_capex_inr",
        "project_capex_inr",
    )

    for field in direct_fields:
        value = to_float(
            technology_record_data.get(field)
        )

        if value is not None:
            return max(0.0, value)

    return None


# ============================================================================
# Financial / tariff evidence hooks
# ============================================================================


def tariff_available(
    factory: Mapping[str, Any],
) -> tuple[Optional[bool], str]:
    """
    Determine whether an applicable electricity tariff is explicitly known.

    This function intentionally does not invent tariff values.

    Accepted direct factory inputs:
        electricity_tariff_inr_per_kwh
        industrial_tariff_inr_per_kwh
        grid_tariff_inr_per_kwh

    Repository tariff data can also be surfaced by the application layer
    before calling the scenario generator.
    """

    fields = (
        "electricity_tariff_inr_per_kwh",
        "industrial_tariff_inr_per_kwh",
        "grid_tariff_inr_per_kwh",
    )

    for field in fields:

        value = to_float(
            factory.get(field)
        )

        if value is not None:
            return (
                value >= 0,
                field,
            )

    tariff_record = factory.get(
        "tariff"
    )

    if isinstance(tariff_record, Mapping):

        value = to_float(
            tariff_record.get(
                "energy_charge_inr_per_kwh"
            )
            or tariff_record.get(
                "inr_per_kwh"
            )
        )

        if value is not None:
            return (
                value >= 0,
                "factory_tariff_record",
            )

    # The repository contains a budget metadata layer with coverage
    # declarations, but this generator cannot safely derive a live tariff
    # from that metadata without knowing the exact tariff record schema.
    budget_data = load_budget_data()

    if budget_data is not None:

        coverage_gap = str(
            budget_data.get(
                "electricity_coverage_gap",
                "",
            )
        ).lower()

        state = extract_state(factory).lower()

        if state and state in coverage_gap:
            return (
                False,
                "repository_tariff_coverage_gap",
            )

    return None, "not_available"


# ============================================================================
# Policy eligibility
# ============================================================================


def _policy_rule_for_state(
    policy_data: Mapping[str, Any],
    state: str,
) -> Optional[Mapping[str, Any]]:
    """Return the verified policy object for a state."""

    states = policy_data.get(
        "states"
    )

    if not isinstance(states, Mapping):
        return None

    if state in states and isinstance(
        states[state],
        Mapping,
    ):
        return states[state]

    normalized_state = normalize(state)

    for state_name, rule in states.items():

        if not isinstance(rule, Mapping):
            continue

        if normalize(state_name) == normalized_state:
            return rule

    return None


def evaluate_policy_eligibility(
    factory: Mapping[str, Any],
    technology_id: str,
) -> tuple[Optional[bool], dict[str, Any], list[str]]:
    """
    Perform a conservative policy gate.

    Policy benefits must never be assumed.

    This screening stage only rejects when the data explicitly proves
    that the required benefit/eligibility condition is not satisfied.

    It may also return "unknown" when policy evidence is absent.

    The detailed financial application of incentives belongs later.
    """

    policy_data = load_policy_data()

    if policy_data is None:
        return (
            None,
            {
                "status": "unknown",
                "reason": "Policy knowledge base unavailable.",
            },
            [
                "Policy eligibility could not be verified."
            ],
        )

    critical_rules = policy_data.get(
        "critical_rules",
        {},
    )

    state_required = bool(
        critical_rules.get(
            "state_is_required",
            True,
        )
    )

    state = extract_state(factory)

    if state_required and not state:
        return (
            None,
            {
                "status": "unknown",
                "reason": "Factory state is required for policy screening.",
            },
            [
                "State is missing; location-based policy eligibility "
                "cannot be verified."
            ],
        )

    state_rule = _policy_rule_for_state(
        policy_data,
        state,
    )

    if state_rule is None:
        return (
            None,
            {
                "status": "unknown",
                "reason": (
                    f"No verified state policy rule exists for "
                    f"'{state}'."
                ),
            },
            [
                (
                    f"No verified state-specific policy rule exists "
                    f"for '{state}'."
                )
            ],
        )

    if str(
        state_rule.get(
            "policy_status",
            "",
        )
    ).strip().lower() in {
        "expired",
        "inactive",
        "closed",
    }:
        return (
            False,
            {
                "status": "rejected",
                "reason": (
                    f"State policy for '{state}' is not active."
                ),
            },
            [
                (
                    f"Policy screening rejected '{technology_id}' because "
                    f"the relevant state policy is inactive."
                )
            ],
        )

    # Policy is informational unless a direct explicit eligibility
    # condition is supplied in the factory or application layer.
    explicit_policy_required = to_bool(
        factory.get("policy_required")
    )

    if explicit_policy_required is True:

        requested_policy = normalize(
            factory.get(
                "required_policy_type"
            )
        )

        if not requested_policy:
            return (
                None,
                {
                    "status": "unknown",
                    "reason": (
                        "Factory requires policy support but no "
                        "policy type was specified."
                    ),
                },
                [
                    (
                        "Policy support is required but the required "
                        "policy type is missing."
                    )
                ],
            )

    return (
        True,
        {
            "status": "verified_state_policy_available",
            "state": state,
            "technology": technology_id,
        },
        [],
    )


# ============================================================================
# Explicit technology compatibility
# ============================================================================


def check_temperature_compatibility(
    technology_id: str,
    factory: Mapping[str, Any],
    technical_result: Mapping[str, Any],
    technology_record_data: Mapping[str, Any],
) -> tuple[bool, str]:
    """
    Explicitly verify process temperature against known technology limits.

    The existing technical engine remains authoritative; this is an
    additional fail-safe guard inside Unit 2.8.
    """

    required_temperature = extract_temperature(factory)

    if required_temperature is None:
        return (
            False,
            (
                "Process temperature is missing; technology "
                "temperature feasibility cannot be established."
            ),
        )

    lower = None
    upper = None

    temperature_range = technology_record_data.get(
        "temperature_range_c"
    )

    if (
        isinstance(temperature_range, (list, tuple))
        and len(temperature_range) >= 2
    ):
        lower = to_float(
            temperature_range[0]
        )
        upper = to_float(
            temperature_range[1]
        )

    if upper is None:
        upper = to_float(
            technical_result.get(
                "temperature_limit_c"
            )
        )

    if upper is None:
        return (
            False,
            (
                f"No verified maximum temperature is available for "
                f"'{technology_id}'."
            ),
        )

    if required_temperature > upper:
        return (
            False,
            (
                f"Required process temperature "
                f"{required_temperature:g}°C exceeds the verified "
                f"{technology_id} limit of {upper:g}°C."
            ),
        )

    if lower is not None and required_temperature < lower:
        return (
            False,
            (
                f"Required process temperature "
                f"{required_temperature:g}°C is below the lower "
                f"operating range of {lower:g}°C for '{technology_id}'."
            ),
        )

    return (
        True,
        (
            f"Process temperature {required_temperature:g}°C is within "
            f"the verified technology range."
        ),
    )


def check_resource_compatibility(
    technology_id: str,
    technology_record_data: Mapping[str, Any],
    factory: Mapping[str, Any],
    technical_result: Mapping[str, Any],
) -> tuple[bool, str, dict[str, Any]]:
    """
    Apply resource-specific hard gates.

    Biomass, solar, and waste-heat systems require explicit evidence.
    """

    tech_type = technology_type(
        technology_record_data
    )

    if tech_type == "biomass" or "biomass" in technology_id:
        available, source = biomass_supply_status(
            factory,
            technical_result,
        )

        if available is False:
            return (
                False,
                "Biomass supply is explicitly unavailable.",
                {
                    "resource": "biomass",
                    "available": False,
                    "evidence_source": source,
                },
            )

        if available is None:
            return (
                False,
                (
                    "Biomass technology requires verified biomass "
                    "availability; none was supplied."
                ),
                {
                    "resource": "biomass",
                    "available": None,
                    "evidence_source": source,
                },
            )

        return (
            True,
            "Verified biomass supply is available.",
            {
                "resource": "biomass",
                "available": True,
                "evidence_source": source,
            },
        )

    if tech_type == "solar" or "solar_thermal" in technology_id:
        available, source = solar_resource_status(
            factory,
            technical_result,
        )

        if available is False:
            return (
                False,
                "Required solar resource is explicitly unavailable.",
                {
                    "resource": "solar",
                    "available": False,
                    "evidence_source": source,
                },
            )

        if available is None:
            return (
                False,
                (
                    "Solar-based technology requires verified solar "
                    "resource availability."
                ),
                {
                    "resource": "solar",
                    "available": None,
                    "evidence_source": source,
                },
            )

        return (
            True,
            "Verified solar resource is available.",
            {
                "resource": "solar",
                "available": True,
                "evidence_source": source,
            },
        )

    if (
        tech_type == "waste_heat_recovery"
        or technology_id == "waste_heat_recovery"
    ):
        available, source = waste_heat_status(
            factory,
            technical_result,
        )

        if available is False:
            return (
                False,
                "Recoverable waste heat is explicitly unavailable.",
                {
                    "resource": "waste_heat",
                    "available": False,
                    "evidence_source": source,
                },
            )

        if available is None:
            return (
                False,
                (
                    "Waste-heat recovery requires verified recoverable "
                    "waste-heat availability."
                ),
                {
                    "resource": "waste_heat",
                    "available": None,
                    "evidence_source": source,
                },
            )

        return (
            True,
            "Verified recoverable waste heat is available.",
            {
                "resource": "waste_heat",
                "available": True,
                "evidence_source": source,
            },
        )

    return (
        True,
        "No dedicated local resource gate is required.",
        {},
    )


def check_grid_compatibility(
    technology_id: str,
    factory: Mapping[str, Any],
    technical_result: Mapping[str, Any],
    technology_record_data: Mapping[str, Any],
) -> tuple[bool, str, dict[str, Any]]:
    """
    Verify grid feasibility for electricity-dependent technologies.
    """

    tech_type = technology_type(
        technology_record_data
    )

    requires_grid = (
        tech_type == "electrification"
        or bool(
            technical_result.get(
                "checks",
                {},
            ).get(
                "grid_capacity",
                False,
            )
        )
    )

    if not requires_grid:
        return (
            True,
            "No grid-capacity gate applies.",
            {},
        )

    available = extract_grid_capacity(
        factory
    )

    required_power = extract_required_power_kw(
        factory,
        technology_id,
        technical_result,
    )

    if available is None:
        return (
            False,
            (
                "Grid capacity is required but was not supplied; "
                "electrical feasibility cannot be established."
            ),
            {
                "available_grid_capacity_kw": None,
                "required_power_kw": required_power,
            },
        )

    if required_power is None:
        return (
            False,
            (
                f"Verified electrical load requirement for "
                f"'{technology_id}' is missing."
            ),
            {
                "available_grid_capacity_kw": available,
                "required_power_kw": None,
            },
        )

    existing_load = extract_existing_load(
        factory
    )
    additional_upgrade = extract_additional_grid_capacity(
        factory
    )

    required_total = (
        existing_load
        + required_power
    )

    effective_capacity = (
        available
        + additional_upgrade
    )

    if required_total > effective_capacity:
        return (
            False,
            (
                f"Electrical capacity is insufficient: "
                f"required {required_total:g} kW, "
                f"available {effective_capacity:g} kW."
            ),
            {
                "existing_load_kw": existing_load,
                "required_power_kw": required_power,
                "available_grid_capacity_kw": available,
                "additional_upgrade_kw": additional_upgrade,
            },
        )

    return (
        True,
        (
            f"Electrical capacity is sufficient: "
            f"required {required_total:g} kW, "
            f"available {effective_capacity:g} kW."
        ),
        {
            "existing_load_kw": existing_load,
            "required_power_kw": required_power,
            "available_grid_capacity_kw": available,
            "additional_upgrade_kw": additional_upgrade,
        },
    )


def check_space_compatibility(
    technology_id: str,
    factory: Mapping[str, Any],
    technical_result: Mapping[str, Any],
    technology_record_data: Mapping[str, Any],
) -> tuple[bool, str, dict[str, Any]]:
    """
    Verify roof/space requirements for solar-related technologies.
    """

    requires_roof = bool(
        technology_record_data.get(
            "requires_roof",
            False,
        )
    )

    if not requires_roof:
        return (
            True,
            "No dedicated roof-space gate applies.",
            {},
        )

    available_area = extract_roof_area(
        factory
    )

    if available_area is None:
        return (
            False,
            (
                f"'{technology_id}' requires available roof/space "
                "information, but it was not provided."
            ),
            {
                "available_roof_area_m2": None,
            },
        )

    minimum_area = to_float(
        technology_record_data.get(
            "minimum_roof_area_m2"
        )
    )

    if minimum_area is None:

        minimum_area = to_float(
            technical_result.get(
                "minimum_roof_area_m2"
            )
        )

    if minimum_area is None:
        return (
            False,
            (
                f"Verified minimum area requirement for "
                f"'{technology_id}' is missing."
            ),
            {
                "available_roof_area_m2": available_area,
                "minimum_roof_area_m2": None,
            },
        )

    if available_area < minimum_area:
        return (
            False,
            (
                f"Insufficient roof/space area: "
                f"requires {minimum_area:g} m², "
                f"available {available_area:g} m²."
            ),
            {
                "available_roof_area_m2": available_area,
                "minimum_roof_area_m2": minimum_area,
            },
        )

    return (
        True,
        (
            f"Roof/space area is sufficient: "
            f"{available_area:g} m² available versus "
            f"{minimum_area:g} m² required."
        ),
        {
            "available_roof_area_m2": available_area,
            "minimum_roof_area_m2": minimum_area,
        },
    )


def check_tariff_viability(
    technology_id: str,
    factory: Mapping[str, Any],
    technology_record_data: Mapping[str, Any],
) -> tuple[bool, str, dict[str, Any]]:
    """
    Apply the tariff gate only when the technology depends materially
    on electricity and a tariff-sensitive decision is required.

    The purpose here is to prevent obviously impossible or unevaluable
    electrical pathways from being turned into fake scenarios.

    We do NOT declare a technology "cheap" here.
    """

    tech_type = technology_type(
        technology_record_data
    )

    electricity_dependent = (
        tech_type == "electrification"
        or technology_id in {
            "heat_pump",
            "electric_boiler",
            "electric_furnace",
            "electric_heater",
            "induction_furnace",
            "resistance_furnace",
            "electric_arc_furnace",
        }
    )

    if not electricity_dependent:
        return (
            True,
            "No electricity-tariff feasibility gate applies.",
            {},
        )

    tariff_ok, tariff_source = tariff_available(
        factory
    )

    if tariff_ok is False:
        return (
            False,
            "Required electricity tariff information is unavailable.",
            {
                "tariff_available": False,
                "tariff_source": tariff_source,
            },
        )

    if tariff_ok is None:
        return (
            False,
            (
                f"Electricity tariff for '{technology_id}' is unknown; "
                "economic feasibility cannot be established."
            ),
            {
                "tariff_available": None,
                "tariff_source": tariff_source,
            },
        )

    return (
        True,
        "Applicable electricity tariff evidence is available.",
        {
            "tariff_available": True,
            "tariff_source": tariff_source,
        },
    )


def check_budget_feasibility(
    technology_id: str,
    factory: Mapping[str, Any],
    technology_record_data: Mapping[str, Any],
) -> tuple[Optional[bool], str, dict[str, Any]]:
    """
    Apply a strict budget check only when both factory budget and a
    technology-specific CapEx are known.

    A missing CapEx does not become a fabricated pass.
    """

    budget = extract_budget(
        factory
    )

    capex = extract_project_capex(
        technology_record_data
    )

    if budget is None:
        return (
            None,
            "Factory budget was not supplied.",
            {
                "budget_inr": None,
                "capex_inr": capex,
            },
        )

    if capex is None:
        return (
            None,
            (
                f"CapEx for '{technology_id}' was not supplied, "
                "so budget feasibility cannot yet be verified."
            ),
            {
                "budget_inr": budget,
                "capex_inr": None,
            },
        )

    if capex > budget:
        return (
            False,
            (
                f"Technology CapEx exceeds factory budget: "
                f"{capex:,.0f} INR > {budget:,.0f} INR."
            ),
            {
                "budget_inr": budget,
                "capex_inr": capex,
            },
        )

    return (
        True,
        (
            f"Technology CapEx fits the factory budget: "
            f"{capex:,.0f} INR <= {budget:,.0f} INR."
        ),
        {
            "budget_inr": budget,
            "capex_inr": capex,
        },
    )


# ============================================================================
# Strict screening engine
# ============================================================================


class TechnologyScreeningEngine:
    """
    Research-backed technology screening gate.

    Hard rule
    ---------
    A technology only survives when every required hard gate passes.

    Unknown critical evidence:
        reject the candidate.

    This is intentionally stricter than the legacy technology filter,
    because Unit 2.8 must not generate fake scenarios.
    """

    def __init__(
        self,
        existing_engine: Optional[_ExistingEngineAdapter] = None,
    ) -> None:

        self.existing_engine = (
            existing_engine
            or _ExistingEngineAdapter()
        )

    def screen_one(
        self,
        factory: Mapping[str, Any],
        candidate: Any,
    ) -> dict[str, Any]:
        """
        Strictly screen one candidate technology.
        """

        record = technology_record(
            candidate
        )

        technology_id = record[
            "technology_id"
        ]

        industry = extract_industry(
            factory
        )

        reasons: list[str] = []
        passed_checks: list[str] = []
        failed_checks: list[str] = []
        evidence: dict[str, Any] = {}

        # --------------------------------------------------------------
        # Gate 1 — Basic input completeness
        # --------------------------------------------------------------

        if not industry:
            reasons.append(
                "Factory industry is required for technology screening."
            )
            failed_checks.append(
                "industry_input"
            )
        else:
            passed_checks.append(
                "industry_input"
            )

        # --------------------------------------------------------------
        # Gate 2 — Existing technical engine
        # --------------------------------------------------------------

        technical_result = (
            self.existing_engine.technical_screen(
                technology=technology_id,
                factory=factory,
            )
        )

        evidence["technical_screening"] = technical_result

        if not technical_result.get(
            "feasible",
            False,
        ):
            failed_checks.append(
                "technical_screening"
            )

            reasons.extend(
                str(reason)
                for reason in technical_result.get(
                    "reasons",
                    [],
                )
            )

        else:
            passed_checks.append(
                "technical_screening"
            )

        # --------------------------------------------------------------
        # Gate 3 — Industry-specific decision layer
        # --------------------------------------------------------------

        if industry:
            industry_result = (
                self.existing_engine.industry_screen(
                    industry=industry,
                    technology=technology_id,
                    technical_result=technical_result,
                )
            )

            evidence["industry_screening"] = (
                industry_result
            )

            if not industry_result.get(
                "allowed",
                False,
            ):
                failed_checks.append(
                    "industry_screening"
                )

                industry_reasons = (
                    industry_result.get(
                        "reasons",
                        [],
                    )
                )

                if not industry_reasons:
                    industry_reasons = [
                        (
                            f"Technology '{technology_id}' "
                            f"is not industry-compatible."
                        )
                    ]

                reasons.extend(
                    str(reason)
                    for reason in industry_reasons
                )

            else:
                passed_checks.append(
                    "industry_screening"
                )

        # --------------------------------------------------------------
        # Gate 4 — Temperature
        # --------------------------------------------------------------

        temperature_ok, temperature_reason = (
            check_temperature_compatibility(
                technology_id=technology_id,
                factory=factory,
                technical_result=technical_result,
                technology_record_data=record,
            )
        )

        evidence["temperature"] = {
            "ok": temperature_ok,
            "reason": temperature_reason,
            "process_temperature_c": (
                extract_temperature(factory)
            ),
        }

        if temperature_ok:
            passed_checks.append(
                "temperature"
            )
        else:
            failed_checks.append(
                "temperature"
            )
            reasons.append(
                temperature_reason
            )

        # --------------------------------------------------------------
        # Gate 5 — Resource / biomass / solar / WHR
        # --------------------------------------------------------------

        resource_ok, resource_reason, resource_evidence = (
            check_resource_compatibility(
                technology_id=technology_id,
                technology_record_data=record,
                factory=factory,
                technical_result=technical_result,
            )
        )

        evidence["resource"] = resource_evidence

        if resource_ok:
            passed_checks.append(
                "resource"
            )
        else:
            failed_checks.append(
                "resource"
            )
            reasons.append(
                resource_reason
            )

        # --------------------------------------------------------------
        # Gate 6 — Grid
        # --------------------------------------------------------------

        grid_ok, grid_reason, grid_evidence = (
            check_grid_compatibility(
                technology_id=technology_id,
                factory=factory,
                technical_result=technical_result,
                technology_record_data=record,
            )
        )

        evidence["grid"] = grid_evidence

        if grid_ok:
            passed_checks.append(
                "grid_capacity"
            )
        else:
            failed_checks.append(
                "grid_capacity"
            )
            reasons.append(
                grid_reason
            )

        # --------------------------------------------------------------
        # Gate 7 — Space
        # --------------------------------------------------------------

        space_ok, space_reason, space_evidence = (
            check_space_compatibility(
                technology_id=technology_id,
                factory=factory,
                technical_result=technical_result,
                technology_record_data=record,
            )
        )

        evidence["space"] = space_evidence

        if space_ok:
            passed_checks.append(
                "space"
            )
        else:
            failed_checks.append(
                "space"
            )
            reasons.append(
                space_reason
            )

        # --------------------------------------------------------------
        # Gate 8 — Policy
        # --------------------------------------------------------------

        policy_ok, policy_evidence, policy_reasons = (
            evaluate_policy_eligibility(
                factory=factory,
                technology_id=technology_id,
            )
        )

        evidence["policy"] = (
            policy_evidence
        )

        # Policy UNKNOWN is not automatically a rejection unless the
        # factory explicitly requires policy support.
        policy_required = (
            to_bool(
                factory.get(
                    "policy_required"
                )
            )
            is True
        )

        if policy_ok is False:
            failed_checks.append(
                "policy"
            )
            reasons.extend(
                policy_reasons
            )

        elif policy_ok is True:
            passed_checks.append(
                "policy"
            )

        elif policy_required:
            failed_checks.append(
                "policy"
            )
            reasons.extend(
                policy_reasons
            )

        else:
            evidence["policy"]["status"] = (
                "unknown_but_not_required_for_screening"
            )

            passed_checks.append(
                "policy"
            )

        # --------------------------------------------------------------
        # Gate 9 — Tariff
        # --------------------------------------------------------------

        tariff_ok, tariff_reason, tariff_evidence = (
            check_tariff_viability(
                technology_id=technology_id,
                factory=factory,
                technology_record_data=record,
            )
        )

        evidence["tariff"] = tariff_evidence

        if tariff_ok:
            passed_checks.append(
                "tariff"
            )
        else:
            failed_checks.append(
                "tariff"
            )
            reasons.append(
                tariff_reason
            )

        # --------------------------------------------------------------
        # Gate 10 — Budget
        # --------------------------------------------------------------

        budget_ok, budget_reason, budget_evidence = (
            check_budget_feasibility(
                technology_id=technology_id,
                factory=factory,
                technology_record_data=record,
            )
        )

        evidence["budget"] = budget_evidence

        if budget_ok is False:
            failed_checks.append(
                "budget"
            )
            reasons.append(
                budget_reason
            )

        elif budget_ok is True:
            passed_checks.append(
                "budget"
            )

        else:
            # Budget is a financial gate only when explicit inputs exist.
            # Unknown is preserved rather than treated as a false claim.
            evidence["budget"]["status"] = (
                "unknown"
            )

        # --------------------------------------------------------------
        # Final result
        # --------------------------------------------------------------

        allowed = (
            len(failed_checks) == 0
        )

        classification = (
            "feasible"
            if allowed
            else "rejected"
        )

        # Deduplicate reasons while preserving order.
        unique_reasons: list[str] = []

        for reason in reasons:
            cleaned = str(
                reason
            ).strip()

            if cleaned and cleaned not in unique_reasons:
                unique_reasons.append(
                    cleaned
                )

        provenance: list[Any] = []

        # Existing technical source citation.
        technical_citation = technical_result.get(
            "source_citation"
        )

        if technical_citation:
            provenance.append(
                technical_citation
            )

        # Existing industry source.
        industry_source = (
            evidence.get(
                "industry_screening",
                {},
            ).get(
                "source"
            )
            if isinstance(
                evidence.get(
                    "industry_screening"
                ),
                Mapping,
            )
            else None
        )

        if industry_source:
            provenance.append(
                industry_source
            )

        if not allowed and not unique_reasons:
            unique_reasons.append(
                (
                    f"Technology '{technology_id}' failed one or more "
                    "screening gates."
                )
            )

        decision = ScreeningDecision(
            technology_id=technology_id,
            allowed=allowed,
            classification=classification,
            reasons=unique_reasons,
            passed_checks=passed_checks,
            failed_checks=failed_checks,
            evidence=evidence,
            source_provenance=provenance,
        )

        result = decision.to_dict()

        # Keep the full input record available downstream. This allows
        # scenario generation and finance to retain the engineering data
        # without reloading the technology profile.
        result["technology_record"] = record

        result["industry"] = industry
        result["state"] = extract_state(
            factory
        )
        result["district"] = extract_district(
            factory
        )

        return result

    def screen(
        self,
        factory: Mapping[str, Any],
        candidates: Iterable[Any],
    ) -> dict[str, Any]:
        """
        Screen all candidates and split them into feasible/rejected.
        """

        normalized_candidates = (
            normalize_feasible_technologies(
                candidates
            )
        )

        results: list[dict[str, Any]] = []

        for candidate in normalized_candidates:
            results.append(
                self.screen_one(
                    factory=factory,
                    candidate=candidate,
                )
            )

        feasible = [
            result
            for result in results
            if result["allowed"]
        ]

        rejected = [
            result
            for result in results
            if not result["allowed"]
        ]

        return {
            "feasible": feasible,
            "rejected": rejected,
            "total_evaluated": len(results),
            "total_feasible": len(feasible),
            "total_rejected": len(rejected),
        }


# ============================================================================
# Public screening API
# ============================================================================


def screen_technology(
    technology: Any,
    factory: Mapping[str, Any],
) -> dict[str, Any]:
    """
    Public single-technology screening helper.
    """

    engine = TechnologyScreeningEngine()

    return engine.screen_one(
        factory=factory,
        candidate=technology,
    )


def screen_technologies(
    factory: Mapping[str, Any],
    candidates: Iterable[Any],
) -> dict[str, Any]:
    """
    Public batch screening helper.
    """

    engine = TechnologyScreeningEngine()

    return engine.screen(
        factory=factory,
        candidates=candidates,
    )


# ============================================================================
# Scenario construction
# ============================================================================


def _pathway(
    technologies: list[dict[str, Any]],
    pathway_type: str,
    *,
    reason: Optional[str] = None,
    metadata: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    """
    Build the shared pathway contract.

    Only screened technologies should reach this function.
    """

    technology_ids = [
        technology["technology_id"]
        for technology in technologies
    ]

    pathway: dict[str, Any] = {
        "technologies": technology_ids,
        "technology_sequence": technology_ids,
        "pathway_type": pathway_type,
        "feasible": True,
        "provenance": {
            "technology_ids": technology_ids,
            "technology_types": [
                technology.get(
                    "technology_type",
                    "other",
                )
                for technology in technologies
            ],
            "screening_evidence": [
                technology.get(
                    "screening",
                    {}
                )
                for technology in technologies
            ],
        },
    }

    if reason:
        pathway["reason"] = reason

    if metadata:
        pathway["scenario_metadata"] = metadata

    return pathway


def _is_biomass(
    item: Mapping[str, Any],
) -> bool:
    """Return True for biomass technologies."""

    return (
        technology_type(item) == "biomass"
        or "biomass" in canonical_technology_id(item)
    )


def _is_biogas(
    item: Mapping[str, Any],
) -> bool:
    """Return True for biogas technologies."""

    return (
        "biogas" in canonical_technology_id(item)
    )


def _is_storage(
    item: Mapping[str, Any],
) -> bool:
    """Return True for thermal-storage technologies."""

    return (
        canonical_technology_id(item)
        == "thermal_storage"
    )


def _compatibility_map(
    technology_record_data: Mapping[str, Any],
    field_name: str,
) -> set[str]:
    """
    Read technology compatibility metadata.

    Compatibility metadata is used as a scenario-generation gate.
    """

    values = technology_record_data.get(
        field_name,
        [],
    )

    return set(
        normalize_list(values)
    )


def _pair_is_meaningful(
    first: Mapping[str, Any],
    second: Mapping[str, Any],
) -> bool:
    """
    Determine whether two screened technologies form a meaningful
    two-technology pathway.

    This is intentionally data-driven.
    """

    first_id = canonical_technology_id(
        first
    )
    second_id = canonical_technology_id(
        second
    )

    if first_id == second_id:
        return False

    first_profile = (
        first.get(
            "technology_record",
            first,
        )
    )
    second_profile = (
        second.get(
            "technology_record",
            second,
        )
    )

    first_compatible = (
        _compatibility_map(
            first_profile,
            "compatible_with",
        )
    )

    second_compatible = (
        _compatibility_map(
            second_profile,
            "compatible_with",
        )
    )

    first_incompatible = (
        _compatibility_map(
            first_profile,
            "incompatible_with",
        )
    )

    second_incompatible = (
        _compatibility_map(
            second_profile,
            "incompatible_with",
        )
    )

    if (
        second_id in first_incompatible
        or first_id in second_incompatible
    ):
        return False

    if (
        second_id in first_compatible
        or first_id in second_compatible
    ):
        return True

    # Solar PV and thermal-storage/electrification pairings are only
    # meaningful when explicitly represented as a compatible pathway.
    if (
        first_id == "solar_pv"
        and second_id
        in {
            "heat_pump",
            "electric_boiler",
            "thermal_storage",
        }
    ):
        return True

    if (
        second_id == "solar_pv"
        and first_id
        in {
            "heat_pump",
            "electric_boiler",
            "thermal_storage",
        }
    ):
        return True

    return False


def _attach_screening(
    result: Mapping[str, Any],
) -> dict[str, Any]:
    """
    Prepare a screened technology record for scenario generation.
    """

    technology_id = result[
        "technology_id"
    ]

    return {
        "technology_id": technology_id,
        "technology_type": result.get(
            "technology_record",
            {},
        ).get(
            "technology_type",
            technology_type(
                technology_id
            ),
        ),
        "technology_record": dict(
            result.get(
                "technology_record",
                {},
            )
        ),
        "screening": dict(
            result
        ),
    }


def _generate_biomass_scenarios(
    feasible_technologies: list[dict[str, Any]],
    maximum_scenarios: int,
) -> list[dict[str, Any]]:
    """
    Generate biomass pathways ONLY after biomass has passed strict
    resource screening.
    """

    biomass = [
        item
        for item in feasible_technologies
        if _is_biomass(item)
    ]

    non_biomass = [
        item
        for item in feasible_technologies
        if not _is_biomass(item)
    ]

    scenarios: list[dict[str, Any]] = []

    for biomass_technology in biomass:

        scenarios.append(
            _pathway(
                [biomass_technology],
                pathway_type="biomass_only",
                reason=(
                    "Biomass technology passed the strict screening "
                    "engine including verified biomass availability."
                ),
                metadata={
                    "biomass_aware": True,
                    "screened_resource": (
                        biomass_technology[
                            "screening"
                        ].get(
                            "evidence",
                            {},
                        ).get(
                            "resource",
                            {},
                        )
                    ),
                },
            )
        )

        if len(scenarios) >= maximum_scenarios:
            return scenarios[:maximum_scenarios]

    for biomass_technology in biomass:

        for supporting_technology in non_biomass:

            if _is_biogas(
                supporting_technology
            ):
                continue

            if not _pair_is_meaningful(
                biomass_technology,
                supporting_technology,
            ):
                continue

            scenarios.append(
                _pathway(
                    [
                        biomass_technology,
                        supporting_technology,
                    ],
                    pathway_type="biomass_hybrid",
                    reason=(
                        "Both technologies passed screening and the "
                        "knowledge base marks the combination as compatible."
                    ),
                    metadata={
                        "biomass_aware": True,
                        "compatibility_evidence": True,
                    },
                )
            )

            if len(scenarios) >= maximum_scenarios:
                return scenarios[:maximum_scenarios]

    return scenarios[:maximum_scenarios]


def generate_candidate_pathways(
    feasible_technologies: list[Any],
    minimum_scenarios: int = 3,
    maximum_scenarios: int = 5,
    *,
    include_biomass_scenarios: bool = True,
    factory: Optional[Mapping[str, Any]] = None,
) -> list[dict[str, Any]]:
    """
    Generate meaningful pathways from STRICTLY SCREENED technologies.

    Backward-compatible behavior:
        - When factory is supplied:
            candidates are screened again before generation.
        - When factory is not supplied:
            the function requires the supplied items to already be
            explicitly marked as feasible/allowed.

    This prevents the generator from blindly treating arbitrary
    technology names as feasible.

    Generation order
    ----------------
    1. biomass-only / biomass-hybrid pathways
    2. single technology pathways
    3. meaningful compatible hybrids
    """

    if minimum_scenarios < 1:
        raise ValueError(
            "minimum_scenarios must be at least 1."
        )

    if maximum_scenarios < minimum_scenarios:
        raise ValueError(
            "maximum_scenarios cannot be smaller than "
            "minimum_scenarios."
        )

    # --------------------------------------------------------------
    # If a factory is supplied, force strict screening.
    # --------------------------------------------------------------

    if factory is not None:

        screening = screen_technologies(
            factory=factory,
            candidates=feasible_technologies,
        )

        technology_inputs = [
            _attach_screening(
                result
            )
            for result in screening["feasible"]
        ]

    else:

        normalized = normalize_feasible_technologies(
            feasible_technologies
        )

        technology_inputs = []

        for item in normalized:

            already_screened = item.get(
                "screening"
            )

            explicitly_feasible = (
                item.get(
                    "feasible"
                ) is True
                or item.get(
                    "allowed"
                ) is True
                or (
                    isinstance(
                        already_screened,
                        Mapping,
                    )
                    and already_screened.get(
                        "feasible"
                    ) is True
                    and already_screened.get(
                        "allowed"
                    ) is True
                )
            )

            if not explicitly_feasible:
                raise ValueError(
                    (
                        f"Technology '{item['technology_id']}' is not "
                        "explicitly screened as feasible. Provide the "
                        "factory to generate scenarios so Unit 2.8 "
                        "can perform strict screening."
                    )
                )

            technology_inputs.append(
                item
            )

    if len(technology_inputs) < minimum_scenarios:
        raise ValueError(
            f"Only {len(technology_inputs)} screened technologies "
            f"survived; at least {minimum_scenarios} are required "
            "to generate the requested scenario set."
        )

    candidates: list[dict[str, Any]] = []

    # --------------------------------------------------------------
    # 1. Biomass-aware candidates
    # --------------------------------------------------------------

    if include_biomass_scenarios:

        biomass_scenarios = (
            _generate_biomass_scenarios(
                feasible_technologies=technology_inputs,
                maximum_scenarios=maximum_scenarios,
            )
        )

        for scenario in biomass_scenarios:

            if scenario not in candidates:
                candidates.append(
                    scenario
                )

            if len(candidates) >= maximum_scenarios:
                return candidates[
                    :maximum_scenarios
                ]

    # --------------------------------------------------------------
    # 2. Single-technology candidates
    # --------------------------------------------------------------

    for technology in technology_inputs:

        if _is_biomass(technology):
            pathway_type = "biomass_only"

        elif _is_biogas(technology):
            pathway_type = "biogas_only"

        elif _is_storage(technology):
            # Storage is technically screened, but it is generally an
            # enabling technology. Its standalone scenario should not
            # be generated unless explicitly configured as such.
            continue

        else:
            pathway_type = "single_technology"

        scenario = _pathway(
            [technology],
            pathway_type=pathway_type,
            metadata={
                "strict_screening_passed": True,
                "screening_evidence": technology[
                    "screening"
                ],
            },
        )

        if scenario not in candidates:
            candidates.append(
                scenario
            )

        if len(candidates) >= maximum_scenarios:
            break

    # --------------------------------------------------------------
    # 3. Meaningful two-technology hybrids
    # --------------------------------------------------------------

    if len(candidates) < maximum_scenarios:

        for technology_a, technology_b in combinations(
            technology_inputs,
            2,
        ):

            if not _pair_is_meaningful(
                technology_a,
                technology_b,
            ):
                continue

            a_biomass = _is_biomass(
                technology_a
            )
            b_biomass = _is_biomass(
                technology_b
            )

            a_biogas = _is_biogas(
                technology_a
            )
            b_biogas = _is_biogas(
                technology_b
            )

            if (
                a_biomass
                and b_biogas
            ) or (
                a_biogas
                and b_biomass
            ):
                continue

            if a_biomass or b_biomass:
                pathway_type = "biomass_hybrid"

            elif a_biogas or b_biogas:
                pathway_type = "biogas_hybrid"

            else:
                pathway_type = "technology_hybrid"

            scenario = _pathway(
                [
                    technology_a,
                    technology_b,
                ],
                pathway_type=pathway_type,
                reason=(
                    "Both technologies passed screening and their "
                    "knowledge-base compatibility rules permit the pairing."
                ),
                metadata={
                    "strict_screening_passed": True,
                    "compatibility_checked": True,
                },
            )

            if scenario not in candidates:
                candidates.append(
                    scenario
                )

            if len(candidates) >= maximum_scenarios:
                break

    if len(candidates) < minimum_scenarios:
        raise ValueError(
            (
                f"Only {len(candidates)} meaningful scenario candidates "
                f"could be generated from the screened technologies; "
                f"required at least {minimum_scenarios}."
            )
        )

    return candidates[
        :maximum_scenarios
    ]


# ============================================================================
# Backward-compatible biogas calculation
# ============================================================================


def generate_biogas_scenario(
    heat_demand_kwh_day: float,
    biogas_energy_content_kwh_m3: float,
    boiler_efficiency: float,
    biogas_emission_factor_kg_co2_m3: float,
) -> dict[str, Any]:
    """
    Preserve the existing biogas scenario calculation contract.
    """

    if heat_demand_kwh_day < 0:
        raise ValueError(
            "heat_demand_kwh_day cannot be negative."
        )

    if biogas_energy_content_kwh_m3 <= 0:
        raise ValueError(
            "biogas_energy_content_kwh_m3 must be greater than zero."
        )

    if not 0 < boiler_efficiency <= 1:
        raise ValueError(
            "boiler_efficiency must be > 0 and <= 1."
        )

    if biogas_emission_factor_kg_co2_m3 < 0:
        raise ValueError(
            "biogas_emission_factor_kg_co2_m3 cannot be negative."
        )

    required_input_energy_kwh_day = (
        heat_demand_kwh_day
        / boiler_efficiency
    )

    biogas_required_m3_day = (
        required_input_energy_kwh_day
        / biogas_energy_content_kwh_m3
    )

    emissions_kg_co2_day = (
        biogas_required_m3_day
        * biogas_emission_factor_kg_co2_m3
    )

    return {
        "technologies": [
            "biogas",
        ],
        "technology_sequence": [
            "biogas",
        ],
        "pathway_type": "biogas_only",
        "heat_demand_kwh_day": heat_demand_kwh_day,
        "biogas_required_m3_day": biogas_required_m3_day,
        "emissions_kg_co2_day": emissions_kg_co2_day,
        "feasible": True,
        "provenance": {
            "legacy_helper": True,
            "note": (
                "This helper is preserved for backward compatibility. "
                "Strict technology feasibility should be established "
                "through screen_technology()/screen_technologies() "
                "before using the result in scenario generation."
            ),
        },
    }


# ============================================================================
# Convenience facade
# ============================================================================


def generate_scenarios(
    factory: Mapping[str, Any],
    candidate_technologies: Iterable[Any],
    minimum_scenarios: int = 3,
    maximum_scenarios: int = 5,
    *,
    include_biomass_scenarios: bool = True,
) -> dict[str, Any]:
    """
    Full Unit 2.8 Part-2 facade.

    Pipeline:
        candidate technologies
              ↓
        strict technology screening
              ↓
        feasible technologies
              ↓
        meaningful scenario generation

    Returns:
        {
            "screening": ...,
            "scenarios": [...]
        }

    No scenario is returned from a rejected technology.
    """

    screening = screen_technologies(
        factory=factory,
        candidates=candidate_technologies,
    )

    if len(screening["feasible"]) < minimum_scenarios:
        return {
            "screening": screening,
            "scenarios": [],
            "scenario_generation": {
                "status": "insufficient_feasible_technologies",
                "reason": (
                    f"Only {len(screening['feasible'])} technologies "
                    f"survived screening; at least "
                    f"{minimum_scenarios} are required."
                ),
            },
        }

    scenarios = generate_candidate_pathways(
        feasible_technologies=screening["feasible"],
        minimum_scenarios=minimum_scenarios,
        maximum_scenarios=maximum_scenarios,
        include_biomass_scenarios=include_biomass_scenarios,
        factory=None,
    )

    return {
        "screening": screening,
        "scenarios": scenarios,
        "scenario_generation": {
            "status": "success",
            "total_scenarios": len(scenarios),
        },
    }


# ============================================================================
# Demonstration
# ============================================================================


if __name__ == "__main__":
    sample_factory = {
        "industry": "textile_dyeing",
        "current_fuel": "coal",
        "process_temperature_c": 150,
        "steam_required": True,
        "direct_heating_required": False,
        "indirect_heating_required": True,
        "grid_capacity_kw": 500,
        "existing_electrical_load_kw": 250,
        "technology_required_power_kw": {
            "heat_pump": 100,
            "electric_boiler": 150,
        },
        "roof_area_m2": 1200,
        "biomass_supply_available": True,
        "solar_resource_available": True,
        "electricity_available": True,
        "recoverable_waste_heat": False,
        "budget_inr": 3000000,
        "electricity_tariff_inr_per_kwh": 8.0,
        "state": "Himachal Pradesh",
    }

    candidates = [
        "heat_pump",
        "electric_boiler",
        "biomass_boiler",
        "solar_thermal",
        "solar_pv",
        "thermal_storage",
        "waste_heat_recovery",
    ]

    result = generate_scenarios(
        factory=sample_factory,
        candidate_technologies=candidates,
        minimum_scenarios=3,
        maximum_scenarios=5,
    )

    print("\n=== FEASIBLE TECHNOLOGIES ===")

    for item in result["screening"]["feasible"]:
        print(
            f"PASS  {item['technology_id']}"
        )

    print("\n=== REJECTED TECHNOLOGIES ===")

    for item in result["screening"]["rejected"]:
        print(
            f"FAIL  {item['technology_id']}: "
            f"{' | '.join(item['reasons'])}"
        )

    print("\n=== GENERATED SCENARIOS ===")

    for index, scenario in enumerate(
        result["scenarios"],
        start=1,
    ):
        print(
            f"{index}. "
            f"{scenario['pathway_type']}: "
            f"{scenario['technologies']}"
        )

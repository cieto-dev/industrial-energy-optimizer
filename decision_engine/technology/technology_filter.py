"""
Industrial Technology Knowledge Engine — Unit 2.3
=================================================

Purpose
-------
Screen industrial heat technologies for technical applicability BEFORE
scenario generation, optimization, economics or ranking.

The engine answers:

    "Can this technology technically serve this factory/process?"

It does NOT answer:

    "Which feasible technology is cheapest/best?"

That decision belongs to later G2 modules.

Supported screening dimensions
------------------------------
- Technology existence
- Sector applicability
- Fuel compatibility
- Process temperature compatibility
- Pressure compatibility
- Steam compatibility
- Direct-heating compatibility
- Indirect-heating compatibility
- Resource availability
- Grid-capacity compatibility
- Roof/space requirements
- Technology maturity
- Operational constraints
- Retrofit compatibility

Design principle
----------------
A technology is rejected when a known hard technical constraint is violated.

Unknown optional information should not automatically reject a technology.

However, when a required technical field is explicitly required by the
technology definition and the factory does not provide enough information
to establish feasibility, the technology is rejected with an explicit
"insufficient data" reason.

This module is intentionally transparent and rule-based.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional


# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parents[2]

RULES_FILE = (
    BASE_DIR
    / "knowledge-base"
    / "constraints"
    / "technology_rules.json"
)

FUEL_RULES_FILE = (
    BASE_DIR
    / "knowledge-base"
    / "constraints"
    / "fuel.json"
)


# ---------------------------------------------------------------------------
# JSON loading
# ---------------------------------------------------------------------------

def load_json(file_path: Path) -> Dict[str, Any]:
    """
    Load a JSON file from the repository knowledge base.
    """
    if not file_path.exists():
        raise FileNotFoundError(
            f"Required knowledge-base file not found: {file_path}"
        )

    try:
        with file_path.open("r", encoding="utf-8") as file:
            data = json.load(file)
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"Invalid JSON in knowledge-base file: {file_path}"
        ) from exc

    if not isinstance(data, dict):
        raise ValueError(
            f"Expected JSON object in {file_path}"
        )

    return data


def load_technology_rules() -> Dict[str, Dict[str, Any]]:
    """
    Load technology applicability and constraint rules.
    """
    data = load_json(RULES_FILE)

    return {
        str(key).strip().lower(): value
        for key, value in data.items()
        if isinstance(value, Mapping)
    }


def load_fuel_rules() -> Dict[str, List[str]]:
    """
    Load the repository's fuel-to-technology compatibility map.
    """
    data = load_json(FUEL_RULES_FILE)

    result: Dict[str, List[str]] = {}

    for fuel, technologies in data.items():
        if isinstance(technologies, list):
            result[str(fuel).strip().lower()] = [
                str(item).strip().lower()
                for item in technologies
            ]

    return result


# ---------------------------------------------------------------------------
# Normalization
# ---------------------------------------------------------------------------

def normalize(value: Optional[Any]) -> str:
    """
    Normalize a value into the repository's canonical text style.
    """
    if value is None:
        return ""

    return (
        str(value)
        .strip()
        .lower()
        .replace("-", "_")
        .replace(" ", "_")
    )


def normalize_list(values: Optional[Iterable[Any]]) -> List[str]:
    """
    Normalize a list of values.
    """
    if values is None:
        return []

    return [normalize(value) for value in values]


def to_float(value: Any) -> Optional[float]:
    """
    Safely convert a value to float.
    """
    try:
        if value is None or value == "":
            return None

        return float(value)
    except (TypeError, ValueError):
        return None


def to_bool(value: Any) -> Optional[bool]:
    """
    Convert common boolean representations.
    """
    if isinstance(value, bool):
        return value

    if value is None:
        return None

    if isinstance(value, (int, float)):
        return bool(value)

    normalized = normalize(value)

    if normalized in {"true", "yes", "y", "1"}:
        return True

    if normalized in {"false", "no", "n", "0"}:
        return False

    return None


# ---------------------------------------------------------------------------
# Factory input extraction
# ---------------------------------------------------------------------------

def extract_industry(factory: Mapping[str, Any]) -> Optional[str]:
    return (
        factory.get("industry")
        or factory.get("industry_id")
        or factory.get("sector")
    )


def extract_current_fuel(factory: Mapping[str, Any]) -> Optional[str]:
    return (
        factory.get("current_fuel")
        or factory.get("fuel")
        or factory.get("primary_fuel")
    )


def extract_temperature(factory: Mapping[str, Any]) -> Optional[float]:
    candidates = (
        "required_process_temperature_c",
        "process_temperature_c",
        "process_temperature",
        "temperature_c",
        "temperature",
    )

    for field in candidates:
        value = to_float(factory.get(field))

        if value is not None:
            return value

    return None


def extract_pressure(factory: Mapping[str, Any]) -> Optional[float]:
    candidates = (
        "required_pressure_bar",
        "process_pressure_bar",
        "steam_pressure_bar",
        "pressure_bar",
        "pressure",
    )

    for field in candidates:
        value = to_float(factory.get(field))

        if value is not None:
            return value

    return None


def extract_roof_area(factory: Mapping[str, Any]) -> Optional[float]:
    candidates = (
        "roof_area_m2",
        "roof_area_sqm",
        "available_roof_area_m2",
        "available_space_m2",
    )

    for field in candidates:
        value = to_float(factory.get(field))

        if value is not None:
            return value

    return None


def extract_grid_capacity(factory: Mapping[str, Any]) -> Optional[float]:
    candidates = (
        "grid_capacity_kw",
        "available_grid_capacity_kw",
        "sanctioned_load_kw",
    )

    for field in candidates:
        value = to_float(factory.get(field))

        if value is not None:
            return value

    return None


def extract_existing_load(factory: Mapping[str, Any]) -> float:
    candidates = (
        "existing_electrical_load_kw",
        "current_electrical_load_kw",
        "peak_electrical_load_kw",
    )

    for field in candidates:
        value = to_float(factory.get(field))

        if value is not None:
            return max(0.0, value)

    return 0.0


def extract_additional_grid_capacity(factory: Mapping[str, Any]) -> float:
    candidates = (
        "additional_grid_capacity_kw",
        "grid_upgrade_capacity_kw",
        "available_upgrade_capacity_kw",
    )

    for field in candidates:
        value = to_float(factory.get(field))

        if value is not None:
            return max(0.0, value)

    return 0.0


# ---------------------------------------------------------------------------
# Resource helpers
# ---------------------------------------------------------------------------

def resource_available(
    factory: Mapping[str, Any],
    technology: str,
    rules: Mapping[str, Any],
) -> tuple[bool, Optional[str]]:
    """
    Evaluate explicit resource requirements.

    Supported explicit factory signals:

        biomass_supply_available
        biomass_available
        solar_resource_available
        recoverable_waste_heat
        electricity_available
        available_heat_source

    Missing information does not reject a technology unless the rule uses
    an explicit "requirement_data" declaration.
    """

    requires = set(
        normalize_list(rules.get("requires"))
    )

    # Biomass
    if (
        "biomass_supply" in requires
        or rules.get("requires_biomass_supply") is True
    ):
        biomass_signal = (
            factory.get("biomass_supply_available")
            if "biomass_supply_available" in factory
            else factory.get("biomass_available")
        )

        parsed = to_bool(biomass_signal)

        if parsed is False:
            return False, "Reliable biomass supply is unavailable."

    # Solar
    if (
        "solar_resource" in requires
        or rules.get("requires_solar_resource") is True
    ):
        solar_signal = factory.get("solar_resource_available")

        parsed = to_bool(solar_signal)

        if parsed is False:
            return False, "Required solar resource is unavailable."

    # Waste heat
    if "recoverable_waste_heat" in requires:
        waste_heat_signal = factory.get("recoverable_waste_heat")

        parsed = to_bool(waste_heat_signal)

        if parsed is False:
            return False, "No recoverable waste-heat source is available."

    # Heat source
    if "heat_source" in requires:
        heat_source_signal = factory.get("available_heat_source")

        parsed = to_bool(heat_source_signal)

        if parsed is False:
            return False, "Required heat source is unavailable."

    # Electricity
    if "electricity" in requires:
        electricity_signal = factory.get("electricity_available")

        parsed = to_bool(electricity_signal)

        if parsed is False:
            return False, "Electricity supply is unavailable."

    return True, None


# ---------------------------------------------------------------------------
# Sector applicability
# ---------------------------------------------------------------------------

def check_industry(
    technology: str,
    factory: Mapping[str, Any],
    rules: Mapping[str, Any],
) -> tuple[bool, Optional[str]]:

    industry = extract_industry(factory)

    if not industry:
        return True, None

    allowed = normalize_list(
        rules.get("allowed_industries", [])
    )

    if not allowed:
        return True, None

    normalized_industry = normalize(industry)

    if normalized_industry in allowed:
        return True, None

    # Controlled project aliases.
    aliases = {
        "textile_dyeing": "textile",
        "textile_processing": "textile",
        "pharma": "pharmaceutical",
        "chemical_processing": "chemical",
        "food": "food_processing",
        "food_and_beverage": "food_processing",
        "iron_steel": "steel",
        "metallurgy": "steel",
    }

    canonical = aliases.get(normalized_industry)

    if canonical and canonical in allowed:
        return True, None

    return (
        False,
        f"Industry '{industry}' is not supported by '{technology}'.",
    )


# ---------------------------------------------------------------------------
# Fuel compatibility
# ---------------------------------------------------------------------------

def check_fuel(
    technology: str,
    factory: Mapping[str, Any],
    rules: Mapping[str, Any],
    fuel_rules: Mapping[str, List[str]],
) -> tuple[bool, Optional[str]]:

    current_fuel = extract_current_fuel(factory)

    if not current_fuel:
        return True, None

    normalized_fuel = normalize(current_fuel)

    replaces_fuels = normalize_list(
        rules.get("replaces_fuels", [])
    )

    # Technologies with no declared fuel replacement are not rejected here.
    if replaces_fuels:
        if normalized_fuel not in replaces_fuels:
            return (
                False,
                f"Technology '{technology}' cannot replace current fuel "
                f"'{current_fuel}'.",
            )

    # Respect the repository's fuel-level map when it contains the fuel.
    

    return True, None


# ---------------------------------------------------------------------------
# Temperature
# ---------------------------------------------------------------------------

def check_temperature(
    technology: str,
    factory: Mapping[str, Any],
    rules: Mapping[str, Any],
) -> tuple[bool, Optional[str]]:

    required_temperature = extract_temperature(factory)

    if required_temperature is None:
        return True, None

    maximum_temperature = to_float(
        rules.get("maximum_process_temperature_c")
    )

    minimum_temperature = to_float(
        rules.get("minimum_process_temperature_c")
    )

    # Support either:
    #   maximum only
    # or:
    #   explicit min/max range.

    if maximum_temperature is not None:
        if required_temperature > maximum_temperature:
            return (
                False,
                (
                    f"Required temperature "
                    f"({required_temperature:g}°C) exceeds maximum "
                    f"supported temperature "
                    f"({maximum_temperature:g}°C)."
                ),
            )

    if minimum_temperature is not None:
        if required_temperature < minimum_temperature:
            return (
                False,
                (
                    f"Required temperature "
                    f"({required_temperature:g}°C) is below minimum "
                    f"operating temperature "
                    f"({minimum_temperature:g}°C)."
                ),
            )

    return True, None


# ---------------------------------------------------------------------------
# Pressure
# ---------------------------------------------------------------------------

def check_pressure(
    technology: str,
    factory: Mapping[str, Any],
    rules: Mapping[str, Any],
) -> tuple[bool, Optional[str]]:

    required_pressure = extract_pressure(factory)

    if required_pressure is None:
        return True, None

    min_pressure = to_float(
        rules.get("minimum_pressure_bar")
    )

    max_pressure = to_float(
        rules.get("maximum_pressure_bar")
    )

    if min_pressure is not None and required_pressure < min_pressure:
        return (
            False,
            (
                f"Required pressure ({required_pressure:g} bar) is below "
                f"the minimum pressure requirement "
                f"({min_pressure:g} bar)."
            ),
        )

    if max_pressure is not None and required_pressure > max_pressure:
        return (
            False,
            (
                f"Required pressure ({required_pressure:g} bar) exceeds "
                f"the maximum supported pressure "
                f"({max_pressure:g} bar)."
            ),
        )

    # Explicit pressure dependency with no known boundaries.
    if (
        (rules.get("pressure_compatible") is False)
        or (rules.get("supports_pressure") is False)
    ):
        return (
            False,
            f"Technology '{technology}' is not pressure-compatible.",
        )

    return True, None


# ---------------------------------------------------------------------------
# Steam compatibility
# ---------------------------------------------------------------------------

def check_steam(
    technology: str,
    factory: Mapping[str, Any],
    rules: Mapping[str, Any],
) -> tuple[bool, Optional[str]]:

    steam_required = to_bool(
        factory.get("steam_required")
    )

    if steam_required is not True:
        return True, None

    supports_steam = rules.get("steam_compatible")

    if supports_steam is False:
        return (
            False,
            f"Technology '{technology}' cannot provide the required steam.",
        )

    return True, None


# ---------------------------------------------------------------------------
# Heating mode compatibility
# ---------------------------------------------------------------------------

def check_heating_mode(
    technology: str,
    factory: Mapping[str, Any],
    rules: Mapping[str, Any],
) -> tuple[bool, Optional[str]]:

    direct_required = to_bool(
        factory.get("direct_heating_required")
    )

    indirect_required = to_bool(
        factory.get("indirect_heating_required")
    )

    supports_direct = rules.get("direct_heating")
    supports_indirect = rules.get("indirect_heating")

    if direct_required is True and supports_direct is False:
        return (
            False,
            f"Technology '{technology}' does not support direct heating.",
        )

    if indirect_required is True and supports_indirect is False:
        return (
            False,
            f"Technology '{technology}' does not support indirect heating.",
        )

    return True, None


# ---------------------------------------------------------------------------
# Grid capacity
# ---------------------------------------------------------------------------

def check_grid_capacity(
    technology: str,
    factory: Mapping[str, Any],
    rules: Mapping[str, Any],
) -> tuple[bool, Optional[str]]:

    requires_grid = rules.get("requires_grid") is True

    if not requires_grid:
        return True, None

    available_capacity = extract_grid_capacity(factory)

    # No explicit grid information:
    # preserve candidate discovery, but do not pretend the grid has passed.
    if available_capacity is None:
        return True, None

    existing_load = extract_existing_load(factory)
    additional_upgrade = extract_additional_grid_capacity(factory)

    required_power = to_float(
        rules.get("required_power_kw")
    )

    # Technology power can alternatively be supplied directly by the factory.
    if required_power is None:
        technology_power_map = factory.get(
            "technology_required_power_kw"
        )

        if isinstance(technology_power_map, Mapping):
            required_power = to_float(
                technology_power_map.get(technology)
            )

    if required_power is None:
        # Do not invent a universal power requirement.
        # This matches the project's grid rule: power must come from the
        # technology configuration or verified engineering data.
        return True, None

    required_capacity = existing_load + required_power
    effective_capacity = available_capacity + additional_upgrade

    if required_capacity > effective_capacity:
        return (
            False,
            (
                f"Electrical capacity is insufficient: required "
                f"{required_capacity:g} kW, available "
                f"{effective_capacity:g} kW."
            ),
        )

    return True, None


# ---------------------------------------------------------------------------
# Roof / space
# ---------------------------------------------------------------------------

def check_space(
    technology: str,
    factory: Mapping[str, Any],
    rules: Mapping[str, Any],
) -> tuple[bool, Optional[str]]:

    if rules.get("requires_roof") is not True:
        return True, None

    available_area = extract_roof_area(factory)

    if available_area is None:
        return True, None

    minimum_area = to_float(
        rules.get("minimum_roof_area_m2")
    )

    if minimum_area is None:
        return True, None

    if available_area < minimum_area:
        return (
            False,
            (
                f"Insufficient roof/space area: requires "
                f"{minimum_area:g} m², available "
                f"{available_area:g} m²."
            ),
        )

    return True, None


# ---------------------------------------------------------------------------
# Technology maturity
# ---------------------------------------------------------------------------

MATURITY_LEVELS = {
    "experimental": 1,
    "early": 2,
    "emerging": 3,
    "commercial": 4,
    "mature": 5,
}


def check_maturity(
    technology: str,
    factory: Mapping[str, Any],
    rules: Mapping[str, Any],
) -> tuple[bool, Optional[str]]:

    required_minimum = normalize(
        factory.get("minimum_technology_maturity")
    )

    if not required_minimum:
        return True, None

    technology_maturity = normalize(
        rules.get("technology_maturity")
    )

    if not technology_maturity:
        return (
            False,
            (
                f"Technology maturity for '{technology}' is not defined, "
                f"so the requested maturity threshold cannot be verified."
            ),
        )

    current_level = MATURITY_LEVELS.get(
        technology_maturity,
        0,
    )

    required_level = MATURITY_LEVELS.get(
        required_minimum,
        0,
    )

    if current_level == 0 or required_level == 0:
        return (
            False,
            (
                f"Unknown maturity level for '{technology}': "
                f"technology='{technology_maturity}', "
                f"required='{required_minimum}'."
            ),
        )

    if current_level < required_level:
        return (
            False,
            (
                f"Technology maturity '{technology_maturity}' is below "
                f"the required minimum '{required_minimum}'."
            ),
        )

    return True, None


# ---------------------------------------------------------------------------
# Operational constraints
# ---------------------------------------------------------------------------

def check_operational_constraints(
    technology: str,
    factory: Mapping[str, Any],
    rules: Mapping[str, Any],
) -> tuple[bool, Optional[str]]:

    # Continuous operation
    continuous_required = rules.get(
        "continuous_operation_required"
    )

    factory_continuous = to_bool(
        factory.get("continuous_operation_required")
    )

    if (
        continuous_required is True
        and factory_continuous is True
    ):
        # This is only a hard check when the factory explicitly states
        # that continuous operation is required.
        backup_available = to_bool(
            factory.get("backup_system_available")
        )

        if backup_available is False:
            # A technology may still be technically capable; this is a
            # reliability/operational constraint, so only reject when the
            # rule explicitly declares it mandatory.
            mandatory_backup = rules.get("backup_required_for_continuity")

            if mandatory_backup is True:
                return (
                    False,
                    (
                        f"Technology '{technology}' requires backup "
                        f"capability for continuous operation."
                    ),
                )

    # Retrofit support
    retrofit_required = to_bool(
        factory.get("retrofit_required")
    )

    if retrofit_required is True:
        retrofit_supported = rules.get(
            "retrofit_supported"
        )

        if retrofit_supported is False:
            return (
                False,
                (
                    f"Technology '{technology}' does not support the "
                    f"required retrofit pathway."
                ),
            )

    # Explicit constraint list from factory
    prohibited = {
        normalize(item)
        for item in factory.get("prohibited_operational_features", [])
    }

    technology_constraints = {
        normalize(item)
        for item in rules.get("operational_constraints", [])
    }

    blocked = prohibited.intersection(
        technology_constraints
    )

    if blocked:
        blocked_text = ", ".join(sorted(blocked))

        return (
            False,
            (
                f"Operational constraints conflict with factory "
                f"requirements: {blocked_text}."
            ),
        )

    return True, None


# ---------------------------------------------------------------------------
# Single technology evaluation
# ---------------------------------------------------------------------------

def evaluate_technology(
    technology: str,
    factory: Mapping[str, Any],
    technology_rules: Optional[Mapping[str, Mapping[str, Any]]] = None,
    fuel_rules: Optional[Mapping[str, List[str]]] = None,
) -> Dict[str, Any]:
    """
    Evaluate ONE technology against a factory.

    Returns a structured, explainable result.
    """

    tech = normalize(technology)

    rules_map = (
        technology_rules
        if technology_rules is not None
        else load_technology_rules()
    )

    fuels_map = (
        fuel_rules
        if fuel_rules is not None
        else load_fuel_rules()
    )

    if tech not in rules_map:
        return {
            "technology": tech,
            "feasible": False,
            "reasons": [
                f"No technology rules found for '{tech}'."
            ],
        }

    rules = rules_map[tech]

    checks: Dict[str, bool] = {}
    reasons: List[str] = []

    checks_to_run = [
        (
            "industry",
            check_industry(
                tech,
                factory,
                rules,
            ),
        ),
        (
            "fuel",
            check_fuel(
                tech,
                factory,
                rules,
                fuels_map,
            ),
        ),
        (
            "temperature",
            check_temperature(
                tech,
                factory,
                rules,
            ),
        ),
        (
            "pressure",
            check_pressure(
                tech,
                factory,
                rules,
            ),
        ),
        (
            "steam",
            check_steam(
                tech,
                factory,
                rules,
            ),
        ),
        (
            "heating_mode",
            check_heating_mode(
                tech,
                factory,
                rules,
            ),
        ),
        (
            "resource",
            resource_available(
                factory,
                tech,
                rules,
            ),
        ),
        (
            "grid_capacity",
            check_grid_capacity(
                tech,
                factory,
                rules,
            ),
        ),
        (
            "space",
            check_space(
                tech,
                factory,
                rules,
            ),
        ),
        (
            "maturity",
            check_maturity(
                tech,
                factory,
                rules,
            ),
        ),
        (
            "operational_constraints",
            check_operational_constraints(
                tech,
                factory,
                rules,
            ),
        ),
    ]

    for check_name, result in checks_to_run:
        passed, reason = result

        checks[check_name] = passed

        if not passed and reason:
            reasons.append(reason)

    feasible = len(reasons) == 0

    return {
        "technology": tech,
        "feasible": feasible,
        "checks": checks,
        "reasons": reasons,
        "technology_maturity": rules.get(
            "technology_maturity"
        ),
        "efficiency": (
            rules.get("efficiency")
            if "efficiency" in rules
            else rules.get("efficiency_pct")
        ),
        "temperature_limit_c": rules.get(
            "maximum_process_temperature_c"
        ),
        "pressure_range_bar": {
            "min": rules.get("minimum_pressure_bar"),
            "max": rules.get("maximum_pressure_bar"),
        },
        "steam_compatible": rules.get(
            "steam_compatible"
        ),
        "direct_heating": rules.get(
            "direct_heating"
        ),
        "indirect_heating": rules.get(
            "indirect_heating"
        ),
        "sector_applicability": rules.get(
            "allowed_industries",
            [],
        ),
        "fuel_compatibility": rules.get(
            "replaces_fuels",
            [],
        ),
        "operational_constraints": rules.get(
            "operational_constraints",
            [],
        ),
    }


# ---------------------------------------------------------------------------
# Full technology screening
# ---------------------------------------------------------------------------

def filter_technologies(
    factory: Mapping[str, Any],
    technologies: Optional[Iterable[str]] = None,
) -> Dict[str, Any]:
    """
    Screen all requested technologies.

    If `technologies` is None, every technology present in the knowledge
    base is evaluated.

    Output:
        {
            "feasible": [...],
            "rejected": [...],
            "total_evaluated": int
        }
    """

    rules = load_technology_rules()
    fuel_rules = load_fuel_rules()

    technology_list = (
        list(technologies)
        if technologies is not None
        else list(rules.keys())
    )

    evaluated = [
        evaluate_technology(
            technology=technology,
            factory=factory,
            technology_rules=rules,
            fuel_rules=fuel_rules,
        )
        for technology in technology_list
    ]

    feasible = [
        result
        for result in evaluated
        if result["feasible"]
    ]

    rejected = [
        result
        for result in evaluated
        if not result["feasible"]
    ]

    return {
        "feasible": feasible,
        "rejected": rejected,
        "total_evaluated": len(evaluated),
    }


# ---------------------------------------------------------------------------
# Backward-compatible biogas helper
# ---------------------------------------------------------------------------

def filter_biogas(
    fuel: str,
    industry: str,
    biogas_supply: bool = True,
    gas_cleaning: bool = True,
    gas_storage: bool = True,
) -> Dict[str, Any]:
    """
    Preserve the existing biogas function contract.

    This helper remains compatible with the previous implementation while
    internally using the Unit 2.3 technology screening logic.
    """

    factory = {
        "industry": industry,
        "current_fuel": fuel,
        "biomass_supply_available": biogas_supply,
        "biogas_supply_available": biogas_supply,
        "gas_cleaning_available": gas_cleaning,
        "gas_storage_available": gas_storage,
    }

    rules = load_technology_rules()

    biogas_rules = rules.get("biogas")

    if not biogas_rules:
        return {
            "technology": "biogas",
            "feasible": False,
            "reason": "Biogas rules not found",
        }

    # Preserve explicit biogas-specific requirements.
    if (
        biogas_rules.get("requires_biogas_supply")
        and not biogas_supply
    ):
        return {
            "technology": "biogas",
            "feasible": False,
            "reason": "Reliable biogas supply is required",
        }

    if (
        biogas_rules.get("requires_gas_cleaning")
        and not gas_cleaning
    ):
        return {
            "technology": "biogas",
            "feasible": False,
            "reason": "Gas cleaning is required",
        }

    if (
        biogas_rules.get("requires_gas_storage")
        and not gas_storage
    ):
        return {
            "technology": "biogas",
            "feasible": False,
            "reason": "Gas storage is required",
        }

    result = evaluate_technology(
        technology="biogas",
        factory=factory,
    )

    return {
        "technology": "biogas",
        "feasible": result["feasible"],
        "reason": (
            "All configured Unit 2.3 constraints passed."
            if result["feasible"]
            else " ".join(result["reasons"])
        ),
    }


# ---------------------------------------------------------------------------
# Simple demo
# ---------------------------------------------------------------------------

if __name__ == "__main__":

    sample_factory = {
        "industry": "textile_dyeing",
        "current_fuel": "coal",
        "required_process_temperature_c": 900,
        "steam_required": True,
        "direct_heating_required": False,
        "indirect_heating_required": True,
        "grid_capacity_kw": 500,
        "existing_electrical_load_kw": 300,
        "roof_area_m2": 1200,
        "biomass_available": True,
        "solar_resource_available": True,
        "electricity_available": True,
    }

    result = filter_technologies(sample_factory)

    print("\n=== FEASIBLE TECHNOLOGIES ===")

    for item in result["feasible"]:
        print(
            f"✔ {item['technology']}"
        )

    print("\n=== REJECTED TECHNOLOGIES ===")

    for item in result["rejected"]:
        print(
            f"✘ {item['technology']}: "
            f"{' | '.join(item['reasons'])}"
        )

import json
from pathlib import Path
from typing import Any, Dict, List, Optional


# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parents[2]

FUEL_RULES_FILE = (
    BASE_DIR
    / "knowledge-base"
    / "constraints"
    / "fuel.json"
)

TECHNOLOGY_RULES_FILE = (
    BASE_DIR
    / "knowledge-base"
    / "constraints"
    / "technology_rules.json"
)


# ---------------------------------------------------------------------------
# JSON loading
# ---------------------------------------------------------------------------

def load_json(file_path: Path) -> Dict[str, Any]:
    """
    Load a JSON file using UTF-8 encoding.
    """
    if not file_path.exists():
        raise FileNotFoundError(
            f"Required knowledge-base file not found: {file_path}"
        )

    with open(file_path, "r", encoding="utf-8") as file:
        return json.load(file)


def load_fuel_rules() -> Dict[str, List[str]]:
    """
    Load fuel replacement rules.
    """
    return load_json(FUEL_RULES_FILE)


def load_technology_rules() -> Dict[str, Dict[str, Any]]:
    """
    Load technology constraint rules.
    """
    return load_json(TECHNOLOGY_RULES_FILE)


# ---------------------------------------------------------------------------
# Normalisation helpers
# ---------------------------------------------------------------------------

def _normalize(value: Optional[str]) -> str:
    """
    Normalize user-provided strings for rule matching.
    """
    if value is None:
        return ""

    return str(value).strip().lower().replace("-", "_").replace(" ", "_")


def _normalize_industry(industry: Optional[str]) -> str:
    """
    Normalize industry names while preserving the repository's
    canonical underscore-based identifiers.

    Examples:
        Textile -> textile
        Textile Dyeing -> textile_dyeing
        food processing -> food_processing
    """
    return _normalize(industry)


def _normalize_fuel(fuel: Optional[str]) -> str:
    """
    Normalize fuel names.
    """
    return _normalize(fuel)


def _get_required_heat_temperature(
    factory: Optional[Dict[str, Any]]
) -> Optional[float]:
    """
    Extract process temperature from common factory-input field names.

    Supported:
        process_temperature_c
        process_temperature
        temperature_c
        temperature
    """
    if not factory:
        return None

    candidates = (
        "process_temperature_c",
        "process_temperature",
        "temperature_c",
        "temperature",
    )

    for field in candidates:
        value = factory.get(field)

        if value is None:
            continue

        try:
            return float(value)
        except (TypeError, ValueError):
            continue

    return None


# ---------------------------------------------------------------------------
# Generic technology discovery
# ---------------------------------------------------------------------------

def find_candidate_technologies(
    fuel: str,
    industry: Optional[str] = None
) -> List[str]:
    """
    Find technologies that can potentially replace the supplied fuel.

    This function preserves the original repository behaviour while adding
    optional industry filtering.

    The fuel-level candidate list comes from:
        knowledge-base/constraints/fuel.json

    Industry-level filtering comes from:
        knowledge-base/constraints/technology_rules.json
    """
    normalized_fuel = _normalize_fuel(fuel)

    if not normalized_fuel:
        return []

    fuel_rules = load_fuel_rules()

    if normalized_fuel not in fuel_rules:
        return []

    candidates = list(fuel_rules[normalized_fuel])

    if not industry:
        return candidates

    normalized_industry = _normalize_industry(industry)
    technology_rules = load_technology_rules()

    matched_candidates: List[str] = []

    for technology in candidates:
        normalized_technology = _normalize(technology)

        rules = technology_rules.get(normalized_technology, {})

        allowed_industries = [
            _normalize_industry(item)
            for item in rules.get("allowed_industries", [])
        ]

        # If a technology has no explicit industry restriction, preserve
        # the fuel-level candidate.
        if not allowed_industries:
            matched_candidates.append(technology)
            continue

        if normalized_industry in allowed_industries:
            matched_candidates.append(technology)

    return matched_candidates


# ---------------------------------------------------------------------------
# Generic rule-based matching
# ---------------------------------------------------------------------------

def match_technology(
    technology: str,
    fuel: Optional[str] = None,
    industry: Optional[str] = None,
    process_temperature_c: Optional[float] = None
) -> bool:
    """
    Determine whether a technology is technically eligible using the
    repository knowledge-base rules.

    Checks:
        1. Technology exists.
        2. Current fuel can be replaced by the technology.
        3. Industry is supported, when supplied.
        4. Required process temperature is within technology capability,
           when both values are available.
    """
    normalized_technology = _normalize(technology)

    if not normalized_technology:
        return False

    technology_rules = load_technology_rules()
    fuel_rules = load_fuel_rules()

    if normalized_technology not in technology_rules:
        return False

    rules = technology_rules[normalized_technology]

    # ------------------------------------------------------------------
    # Fuel compatibility
    # ------------------------------------------------------------------

    if fuel:
        normalized_fuel = _normalize_fuel(fuel)

        candidate_fuels = {
            _normalize_fuel(item)
            for item in rules.get("replaces_fuels", [])
        }

        # Some technologies do not replace a fuel directly, e.g. solar PV
        # or thermal storage. In that case the fuel check only applies when
        # the technology explicitly declares replacement fuels.
        if candidate_fuels and normalized_fuel not in candidate_fuels:
            return False

        # Also respect the top-level fuel compatibility map when available.
        if normalized_fuel in fuel_rules:
            fuel_candidates = {
                _normalize(item)
                for item in fuel_rules[normalized_fuel]
            }

            if normalized_technology not in fuel_candidates:
                return False

    # ------------------------------------------------------------------
    # Industry compatibility
    # ------------------------------------------------------------------

    if industry:
        normalized_industry = _normalize_industry(industry)

        allowed_industries = {
            _normalize_industry(item)
            for item in rules.get("allowed_industries", [])
        }

        if allowed_industries and normalized_industry not in allowed_industries:
            return False

    # ------------------------------------------------------------------
    # Temperature compatibility
    # ------------------------------------------------------------------

    if process_temperature_c is not None:
        try:
            required_temperature = float(process_temperature_c)
        except (TypeError, ValueError):
            return False

        maximum_temperature = rules.get(
            "maximum_process_temperature_c"
        )

        if maximum_temperature is not None:
            try:
                if required_temperature > float(maximum_temperature):
                    return False
            except (TypeError, ValueError):
                pass

    return True


# ---------------------------------------------------------------------------
# Biogas matching
# ---------------------------------------------------------------------------

def match_biogas(
    fuel: str,
    industry: Optional[str] = None,
    process_temperature_c: Optional[float] = None
) -> bool:
    """
    Check whether biogas is a technically valid candidate for replacing
    the supplied fuel.

    Preserves the existing biogas behaviour and adds an optional
    process-temperature check.
    """
    normalized_fuel = _normalize_fuel(fuel)

    fuel_rules = load_fuel_rules()
    technology_rules = load_technology_rules()

    if normalized_fuel not in fuel_rules:
        return False

    if "biogas" not in {
        _normalize(item) for item in fuel_rules[normalized_fuel]
    }:
        return False

    biogas_rules = technology_rules.get("biogas", {})

    # Industry restriction
    if industry:
        normalized_industry = _normalize_industry(industry)

        allowed_industries = {
            _normalize_industry(item)
            for item in biogas_rules.get("allowed_industries", [])
        }

        if allowed_industries and normalized_industry not in allowed_industries:
            return False

    # Fuel replacement restriction
    replaces_fuels = {
        _normalize_fuel(item)
        for item in biogas_rules.get("replaces_fuels", [])
    }

    if replaces_fuels and normalized_fuel not in replaces_fuels:
        return False

    # Temperature restriction, if available
    if process_temperature_c is not None:
        maximum_temperature = biogas_rules.get(
            "maximum_process_temperature_c"
        )

        if maximum_temperature is not None:
            try:
                if float(process_temperature_c) > float(maximum_temperature):
                    return False
            except (TypeError, ValueError):
                return False

    return True


# ---------------------------------------------------------------------------
# Biomass matching helpers
# ---------------------------------------------------------------------------

def _biomass_has_supply(factory: Dict[str, Any]) -> bool:
    """
    Determine whether the factory indicates that biomass supply exists.

    The engine remains conservative:
    - explicit False => unavailable
    - positive numeric quantity => available
    - non-empty textual/location information => available
    - no information => assumed available for candidate discovery

    Final technical feasibility remains the responsibility of the
    BiomassEngine / engineering layer.
    """
    supply_keys = (
        "biomass_available",
        "biomass_supply_available",
        "biomass_supply",
        "biomass_availability",
        "biomass_kg_day",
        "biomass_available_kg_day",
        "biomass_surplus_tonnes_per_year",
        "biomass_surplus_mtpa",
    )

    for key in supply_keys:
        if key not in factory:
            continue

        value = factory.get(key)

        if isinstance(value, bool):
            return value

        if isinstance(value, (int, float)):
            return value > 0

        if isinstance(value, str):
            normalized = value.strip().lower()

            if normalized in {
                "false",
                "no",
                "none",
                "unavailable",
                "not_available",
                "0",
            }:
                return False

            if normalized:
                return True

    # Do not reject a biomass candidate merely because the front-end
    # has not supplied a biomass assessment yet.
    return True


def _biomass_industry_match(
    industry: Optional[str],
    allowed_industries: List[str]
) -> bool:
    """
    Match an industry against biomass-supported industries.

    Exact canonical matches are preferred, but a small amount of
    controlled normalization is allowed.
    """
    if not industry:
        return True

    normalized_industry = _normalize_industry(industry)

    allowed = {
        _normalize_industry(item)
        for item in allowed_industries
    }

    if not allowed:
        return True

    if normalized_industry in allowed:
        return True

    # Controlled aliases frequently used by the project.
    aliases = {
        "textile_dyeing": "textile",
        "textile_processing": "textile",
        "food": "food_processing",
        "food_and_beverage": "food_processing",
        "pharma": "pharmaceutical",
        "paper_pulp": "paper",
        "iron_steel": "steel",
        "metallurgy": "steel",
    }

    canonical = aliases.get(normalized_industry)

    return canonical in allowed if canonical else False


def match_biomass(
    fuel: str,
    industry: Optional[str] = None,
    process_temperature_c: Optional[float] = None,
    factory: Optional[Dict[str, Any]] = None
) -> bool:
    """
    Check whether biomass is a valid candidate for replacing the supplied
    fuel.

    Biomass matching combines:
        - fuel replacement rules
        - industry applicability
        - process temperature capability
        - biomass supply indication

    The function deliberately does NOT perform detailed biomass sizing,
    delivered-cost calculation, transport optimisation, or emissions
    calculations. Those belong to BiomassEngine / downstream decision
    modules.
    """
    normalized_fuel = _normalize_fuel(fuel)

    fuel_rules = load_fuel_rules()
    technology_rules = load_technology_rules()

    # ---------------------------------------------------------------
    # Fuel compatibility
    # ---------------------------------------------------------------

    if normalized_fuel not in fuel_rules:
        return False

    fuel_candidates = {
        _normalize(item)
        for item in fuel_rules[normalized_fuel]
    }

    if "biomass" not in fuel_candidates:
        return False

    biomass_rules = technology_rules.get("biomass_boiler", {})

    # Biomass can replace only fuels declared by technology rules.
    replaces_fuels = {
        _normalize_fuel(item)
        for item in biomass_rules.get("replaces_fuels", [])
    }

    if replaces_fuels and normalized_fuel not in replaces_fuels:
        return False

    # ---------------------------------------------------------------
    # Industry compatibility
    # ---------------------------------------------------------------

    allowed_industries = biomass_rules.get(
        "allowed_industries",
        []
    )

    if not _biomass_industry_match(
        industry,
        allowed_industries
    ):
        return False

    # ---------------------------------------------------------------
    # Temperature compatibility
    # ---------------------------------------------------------------

    if process_temperature_c is not None:
        maximum_temperature = biomass_rules.get(
            "maximum_process_temperature_c"
        )

        if maximum_temperature is not None:
            try:
                if float(process_temperature_c) > float(maximum_temperature):
                    return False
            except (TypeError, ValueError):
                return False

    # ---------------------------------------------------------------
    # Biomass resource availability
    # ---------------------------------------------------------------

    factory_data = factory or {}

    if not _biomass_has_supply(factory_data):
        return False

    return True


# ---------------------------------------------------------------------------
# Biomass candidate discovery
# ---------------------------------------------------------------------------

def find_biomass_candidates(
    fuel: str,
    industry: Optional[str] = None,
    process_temperature_c: Optional[float] = None,
    factory: Optional[Dict[str, Any]] = None
) -> List[str]:
    """
    Return biomass-related technology candidates.

    Current architecture uses biomass_boiler as the primary solid-biomass
    combustion technology. The method is intentionally extensible so
    additional biomass technologies can later be introduced without
    changing the public matcher interface.
    """
    candidates: List[str] = []

    if match_biomass(
        fuel=fuel,
        industry=industry,
        process_temperature_c=process_temperature_c,
        factory=factory,
    ):
        candidates.append("biomass_boiler")

    return candidates


# ---------------------------------------------------------------------------
# Detailed matching result
# ---------------------------------------------------------------------------

def get_technology_match(
    technology: str,
    fuel: Optional[str] = None,
    industry: Optional[str] = None,
    process_temperature_c: Optional[float] = None,
    factory: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Return a structured match result suitable for the Technology Engine.

    This keeps matching logic transparent and preserves provenance for
    downstream scenario generation and explanation.
    """
    normalized_technology = _normalize(technology)

    technology_rules = load_technology_rules()

    result: Dict[str, Any] = {
        "technology": normalized_technology,
        "fuel": _normalize_fuel(fuel) if fuel else None,
        "industry": _normalize_industry(industry) if industry else None,
        "process_temperature_c": process_temperature_c,
        "matched": False,
        "reason": None,
    }

    if normalized_technology not in technology_rules:
        result["reason"] = "technology_not_defined"
        return result

    # Dedicated biomass path
    if normalized_technology == "biomass_boiler":
        matched = match_biomass(
            fuel=fuel or "",
            industry=industry,
            process_temperature_c=process_temperature_c,
            factory=factory,
        )

        result["matched"] = matched
        result["reason"] = (
            "biomass_constraints_satisfied"
            if matched
            else "biomass_constraints_not_satisfied"
        )

        return result

    # Dedicated biogas path
    if normalized_technology == "biogas":
        matched = match_biogas(
            fuel=fuel or "",
            industry=industry,
            process_temperature_c=process_temperature_c,
        )

        result["matched"] = matched
        result["reason"] = (
            "biogas_constraints_satisfied"
            if matched
            else "biogas_constraints_not_satisfied"
        )

        return result

    # Generic technology path
    matched = match_technology(
        technology=normalized_technology,
        fuel=fuel,
        industry=industry,
        process_temperature_c=process_temperature_c,
    )

    result["matched"] = matched
    result["reason"] = (
        "technology_constraints_satisfied"
        if matched
        else "technology_constraints_not_satisfied"
    )

    return result


# ---------------------------------------------------------------------------
# Public compatibility aliases
# ---------------------------------------------------------------------------

def match_biomass_boiler(
    fuel: str,
    industry: Optional[str] = None,
    process_temperature_c: Optional[float] = None,
    factory: Optional[Dict[str, Any]] = None
) -> bool:
    """
    Compatibility wrapper for callers that use the explicit
    biomass-boiler technology name.
    """
    return match_biomass(
        fuel=fuel,
        industry=industry,
        process_temperature_c=process_temperature_c,
        factory=factory,
    )


# ---------------------------------------------------------------------------
# Manual smoke test
# ---------------------------------------------------------------------------

if __name__ == "__main__":

    print("Technology Matcher")
    print("------------------")

    test_cases = [
        {
            "technology": "biogas",
            "fuel": "coal",
            "industry": "textile",
        },
        {
            "technology": "biomass_boiler",
            "fuel": "coal",
            "industry": "textile",
            "process_temperature_c": 180,
        },
        {
            "technology": "biomass_boiler",
            "fuel": "natural_gas",
            "industry": "food_processing",
            "process_temperature_c": 250,
        },
        {
            "technology": "heat_pump",
            "fuel": "coal",
            "industry": "textile",
            "process_temperature_c": 150,
        },
    ]

    for case in test_cases:

        result = get_technology_match(**case)

        print(
            f"{case['technology']} | "
            f"{case.get('fuel')} | "
            f"{case.get('industry')} -> "
            f"{result['matched']} "
            f"({result['reason']})"
        )

from pathlib import Path
import json


# Project root
PROJECT_ROOT = Path(__file__).resolve().parents[2]

# Technology cost database
TECHNOLOGY_COSTS_FILE = (
    PROJECT_ROOT
    / "knowledge-base"
    / "finance"
    / "technology_costs.json"
)


def load_technology_costs():
    """
    Load technology cost data from technology_costs.json.
    """

    if not TECHNOLOGY_COSTS_FILE.exists():
        raise FileNotFoundError(
            f"Technology cost file not found: {TECHNOLOGY_COSTS_FILE}"
        )

    with open(
        TECHNOLOGY_COSTS_FILE,
        "r",
        encoding="utf-8"
    ) as file:
        return json.load(file)


def get_technology_data(technology_id):
    """
    Get technology information using the exact TECH_* ID.
    """

    data = load_technology_costs()

    entities = data.get("entities", {})

    if technology_id not in entities:
        raise ValueError(
            f"Technology ID not found: {technology_id}"
        )

    return entities[technology_id]


def convert_capex_to_inr(
    value,
    unit,
    capacity=None,
    usd_to_inr=None
):
    """
    Convert supported CAPEX units into total INR CAPEX.

    capacity must be supplied when the CAPEX is expressed
    per kW, kWth, MW, etc.
    """

    if value is None:
        return None

    value = float(value)

    # Already total INR
    if unit == "INR":
        return value

    # INR lakh
    if unit == "INR_lakh":
        return value * 100000

    # INR per kW
    if unit == "INR_per_kW":

        if capacity is None:
            raise ValueError(
                "capacity_kw is required for INR_per_kW CAPEX."
            )

        return value * capacity

    # INR per kW thermal
    if unit == "INR_per_kWth":

        if capacity is None:
            raise ValueError(
                "capacity_kwth is required for INR_per_kWth CAPEX."
            )

        return value * capacity

    # INR per MW
    if unit == "INR_per_MW":

        if capacity is None:
            raise ValueError(
                "capacity_mw is required for INR_per_MW CAPEX."
            )

        return value * capacity

    # USD per kW
    if unit == "USD_per_kW":

        if capacity is None:
            raise ValueError(
                "capacity_kw is required for USD_per_kW CAPEX."
            )

        if usd_to_inr is None:
            raise ValueError(
                "usd_to_inr is required for USD-denominated CAPEX."
            )

        return value * capacity * usd_to_inr

    # USD per kW thermal
    if unit == "USD_per_kWth":

        if capacity is None:
            raise ValueError(
                "capacity_kwth is required for USD_per_kWth CAPEX."
            )

        if usd_to_inr is None:
            raise ValueError(
                "usd_to_inr is required for USD-denominated CAPEX."
            )

        return value * capacity * usd_to_inr

    # USD per kW thermal recovered
    if unit == "USD_per_kW_thermal_recovered":

        if capacity is None:
            raise ValueError(
                "capacity_kw_thermal_recovered is required "
                "for USD_per_kW_thermal_recovered CAPEX."
            )

        if usd_to_inr is None:
            raise ValueError(
                "usd_to_inr is required for USD-denominated CAPEX."
            )

        return value * capacity * usd_to_inr

    # USD per kWh thermal
    if unit == "USD_per_kWh_thermal":

        if capacity is None:
            raise ValueError(
                "capacity_kwh_thermal is required "
                "for USD_per_kWh_thermal CAPEX."
            )

        if usd_to_inr is None:
            raise ValueError(
                "usd_to_inr is required for USD-denominated CAPEX."
            )

        return value * capacity * usd_to_inr

    raise ValueError(
        f"Unsupported CAPEX unit: {unit}"
    )


def _convert_parameter(
    parameter,
    capacity=None,
    usd_to_inr=None
):
    """
    Convert one CAPEX parameter object into INR.
    """

    if not parameter:
        return None

    value = parameter.get("value")
    unit = parameter.get("unit")

    if value is None:
        return None

    return convert_capex_to_inr(
        value=value,
        unit=unit,
        capacity=capacity,
        usd_to_inr=usd_to_inr
    )


def calculate_capex(
    technology_id,
    capacity=None,
    usd_to_inr=None
):
    """
    Calculate CAPEX for a technology.

    Handles:
    - capex
    - capex_min / capex_max
    - capex_range_min / capex_range_max
    - capex_per_kwth
    - capex_per_mw_large_scale

    Returns CAPEX in INR.
    """
    # This is a legacy wrapper.
    # We should encourage the use of load_capex_result.
    result = load_capex_result(technology_id, capacity, usd_to_inr)
    
    if result.status == "unavailable":
        raise ValueError(
            f"No usable CAPEX found for "
            f"technology: {technology_id}"
        )
        
    return {
        "technology_id": technology_id,
        "capex_min": result.capex_min_inr,
        "capex_max": result.capex_max_inr,
        "capex_estimate": result.capex_estimate_inr,
        "currency": "INR"
    }


def _normalize_confidence(confidence: float | str | None) -> str:
    """
    Normalize confidence from 0-1 float to High/Medium/Low string.
    """
    if confidence is None:
        return "Low"
    if isinstance(confidence, str):
        # Pass through existing string scale if already used
        if confidence in ["High", "Medium", "Low"]:
            return confidence
        # Try to parse as float if it's a string number
        try:
            confidence = float(confidence)
        except ValueError:
            return "Low"
            
    if isinstance(confidence, (int, float)):
        if confidence >= 0.7:
            return "High"
        elif confidence >= 0.5:
            return "Medium"
        else:
            return "Low"
            
    return "Low"


def load_capex_result(
    technology_id: str,
    capacity: float | None = None,
    usd_to_inr: float | None = None
):
    """
    Calculate CAPEX for a technology and return a structured CapexResult.
    Gracefully handles missing data instead of raising an exception.
    """
    # We import here to avoid circular imports if any
    from decision_engine.economics.models import CapexResult
    
    try:
        technology = get_technology_data(technology_id)
    except ValueError:
        # Tech not found in technology_costs.json
        return CapexResult(
            status="unavailable",
            capex_min_inr=None,
            capex_max_inr=None,
            capex_estimate_inr=None,
            confidence=None,
            source_id=None,
            last_verified=None
        )

    parameters = technology.get("parameters", {})
    
    # Track metadata from whichever parameter we end up using
    used_parameter = None

    # --------------------------------------------------
    # CAPEX range
    # --------------------------------------------------

    min_parameter = (
        parameters.get("capex_min")
        or parameters.get("capex_range_min")
    )

    max_parameter = (
        parameters.get("capex_max")
        or parameters.get("capex_range_max")
    )

    capex_min = _convert_parameter(
        min_parameter,
        capacity=capacity,
        usd_to_inr=usd_to_inr
    )

    capex_max = _convert_parameter(
        max_parameter,
        capacity=capacity,
        usd_to_inr=usd_to_inr
    )
    
    if min_parameter and min_parameter.get("value") is not None:
        used_parameter = min_parameter
    elif max_parameter and max_parameter.get("value") is not None:
        used_parameter = max_parameter

    # --------------------------------------------------
    # Single CAPEX value
    # --------------------------------------------------

    capex_parameter = parameters.get("capex")

    capex_value = _convert_parameter(
        capex_parameter,
        capacity=capacity,
        usd_to_inr=usd_to_inr
    )
    
    if capex_value is not None:
        used_parameter = capex_parameter

    # --------------------------------------------------
    # CAPEX per kWth
    # --------------------------------------------------

    if capex_value is None:

        capex_per_kwth = parameters.get(
            "capex_per_kwth"
        )

        capex_value = _convert_parameter(
            capex_per_kwth,
            capacity=capacity,
            usd_to_inr=usd_to_inr
        )
        
        if capex_value is not None:
            used_parameter = capex_per_kwth

    # --------------------------------------------------
    # Large-scale CAPEX per MW
    # --------------------------------------------------

    if capex_value is None:

        capex_per_mw = parameters.get(
            "capex_per_mw_large_scale"
        )

        capex_value = _convert_parameter(
            capex_per_mw,
            capacity=capacity,
            usd_to_inr=usd_to_inr
        )
        
        if capex_value is not None:
            used_parameter = capex_per_mw

    # --------------------------------------------------
    # Determine final range
    # --------------------------------------------------

    if capex_min is None and capex_max is None:

        if capex_value is None:
            # All null -> gracefully return unavailable
            # Use metadata from capex_parameter if available (even if value is null)
            meta_param = capex_parameter or {}
            
            return CapexResult(
                status="unavailable",
                capex_min_inr=None,
                capex_max_inr=None,
                capex_estimate_inr=None,
                confidence=_normalize_confidence(meta_param.get("confidence")),
                source_id=meta_param.get("source_id"),
                last_verified=meta_param.get("last_verified")
            )

        capex_min = capex_value
        capex_max = capex_value

    else:

        # If only minimum exists
        if capex_min is None:
            capex_min = capex_value

        # If only maximum exists
        if capex_max is None:
            capex_max = capex_value

    # --------------------------------------------------
    # Estimate = midpoint when range exists
    # --------------------------------------------------

    if capex_min is not None and capex_max is not None:

        capex_estimate = (
            capex_min + capex_max
        ) / 2

    elif capex_min is not None:

        capex_estimate = capex_min

    else:

        capex_estimate = capex_max
        
    # Extract metadata
    confidence = None
    source_id = None
    last_verified = None
    
    if used_parameter:
        confidence = _normalize_confidence(used_parameter.get("confidence"))
        source_id = used_parameter.get("source_id")
        last_verified = used_parameter.get("last_verified")

    return CapexResult(
        status="available",
        capex_min_inr=capex_min,
        capex_max_inr=capex_max,
        capex_estimate_inr=capex_estimate,
        confidence=confidence,
        source_id=source_id,
        last_verified=last_verified
    )
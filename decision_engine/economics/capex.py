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

    technology = get_technology_data(
        technology_id
    )

    parameters = technology.get(
        "parameters",
        {}
    )

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

    # --------------------------------------------------
    # Single CAPEX value
    # --------------------------------------------------

    capex_parameter = parameters.get("capex")

    capex_value = _convert_parameter(
        capex_parameter,
        capacity=capacity,
        usd_to_inr=usd_to_inr
    )

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

    # --------------------------------------------------
    # Determine final range
    # --------------------------------------------------

    if capex_min is None and capex_max is None:

        if capex_value is None:
            raise ValueError(
                f"No usable CAPEX found for "
                f"technology: {technology_id}"
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

    return {
        "technology_id": technology_id,
        "capex_min": capex_min,
        "capex_max": capex_max,
        "capex_estimate": capex_estimate,
        "currency": "INR"
    }
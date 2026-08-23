
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from models.factory import Factory
from decision_engine.baseline._units import standardize_daily_consumption
from decision_engine.emissions.emission_factors import get_emission_factor


BASE_DIR = Path(__file__).resolve().parents[2]

FUEL_PRICES_FILE = (
    BASE_DIR
    / "knowledge-base"
    / "finance"
    / "fuel_prices.json"
)

ELEC_TARIFFS_FILE = (
    BASE_DIR
    / "knowledge-base"
    / "finance"
    / "electricity_tariffs.json"
)


FUEL_PRICE_UNIT_NORMALIZATION = {
    "inr_per_kg": "INR/kg",
    "inr_per_litre": "INR/L",
    "inr_per_scm": "INR/SCM",
    "inr_per_tonne": "INR/t",
}


def _load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(
            f"Knowledge-base file not found: {path}"
        )

    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def _normalize_fuel_price_unit(unit: str) -> str:
    normalized = unit.lower().strip()

    if normalized in FUEL_PRICE_UNIT_NORMALIZATION:
        return FUEL_PRICE_UNIT_NORMALIZATION[normalized]

    return unit


def get_fuel_price_record(fuel: str) -> dict[str, Any]:
    """
    Return the best available verified/estimated price record for the fuel.

    Priority is intentionally:
      1. delivered MSME estimate
      2. industrial/reference price
      3. any remaining price_* parameter
    """
    fuel = fuel.lower().strip()

    fuel_mapping = {
        "coal": "FUEL_COAL",
        "diesel": "FUEL_DIESEL_HSD",
        "lpg": "FUEL_LPG",
        "natural_gas": "FUEL_NATURAL_GAS_PNG",
        "biomass": "FUEL_BIOMASS",
    }

    fuel_id = fuel_mapping.get(fuel)

    if not fuel_id:
        raise ValueError(
            f"Unknown fuel mapping for '{fuel}'."
        )

    prices_data = _load_json(FUEL_PRICES_FILE).get("entities", {})

    entity = prices_data.get(fuel_id)

    if not entity:
        raise ValueError(
            f"Fuel ID '{fuel_id}' not found in fuel_prices.json."
        )

    parameters = entity.get("parameters", {})

    preferred_keys = (
        "price_delivered_msme_estimate",
        "price_retail_reference",
        "price_briquettes_industrial",
        "price_pellets_industrial",
    )

    for key in preferred_keys:
        data = parameters.get(key)

        if data and data.get("value") is not None:
            return {
                "fuel": fuel,
                "fuel_id": fuel_id,
                "parameter": key,
                "price": float(data["value"]),
                "unit": _normalize_fuel_price_unit(
                    str(data.get("unit", ""))
                ),
                "status": data.get("status"),
                "confidence": data.get("confidence"),
                "source_id": data.get("source_id"),
            }

    for key, data in parameters.items():
        if (
            key.startswith("price_")
            and isinstance(data, dict)
            and data.get("value") is not None
        ):
            return {
                "fuel": fuel,
                "fuel_id": fuel_id,
                "parameter": key,
                "price": float(data["value"]),
                "unit": _normalize_fuel_price_unit(
                    str(data.get("unit", ""))
                ),
                "status": data.get("status"),
                "confidence": data.get("confidence"),
                "source_id": data.get("source_id"),
            }

    raise ValueError(
        f"No usable price record was found for fuel '{fuel}'."
    )


def get_fuel_price(fuel: str) -> float:
    """
    Backward-compatible helper returning only the numeric price.
    """
    return get_fuel_price_record(fuel)["price"]


def get_electricity_tariff_record(state: str) -> dict[str, Any]:
    """
    Resolve an electricity energy charge for the supplied state.

    This intentionally does not add demand charges yet because Factory does
    not currently expose contracted/maximum demand in kVA.
    """
    tariffs_data = _load_json(ELEC_TARIFFS_FILE).get("entities", {})

    for tariff_id, data in tariffs_data.items():
        parameters = data.get("parameters", {})

        energy_charge = parameters.get(
            "energy_charge_inr_per_kwh"
        )

        if energy_charge:
            applicability = energy_charge.get(
                "applicability",
                {},
            )

            if applicability.get("state") == state:
                return {
                    "tariff_id": tariff_id,
                    "charge": float(
                        energy_charge["value"]
                    ),
                    "unit": "INR/kWh",
                    "status": energy_charge.get("status"),
                    "source_id": energy_charge.get("source_id"),
                }

        energy_charge_kvah = parameters.get(
            "energy_charge_inr_per_kvah"
        )

        if energy_charge_kvah:
            applicability = energy_charge_kvah.get(
                "applicability",
                {},
            )

            if applicability.get("state") == state:
                return {
                    "tariff_id": tariff_id,
                    "charge": float(
                        energy_charge_kvah["value"]
                    ),
                    "unit": "INR/kVAh",
                    "status": energy_charge_kvah.get("status"),
                    "source_id": energy_charge_kvah.get("source_id"),
                }

    raise ValueError(
        f"Missing electricity tariff for state '{state}'."
    )


def get_electricity_tariff(state: str) -> float:
    """
    Backward-compatible helper returning the numeric energy charge.
    """
    return get_electricity_tariff_record(state)["charge"]


def _annual_consumption_in_unit(
    factory: Factory,
    target_unit: str,
) -> float:
    """
    Convert the factory daily fuel quantity to the pricing unit's compatible
    physical unit and annualize it.
    """
    daily = standardize_daily_consumption(
        factory.fuel_consumption.value,
        factory.fuel_consumption.unit,
        target_unit,
    )

    return daily * factory.operating_days_per_year


def calculate_annual_energy_cost(
    factory: Factory,
    annual_fuel_base: float | None = None,
    annual_electricity_kwh: float | None = None,
) -> dict[str, Any]:
    """
    Calculate annual energy cost using the knowledge-base prices.

    Backward compatibility:
        annual_fuel_base and annual_electricity_kwh may still be supplied
        by existing callers.

    However, for robust unit handling, the preferred path is to call this
    function with the Factory and let it derive annual fuel consumption from
    Factory.fuel_consumption.
    """
    fuel = factory.current_fuel.lower().strip()

    fuel_record = get_fuel_price_record(fuel)
    fuel_price = fuel_record["price"]
    price_unit = fuel_record["unit"]

    # ------------------------------------------------------------------
    # Fuel quantity matching
    # ------------------------------------------------------------------
    #
    # The knowledge base stores fuel prices in physical price units.
    # We therefore derive annual physical consumption from Factory unless
    # an explicitly compatible annual_fuel_base was supplied.
    #
    # For backward compatibility, only use annual_fuel_base when it matches
    # the price unit's intended basis.
    #
    if price_unit == "INR/kg":
        annual_fuel_quantity = _annual_consumption_in_unit(
            factory,
            "kg/day",
        )
    elif price_unit == "INR/L":
        annual_fuel_quantity = _annual_consumption_in_unit(
            factory,
            "L/day",
        )
    elif price_unit == "INR/SCM":
        annual_fuel_quantity = _annual_consumption_in_unit(
            factory,
            "SCM/day",
        )
    elif price_unit == "INR/t":
        annual_fuel_quantity = _annual_consumption_in_unit(
            factory,
            "tonnes/day",
        )
    else:
        # Legacy escape hatch for unusual future datasets.
        if annual_fuel_base is None:
            raise ValueError(
                f"Unsupported fuel price unit '{price_unit}'."
            )

        annual_fuel_quantity = annual_fuel_base

    annual_fuel_cost = fuel_price * annual_fuel_quantity

    # ------------------------------------------------------------------
    # Electricity
    # ------------------------------------------------------------------
    if annual_electricity_kwh is None:
        annual_electricity_kwh = (
            factory.electricity_consumption_kwh_day
            * factory.operating_days_per_year
        )

    tariff_record = get_electricity_tariff_record(
        factory.state
    )

    tariff = tariff_record["charge"]

    annual_electricity_cost = (
        tariff
        * annual_electricity_kwh
    )

    total_energy_cost = (
        annual_fuel_cost
        + annual_electricity_cost
    )

    return {
        "annual_fuel_cost_inr": round(
            annual_fuel_cost,
            2,
        ),
        "annual_electricity_cost_inr": round(
            annual_electricity_cost,
            2,
        ),
        "total_energy_cost_inr": round(
            total_energy_cost,
            2,
        ),
        "fuel": fuel,
        "annual_fuel_quantity": round(
            annual_fuel_quantity,
            6,
        ),
        "fuel_price": fuel_price,
        "fuel_price_unit": price_unit,
        "fuel_price_status": fuel_record.get("status"),
        "fuel_price_confidence": fuel_record.get(
            "confidence"
        ),
        "fuel_price_source_id": fuel_record.get(
            "source_id"
        ),
        "electricity_tariff_inr_per_kwh": tariff,
        "electricity_tariff_source_id": tariff_record.get(
            "source_id"
        ),
        "electricity_tariff_status": tariff_record.get(
            "status"
        ),
        "demand_charge_modeled": False,
        "demand_charge_note": (
            "Demand charges are not included because the current Factory "
            "contract does not contain contracted/maximum demand in kVA."
        ),
    }

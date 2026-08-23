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
                "price": float(data["value"]),
                "unit": _normalize_fuel_price_unit(
                    data.get("unit", "")
                ),
                "status": data.get("status", "estimated"),
                "confidence": data.get("confidence", "medium"),
                "source_id": data.get("source_id"),
                "source_type": data.get("source_type"),
                "parameter_key": key,
            }

    # Fallback: first price_* parameter that has a numeric value
    for key, data in parameters.items():
        if not key.startswith("price_"):
            continue
        if data and data.get("value") is not None:
            return {
                "fuel": fuel,
                "fuel_id": fuel_id,
                "price": float(data["value"]),
                "unit": _normalize_fuel_price_unit(
                    data.get("unit", "")
                ),
                "status": data.get("status", "estimated"),
                "confidence": data.get("confidence", "medium"),
                "source_id": data.get("source_id"),
                "source_type": data.get("source_type"),
                "parameter_key": key,
            }

    raise ValueError(
        f"No usable price parameter found for fuel '{fuel}' "
        f"(fuel_id={fuel_id})."
    )


def get_electricity_tariff_record(state: str) -> dict[str, Any]:
    """
    Return the energy-charge (INR/kWh) record for the given state.

    Demand charges are intentionally NOT returned here for the MVP
    baseline path (see calculate_annual_energy_cost coverage note).
    """
    state = state.strip()

    data = _load_json(ELEC_TARIFFS_FILE)
    entities = data.get("entities", {})

    # Prefer exact state match, then normalized lookup
    for entity_id, entity in entities.items():
        meta = entity.get("metadata", {})
        entity_state = (
            meta.get("state")
            or entity.get("state")
            or entity_id
        )
        if str(entity_state).strip().lower() == state.lower():
            parameters = entity.get("parameters", {})

            # Prefer energy_charge_kwh, then energy_charge, then any charge
            for key in (
                "energy_charge_kwh",
                "energy_charge",
                "energy_charge_inr_per_kwh",
                "tariff_energy",
            ):
                charge_data = parameters.get(key)
                if charge_data and charge_data.get("value") is not None:
                    return {
                        "state": state,
                        "entity_id": entity_id,
                        "charge": float(charge_data["value"]),
                        "unit": charge_data.get(
                            "unit", "INR/kWh"
                        ),
                        "status": charge_data.get(
                            "status", "estimated"
                        ),
                        "confidence": charge_data.get(
                            "confidence", "medium"
                        ),
                        "source_id": charge_data.get("source_id"),
                        "source_type": charge_data.get(
                            "source_type"
                        ),
                        "parameter_key": key,
                    }

            # Legacy kvah fallback (still energy-only)
            energy_charge_kvah = parameters.get(
                "energy_charge_kvah"
            )
            if (
                energy_charge_kvah
                and energy_charge_kvah.get("value") is not None
            ):
                return {
                    "state": state,
                    "entity_id": entity_id,
                    "charge": float(
                        energy_charge_kvah["value"]
                    ),
                    "unit": energy_charge_kvah.get(
                        "unit", "INR/kVAh"
                    ),
                    "status": energy_charge_kvah.get(
                        "status", "estimated"
                    ),
                    "confidence": energy_charge_kvah.get(
                        "confidence", "medium"
                    ),
                    "source_id": energy_charge_kvah.get(
                        "source_id"
                    ),
                    "source_type": energy_charge_kvah.get(
                        "source_type"
                    ),
                    "parameter_key": "energy_charge_kvah",
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

    MVP coverage limitation (Task 3.1 item 6)
    ----------------------------------------
    Electricity cost is **energy-only** (INR/kWh × annual kWh).
    Demand (kVA/kW) charges, fixed charges, and duty/surcharge are
    deliberately excluded because the current Factory contract does
    not supply contracted_demand_kva / maximum_demand_kva.

    The returned dict therefore always contains:
      - demand_charge_modeled = False
      - cost_coverage = "energy_only"
      - coverage_limitation / uncertainty notes

    Callers MUST treat annual_electricity_cost_inr as incomplete for
    any site that faces material demand charges.
    """
    fuel = factory.current_fuel.lower().strip()

    fuel_record = get_fuel_price_record(fuel)
    fuel_price = fuel_record["price"]
    price_unit = fuel_record["unit"]

    # ------------------------------------------------------------------
    # Fuel quantity matching
    # ------------------------------------------------------------------
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
    # Electricity (energy-only by design for MVP)
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

    # Explicit coverage limitation (Task 6)
    coverage_note = (
        "MVP electricity cost is energy-only (INR/kWh × annual kWh). "
        "Demand (kVA/kW) charges, fixed charges, electricity duty and "
        "surcharges are excluded because the Factory contract does not "
        "supply contracted_demand_kva or maximum_demand_kva. "
        "Treat annual_electricity_cost_inr (and therefore "
        "total_energy_cost_inr) as incomplete for any site that faces "
        "material demand charges. Full bill modelling requires the "
        "TariffEngine path with explicit demand inputs."
    )

    return {
        "annual_fuel_cost_inr": round(annual_fuel_cost, 2),
        "annual_electricity_cost_inr": round(annual_electricity_cost, 2),
        "total_energy_cost_inr": round(total_energy_cost, 2),
        "fuel": fuel,
        "annual_fuel_quantity": round(annual_fuel_quantity, 6),
        "fuel_price": fuel_price,
        "fuel_price_unit": price_unit,
        "fuel_price_status": fuel_record.get("status"),
        "fuel_price_confidence": fuel_record.get("confidence"),
        "fuel_price_source_id": fuel_record.get("source_id"),
        "electricity_tariff_inr_per_kwh": tariff,
        "electricity_tariff_source_id": tariff_record.get("source_id"),
        "electricity_tariff_status": tariff_record.get("status"),
        "electricity_tariff_confidence": tariff_record.get("confidence"),
        # ---- Task 6 coverage / uncertainty surface ----
        "demand_charge_modeled": False,
        "cost_coverage": "energy_only",
        "cost_coverage_status": "incomplete_mvp",
        "cost_coverage_limitation": coverage_note,
        "demand_charge_note": (
            "Demand charges are not included because the current Factory "
            "contract does not contain contracted/maximum demand in kVA."
        ),
        "uncertainty_flags": [
            "electricity_cost_excludes_demand_charges",
            "electricity_cost_excludes_fixed_charges",
            "electricity_cost_excludes_duty_surcharge",
            "annual_electricity_cost_is_energy_only",
        ],
    }
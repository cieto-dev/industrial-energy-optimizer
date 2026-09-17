"""
CO2 calculator for industrial fuel consumption.

All numeric values are obtained through v2.0-aware helper functions that
unwrap nested parameter objects and enforce the No-Invention Rule.
Provenance (confidence, source_id) is propagated into the result.
"""

import json
from pathlib import Path

from decision_engine.emissions.emission_factors import (
    get_emission_factor,
    get_emission_factor_value,
    get_ncv_value,
)

BASE_DIR = Path(__file__).resolve().parents[2]

EMISSION_FILE = (
    BASE_DIR
    / "knowledge-base"
    / "emissions"
    / "emission_factors.json"
)


def load_emission_factors():
    with open(EMISSION_FILE, "r", encoding="utf-8") as file:
        return json.load(file)


def _confidence_for(fuel: str, field: str) -> str | None:
    """Return confidence tag for a named field in a fuel record."""
    try:
        record = get_emission_factor(fuel)
        param = record.get(field)
        if isinstance(param, dict):
            return param.get("confidence")
    except Exception:
        pass
    return None


def calculate_biogas_co2(biogas_m3_day: float) -> dict:
    """
    Calculate biogas CO2 emissions.

    Formula:
        Energy (MJ/day) = biogas_volume (m³/day) × NCV (MJ/m³)
        CO2 (tCO2/day)  = Energy (TJ/day) × emission_factor (tCO2/TJ)

    Values are unwrapped from the v2.0 nested schema via helper functions.
    Confidence metadata is included in the returned dict.
    """
    ncv_mj_m3 = get_ncv_value("biogas")
    emission_factor_tco2_tj = get_emission_factor_value("biogas")

    energy_mj_day = biogas_m3_day * ncv_mj_m3
    energy_tj_day = energy_mj_day / 1_000_000
    co2_tco2_day = energy_tj_day * emission_factor_tco2_tj

    return {
        "fuel": "biogas",
        "fuel_consumption_m3_day": biogas_m3_day,
        "energy_mj_day": round(energy_mj_day, 2),
        "energy_tj_day": round(energy_tj_day, 6),
        "emission_factor_tco2_tj": emission_factor_tco2_tj,
        "emission_factor_confidence": _confidence_for("biogas", "emission_factor"),
        "ncv_mj_m3": ncv_mj_m3,
        "ncv_confidence": _confidence_for("biogas", "ncv"),
        "co2_tco2_day": round(co2_tco2_day, 4),
        "co2_kg_day": round(co2_tco2_day * 1000, 2),
    }


def calculate_fuel_co2(
    fuel: str,
    consumption_kg_day: float,
) -> dict:
    """
    Generic CO2 calculator for any supported fuel (by mass).

    Parameters
    ----------
    fuel :
        Fuel identifier as used in emission_factors.json
        (e.g. 'coal', 'diesel', 'lpg', 'natural_gas', 'furnace_oil').
    consumption_kg_day :
        Fuel consumption in kg/day.

    Returns a dict including CO2 in tCO2/day and confidence metadata.
    """
    emission_factor_tco2_tj = get_emission_factor_value(fuel)
    ncv_tj_kt = get_ncv_value(fuel)

    # Convert kg/day → kt/day → TJ/day
    consumption_kt_day = consumption_kg_day / 1_000_000
    energy_tj_day = consumption_kt_day * ncv_tj_kt
    co2_tco2_day = energy_tj_day * emission_factor_tco2_tj

    return {
        "fuel": fuel,
        "fuel_consumption_kg_day": consumption_kg_day,
        "energy_tj_day": round(energy_tj_day, 6),
        "emission_factor_tco2_tj": emission_factor_tco2_tj,
        "emission_factor_confidence": _confidence_for(fuel, "emission_factor"),
        "ncv_tj_kt": ncv_tj_kt,
        "ncv_confidence": _confidence_for(fuel, "ncv"),
        "co2_tco2_day": round(co2_tco2_day, 4),
        "co2_kg_day": round(co2_tco2_day * 1000, 2),
    }


if __name__ == "__main__":

    biogas_required = 2263.58

    result = calculate_biogas_co2(biogas_required)

    print("Biogas CO2 Calculator")
    print("---------------------")

    for key, value in result.items():
        print(f"{key}: {value}")

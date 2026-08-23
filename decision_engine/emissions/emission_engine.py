"""
Emission Engine
===============

Computes fuel combustion CO₂ for a declared time basis.

Critical design rules (Task 3.1 / research validation):
- Caller MUST declare the period of the consumption quantity.
- Function returns BOTH daily and annual values so unit errors cannot recur.
- Biogenic vs fossil accounting is explicit.
- NCV must be present; null NCV fails closed.
"""

from __future__ import annotations

from typing import Any, Literal

from decision_engine.emissions.emission_factors import get_emission_factor
from decision_engine.validation.validation_engine import ValidationEngine

_VALIDATION_ENGINE = ValidationEngine()

Period = Literal["day", "year"]


def calculate_fuel_emissions(
    fuel: str,
    consumption: float,
    *,
    period: Period = "day",
    operating_days_per_year: float | None = None,
) -> dict[str, Any]:
    """
    Calculate CO₂ emissions for a fuel.

    Parameters
    ----------
    fuel :
        Fuel key (coal, biomass, biogas, …).
    consumption :
        Quantity in the fuel’s canonical input unit
        (see emission_factors.json → input_unit).
    period :
        Whether `consumption` is a daily or annual quantity.
    operating_days_per_year :
        Required when period="year" is not used and daily→annual
        conversion is needed, or when period="day" and annual
        values are requested. Defaults to 300 if omitted.

    Returns
    -------
    dict with both daily and annual results, plus provenance.
    """
    fuel = fuel.lower().strip()
    data = get_emission_factor(fuel)

    ncv = data.get("ncv")
    emission_factor = data.get("emission_factor")  # tCO₂ / TJ
    ncv_unit = data.get("ncv_unit")

    # ---- validation -------------------------------------------------------
    category = (
        "biogenic_combustion"
        if "biogenic" in str(data.get("source_type", "")).lower()
        else "fossil_combustion"
    )

    validation = _VALIDATION_ENGINE.validate_emission_factor(
        parameter=f"{fuel}_emission_factor",
        emission_factor=emission_factor,
        emission_factor_unit=data["unit"],
        category=category,
    )
    if not validation.passed:
        raise ValueError(
            "Emission-factor validation failed: "
            + "; ".join(i.message for i in validation.issues)
        )

    if ncv is None:
        raise ValueError(
            f"NCV is not configured for fuel '{fuel}'. "
            "A fuel without a validated net calorific value cannot be "
            "converted into energy or emissions."
        )

    if operating_days_per_year is None:
        operating_days_per_year = 300.0
    if operating_days_per_year <= 0:
        raise ValueError("operating_days_per_year must be > 0")

    # ---- normalise to daily quantity --------------------------------------
    if period == "day":
        consumption_per_day = float(consumption)
    elif period == "year":
        consumption_per_day = float(consumption) / operating_days_per_year
    else:
        raise ValueError(f"Unsupported period: {period!r}")

    # ---- energy (TJ/day) --------------------------------------------------
    if ncv_unit == "TJ/kt":
        # kg/day → kt/day
        consumption_kt_day = consumption_per_day / 1_000_000.0
        energy_tj_day = consumption_kt_day * ncv
    elif ncv_unit == "MJ/m3":
        energy_mj_day = consumption_per_day * ncv
        energy_tj_day = energy_mj_day / 1_000_000.0
    else:
        raise ValueError(f"Unsupported NCV unit: {ncv_unit}")

    co2_tco2_day = energy_tj_day * emission_factor
    co2_tco2_year = co2_tco2_day * operating_days_per_year

    return {
        "fuel": fuel,
        "period_of_input": period,
        "consumption_input": float(consumption),
        "consumption_per_day": round(consumption_per_day, 6),
        "operating_days_per_year": float(operating_days_per_year),
        "energy_tj_day": round(energy_tj_day, 9),
        "energy_tj_year": round(energy_tj_day * operating_days_per_year, 9),
        "emission_factor_tco2_tj": emission_factor,
        "category": category,
        "co2_tco2_day": round(co2_tco2_day, 6),
        "co2_tco2_year": round(co2_tco2_year, 6),
        "co2_kg_day": round(co2_tco2_day * 1000.0, 3),
        "co2_kg_year": round(co2_tco2_year * 1000.0, 3),
        "source_id": data.get("source_id"),
        "source_type": data.get("source_type"),
        "is_biogenic": category == "biogenic_combustion",
    }


def compare_fuels(
    existing_fuel: str,
    existing_consumption: float,
    replacement_fuel: str,
    replacement_consumption: float,
    *,
    period: Period = "day",
    operating_days_per_year: float | None = None,
) -> dict[str, Any]:
    """Compare two fuels on the same time basis."""
    existing = calculate_fuel_emissions(
        existing_fuel,
        existing_consumption,
        period=period,
        operating_days_per_year=operating_days_per_year,
    )
    replacement = calculate_fuel_emissions(
        replacement_fuel,
        replacement_consumption,
        period=period,
        operating_days_per_year=operating_days_per_year,
    )

    return {
        "existing_fuel": existing_fuel,
        "existing_co2_tco2_year": existing["co2_tco2_year"],
        "replacement_fuel": replacement_fuel,
        "replacement_co2_tco2_year": replacement["co2_tco2_year"],
        "co2_difference_tco2_year": round(
            existing["co2_tco2_year"] - replacement["co2_tco2_year"], 6
        ),
        "existing_is_biogenic": existing["is_biogenic"],
        "replacement_is_biogenic": replacement["is_biogenic"],
    }


if __name__ == "__main__":
    print("Emission Engine – period-aware")
    print("-" * 40)

    # Daily coal
    r = calculate_fuel_emissions("coal", 2000.0, period="day")
    for k, v in r.items():
        print(f"{k}: {v}")

    print()

    # Annual coal (should give same daily values)
    r2 = calculate_fuel_emissions(
        "coal", 2000.0 * 300, period="year", operating_days_per_year=300
    )
    print("Annual path co2_tco2_year:", r2["co2_tco2_year"])
    print("Daily path co2_tco2_year :", r["co2_tco2_year"])
"""
decision_engine/baseline/baseline_engine.py

Computes the immutable current-state BaselineProfile for a Factory.

Flow
----
Factory
  → Fuel input energy + thermal energy balance (validated)
  → Electricity demand
  → Energy costs
  → Fuel + electricity emissions (correct daily → annual conversion)
  → FuelConsumptionProfile + EnergyBalance objects
  → BaselineProfile (with full provenance / assumptions)

Task-3.1 / research-policy rules applied here
---------------------------------------------
1. Annual fuel CO₂ must never be taken from a field named *_day.
2. Grid emission factor accounting basis is explicit.
3. Planning defaults carry evidence records (propagated from energy_calculator).
4. Assumptions stay versioned and traceable; no silent fabrication.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from models.factory import Factory
from decision_engine.baseline.energy_calculator import (
    calculate_annual_electricity_demand,
    calculate_annual_electricity_energy_mj,
    calculate_annual_total_energy_input_mj,
    calculate_energy_balance,
    calculate_energy_intensity,
    validate_energy_balance,
)
from decision_engine.baseline.fuel_calculator import (
    calculate_annual_energy_cost,
)
from decision_engine.baseline.models import (
    BaselineProfile,
    EnergyBalance,
    FuelConsumptionProfile,
)
from decision_engine.emissions.emission_engine import (
    calculate_fuel_emissions,
)
from decision_engine.emissions.emission_factors import (
    get_emission_factor,
    get_grid_emission_factor,
)
from decision_engine.validation.validation_engine import ValidationEngine

BASE_DIR = Path(__file__).resolve().parents[2]

_VALIDATION_ENGINE = ValidationEngine(
    references_root=(
        BASE_DIR
        / "knowledge-base"
        / "references"
    )
)

# Explicit default used when grid_factors.json is missing or malformed.
# Matches CEA "weighted_average_including_res_and_captive" for FY 2024-25.
_DEFAULT_GRID_FACTOR_KGCO2E_PER_KWH = 0.7117
_DEFAULT_GRID_FACTOR_BASIS = (
    "weighted_average_including_res_and_captive"
)
_DEFAULT_GRID_FACTOR_SOURCE = (
    "CEA CO2 Baseline Database for the Indian Power Sector v21.0 "
    "(November 2025) – weighted average including RES & captive"
)


# ---------------------------------------------------------------------------
# Grid emission factor — explicit accounting basis (Task 4)
# ---------------------------------------------------------------------------

def _validate_grid_emission_factor(grid_factor: float) -> float:
    """Validate a numeric grid factor (kgCO2e/kWh)."""
    grid_validation = _VALIDATION_ENGINE.validate_unit(
        name="grid_emission_factor",
        value=grid_factor,
        unit="kgCO2e/kWh",
        expected_unit="kgCO2e/kWh",
        minimum=0.0,
    )
    if not grid_validation.passed:
        raise ValueError(
            "Grid emission factor validation failed: "
            + "; ".join(issue.message for issue in grid_validation.issues)
        )
    return float(grid_factor)


def _load_grid_emission_factor(
    basis: str | None = None,
) -> tuple[float, dict[str, Any]]:
    """
    Resolve the grid emission factor with full accounting metadata.

    The Factory contract does not yet expose a per-factory grid-factor
    selector, so the project default basis is used
    (weighted_average_including_res_and_captive). Callers that need OM/BM/CM
    must pass ``basis`` explicitly.

    Returns
    -------
    (factor_value_kgco2e_per_kwh, metadata_dict)
    """
    try:
        meta = get_grid_emission_factor(basis=basis)
        value = _validate_grid_emission_factor(meta["value"])
        return value, meta
    except (FileNotFoundError, ValueError, KeyError, TypeError, OSError):
        # Last-resort fallback only if knowledge-base is missing.
        # Still document the fallback so it is never silent.
        fallback_value = _DEFAULT_GRID_FACTOR_KGCO2E_PER_KWH
        fallback_meta = {
            "type": _DEFAULT_GRID_FACTOR_BASIS,
            "basis_key": _DEFAULT_GRID_FACTOR_BASIS,
            "value": fallback_value,
            "unit": "kgCO2e/kWh",
            "reporting_year": "FY 2024-25",
            "source_id": "CEA-CO2-BASELINE-V21-FALLBACK",
            "source_type": "government",
            "confidence": "medium",
            "status": "fallback",
            "is_project_default": True,
            "accounting_rationale": (
                "Hard-coded fallback used because grid_factors.json "
                "could not be loaded. Replace with knowledge-base value."
            ),
            "scope2_alignment": "location-based",
            "applicability": "planning_default_location_based",
            "source_document": _DEFAULT_GRID_FACTOR_SOURCE,
        }
        return _validate_grid_emission_factor(fallback_value), fallback_meta


def _build_fuel_profile(
    factory: Factory,
    annual_fuel_co2_tonnes: float,
) -> FuelConsumptionProfile:
    """
    Build the normalised annual fuel profile from the emission-factor
    knowledge base.
    """
    fuel = factory.current_fuel.lower().strip()
    ef_data = get_emission_factor(fuel)

    target_unit = ef_data["input_unit"]

    from decision_engine.baseline._units import (
        standardize_daily_consumption,
    )

    daily_consumption = standardize_daily_consumption(
        factory.fuel_consumption.value,
        factory.fuel_consumption.unit,
        target_unit,
    )

    annual_consumption = (
        daily_consumption * factory.operating_days_per_year
    )

    ncv = ef_data.get("ncv")
    ncv_unit = ef_data.get("ncv_unit")

    if ncv is None:
        raise ValueError(
            f"Cannot build fuel profile for '{fuel}' because NCV is missing. "
            "Biomass and other alternative fuels require a validated NCV "
            "before they can be used in the baseline."
        )

    if ncv_unit == "TJ/kt":
        annual_energy_tj = (annual_consumption / 1_000_000.0) * ncv
        annual_energy_mj = annual_energy_tj * 1_000_000.0

    elif ncv_unit == "MJ/m3":
        annual_energy_mj = annual_consumption * ncv
        annual_energy_tj = annual_energy_mj / 1_000_000.0

    else:
        raise ValueError(
            f"Unsupported NCV unit '{ncv_unit}' for fuel '{fuel}'."
        )

    return FuelConsumptionProfile(
        fuel=fuel,
        input_unit=target_unit,
        daily_consumption=float(daily_consumption),
        annual_consumption=float(annual_consumption),
        annual_fuel_input_energy_mj=float(round(annual_energy_mj, 6)),
        annual_fuel_input_energy_gj=float(
            round(annual_energy_mj / 1000.0, 6)
        ),
        annual_fuel_input_energy_tj=float(round(annual_energy_tj, 9)),
        emission_factor_tco2_per_tj=float(ef_data["emission_factor"]),
        annual_co2_tonnes=float(round(annual_fuel_co2_tonnes, 6)),
        source_id=ef_data.get("source_id"),
        source_type=ef_data.get("source_type"),
    )


def compute_baseline(factory: Factory) -> BaselineProfile:
    """
    Compute the immutable current-state baseline.

    Flow
    ----
    Factory
      ↓
    Fuel input energy
      ↓
    Boiler efficiency → distribution → process utilisation
      ↓
    Useful heat + losses (validated energy balance)
      ↓
    Fuel + electricity cost
      ↓
    Fuel + electricity emissions  (daily → annual conversion is explicit)
      ↓
    BaselineProfile
    """

    # ------------------------------------------------------------------
    # 1. Thermal energy balance (includes evidence records)
    # ------------------------------------------------------------------
    energy_balance_data = calculate_energy_balance(factory)

    # Hard validation of conservation of energy.
    validate_energy_balance(factory)

    annual_useful_heat_mj = energy_balance_data[
        "annual_process_useful_heat_mj"
    ]

    # ------------------------------------------------------------------
    # 2. Electricity
    # ------------------------------------------------------------------
    annual_electricity_kwh = calculate_annual_electricity_demand(factory)
    annual_electricity_mj = calculate_annual_electricity_energy_mj(factory)

    # ------------------------------------------------------------------
    # 3. Costs
    # ------------------------------------------------------------------
    # NOTE (MVP limitation – Task 3.1 item 6):
    # The cost engine currently excludes demand (kVA) charges because the
    # Factory contract does not supply contracted demand. Annual electricity
    # cost is therefore energy-only and must be treated as incomplete for
    # factories that face significant demand charges.
    costs = calculate_annual_energy_cost(
        factory,
        annual_fuel_base=None,
        annual_electricity_kwh=annual_electricity_kwh,
    )

    # ------------------------------------------------------------------
    # 4. Fuel emissions  ★ CRITICAL UNIT FIX ★
    # ------------------------------------------------------------------
    # calculate_fuel_emissions() is defined to accept *daily* consumption
    # and returns fields named *_day.  We therefore:
    #   a) convert the factory quantity to daily units,
    #   b) call the emissions engine with that daily value,
    #   c) scale the daily CO₂ result by operating days to obtain annual.
    #
    # Passing annual consumption into a daily API was the original bug
    # (dimensionally wrong by a factor of operating_days_per_year).
    fuel = factory.current_fuel.lower().strip()
    fuel_ef_data = get_emission_factor(fuel)

    from decision_engine.baseline._units import (
        standardize_daily_consumption,
    )

    daily_fuel_consumption = standardize_daily_consumption(
        factory.fuel_consumption.value,
        factory.fuel_consumption.unit,
        fuel_ef_data["input_unit"],
    )

    # Daily emissions (correct API usage)
    daily_fuel_emissions = calculate_fuel_emissions(
        fuel,
        daily_fuel_consumption,
    )

    daily_fuel_co2_tonnes = float(daily_fuel_emissions["co2_tco2_day"])

    # Explicit conversion to annual
    operating_days = float(factory.operating_days_per_year)
    annual_fuel_co2_tonnes = daily_fuel_co2_tonnes * operating_days

    # ------------------------------------------------------------------
    # 5. Electricity emissions — explicit grid accounting basis
    # ------------------------------------------------------------------
    grid_factor, grid_meta = _load_grid_emission_factor(
        basis=None  # project default; pass explicit basis when Factory supports it
    )

    # Convenience aliases used by provenance / assumptions
    grid_source_id = grid_meta.get("source_id")
    grid_basis = (
        grid_meta.get("basis_key")
        or grid_meta.get("type")
        or _DEFAULT_GRID_FACTOR_BASIS
    )

    electricity_co2_kg = annual_electricity_kwh * grid_factor
    annual_electricity_co2_tonnes = electricity_co2_kg / 1000.0

    annual_total_co2_tonnes = (
        annual_fuel_co2_tonnes + annual_electricity_co2_tonnes
    )

    # ------------------------------------------------------------------
    # 6. Total primary / purchased energy representation
    # ------------------------------------------------------------------
    annual_total_energy_input_mj = (
        calculate_annual_total_energy_input_mj(factory)
    )
    annual_total_energy_input_gj = annual_total_energy_input_mj / 1000.0

    # ------------------------------------------------------------------
    # 7. Normalised fuel profile
    # ------------------------------------------------------------------
    fuel_profile = _build_fuel_profile(
        factory=factory,
        annual_fuel_co2_tonnes=annual_fuel_co2_tonnes,
    )

    # ------------------------------------------------------------------
    # 8. Energy balance object
    # ------------------------------------------------------------------
    energy_balance = EnergyBalance(
        annual_fuel_input_energy_mj=energy_balance_data[
            "annual_fuel_input_energy_mj"
        ],
        annual_boiler_useful_heat_mj=energy_balance_data[
            "annual_boiler_useful_heat_mj"
        ],
        annual_distribution_useful_heat_mj=energy_balance_data[
            "annual_distribution_useful_heat_mj"
        ],
        annual_process_useful_heat_mj=energy_balance_data[
            "annual_process_useful_heat_mj"
        ],
        annual_boiler_losses_mj=energy_balance_data[
            "annual_boiler_losses_mj"
        ],
        annual_distribution_losses_mj=energy_balance_data[
            "annual_distribution_losses_mj"
        ],
        annual_process_losses_mj=energy_balance_data[
            "annual_process_losses_mj"
        ],
        annual_total_losses_mj=energy_balance_data[
            "annual_total_losses_mj"
        ],
        boiler_efficiency_pct=energy_balance_data[
            "boiler_efficiency_pct"
        ],
        steam_distribution_efficiency_pct=energy_balance_data[
            "steam_distribution_efficiency_pct"
        ],
        process_heat_utilization_pct=energy_balance_data[
            "process_heat_utilization_pct"
        ],
        overall_fuel_to_process_efficiency_pct=energy_balance_data[
            "overall_fuel_to_process_efficiency_pct"
        ],
        energy_balance_residual_mj=energy_balance_data[
            "energy_balance_residual_mj"
        ],
        assumptions=energy_balance_data.get("assumptions", {}),
    )

    # ------------------------------------------------------------------
    # 9. Energy intensity
    # ------------------------------------------------------------------
    energy_intensity = calculate_energy_intensity(
        factory,
        useful_heat_mj=annual_useful_heat_mj,
    )

    # ------------------------------------------------------------------
    # 10. Provenance
    # ------------------------------------------------------------------
    source_ids: list[str] = []

    fuel_source_id = fuel_ef_data.get("source_id")
    if fuel_source_id:
        source_ids.append(str(fuel_source_id))

    if grid_source_id:
        source_ids.append(str(grid_source_id))

    source_ids = sorted(set(source_ids))

    # ------------------------------------------------------------------
    # 11. Assumptions / transparency (full evidence records)
    # ------------------------------------------------------------------
    thermal_assumptions = energy_balance_data.get("assumptions", {})

    calculation_assumptions: dict[str, Any] = {
        "thermal_model": {
            "boiler_efficiency_pct": energy_balance.boiler_efficiency_pct,
            "steam_distribution_efficiency_pct": (
                energy_balance.steam_distribution_efficiency_pct
            ),
            "process_heat_utilization_pct": (
                energy_balance.process_heat_utilization_pct
            ),
            "assumption_status": "planning_default",
            "evidence": thermal_assumptions.get("evidence", {}),
            "important_note": (
                "These are planning assumptions because the current "
                "Factory input contract does not include measured boiler, "
                "steam-distribution, condensate-recovery, or process-heat "
                "metering data. Replace with site measurements when available."
            ),
        },
        "electricity": {
            "unit_conversion": "1 kWh = 3.6 MJ",
            "grid_emission_factor_kgco2e_per_kwh": grid_factor,
            "grid_emission_factor_basis": grid_basis,
            "grid_emission_factor_source_id": grid_source_id,
            "grid_emission_factor_source_type": grid_meta.get("source_type"),
            "grid_emission_factor_reporting_year": grid_meta.get(
                "reporting_year"
            ),
            "grid_emission_factor_confidence": grid_meta.get("confidence"),
            "grid_emission_factor_status": grid_meta.get("status"),
            "grid_emission_factor_scope2_alignment": grid_meta.get(
                "scope2_alignment"
            ),
            "grid_emission_factor_note": (
                "Default is CEA weighted-average including RES & captive "
                f"({grid_factor} kgCO₂e/kWh, {grid_meta.get('reporting_year')}). "
                "Other CEA factors (operating margin, build margin, "
                "combined margin) exist in knowledge-base/emissions/"
                "grid_factors.json and can be selected once the Factory "
                "contract exposes a selector. Factors are never averaged."
            ),
            "cost_coverage_limitation": (
                "MVP electricity cost excludes demand (kVA) charges "
                "because the Factory contract does not supply contracted "
                "demand. Treat annual_electricity_cost_inr as energy-only "
                "and therefore incomplete for sites with material demand charges."
            ),
        },
        "fuel": {
            "fuel": fuel,
            "input_unit": fuel_ef_data.get("input_unit"),
            "ncv": fuel_ef_data.get("ncv"),
            "ncv_unit": fuel_ef_data.get("ncv_unit"),
            "emission_factor_tco2_per_tj": fuel_ef_data.get(
                "emission_factor"
            ),
            "emission_factor_source_id": fuel_source_id,
            "emission_factor_source_type": fuel_ef_data.get(
                "source_type"
            ),
            "daily_fuel_co2_tonnes": round(daily_fuel_co2_tonnes, 6),
            "operating_days_per_year": operating_days,
            "annual_fuel_co2_tonnes": round(annual_fuel_co2_tonnes, 6),
            "conversion_note": (
                "Daily CO₂ from emission_engine × operating_days_per_year "
                "→ annual_fuel_co2_tonnes. Never treat a *_day field as annual."
            ),
        },
        "energy_balance": {
            "validated": True,
            "residual_mj": energy_balance.energy_balance_residual_mj,
        },
        "emissions_boundary": {
            "note": (
                "Fuel CO₂ is calculated from the IPCC-style emission factor "
                "stored for the fuel. Biogenic fuels still produce physical "
                "combustion CO₂; the project's reported fossil/biogenic "
                "accounting boundary is applied downstream by the "
                "recommendation / emissions boundary layer, not by zeroing "
                "the physical factor here."
            ),
        },
    }

    return BaselineProfile(
        annual_thermal_energy_mj=annual_useful_heat_mj,
        annual_electricity_kwh=annual_electricity_kwh,
        annual_electricity_energy_mj=annual_electricity_mj,
        fuel_profile=fuel_profile,
        energy_balance=energy_balance,
        annual_fuel_cost_inr=costs["annual_fuel_cost_inr"],
        annual_electricity_cost_inr=costs["annual_electricity_cost_inr"],
        annual_total_energy_cost_inr=costs["total_energy_cost_inr"],
        annual_fuel_co2_tonnes=annual_fuel_co2_tonnes,
        annual_electricity_co2_tonnes=annual_electricity_co2_tonnes,
        annual_co2_tonnes=annual_total_co2_tonnes,
        annual_useful_heat_mj=annual_useful_heat_mj,
        annual_total_energy_input_mj=annual_total_energy_input_mj,
        annual_total_energy_input_gj=annual_total_energy_input_gj,
        annual_energy_intensity_mj_per_production_unit=energy_intensity,
        calculation_assumptions=calculation_assumptions,
        source_ids=source_ids,
    )
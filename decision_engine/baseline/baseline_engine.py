
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
)


BASE_DIR = Path(__file__).resolve().parents[2]


def _load_grid_emission_factor() -> tuple[float, str | None]:
    """
    Load the default grid emission factor.

    The current Factory contract does not yet contain a dedicated grid-factor
    selector. Therefore the baseline uses the repository's default factor.

    Future state-specific grid factors can be resolved here once the Factory
    contract includes the relevant selector.
    """
    grid_file = (
        BASE_DIR
        / "knowledge-base"
        / "emissions"
        / "grid_factors.json"
    )

    if not grid_file.exists():
        # Preserve the project's previous fallback.
        return 0.7117, None

    try:
        import json

        with grid_file.open(
            "r",
            encoding="utf-8",
        ) as file:
            grid_data = json.load(file)

        default_factor = grid_data.get("default_factor")

        if isinstance(default_factor, dict):
            value = default_factor.get("value")
            source_id = default_factor.get("source_id")

            if value is not None:
                return float(value), source_id

        if isinstance(default_factor, (float, int)):
            return float(default_factor), None

    except (
        OSError,
        ValueError,
        TypeError,
    ):
        pass

    return 0.7117, None


def _build_fuel_profile(
    factory: Factory,
    annual_fuel_co2_tonnes: float,
) -> FuelConsumptionProfile:
    """
    Build the normalized annual fuel profile from the existing emission-factor
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
        daily_consumption
        * factory.operating_days_per_year
    )

    ncv = ef_data.get("ncv")
    ncv_unit = ef_data.get("ncv_unit")

    if ncv is None:
        raise ValueError(
            f"Cannot build fuel profile for '{fuel}' because NCV is missing."
        )

    if ncv_unit == "TJ/kt":
        annual_energy_tj = (
            annual_consumption / 1_000_000.0
        ) * ncv
        annual_energy_mj = (
            annual_energy_tj * 1_000_000.0
        )

    elif ncv_unit == "MJ/m3":
        annual_energy_mj = (
            annual_consumption * ncv
        )
        annual_energy_tj = (
            annual_energy_mj / 1_000_000.0
        )

    else:
        raise ValueError(
            f"Unsupported NCV unit '{ncv_unit}' for fuel '{fuel}'."
        )

    return FuelConsumptionProfile(
        fuel=fuel,
        input_unit=target_unit,
        daily_consumption=float(daily_consumption),
        annual_consumption=float(annual_consumption),
        annual_fuel_input_energy_mj=float(
            round(annual_energy_mj, 6)
        ),
        annual_fuel_input_energy_gj=float(
            round(annual_energy_mj / 1000.0, 6)
        ),
        annual_fuel_input_energy_tj=float(
            round(annual_energy_tj, 9)
        ),
        emission_factor_tco2_per_tj=float(
            ef_data["emission_factor"]
        ),
        annual_co2_tonnes=float(
            round(annual_fuel_co2_tonnes, 6)
        ),
        source_id=ef_data.get("source_id"),
        source_type=ef_data.get("source_type"),
    )


def compute_baseline(factory: Factory) -> BaselineProfile:
    """
    Compute the immutable current-state baseline.

    Flow:

        Factory
          ↓
        Fuel input energy
          ↓
        Boiler efficiency
          ↓
        Steam/distribution efficiency
          ↓
        Process heat utilization
          ↓
        Useful heat + losses
          ↓
        Fuel + electricity cost
          ↓
        Fuel + electricity emissions
          ↓
        BaselineProfile
    """

    # ------------------------------------------------------------------
    # 1. Thermal energy balance
    # ------------------------------------------------------------------
    energy_balance_data = calculate_energy_balance(factory)

    # Hard validation of conservation of energy.
    validate_energy_balance(factory)

    annual_useful_heat_mj = (
        energy_balance_data[
            "annual_process_useful_heat_mj"
        ]
    )

    # ------------------------------------------------------------------
    # 2. Electricity
    # ------------------------------------------------------------------
    annual_electricity_kwh = (
        calculate_annual_electricity_demand(factory)
    )

    annual_electricity_mj = (
        calculate_annual_electricity_energy_mj(factory)
    )

    # ------------------------------------------------------------------
    # 3. Costs
    # ------------------------------------------------------------------
    costs = calculate_annual_energy_cost(
        factory,
        annual_fuel_base=None,
        annual_electricity_kwh=annual_electricity_kwh,
    )

    # ------------------------------------------------------------------
    # 4. Fuel emissions
    # ------------------------------------------------------------------
    fuel = factory.current_fuel.lower().strip()

    from decision_engine.baseline._units import (
        standardize_daily_consumption,
    )

    fuel_ef_data = get_emission_factor(fuel)

    daily_fuel_consumption = standardize_daily_consumption(
        factory.fuel_consumption.value,
        factory.fuel_consumption.unit,
        fuel_ef_data["input_unit"],
    )

    annual_fuel_consumption = (
        daily_fuel_consumption
        * factory.operating_days_per_year
    )

    fuel_emissions = calculate_fuel_emissions(
        fuel,
        annual_fuel_consumption,
    )

    annual_fuel_co2_tonnes = float(
        fuel_emissions["co2_tco2_day"]
    )

    # ------------------------------------------------------------------
    # 5. Electricity emissions
    # ------------------------------------------------------------------
    grid_factor, grid_source_id = (
        _load_grid_emission_factor()
    )

    electricity_co2_kg = (
        annual_electricity_kwh
        * grid_factor
    )

    annual_electricity_co2_tonnes = (
        electricity_co2_kg / 1000.0
    )

    annual_total_co2_tonnes = (
        annual_fuel_co2_tonnes
        + annual_electricity_co2_tonnes
    )

    # ------------------------------------------------------------------
    # 6. Total primary / purchased energy representation
    # ------------------------------------------------------------------
    annual_total_energy_input_mj = (
        calculate_annual_total_energy_input_mj(factory)
    )

    annual_total_energy_input_gj = (
        annual_total_energy_input_mj / 1000.0
    )

    # ------------------------------------------------------------------
    # 7. Normalized fuel profile
    # ------------------------------------------------------------------
    fuel_profile = _build_fuel_profile(
        factory=factory,
        annual_fuel_co2_tonnes=annual_fuel_co2_tonnes,
    )

    # ------------------------------------------------------------------
    # 8. Energy balance object
    # ------------------------------------------------------------------
    energy_balance = EnergyBalance(
        annual_fuel_input_energy_mj=(
            energy_balance_data[
                "annual_fuel_input_energy_mj"
            ]
        ),
        annual_boiler_useful_heat_mj=(
            energy_balance_data[
                "annual_boiler_useful_heat_mj"
            ]
        ),
        annual_distribution_useful_heat_mj=(
            energy_balance_data[
                "annual_distribution_useful_heat_mj"
            ]
        ),
        annual_process_useful_heat_mj=(
            energy_balance_data[
                "annual_process_useful_heat_mj"
            ]
        ),
        annual_boiler_losses_mj=(
            energy_balance_data[
                "annual_boiler_losses_mj"
            ]
        ),
        annual_distribution_losses_mj=(
            energy_balance_data[
                "annual_distribution_losses_mj"
            ]
        ),
        annual_process_losses_mj=(
            energy_balance_data[
                "annual_process_losses_mj"
            ]
        ),
        annual_total_losses_mj=(
            energy_balance_data[
                "annual_total_losses_mj"
            ]
        ),
        boiler_efficiency_pct=(
            energy_balance_data[
                "boiler_efficiency_pct"
            ]
        ),
        steam_distribution_efficiency_pct=(
            energy_balance_data[
                "steam_distribution_efficiency_pct"
            ]
        ),
        process_heat_utilization_pct=(
            energy_balance_data[
                "process_heat_utilization_pct"
            ]
        ),
        overall_fuel_to_process_efficiency_pct=(
            energy_balance_data[
                "overall_fuel_to_process_efficiency_pct"
            ]
        ),
        energy_balance_residual_mj=(
            energy_balance_data[
                "energy_balance_residual_mj"
            ]
        ),
        assumptions=(
            energy_balance_data["assumptions"]
        ),
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
        source_ids.append(fuel_source_id)

    if grid_source_id:
        source_ids.append(grid_source_id)

    source_ids = sorted(set(source_ids))

    # ------------------------------------------------------------------
    # 11. Assumptions / transparency
    # ------------------------------------------------------------------
    calculation_assumptions: dict[str, Any] = {
        "thermal_model": {
            "boiler_efficiency_pct": (
                energy_balance.boiler_efficiency_pct
            ),
            "steam_distribution_efficiency_pct": (
                energy_balance.steam_distribution_efficiency_pct
            ),
            "process_heat_utilization_pct": (
                energy_balance.process_heat_utilization_pct
            ),
            "assumption_status": "planning_default",
            "important_note": (
                "These are planning assumptions because the current "
                "Factory input contract does not include measured boiler, "
                "steam-distribution, condensate-recovery, or process heat "
                "metering data."
            ),
        },
        "electricity": {
            "unit_conversion": "1 kWh = 3.6 MJ",
            "grid_emission_factor_kgco2e_per_kwh": grid_factor,
            "grid_emission_factor_source_id": grid_source_id,
        },
        "fuel": {
            "fuel": fuel,
            "input_unit": fuel_ef_data.get("input_unit"),
            "ncv": fuel_ef_data.get("ncv"),
            "ncv_unit": fuel_ef_data.get("ncv_unit"),
            "emission_factor_tco2_per_tj": (
                fuel_ef_data.get("emission_factor")
            ),
            "emission_factor_source_id": (
                fuel_source_id
            ),
        },
        "energy_balance": {
            "validated": True,
            "residual_mj": (
                energy_balance.energy_balance_residual_mj
            ),
        },
    }

    return BaselineProfile(
        annual_thermal_energy_mj=annual_useful_heat_mj,
        annual_electricity_kwh=annual_electricity_kwh,
        annual_electricity_energy_mj=annual_electricity_mj,
        fuel_profile=fuel_profile,
        energy_balance=energy_balance,
        annual_fuel_cost_inr=costs[
            "annual_fuel_cost_inr"
        ],
        annual_electricity_cost_inr=costs[
            "annual_electricity_cost_inr"
        ],
        annual_total_energy_cost_inr=costs[
            "total_energy_cost_inr"
        ],
        annual_fuel_co2_tonnes=(
            annual_fuel_co2_tonnes
        ),
        annual_electricity_co2_tonnes=(
            annual_electricity_co2_tonnes
        ),
        annual_co2_tonnes=(
            annual_total_co2_tonnes
        ),
        annual_useful_heat_mj=annual_useful_heat_mj,
        annual_total_energy_input_mj=(
            annual_total_energy_input_mj
        ),
        annual_total_energy_input_gj=(
            annual_total_energy_input_gj
        ),
        annual_energy_intensity_mj_per_production_unit=(
            energy_intensity
        ),
        calculation_assumptions=(
            calculation_assumptions
        ),
        source_ids=source_ids,
    )

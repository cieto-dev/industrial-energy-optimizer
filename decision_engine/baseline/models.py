
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class EnergyBalance(BaseModel):
    """
    Research-backed current-state energy balance.

    All energy quantities are annual unless explicitly stated otherwise.

    Definitions:
    - fuel_input_energy_mj: chemical energy entering the boiler/heating system.
    - boiler_useful_heat_mj: useful heat leaving the boiler/heater boundary.
    - distribution_useful_heat_mj: heat remaining after steam/thermal-fluid
      distribution losses.
    - process_useful_heat_mj: heat ultimately delivered to the process.
    - total_fuel_related_losses_mj: all losses between fuel input and process
      useful heat.
    """

    model_config = ConfigDict(frozen=True)

    annual_fuel_input_energy_mj: float = Field(ge=0)
    annual_boiler_useful_heat_mj: float = Field(ge=0)
    annual_distribution_useful_heat_mj: float = Field(ge=0)
    annual_process_useful_heat_mj: float = Field(ge=0)

    annual_boiler_losses_mj: float = Field(ge=0)
    annual_distribution_losses_mj: float = Field(ge=0)
    annual_process_losses_mj: float = Field(ge=0)
    annual_total_losses_mj: float = Field(ge=0)

    boiler_efficiency_pct: float = Field(ge=0, le=100)
    steam_distribution_efficiency_pct: float = Field(ge=0, le=100)
    process_heat_utilization_pct: float = Field(ge=0, le=100)
    overall_fuel_to_process_efficiency_pct: float = Field(ge=0, le=100)

    # Accounting identity residual. Ideally zero (within floating tolerance).
    energy_balance_residual_mj: float

    # Useful for downstream explanation / audit trail.
    assumptions: dict[str, Any] = Field(default_factory=dict)


class FuelConsumptionProfile(BaseModel):
    """
    Normalized annual fuel-consumption information.
    """

    model_config = ConfigDict(frozen=True)

    fuel: str
    input_unit: str

    daily_consumption: float = Field(ge=0)
    annual_consumption: float = Field(ge=0)

    annual_fuel_input_energy_mj: float = Field(ge=0)
    annual_fuel_input_energy_gj: float = Field(ge=0)
    annual_fuel_input_energy_tj: float = Field(ge=0)

    emission_factor_tco2_per_tj: float = Field(ge=0)
    annual_co2_tonnes: float = Field(ge=0)

    source_id: str | None = None
    source_type: str | None = None


class BaselineProfile(BaseModel):
    """
    Immutable current-state baseline profile of the Factory.

    This is the canonical baseline object consumed by downstream modules.

    The baseline separates:
      1. purchased electricity,
      2. fuel input energy,
      3. useful process heat,
      4. thermal losses,
      5. energy costs,
      6. emissions.

    Pathways must be evaluated against this object without mutating it.
    """

    model_config = ConfigDict(frozen=True)

    # ---- Annual energy ----
    annual_thermal_energy_mj: float = Field(ge=0)
    annual_electricity_kwh: float = Field(ge=0)
    annual_electricity_energy_mj: float = Field(ge=0)

    # ---- Fuel / thermal system ----
    fuel_profile: FuelConsumptionProfile
    energy_balance: EnergyBalance

    # ---- Costs ----
    annual_fuel_cost_inr: float = Field(ge=0)
    annual_electricity_cost_inr: float = Field(ge=0)
    annual_total_energy_cost_inr: float = Field(ge=0)

    # ---- Emissions ----
    annual_fuel_co2_tonnes: float = Field(ge=0)
    annual_electricity_co2_tonnes: float = Field(ge=0)
    annual_co2_tonnes: float = Field(ge=0)

    # ---- Useful / reporting values ----
    annual_useful_heat_mj: float = Field(ge=0)
    annual_total_energy_input_mj: float = Field(ge=0)
    annual_total_energy_input_gj: float = Field(ge=0)
    annual_energy_intensity_mj_per_production_unit: float | None = Field(
        default=None,
        ge=0,
    )

    # ---- Transparency ----
    calculation_assumptions: dict[str, Any] = Field(default_factory=dict)
    source_ids: list[str] = Field(default_factory=list)

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class DataQualityWarning(BaseModel):
    """
    A structured warning emitted when a v2.0 parameter used in the baseline
    has Low confidence, a missing value, or a missing source_id.

    Consumers (UI, reports, optimizer) must surface these before issuing
    recommendations. A warning does not by itself block computation, but
    firm_recommendation_blocked in BaselineProfile must be checked.
    """

    model_config = ConfigDict(frozen=True)

    field: str
    """The parameter key that triggered the warning (e.g. 'ncv', 'emission_factor')."""

    fuel_or_context: str
    """Fuel identifier or context string (e.g. 'biomass')."""

    confidence: str | None
    """Confidence level: 'Low', 'Medium', 'High', or None if the field is absent."""

    source_id: str | None
    """source_id from the v2.0 parameter object, or None if absent."""

    message: str
    """Human-readable warning, ready to be shown in the UI or report."""

    is_blocking: bool = False
    """True when this warning caused firm_recommendation_blocked=True."""


class CostCoverageLimitation(BaseModel):
    """
    Explicit model for electricity and energy cost coverage limitations.
    """

    model_config = ConfigDict(frozen=True)

    demand_charge_modeled: bool = False
    cost_coverage: str = "energy_only"
    cost_coverage_status: str = "incomplete_mvp"
    limitation: str = ""
    uncertainty_flags: list[str] = Field(default_factory=list)


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

    Cost coverage (Task 3.1 item 6)
    ------------------------------
    annual_electricity_cost_inr is energy-only (no demand charges).
    See calculation_assumptions["electricity"]["cost_coverage_*"]
    and the top-level coverage fields for the explicit limitation.
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

    # ---- Task 6: explicit cost-coverage surface ----
    electricity_cost_coverage: str = Field(
        default="energy_only",
        description=(
            "MVP coverage of the electricity cost figure. "
            "'energy_only' means demand/fixed/duty charges are excluded."
        ),
    )
    electricity_cost_coverage_status: str = Field(
        default="incomplete_mvp",
        description=(
            "Status of the electricity cost figure. "
            "'incomplete_mvp' indicates the value must not be treated "
            "as a complete annual bill."
        ),
    )
    electricity_cost_coverage_limitation: str = Field(
        default=(
            "MVP electricity cost excludes demand (kVA/kW) charges, "
            "fixed charges and duty/surcharge because the Factory "
            "contract does not supply contracted demand. Treat "
            "annual_electricity_cost_inr as energy-only and therefore "
            "incomplete for sites with material demand charges."
        ),
        description="Human-readable coverage limitation for reports and UI.",
    )

    # ---- v2.0 data quality gate (mandatory; checked before recommendations) ----
    data_quality_warnings: list[DataQualityWarning] = Field(
        default_factory=list,
        description=(
            "Warnings raised when any parameter used in this baseline has "
            "Low confidence, a null value, or a missing source_id. "
            "Downstream optimizer MUST check this list before recommendations."
        ),
    )
    firm_recommendation_blocked: bool = Field(
        default=False,
        description=(
            "True when any mandatory parameter is absent or has no source_id. "
            "The baseline is computed but no firm recommendation may be issued "
            "without operator confirmation and data-gap resolution."
        ),
    )
    firm_recommendation_blocked_reasons: list[str] = Field(
        default_factory=list,
        description="Reasons why firm recommendations are blocked.",
    )
    parameter_confidence_summary: dict[str, str] = Field(
        default_factory=dict,
        description=(
            "Mapping of parameter name → confidence level for every "
            "quantitative KB parameter used in this baseline computation."
        ),
    )
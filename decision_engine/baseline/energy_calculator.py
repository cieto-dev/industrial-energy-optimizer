from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any

from models.factory import Factory
from decision_engine.baseline._units import standardize_daily_consumption
from decision_engine.emissions.emission_engine import calculate_fuel_emissions
from decision_engine.emissions.emission_factors import get_emission_factor
from decision_engine.validation.validation_engine import ValidationEngine
from decision_engine.research.assumption_registry import (
    get_assumption_registry,
    ResolvedAssumption,
)

_VALIDATION_ENGINE = ValidationEngine()
_ASSUMPTION_REGISTRY = get_assumption_registry()

MJ_PER_KWH = 3.6
MJ_PER_GJ = 1000.0
MJ_PER_TJ = 1_000_000.0


@dataclass(frozen=True)
class ThermalEfficiencyAssumptions:
    """
    Resolved thermal-efficiency values together with their full
    evidence records (Task 3.1).
    """

    boiler_efficiency_pct: float
    steam_distribution_efficiency_pct: float
    process_heat_utilization_pct: float
    boiler_evidence: dict[str, Any]
    distribution_evidence: dict[str, Any]
    process_evidence: dict[str, Any]

    def validate(self) -> None:
        for name, value in (
            ("boiler_efficiency_pct", self.boiler_efficiency_pct),
            (
                "steam_distribution_efficiency_pct",
                self.steam_distribution_efficiency_pct,
            ),
            (
                "process_heat_utilization_pct",
                self.process_heat_utilization_pct,
            ),
        ):
            if not 0 < value <= 100:
                raise ValueError(
                    f"{name} must be > 0 and <= 100; received {value}"
                )


def _normalize_percent(value: float, name: str) -> float:
    """Accept either 0-1 or 0-100 representation and return 0-100."""
    if value < 0:
        raise ValueError(f"{name} cannot be negative")
    if 0 < value <= 1:
        value *= 100.0
    if value > 100:
        raise ValueError(f"{name} cannot exceed 100%; received {value}")
    return value


def _get_factory_efficiency_assumptions(
    factory: Factory,
) -> ThermalEfficiencyAssumptions:
    """
    Resolve efficiency assumptions from the authoritative registry.

    Current Factory does not yet carry measured boiler/process efficiency
    fields. Therefore the baseline uses documented engineering defaults
    that carry full provenance, confidence and uncertainty metadata.
    """
    bundle = _ASSUMPTION_REGISTRY.get_thermal_efficiency_bundle()

    boiler = bundle["boiler_efficiency"]
    dist = bundle["steam_distribution_efficiency"]
    process = bundle["process_heat_utilization"]

    assumptions = ThermalEfficiencyAssumptions(
        boiler_efficiency_pct=_normalize_percent(
            boiler.value, "boiler_efficiency"
        ),
        steam_distribution_efficiency_pct=_normalize_percent(
            dist.value, "steam_distribution_efficiency"
        ),
        process_heat_utilization_pct=_normalize_percent(
            process.value, "process_heat_utilization"
        ),
        boiler_evidence=boiler.to_dict(),
        distribution_evidence=dist.to_dict(),
        process_evidence=process.to_dict(),
    )
    assumptions.validate()
    return assumptions


def calculate_annual_electricity_demand(factory: Factory) -> float:
    """Calculate annual electricity demand in kWh/year."""
    annual_kwh = (
        factory.electricity_consumption_kwh_day
        * factory.operating_days_per_year
    )
    return round(annual_kwh, 6)


def calculate_annual_electricity_energy_mj(factory: Factory) -> float:
    """Convert annual electricity demand from kWh to MJ. 1 kWh = 3.6 MJ."""
    annual_kwh = calculate_annual_electricity_demand(factory)
    return round(annual_kwh * MJ_PER_KWH, 6)


def calculate_annual_fuel_input_energy(
    factory: Factory,
) -> tuple[float, float, dict[str, Any]]:
    """
    Calculate annual fuel input energy.

    Returns:
        (
            annual_fuel_input_energy_mj,
            annual_fuel_input_energy_tj,
            emission_factor_data
        )
    """
    fuel_id = factory.current_fuel.lower().strip()
    emission_factor_data = get_emission_factor(fuel_id)

    target_unit = emission_factor_data["input_unit"]

    daily_consumption_in_target = standardize_daily_consumption(
        factory.fuel_consumption.value,
        factory.fuel_consumption.unit,
        target_unit,
    )

    annual_consumption = (
        daily_consumption_in_target * factory.operating_days_per_year
    )

    ncv = emission_factor_data.get("ncv")
    ncv_unit = emission_factor_data.get("ncv_unit")

    if ncv is None:
        raise ValueError(
            f"NCV is not configured for fuel '{fuel_id}'. "
            "A fuel without a validated energy content cannot be "
            "converted into thermal energy."
        )

    if ncv_unit == "TJ/kt":
        annual_consumption_kt = annual_consumption / 1_000_000.0
        annual_energy_tj = annual_consumption_kt * ncv
        annual_energy_mj = annual_energy_tj * MJ_PER_TJ

    elif ncv_unit == "MJ/m3":
        annual_energy_mj = annual_consumption * ncv
        annual_energy_tj = annual_energy_mj / MJ_PER_TJ

    else:
        raise ValueError(
            f"Unsupported NCV unit '{ncv_unit}' for fuel '{fuel_id}'."
        )

    return (
        round(annual_energy_mj, 6),
        round(annual_energy_tj, 9),
        emission_factor_data,
    )


def calculate_energy_balance(
    factory: Factory,
    *,
    efficiency_assumptions: ThermalEfficiencyAssumptions | None = None,
) -> dict[str, Any]:
    """
    Build a full annual thermal energy balance.

    Chain:
        fuel input → boiler/heater → steam/thermal distribution → process
        → useful process heat

    Losses are explicit at each stage. Every efficiency parameter carries
    its full evidence record (Task 3.1).
    """
    assumptions = (
        efficiency_assumptions
        if efficiency_assumptions is not None
        else _get_factory_efficiency_assumptions(factory)
    )
    assumptions.validate()

    annual_fuel_input_mj, annual_fuel_input_tj, ef_data = (
        calculate_annual_fuel_input_energy(factory)
    )

    boiler_eff = assumptions.boiler_efficiency_pct / 100.0
    distribution_eff = (
        assumptions.steam_distribution_efficiency_pct / 100.0
    )
    process_utilization = (
        assumptions.process_heat_utilization_pct / 100.0
    )

    annual_boiler_useful_heat_mj = annual_fuel_input_mj * boiler_eff
    annual_boiler_losses_mj = (
        annual_fuel_input_mj - annual_boiler_useful_heat_mj
    )

    annual_distribution_useful_heat_mj = (
        annual_boiler_useful_heat_mj * distribution_eff
    )
    annual_distribution_losses_mj = (
        annual_boiler_useful_heat_mj - annual_distribution_useful_heat_mj
    )

    annual_process_useful_heat_mj = (
        annual_distribution_useful_heat_mj * process_utilization
    )
    annual_process_losses_mj = (
        annual_distribution_useful_heat_mj - annual_process_useful_heat_mj
    )

    annual_total_losses_mj = (
        annual_boiler_losses_mj
        + annual_distribution_losses_mj
        + annual_process_losses_mj
    )

    reconstructed_input_mj = (
        annual_process_useful_heat_mj + annual_total_losses_mj
    )
    residual_mj = annual_fuel_input_mj - reconstructed_input_mj

    validation = _VALIDATION_ENGINE.validate_energy_balance(
        input_energy_mj=annual_fuel_input_mj,
        useful_energy_mj=annual_process_useful_heat_mj,
        loss_components_mj={
            "boiler_losses": annual_boiler_losses_mj,
            "distribution_losses": annual_distribution_losses_mj,
            "process_losses": annual_process_losses_mj,
        },
    )

    if not validation.passed:
        raise ValueError(
            "Thermal energy balance validation failed: "
            + "; ".join(issue.message for issue in validation.issues)
        )

    overall_efficiency = 0.0
    if annual_fuel_input_mj > 0:
        overall_efficiency = (
            annual_process_useful_heat_mj / annual_fuel_input_mj * 100.0
        )

    return {
        "annual_fuel_input_energy_mj": round(annual_fuel_input_mj, 6),
        "annual_fuel_input_energy_tj": round(annual_fuel_input_tj, 9),
        "annual_boiler_useful_heat_mj": round(annual_boiler_useful_heat_mj, 6),
        "annual_distribution_useful_heat_mj": round(
            annual_distribution_useful_heat_mj, 6
        ),
        "annual_process_useful_heat_mj": round(
            annual_process_useful_heat_mj, 6
        ),
        "annual_boiler_losses_mj": round(annual_boiler_losses_mj, 6),
        "annual_distribution_losses_mj": round(
            annual_distribution_losses_mj, 6
        ),
        "annual_process_losses_mj": round(annual_process_losses_mj, 6),
        "annual_total_losses_mj": round(annual_total_losses_mj, 6),
        "boiler_efficiency_pct": round(assumptions.boiler_efficiency_pct, 4),
        "steam_distribution_efficiency_pct": round(
            assumptions.steam_distribution_efficiency_pct, 4
        ),
        "process_heat_utilization_pct": round(
            assumptions.process_heat_utilization_pct, 4
        ),
        "overall_fuel_to_process_efficiency_pct": round(overall_efficiency, 4),
        "energy_balance_residual_mj": round(residual_mj, 9),
        "fuel": factory.current_fuel.lower().strip(),
        "emission_factor_tco2_per_tj": ef_data["emission_factor"],
        "emission_factor_source_id": ef_data.get("source_id"),
        "ncv": ef_data.get("ncv"),
        "ncv_unit": ef_data.get("ncv_unit"),
        # Full evidence records attached (Task 3.1)
        "assumptions": {
            "boiler_efficiency_pct": assumptions.boiler_efficiency_pct,
            "steam_distribution_efficiency_pct": (
                assumptions.steam_distribution_efficiency_pct
            ),
            "process_heat_utilization_pct": (
                assumptions.process_heat_utilization_pct
            ),
            "assumption_status": "planning_default",
            "evidence": {
                "boiler_efficiency": assumptions.boiler_evidence,
                "steam_distribution_efficiency": (
                    assumptions.distribution_evidence
                ),
                "process_heat_utilization": assumptions.process_evidence,
            },
        },
    }


def calculate_annual_thermal_demand(factory: Factory) -> float:
    """
    Backward-compatible annual thermal demand.
    Returns useful process heat (not raw fuel input energy).
    """
    balance = calculate_energy_balance(factory)
    return balance["annual_process_useful_heat_mj"]


def calculate_annual_useful_heat(factory: Factory) -> float:
    """Explicit alias for downstream modules."""
    return calculate_annual_thermal_demand(factory)


def calculate_annual_total_energy_input_mj(factory: Factory) -> float:
    """
    Total purchased/primary energy input:
        fuel input energy + purchased electricity energy
    """
    annual_fuel_input_mj, _, _ = calculate_annual_fuel_input_energy(factory)
    annual_electricity_mj = calculate_annual_electricity_energy_mj(factory)
    return round(annual_fuel_input_mj + annual_electricity_mj, 6)


def calculate_energy_intensity(
    factory: Factory,
    useful_heat_mj: float | None = None,
) -> float | None:
    """Calculate useful-heat intensity per unit of annual production."""
    if useful_heat_mj is None:
        useful_heat_mj = calculate_annual_useful_heat(factory)

    production_value = factory.production_per_day.value
    production_unit = factory.production_per_day.unit.lower().strip()

    if production_value <= 0:
        return None

    supported_mass_units = {
        "kg/day": 1_000.0,
        "tonnes/day": 1.0,
        "t/day": 1.0,
    }

    if production_unit not in supported_mass_units:
        return None

    daily_mass_tonnes = (
        production_value / 1_000.0
        if production_unit == "kg/day"
        else production_value
    )

    if daily_mass_tonnes <= 0:
        return None

    annual_production_tonnes = (
        daily_mass_tonnes * factory.operating_days_per_year
    )

    if annual_production_tonnes <= 0:
        return None

    return round(useful_heat_mj / annual_production_tonnes, 6)


def validate_energy_balance(
    factory: Factory,
    *,
    tolerance_mj: float = 1e-6,
) -> bool:
    """
    Validate conservation of energy for the modeled thermal boundary.
    """
    balance = calculate_energy_balance(factory)
    residual = abs(balance["energy_balance_residual_mj"])

    if residual > tolerance_mj:
        raise ValueError(
            "Energy balance failed: residual "
            f"{residual:.9f} MJ exceeds tolerance "
            f"{tolerance_mj:.9f} MJ."
        )
    return True
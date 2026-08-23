"""
decision_engine/baseline/energy_calculator.py

Annual thermal & electricity energy calculations for the industrial baseline
(digital twin).

Responsibilities
----------------
* Convert factory fuel + electricity inputs into consistent MJ / TJ units.
* Build an explicit multi-stage thermal energy balance
  (fuel input → boiler → distribution → process → useful heat).
* Attach parameter-level provenance, confidence and uncertainty records
  to every planning-default efficiency so the validation engine and
  downstream recommendation logic can treat them as evidence-backed
  assumptions rather than hard facts.
* Validate conservation of energy via the central ValidationEngine.

Design rules (Task 3.1 / research policy)
-----------------------------------------
* Never present planning defaults as measured plant data.
* Every important numeric assumption carries:
    parameter, value, unit, source_id, source_type, status,
    confidence, uncertainty, applicability.
* Research conflicts are NOT averaged; they remain separate evidence
  records (handled in the assumption registry / conflicts file).
* Units are normalised: 1 kWh = 3.6 MJ; MJ / GJ / TJ internally.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any

from models.factory import Factory
from decision_engine.baseline._units import standardize_daily_consumption
from decision_engine.emissions.emission_factors import get_emission_factor
from decision_engine.validation.validation_engine import ValidationEngine

_VALIDATION_ENGINE = ValidationEngine()

# ---------------------------------------------------------------------------
# Physical constants (explicit, not magic numbers)
# ---------------------------------------------------------------------------
MJ_PER_KWH = 3.6
MJ_PER_GJ = 1_000.0
MJ_PER_TJ = 1_000_000.0

# ---------------------------------------------------------------------------
# Planning-default thermal efficiencies WITH full evidence records
# ---------------------------------------------------------------------------
#
# These are engineering defaults used only when the Factory contract does not
# supply measured boiler / steam-distribution / process-heat utilisation data.
#
# Source basis (kept as separate evidence, never averaged):
#   - MNRE/GIZ biomass-for-MSME material: boiler & system performance matter
#     materially for industrial green heat/steam.
#   - Energy Innovation (April 2026): combustion systems lose efficiency through
#     the thermal conversion chain; electric end-uses can be far higher.
#   - Project industry profiles: steam systems and process temperatures vary.
#
# Status is deliberately "estimated" / "planning_default".
# Confidence is medium because the numbers are research-informed ranges,
# not site measurements.
# ---------------------------------------------------------------------------

DEFAULT_BOILER_EFFICIENCY = {
    "parameter": "boiler_efficiency",
    "value": 80.0,
    "unit": "percent",
    "source_id": "mnre_giz_biomass_msme + energy_innovation_2026 + project_industry_profiles",
    "source_type": "government|project_research",
    "status": "estimated",
    "confidence": "medium",
    "uncertainty": (
        "Site-specific; replace with measured boiler efficiency "
        "(or manufacturer curve at actual load) when available. "
        "Typical industrial solid/liquid-fuel boilers range 70-85 %."
    ),
    "applicability": "planning_default",
}

DEFAULT_STEAM_DISTRIBUTION_EFFICIENCY = {
    "parameter": "steam_distribution_efficiency",
    "value": 90.0,
    "unit": "percent",
    "source_id": "mnre_giz_biomass_msme + project_engineering_estimate",
    "source_type": "government|project_research",
    "status": "estimated",
    "confidence": "medium",
    "uncertainty": (
        "Site-specific; replace with measured distribution losses "
        "(pipe insulation, steam traps, condensate return) when available. "
        "Well-maintained systems can exceed 90 %; poorly insulated lines "
        "can fall well below."
    ),
    "applicability": "planning_default",
}

DEFAULT_PROCESS_HEAT_UTILIZATION = {
    "parameter": "process_heat_utilization",
    "value": 95.0,
    "unit": "percent",
    "source_id": "project_engineering_estimate + energy_innovation_2026",
    "source_type": "project_research",
    "status": "estimated",
    "confidence": "medium",
    "uncertainty": (
        "Site-specific; replace with measured process heat utilisation "
        "when available. Represents the fraction of delivered heat that "
        "actually performs useful work in the process."
    ),
    "applicability": "planning_default",
}


@dataclass(frozen=True)
class ThermalEfficiencyAssumptions:
    """Resolved efficiency set used by the energy-balance calculation."""

    boiler_efficiency_pct: float
    steam_distribution_efficiency_pct: float
    process_heat_utilization_pct: float
    # Full evidence records (kept separate so callers can surface them)
    evidence: dict[str, dict[str, Any]]

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
    """
    Accept either 0-1 or 0-100 representation and return 0-100.
    """
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
    Resolve efficiency assumptions for the current Factory.

    Current Factory contract does not yet carry measured boiler / process
    efficiency fields. Therefore the baseline uses the documented
    planning defaults together with their full evidence records.

    Future measured fields can be added to Factory without changing the
    calculation pipeline; this function is the single resolution point.
    """
    # In a later iteration these can be read from factory attributes
    # (e.g. factory.measured_boiler_efficiency_pct) when present.
    boiler = DEFAULT_BOILER_EFFICIENCY
    dist = DEFAULT_STEAM_DISTRIBUTION_EFFICIENCY
    util = DEFAULT_PROCESS_HEAT_UTILIZATION

    assumptions = ThermalEfficiencyAssumptions(
        boiler_efficiency_pct=float(boiler["value"]),
        steam_distribution_efficiency_pct=float(dist["value"]),
        process_heat_utilization_pct=float(util["value"]),
        evidence={
            "boiler_efficiency": dict(boiler),
            "steam_distribution_efficiency": dict(dist),
            "process_heat_utilization": dict(util),
        },
    )
    assumptions.validate()
    return assumptions


# ---------------------------------------------------------------------------
# Electricity
# ---------------------------------------------------------------------------

def calculate_annual_electricity_demand(factory: Factory) -> float:
    """
    Calculate annual electricity demand in kWh/year.
    """
    annual_kwh = (
        factory.electricity_consumption_kwh_day
        * factory.operating_days_per_year
    )
    return round(annual_kwh, 6)


def calculate_annual_electricity_energy_mj(factory: Factory) -> float:
    """
    Convert annual electricity demand from kWh to MJ.

    Explicit conversion: 1 kWh = 3.6 MJ.
    """
    annual_kwh = calculate_annual_electricity_demand(factory)
    return round(annual_kwh * MJ_PER_KWH, 6)


# ---------------------------------------------------------------------------
# Fuel input energy
# ---------------------------------------------------------------------------

def calculate_annual_fuel_input_energy(
    factory: Factory,
) -> tuple[float, float, dict[str, Any]]:
    """
    Calculate annual fuel input energy.

    Returns
    -------
    (
        annual_fuel_input_energy_mj,
        annual_fuel_input_energy_tj,
        emission_factor_data
    )

    Uses the emission-factor knowledge base because that dataset already
    contains validated NCV and source provenance.
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
        daily_consumption_in_target
        * factory.operating_days_per_year
    )

    ncv = emission_factor_data.get("ncv")
    ncv_unit = emission_factor_data.get("ncv_unit")

    if ncv is None:
        raise ValueError(
            f"NCV is not configured for fuel '{fuel_id}'. "
            "A fuel without a validated energy content cannot be "
            "converted into thermal energy. "
            "(Biomass pathways require a non-null NCV before they can "
            "be used in the baseline.)"
        )

    if ncv_unit == "TJ/kt":
        # Annual consumption is kg/year for the fuels using this basis.
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


# ---------------------------------------------------------------------------
# Full thermal energy balance
# ---------------------------------------------------------------------------

def calculate_energy_balance(
    factory: Factory,
    *,
    efficiency_assumptions: ThermalEfficiencyAssumptions | None = None,
) -> dict[str, Any]:
    """
    Build a full annual thermal energy balance.

    Chain
    -----
        fuel input
            ↓
        boiler / heater
            ↓
        steam / thermal distribution
            ↓
        process
            ↓
        useful process heat

    Losses are explicit at each stage. This is preferable to treating
    fuel energy as if it were directly equal to process heat.
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
        annual_boiler_useful_heat_mj
        - annual_distribution_useful_heat_mj
    )

    annual_process_useful_heat_mj = (
        annual_distribution_useful_heat_mj
        * process_utilization
    )
    annual_process_losses_mj = (
        annual_distribution_useful_heat_mj
        - annual_process_useful_heat_mj
    )

    annual_total_losses_mj = (
        annual_boiler_losses_mj
        + annual_distribution_losses_mj
        + annual_process_losses_mj
    )

    reconstructed_input_mj = (
        annual_process_useful_heat_mj
        + annual_total_losses_mj
    )

    residual_mj = annual_fuel_input_mj - reconstructed_input_mj

    # Central validation engine – physical conservation check
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
            + "; ".join(
                issue.message
                for issue in validation.issues
            )
        )

    overall_efficiency = 0.0
    if annual_fuel_input_mj > 0:
        overall_efficiency = (
            annual_process_useful_heat_mj
            / annual_fuel_input_mj
            * 100.0
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
        "boiler_efficiency_pct": round(
            assumptions.boiler_efficiency_pct, 4
        ),
        "steam_distribution_efficiency_pct": round(
            assumptions.steam_distribution_efficiency_pct, 4
        ),
        "process_heat_utilization_pct": round(
            assumptions.process_heat_utilization_pct, 4
        ),
        "overall_fuel_to_process_efficiency_pct": round(
            overall_efficiency, 4
        ),
        "energy_balance_residual_mj": round(residual_mj, 9),
        "fuel": factory.current_fuel.lower().strip(),
        "emission_factor_tco2_per_tj": ef_data["emission_factor"],
        "emission_factor_source_id": ef_data.get("source_id"),
        "ncv": ef_data.get("ncv"),
        "ncv_unit": ef_data.get("ncv_unit"),
        # Full evidence records – required by Task 3.1
        "assumptions": {
            "boiler_efficiency_pct": assumptions.boiler_efficiency_pct,
            "steam_distribution_efficiency_pct": (
                assumptions.steam_distribution_efficiency_pct
            ),
            "process_heat_utilization_pct": (
                assumptions.process_heat_utilization_pct
            ),
            "assumption_status": "planning_default",
            "evidence": assumptions.evidence,
            "important_note": (
                "These are planning assumptions because the current "
                "Factory input contract does not include measured boiler, "
                "steam-distribution, condensate-recovery, or process-heat "
                "metering data. Replace with site measurements when available."
            ),
        },
    }


# ---------------------------------------------------------------------------
# Convenience / downstream helpers
# ---------------------------------------------------------------------------

def calculate_annual_thermal_demand(factory: Factory) -> float:
    """
    Backward-compatible annual thermal demand.

    IMPORTANT
    ---------
    Returns *useful process heat* (not raw fuel input energy).
    This aligns the baseline with the requirement to distinguish
    fuel input from useful heat.
    """
    balance = calculate_energy_balance(factory)
    return balance["annual_process_useful_heat_mj"]


def calculate_annual_useful_heat(factory: Factory) -> float:
    """Explicit alias for downstream modules."""
    return calculate_annual_thermal_demand(factory)


def calculate_annual_total_energy_input_mj(factory: Factory) -> float:
    """
    Total purchased / primary energy input represented by the current baseline:

        fuel input energy + purchased electricity energy
    """
    annual_fuel_input_mj, _, _ = calculate_annual_fuel_input_energy(factory)
    annual_electricity_mj = calculate_annual_electricity_energy_mj(factory)
    return round(annual_fuel_input_mj + annual_electricity_mj, 6)


def calculate_energy_intensity(
    factory: Factory,
    useful_heat_mj: float | None = None,
) -> float | None:
    """
    Calculate useful-heat intensity per unit of annual production.

    Production units are normalised only when the supplied factory unit is
    explicitly supported.
    """
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
    Validate conservation of energy for the modelled thermal boundary.

    Fuel input energy must equal useful process heat plus all modelled losses,
    within the specified numerical tolerance.
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
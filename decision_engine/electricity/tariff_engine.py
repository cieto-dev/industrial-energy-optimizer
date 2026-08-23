# `decision_engine/electricity/tariff_engine.py`


"""
Industrial Electricity Tariff Engine
====================================

Decision Engine / Electricity Layer
-----------------------------------

Purpose
-------
Provides a production-oriented electricity tariff calculation and comparison
engine for the Industrial Energy Transition Optimizer.

Core responsibilities
---------------------
1. Industrial tariff lookup
2. DISCOM lookup
3. Time-of-Day (TOD) tariff logic
4. Demand-charge calculation
5. Fixed-charge calculation
6. Energy-charge calculation
7. Electricity duty / surcharge handling
8. State tariff comparison
9. Tariff escalation projections
10. Renewable electricity procurement scenarios
11. Green Energy Open Access suitability screening
12. Grid emission factor estimation
13. Result dataclasses and stable integration contracts
14. CSV loading
15. Validation and error handling
16. Compatibility with repository decision-engine consumers

Design principles
-----------------
- Explicit units
- Deterministic calculations
- No hidden assumptions
- No silent fallback to invented tariff values
- Source metadata preserved
- Current tariff values remain data-driven
- Historical / estimated / proposed values are explicitly flagged
- All monetary values are INR unless otherwise noted
- Energy is represented in kWh
- Demand is represented in kW or kVA depending on tariff basis
- Annual totals are based on 12 billing periods unless configured otherwise

Important evidence rule
-----------------------
State-specific tariff values should ideally come from official SERC / DISCOM
orders. Where research data is incomplete or conflicting, the engine allows
the caller to inject verified tariff records or load CSV data instead of
hard-coding uncertain numbers.

Typical usage
-------------
    engine = TariffEngine()

    result = engine.calculate_bill(
        state="Tamil Nadu",
        discom="TANGEDCO",
        tariff_category="HT_IIA",
        monthly_energy_kwh=12500,
        contracted_demand_kva=100,
        maximum_demand_kva=85,
        billing_months=12,
    )

    comparison = engine.compare_states(
        states=["Tamil Nadu", "Karnataka", "Gujarat"],
        tariff_category="industrial",
        monthly_energy_kwh=12500,
        demand_kw=100,
    )

    projection = engine.project_escalation(
        base_result=result,
        years=5,
        annual_escalation_rate=0.06,
    )

    oa = engine.assess_open_access(
        annual_consumption_kwh=2_000_000,
        contracted_demand_kw=500,
        annual_renewable_generation_kwh=1_500_000,
    )

Repository integration
---------------------
The module is intentionally self-contained. It can operate using:
- embedded baseline tariff records,
- caller-supplied tariff records,
- CSV tariff files,
- dictionaries loaded from application data.

The engine does not require pandas or NumPy. Standard library Python is used
for portability and predictable deployment.

"""

from __future__ import annotations

import csv
import math
import os
from dataclasses import asdict, dataclass, field
from datetime import date, datetime
from pathlib import Path
from typing import (
    Any,
    Dict,
    Iterable,
    List,
    Mapping,
    MutableMapping,
    Optional,
    Sequence,
    Tuple,
    Union,
)


# ============================================================================
# Exceptions
# ============================================================================


class TariffEngineError(Exception):
    """Base exception for tariff-engine failures."""


class TariffValidationError(TariffEngineError, ValueError):
    """Raised when tariff input fails validation."""


class TariffNotFoundError(TariffEngineError, LookupError):
    """Raised when no tariff record matches the requested lookup."""


class TariffDataError(TariffEngineError):
    """Raised when tariff data cannot be loaded or interpreted safely."""


class UnsupportedCalculationError(TariffEngineError):
    """Raised when a requested calculation cannot be performed."""


# ============================================================================
# Constants
# ============================================================================


MONTHS_PER_YEAR = 12
DEFAULT_BILLING_DAYS = 30
DEFAULT_ESCALATION_RATE = 0.05

# Generic grid emission-factor fallback only.
# This is deliberately kept as a configurable assumption rather than a claim
# that it is the official India grid factor.
DEFAULT_GRID_EMISSION_FACTOR_KG_CO2_PER_KWH = 0.70

DEFAULT_GREEN_POWER_EMISSION_FACTOR_KG_CO2_PER_KWH = 0.05

# Green Energy Open Access Rules commonly use 100 kW as the eligibility
# threshold. This is configurable because applicable rules/orders may change.
DEFAULT_GEOA_MIN_CONTRACTED_LOAD_KW = 100.0

VALID_BASIS = {"kW", "kVA"}

TARIFF_STATUS_VALUES = {
    "current",
    "historical",
    "estimated",
    "provisional",
    "proposed",
    "unknown",
}

SOURCE_CONFIDENCE_VALUES = {
    "high",
    "medium",
    "low",
    "unknown",
}


# ============================================================================
# Utility functions
# ============================================================================


def _clean_text(value: Any) -> str:
    """Normalize a value to a trimmed string."""
    if value is None:
        return ""
    return str(value).strip()


def _normalize_key(value: Any) -> str:
    """Create a lookup-safe key."""
    text = _clean_text(value).lower()
    return (
        text.replace("&", "and")
        .replace("-", "_")
        .replace(" ", "_")
        .replace("/", "_")
    )


def _safe_float(
    value: Any,
    *,
    field_name: str,
    minimum: Optional[float] = None,
    maximum: Optional[float] = None,
    allow_none: bool = False,
) -> Optional[float]:
    """Convert input to float and validate numerical bounds."""
    if value is None and allow_none:
        return None

    if isinstance(value, bool):
        raise TariffValidationError(
            f"{field_name} must be numeric, not boolean."
        )

    try:
        result = float(value)
    except (TypeError, ValueError) as exc:
        raise TariffValidationError(
            f"{field_name} must be numeric; received {value!r}."
        ) from exc

    if not math.isfinite(result):
        raise TariffValidationError(
            f"{field_name} must be finite; received {value!r}."
        )

    if minimum is not None and result < minimum:
        raise TariffValidationError(
            f"{field_name} must be >= {minimum}; received {result}."
        )

    if maximum is not None and result > maximum:
        raise TariffValidationError(
            f"{field_name} must be <= {maximum}; received {result}."
        )

    return result


def _safe_int(
    value: Any,
    *,
    field_name: str,
    minimum: Optional[int] = None,
    maximum: Optional[int] = None,
) -> int:
    """Convert input to int and validate bounds."""
    try:
        result = int(value)
    except (TypeError, ValueError) as exc:
        raise TariffValidationError(
            f"{field_name} must be an integer; received {value!r}."
        ) from exc

    if minimum is not None and result < minimum:
        raise TariffValidationError(
            f"{field_name} must be >= {minimum}; received {result}."
        )

    if maximum is not None and result > maximum:
        raise TariffValidationError(
            f"{field_name} must be <= {maximum}; received {result}."
        )

    return result


def _round_money(value: float) -> float:
    """Round INR monetary value to two decimal places."""
    return round(float(value), 2)


def _round_energy(value: float) -> float:
    """Round energy values to six decimal places."""
    return round(float(value), 6)


def _round_rate(value: float) -> float:
    """Round tariff/rate values to six decimal places."""
    return round(float(value), 6)


def _coalesce(value: Any, default: Any) -> Any:
    """Return default when value is None or blank text."""
    if value is None:
        return default
    if isinstance(value, str) and not value.strip():
        return default
    return value


def _annualize_monthly(value: float, months: int = MONTHS_PER_YEAR) -> float:
    """Annualize a monthly amount."""
    return float(value) * months


# ============================================================================
# Dataclasses
# ============================================================================


@dataclass(frozen=True)
class TODPeriod:
    """
    A Time-of-Day tariff period.

    start_hour/end_hour:
        Decimal hours in [0, 24). End is exclusive under the tariff engine.

    multiplier:
        Multiplier applied to the base energy tariff.

    surcharge_pct:
        Percentage added to the base tariff.

    discount_pct:
        Percentage deducted from the base tariff.

    priority:
        Used if overlapping periods exist. Higher priority wins.
    """

    name: str
    start_hour: float
    end_hour: float
    multiplier: float = 1.0
    surcharge_pct: float = 0.0
    discount_pct: float = 0.0
    priority: int = 0

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise TariffValidationError("TOD period name cannot be empty.")

        if not 0 <= self.start_hour < 24:
            raise TariffValidationError(
                "TOD start_hour must be in [0, 24)."
            )

        if not 0 < self.end_hour <= 24:
            raise TariffValidationError(
                "TOD end_hour must be in (0, 24]."
            )

        if self.start_hour == self.end_hour:
            raise TariffValidationError(
                "TOD period cannot have identical start/end hour."
            )

        if self.multiplier <= 0:
            raise TariffValidationError(
                "TOD multiplier must be > 0."
            )

        if self.surcharge_pct < 0:
            raise TariffValidationError(
                "TOD surcharge_pct cannot be negative."
            )

        if self.discount_pct < 0 or self.discount_pct > 100:
            raise TariffValidationError(
                "TOD discount_pct must be between 0 and 100."
            )


@dataclass(frozen=True)
class TariffSlab:
    """
    Optional energy-charge slab.

    upper_kwh:
        Upper boundary for the slab. None means unlimited.

    rate_inr_per_kwh:
        Energy rate for that slab.
    """

    lower_kwh: float
    upper_kwh: Optional[float]
    rate_inr_per_kwh: float

    def __post_init__(self) -> None:
        if self.lower_kwh < 0:
            raise TariffValidationError(
                "Tariff slab lower_kwh cannot be negative."
            )

        if self.upper_kwh is not None and self.upper_kwh <= self.lower_kwh:
            raise TariffValidationError(
                "Tariff slab upper_kwh must exceed lower_kwh."
            )

        if self.rate_inr_per_kwh < 0:
            raise TariffValidationError(
                "Tariff slab rate cannot be negative."
            )


@dataclass
class TariffRecord:
    """
    Canonical tariff record used by the tariff engine.
    """

    state: str
    discom: str
    tariff_category: str
    voltage_level: Optional[str] = None

    energy_charge_inr_per_kwh: float = 0.0

    demand_charge_inr_per_kw_month: float = 0.0
    demand_charge_inr_per_kva_month: float = 0.0

    fixed_charge_inr_per_month: float = 0.0

    electricity_duty_pct: float = 0.0

    fuel_power_adjustment_inr_per_kwh: float = 0.0

    power_factor_penalty_pct: float = 0.0
    power_factor_incentive_pct: float = 0.0

    tod_periods: List[TODPeriod] = field(default_factory=list)

    energy_slabs: List[TariffSlab] = field(default_factory=list)

    demand_basis: str = "kW"

    minimum_bill_inr_per_month: float = 0.0

    effective_from: Optional[str] = None
    effective_to: Optional[str] = None

    source: str = ""
    source_date: Optional[str] = None
    status: str = "unknown"
    confidence: str = "unknown"
    notes: str = ""

    # Open-access / renewable procurement metadata
    open_access_allowed: Optional[bool] = None
    wheeling_charge_inr_per_kwh: float = 0.0
    banking_charge_pct: float = 0.0
    additional_surcharge_inr_per_kwh: float = 0.0
    cross_subsidy_surcharge_inr_per_kwh: float = 0.0

    # Grid emission factor metadata
    grid_emission_factor_kg_co2_per_kwh: Optional[float] = None

    # Optional annual escalation hint
    annual_escalation_rate: Optional[float] = None

    def __post_init__(self) -> None:
        self.state = _clean_text(self.state)
        self.discom = _clean_text(self.discom)
        self.tariff_category = _clean_text(self.tariff_category)

        if not self.state:
            raise TariffValidationError("TariffRecord.state is required.")

        if not self.discom:
            raise TariffValidationError("TariffRecord.discom is required.")

        if not self.tariff_category:
            raise TariffValidationError(
                "TariffRecord.tariff_category is required."
            )

        self.demand_basis = _clean_text(self.demand_basis) or "kW"

        if self.demand_basis not in VALID_BASIS:
            raise TariffValidationError(
                "demand_basis must be 'kW' or 'kVA'."
            )

        if self.status not in TARIFF_STATUS_VALUES:
            raise TariffValidationError(
                f"Unsupported tariff status: {self.status!r}."
            )

        if self.confidence not in SOURCE_CONFIDENCE_VALUES:
            raise TariffValidationError(
                f"Unsupported confidence level: {self.confidence!r}."
            )

        numeric_fields = (
            "energy_charge_inr_per_kwh",
            "demand_charge_inr_per_kw_month",
            "demand_charge_inr_per_kva_month",
            "fixed_charge_inr_per_month",
            "electricity_duty_pct",
            "fuel_power_adjustment_inr_per_kwh",
            "power_factor_penalty_pct",
            "power_factor_incentive_pct",
            "minimum_bill_inr_per_month",
            "wheeling_charge_inr_per_kwh",
            "banking_charge_pct",
            "additional_surcharge_inr_per_kwh",
            "cross_subsidy_surcharge_inr_per_kwh",
        )

        for field_name in numeric_fields:
            value = getattr(self, field_name)
            if value < 0:
                raise TariffValidationError(
                    f"{field_name} cannot be negative."
                )

        if self.electricity_duty_pct > 100:
            raise TariffValidationError(
                "electricity_duty_pct cannot exceed 100%."
            )

        if self.banking_charge_pct > 100:
            raise TariffValidationError(
                "banking_charge_pct cannot exceed 100%."
            )

        if (
            self.annual_escalation_rate is not None
            and self.annual_escalation_rate < -1
        ):
            raise TariffValidationError(
                "annual_escalation_rate cannot be below -100%."
            )

        if (
            self.grid_emission_factor_kg_co2_per_kwh is not None
            and self.grid_emission_factor_kg_co2_per_kwh < 0
        ):
            raise TariffValidationError(
                "grid emission factor cannot be negative."
            )


@dataclass
class TariffCalculationInput:
    """Validated inputs for a tariff calculation."""

    state: str
    discom: Optional[str] = None
    tariff_category: str = "industrial"
    monthly_energy_kwh: float = 0.0

    contracted_demand_kw: Optional[float] = None
    contracted_demand_kva: Optional[float] = None

    maximum_demand_kw: Optional[float] = None
    maximum_demand_kva: Optional[float] = None

    billing_months: int = 1

    average_power_factor: Optional[float] = None

    electricity_duty_pct_override: Optional[float] = None
    fuel_power_adjustment_override: Optional[float] = None

    tod_energy_split: Dict[str, float] = field(default_factory=dict)

    # If no explicit TOD split is supplied, the entire load is billed at the
    # base tariff.
    use_tod: bool = True

    # Annual energy can be supplied for open-access screening.
    annual_energy_kwh: Optional[float] = None

    renewable_energy_kwh: float = 0.0

    def validate(self) -> None:
        self.state = _clean_text(self.state)
        self.discom = _clean_text(self.discom) or None
        self.tariff_category = (
            _clean_text(self.tariff_category) or "industrial"
        )

        if not self.state:
            raise TariffValidationError("state is required.")

        _safe_float(
            self.monthly_energy_kwh,
            field_name="monthly_energy_kwh",
            minimum=0,
        )

        if self.contracted_demand_kw is not None:
            _safe_float(
                self.contracted_demand_kw,
                field_name="contracted_demand_kw",
                minimum=0,
            )

        if self.contracted_demand_kva is not None:
            _safe_float(
                self.contracted_demand_kva,
                field_name="contracted_demand_kva",
                minimum=0,
            )

        if self.maximum_demand_kw is not None:
            _safe_float(
                self.maximum_demand_kw,
                field_name="maximum_demand_kw",
                minimum=0,
            )

        if self.maximum_demand_kva is not None:
            _safe_float(
                self.maximum_demand_kva,
                field_name="maximum_demand_kva",
                minimum=0,
            )

        self.billing_months = _safe_int(
            self.billing_months,
            field_name="billing_months",
            minimum=1,
            maximum=120,
        )

        if self.average_power_factor is not None:
            _safe_float(
                self.average_power_factor,
                field_name="average_power_factor",
                minimum=0.0,
                maximum=1.0,
            )

        if self.electricity_duty_pct_override is not None:
            _safe_float(
                self.electricity_duty_pct_override,
                field_name="electricity_duty_pct_override",
                minimum=0,
                maximum=100,
            )

        if self.fuel_power_adjustment_override is not None:
            _safe_float(
                self.fuel_power_adjustment_override,
                field_name="fuel_power_adjustment_override",
                minimum=0,
            )

        self.renewable_energy_kwh = _safe_float(
            self.renewable_energy_kwh,
            field_name="renewable_energy_kwh",
            minimum=0,
        ) or 0.0

        if self.annual_energy_kwh is not None:
            self.annual_energy_kwh = _safe_float(
                self.annual_energy_kwh,
                field_name="annual_energy_kwh",
                minimum=0,
            )

        if self.tod_energy_split:
            total = sum(
                _safe_float(
                    value,
                    field_name=f"tod_energy_split[{key}]",
                    minimum=0,
                )
                or 0.0
                for key, value in self.tod_energy_split.items()
            )

            if total <= 0:
                raise TariffValidationError(
                    "TOD energy split must contain positive energy."
                )

            # Treat values as kWh if their sum materially exceeds 1,
            # otherwise treat them as shares.
            if total <= 1.000001:
                self.tod_energy_split = {
                    key: float(value) / total
                    for key, value in self.tod_energy_split.items()
                }
            else:
                base = self.monthly_energy_kwh
                if base <= 0:
                    raise TariffValidationError(
                        "monthly_energy_kwh must be positive when TOD split "
                        "is supplied as absolute kWh."
                    )
                self.tod_energy_split = {
                    key: float(value) / total
                    for key, value in self.tod_energy_split.items()
                }


@dataclass
class TariffChargeBreakdown:
    """Breakdown of charges in one billing period."""

    energy_charge: float = 0.0
    tod_adjustment: float = 0.0
    demand_charge: float = 0.0
    fixed_charge: float = 0.0
    fuel_power_adjustment: float = 0.0
    power_factor_adjustment: float = 0.0
    electricity_duty: float = 0.0
    minimum_bill_adjustment: float = 0.0
    total_before_minimum_bill: float = 0.0
    subtotal_after_minimum_bill: float = 0.0
    total_bill: float = 0.0

    def to_dict(self) -> Dict[str, float]:
        return {
            key: _round_money(value)
            for key, value in asdict(self).items()
        }


@dataclass
class TariffResult:
    """Stable tariff-calculation output."""

    state: str
    discom: str
    tariff_category: str

    monthly_energy_kwh: float
    billing_months: int

    demand_basis: str
    billed_demand: float

    effective_energy_rate_inr_per_kwh: float
    effective_demand_rate_inr_per_unit_month: float

    monthly_charge: TariffChargeBreakdown
    annual_charge: float

    annual_energy_kwh: float
    average_cost_inr_per_kwh: float

    grid_emissions_kg_co2: float
    grid_emissions_tco2: float

    source: str
    status: str
    confidence: str
    notes: List[str] = field(default_factory=list)

    raw_tariff: Optional[TariffRecord] = None

    def to_dict(self) -> Dict[str, Any]:
        result = {
            "state": self.state,
            "discom": self.discom,
            "tariff_category": self.tariff_category,
            "monthly_energy_kwh": _round_energy(self.monthly_energy_kwh),
            "billing_months": self.billing_months,
            "demand_basis": self.demand_basis,
            "billed_demand": _round_energy(self.billed_demand),
            "effective_energy_rate_inr_per_kwh": _round_rate(
                self.effective_energy_rate_inr_per_kwh
            ),
            "effective_demand_rate_inr_per_unit_month": _round_rate(
                self.effective_demand_rate_inr_per_unit_month
            ),
            "monthly_charge": self.monthly_charge.to_dict(),
            "annual_charge": _round_money(self.annual_charge),
            "annual_energy_kwh": _round_energy(self.annual_energy_kwh),
            "average_cost_inr_per_kwh": _round_rate(
                self.average_cost_inr_per_kwh
            ),
            "grid_emissions_kg_co2": _round_energy(
                self.grid_emissions_kg_co2
            ),
            "grid_emissions_tco2": round(self.grid_emissions_tco2, 6),
            "source": self.source,
            "status": self.status,
            "confidence": self.confidence,
            "notes": list(self.notes),
        }

        if self.raw_tariff is not None:
            result["raw_tariff"] = tariff_record_to_dict(self.raw_tariff)

        return result


@dataclass
class StateTariffComparison:
    """State-by-state electricity cost comparison."""

    results: List[TariffResult]
    cheapest_state: Optional[str]
    most_expensive_state: Optional[str]
    savings_vs_most_expensive_inr_per_year: Optional[float]
    spread_pct: Optional[float]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "results": [item.to_dict() for item in self.results],
            "cheapest_state": self.cheapest_state,
            "most_expensive_state": self.most_expensive_state,
            "savings_vs_most_expensive_inr_per_year": (
                None
                if self.savings_vs_most_expensive_inr_per_year is None
                else _round_money(
                    self.savings_vs_most_expensive_inr_per_year
                )
            ),
            "spread_pct": (
                None if self.spread_pct is None else round(self.spread_pct, 4)
            ),
        }


@dataclass
class EscalationProjectionYear:
    """One year in a tariff escalation projection."""

    year: int
    escalation_rate: float
    projected_annual_charge: float
    projected_average_cost_inr_per_kwh: float


@dataclass
class EscalationProjection:
    """Tariff escalation projection output."""

    base_year: int
    years: List[EscalationProjectionYear]
    cumulative_increase_pct: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "base_year": self.base_year,
            "years": [
                {
                    "year": item.year,
                    "escalation_rate": round(item.escalation_rate, 6),
                    "projected_annual_charge": _round_money(
                        item.projected_annual_charge
                    ),
                    "projected_average_cost_inr_per_kwh": _round_rate(
                        item.projected_average_cost_inr_per_kwh
                    ),
                }
                for item in self.years
            ],
            "cumulative_increase_pct": round(
                self.cumulative_increase_pct,
                4,
            ),
        }


@dataclass
class RenewableProcurementScenario:
    """Renewable electricity procurement scenario."""

    source_type: str
    annual_renewable_kwh: float

    energy_rate_inr_per_kwh: float

    wheeling_charge_inr_per_kwh: float = 0.0
    css_inr_per_kwh: float = 0.0
    additional_surcharge_inr_per_kwh: float = 0.0
    banking_cost_inr_per_kwh: float = 0.0

    annual_fixed_cost_inr: float = 0.0
    annual_other_cost_inr: float = 0.0

    renewable_emission_factor_kg_co2_per_kwh: float = (
        DEFAULT_GREEN_POWER_EMISSION_FACTOR_KG_CO2_PER_KWH
    )

    baseline_grid_cost_inr: float = 0.0

    total_renewable_cost_inr: float = 0.0
    annual_savings_inr: float = 0.0

    baseline_emissions_kg_co2: float = 0.0
    renewable_emissions_kg_co2: float = 0.0
    emissions_reduction_kg_co2: float = 0.0

    notes: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source_type": self.source_type,
            "annual_renewable_kwh": _round_energy(
                self.annual_renewable_kwh
            ),
            "energy_rate_inr_per_kwh": _round_rate(
                self.energy_rate_inr_per_kwh
            ),
            "wheeling_charge_inr_per_kwh": _round_rate(
                self.wheeling_charge_inr_per_kwh
            ),
            "css_inr_per_kwh": _round_rate(self.css_inr_per_kwh),
            "additional_surcharge_inr_per_kwh": _round_rate(
                self.additional_surcharge_inr_per_kwh
            ),
            "banking_cost_inr_per_kwh": _round_rate(
                self.banking_cost_inr_per_kwh
            ),
            "annual_fixed_cost_inr": _round_money(
                self.annual_fixed_cost_inr
            ),
            "annual_other_cost_inr": _round_money(
                self.annual_other_cost_inr
            ),
            "renewable_emission_factor_kg_co2_per_kwh": _round_rate(
                self.renewable_emission_factor_kg_co2_per_kwh
            ),
            "baseline_grid_cost_inr": _round_money(
                self.baseline_grid_cost_inr
            ),
            "total_renewable_cost_inr": _round_money(
                self.total_renewable_cost_inr
            ),
            "annual_savings_inr": _round_money(self.annual_savings_inr),
            "baseline_emissions_kg_co2": _round_energy(
                self.baseline_emissions_kg_co2
            ),
            "renewable_emissions_kg_co2": _round_energy(
                self.renewable_emissions_kg_co2
            ),
            "emissions_reduction_kg_co2": _round_energy(
                self.emissions_reduction_kg_co2
            ),
            "notes": list(self.notes),
        }


@dataclass
class OpenAccessAssessment:
    """Suitability assessment for renewable open access."""

    eligible_by_load: bool
    annual_consumption_threshold_met: bool
    generation_sufficient: bool

    contracted_demand_kw: float
    annual_consumption_kwh: float
    annual_renewable_generation_kwh: float

    minimum_load_kw: float

    renewable_coverage_pct: float
    estimated_grid_cost_inr: float
    estimated_open_access_cost_inr: float
    estimated_savings_inr: float

    estimated_emissions_reduction_kg_co2: float

    suitable: bool
    score: float
    reasons: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "eligible_by_load": self.eligible_by_load,
            "annual_consumption_threshold_met": (
                self.annual_consumption_threshold_met
            ),
            "generation_sufficient": self.generation_sufficient,
            "contracted_demand_kw": _round_energy(
                self.contracted_demand_kw
            ),
            "annual_consumption_kwh": _round_energy(
                self.annual_consumption_kwh
            ),
            "annual_renewable_generation_kwh": _round_energy(
                self.annual_renewable_generation_kwh
            ),
            "minimum_load_kw": _round_energy(self.minimum_load_kw),
            "renewable_coverage_pct": round(
                self.renewable_coverage_pct,
                4,
            ),
            "estimated_grid_cost_inr": _round_money(
                self.estimated_grid_cost_inr
            ),
            "estimated_open_access_cost_inr": _round_money(
                self.estimated_open_access_cost_inr
            ),
            "estimated_savings_inr": _round_money(
                self.estimated_savings_inr
            ),
            "estimated_emissions_reduction_kg_co2": _round_energy(
                self.estimated_emissions_reduction_kg_co2
            ),
            "suitable": self.suitable,
            "score": round(self.score, 4),
            "reasons": list(self.reasons),
            "warnings": list(self.warnings),
        }


# ============================================================================
# Serialization helpers
# ============================================================================


def tod_period_to_dict(period: TODPeriod) -> Dict[str, Any]:
    """Serialize TODPeriod."""
    return asdict(period)


def tod_period_from_dict(data: Mapping[str, Any]) -> TODPeriod:
    """Create TODPeriod from mapping."""
    return TODPeriod(
        name=_clean_text(data.get("name")),
        start_hour=float(data.get("start_hour", 0)),
        end_hour=float(data.get("end_hour", 24)),
        multiplier=float(data.get("multiplier", 1)),
        surcharge_pct=float(data.get("surcharge_pct", 0)),
        discount_pct=float(data.get("discount_pct", 0)),
        priority=int(data.get("priority", 0)),
    )


def tariff_slab_to_dict(slab: TariffSlab) -> Dict[str, Any]:
    """Serialize tariff slab."""
    return asdict(slab)


def tariff_slab_from_dict(data: Mapping[str, Any]) -> TariffSlab:
    """Create tariff slab from mapping."""
    upper = data.get("upper_kwh")
    return TariffSlab(
        lower_kwh=float(data.get("lower_kwh", 0)),
        upper_kwh=None if upper in (None, "") else float(upper),
        rate_inr_per_kwh=float(
            data.get(
                "rate_inr_per_kwh",
                data.get("energy_charge_inr_per_kwh", 0),
            )
        ),
    )


def tariff_record_to_dict(record: TariffRecord) -> Dict[str, Any]:
    """Serialize TariffRecord to plain dictionary."""
    data = asdict(record)

    data["tod_periods"] = [
        tod_period_to_dict(item)
        for item in record.tod_periods
    ]

    data["energy_slabs"] = [
        tariff_slab_to_dict(item)
        for item in record.energy_slabs
    ]

    return data


def tariff_record_from_dict(data: Mapping[str, Any]) -> TariffRecord:
    """Construct TariffRecord from a mapping."""
    tod_periods = [
        (
            item
            if isinstance(item, TODPeriod)
            else tod_period_from_dict(item)
        )
        for item in data.get("tod_periods", [])
    ]

    slabs = [
        (
            item
            if isinstance(item, TariffSlab)
            else tariff_slab_from_dict(item)
        )
        for item in data.get("energy_slabs", [])
    ]

    def optional_float(key: str) -> Optional[float]:
        value = data.get(key)
        if value in (None, ""):
            return None
        return float(value)

    return TariffRecord(
        state=_clean_text(data.get("state")),
        discom=_clean_text(data.get("discom")),
        tariff_category=_clean_text(
            data.get("tariff_category", "industrial")
        ),
        voltage_level=_coalesce(
            data.get("voltage_level"),
            None,
        ),
        energy_charge_inr_per_kwh=float(
            data.get("energy_charge_inr_per_kwh", 0)
        ),
        demand_charge_inr_per_kw_month=float(
            data.get("demand_charge_inr_per_kw_month", 0)
        ),
        demand_charge_inr_per_kva_month=float(
            data.get("demand_charge_inr_per_kva_month", 0)
        ),
        fixed_charge_inr_per_month=float(
            data.get("fixed_charge_inr_per_month", 0)
        ),
        electricity_duty_pct=float(
            data.get("electricity_duty_pct", 0)
        ),
        fuel_power_adjustment_inr_per_kwh=float(
            data.get("fuel_power_adjustment_inr_per_kwh", 0)
        ),
        power_factor_penalty_pct=float(
            data.get("power_factor_penalty_pct", 0)
        ),
        power_factor_incentive_pct=float(
            data.get("power_factor_incentive_pct", 0)
        ),
        tod_periods=tod_periods,
        energy_slabs=slabs,
        demand_basis=_clean_text(
            data.get("demand_basis", "kW")
        ) or "kW",
        minimum_bill_inr_per_month=float(
            data.get("minimum_bill_inr_per_month", 0)
        ),
        effective_from=_coalesce(
            data.get("effective_from"),
            None,
        ),
        effective_to=_coalesce(
            data.get("effective_to"),
            None,
        ),
        source=_clean_text(data.get("source")),
        source_date=_coalesce(
            data.get("source_date"),
            None,
        ),
        status=_clean_text(
            data.get("status", "unknown")
        ) or "unknown",
        confidence=_clean_text(
            data.get("confidence", "unknown")
        ) or "unknown",
        notes=_clean_text(data.get("notes")),
        open_access_allowed=(
            None
            if data.get("open_access_allowed") in (None, "")
            else bool(data.get("open_access_allowed"))
        ),
        wheeling_charge_inr_per_kwh=float(
            data.get("wheeling_charge_inr_per_kwh", 0)
        ),
        banking_charge_pct=float(
            data.get("banking_charge_pct", 0)
        ),
        additional_surcharge_inr_per_kwh=float(
            data.get("additional_surcharge_inr_per_kwh", 0)
        ),
        cross_subsidy_surcharge_inr_per_kwh=float(
            data.get("cross_subsidy_surcharge_inr_per_kwh", 0)
        ),
        grid_emission_factor_kg_co2_per_kwh=optional_float(
            "grid_emission_factor_kg_co2_per_kwh"
        ),
        annual_escalation_rate=optional_float(
            "annual_escalation_rate"
        ),
    )


# ============================================================================
# Default baseline data
# ============================================================================


def _build_default_tariff_records() -> List[TariffRecord]:
    """
    Create deliberately conservative baseline records.

    These records are illustrative and are marked as estimated/provisional.
    They are intended to keep the engine executable while strongly signalling
    that production deployments should replace them with official tariff data.
    """

    return [
        TariffRecord(
            state="Tamil Nadu",
            discom="TANGEDCO",
            tariff_category="HT_IIA",
            voltage_level="HT",
            energy_charge_inr_per_kwh=9.50,
            demand_charge_inr_per_kva_month=450.00,
            fixed_charge_inr_per_month=0.00,
            electricity_duty_pct=5.0,
            tod_periods=[
                TODPeriod(
                    name="peak",
                    start_hour=6.0,
                    end_hour=10.0,
                    multiplier=1.25,
                    surcharge_pct=0.0,
                ),
                TODPeriod(
                    name="peak_evening",
                    start_hour=18.0,
                    end_hour=22.0,
                    multiplier=1.25,
                ),
                TODPeriod(
                    name="off_peak",
                    start_hour=22.0,
                    end_hour=24.0,
                    multiplier=0.95,
                ),
                TODPeriod(
                    name="off_peak_night",
                    start_hour=0.0,
                    end_hour=5.0,
                    multiplier=0.95,
                ),
            ],
            demand_basis="kVA",
            source=(
                "Project research notes; verify against current TNERC/"
                "TANGEDCO tariff order before production use."
            ),
            source_date="2026",
            status="estimated",
            confidence="low",
            notes=(
                "Research-note value; not an official tariff-order import."
            ),
            open_access_allowed=True,
            wheeling_charge_inr_per_kwh=0.0,
            banking_charge_pct=0.0,
            additional_surcharge_inr_per_kwh=0.0,
            cross_subsidy_surcharge_inr_per_kwh=0.0,
            grid_emission_factor_kg_co2_per_kwh=(
                DEFAULT_GRID_EMISSION_FACTOR_KG_CO2_PER_KWH
            ),
            annual_escalation_rate=DEFAULT_ESCALATION_RATE,
        ),
        TariffRecord(
            state="Tamil Nadu",
            discom="TANGEDCO",
            tariff_category="LT_CT",
            voltage_level="LT",
            energy_charge_inr_per_kwh=8.20,
            demand_charge_inr_per_kw_month=75.00,
            electricity_duty_pct=5.0,
            tod_periods=[
                TODPeriod(
                    name="peak_morning",
                    start_hour=6.0,
                    end_hour=10.0,
                    multiplier=1.25,
                ),
                TODPeriod(
                    name="peak_evening",
                    start_hour=18.0,
                    end_hour=22.0,
                    multiplier=1.25,
                ),
                TODPeriod(
                    name="off_peak",
                    start_hour=22.0,
                    end_hour=24.0,
                    multiplier=0.95,
                ),
                TODPeriod(
                    name="off_peak_night",
                    start_hour=0.0,
                    end_hour=5.0,
                    multiplier=0.95,
                ),
            ],
            demand_basis="kW",
            source=(
                "Project research notes; verify against current TNERC/"
                "TANGEDCO tariff order before production use."
            ),
            source_date="2026",
            status="estimated",
            confidence="low",
            notes=(
                "Research-note value; tariff applicability should be "
                "validated against the customer's exact LT category."
            ),
            open_access_allowed=True,
            grid_emission_factor_kg_co2_per_kwh=(
                DEFAULT_GRID_EMISSION_FACTOR_KG_CO2_PER_KWH
            ),
            annual_escalation_rate=DEFAULT_ESCALATION_RATE,
        ),
        TariffRecord(
            state="Karnataka",
            discom="BESCOM",
            tariff_category="industrial",
            voltage_level="LT/HT",
            energy_charge_inr_per_kwh=3.00,
            demand_charge_inr_per_kw_month=120.00,
            fixed_charge_inr_per_month=0.00,
            electricity_duty_pct=0.0,
            source=(
                "Project research notes; conflicting secondary-source "
                "figures exist and official KERC tariff order verification "
                "is required."
            ),
            source_date="2026",
            status="estimated",
            confidence="low",
            notes=(
                "Potential category ambiguity. Do not use as authoritative "
                "without KERC category/order confirmation."
            ),
            open_access_allowed=True,
            grid_emission_factor_kg_co2_per_kwh=(
                DEFAULT_GRID_EMISSION_FACTOR_KG_CO2_PER_KWH
            ),
            annual_escalation_rate=0.07,
        ),
    ]


# ============================================================================
# CSV loading
# ============================================================================


CSV_FLOAT_FIELDS = {
    "energy_charge_inr_per_kwh",
    "demand_charge_inr_per_kw_month",
    "demand_charge_inr_per_kva_month",
    "fixed_charge_inr_per_month",
    "electricity_duty_pct",
    "fuel_power_adjustment_inr_per_kwh",
    "power_factor_penalty_pct",
    "power_factor_incentive_pct",
    "minimum_bill_inr_per_month",
    "wheeling_charge_inr_per_kwh",
    "banking_charge_pct",
    "additional_surcharge_inr_per_kwh",
    "cross_subsidy_surcharge_inr_per_kwh",
    "grid_emission_factor_kg_co2_per_kwh",
    "annual_escalation_rate",
}

CSV_BOOL_FIELDS = {
    "open_access_allowed",
}


def _parse_csv_value(key: str, value: Any) -> Any:
    """Convert CSV strings into typed values."""
    if value is None:
        return None

    text = str(value).strip()

    if text == "":
        return None

    if key in CSV_FLOAT_FIELDS:
        return float(text)

    if key in CSV_BOOL_FIELDS:
        normalized = text.lower()
        if normalized in {"true", "1", "yes", "y"}:
            return True
        if normalized in {"false", "0", "no", "n"}:
            return False
        raise TariffDataError(
            f"Invalid boolean value for {key}: {value!r}"
        )

    return value


def load_tariffs_from_csv(
    path: Union[str, os.PathLike[str]],
) -> List[TariffRecord]:
    """
    Load tariff records from CSV.

    The CSV must contain at least:
        state, discom, tariff_category

    TOD periods are not encoded as separate rows in the base CSV. They can
    be loaded through the optional semicolon-delimited fields:

        tod_names
        tod_start_hours
        tod_end_hours
        tod_multipliers
        tod_surcharge_pcts
        tod_discount_pcts

    Example:
        tod_names=peak;off_peak
        tod_start_hours=18;22
        tod_end_hours=22;24
        tod_multipliers=1.25;0.95
    """

    file_path = Path(path)

    if not file_path.exists():
        raise TariffDataError(
            f"Tariff CSV not found: {file_path}"
        )

    if not file_path.is_file():
        raise TariffDataError(
            f"Tariff path is not a file: {file_path}"
        )

    records: List[TariffRecord] = []

    try:
        with file_path.open(
            "r",
            encoding="utf-8-sig",
            newline="",
        ) as handle:
            reader = csv.DictReader(handle)

            if reader.fieldnames is None:
                raise TariffDataError(
                    "CSV file has no header row."
                )

            required = {
                "state",
                "discom",
                "tariff_category",
            }

            missing = required.difference(
                set(reader.fieldnames)
            )

            if missing:
                raise TariffDataError(
                    "Tariff CSV is missing required columns: "
                    + ", ".join(sorted(missing))
                )

            for row_number, raw_row in enumerate(
                reader,
                start=2,
            ):
                data: Dict[str, Any] = {}

                for key, value in raw_row.items():
                    if key is None:
                        continue
                    data[key] = _parse_csv_value(
                        key,
                        value,
                    )

                tod_periods = _tod_periods_from_csv_row(data)
                data["tod_periods"] = tod_periods

                record = tariff_record_from_dict(data)

                if not record.source:
                    record.source = str(file_path)

                records.append(record)

    except TariffDataError:
        raise
    except (OSError, csv.Error, ValueError) as exc:
        raise TariffDataError(
            f"Failed to load tariff CSV {file_path}: {exc}"
        ) from exc

    if not records:
        raise TariffDataError(
            f"No tariff records found in {file_path}."
        )

    return records


def _split_semicolon_values(value: Any) -> List[str]:
    """Split semicolon-delimited CSV value."""
    if value in (None, ""):
        return []
    return [item.strip() for item in str(value).split(";")]


def _tod_periods_from_csv_row(
    row: Mapping[str, Any],
) -> List[TODPeriod]:
    """Build TODPeriod list from optional CSV columns."""
    names = _split_semicolon_values(row.get("tod_names"))
    starts = _split_semicolon_values(row.get("tod_start_hours"))
    ends = _split_semicolon_values(row.get("tod_end_hours"))
    multipliers = _split_semicolon_values(
        row.get("tod_multipliers")
    )
    surcharge_pcts = _split_semicolon_values(
        row.get("tod_surcharge_pcts")
    )
    discount_pcts = _split_semicolon_values(
        row.get("tod_discount_pcts")
    )

    if not names:
        return []

    expected = len(names)

    if not (
        len(starts) == expected
        and len(ends) == expected
        and len(multipliers) == expected
    ):
        raise TariffDataError(
            "TOD CSV columns must have matching lengths."
        )

    result = []

    for index in range(expected):
        surcharge = (
            float(surcharge_pcts[index])
            if index < len(surcharge_pcts)
            else 0.0
        )

        discount = (
            float(discount_pcts[index])
            if index < len(discount_pcts)
            else 0.0
        )

        result.append(
            TODPeriod(
                name=names[index],
                start_hour=float(starts[index]),
                end_hour=float(ends[index]),
                multiplier=float(multipliers[index]),
                surcharge_pct=surcharge,
                discount_pct=discount,
                priority=index,
            )
        )

    return result


# ============================================================================
# Tariff store
# ============================================================================


class TariffStore:
    """
    In-memory tariff registry.

    Supports:
    - direct record registration
    - bulk registration
    - CSV loading
    - flexible category matching
    - state/DISCOM lookup
    """

    def __init__(
        self,
        records: Optional[Iterable[TariffRecord]] = None,
    ) -> None:
        self._records: List[TariffRecord] = []

        if records is not None:
            self.add_many(records)

    @property
    def records(self) -> List[TariffRecord]:
        """Return a copy of all tariff records."""
        return list(self._records)

    def add(self, record: TariffRecord) -> None:
        """Add a single tariff record."""
        if not isinstance(record, TariffRecord):
            raise TariffValidationError(
                "TariffStore accepts TariffRecord instances."
            )

        self._records.append(record)

    def add_many(
        self,
        records: Iterable[TariffRecord],
    ) -> None:
        """Add multiple tariff records."""
        for record in records:
            self.add(record)

    def add_from_csv(
        self,
        path: Union[str, os.PathLike[str]],
    ) -> int:
        """Load records from CSV and return count added."""
        records = load_tariffs_from_csv(path)
        self.add_many(records)
        return len(records)

    def clear(self) -> None:
        """Remove all records."""
        self._records.clear()

    def find(
        self,
        *,
        state: str,
        discom: Optional[str] = None,
        tariff_category: Optional[str] = None,
        voltage_level: Optional[str] = None,
    ) -> TariffRecord:
        """
        Find the best matching tariff record.

        Matching priority:
        1. exact state + discom + category + voltage
        2. exact state + discom + category
        3. exact state + category
        4. exact state
        5. normalized category aliases
        """

        state_key = _normalize_key(state)
        discom_key = _normalize_key(discom)
        category_key = _normalize_key(
            tariff_category or "industrial"
        )
        voltage_key = _normalize_key(voltage_level)

        candidates = [
            item
            for item in self._records
            if _normalize_key(item.state) == state_key
        ]

        if discom_key:
            exact_discom = [
                item
                for item in candidates
                if _normalize_key(item.discom) == discom_key
            ]
            if exact_discom:
                candidates = exact_discom

        if voltage_key:
            exact_voltage = [
                item
                for item in candidates
                if _normalize_key(item.voltage_level)
                == voltage_key
            ]
            if exact_voltage:
                candidates = exact_voltage

        if not candidates:
            raise TariffNotFoundError(
                f"No tariff records found for state={state!r}, "
                f"discom={discom!r}."
            )

        exact_category = [
            item
            for item in candidates
            if _category_matches(
                item.tariff_category,
                category_key,
            )
        ]

        if exact_category:
            return _select_best_record(exact_category)

        # For generic "industrial", allow records such as HT_IIA,
        # HT-industrial, industrial-HT, etc.
        generic_candidates = [
            item
            for item in candidates
            if _is_industrial_category(item.tariff_category)
        ]

        if category_key in {
            "industrial",
            "industry",
            "ht",
            "lt",
        } and generic_candidates:
            return _select_best_record(generic_candidates)

        if len(candidates) == 1:
            return candidates[0]

        raise TariffNotFoundError(
            "Multiple tariff records matched the location, but none "
            "matched the requested category. "
            f"state={state!r}, discom={discom!r}, "
            f"tariff_category={tariff_category!r}."
        )

    def list_states(self) -> List[str]:
        """Return unique states."""
        return sorted(
            {
                item.state
                for item in self._records
            }
        )

    def list_discoms(
        self,
        state: Optional[str] = None,
    ) -> List[str]:
        """Return unique DISCOMs, optionally filtered by state."""
        if state:
            state_key = _normalize_key(state)
            values = [
                item.discom
                for item in self._records
                if _normalize_key(item.state) == state_key
            ]
        else:
            values = [
                item.discom
                for item in self._records
            ]

        return sorted(set(values))

    def list_categories(
        self,
        state: Optional[str] = None,
        discom: Optional[str] = None,
    ) -> List[str]:
        """Return unique tariff categories."""
        records = self._records

        if state:
            state_key = _normalize_key(state)
            records = [
                item
                for item in records
                if _normalize_key(item.state) == state_key
            ]

        if discom:
            discom_key = _normalize_key(discom)
            records = [
                item
                for item in records
                if _normalize_key(item.discom) == discom_key
            ]

        return sorted(
            {
                item.tariff_category
                for item in records
            }
        )


def _select_best_record(
    records: Sequence[TariffRecord],
) -> TariffRecord:
    """
    Prefer current/high-confidence records.

    Ranking:
    current > provisional > estimated > historical > proposed > unknown
    high > medium > low > unknown
    """
    status_score = {
        "current": 6,
        "provisional": 5,
        "estimated": 4,
        "historical": 3,
        "proposed": 2,
        "unknown": 1,
    }

    confidence_score = {
        "high": 4,
        "medium": 3,
        "low": 2,
        "unknown": 1,
    }

    return max(
        records,
        key=lambda item: (
            status_score.get(item.status, 0),
            confidence_score.get(item.confidence, 0),
        ),
    )


def _is_industrial_category(category: str) -> bool:
    """Determine whether a tariff category appears industrial."""
    value = _normalize_key(category)

    industrial_terms = (
        "industrial",
        "industry",
        "ht_i",
        "ht_ii",
        "ht2",
        "ht_ii_a",
        "lt_industrial",
        "lt_ind",
        "medium_industry",
        "large_industry",
        "factory",
    )

    return any(term in value for term in industrial_terms)


def _category_matches(
    record_category: str,
    requested_key: str,
) -> bool:
    """Flexible category matching."""
    record_key = _normalize_key(record_category)

    if record_key == requested_key:
        return True

    aliases = {
        "industrial": {
            "industrial",
            "industry",
            "ht_i",
            "ht_ii",
            "ht_iia",
            "ht_ii_a",
            "lt_industrial",
            "lt_ind",
        },
        "industry": {
            "industrial",
            "industry",
            "ht_i",
            "ht_ii",
            "ht_iia",
            "ht_ii_a",
            "lt_industrial",
            "lt_ind",
        },
        "ht_iia": {
            "ht_iia",
            "ht_ii_a",
            "ht_industrial",
            "ht_ii",
        },
        "lt_ct": {
            "lt_ct",
            "lt_commercial",
        },
    }

    if requested_key in aliases:
        return record_key in aliases[requested_key]

    return (
        requested_key in record_key
        or record_key in requested_key
    )


# ============================================================================
# Core tariff calculations
# ============================================================================


class TariffEngine:
    """
    Main electricity tariff engine.

    The class is deliberately stateless with respect to calculations. Tariff
    records live in TariffStore and every calculation returns a fresh result.

    This makes the engine:
    - deterministic
    - easy to unit test
    - safe to reuse
    - compatible with Streamlit/FastAPI
    """

    def __init__(
        self,
        store: Optional[TariffStore] = None,
        *,
        use_default_records: bool = True,
        default_grid_emission_factor_kg_co2_per_kwh: float = (
            DEFAULT_GRID_EMISSION_FACTOR_KG_CO2_PER_KWH
        ),
        minimum_geoa_load_kw: float = DEFAULT_GEOA_MIN_CONTRACTED_LOAD_KW,
    ) -> None:
        if store is None:
            store = TariffStore()

            if use_default_records:
                store.add_many(
                    _build_default_tariff_records()
                )

        self.store = store

        self.default_grid_emission_factor_kg_co2_per_kwh = (
            _safe_float(
                default_grid_emission_factor_kg_co2_per_kwh,
                field_name=(
                    "default_grid_emission_factor_kg_co2_per_kwh"
                ),
                minimum=0,
            )
            or DEFAULT_GRID_EMISSION_FACTOR_KG_CO2_PER_KWH
        )

        self.minimum_geoа_load_kw = _safe_float(
            minimum_geoa_load_kw,
            field_name="minimum_geoа_load_kw",
            minimum=0,
        ) or DEFAULT_GEOA_MIN_CONTRACTED_LOAD_KW

        # Correct ASCII alias retained for external consumers.
        self.minimum_geoa_load_kw = self.minimum_geoа_load_kw

    # ---------------------------------------------------------------------
    # Data loading / lookup
    # ---------------------------------------------------------------------

    def load_csv(
        self,
        path: Union[str, os.PathLike[str]],
    ) -> int:
        """Load tariff data from CSV."""
        return self.store.add_from_csv(path)

    def register_tariff(
        self,
        tariff: Union[TariffRecord, Mapping[str, Any]],
    ) -> TariffRecord:
        """Register one tariff record."""
        record = (
            tariff
            if isinstance(tariff, TariffRecord)
            else tariff_record_from_dict(tariff)
        )

        self.store.add(record)
        return record

    def register_tariffs(
        self,
        tariffs: Iterable[
            Union[TariffRecord, Mapping[str, Any]]
        ],
    ) -> int:
        """Register multiple tariff records."""
        count = 0

        for tariff in tariffs:
            self.register_tariff(tariff)
            count += 1

        return count

    def get_tariff(
        self,
        *,
        state: str,
        discom: Optional[str] = None,
        tariff_category: str = "industrial",
        voltage_level: Optional[str] = None,
    ) -> TariffRecord:
        """Return a matching tariff record."""
        return self.store.find(
            state=state,
            discom=discom,
            tariff_category=tariff_category,
            voltage_level=voltage_level,
        )

    def get_discoms(
        self,
        state: Optional[str] = None,
    ) -> List[str]:
        """Return available DISCOMs."""
        return self.store.list_discoms(state)

    def get_states(self) -> List[str]:
        """Return all available states."""
        return self.store.list_states()

    # ---------------------------------------------------------------------
    # Validation
    # ---------------------------------------------------------------------

    @staticmethod
    def validate_inputs(
        inputs: TariffCalculationInput,
    ) -> TariffCalculationInput:
        """Validate calculation input and return it."""
        inputs.validate()
        return inputs

    # ---------------------------------------------------------------------
    # Energy-charge logic
    # ---------------------------------------------------------------------

    def calculate_energy_charge(
        self,
        tariff: TariffRecord,
        energy_kwh: float,
    ) -> float:
        """
        Calculate base energy charges.

        If energy slabs are present, the slabs are applied progressively.
        Otherwise the flat energy charge is used.
        """
        energy = _safe_float(
            energy_kwh,
            field_name="energy_kwh",
            minimum=0,
        ) or 0.0

        if energy <= 0:
            return 0.0

        if not tariff.energy_slabs:
            return _round_money(
                energy
                * tariff.energy_charge_inr_per_kwh
            )

        slabs = sorted(
            tariff.energy_slabs,
            key=lambda item: item.lower_kwh,
        )

        total_charge = 0.0

        for slab in slabs:
            if energy <= slab.lower_kwh:
                continue

            upper = (
                energy
                if slab.upper_kwh is None
                else min(
                    energy,
                    slab.upper_kwh,
                )
            )

            slab_energy = max(
                0.0,
                upper - slab.lower_kwh,
            )

            total_charge += (
                slab_energy
                * slab.rate_inr_per_kwh
            )

            if slab.upper_kwh is None:
                break

        # If slabs do not fully cover the energy range, use the flat rate for
        # the remainder rather than silently under-billing.
        max_covered = max(
            (
                slab.upper_kwh
                for slab in slabs
                if slab.upper_kwh is not None
            ),
            default=0.0,
        )

        if energy > max_covered:
            remainder = max(
                0.0,
                energy - max_covered,
            )

            if all(
                slab.upper_kwh is not None
                for slab in slabs
            ):
                total_charge += (
                    remainder
                    * tariff.energy_charge_inr_per_kwh
                )

        return _round_money(total_charge)

    # ---------------------------------------------------------------------
    # TOD logic
    # ---------------------------------------------------------------------

    @staticmethod
    def tod_multiplier(
        tariff: TariffRecord,
        period_name: str,
    ) -> float:
        """Return multiplier for a named TOD period."""
        name_key = _normalize_key(period_name)

        periods = [
            item
            for item in tariff.tod_periods
            if _normalize_key(item.name) == name_key
        ]

        if not periods:
            raise TariffValidationError(
                f"TOD period {period_name!r} not found."
            )

        period = _select_tod_period(periods)

        return _calculate_tod_multiplier(period)

    def calculate_tod_charge(
        self,
        tariff: TariffRecord,
        energy_kwh: float,
        tod_energy_split: Optional[Mapping[str, float]] = None,
    ) -> Tuple[float, float, Dict[str, float]]:
        """
        Calculate TOD-adjusted energy charge.

        Returns:
            total_charge,
            tod_adjustment,
            applied_period_rates
        """
        energy = _safe_float(
            energy_kwh,
            field_name="energy_kwh",
            minimum=0,
        ) or 0.0

        if energy <= 0:
            return 0.0, 0.0, {}

        if not tariff.tod_periods:
            base = self.calculate_energy_charge(
                tariff,
                energy,
            )
            return base, 0.0, {}

        if not tod_energy_split:
            # No temporal distribution means base billing is safest.
            base = self.calculate_energy_charge(
                tariff,
                energy,
            )

            return base, 0.0, {}

        shares = _normalize_tod_split(
            tod_energy_split
        )

        total_charge = 0.0
        base_charge = self.calculate_energy_charge(
            tariff,
            energy,
        )

        applied_period_rates: Dict[str, float] = {}

        for period_name, share in shares.items():
            period_energy = energy * share

            periods = [
                item
                for item in tariff.tod_periods
                if _normalize_key(item.name)
                == _normalize_key(period_name)
            ]

            if not periods:
                raise TariffValidationError(
                    f"TOD period {period_name!r} not present "
                    f"in tariff {tariff.tariff_category!r}."
                )

            period = _select_tod_period(periods)
            multiplier = _calculate_tod_multiplier(period)

            base_period_charge = self.calculate_energy_charge(
                tariff,
                period_energy,
            )

            adjusted = (
                base_period_charge
                * multiplier
            )

            total_charge += adjusted
            applied_period_rates[
                period.name
            ] = multiplier

        tod_adjustment = total_charge - base_charge

        return (
            _round_money(total_charge),
            _round_money(tod_adjustment),
            applied_period_rates,
        )

    # ---------------------------------------------------------------------
    # Demand charge
    # ---------------------------------------------------------------------

    def calculate_demand_charge(
        self,
        tariff: TariffRecord,
        *,
        contracted_demand_kw: Optional[float] = None,
        contracted_demand_kva: Optional[float] = None,
        maximum_demand_kw: Optional[float] = None,
        maximum_demand_kva: Optional[float] = None,
    ) -> Tuple[float, float]:
        """
        Calculate demand charge.

        Principle:
        - use the tariff's demand basis;
        - bill the greater of contracted and measured maximum demand where
          both are supplied;
        - never use a negative demand.
        """

        if tariff.demand_basis == "kVA":
            contracted = float(
                contracted_demand_kva or 0.0
            )
            measured = float(
                maximum_demand_kva or 0.0
            )

            billed_demand = max(
                contracted,
                measured,
            )

            rate = tariff.demand_charge_inr_per_kva_month

        else:
            contracted = float(
                contracted_demand_kw or 0.0
            )
            measured = float(
                maximum_demand_kw or 0.0
            )

            billed_demand = max(
                contracted,
                measured,
            )

            rate = tariff.demand_charge_inr_per_kw_month

        charge = billed_demand * rate

        return (
            _round_money(charge),
            _round_energy(billed_demand),
        )

    # ---------------------------------------------------------------------
    # Fixed charge
    # ---------------------------------------------------------------------

    @staticmethod
    def calculate_fixed_charge(
        tariff: TariffRecord,
    ) -> float:
        """Return fixed monthly charge."""
        return _round_money(
            tariff.fixed_charge_inr_per_month
        )

    # ---------------------------------------------------------------------
    # Fuel/power adjustment
    # ---------------------------------------------------------------------

    @staticmethod
    def calculate_fuel_power_adjustment(
        tariff: TariffRecord,
        energy_kwh: float,
        override_rate: Optional[float] = None,
    ) -> float:
        """
        Calculate fuel/power purchase cost adjustment.

        The tariff engine keeps this separate from the base energy tariff
        because the project's research identifies it as a volatile component.
        """
        rate = (
            tariff.fuel_power_adjustment_inr_per_kwh
            if override_rate is None
            else _safe_float(
                override_rate,
                field_name="override_rate",
                minimum=0,
            )
        )

        return _round_money(
            float(energy_kwh) * float(rate)
        )

    # ---------------------------------------------------------------------
    # Power factor adjustment
    # ---------------------------------------------------------------------

    @staticmethod
    def calculate_power_factor_adjustment(
        tariff: TariffRecord,
        subtotal_before_pf: float,
        average_power_factor: Optional[float],
    ) -> float:
        """
        Apply configured PF penalty/incentive.

        A single tariff record may define either penalty or incentive.
        """
        if average_power_factor is None:
            return 0.0

        pf = _safe_float(
            average_power_factor,
            field_name="average_power_factor",
            minimum=0,
            maximum=1,
        ) or 0.0

        if pf >= 1.0:
            return 0.0

        if tariff.power_factor_penalty_pct > 0:
            penalty = (
                subtotal_before_pf
                * tariff.power_factor_penalty_pct
                / 100
            )
            return _round_money(penalty)

        if tariff.power_factor_incentive_pct > 0:
            incentive = (
                subtotal_before_pf
                * tariff.power_factor_incentive_pct
                / 100
            )
            return _round_money(-incentive)

        return 0.0

    # ---------------------------------------------------------------------
    # Electricity duty
    # ---------------------------------------------------------------------

    @staticmethod
    def calculate_electricity_duty(
        taxable_amount: float,
        duty_pct: float,
    ) -> float:
        """Calculate electricity duty."""
        if taxable_amount <= 0:
            return 0.0

        if duty_pct < 0:
            raise TariffValidationError(
                "Duty percentage cannot be negative."
            )

        return _round_money(
            taxable_amount
            * duty_pct
            / 100
        )

    # ---------------------------------------------------------------------
    # Full bill
    # ---------------------------------------------------------------------

    def calculate_bill(
        self,
        *,
        state: str,
        discom: Optional[str] = None,
        tariff_category: str = "industrial",
        monthly_energy_kwh: float,
        contracted_demand_kw: Optional[float] = None,
        contracted_demand_kva: Optional[float] = None,
        maximum_demand_kw: Optional[float] = None,
        maximum_demand_kva: Optional[float] = None,
        billing_months: int = 1,
        average_power_factor: Optional[float] = None,
        electricity_duty_pct_override: Optional[float] = None,
        fuel_power_adjustment_override: Optional[float] = None,
        tod_energy_split: Optional[Mapping[str, float]] = None,
        use_tod: bool = True,
        annual_energy_kwh: Optional[float] = None,
        renewable_energy_kwh: float = 0.0,
        voltage_level: Optional[str] = None,
    ) -> TariffResult:
        """Calculate a complete electricity bill."""
        inputs = TariffCalculationInput(
            state=state,
            discom=discom,
            tariff_category=tariff_category,
            monthly_energy_kwh=monthly_energy_kwh,
            contracted_demand_kw=contracted_demand_kw,
            contracted_demand_kva=contracted_demand_kva,
            maximum_demand_kw=maximum_demand_kw,
            maximum_demand_kva=maximum_demand_kva,
            billing_months=billing_months,
            average_power_factor=average_power_factor,
            electricity_duty_pct_override=(
                electricity_duty_pct_override
            ),
            fuel_power_adjustment_override=(
                fuel_power_adjustment_override
            ),
            tod_energy_split=dict(
                tod_energy_split or {}
            ),
            use_tod=use_tod,
            annual_energy_kwh=annual_energy_kwh,
            renewable_energy_kwh=renewable_energy_kwh,
        )

        self.validate_inputs(inputs)

        tariff = self.get_tariff(
            state=inputs.state,
            discom=inputs.discom,
            tariff_category=inputs.tariff_category,
            voltage_level=voltage_level,
        )

        energy = inputs.monthly_energy_kwh

        # Energy charge
        base_energy_charge = self.calculate_energy_charge(
            tariff,
            energy,
        )

        tod_charge = base_energy_charge
        tod_adjustment = 0.0
        _applied_tod_rates: Dict[str, float] = {}

        if inputs.use_tod:
            (
                tod_charge,
                tod_adjustment,
                _applied_tod_rates,
            ) = self.calculate_tod_charge(
                tariff,
                energy,
                inputs.tod_energy_split,
            )

        # Demand
        demand_charge, billed_demand = (
            self.calculate_demand_charge(
                tariff,
                contracted_demand_kw=(
                    inputs.contracted_demand_kw
                ),
                contracted_demand_kva=(
                    inputs.contracted_demand_kva
                ),
                maximum_demand_kw=(
                    inputs.maximum_demand_kw
                ),
                maximum_demand_kva=(
                    inputs.maximum_demand_kva
                ),
            )
        )

        fixed_charge = self.calculate_fixed_charge(
            tariff
        )

        fuel_adjustment = (
            self.calculate_fuel_power_adjustment(
                tariff,
                energy,
                override_rate=(
                    inputs.fuel_power_adjustment_override
                ),
            )
        )

        subtotal_before_pf = (
            tod_charge
            + demand_charge
            + fixed_charge
            + fuel_adjustment
        )

        pf_adjustment = (
            self.calculate_power_factor_adjustment(
                tariff,
                subtotal_before_pf,
                inputs.average_power_factor,
            )
        )

        subtotal_before_duty = (
            subtotal_before_pf
            + pf_adjustment
        )

        duty_pct = (
            tariff.electricity_duty_pct
            if inputs.electricity_duty_pct_override is None
            else inputs.electricity_duty_pct_override
        )

        electricity_duty = (
            self.calculate_electricity_duty(
                subtotal_before_duty,
                float(duty_pct),
            )
        )

        total_before_minimum = (
            subtotal_before_duty
            + electricity_duty
        )

        minimum_adjustment = max(
            0.0,
            tariff.minimum_bill_inr_per_month
            - total_before_minimum,
        )

        subtotal_after_minimum = (
            total_before_minimum
            + minimum_adjustment
        )

        total_bill = subtotal_after_minimum

        annual_energy = (
            inputs.annual_energy_kwh
            if inputs.annual_energy_kwh is not None
            else energy * MONTHS_PER_YEAR
        )

        annual_charge = (
            total_bill
            * inputs.billing_months
        )

        average_cost = (
            annual_charge / annual_energy
            if annual_energy > 0
            else 0.0
        )

        emission_factor = (
            tariff.grid_emission_factor_kg_co2_per_kwh
            if tariff.grid_emission_factor_kg_co2_per_kwh
            is not None
            else self.default_grid_emission_factor_kg_co2_per_kwh
        )

        renewable_energy = max(
            0.0,
            min(
                annual_energy,
                inputs.renewable_energy_kwh,
            ),
        )

        grid_energy = max(
            0.0,
            annual_energy - renewable_energy,
        )

        annual_grid_emissions = (
            grid_energy * float(emission_factor)
        )

        notes: List[str] = []

        if tariff.status != "current":
            notes.append(
                "Tariff record is not marked current; verify before "
                "financial commitment."
            )

        if tariff.confidence != "high":
            notes.append(
                "Tariff source confidence is below high."
            )

        if tariff.tod_periods and not inputs.tod_energy_split:
            notes.append(
                "TOD tariff exists but no explicit TOD energy split "
                "was supplied; base energy charge was used."
            )

        if tariff.notes:
            notes.append(tariff.notes)

        breakdown = TariffChargeBreakdown(
            energy_charge=base_energy_charge,
            tod_adjustment=tod_adjustment,
            demand_charge=demand_charge,
            fixed_charge=fixed_charge,
            fuel_power_adjustment=fuel_adjustment,
            power_factor_adjustment=pf_adjustment,
            electricity_duty=electricity_duty,
            minimum_bill_adjustment=_round_money(
                minimum_adjustment
            ),
            total_before_minimum_bill=_round_money(
                total_before_minimum
            ),
            subtotal_after_minimum_bill=_round_money(
                subtotal_after_minimum
            ),
            total_bill=_round_money(total_bill),
        )

        return TariffResult(
            state=tariff.state,
            discom=tariff.discom,
            tariff_category=tariff.tariff_category,
            monthly_energy_kwh=energy,
            billing_months=inputs.billing_months,
            demand_basis=tariff.demand_basis,
            billed_demand=billed_demand,
            effective_energy_rate_inr_per_kwh=(
                (
                    tod_charge
                    / energy
                )
                if energy > 0
                else tariff.energy_charge_inr_per_kwh
            ),
            effective_demand_rate_inr_per_unit_month=(
                (
                    demand_charge
                    / billed_demand
                )
                if billed_demand > 0
                else 0.0
            ),
            monthly_charge=breakdown,
            annual_charge=_round_money(
                annual_charge
            ),
            annual_energy_kwh=_round_energy(
                annual_energy
            ),
            average_cost_inr_per_kwh=_round_rate(
                average_cost
            ),
            grid_emissions_kg_co2=_round_energy(
                annual_grid_emissions
            ),
            grid_emissions_tco2=(
                annual_grid_emissions / 1000
            ),
            source=tariff.source,
            status=tariff.status,
            confidence=tariff.confidence,
            notes=notes,
            raw_tariff=tariff,
        )

    # ---------------------------------------------------------------------
    # State comparison
    # ---------------------------------------------------------------------

    def compare_states(
        self,
        *,
        states: Sequence[str],
        tariff_category: str,
        monthly_energy_kwh: float,
        demand_kw: Optional[float] = None,
        demand_kva: Optional[float] = None,
        discom_by_state: Optional[Mapping[str, str]] = None,
        maximum_demand_kw: Optional[float] = None,
        maximum_demand_kva: Optional[float] = None,
        billing_months: int = 12,
        average_power_factor: Optional[float] = None,
        tod_energy_split: Optional[Mapping[str, float]] = None,
    ) -> StateTariffComparison:
        """Compare annual electricity costs across states."""
        if not states:
            raise TariffValidationError(
                "At least one state is required."
            )

        results: List[TariffResult] = []
        mapping = discom_by_state or {}

        for state in states:
            discom = mapping.get(state)

            result = self.calculate_bill(
                state=state,
                discom=discom,
                tariff_category=tariff_category,
                monthly_energy_kwh=monthly_energy_kwh,
                contracted_demand_kw=demand_kw,
                contracted_demand_kva=demand_kva,
                maximum_demand_kw=maximum_demand_kw,
                maximum_demand_kva=maximum_demand_kva,
                billing_months=billing_months,
                average_power_factor=average_power_factor,
                tod_energy_split=tod_energy_split,
            )

            results.append(result)

        results.sort(
            key=lambda item: item.annual_charge
        )

        cheapest = (
            results[0]
            if results
            else None
        )

        most_expensive = (
            results[-1]
            if results
            else None
        )

        if cheapest and most_expensive:
            savings = (
                most_expensive.annual_charge
                - cheapest.annual_charge
            )

            if cheapest.annual_charge > 0:
                spread = (
                    savings
                    / cheapest.annual_charge
                    * 100
                )
            else:
                spread = None

            cheapest_state = cheapest.state
            most_expensive_state = (
                most_expensive.state
            )
        else:
            savings = None
            spread = None
            cheapest_state = None
            most_expensive_state = None

        return StateTariffComparison(
            results=results,
            cheapest_state=cheapest_state,
            most_expensive_state=most_expensive_state,
            savings_vs_most_expensive_inr_per_year=savings,
            spread_pct=spread,
        )

    # ---------------------------------------------------------------------
    # Escalation
    # ---------------------------------------------------------------------

    def project_escalation(
        self,
        *,
        base_result: TariffResult,
        years: int,
        annual_escalation_rate: Optional[float] = None,
        base_year: Optional[int] = None,
        annual_rate_schedule: Optional[
            Mapping[int, float]
        ] = None,
    ) -> EscalationProjection:
        """
        Project tariff costs over future years.

        Annual rates are applied multiplicatively.

        Example:
            Year 1 = base * (1+r1)
            Year 2 = Year 1 * (1+r2)
        """
        year_count = _safe_int(
            years,
            field_name="years",
            minimum=0,
            maximum=100,
        )

        start_year = (
            base_year
            if base_year is not None
            else datetime.now().year
        )

        if annual_escalation_rate is None:
            if (
                base_result.raw_tariff is not None
                and base_result.raw_tariff.annual_escalation_rate
                is not None
            ):
                annual_escalation_rate = (
                    base_result.raw_tariff.annual_escalation_rate
                )
            else:
                annual_escalation_rate = (
                    DEFAULT_ESCALATION_RATE
                )

        rate = _safe_float(
            annual_escalation_rate,
            field_name="annual_escalation_rate",
            minimum=-1,
        )

        schedule = dict(
            annual_rate_schedule or {}
        )

        base_cost = base_result.annual_charge
        base_energy = base_result.annual_energy_kwh

        projections: List[
            EscalationProjectionYear
        ] = []

        current_cost = base_cost

        for offset in range(
            1,
            year_count + 1,
        ):
            target_year = start_year + offset

            year_rate = (
                schedule.get(
                    target_year,
                    rate,
                )
            )

            if year_rate is None:
                year_rate = rate

            if year_rate < -1:
                raise TariffValidationError(
                    f"Escalation rate for {target_year} "
                    "cannot be below -100%."
                )

            current_cost *= (
                1 + year_rate
            )

            avg_cost = (
                current_cost / base_energy
                if base_energy > 0
                else 0.0
            )

            projections.append(
                EscalationProjectionYear(
                    year=target_year,
                    escalation_rate=float(
                        year_rate
                    ),
                    projected_annual_charge=(
                        _round_money(
                            current_cost
                        )
                    ),
                    projected_average_cost_inr_per_kwh=(
                        _round_rate(
                            avg_cost
                        )
                    ),
                )
            )

        cumulative_increase = (
            0.0
            if base_cost <= 0 or not projections
            else (
                (
                    projections[-1].projected_annual_charge
                    / base_cost
                )
                - 1
            )
            * 100
        )

        return EscalationProjection(
            base_year=start_year,
            years=projections,
            cumulative_increase_pct=cumulative_increase,
        )

    # ---------------------------------------------------------------------
    # Grid emission factors
    # ---------------------------------------------------------------------

    def get_grid_emission_factor(
        self,
        *,
        state: str,
        discom: Optional[str] = None,
        tariff_category: str = "industrial",
        custom_factor_kg_co2_per_kwh: Optional[float] = None,
    ) -> float:
        """
        Return grid emission factor.

        Priority:
        1. custom caller-supplied factor
        2. tariff record factor
        3. engine default factor
        """
        if custom_factor_kg_co2_per_kwh is not None:
            return _safe_float(
                custom_factor_kg_co2_per_kwh,
                field_name="custom_factor_kg_co2_per_kwh",
                minimum=0,
            ) or 0.0

        try:
            tariff = self.get_tariff(
                state=state,
                discom=discom,
                tariff_category=tariff_category,
            )
        except TariffNotFoundError:
            return self.default_grid_emission_factor_kg_co2_per_kwh

        if tariff.grid_emission_factor_kg_co2_per_kwh is not None:
            return tariff.grid_emission_factor_kg_co2_per_kwh

        return self.default_grid_emission_factor_kg_co2_per_kwh

    def calculate_grid_emissions(
        self,
        annual_energy_kwh: float,
        *,
        emission_factor_kg_co2_per_kwh: Optional[float] = None,
    ) -> Dict[str, float]:
        """Calculate grid emissions."""
        energy = _safe_float(
            annual_energy_kwh,
            field_name="annual_energy_kwh",
            minimum=0,
        ) or 0.0

        factor = (
            self.default_grid_emission_factor_kg_co2_per_kwh
            if emission_factor_kg_co2_per_kwh is None
            else _safe_float(
                emission_factor_kg_co2_per_kwh,
                field_name="emission_factor_kg_co2_per_kwh",
                minimum=0,
            )
        )

        emissions_kg = energy * float(factor)

        return {
            "annual_energy_kwh": _round_energy(
                energy
            ),
            "emission_factor_kg_co2_per_kwh": _round_rate(
                float(factor)
            ),
            "emissions_kg_co2": _round_energy(
                emissions_kg
            ),
            "emissions_tco2": round(
                emissions_kg / 1000,
                6,
            ),
        }

    # ---------------------------------------------------------------------
    # Renewable procurement
    # ---------------------------------------------------------------------

    def model_renewable_procurement(
        self,
        *,
        baseline_result: TariffResult,
        annual_renewable_kwh: float,
        source_type: str,
        renewable_energy_rate_inr_per_kwh: float,
        wheeling_charge_inr_per_kwh: float = 0.0,
        cross_subsidy_surcharge_inr_per_kwh: float = 0.0,
        additional_surcharge_inr_per_kwh: float = 0.0,
        banking_charge_pct: float = 0.0,
        annual_fixed_cost_inr: float = 0.0,
        annual_other_cost_inr: float = 0.0,
        renewable_emission_factor_kg_co2_per_kwh: float = (
            DEFAULT_GREEN_POWER_EMISSION_FACTOR_KG_CO2_PER_KWH
        ),
    ) -> RenewableProcurementScenario:
        """
        Model renewable procurement against the grid baseline.

        Costs include:
            renewable energy purchase
            + wheeling
            + CSS
            + additional surcharge
            + banking
            + annual fixed costs
            + annual other costs
        """
        renewable_kwh = _safe_float(
            annual_renewable_kwh,
            field_name="annual_renewable_kwh",
            minimum=0,
        ) or 0.0

        baseline_energy = baseline_result.annual_energy_kwh

        renewable_kwh = min(
            renewable_kwh,
            baseline_energy,
        )

        renewable_rate = _safe_float(
            renewable_energy_rate_inr_per_kwh,
            field_name="renewable_energy_rate_inr_per_kwh",
            minimum=0,
        ) or 0.0

        wheeling = _safe_float(
            wheeling_charge_inr_per_kwh,
            field_name="wheeling_charge_inr_per_kwh",
            minimum=0,
        ) or 0.0

        css = _safe_float(
            cross_subsidy_surcharge_inr_per_kwh,
            field_name=(
                "cross_subsidy_surcharge_inr_per_kwh"
            ),
            minimum=0,
        ) or 0.0

        additional = _safe_float(
            additional_surcharge_inr_per_kwh,
            field_name=(
                "additional_surcharge_inr_per_kwh"
            ),
            minimum=0,
        ) or 0.0

        banking_pct = _safe_float(
            banking_charge_pct,
            field_name="banking_charge_pct",
            minimum=0,
            maximum=100,
        ) or 0.0

        fixed_cost = _safe_float(
            annual_fixed_cost_inr,
            field_name="annual_fixed_cost_inr",
            minimum=0,
        ) or 0.0

        other_cost = _safe_float(
            annual_other_cost_inr,
            field_name="annual_other_cost_inr",
            minimum=0,
        ) or 0.0

        re_factor = _safe_float(
            renewable_emission_factor_kg_co2_per_kwh,
            field_name=(
                "renewable_emission_factor_kg_co2_per_kwh"
            ),
            minimum=0,
        ) or 0.0

        base_cost_component = (
            renewable_rate
            + wheeling
            + css
            + additional
        )

        banking_cost = (
            base_cost_component
            * banking_pct
            / 100
        )

        variable_cost = (
            renewable_kwh
            * (
                base_cost_component
                + banking_cost
            )
        )

        total_cost = (
            variable_cost
            + fixed_cost
            + other_cost
        )

        baseline_unit_cost = (
            baseline_result.average_cost_inr_per_kwh
        )

        baseline_cost_for_covered_energy = (
            renewable_kwh
            * baseline_unit_cost
        )

        savings = (
            baseline_cost_for_covered_energy
            - total_cost
        )

        baseline_emissions = (
            renewable_kwh
            * (
                baseline_result.grid_emissions_kg_co2
                / baseline_energy
                if baseline_energy > 0
                else self.default_grid_emission_factor_kg_co2_per_kwh
            )
        )

        renewable_emissions = (
            renewable_kwh
            * re_factor
        )

        emissions_reduction = (
            baseline_emissions
            - renewable_emissions
        )

        notes = []

        if source_type.lower() in {
            "open_access",
            "group_captive",
            "captive",
        }:
            notes.append(
                "Final delivered renewable cost must include all "
                "state-specific open-access charges and applicable "
                "regulatory conditions."
            )

        if savings < 0:
            notes.append(
                "Renewable procurement is more expensive than the "
                "baseline for the modeled covered energy under the "
                "supplied assumptions."
            )

        return RenewableProcurementScenario(
            source_type=source_type,
            annual_renewable_kwh=renewable_kwh,
            energy_rate_inr_per_kwh=renewable_rate,
            wheeling_charge_inr_per_kwh=wheeling,
            css_inr_per_kwh=css,
            additional_surcharge_inr_per_kwh=additional,
            banking_cost_inr_per_kwh=banking_cost,
            annual_fixed_cost_inr=fixed_cost,
            annual_other_cost_inr=other_cost,
            renewable_emission_factor_kg_co2_per_kwh=re_factor,
            baseline_grid_cost_inr=baseline_cost_for_covered_energy,
            total_renewable_cost_inr=total_cost,
            annual_savings_inr=savings,
            baseline_emissions_kg_co2=baseline_emissions,
            renewable_emissions_kg_co2=renewable_emissions,
            emissions_reduction_kg_co2=emissions_reduction,
            notes=notes,
        )

    # ---------------------------------------------------------------------
    # Open access suitability
    # ---------------------------------------------------------------------

    def assess_open_access(
        self,
        *,
        annual_consumption_kwh: float,
        contracted_demand_kw: float,
        annual_renewable_generation_kwh: float,
        baseline_tariff_inr_per_kwh: Optional[float] = None,
        renewable_energy_rate_inr_per_kwh: Optional[float] = None,
        wheeling_charge_inr_per_kwh: float = 0.0,
        cross_subsidy_surcharge_inr_per_kwh: float = 0.0,
        additional_surcharge_inr_per_kwh: float = 0.0,
        banking_charge_pct: float = 0.0,
        renewable_emission_factor_kg_co2_per_kwh: float = (
            DEFAULT_GREEN_POWER_EMISSION_FACTOR_KG_CO2_PER_KWH
        ),
        minimum_load_kw: Optional[float] = None,
    ) -> OpenAccessAssessment:
        """
        Assess Green Energy Open Access suitability.

        This is a screening engine, not a legal eligibility opinion.
        State-specific orders/rules should be verified before financial
        commitment.

        Primary checks:
        - minimum contracted-load threshold
        - renewable generation availability
        - renewable coverage
        - indicative economic result
        - indicative emissions reduction
        """
        consumption = _safe_float(
            annual_consumption_kwh,
            field_name="annual_consumption_kwh",
            minimum=0,
        ) or 0.0

        demand = _safe_float(
            contracted_demand_kw,
            field_name="contracted_demand_kw",
            minimum=0,
        ) or 0.0

        generation = _safe_float(
            annual_renewable_generation_kwh,
            field_name="annual_renewable_generation_kwh",
            minimum=0,
        ) or 0.0

        threshold = (
            self.minimum_geoa_load_kw
            if minimum_load_kw is None
            else _safe_float(
                minimum_load_kw,
                field_name="minimum_load_kw",
                minimum=0,
            )
        )

        if threshold is None:
            threshold = self.minimum_geoa_load_kw

        eligible_by_load = demand >= threshold

        generation_sufficient = (
            generation > 0
            and consumption > 0
        )

        annual_consumption_threshold_met = (
            consumption > 0
        )

        coverage_pct = (
            min(
                100.0,
                generation / consumption * 100,
            )
            if consumption > 0
            else 0.0
        )

        baseline_rate = (
            baseline_tariff_inr_per_kwh
            if baseline_tariff_inr_per_kwh is not None
            else 0.0
        )

        renewable_rate = (
            renewable_energy_rate_inr_per_kwh
            if renewable_energy_rate_inr_per_kwh is not None
            else 0.0
        )

        oa_unit_cost = (
            renewable_rate
            + wheeling_charge_inr_per_kwh
            + cross_subsidy_surcharge_inr_per_kwh
            + additional_surcharge_inr_per_kwh
        )

        banking_cost = (
            oa_unit_cost
            * banking_charge_pct
            / 100
        )

        oa_unit_cost += banking_cost

        covered_kwh = min(
            consumption,
            generation,
        )

        uncovered_kwh = max(
            0.0,
            consumption - covered_kwh,
        )

        estimated_grid_cost = (
            consumption
            * baseline_rate
        )

        estimated_oa_cost = (
            covered_kwh
            * oa_unit_cost
            + uncovered_kwh
            * baseline_rate
        )

        savings = (
            estimated_grid_cost
            - estimated_oa_cost
        )

        grid_factor = (
            self.default_grid_emission_factor_kg_co2_per_kwh
        )

        baseline_emissions = (
            covered_kwh
            * grid_factor
        )

        renewable_emissions = (
            covered_kwh
            * renewable_emission_factor_kg_co2_per_kwh
        )

        emissions_reduction = (
            baseline_emissions
            - renewable_emissions
        )

        reasons: List[str] = []
        warnings: List[str] = []

        score = 0.0

        if eligible_by_load:
            score += 40.0
            reasons.append(
                "Contracted demand meets the configured "
                "open-access screening threshold."
            )
        else:
            warnings.append(
                "Contracted demand is below the configured "
                "open-access screening threshold."
            )

        if generation_sufficient:
            score += 20.0
            reasons.append(
                "Renewable generation is available for the "
                "screened scenario."
            )
        else:
            warnings.append(
                "No positive renewable generation volume was supplied."
            )

        if coverage_pct >= 50:
            score += 20.0
            reasons.append(
                "Renewable generation can cover a substantial "
                "share of annual electricity demand."
            )
        elif coverage_pct > 0:
            score += 10.0
            reasons.append(
                "Renewable generation covers part of annual demand."
            )

        if savings > 0:
            score += 10.0
            reasons.append(
                "Indicative open-access economics show annual savings."
            )
        else:
            warnings.append(
                "Indicative open-access economics do not show savings "
                "under the supplied assumptions."
            )

        if emissions_reduction > 0:
            score += 10.0
            reasons.append(
                "The screened renewable procurement reduces grid-related "
                "CO2 emissions."
            )

        suitable = (
            eligible_by_load
            and generation_sufficient
            and coverage_pct > 0
            and score >= 50.0
        )

        warnings.append(
            "This assessment is a financial/technical screening result, "
            "not a legal determination of open-access eligibility."
        )

        return OpenAccessAssessment(
            eligible_by_load=eligible_by_load,
            annual_consumption_threshold_met=(
                annual_consumption_threshold_met
            ),
            generation_sufficient=generation_sufficient,
            contracted_demand_kw=demand,
            annual_consumption_kwh=consumption,
            annual_renewable_generation_kwh=generation,
            minimum_load_kw=float(threshold),
            renewable_coverage_pct=coverage_pct,
            estimated_grid_cost_inr=estimated_grid_cost,
            estimated_open_access_cost_inr=(
                estimated_oa_cost
            ),
            estimated_savings_inr=savings,
            estimated_emissions_reduction_kg_co2=(
                emissions_reduction
            ),
            suitable=suitable,
            score=score,
            reasons=reasons,
            warnings=warnings,
        )

    # ---------------------------------------------------------------------
    # Integration helpers
    # ---------------------------------------------------------------------

    def calculate_from_factory_input(
        self,
        factory: Mapping[str, Any],
    ) -> TariffResult:
        """
        Calculate tariff from the shared factory input contract.

        Supported keys include:
            location
            electricity_kwh_day
            grid_capacity_kw
            operating_hours
            annual_electricity_kwh
            discom
            tariff_category
        """
        state = _clean_text(
            factory.get("state")
            or factory.get("location")
        )

        if not state:
            raise TariffValidationError(
                "Factory input must contain 'state' or 'location'."
            )

        electricity_kwh_day = factory.get(
            "electricity_kwh_day"
        )

        if electricity_kwh_day is None:
            electricity_kwh_day = factory.get(
                "daily_electricity_kwh",
                0,
            )

        monthly_energy = (
            float(electricity_kwh_day)
            * DEFAULT_BILLING_DAYS
        )

        annual_energy = factory.get(
            "annual_electricity_kwh"
        )

        if annual_energy is None:
            annual_energy = (
                float(electricity_kwh_day)
                * 365
            )

        contracted_kw = factory.get(
            "contracted_demand_kw"
        )

        if contracted_kw is None:
            contracted_kw = factory.get(
                "grid_capacity_kw"
            )

        return self.calculate_bill(
            state=state,
            discom=factory.get("discom"),
            tariff_category=(
                factory.get(
                    "tariff_category",
                    "industrial",
                )
            ),
            monthly_energy_kwh=monthly_energy,
            contracted_demand_kw=contracted_kw,
            maximum_demand_kw=factory.get(
                "maximum_demand_kw"
            ),
            billing_months=12,
            average_power_factor=factory.get(
                "power_factor"
            ),
            annual_energy_kwh=annual_energy,
        )

    def build_electricity_cost_summary(
        self,
        *,
        state: str,
        discom: Optional[str],
        tariff_category: str,
        annual_energy_kwh: float,
        demand_kw: Optional[float] = None,
        demand_kva: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Return a compact decision-engine-friendly summary.

        Designed for direct integration into pathway/finance calculations.
        """
        monthly_energy = (
            float(annual_energy_kwh)
            / MONTHS_PER_YEAR
        )

        result = self.calculate_bill(
            state=state,
            discom=discom,
            tariff_category=tariff_category,
            monthly_energy_kwh=monthly_energy,
            contracted_demand_kw=demand_kw,
            contracted_demand_kva=demand_kva,
            billing_months=12,
            annual_energy_kwh=annual_energy_kwh,
        )

        return {
            "state": result.state,
            "discom": result.discom,
            "tariff_category": result.tariff_category,
            "annual_energy_kwh": result.annual_energy_kwh,
            "annual_electricity_cost_inr": (
                result.annual_charge
            ),
            "electricity_cost_inr_per_kwh": (
                result.average_cost_inr_per_kwh
            ),
            "annual_grid_emissions_tco2": (
                result.grid_emissions_tco2
            ),
            "demand_basis": result.demand_basis,
            "billed_demand": result.billed_demand,
            "source": result.source,
            "status": result.status,
            "confidence": result.confidence,
            "notes": result.notes,
        }


# ============================================================================
# Standalone helper functions
# ============================================================================


def _select_tod_period(
    periods: Sequence[TODPeriod],
) -> TODPeriod:
    """Select highest-priority TOD period."""
    return max(
        periods,
        key=lambda item: item.priority,
    )


def _calculate_tod_multiplier(
    period: TODPeriod,
) -> float:
    """
    Calculate effective TOD multiplier.

    Formula:
        multiplier × (1 + surcharge%)
                  × (1 - discount%)
    """
    return (
        period.multiplier
        * (
            1
            + period.surcharge_pct / 100
        )
        * (
            1
            - period.discount_pct / 100
        )
    )


def _normalize_tod_split(
    split: Mapping[str, float],
) -> Dict[str, float]:
    """Normalize TOD allocation to shares summing to 1."""
    cleaned: Dict[str, float] = {}

    for key, value in split.items():
        amount = _safe_float(
            value,
            field_name=f"tod_split[{key}]",
            minimum=0,
        ) or 0.0

        cleaned[str(key)] = amount

    total = sum(cleaned.values())

    if total <= 0:
        raise TariffValidationError(
            "TOD split must have a positive total."
        )

    return {
        key: value / total
        for key, value in cleaned.items()
    }


def annualize_bill(
    monthly_bill_inr: float,
    months: int = 12,
) -> float:
    """Annualize a monthly electricity bill."""
    return _round_money(
        float(monthly_bill_inr) * months
    )


def calculate_simple_tariff_cost(
    annual_energy_kwh: float,
    energy_rate_inr_per_kwh: float,
    *,
    annual_fixed_charges_inr: float = 0.0,
    annual_demand_charges_inr: float = 0.0,
    duty_pct: float = 0.0,
) -> float:
    """
    Lightweight helper for callers that do not need TariffEngine.

    Useful in finance/impact modules when a fully resolved tariff record already
    exists upstream.
    """
    energy = _safe_float(
        annual_energy_kwh,
        field_name="annual_energy_kwh",
        minimum=0,
    ) or 0.0

    energy_rate = _safe_float(
        energy_rate_inr_per_kwh,
        field_name="energy_rate_inr_per_kwh",
        minimum=0,
    ) or 0.0

    fixed = _safe_float(
        annual_fixed_charges_inr,
        field_name="annual_fixed_charges_inr",
        minimum=0,
    ) or 0.0

    demand = _safe_float(
        annual_demand_charges_inr,
        field_name="annual_demand_charges_inr",
        minimum=0,
    ) or 0.0

    duty = _safe_float(
        duty_pct,
        field_name="duty_pct",
        minimum=0,
        maximum=100,
    ) or 0.0

    subtotal = (
        energy * energy_rate
        + fixed
        + demand
    )

    duty_amount = (
        subtotal * duty / 100
    )

    return _round_money(
        subtotal + duty_amount
    )


def compare_tariff_costs(
    tariff_results: Iterable[TariffResult],
) -> List[Tuple[str, float]]:
    """
    Return tariff results sorted from cheapest to most expensive.

    Useful for optimizer ranking.
    """
    values = [
        (
            result.state,
            result.annual_charge,
        )
        for result in tariff_results
    ]

    return sorted(
        values,
        key=lambda item: item[1],
    )


def tariff_result_to_pathway_metrics(
    result: TariffResult,
) -> Dict[str, float]:
    """
    Convert TariffResult to optimizer-friendly metrics.

    This intentionally uses the shared decision-engine vocabulary:
        annual_cost
        electricity_cost
        co2
    """
    return {
        "annual_cost": float(
            result.annual_charge
        ),
        "electricity_cost": float(
            result.annual_charge
        ),
        "electricity_cost_inr_per_kwh": float(
            result.average_cost_inr_per_kwh
        ),
        "co2_kg": float(
            result.grid_emissions_kg_co2
        ),
        "co2_tonnes": float(
            result.grid_emissions_tco2
        ),
    }


# ============================================================================
# Backward-compatible aliases
# ============================================================================


ElectricityTariffEngine = TariffEngine


# ============================================================================
# Public exports
# ============================================================================


__all__ = [
    "TariffEngineError",
    "TariffValidationError",
    "TariffNotFoundError",
    "TariffDataError",
    "UnsupportedCalculationError",
    "TODPeriod",
    "TariffSlab",
    "TariffRecord",
    "TariffCalculationInput",
    "TariffChargeBreakdown",
    "TariffResult",
    "StateTariffComparison",
    "EscalationProjectionYear",
    "EscalationProjection",
    "RenewableProcurementScenario",
    "OpenAccessAssessment",
    "TariffStore",
    "TariffEngine",
    "ElectricityTariffEngine",
    "load_tariffs_from_csv",
    "tariff_record_to_dict",
    "tariff_record_from_dict",
    "tod_period_to_dict",
    "tod_period_from_dict",
    "tariff_slab_to_dict",
    "tariff_slab_from_dict",
    "annualize_bill",
    "calculate_simple_tariff_cost",
    "compare_tariff_costs",
    "tariff_result_to_pathway_metrics",
]


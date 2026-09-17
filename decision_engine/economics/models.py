from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class DataGapFlag:
    """
    Indicates a missing or low-confidence data point that impacts the financial model.
    """
    field: str
    severity: str  # "blocking" or "warning"
    reason: str
    source_id: str | None


@dataclass(frozen=True)
class CapexResult:
    """
    Result of a CAPEX calculation. 
    Gracefully handles missing data instead of raising an exception.
    """
    status: str  # "available", "unavailable", "partial"
    capex_min_inr: float | None
    capex_max_inr: float | None
    capex_estimate_inr: float | None
    confidence: str | None
    source_id: str | None
    last_verified: str | None


@dataclass(frozen=True)
class OpexResult:
    """
    Result of an OPEX calculation with confidence propagation.
    """
    fuel_cost_inr: float | None
    electricity_cost_inr: float | None
    maintenance_cost_inr: float | None
    labour_cost_inr: float | None
    other_cost_inr: float | None
    total_inr: float
    confidence_summary: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class FinancialModel:
    """
    Complete financial result for one technology scenario.
    Version 2.0 with data quality gates, NPV, and robust confidence propagation.
    """
    technology_id: str
    scenario_id: str

    # CAPEX
    capex: CapexResult

    # OPEX
    baseline_opex: OpexResult
    proposed_opex: OpexResult

    # Savings (range)
    annual_savings_min_inr: float | None
    annual_savings_max_inr: float | None

    # Payback (range)
    payback_min_years: float | None
    payback_max_years: float | None

    # NPV (range)
    npv_min_inr: float | None
    npv_max_inr: float | None
    discount_rate_pct: float | None
    lifetime_years: float | None

    # Simple ROI (range)
    roi_min_pct: float | None
    roi_max_pct: float | None

    # Data quality gate
    firm_recommendation_blocked: bool
    firm_recommendation_blocked_reasons: list[str] = field(default_factory=list)
    data_gap_flags: list[DataGapFlag] = field(default_factory=list)
    data_quality_warnings: list[str] = field(default_factory=list)
    confidence_propagation: dict[str, str] = field(default_factory=dict)

    # Note: ReliabilitySweepResult is imported optionally in the engine,
    # or kept here as Any/dict to avoid circular dependencies if needed.
    monte_carlo_result: Any | None = None

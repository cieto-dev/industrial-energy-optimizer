"""
mcda.py — Multi-criteria scoring (weighted sum after min-max normalisation).

Purpose
-------
Turn raw economics / emissions / reliability metrics into the three
DOMAIN_MODEL `objective_scores` (cost, emissions, risk) and a composite
MCDA score. Ranking is NOT least-cost-only.

Method
------
Weighted Sum Method (WSM) on benefit scores in [0, 1]:

    1. Extract a raw *cost* metric (lower is better): lifecycle cost
       = CAPEX + annual OPEX × 10-year MSME planning horizon.
    2. Extract a raw *emissions* metric (lower is better): pathway CO2
       tonnes/year, or 100 − reduction_pct if only a reduction is supplied.
    3. Extract a raw *risk* metric (lower is better): reliability
       spread_ratio, else a numeric mapping of the risk tier.
    4. Min-max normalise each criterion across the candidate set, then
       invert so higher = better (matches models/scenario.py ObjectiveScores).
    5. composite = w_cost × cost + w_emissions × emissions + w_risk × risk

When every candidate has the same raw value on a criterion, that
criterion scores 1.0 for all (no false differentiation).

This module does not rank and does not pick a winner. ranking.py sorts;
optimization_engine.py orchestrates.

Dependency
----------
    weights.py
    Upstream values are passed in — this file does not call
    economics/, emissions/, or reliability/ engines.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable, Optional

from decision_engine.optimizer.weights import (
    CRITERION_COST,
    CRITERION_EMISSIONS,
    CRITERION_RISK,
    Weights,
    default_weights,
)


# MSME planning horizon used to combine CAPEX (stock) and OPEX (flow)
# into one cost metric. Documented so it is not a silent magic number.
COST_HORIZON_YEARS = 10.0

TIER_TO_RISK_VALUE = {
    "LOW": 0.10,
    "MEDIUM": 0.25,
    "HIGH": 0.40,
    "VERY_HIGH": 0.60,
}


@dataclass
class ScenarioMetrics:
    """
    Raw inputs for one candidate pathway, collected from upstream engines.

    The optimizer does not recompute CAPEX, CO2, or sweep results.
    Missing optional fields are filled from duck-typed nested objects
    when present (economics FinancialModel, models.EmissionModel,
    reliability ScenarioRiskScore / ReliabilitySweepResult).
    """

    scenario_id: str
    technology_sequence: list[str] = field(default_factory=list)
    capex_inr: Optional[float] = None
    annual_opex_inr: Optional[float] = None
    pathway_co2_tonnes_year: Optional[float] = None
    co2_reduction_pct: Optional[float] = None
    spread_ratio: Optional[float] = None
    risk_tier: Optional[str] = None
    reliability_score_pct: Optional[float] = None
    financial: Any = None
    emission: Any = None
    risk_score: Any = None
    extra: dict[str, Any] = field(default_factory=dict)


@dataclass
class ScoredScenario:
    """One scenario after MCDA scoring."""

    scenario_id: str
    technology_sequence: list[str]
    raw_cost: float
    raw_emissions: float
    raw_risk: float
    objective_scores: dict[str, float]
    composite_score: float
    metrics: ScenarioMetrics


def _attr(obj: Any, *names: str) -> Optional[float]:
    if obj is None:
        return None
    for name in names:
        if isinstance(obj, dict) and name in obj:
            value = obj[name]
        else:
            value = getattr(obj, name, None)
        if value is not None:
            try:
                return float(value)
            except (TypeError, ValueError):
                continue
    return None


def _str_attr(obj: Any, *names: str) -> Optional[str]:
    if obj is None:
        return None
    for name in names:
        if isinstance(obj, dict) and name in obj:
            value = obj[name]
        else:
            value = getattr(obj, name, None)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


def _resolve_capex(metrics: ScenarioMetrics) -> float:
    capex = metrics.capex_inr
    if capex is None:
        capex = _attr(
            metrics.financial,
            "capex_estimate",
            "capex_gross_inr",
            "net_financed_cost_inr",
            "capex_min",
        )
    if capex is None:
        raise ValueError(
            f"Scenario '{metrics.scenario_id}' is missing CAPEX "
            "(capex_inr or financial.capex_*)."
        )
    if capex < 0:
        raise ValueError(
            f"Scenario '{metrics.scenario_id}' CAPEX cannot be negative."
        )
    return capex


def _resolve_opex(metrics: ScenarioMetrics) -> float:
    opex = metrics.annual_opex_inr
    if opex is None:
        opex = _attr(
            metrics.financial,
            "proposed_annual_opex",
            "annual_opex_inr",
        )
    if opex is None:
        return 0.0
    if opex < 0:
        raise ValueError(
            f"Scenario '{metrics.scenario_id}' OPEX cannot be negative."
        )
    return opex


def lifecycle_cost(metrics: ScenarioMetrics) -> float:
    """Lower is better. CAPEX + 10 years of proposed annual OPEX."""
    return _resolve_capex(metrics) + _resolve_opex(metrics) * COST_HORIZON_YEARS


def raw_emissions_metric(metrics: ScenarioMetrics) -> float:
    """
    Lower is better.

    Prefer absolute pathway CO2 (tonnes/year). If only a reduction
    percentage is available, invert it so a 90% cut scores better than 10%.
    """
    pathway = metrics.pathway_co2_tonnes_year
    if pathway is None:
        pathway = _attr(
            metrics.emission,
            "pathway_co2_tonnes_year",
        )
    if pathway is not None:
        if pathway < 0:
            raise ValueError(
                f"Scenario '{metrics.scenario_id}' pathway CO2 cannot "
                "be negative."
            )
        return pathway

    reduction = metrics.co2_reduction_pct
    if reduction is None:
        reduction = _attr(metrics.emission, "reduction_pct", "co2_reduction_pct")
    if reduction is None:
        raise ValueError(
            f"Scenario '{metrics.scenario_id}' is missing emissions "
            "(pathway_co2_tonnes_year or co2_reduction_pct)."
        )
    return max(0.0, 100.0 - float(reduction))


def raw_risk_metric(metrics: ScenarioMetrics) -> float:
    """
    Lower is better.

    Prefer the Monte Carlo spread_ratio from reliability_engine.
    Fall back to the derived risk tier, then to inverted reliability %.
    """
    spread = metrics.spread_ratio
    if spread is None:
        spread = _attr(metrics.risk_score, "spread_ratio")
    if spread is not None:
        if spread < 0:
            raise ValueError(
                f"Scenario '{metrics.scenario_id}' spread_ratio cannot "
                "be negative."
            )
        return spread

    tier = metrics.risk_tier
    if tier is None:
        tier = _str_attr(metrics.risk_score, "overall_tier")
    if tier is not None:
        key = tier.upper()
        if key not in TIER_TO_RISK_VALUE:
            raise ValueError(
                f"Scenario '{metrics.scenario_id}' has unknown risk tier "
                f"'{tier}'."
            )
        return TIER_TO_RISK_VALUE[key]

    reliability_pct = metrics.reliability_score_pct
    if reliability_pct is None:
        reliability_pct = _attr(metrics.risk_score, "reliability_score_pct")
    if reliability_pct is not None:
        return max(0.0, 100.0 - float(reliability_pct))

    raise ValueError(
        f"Scenario '{metrics.scenario_id}' is missing risk "
        "(spread_ratio, risk_tier, or reliability_score_pct)."
    )


def _minmax_benefit(raw_values: list[float]) -> list[float]:
    """
    Convert lower-is-better raw values into higher-is-better scores in [0, 1].

    benefit_i = (max - x_i) / (max - min)
    """
    lo = min(raw_values)
    hi = max(raw_values)
    if hi - lo <= 0:
        return [1.0] * len(raw_values)
    return [(hi - value) / (hi - lo) for value in raw_values]


def score_scenarios(
    candidates: Iterable[ScenarioMetrics],
    weights: Optional[Weights] = None,
) -> list[ScoredScenario]:
    """
    Normalise and apply weights. Returns scored scenarios in input order.

    Does not sort. Does not select a recommended scenario.
    """
    metrics_list = list(candidates)
    if not metrics_list:
        raise ValueError("MCDA requires at least one scored scenario.")

    seen: set[str] = set()
    for item in metrics_list:
        if item.scenario_id in seen:
            raise ValueError(
                f"Duplicate scenario_id '{item.scenario_id}' in MCDA input."
            )
        seen.add(item.scenario_id)

    w = weights or default_weights()

    raw_cost = [lifecycle_cost(m) for m in metrics_list]
    raw_emissions = [raw_emissions_metric(m) for m in metrics_list]
    raw_risk = [raw_risk_metric(m) for m in metrics_list]

    cost_scores = _minmax_benefit(raw_cost)
    emissions_scores = _minmax_benefit(raw_emissions)
    risk_scores = _minmax_benefit(raw_risk)

    scored: list[ScoredScenario] = []
    for i, metrics in enumerate(metrics_list):
        objective = {
            CRITERION_COST: round(cost_scores[i], 6),
            CRITERION_EMISSIONS: round(emissions_scores[i], 6),
            CRITERION_RISK: round(risk_scores[i], 6),
        }
        composite = (
            w.cost * objective[CRITERION_COST]
            + w.emissions * objective[CRITERION_EMISSIONS]
            + w.risk * objective[CRITERION_RISK]
        )
        scored.append(
            ScoredScenario(
                scenario_id=metrics.scenario_id,
                technology_sequence=list(metrics.technology_sequence),
                raw_cost=raw_cost[i],
                raw_emissions=raw_emissions[i],
                raw_risk=raw_risk[i],
                objective_scores=objective,
                composite_score=round(composite, 6),
                metrics=metrics,
            )
        )
    return scored

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable, Optional

from decision_engine.optimizer.weights import (
    CRITERION_BIOMASS_DEPENDENCE,
    CRITERION_CARBON_REDUCTION,
    CRITERION_CONFIDENCE,
    CRITERION_ELECTRICITY_DEPENDENCE,
    CRITERION_FINANCIAL,
    CRITERION_IMPLEMENTATION_COMPLEXITY,
    CRITERION_POLICY,
    CRITERION_RESOURCE,
    CRITERION_RISK,
    CRITERION_SUPPLY_RELIABILITY,
    CRITERION_TECHNICAL,
    CRITERION_TECHNOLOGY_MATURITY,
    CRITERIA,
    CRITERION_IS_BENEFIT,
    Weights,
    default_weights,
)


# Retained for compatibility with the existing optimizer.
COST_HORIZON_YEARS = 10.0


@dataclass
class ScenarioMetrics:
    """
    Raw inputs for one candidate pathway.

    New research-informed criteria are intentionally optional so older
    scenario outputs remain usable while the upstream modules are migrated.
    """

    scenario_id: str
    technology_sequence: list[str] = field(default_factory=list)

    # Existing economic / emissions / reliability fields
    capex_inr: Optional[float] = None
    annual_opex_inr: Optional[float] = None
    pathway_co2_tonnes_year: Optional[float] = None
    co2_reduction_pct: Optional[float] = None
    spread_ratio: Optional[float] = None
    risk_tier: Optional[str] = None
    reliability_score_pct: Optional[float] = None

    # New MCDA dimensions
    technical_score: Optional[float] = None
    financial_score: Optional[float] = None
    resource_score: Optional[float] = None
    policy_score: Optional[float] = None
    risk_score_value: Optional[float] = None
    technology_maturity: Optional[float] = None
    implementation_complexity: Optional[float] = None
    supply_reliability: Optional[float] = None
    electricity_dependence: Optional[float] = None
    biomass_dependence: Optional[float] = None
    carbon_reduction: Optional[float] = None
    confidence_score: Optional[float] = None

    # Duck-typed upstream model objects
    financial: Any = None
    emission: Any = None
    risk_score: Any = None

    # Anything else passed by upstream modules
    extra: dict[str, Any] = field(default_factory=dict)


@dataclass
class ScoredScenario:
    """One scenario after multi-criteria scoring."""

    scenario_id: str
    technology_sequence: list[str]

    raw_cost: float
    raw_emissions: float
    raw_risk: float

    criterion_raw_values: dict[str, float]
    criterion_scores: dict[str, float]

    # Kept for backward compatibility with existing dashboard/code.
    objective_scores: dict[str, float]

    composite_score: float
    metrics: ScenarioMetrics


def _attr(obj: Any, *names: str) -> Optional[float]:
    if obj is None:
        return None

    for name in names:
        if isinstance(obj, dict):
            value = obj.get(name)
        else:
            value = getattr(obj, name, None)

        if value is None:
            continue

        try:
            return float(value)
        except (TypeError, ValueError):
            continue

    return None


def _str_attr(obj: Any, *names: str) -> Optional[str]:
    if obj is None:
        return None

    for name in names:
        if isinstance(obj, dict):
            value = obj.get(name)
        else:
            value = getattr(obj, name, None)

        if isinstance(value, str) and value.strip():
            return value.strip()

    return None


def _clamp_score(
    value: float,
    *,
    criterion: str,
    scenario_id: str,
) -> float:
    """
    Enforce the [0, 100] convention for manually supplied MCDA scores.
    """

    if not 0.0 <= value <= 100.0:
        raise ValueError(
            f"Scenario '{scenario_id}' criterion '{criterion}' "
            f"must be between 0 and 100, got {value}."
        )

    return value


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
            f"Scenario '{metrics.scenario_id}' is missing CAPEX."
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
    """Lower lifecycle cost is better."""
    return (
        _resolve_capex(metrics)
        + _resolve_opex(metrics) * COST_HORIZON_YEARS
    )


def raw_emissions_metric(metrics: ScenarioMetrics) -> float:
    """
    Lower emissions are better.

    Absolute pathway CO2 is preferred.
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
                f"Scenario '{metrics.scenario_id}' pathway CO2 "
                "cannot be negative."
            )
        return pathway

    reduction = metrics.co2_reduction_pct

    if reduction is None:
        reduction = _attr(
            metrics.emission,
            "reduction_pct",
            "co2_reduction_pct",
        )

    if reduction is None:
        raise ValueError(
            f"Scenario '{metrics.scenario_id}' is missing emissions."
        )

    return max(0.0, 100.0 - reduction)


def raw_risk_metric(metrics: ScenarioMetrics) -> float:
    """
    Lower risk is better.

    Preferred source:
      1. explicit spread_ratio
      2. supplied risk tier
      3. inverted reliability score
      4. explicit risk_score_value
    """

    if metrics.risk_score_value is not None:
        return _clamp_score(
            float(metrics.risk_score_value),
            criterion=CRITERION_RISK,
            scenario_id=metrics.scenario_id,
        )

    spread = metrics.spread_ratio

    if spread is None:
        spread = _attr(metrics.risk_score, "spread_ratio")

    if spread is not None:
        if spread < 0:
            raise ValueError(
                f"Scenario '{metrics.scenario_id}' spread_ratio "
                "cannot be negative."
            )
        return spread

    tier = metrics.risk_tier

    if tier is None:
        tier = _str_attr(metrics.risk_score, "overall_tier")

    if tier:
        values = {
            "LOW": 10.0,
            "MEDIUM": 25.0,
            "HIGH": 40.0,
            "VERY_HIGH": 60.0,
        }

        key = tier.upper()

        if key not in values:
            raise ValueError(
                f"Scenario '{metrics.scenario_id}' has unknown risk tier "
                f"'{tier}'."
            )

        return values[key]

    reliability = metrics.reliability_score_pct

    if reliability is None:
        reliability = _attr(
            metrics.risk_score,
            "reliability_score_pct",
        )

    if reliability is not None:
        return max(0.0, 100.0 - reliability)

    raise ValueError(
        f"Scenario '{metrics.scenario_id}' is missing risk information."
    )


def _resolve_criterion(
    metrics: ScenarioMetrics,
    criterion: str,
) -> Optional[float]:
    """
    Resolve a criterion from direct fields first, then useful upstream
    nested objects, then derived values where appropriate.
    """

    direct_map = {
        CRITERION_TECHNICAL: metrics.technical_score,
        CRITERION_FINANCIAL: metrics.financial_score,
        CRITERION_RESOURCE: metrics.resource_score,
        CRITERION_POLICY: metrics.policy_score,
        CRITERION_RISK: metrics.risk_score_value,
        CRITERION_TECHNOLOGY_MATURITY: metrics.technology_maturity,
        CRITERION_IMPLEMENTATION_COMPLEXITY: metrics.implementation_complexity,
        CRITERION_SUPPLY_RELIABILITY: metrics.supply_reliability,
        CRITERION_ELECTRICITY_DEPENDENCE: metrics.electricity_dependence,
        CRITERION_BIOMASS_DEPENDENCE: metrics.biomass_dependence,
        CRITERION_CARBON_REDUCTION: metrics.carbon_reduction,
        CRITERION_CONFIDENCE: metrics.confidence_score,
    }

    direct = direct_map.get(criterion)

    if direct is not None:
        return _clamp_score(
            float(direct),
            criterion=criterion,
            scenario_id=metrics.scenario_id,
        )

    # Common aliases accepted from upstream models.
    alias_map = {
        CRITERION_TECHNICAL: (
            "technical_score",
            "technical_feasibility",
            "technical",
        ),
        CRITERION_FINANCIAL: (
            "financial_score",
            "financial_feasibility",
            "financial",
        ),
        CRITERION_RESOURCE: (
            "resource_score",
            "resource_availability",
            "resource",
        ),
        CRITERION_POLICY: (
            "policy_score",
            "policy_support",
            "policy",
        ),
        CRITERION_TECHNOLOGY_MATURITY: (
            "technology_maturity",
            "maturity_score",
            "technology_readiness",
            "trl_score",
        ),
        CRITERION_IMPLEMENTATION_COMPLEXITY: (
            "implementation_complexity",
            "installation_complexity",
            "complexity_score",
        ),
        CRITERION_SUPPLY_RELIABILITY: (
            "supply_reliability",
            "fuel_reliability",
            "supply_score",
        ),
        CRITERION_ELECTRICITY_DEPENDENCE: (
            "electricity_dependence",
            "grid_dependence",
            "electricity_dependency",
        ),
        CRITERION_BIOMASS_DEPENDENCE: (
            "biomass_dependence",
            "biomass_dependency",
        ),
        CRITERION_CARBON_REDUCTION: (
            "carbon_reduction",
            "co2_reduction_pct",
        ),
        CRITERION_CONFIDENCE: (
            "confidence_score",
            "confidence",
            "evidence_confidence",
        ),
    }

    aliases = alias_map.get(criterion, ())

    nested_sources = (
        metrics.financial,
        metrics.emission,
        metrics.risk_score,
    )

    for source in nested_sources:
        value = _attr(source, *aliases)

        if value is not None:
            return _clamp_score(
                value,
                criterion=criterion,
                scenario_id=metrics.scenario_id,
            )

    # Derived fallbacks
    if criterion == CRITERION_RISK:
        return raw_risk_metric(metrics)

    if criterion == CRITERION_CARBON_REDUCTION:
        reduction = metrics.co2_reduction_pct

        if reduction is None:
            reduction = _attr(
                metrics.emission,
                "reduction_pct",
                "co2_reduction_pct",
            )

        if reduction is not None:
            return _clamp_score(
                reduction,
                criterion=criterion,
                scenario_id=metrics.scenario_id,
            )

    if criterion == CRITERION_TECHNICAL:
        technical = _attr(
            metrics.extra,
            "technical_score",
            "technical_feasibility",
        )

        if technical is not None:
            return _clamp_score(
                technical,
                criterion=criterion,
                scenario_id=metrics.scenario_id,
            )

    if criterion == CRITERION_SUPPLY_RELIABILITY:
        reliability = metrics.reliability_score_pct

        if reliability is None:
            reliability = _attr(
                metrics.risk_score,
                "reliability_score_pct",
            )

        if reliability is not None:
            return _clamp_score(
                reliability,
                criterion=criterion,
                scenario_id=metrics.scenario_id,
            )

    return None


def _default_from_legacy(metrics: ScenarioMetrics, criterion: str) -> float:
    """
    Compatibility fallback for older pathway contracts.

    We derive a few criteria from existing fields rather than inventing
    false precision.
    """

    if criterion == CRITERION_FINANCIAL:
        cost = lifecycle_cost(metrics)
        return 1.0 / (1.0 + cost / 1_000_000.0) * 100.0

    if criterion == CRITERION_TECHNICAL:
        return 100.0

    if criterion == CRITERION_RESOURCE:
        return 50.0

    if criterion == CRITERION_POLICY:
        return 50.0

    if criterion == CRITERION_TECHNOLOGY_MATURITY:
        return 50.0

    if criterion == CRITERION_IMPLEMENTATION_COMPLEXITY:
        return 50.0

    if criterion == CRITERION_ELECTRICITY_DEPENDENCE:
        return 50.0

    if criterion == CRITERION_BIOMASS_DEPENDENCE:
        return 50.0

    if criterion == CRITERION_CONFIDENCE:
        return 50.0

    raise ValueError(
        f"Scenario '{metrics.scenario_id}' is missing criterion "
        f"'{criterion}'."
    )


def _resolve_all_criteria(
    metrics: ScenarioMetrics,
) -> dict[str, float]:
    values: dict[str, float] = {}

    for criterion in CRITERIA:
        value = _resolve_criterion(metrics, criterion)

        if value is None:
            value = _default_from_legacy(
                metrics,
                criterion,
            )

        values[criterion] = float(value)

    return values


def _normalize(
    raw_values: list[float],
    *,
    benefit: bool,
) -> list[float]:
    """
    Min-max normalization to [0, 1].

    Benefit criterion:
        (x - min) / (max - min)

    Cost criterion:
        (max - x) / (max - min)

    Equal values receive 1.0 for every scenario because there is no
    discriminating information in that criterion.
    """

    if not raw_values:
        return []

    minimum = min(raw_values)
    maximum = max(raw_values)

    if maximum - minimum <= 0:
        return [1.0] * len(raw_values)

    if benefit:
        return [
            (value - minimum) / (maximum - minimum)
            for value in raw_values
        ]

    return [
        (maximum - value) / (maximum - minimum)
        for value in raw_values
    ]


def score_scenarios(
    candidates: Iterable[ScenarioMetrics],
    weights: Optional[Weights] = None,
) -> list[ScoredScenario]:
    """
    Normalize all criteria and compute the weighted MCDA composite score.

    Returns scenarios in input order. It does not sort them.
    """

    metrics_list = list(candidates)

    if not metrics_list:
        raise ValueError(
            "MCDA requires at least one scenario."
        )

    seen: set[str] = set()

    for metrics in metrics_list:
        if metrics.scenario_id in seen:
            raise ValueError(
                f"Duplicate scenario_id '{metrics.scenario_id}'."
            )

        seen.add(metrics.scenario_id)

    resolved_weights = weights or default_weights()

    raw_by_criterion = {
        criterion: [
            _resolve_all_criteria(metrics)[criterion]
            for metrics in metrics_list
        ]
        for criterion in CRITERIA
    }

    normalized_by_criterion = {
        criterion: _normalize(
            raw_by_criterion[criterion],
            benefit=CRITERION_IS_BENEFIT[criterion],
        )
        for criterion in CRITERIA
    }

    scored: list[ScoredScenario] = []

    for index, metrics in enumerate(metrics_list):
        criterion_scores = {
            criterion: round(
                normalized_by_criterion[criterion][index],
                6,
            )
            for criterion in CRITERIA
        }

        composite = sum(
            getattr(resolved_weights, criterion)
            * criterion_scores[criterion]
            for criterion in CRITERIA
        )

        # Compatibility objective scores:
        # technical / financial / resource / policy / risk etc. now exist
        # in criterion_scores, while these three remain available to older
        # consumers.
        objective_scores = {
            "cost": criterion_scores[CRITERION_FINANCIAL],
            "emissions": criterion_scores[CRITERION_CARBON_REDUCTION],
            "risk": criterion_scores[CRITERION_RISK],
        }

        raw_cost = lifecycle_cost(metrics)

        raw_emissions = raw_emissions_metric(metrics)

        raw_risk = raw_risk_metric(metrics)

        scored.append(
            ScoredScenario(
                scenario_id=metrics.scenario_id,
                technology_sequence=list(
                    metrics.technology_sequence
                ),
                raw_cost=raw_cost,
                raw_emissions=raw_emissions,
                raw_risk=raw_risk,
                criterion_raw_values=dict(
                    raw_by_criterion[criterion][index]
                    for criterion in CRITERIA
                ),
                criterion_scores=criterion_scores,
                objective_scores=objective_scores,
                composite_score=round(composite, 6),
                metrics=metrics,
            )
        )

    return scored

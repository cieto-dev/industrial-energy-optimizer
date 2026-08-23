
from __future__ import annotations

from dataclasses import dataclass, field
from functools import lru_cache
from typing import Any, Iterable, Optional

import numpy as np

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


COST_HORIZON_YEARS = 10.0


@dataclass
class ScenarioMetrics:
    scenario_id: str
    technology_sequence: list[str] = field(default_factory=list)

    capex_inr: Optional[float] = None
    annual_opex_inr: Optional[float] = None
    pathway_co2_tonnes_year: Optional[float] = None
    co2_reduction_pct: Optional[float] = None
    spread_ratio: Optional[float] = None
    risk_tier: Optional[str] = None
    reliability_score_pct: Optional[float] = None

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

    financial: Any = None
    emission: Any = None
    risk_score: Any = None

    extra: dict[str, Any] = field(default_factory=dict)


@dataclass
class ScoredScenario:
    scenario_id: str
    technology_sequence: list[str]

    raw_cost: float
    raw_emissions: float
    raw_risk: float

    criterion_raw_values: dict[str, float]
    criterion_scores: dict[str, float]
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

    if not 0.0 <= value <= 100.0:
        raise ValueError(
            f"Scenario '{scenario_id}' criterion "
            f"'{criterion}' must be between 0 and 100, "
            f"got {value}."
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


@lru_cache(maxsize=4096)
def _lifecycle_cost_cached(
    capex: float,
    annual_opex: float,
) -> float:
    return (
        capex
        + annual_opex * COST_HORIZON_YEARS
    )


def lifecycle_cost(metrics: ScenarioMetrics) -> float:
    return _lifecycle_cost_cached(
        _resolve_capex(metrics),
        _resolve_opex(metrics),
    )


def raw_emissions_metric(metrics: ScenarioMetrics) -> float:
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
            f"Scenario '{metrics.scenario_id}' "
            "is missing emissions."
        )

    return max(
        0.0,
        100.0 - reduction,
    )


def raw_risk_metric(metrics: ScenarioMetrics) -> float:

    if metrics.risk_score_value is not None:
        return _clamp_score(
            float(metrics.risk_score_value),
            criterion=CRITERION_RISK,
            scenario_id=metrics.scenario_id,
        )

    spread = metrics.spread_ratio

    if spread is None:
        spread = _attr(
            metrics.risk_score,
            "spread_ratio",
        )

    if spread is not None:
        if spread < 0:
            raise ValueError(
                f"Scenario '{metrics.scenario_id}' "
                "spread_ratio cannot be negative."
            )

        return spread

    tier = metrics.risk_tier

    if tier is None:
        tier = _str_attr(
            metrics.risk_score,
            "overall_tier",
        )

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
                f"Scenario '{metrics.scenario_id}' "
                f"has unknown risk tier '{tier}'."
            )

        return values[key]

    reliability = metrics.reliability_score_pct

    if reliability is None:
        reliability = _attr(
            metrics.risk_score,
            "reliability_score_pct",
        )

    if reliability is not None:
        return max(
            0.0,
            100.0 - reliability,
        )

    raise ValueError(
        f"Scenario '{metrics.scenario_id}' "
        "is missing risk information."
    )


def _resolve_criterion(
    metrics: ScenarioMetrics,
    criterion: str,
) -> Optional[float]:

    direct_map = {
        CRITERION_TECHNICAL: metrics.technical_score,
        CRITERION_FINANCIAL: metrics.financial_score,
        CRITERION_RESOURCE: metrics.resource_score,
        CRITERION_POLICY: metrics.policy_score,
        CRITERION_RISK: metrics.risk_score_value,
        CRITERION_TECHNOLOGY_MATURITY: metrics.technology_maturity,
        CRITERION_IMPLEMENTATION_COMPLEXITY:
            metrics.implementation_complexity,
        CRITERION_SUPPLY_RELIABILITY:
            metrics.supply_reliability,
        CRITERION_ELECTRICITY_DEPENDENCE:
            metrics.electricity_dependence,
        CRITERION_BIOMASS_DEPENDENCE:
            metrics.biomass_dependence,
        CRITERION_CARBON_REDUCTION:
            metrics.carbon_reduction,
        CRITERION_CONFIDENCE:
            metrics.confidence_score,
    }

    direct = direct_map.get(criterion)

    if direct is not None:
        return _clamp_score(
            float(direct),
            criterion=criterion,
            scenario_id=metrics.scenario_id,
        )

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

    aliases = alias_map.get(
        criterion,
        (),
    )

    sources = (
        metrics.financial,
        metrics.emission,
        metrics.risk_score,
        metrics.extra,
    )

    for source in sources:
        value = _attr(
            source,
            *aliases,
        )

        if value is not None:
            return _clamp_score(
                value,
                criterion=criterion,
                scenario_id=metrics.scenario_id,
            )

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


def _default_from_legacy(
    metrics: ScenarioMetrics,
    criterion: str,
) -> float:

    if criterion == CRITERION_FINANCIAL:
        cost = lifecycle_cost(metrics)

        return (
            1.0
            / (1.0 + cost / 1_000_000.0)
            * 100.0
        )

    if criterion == CRITERION_TECHNICAL:
        return 100.0

    if criterion in {
        CRITERION_RESOURCE,
        CRITERION_POLICY,
        CRITERION_TECHNOLOGY_MATURITY,
        CRITERION_IMPLEMENTATION_COMPLEXITY,
        CRITERION_ELECTRICITY_DEPENDENCE,
        CRITERION_BIOMASS_DEPENDENCE,
        CRITERION_CONFIDENCE,
    }:
        return 50.0

    raise ValueError(
        f"Scenario '{metrics.scenario_id}' is missing "
        f"criterion '{criterion}'."
    )


def _resolve_all_criteria(
    metrics: ScenarioMetrics,
) -> dict[str, float]:
    """
    Resolve every criterion exactly once per scenario.
    """
    return {
        criterion: float(
            _resolve_criterion(
                metrics,
                criterion,
            )
            if _resolve_criterion(
                metrics,
                criterion,
            ) is not None
            else _default_from_legacy(
                metrics,
                criterion,
            )
        )
        for criterion in CRITERIA
    }


def _criteria_matrix(
    metrics_list: list[ScenarioMetrics],
) -> np.ndarray:
    """
    Build an N x 12 NumPy matrix.

    Critical optimization:
    each scenario is resolved once, rather than once per criterion.
    """
    rows = []

    for metrics in metrics_list:
        row = []

        for criterion in CRITERIA:
            value = _resolve_criterion(
                metrics,
                criterion,
            )

            if value is None:
                value = _default_from_legacy(
                    metrics,
                    criterion,
                )

            row.append(float(value))

        rows.append(row)

    return np.asarray(
        rows,
        dtype=np.float64,
    )


def _vectorized_normalize(
    values: np.ndarray,
    benefit_mask: np.ndarray,
) -> np.ndarray:
    """
    Vectorized min-max normalization.

    values shape = [n_scenarios, n_criteria]
    """
    minimum = values.min(axis=0)
    maximum = values.max(axis=0)

    spread = maximum - minimum

    normalized = np.ones_like(
        values,
        dtype=np.float64,
    )

    variable = spread > 0

    if np.any(variable):
        benefit_values = (
            values[:, variable]
            - minimum[variable]
        ) / spread[variable]

        cost_values = (
            maximum[variable]
            - values[:, variable]
        ) / spread[variable]

        normalized[:, variable] = np.where(
            benefit_mask[variable],
            benefit_values,
            cost_values,
        )

    return normalized


@lru_cache(maxsize=8)
def _benefit_mask() -> np.ndarray:
    return np.asarray(
        [
            bool(
                CRITERION_IS_BENEFIT[
                    criterion
                ]
            )
            for criterion in CRITERIA
        ],
        dtype=bool,
    )


def score_scenarios(
    candidates: Iterable[ScenarioMetrics],
    weights: Optional[Weights] = None,
) -> list[ScoredScenario]:

    metrics_list = list(candidates)

    if not metrics_list:
        raise ValueError(
            "MCDA requires at least one scenario."
        )

    scenario_ids = [
        metrics.scenario_id
        for metrics in metrics_list
    ]

    if len(scenario_ids) != len(set(scenario_ids)):
        raise ValueError(
            "Duplicate scenario_id detected."
        )

    resolved_weights = (
        weights
        or default_weights()
    )

    matrix = _criteria_matrix(
        metrics_list
    )

    normalized = _vectorized_normalize(
        matrix,
        _benefit_mask(),
    )

    weight_vector = np.asarray(
        [
            getattr(
                resolved_weights,
                criterion,
            )
            for criterion in CRITERIA
        ],
        dtype=np.float64,
    )

    composite_scores = normalized @ weight_vector

    scored: list[ScoredScenario] = []

    for index, metrics in enumerate(
        metrics_list
    ):
        criterion_raw_values = {
            criterion: float(
                matrix[index, column]
            )
            for column, criterion
            in enumerate(CRITERIA)
        }

        criterion_scores = {
            criterion: round(
                float(
                    normalized[
                        index,
                        column,
                    ]
                ),
                6,
            )
            for column, criterion
            in enumerate(CRITERIA)
        }

        objective_scores = {
            "cost": criterion_scores[
                CRITERION_FINANCIAL
            ],
            "emissions": criterion_scores[
                CRITERION_CARBON_REDUCTION
            ],
            "risk": criterion_scores[
                CRITERION_RISK
            ],
        }

        scored.append(
            ScoredScenario(
                scenario_id=metrics.scenario_id,
                technology_sequence=list(
                    metrics.technology_sequence
                ),
                raw_cost=lifecycle_cost(
                    metrics
                ),
                raw_emissions=raw_emissions_metric(
                    metrics
                ),
                raw_risk=raw_risk_metric(
                    metrics
                ),
                criterion_raw_values=criterion_raw_values,
                criterion_scores=criterion_scores,
                objective_scores=objective_scores,
                composite_score=round(
                    float(
                        composite_scores[index]
                    ),
                    6,
                ),
                metrics=metrics,
            )
        )

    return scored


def clear_mcda_cache() -> None:
    """
    Clear function-level memoization.

    Useful in tests or when a runtime configuration changes.
    """
    _lifecycle_cost_cached.cache_clear()
    _benefit_mask.cache_clear()

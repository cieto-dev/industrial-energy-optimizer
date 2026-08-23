
from __future__ import annotations

from dataclasses import dataclass, field
from functools import lru_cache
from typing import Any, Iterable, Mapping, Optional, Union

from decision_engine.optimizer.mcda import (
    COST_HORIZON_YEARS,
    ScenarioMetrics,
    ScoredScenario,
    clear_mcda_cache,
    lifecycle_cost,
    score_scenarios,
)
from decision_engine.optimizer.ranking import (
    RankedScenario,
    rank_scenarios,
)
from decision_engine.optimizer.weights import (
    Weights,
    default_weights,
)


@dataclass
class OptimizationResult:
    recommended_scenario_id: str
    cheapest_scenario_id: str
    recommended_is_cheapest: bool
    weights_used: dict[str, float]
    ranked_scenarios: list[RankedScenario]
    why_not_always_cheapest: str
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "recommended_scenario_id":
                self.recommended_scenario_id,
            "cheapest_scenario_id":
                self.cheapest_scenario_id,
            "recommended_is_cheapest":
                self.recommended_is_cheapest,
            "weights_used":
                dict(self.weights_used),
            "why_not_always_cheapest":
                self.why_not_always_cheapest,
            "notes":
                list(self.notes),
            "ranked_scenarios": [
                {
                    "rank": row.rank,
                    "scenario_id": row.scenario_id,
                    "technology_sequence":
                        row.technology_sequence,
                    "composite_score":
                        row.composite_score,
                    "objective_scores":
                        dict(row.objective_scores),
                    "criterion_scores":
                        dict(row.criterion_scores),
                    "raw_cost":
                        row.raw_cost,
                    "raw_emissions":
                        row.raw_emissions,
                    "raw_risk":
                        row.raw_risk,
                    "is_cheapest":
                        row.is_cheapest,
                    "is_recommended":
                        row.is_recommended,
                    "rank_reason":
                        row.rank_reason,
                }
                for row in self.ranked_scenarios
            ],
        }


def _as_metrics(
    item: Union[
        ScenarioMetrics,
        Mapping[str, Any],
    ],
) -> ScenarioMetrics:

    if isinstance(
        item,
        ScenarioMetrics,
    ):
        return item

    data = dict(item)

    sequence = (
        data.get("technology_sequence")
        or data.get("technologies")
        or []
    )

    if isinstance(
        sequence,
        str,
    ):
        sequence = [sequence]

    known_fields = {
        "scenario_id",
        "technology_sequence",
        "technologies",
        "capex_inr",
        "annual_opex_inr",
        "pathway_co2_tonnes_year",
        "co2_reduction_pct",
        "spread_ratio",
        "risk_tier",
        "reliability_score_pct",
        "technical_score",
        "financial_score",
        "resource_score",
        "policy_score",
        "risk_score_value",
        "technology_maturity",
        "implementation_complexity",
        "supply_reliability",
        "electricity_dependence",
        "biomass_dependence",
        "carbon_reduction",
        "confidence_score",
        "financial",
        "emission",
        "risk_score",
    }

    return ScenarioMetrics(
        scenario_id=str(
            data["scenario_id"]
        ),
        technology_sequence=list(sequence),
        capex_inr=data.get(
            "capex_inr"
        ),
        annual_opex_inr=data.get(
            "annual_opex_inr"
        ),
        pathway_co2_tonnes_year=data.get(
            "pathway_co2_tonnes_year"
        ),
        co2_reduction_pct=data.get(
            "co2_reduction_pct"
        ),
        spread_ratio=data.get(
            "spread_ratio"
        ),
        risk_tier=data.get(
            "risk_tier"
        ),
        reliability_score_pct=data.get(
            "reliability_score_pct"
        ),
        technical_score=data.get(
            "technical_score"
        ),
        financial_score=data.get(
            "financial_score"
        ),
        resource_score=data.get(
            "resource_score"
        ),
        policy_score=data.get(
            "policy_score"
        ),
        risk_score_value=(
            data.get("risk_score_value")
            if data.get("risk_score_value")
            is not None
            else (
                data.get("risk_score")
                if isinstance(
                    data.get("risk_score"),
                    (int, float),
                )
                else None
            )
        ),
        technology_maturity=data.get(
            "technology_maturity"
        ),
        implementation_complexity=data.get(
            "implementation_complexity"
        ),
        supply_reliability=data.get(
            "supply_reliability"
        ),
        electricity_dependence=data.get(
            "electricity_dependence"
        ),
        biomass_dependence=data.get(
            "biomass_dependence"
        ),
        carbon_reduction=data.get(
            "carbon_reduction"
        ),
        confidence_score=data.get(
            "confidence_score"
        ),
        financial=data.get(
            "financial"
        ),
        emission=data.get(
            "emission"
        ),
        risk_score=(
            data.get("risk_score")
            if not isinstance(
                data.get("risk_score"),
                (int, float),
            )
            else None
        ),
        extra={
            key: value
            for key, value in data.items()
            if key not in known_fields
        },
    )


def _weights_from_input(
    weights: Optional[
        Union[
            Weights,
            Mapping[str, float],
        ]
    ],
) -> Weights:

    if weights is None:
        return default_weights()

    if isinstance(
        weights,
        Weights,
    ):
        return weights

    return Weights.from_mapping(
        weights
    )


def _metrics_cache_key(
    metrics: list[ScenarioMetrics],
    weights: Weights,
) -> tuple[Any, ...]:

    scenario_signature = []

    for metric in metrics:
        scenario_signature.append(
            (
                metric.scenario_id,
                tuple(
                    metric.technology_sequence
                ),
                metric.capex_inr,
                metric.annual_opex_inr,
                metric.pathway_co2_tonnes_year,
                metric.co2_reduction_pct,
                metric.spread_ratio,
                metric.risk_tier,
                metric.reliability_score_pct,
                metric.technical_score,
                metric.financial_score,
                metric.resource_score,
                metric.policy_score,
                metric.risk_score_value,
                metric.technology_maturity,
                metric.implementation_complexity,
                metric.supply_reliability,
                metric.electricity_dependence,
                metric.biomass_dependence,
                metric.carbon_reduction,
                metric.confidence_score,
            )
        )

    return (
        tuple(scenario_signature),
        tuple(
            weights.as_dict().items()
        ),
    )


@lru_cache(maxsize=256)
def _score_cached(
    cache_key: tuple[Any, ...],
) -> tuple[ScoredScenario, ...]:
    """
    Request-level memoization.

    The actual ScenarioMetrics objects are reconstructed from the cache key.
    """
    scenario_rows = cache_key[0]
    weights_items = cache_key[1]

    metrics: list[ScenarioMetrics] = []

    for row in scenario_rows:
        (
            scenario_id,
            technology_sequence,
            capex_inr,
            annual_opex_inr,
            pathway_co2_tonnes_year,
            co2_reduction_pct,
            spread_ratio,
            risk_tier,
            reliability_score_pct,
            technical_score,
            financial_score,
            resource_score,
            policy_score,
            risk_score_value,
            technology_maturity,
            implementation_complexity,
            supply_reliability,
            electricity_dependence,
            biomass_dependence,
            carbon_reduction,
            confidence_score,
        ) = row

        metrics.append(
            ScenarioMetrics(
                scenario_id=scenario_id,
                technology_sequence=list(
                    technology_sequence
                ),
                capex_inr=capex_inr,
                annual_opex_inr=annual_opex_inr,
                pathway_co2_tonnes_year=(
                    pathway_co2_tonnes_year
                ),
                co2_reduction_pct=(
                    co2_reduction_pct
                ),
                spread_ratio=spread_ratio,
                risk_tier=risk_tier,
                reliability_score_pct=(
                    reliability_score_pct
                ),
                technical_score=technical_score,
                financial_score=financial_score,
                resource_score=resource_score,
                policy_score=policy_score,
                risk_score_value=risk_score_value,
                technology_maturity=(
                    technology_maturity
                ),
                implementation_complexity=(
                    implementation_complexity
                ),
                supply_reliability=(
                    supply_reliability
                ),
                electricity_dependence=(
                    electricity_dependence
                ),
                biomass_dependence=(
                    biomass_dependence
                ),
                carbon_reduction=(
                    carbon_reduction
                ),
                confidence_score=confidence_score,
            )
        )

    weights = Weights.from_mapping(
        dict(weights_items)
    )

    return tuple(
        score_scenarios(
            metrics,
            weights,
        )
    )


def _cheapest_explanation(
    recommended: RankedScenario,
    cheapest: RankedScenario,
    weights: Weights,
) -> str:

    if (
        recommended.scenario_id
        == cheapest.scenario_id
    ):
        return (
            "Under these inputs the recommended "
            "scenario is also the cheapest. "
            "That is allowed, but not required: "
            f"the financial weight is "
            f"{weights.financial:.0%}, not 100%. "
            "Re-rank with higher carbon or risk "
            "weight to confirm the engine can select "
            "a more expensive pathway."
        )

    return (
        f"Recommended '{recommended.scenario_id}' "
        "is not the cheapest "
        f"(cheapest is '{cheapest.scenario_id}', "
        f"lifecycle cost "
        f"{cheapest.raw_cost:.0f} INR vs "
        f"{recommended.raw_cost:.0f} INR). "
        f"{recommended.rank_reason}"
    )


def optimize(
    candidates: Iterable[
        Union[
            ScenarioMetrics,
            Mapping[str, Any],
        ]
    ],
    weights: Optional[
        Union[
            Weights,
            Mapping[str, float],
        ]
    ] = None,
) -> OptimizationResult:

    metrics = [
        _as_metrics(item)
        for item in candidates
    ]

    if len(metrics) < 2:
        raise ValueError(
            "Optimizer requires at least two "
            "candidate scenarios to rank."
        )

    resolved_weights = _weights_from_input(
        weights
    )

    cache_key = _metrics_cache_key(
        metrics,
        resolved_weights,
    )

    scored = list(
        _score_cached(
            cache_key
        )
    )

    ranked = rank_scenarios(
        scored
    )

    recommended = ranked[0]

    cheapest = next(
        row
        for row in ranked
        if row.is_cheapest
    )

    notes = [
        "Dataset lookups use lazy indexes and cache-backed reads.",
        "MCDA criterion resolution is performed once per scenario.",
        "MCDA normalization is vectorized with NumPy.",
        "Repeated identical optimization requests use memoization.",
        (
            f"Lifecycle cost = CAPEX + annual OPEX × "
            f"{COST_HORIZON_YEARS:.0f} years."
        ),
        (
            "criterion_scores are min-max benefit scores "
            "in [0, 1] for the 12 MCDA criteria."
        ),
        (
            "Composite score is a weighted sum; it is "
            "not a least-cost sort."
        ),
    ]

    return OptimizationResult(
        recommended_scenario_id=(
            recommended.scenario_id
        ),
        cheapest_scenario_id=(
            cheapest.scenario_id
        ),
        recommended_is_cheapest=(
            recommended.scenario_id
            == cheapest.scenario_id
        ),
        weights_used=resolved_weights.as_dict(),
        ranked_scenarios=ranked,
        why_not_always_cheapest=_cheapest_explanation(
            recommended,
            cheapest,
            resolved_weights,
        ),
        notes=notes,
    )


def cheapest_by_lifecycle(
    candidates: Iterable[
        Union[
            ScenarioMetrics,
            Mapping[str, Any],
        ]
    ],
) -> str:

    metrics = [
        _as_metrics(item)
        for item in candidates
    ]

    winner = min(
        metrics,
        key=lambda metric: (
            lifecycle_cost(metric),
            metric.scenario_id,
        ),
    )

    return winner.scenario_id


def clear_optimizer_cache() -> None:
    """
    Clear all optimizer memoization caches.
    """
    _score_cached.cache_clear()
    clear_mcda_cache()

"""
optimization_engine.py — Orchestrator for Unit 2.9 / Sprint 3.2 Optimizer / MCDA.

Purpose
-------
Coordinate weights → MCDA scoring → ranking. This file does not implement
normalisation or sort logic itself, so a later solver (PuLP / OR-Tools)
can replace mcda.py without changing callers.

Contract (docs/DECISION_ENGINE_ARCHITECTURE.md)
-----------------------------------------------
Input:  candidate scenarios already scored by economics/, emissions/,
        reliability/, biomass/, policy/ etc.
Output: ranked list with DOMAIN_MODEL objective_scores {cost, emissions, risk}
        plus the full 12-criterion scores and a recommended scenario_id.

Critical
--------
Ranking must NOT always pick the cheapest scenario. The engine records
an explicit explanation when the winner is not least-cost.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable, Mapping, Optional, Union

from decision_engine.optimizer.mcda import (
    COST_HORIZON_YEARS,
    ScenarioMetrics,
    ScoredScenario,
    lifecycle_cost,
    score_scenarios,
)
from decision_engine.optimizer.ranking import RankedScenario, rank_scenarios
from decision_engine.optimizer.weights import Weights, default_weights


@dataclass
class OptimizationResult:
    """Full optimizer output for one factory's candidate set."""

    recommended_scenario_id: str
    cheapest_scenario_id: str
    recommended_is_cheapest: bool
    weights_used: dict[str, float]
    ranked_scenarios: list[RankedScenario]
    why_not_always_cheapest: str
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "recommended_scenario_id": self.recommended_scenario_id,
            "cheapest_scenario_id": self.cheapest_scenario_id,
            "recommended_is_cheapest": self.recommended_is_cheapest,
            "weights_used": dict(self.weights_used),
            "why_not_always_cheapest": self.why_not_always_cheapest,
            "notes": list(self.notes),
            "ranked_scenarios": [
                {
                    "rank": row.rank,
                    "scenario_id": row.scenario_id,
                    "technology_sequence": row.technology_sequence,
                    "composite_score": row.composite_score,
                    "objective_scores": dict(row.objective_scores),
                    "criterion_scores": dict(row.criterion_scores),
                    "raw_cost": row.raw_cost,
                    "raw_emissions": row.raw_emissions,
                    "raw_risk": row.raw_risk,
                    "is_cheapest": row.is_cheapest,
                    "is_recommended": row.is_recommended,
                    "rank_reason": row.rank_reason,
                }
                for row in self.ranked_scenarios
            ],
        }


def _as_metrics(item: Union[ScenarioMetrics, Mapping[str, Any]]) -> ScenarioMetrics:
    if isinstance(item, ScenarioMetrics):
        return item

    data = dict(item)
    sequence = data.get("technology_sequence") or data.get("technologies") or []
    if isinstance(sequence, str):
        sequence = [sequence]

    return ScenarioMetrics(
        scenario_id=str(data["scenario_id"]),
        technology_sequence=list(sequence),
        capex_inr=data.get("capex_inr"),
        annual_opex_inr=data.get("annual_opex_inr"),
        pathway_co2_tonnes_year=data.get("pathway_co2_tonnes_year"),
        co2_reduction_pct=data.get("co2_reduction_pct"),
        spread_ratio=data.get("spread_ratio"),
        risk_tier=data.get("risk_tier"),
        reliability_score_pct=data.get("reliability_score_pct"),
        technical_score=data.get("technical_score"),
        financial_score=data.get("financial_score"),
        resource_score=data.get("resource_score"),
        policy_score=data.get("policy_score"),
        risk_score_value=data.get("risk_score_value") or data.get("risk_score"),
        technology_maturity=data.get("technology_maturity"),
        implementation_complexity=data.get("implementation_complexity"),
        supply_reliability=data.get("supply_reliability"),
        electricity_dependence=data.get("electricity_dependence"),
        biomass_dependence=data.get("biomass_dependence"),
        carbon_reduction=data.get("carbon_reduction"),
        confidence_score=data.get("confidence_score"),
        financial=data.get("financial"),
        emission=data.get("emission"),
        risk_score=data.get("risk_score"),
        extra={
            key: value
            for key, value in data.items()
            if key
            not in {
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
        },
    )


def _cheapest_explanation(
    recommended: RankedScenario,
    cheapest: RankedScenario,
    weights: Weights,
) -> str:
    if recommended.scenario_id == cheapest.scenario_id:
        return (
            "Under these inputs the recommended scenario is also the cheapest. "
            "That is allowed, but not required: the financial weight is "
            f"{weights.financial:.0%}, not 100%. Re-rank with higher carbon "
            "or risk weight to confirm the engine can select a more expensive "
            "pathway."
        )
    return (
        f"Recommended '{recommended.scenario_id}' is not the cheapest "
        f"(cheapest is '{cheapest.scenario_id}', lifecycle cost "
        f"{cheapest.raw_cost:.0f} INR vs {recommended.raw_cost:.0f} INR). "
        f"{recommended.rank_reason}"
    )


def optimize(
    candidates: Iterable[Union[ScenarioMetrics, Mapping[str, Any]]],
    weights: Optional[Union[Weights, Mapping[str, float]]] = None,
) -> OptimizationResult:
    """
    Rank candidate pathways and return the recommended scenario.

    Parameters
    ----------
    candidates
        Iterable of ScenarioMetrics or dicts with at least scenario_id,
        cost (capex_inr / financial), emissions, and risk fields.
        New 12-criterion fields are optional and fall back gracefully.
    weights
        Weights instance, mapping override, or None for the documented default.
    """
    metrics = [_as_metrics(item) for item in candidates]
    if len(metrics) < 2:
        raise ValueError(
            "Optimizer requires at least two candidate scenarios to rank."
        )

    if weights is None:
        resolved_weights = default_weights()
    elif isinstance(weights, Weights):
        resolved_weights = weights
    else:
        resolved_weights = Weights.from_mapping(weights)

    scored: list[ScoredScenario] = score_scenarios(metrics, resolved_weights)
    ranked = rank_scenarios(scored)

    recommended = ranked[0]
    cheapest = next(row for row in ranked if row.is_cheapest)

    notes = [
        f"Lifecycle cost = CAPEX + annual OPEX × {COST_HORIZON_YEARS:.0f} years.",
        "criterion_scores are min-max benefit scores in [0, 1] "
        "(higher is better) for all 12 research criteria.",
        "objective_scores keep the legacy {cost, emissions, risk} contract.",
        "Composite score is a weighted sum; it is not a least-cost sort.",
    ]

    return OptimizationResult(
        recommended_scenario_id=recommended.scenario_id,
        cheapest_scenario_id=cheapest.scenario_id,
        recommended_is_cheapest=(
            recommended.scenario_id == cheapest.scenario_id
        ),
        weights_used=resolved_weights.as_dict(),
        ranked_scenarios=ranked,
        why_not_always_cheapest=_cheapest_explanation(
            recommended, cheapest, resolved_weights
        ),
        notes=notes,
    )


def cheapest_by_lifecycle(
    candidates: Iterable[Union[ScenarioMetrics, Mapping[str, Any]]],
) -> str:
    """Least-cost scenario id (for tests comparing MCDA vs cheapest)."""
    metrics = [_as_metrics(item) for item in candidates]
    winner = min(metrics, key=lambda m: (lifecycle_cost(m), m.scenario_id))
    return winner.scenario_id
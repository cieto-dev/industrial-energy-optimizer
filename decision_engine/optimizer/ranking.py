"""
ranking.py — Sort MCDA-scored scenarios and attach rank + explainability.

Purpose
-------
Produce the ranked scenario list required by ROADMAP Sprint 3.2 / Unit 2.9.
Does not compute scores (mcda.py) and does not load weights (weights.py).

Sort order
----------
1. composite_score descending (higher MCDA score wins)
2. objective_scores["risk"] descending (prefer lower operational risk)
3. objective_scores["emissions"] descending
4. raw_cost ascending (cheapest last-resort tie-break, never the primary key)

Explainability
--------------
Each ranked row records whether it is the cheapest by lifecycle cost
and a short reason string the reports module can later expand.
"""

from __future__ import annotations

from dataclasses import dataclass

from decision_engine.optimizer.mcda import ScoredScenario
from decision_engine.optimizer.weights import (
    CRITERION_COST,
    CRITERION_EMISSIONS,
    CRITERION_RISK,
)


@dataclass
class RankedScenario:
    """One scenario in ranked order (rank 1 = recommended)."""

    rank: int
    scenario_id: str
    technology_sequence: list[str]
    composite_score: float
    objective_scores: dict[str, float]
    criterion_scores: dict[str, float]
    raw_cost: float
    raw_emissions: float
    raw_risk: float
    is_cheapest: bool
    is_recommended: bool
    rank_reason: str
    scored: ScoredScenario


def _rank_reason(
    item: ScoredScenario,
    cheapest_id: str,
    recommended_id: str,
) -> str:
    scores = item.objective_scores
    if item.scenario_id == recommended_id and item.scenario_id != cheapest_id:
        return (
            f"Ranked above the cheapest option because emissions score "
            f"{scores.get(CRITERION_EMISSIONS, scores.get('emissions', 0)):.2f} "
            f"and risk score "
            f"{scores.get(CRITERION_RISK, scores.get('risk', 0)):.2f} "
            f"outweigh its cost score "
            f"{scores.get(CRITERION_COST, scores.get('cost', 0)):.2f} "
            f"under the configured MCDA weights."
        )
    if item.scenario_id == recommended_id and item.scenario_id == cheapest_id:
        return (
            f"Highest composite MCDA score "
            f"({item.composite_score:.3f}); also the lowest lifecycle cost."
        )
    if item.scenario_id == cheapest_id:
        return (
            f"Lowest lifecycle cost, but composite score "
            f"{item.composite_score:.3f} is below the recommended scenario "
            f"because cost is only one of the MCDA criteria."
        )
    return (
        f"Composite MCDA score {item.composite_score:.3f} "
        f"(cost={scores.get(CRITERION_COST, scores.get('cost', 0)):.2f}, "
        f"emissions={scores.get(CRITERION_EMISSIONS, scores.get('emissions', 0)):.2f}, "
        f"risk={scores.get(CRITERION_RISK, scores.get('risk', 0)):.2f})."
    )


def rank_scenarios(scored: list[ScoredScenario]) -> list[RankedScenario]:
    """
    Return scenarios sorted best-first with 1-based ranks.

    Raises ValueError if the list is empty.
    """
    if not scored:
        raise ValueError("Cannot rank an empty scenario list.")

    cheapest_id = min(
        scored, key=lambda s: (s.raw_cost, s.scenario_id)
    ).scenario_id

    ordered = sorted(
        scored,
        key=lambda s: (
            -s.composite_score,
            -s.objective_scores.get(CRITERION_RISK, s.objective_scores.get("risk", 0)),
            -s.objective_scores.get(
                CRITERION_EMISSIONS, s.objective_scores.get("emissions", 0)
            ),
            s.raw_cost,
            s.scenario_id,
        ),
    )
    recommended_id = ordered[0].scenario_id

    ranked: list[RankedScenario] = []
    for index, item in enumerate(ordered, start=1):
        ranked.append(
            RankedScenario(
                rank=index,
                scenario_id=item.scenario_id,
                technology_sequence=list(item.technology_sequence),
                composite_score=item.composite_score,
                objective_scores=dict(item.objective_scores),
                criterion_scores=dict(item.criterion_scores),
                raw_cost=item.raw_cost,
                raw_emissions=item.raw_emissions,
                raw_risk=item.raw_risk,
                is_cheapest=(item.scenario_id == cheapest_id),
                is_recommended=(index == 1),
                rank_reason=_rank_reason(item, cheapest_id, recommended_id),
                scored=item,
            )
        )
    return ranked
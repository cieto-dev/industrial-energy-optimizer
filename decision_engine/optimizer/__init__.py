"""
optimizer package — MCDA ranking of scored energy-transition scenarios.

Public API
----------
optimize()           orchestrator (weights → mcda → ranking)
default_weights()    documented default cost / emissions / risk weights
ScenarioMetrics      input contract for one candidate pathway
OptimizationResult   ranked output with explainability
"""

from decision_engine.optimizer.mcda import ScenarioMetrics, ScoredScenario
from decision_engine.optimizer.optimization_engine import (
    OptimizationResult,
    optimize,
)
from decision_engine.optimizer.ranking import RankedScenario, rank_scenarios
from decision_engine.optimizer.weights import Weights, default_weights

__all__ = [
    "OptimizationResult",
    "RankedScenario",
    "ScenarioMetrics",
    "ScoredScenario",
    "Weights",
    "default_weights",
    "optimize",
    "rank_scenarios",
]

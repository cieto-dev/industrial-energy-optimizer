"""
Constraint Policy Filter
========================

Stub implementation. Evaluates pathway feasibility against technology rules
and industry constraints. Currently passes all pathways through as feasible
(no-block default), logging the constraint inputs for traceability.

Replace the body of ``evaluate_pathway`` with real logic when the
constraint knowledge base is ready.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class PathwayEvaluation:
    """Result of evaluating one pathway against constraints."""

    feasible: bool
    pathway: dict[str, Any]
    rejection_reasons: list[str] = field(default_factory=list)


class ConstraintPolicyFilter:
    """
    Evaluates candidate pathways against technology rules and industry
    constraints loaded from the knowledge base.

    This stub always returns feasible=True.  Wire in real constraint logic
    once the constraint_policy knowledge base is populated.
    """

    def __init__(
        self,
        technology_rules: Any = None,
        industry_constraints: Any = None,
    ) -> None:
        self._technology_rules = technology_rules or {}
        self._industry_constraints = industry_constraints or {}

    def evaluate_pathway(
        self,
        pathway: dict[str, Any],
        factory: Any = None,
    ) -> PathwayEvaluation:
        """
        Evaluate one pathway.

        Returns feasible=True in the stub. A real implementation would
        check capacity limits, land / roof constraints, fuel availability,
        regulatory bans, etc.
        """
        return PathwayEvaluation(
            feasible=True,
            pathway=pathway,
            rejection_reasons=[],
        )

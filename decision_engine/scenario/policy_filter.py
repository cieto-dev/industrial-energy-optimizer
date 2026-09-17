"""
Policy Scenario Filter
======================

Stub implementation. Evaluates whether candidate pathways are eligible under
central and state policies (e.g., MNRE incentives, state net-metering rules).

Currently passes all pathways through as feasible. Replace with real policy
logic once the policy eligibility knowledge base is populated.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class PathwayPolicyEvaluation:
    """Result of evaluating one pathway against policy rules."""

    feasible: bool
    pathway: dict[str, Any]
    rejection_reasons: list[str] = field(default_factory=list)
    eligible_incentives: list[str] = field(default_factory=list)


class PolicyScenarioFilter:
    """
    Evaluates candidate pathways against central and state policy rules.

    This stub always returns feasible=True. A real implementation would
    check MSME registration, technology eligibility under MNRE/SIDBI
    schemes, state-level incentive applicability, etc.
    """

    def __init__(
        self,
        central_policies: Any = None,
        state_policies: Any = None,
        eligibility_rules: Any = None,
    ) -> None:
        self._central_policies = central_policies or {}
        self._state_policies = state_policies or {}
        self._eligibility_rules = eligibility_rules or {}

    def evaluate_pathway(
        self,
        pathway: dict[str, Any],
        factory: Any = None,
    ) -> PathwayPolicyEvaluation:
        """
        Evaluate one pathway against policy rules.

        Returns feasible=True in the stub. A real implementation would
        check policy eligibility, incentive stacking, and registration
        requirements.
        """
        return PathwayPolicyEvaluation(
            feasible=True,
            pathway=pathway,
            rejection_reasons=[],
            eligible_incentives=[],
        )

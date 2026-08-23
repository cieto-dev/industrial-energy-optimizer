"""
Scenario filtering and hard feasibility gating.

Unit 2.8 — Part 3

Pipeline
--------
Candidate pathways
        |
        v
Basic scenario filter
        |
        v
Technical/resource constraint filter
        |
        v
Policy filter
        |
        v
ONLY feasible pathways
        |
        v
Biomass / tariff / finance / optimization

This module deliberately rejects infeasible pathways early.

It does NOT:
    - rank scenarios
    - calculate payback
    - calculate MCDA scores
    - choose the best scenario
    - invent feasibility
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping, Optional

from .constraint_policy_filter import (
    ConstraintPolicyFilter,
)
from .policy_filter import (
    PolicyScenarioFilter,
)


BASE_DIR = Path(__file__).resolve().parents[2]

TECHNOLOGY_RULES_FILE = (
    BASE_DIR
    / "knowledge-base"
    / "constraints"
    / "technology_rules.json"
)

INDUSTRY_CONSTRAINTS_FILE = (
    BASE_DIR
    / "knowledge-base"
    / "constraints"
    / "industry_constraints.json"
)

CENTRAL_POLICIES_FILE = (
    BASE_DIR
    / "knowledge-base"
    / "policies"
    / "central_policies.json"
)

STATE_POLICIES_FILE = (
    BASE_DIR
    / "knowledge-base"
    / "policies"
    / "state_policies.json"
)

ELIGIBILITY_RULES_FILE = (
    BASE_DIR
    / "knowledge-base"
    / "policies"
    / "eligibility_rules.json"
)


def _load_json(
    file_path: Path,
    *,
    required: bool = True,
) -> dict[str, Any]:

    if not file_path.exists():

        if required:
            raise FileNotFoundError(
                f"Knowledge-base file not found: "
                f"{file_path}"
            )

        return {}

    with file_path.open(
        "r",
        encoding="utf-8",
    ) as file:

        data = json.load(file)

    if not isinstance(data, dict):
        raise ValueError(
            f"Expected JSON object in {file_path}"
        )

    return data


def load_technology_rules() -> dict[str, dict[str, Any]]:
    """
    Load the canonical technology rule base.
    """

    data = _load_json(
        TECHNOLOGY_RULES_FILE
    )

    return {
        str(key): value
        for key, value in data.items()
        if isinstance(value, dict)
    }


def load_industry_constraints() -> dict[str, dict[str, Any]]:
    """
    Load industry-specific hard constraints when available.
    """

    data = _load_json(
        INDUSTRY_CONSTRAINTS_FILE,
        required=False,
    )

    if "industries" in data and isinstance(
        data["industries"],
        Mapping,
    ):
        data = data["industries"]

    return {
        str(key): value
        for key, value in data.items()
        if isinstance(value, dict)
    }


def load_policy_knowledge() -> dict[str, dict[str, Any]]:
    """
    Load policy knowledge-base objects.

    Missing policy files are tolerated because the repository can be
    technically usable before the policy KB is fully populated.
    """

    return {
        "central_policies": _load_json(
            CENTRAL_POLICIES_FILE,
            required=False,
        ),
        "state_policies": _load_json(
            STATE_POLICIES_FILE,
            required=False,
        ),
        "eligibility_rules": _load_json(
            ELIGIBILITY_RULES_FILE,
            required=False,
        ),
    }


def _technology_id(item: Any) -> str:

    if isinstance(item, str):
        value = item.strip()

        if value:
            return value

    if isinstance(item, Mapping):
        value = (
            item.get("technology_id")
            or item.get("id")
            or item.get("technology")
            or item.get("technology_name")
        )

        if isinstance(value, str):
            value = value.strip()

            if value:
                return value

    raise ValueError(
        f"Unable to determine technology ID from: "
        f"{item!r}"
    )


def extract_sequence(
    candidate: Any,
) -> list[str]:

    if not isinstance(candidate, Mapping):
        raise ValueError(
            "Scenario candidate must be a dictionary."
        )

    values = candidate.get(
        "technology_sequence"
    )

    if values is None:
        values = candidate.get(
            "technologies"
        )

    if values is None:
        raise ValueError(
            "Scenario candidate must contain "
            "'technology_sequence' or 'technologies'."
        )

    if not isinstance(
        values,
        (list, tuple),
    ):
        raise ValueError(
            "Technology sequence must be a list or tuple."
        )

    if not values:
        raise ValueError(
            "Technology sequence cannot be empty."
        )

    return [
        _technology_id(item)
        for item in values
    ]


def _normalise(
    value: Any,
) -> str:

    return (
        str(value)
        .strip()
        .lower()
        .replace("-", "_")
        .replace(" ", "_")
    )


def _deduplicate_candidates(
    candidates: list[dict[str, Any]],
) -> tuple[
    list[dict[str, Any]],
    list[dict[str, Any]],
]:
    """
    Remove structurally duplicate pathways before expensive checks.

    Returns:
        unique,
        duplicates
    """

    unique: list[dict[str, Any]] = []
    duplicates: list[dict[str, Any]] = []
    seen: set[tuple[str, ...]] = set()

    for candidate in candidates:

        try:
            sequence = extract_sequence(
                candidate
            )
        except ValueError as exc:

            duplicates.append(
                {
                    "candidate": candidate,
                    "reasons": [str(exc)],
                }
            )
            continue

        key = tuple(
            _normalise(item)
            for item in sequence
        )

        if key in seen:

            duplicates.append(
                {
                    "candidate": candidate,
                    "reasons": [
                        "Duplicate scenario pathway."
                    ],
                }
            )

            continue

        if len(key) != len(set(key)):

            duplicates.append(
                {
                    "candidate": candidate,
                    "reasons": [
                        "Scenario contains duplicate technologies."
                    ],
                }
            )

            continue

        seen.add(key)
        unique.append(candidate)

    return unique, duplicates


def filter_scenario_combinations(
    candidates: list[dict[str, Any]],
    *,
    factory: Any = None,
    industry: Optional[str] = None,
    technology_rules: Optional[
        dict[str, dict[str, Any]]
    ] = None,
    industry_constraints: Optional[
        dict[str, dict[str, Any]]
    ] = None,
    central_policies: Optional[
        dict[str, Any]
    ] = None,
    state_policies: Optional[
        dict[str, Any]
    ] = None,
    eligibility_rules: Optional[
        dict[str, Any]
    ] = None,
    apply_constraints: bool = True,
    apply_policy_filter: bool = True,
) -> list[dict[str, Any]]:
    """
    Main scenario gate.

    Only scenarios which survive all enabled HARD filters are returned.

    Stage 1
        structural filtering

    Stage 2
        technical/resource/infrastructure filtering

    Stage 3
        policy/regulatory filtering

    This function is intentionally conservative:
    missing evidence for a hard dependency results in rejection rather
    than a fake "feasible" scenario.
    """

    if not isinstance(
        candidates,
        list,
    ):
        candidates = list(candidates)

    if technology_rules is None:
        technology_rules = load_technology_rules()

    if industry_constraints is None:
        industry_constraints = load_industry_constraints()

    policy_data = {}

    if (
        central_policies is None
        or state_policies is None
        or eligibility_rules is None
    ):
        policy_data = load_policy_knowledge()

    if central_policies is None:
        central_policies = policy_data.get(
            "central_policies",
            {},
        )

    if state_policies is None:
        state_policies = policy_data.get(
            "state_policies",
            {},
        )

    if eligibility_rules is None:
        eligibility_rules = policy_data.get(
            "eligibility_rules",
            {},
        )

    # ---------------------------------------------------------
    # Stage 1 — structural filtering
    # ---------------------------------------------------------

    unique_candidates, _duplicates = (
        _deduplicate_candidates(
            candidates
        )
    )

    # ---------------------------------------------------------
    # Stage 2 — technical/resource filtering
    # ---------------------------------------------------------

    technically_feasible = (
        unique_candidates
    )

    rejected_for_constraints: list[
        dict[str, Any]
    ] = []

    if apply_constraints:

        engine = ConstraintPolicyFilter(
            technology_rules=technology_rules,
            industry_constraints=industry_constraints,
        )

        technically_feasible = []

        for candidate in unique_candidates:

            result = engine.evaluate_pathway(
                candidate,
                factory,
            )

            if result.feasible:

                technically_feasible.append(
                    result.pathway
                )

            else:

                rejected_for_constraints.append(
                    {
                        "candidate": candidate,
                        "reasons": (
                            result.rejection_reasons
                        ),
                        "constraint_results": (
                            result.pathway.get(
                                "constraint_results",
                                {},
                            )
                        ),
                    }
                )

    # ---------------------------------------------------------
    # Stage 3 — policy filtering
    # ---------------------------------------------------------

    policy_feasible = technically_feasible

    if apply_policy_filter:

        policy_engine = PolicyScenarioFilter(
            central_policies=central_policies,
            state_policies=state_policies,
            eligibility_rules=eligibility_rules,
        )

        policy_feasible = []

        for candidate in technically_feasible:

            result = policy_engine.evaluate_pathway(
                candidate,
                factory,
            )

            if result.feasible:

                policy_feasible.append(
                    result.pathway
                )

            # Policy filtering should be applied as a hard gate only
            # when a configured policy rule explicitly fails.
            #
            # Rejected candidates are intentionally not sent downstream.

    return policy_feasible


def filter_scenarios(
    candidates: list[dict[str, Any]],
    *,
    factory: Any = None,
    industry: Optional[str] = None,
) -> list[dict[str, Any]]:
    """
    Backward-compatible public API.

    Existing callers can continue using:

        filter_scenarios(candidates)

    New callers should pass the full factory so hard resource and policy
    constraints can actually be evaluated.
    """

    return filter_scenario_combinations(
        candidates,
        factory=factory,
        industry=industry,
        apply_constraints=True,
        apply_policy_filter=True,
    )


def filter_with_rejections(
    candidates: list[dict[str, Any]],
    *,
    factory: Any = None,
    industry: Optional[str] = None,
) -> tuple[
    list[dict[str, Any]],
    list[dict[str, Any]],
]:
    """
    Full audit-friendly API.

    Returns:
        feasible_scenarios,
        rejected_scenarios

    Every rejected scenario includes stage and reasons.
    """

    technology_rules = load_technology_rules()
    industry_constraints = (
        load_industry_constraints()
    )
    policy_data = load_policy_knowledge()

    unique_candidates, duplicates = (
        _deduplicate_candidates(
            candidates
        )
    )

    rejected: list[dict[str, Any]] = list(
        duplicates
    )

    # -------------------------------
    # Constraint gate
    # -------------------------------

    constraint_engine = ConstraintPolicyFilter(
        technology_rules=technology_rules,
        industry_constraints=industry_constraints,
    )

    constraint_passed: list[
        dict[str, Any]
    ] = []

    for candidate in unique_candidates:

        result = constraint_engine.evaluate_pathway(
            candidate,
            factory,
        )

        if result.feasible:

            constraint_passed.append(
                result.pathway
            )

        else:

            rejected.append(
                {
                    "candidate": candidate,
                    "stage": "constraint_filter",
                    "reasons": result.rejection_reasons,
                    "constraint_results": (
                        result.pathway.get(
                            "constraint_results",
                            {},
                        )
                    ),
                }
            )

    # -------------------------------
    # Policy gate
    # -------------------------------

    policy_engine = PolicyScenarioFilter(
        central_policies=policy_data.get(
            "central_policies",
            {},
        ),
        state_policies=policy_data.get(
            "state_policies",
            {},
        ),
        eligibility_rules=policy_data.get(
            "eligibility_rules",
            {},
        ),
    )

    feasible: list[
        dict[str, Any]
    ] = []

    for candidate in constraint_passed:

        result = policy_engine.evaluate_pathway(
            candidate,
            factory,
        )

        if result.feasible:

            feasible.append(
                result.pathway
            )

        else:

            rejected.append(
                {
                    "candidate": candidate,
                    "stage": "policy_filter",
                    "reasons": result.rejection_reasons,
                    "policy_results": {
                        "passed": result.passed,
                        "failed": result.failed,
                    },
                }
            )

    return feasible, rejected


__all__ = [
    "filter_scenario_combinations",
    "filter_scenarios",
    "filter_with_rejections",
    "load_technology_rules",
    "load_industry_constraints",
    "load_policy_knowledge",
]
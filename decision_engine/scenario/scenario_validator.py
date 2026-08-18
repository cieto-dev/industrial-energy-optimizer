"""
Scenario validation.

Performs final consistency checks on candidate technology pathways.

The validator checks:
- scenario structure
- duplicate technologies
- known technology IDs
- explicitly incompatible technologies
- thermal-load allocation when supplied

It does NOT calculate:
- CAPEX
- OPEX
- emissions
- payback
- MCDA scores
- ranking

Maps to:
    decision-engine/scenario/
    docs/DECISION_ENGINE_ARCHITECTURE.md
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


BASE_DIR = Path(__file__).resolve().parents[2]

RULES_FILE = (
    BASE_DIR
    / "knowledge-base"
    / "constraints"
    / "technology_rules.json"
)


def load_technology_rules() -> dict[str, dict[str, Any]]:
    """Load technology compatibility rules from the knowledge base."""

    with RULES_FILE.open("r", encoding="utf-8") as file:
        return json.load(file)


def _normalize_lookup_id(value: str) -> str:
    """Normalize a technology ID only for comparison."""
    return value.strip().lower()


def _technology_id(item: Any) -> str:
    """Extract a technology ID from supported input formats."""

    if isinstance(item, str):
        technology_id = item.strip()

        if technology_id:
            return technology_id

    if isinstance(item, dict):
        value = (
            item.get("technology_id")
            or item.get("id")
            or item.get("technology")
        )

        if isinstance(value, str):
            technology_id = value.strip()

            if technology_id:
                return technology_id

    raise ValueError(
        f"Unable to determine technology ID from: {item!r}"
    )


def _extract_sequence(candidate: Any) -> list[str]:
    """Extract and normalize the technology sequence."""

    if not isinstance(candidate, dict):
        raise ValueError(
            "Scenario candidate must be a dictionary."
        )

    sequence = candidate.get("technology_sequence")

    if sequence is None:
        sequence = candidate.get("technologies")

    if sequence is None:
        raise ValueError(
            "Scenario candidate must contain "
            "'technology_sequence'."
        )

    if not isinstance(sequence, (list, tuple)):
        raise ValueError(
            "'technology_sequence' must be a list or tuple."
        )

    if not sequence:
        raise ValueError(
            "technology_sequence cannot be empty."
        )

    return [
        _technology_id(item)
        for item in sequence
    ]


def _rule_for_technology(
    technology_id: str,
    rules: dict[str, dict[str, Any]],
) -> dict[str, Any] | None:
    """Find the KB rule for a technology."""

    lookup_id = _normalize_lookup_id(
        technology_id
    )

    for rule_id, rule in rules.items():

        if (
            _normalize_lookup_id(
                str(rule_id)
            )
            == lookup_id
        ):
            return rule

    return None


def _validate_technology_ids(
    sequence: list[str],
    rules: dict[str, dict[str, Any]],
) -> list[str]:
    """Check that every technology exists in the KB."""

    errors: list[str] = []

    for technology_id in sequence:

        if (
            _rule_for_technology(
                technology_id,
                rules,
            )
            is None
        ):
            errors.append(
                f"Unknown technology ID '{technology_id}'."
            )

    return errors


def _validate_duplicate_technologies(
    sequence: list[str],
) -> list[str]:
    """Ensure a technology is not used twice."""

    normalized = [
        _normalize_lookup_id(
            technology_id
        )
        for technology_id in sequence
    ]

    if len(normalized) != len(set(normalized)):
        return [
            "technology_sequence contains duplicate technologies."
        ]

    return []


def _validate_incompatible_pairs(
    sequence: list[str],
    rules: dict[str, dict[str, Any]],
) -> list[str]:
    """Validate explicitly declared incompatible pairs."""

    errors: list[str] = []

    for index, technology_a in enumerate(sequence):

        rules_a = _rule_for_technology(
            technology_a,
            rules,
        )

        if rules_a is None:
            continue

        incompatible_a = {
            _normalize_lookup_id(
                str(value)
            )
            for value in rules_a.get(
                "incompatible_with",
                [],
            )
        }

        lookup_a = _normalize_lookup_id(
            technology_a
        )

        for technology_b in sequence[index + 1:]:

            lookup_b = _normalize_lookup_id(
                technology_b
            )

            if lookup_b in incompatible_a:
                errors.append(
                    (
                        f"'{technology_a}' is incompatible "
                        f"with '{technology_b}'."
                    )
                )

            rules_b = _rule_for_technology(
                technology_b,
                rules,
            )

            if rules_b is None:
                continue

            incompatible_b = {
                _normalize_lookup_id(
                    str(value)
                )
                for value in rules_b.get(
                    "incompatible_with",
                    [],
                )
            }

            if lookup_a in incompatible_b:
                errors.append(
                    (
                        f"'{technology_b}' is incompatible "
                        f"with '{technology_a}'."
                    )
                )

    return errors


def _validate_thermal_load_allocation(
    candidate: dict[str, Any],
) -> list[str]:
    """
    Validate an optional thermal-load allocation map.

    Example:

        "thermal_load_shares_pct": {
            "heat_pump": 40,
            "biomass_boiler": 60
        }

    The total must not exceed 100%.
    """

    shares = candidate.get(
        "thermal_load_shares_pct"
    )

    if shares is None:
        return []

    if not isinstance(shares, dict):
        return [
            "thermal_load_shares_pct must be an object/map."
        ]

    errors: list[str] = []
    total = 0.0

    for technology_id, share in shares.items():

        try:
            share_value = float(share)

        except (TypeError, ValueError):
            errors.append(
                (
                    f"Thermal-load share for "
                    f"'{technology_id}' is not numeric."
                )
            )
            continue

        if share_value < 0:
            errors.append(
                (
                    f"Thermal-load share for "
                    f"'{technology_id}' cannot be negative."
                )
            )

        if share_value > 100:
            errors.append(
                (
                    f"Thermal-load share for "
                    f"'{technology_id}' cannot exceed 100%."
                )
            )

        total += share_value

    if total > 100.01:
        errors.append(
            (
                "Thermal-load allocation exceeds 100%; "
                "the same thermal demand would be double-counted."
            )
        )

    return errors


def validate_scenario(
    candidate: dict[str, Any],
    rules: dict[str, dict[str, Any]] | None = None,
) -> tuple[bool, list[str]]:
    """
    Validate one candidate scenario.

    Returns:
        (True, []) when valid.

        (False, [reasons]) when invalid.
    """

    if rules is None:
        rules = load_technology_rules()

    try:
        sequence = _extract_sequence(
            candidate
        )

    except ValueError as exc:
        return False, [str(exc)]

    errors: list[str] = []

    errors.extend(
        _validate_technology_ids(
            sequence,
            rules,
        )
    )

    errors.extend(
        _validate_duplicate_technologies(
            sequence
        )
    )

    errors.extend(
        _validate_incompatible_pairs(
            sequence,
            rules,
        )
    )

    errors.extend(
        _validate_thermal_load_allocation(
            candidate
        )
    )

    return (
        len(errors) == 0,
        errors,
    )


def validate_scenarios(
    candidates: list[dict[str, Any]],
) -> tuple[
    list[dict[str, Any]],
    list[dict[str, Any]],
]:
    """
    Validate multiple candidate scenarios.

    Returns:

        valid_scenarios,
        rejected_scenarios

    Rejected scenarios retain:
        - original candidate
        - validation reasons
    """

    rules = load_technology_rules()

    valid: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []

    seen: set[tuple[str, ...]] = set()

    for candidate in candidates:

        try:
            sequence = _extract_sequence(
                candidate
            )

        except ValueError as exc:
            rejected.append(
                {
                    "candidate": candidate,
                    "reasons": [str(exc)],
                }
            )
            continue

        normalized_sequence = tuple(
            _normalize_lookup_id(
                technology_id
            )
            for technology_id in sequence
        )

        if normalized_sequence in seen:
            rejected.append(
                {
                    "candidate": candidate,
                    "reasons": [
                        "Duplicate scenario pathway."
                    ],
                }
            )
            continue

        is_valid, errors = validate_scenario(
            candidate,
            rules=rules,
        )

        if is_valid:
            seen.add(
                normalized_sequence
            )
            valid.append(candidate)

        else:
            rejected.append(
                {
                    "candidate": candidate,
                    "reasons": errors,
                }
            )

    return valid, rejected
"""
Scenario filtering and combination rules.

Filters candidate technology pathways before validation.

The filter:
- removes duplicate technologies within a pathway
- removes duplicate pathways
- removes explicitly incompatible technology combinations
- checks industry eligibility when requested
- preserves the original technology IDs in the output
- uses technology_rules.json as the rule source

It does NOT calculate:
- economics
- emissions
- ranking
- payback

Maps to:
- decision_engine/scenario/
- docs/DECISION_ENGINE_ARCHITECTURE.md
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable


BASE_DIR = Path(__file__).resolve().parents[2]

RULES_FILE = (
    BASE_DIR
    / "knowledge-base"
    / "constraints"
    / "technology_rules.json"
)


# Known differences between factory/industry identifiers and
# the identifiers currently used by technology_rules.json.
INDUSTRY_ALIASES = {
    "pharma": "pharmaceutical",
    "food": "food_processing",
}


def load_technology_rules() -> dict[str, dict[str, Any]]:
    """Load technology compatibility rules from the knowledge base."""

    with RULES_FILE.open("r", encoding="utf-8") as file:
        return json.load(file)


def _normalize_lookup_id(value: str) -> str:
    """
    Normalize an ID only for rule lookup/comparison.

    IMPORTANT:
    This does NOT change the ID stored in the returned scenario.
    """

    return value.strip().lower()


def _technology_id(item: Any) -> str:
    """
    Extract a technology ID while preserving its original spelling.

    Supported inputs:
    - "TECH_WHR"
    - {"technology_id": "TECH_WHR"}
    - {"id": "TECH_WHR"}
    - {"technology": "TECH_WHR"}
    """

    if isinstance(item, str):
        technology_id = item.strip()

        if technology_id:
            return technology_id

    elif isinstance(item, dict):
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


def normalize_sequence(
    sequence: Iterable[Any],
) -> tuple[str, ...]:
    """
    Extract technology IDs while preserving their canonical spelling.
    """

    normalized = tuple(
        _technology_id(item)
        for item in sequence
    )

    if not normalized:
        raise ValueError(
            "Technology sequence cannot be empty."
        )

    return normalized


def _extract_sequence(
    candidate: Any,
) -> tuple[str, ...]:
    """Extract technology_sequence from a scenario candidate."""

    if isinstance(candidate, dict):

        sequence = candidate.get(
            "technology_sequence"
        )

        if sequence is None:
            sequence = candidate.get(
                "technologies"
            )

        if sequence is None:
            raise ValueError(
                "Scenario candidate must contain "
                "'technology_sequence'."
            )

        return normalize_sequence(sequence)

    return normalize_sequence(candidate)


def _rule_for_technology(
    technology_id: str,
    rules: dict[str, dict[str, Any]],
) -> dict[str, Any] | None:
    """
    Find the technology rule using a normalized lookup ID.

    This allows the domain model to preserve canonical IDs while the
    current technology_rules.json uses lowercase identifiers.
    """

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


def _rule_id_exists(
    technology_id: str,
    rules: dict[str, dict[str, Any]],
) -> bool:
    """Return True when a technology has a rule entry."""

    return (
        _rule_for_technology(
            technology_id,
            rules,
        )
        is not None
    )


def _normalized_rule_references(
    values: Any,
) -> set[str]:
    """
    Normalize technology IDs contained inside a rule list.

    Used only for comparison.
    """

    if not isinstance(values, list):
        return set()

    return {
        _normalize_lookup_id(str(value))
        for value in values
        if value is not None
    }


def _has_explicit_incompatibility(
    sequence: tuple[str, ...],
    rules: dict[str, dict[str, Any]],
) -> tuple[bool, str]:
    """
    Check explicitly declared incompatible technology pairs.

    We intentionally DO NOT treat absence from compatible_with as
    incompatibility. Only an explicit incompatible_with declaration
    causes rejection.
    """

    for index, technology_a in enumerate(sequence):

        rules_a = _rule_for_technology(
            technology_a,
            rules,
        )

        if rules_a is None:
            continue

        incompatible_a = (
            _normalized_rule_references(
                rules_a.get(
                    "incompatible_with",
                    [],
                )
            )
        )

        lookup_a = _normalize_lookup_id(
            technology_a
        )

        for technology_b in sequence[index + 1:]:

            lookup_b = _normalize_lookup_id(
                technology_b
            )

            # A explicitly says B is incompatible.
            if lookup_b in incompatible_a:
                return (
                    True,
                    (
                        f"'{technology_a}' is incompatible "
                        f"with '{technology_b}'."
                    ),
                )

            # Check the reverse declaration too.
            rules_b = _rule_for_technology(
                technology_b,
                rules,
            )

            if rules_b is None:
                continue

            incompatible_b = (
                _normalized_rule_references(
                    rules_b.get(
                        "incompatible_with",
                        [],
                    )
                )
            )

            if lookup_a in incompatible_b:
                return (
                    True,
                    (
                        f"'{technology_b}' is incompatible "
                        f"with '{technology_a}'."
                    ),
                )

    return False, ""


def _industry_is_allowed(
    sequence: tuple[str, ...],
    industry: str | None,
    rules: dict[str, dict[str, Any]],
) -> tuple[bool, str]:
    """
    Check technology eligibility for the requested industry.

    If an industry is not supplied, this check is skipped.
    """

    if industry is None:
        return True, ""

    cleaned_industry = (
        industry.strip().lower()
    )

    industry_id = INDUSTRY_ALIASES.get(
        cleaned_industry,
        cleaned_industry,
    )

    for technology_id in sequence:

        technology_rules = _rule_for_technology(
            technology_id,
            rules,
        )

        if technology_rules is None:
            return (
                False,
                (
                    f"No technology rules found for "
                    f"'{technology_id}'."
                ),
            )

        allowed_industries = {
            str(value).strip().lower()
            for value in technology_rules.get(
                "allowed_industries",
                [],
            )
        }

        # Empty allowed_industries means the current KB does not
        # restrict this technology by industry.
        if not allowed_industries:
            continue

        if industry_id not in allowed_industries:
            return (
                False,
                (
                    f"Technology '{technology_id}' is not "
                    f"configured for industry '{industry_id}'."
                ),
            )

    return True, ""


def filter_scenario_combinations(
    candidates: Iterable[Any],
    industry: str | None = None,
    rules: dict[str, dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    """
    Remove duplicate and explicitly inconsistent scenario combinations.

    Returns normalized candidate dictionaries containing:
        technology_sequence

    The original technology ID spelling is preserved.
    """

    if rules is None:
        rules = load_technology_rules()

    filtered: list[dict[str, Any]] = []

    # Comparison keys use normalized IDs, but output preserves
    # the canonical IDs supplied by the caller.
    seen: set[tuple[str, ...]] = set()

    for candidate in candidates:

        try:
            sequence = _extract_sequence(
                candidate
            )

        except ValueError:
            # Invalid candidate structure.
            continue

        comparison_sequence = tuple(
            _normalize_lookup_id(
                technology_id
            )
            for technology_id in sequence
        )

        # ---------------------------------------------------------
        # 1. No duplicate technology within one scenario
        # ---------------------------------------------------------

        if (
            len(comparison_sequence)
            != len(set(comparison_sequence))
        ):
            continue

        # ---------------------------------------------------------
        # 2. No duplicate scenario pathway
        # ---------------------------------------------------------

        if comparison_sequence in seen:
            continue

        # ---------------------------------------------------------
        # 3. Every technology must exist in the KB rules
        # ---------------------------------------------------------

        if any(
            not _rule_id_exists(
                technology_id,
                rules,
            )
            for technology_id in sequence
        ):
            continue

        # ---------------------------------------------------------
        # 4. Explicit incompatibility check
        # ---------------------------------------------------------

        incompatible, _reason = (
            _has_explicit_incompatibility(
                sequence,
                rules,
            )
        )

        if incompatible:
            continue

        # ---------------------------------------------------------
        # 5. Industry eligibility
        # ---------------------------------------------------------

        industry_allowed, _reason = (
            _industry_is_allowed(
                sequence,
                industry,
                rules,
            )
        )

        if not industry_allowed:
            continue

        # Scenario has survived all filter rules.
        seen.add(comparison_sequence)

        if isinstance(candidate, dict):

            normalized_candidate = dict(
                candidate
            )

            # Preserve canonical IDs.
            normalized_candidate[
                "technology_sequence"
            ] = list(sequence)

        else:

            normalized_candidate = {
                "technology_sequence": list(
                    sequence
                )
            }

        filtered.append(
            normalized_candidate
        )

    return filtered


def filter_scenarios(
    candidates: Iterable[Any],
    industry: str | None = None,
) -> list[dict[str, Any]]:
    """
    Public convenience wrapper.
    """

    return filter_scenario_combinations(
        candidates=candidates,
        industry=industry,
    )
"""
Scenario Generator.

Generates multiple candidate technology pathways from feasible
technologies.

The scenario module is responsible for generating 3–5 candidate
pathways. It does NOT perform:
- emissions scoring
- reliability scoring
- MCDA ranking
- policy eligibility

Economic calculations are handled by downstream modules.

The existing Biogas-specific scenario generator is preserved.

Maps to:
    decision-engine/scenario/
    docs/DECISION_ENGINE_ARCHITECTURE.md
"""

from __future__ import annotations

from itertools import combinations
from typing import Any


def _technology_id(item: Any) -> str:
    """
    Extract a technology ID from supported input formats.

    Supported:
        "heat_pump"
        {"technology_id": "heat_pump"}
        {"id": "heat_pump"}
        {"technology": "heat_pump"}
    """

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


def normalize_feasible_technologies(
    feasible_technologies: list[Any],
) -> list[str]:
    """
    Normalize feasible technology inputs into unique technology IDs.

    Preserves the original casing for output while deduplicating
    technology IDs case-insensitively.
    """

    technology_ids: list[str] = []
    seen: set[str] = set()

    for item in feasible_technologies:

        try:
            technology_id = _technology_id(item)

        except ValueError:
            continue

        comparison_id = technology_id.lower()

        if comparison_id in seen:
            continue

        seen.add(comparison_id)
        technology_ids.append(technology_id)

    return technology_ids


def generate_candidate_pathways(
    feasible_technologies: list[Any],
    minimum_scenarios: int = 3,
    maximum_scenarios: int = 5,
) -> list[dict[str, Any]]:
    """
    Generate 3–5 unique candidate technology pathways.

    Pathways are generated deterministically from the supplied
    feasible technologies.

    Single-technology pathways are considered first, followed by
    two-technology hybrid pathways.

    This function only generates candidate combinations.

    It does NOT calculate:
        - CAPEX
        - OPEX
        - emissions
        - payback
        - reliability
        - MCDA scores
        - ranking
    """

    if minimum_scenarios < 1:
        raise ValueError(
            "minimum_scenarios must be at least 1."
        )

    if maximum_scenarios < minimum_scenarios:
        raise ValueError(
            "maximum_scenarios cannot be smaller than "
            "minimum_scenarios."
        )

    technology_ids = normalize_feasible_technologies(
        feasible_technologies
    )

    # The scenario gate requires at least the configured minimum
    # number of candidate pathways.
    if len(technology_ids) < minimum_scenarios:
        raise ValueError(
            f"At least {minimum_scenarios} unique feasible technologies "
            f"are required to generate {minimum_scenarios} "
            f"candidate pathways."
        )

    candidates: list[dict[str, Any]] = []

    # ---------------------------------------------------------
    # 1. Single-technology pathways
    # ---------------------------------------------------------

    for technology_id in technology_ids:

        candidates.append(
            {
                "technology_sequence": [
                    technology_id
                ]
            }
        )

        if len(candidates) >= maximum_scenarios:
            break

    # ---------------------------------------------------------
    # 2. Two-technology hybrid pathways
    # ---------------------------------------------------------

    if len(candidates) < maximum_scenarios:

        for technology_a, technology_b in combinations(
            technology_ids,
            2,
        ):

            candidates.append(
                {
                    "technology_sequence": [
                        technology_a,
                        technology_b,
                    ]
                }
            )

            if len(candidates) >= maximum_scenarios:
                break

    # ---------------------------------------------------------
    # 3. Final scenario-count gate
    # ---------------------------------------------------------

    if len(candidates) < minimum_scenarios:
        raise ValueError(
            f"Only {len(candidates)} candidate pathways could "
            f"be generated; required at least "
            f"{minimum_scenarios}."
        )

    return candidates[:maximum_scenarios]


def generate_biogas_scenario(
    heat_demand_kwh_day: float,
    biogas_energy_content_kwh_m3: float,
    boiler_efficiency: float,
    biogas_emission_factor_kg_co2_m3: float,
) -> dict[str, Any]:
    """
    Generate the existing Biogas replacement scenario.

    This function is retained for backward compatibility with the
    existing prototype.
    """

    if heat_demand_kwh_day < 0:
        raise ValueError(
            "heat_demand_kwh_day cannot be negative."
        )

    if biogas_energy_content_kwh_m3 <= 0:
        raise ValueError(
            "biogas_energy_content_kwh_m3 must be greater than zero."
        )

    if not 0 < boiler_efficiency <= 1:
        raise ValueError(
            "boiler_efficiency must be greater than 0 and <= 1."
        )

    if biogas_emission_factor_kg_co2_m3 < 0:
        raise ValueError(
            "biogas_emission_factor_kg_co2_m3 cannot be negative."
        )

    required_input_energy_kwh_day = (
        heat_demand_kwh_day / boiler_efficiency
    )

    biogas_required_m3_day = (
        required_input_energy_kwh_day
        / biogas_energy_content_kwh_m3
    )

    co2_kg_day = (
        biogas_required_m3_day
        * biogas_emission_factor_kg_co2_m3
    )

    co2_tco2_day = co2_kg_day / 1000.0

    return {
        "scenario": "biogas_replacement",
        "replacement_technology": "biogas",
        "heat_demand_kwh_day": heat_demand_kwh_day,
        "biogas_required_m3_day": biogas_required_m3_day,
        "co2_kg_day": co2_kg_day,
        "co2_tco2_day": co2_tco2_day,
        "feasible": True,
    }
"""
Scenario Generator.

Generates meaningful candidate technology pathways from technically
feasible technology outputs.

Responsibilities
----------------
This module:
    - accepts feasible technology outputs from the technology layer
    - preserves technology/pathway provenance
    - generates baseline, single-technology and meaningful hybrid pathways
    - supports biomass-aware pathways
    - preserves the existing biogas scenario functionality

This module does NOT:
    - calculate optimisation scores
    - perform MCDA ranking
    - calculate financial returns
    - determine policy eligibility
    - replace the constraint engine

Architecture
------------
G1 technical engine
        |
        v
feasible technology outputs
        |
        v
Scenario Generator
        |
        v
candidate pathways
        |
        v
Optimizer / Finance / Impact

The scenario contract remains intentionally lightweight so that the
optimizer and pipeline do not need to change.
"""

from __future__ import annotations

from itertools import combinations
from typing import Any


# ---------------------------------------------------------------------------
# Technology extraction helpers
# ---------------------------------------------------------------------------


def _technology_id(item: Any) -> str:
    """
    Extract a technology identifier from supported input formats.

    Supported examples
    -------------------
    "heat_pump"

    {
        "technology_id": "heat_pump"
    }

    {
        "id": "heat_pump"
    }

    {
        "technology": "heat_pump"
    }

    {
        "technology_id": "biomass_boiler",
        "technology_type": "biomass"
    }
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
            or item.get("technology_name")
        )

        if isinstance(value, str):
            technology_id = value.strip()

            if technology_id:
                return technology_id

    raise ValueError(
        f"Unable to determine technology ID from: {item!r}"
    )


def _technology_type(item: Any) -> str:
    """
    Infer the technology type.

    Explicit type fields are preferred. If absent, the technology ID
    is inspected for known biomass / biogas naming patterns.
    """

    if isinstance(item, dict):
        explicit_type = (
            item.get("technology_type")
            or item.get("type")
            or item.get("fuel_type")
            or item.get("resource_type")
        )

        if isinstance(explicit_type, str):
            value = explicit_type.strip().lower()

            if value:
                return value

    technology_id = _technology_id(item).lower()

    if "biomass" in technology_id:
        return "biomass"

    if "biogas" in technology_id:
        return "biogas"

    return "other"


def _is_biomass_technology(item: Any) -> bool:
    """Return True when the candidate represents biomass technology."""

    return _technology_type(item) == "biomass"


def _is_biogas_technology(item: Any) -> bool:
    """Return True when the candidate represents biogas technology."""

    return _technology_type(item) == "biogas"


def _technology_record(item: Any) -> dict[str, Any]:
    """
    Convert a supported technology input into a safe internal record.

    The original technical metadata is retained where possible so that
    scenario provenance is not lost.
    """

    technology_id = _technology_id(item)

    if isinstance(item, dict):
        record = dict(item)
    else:
        record = {}

    record.setdefault("technology_id", technology_id)
    record.setdefault("technology_type", _technology_type(item))

    return record


# ---------------------------------------------------------------------------
# Normalisation
# ---------------------------------------------------------------------------


def normalize_feasible_technologies(
    feasible_technologies: list[Any],
) -> list[dict[str, Any]]:
    """
    Normalize feasible technology inputs.

    Returns unique technology records while preserving the original
    metadata associated with each candidate.

    Deduplication is case-insensitive on technology_id.
    """

    normalized: list[dict[str, Any]] = []
    seen: set[str] = set()

    for item in feasible_technologies:
        try:
            record = _technology_record(item)
        except ValueError:
            continue

        technology_id = record["technology_id"]
        comparison_id = technology_id.lower()

        if comparison_id in seen:
            continue

        seen.add(comparison_id)
        normalized.append(record)

    return normalized


# ---------------------------------------------------------------------------
# Candidate pathway helpers
# ---------------------------------------------------------------------------


def _pathway(
    technologies: list[dict[str, Any]],
    pathway_type: str,
    *,
    reason: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Build the stable pathway contract used by downstream modules.

    Only technical/pathway information is included here. Economic and
    optimisation fields remain downstream responsibilities.
    """

    technology_ids = [
        technology["technology_id"]
        for technology in technologies
    ]

    pathway: dict[str, Any] = {
        "technologies": technology_ids,
        "technology_sequence": technology_ids,
        "pathway_type": pathway_type,
        "feasible": True,
        "provenance": {
            "technology_ids": technology_ids,
            "technology_types": [
                technology.get("technology_type", "other")
                for technology in technologies
            ],
        },
    }

    if reason:
        pathway["reason"] = reason

    if metadata:
        pathway["scenario_metadata"] = metadata

    return pathway


def _contains_type(
    technologies: list[dict[str, Any]],
    technology_type: str,
) -> bool:
    """Check whether a technology collection contains a given type."""

    return any(
        technology.get("technology_type") == technology_type
        for technology in technologies
    )


def _has_biomass_metadata(
    technology: dict[str, Any],
) -> bool:
    """
    Detect whether a biomass candidate carries explicit resource /
    supply-chain metadata.

    This intentionally accepts several possible field names so the
    scenario generator remains compatible with different BiomassEngine
    output structures.
    """

    if not _is_biomass_technology(technology):
        return False

    biomass_fields = {
        "biomass_available",
        "available_biomass",
        "biomass_availability",
        "resource_available",
        "fuel_available",
        "annual_biomass_tonnes",
        "surplus_biomass_tonnes",
        "supply_reliability",
        "biomass_supply_reliability",
        "transport_distance_km",
        "delivered_biomass_cost",
        "fuel_cost",
        "biomass_source",
    }

    return any(
        field in technology
        for field in biomass_fields
    )


# ---------------------------------------------------------------------------
# Biomass-aware scenario generation
# ---------------------------------------------------------------------------


def _generate_biomass_scenarios(
    technology_records: list[dict[str, Any]],
    maximum_scenarios: int,
) -> list[dict[str, Any]]:
    """
    Generate biomass-aware scenarios.

    The BiomassEngine is expected to have already evaluated technical
    biomass suitability/availability. This function therefore does not
    recalculate biomass availability; it uses the supplied technical
    output as the source of truth.

    Scenario patterns:
        1. biomass-only pathway
        2. biomass + non-biomass hybrid
        3. biomass + other compatible technology

    No financial or optimisation calculations are performed.
    """

    scenarios: list[dict[str, Any]] = []

    biomass = [
        technology
        for technology in technology_records
        if _is_biomass_technology(technology)
    ]

    non_biomass = [
        technology
        for technology in technology_records
        if not _is_biomass_technology(technology)
    ]

    if not biomass:
        return scenarios

    # ---------------------------------------------------------
    # Biomass-only pathways
    # ---------------------------------------------------------

    for biomass_technology in biomass:
        metadata = {
            "biomass_aware": True,
            "biomass_metadata_available": _has_biomass_metadata(
                biomass_technology
            ),
        }

        scenarios.append(
            _pathway(
                [biomass_technology],
                pathway_type="biomass_only",
                reason=(
                    "Biomass technology supplied by the technical "
                    "technology engine."
                ),
                metadata=metadata,
            )
        )

        if len(scenarios) >= maximum_scenarios:
            return scenarios[:maximum_scenarios]

    # ---------------------------------------------------------
    # Biomass hybrid pathways
    # ---------------------------------------------------------

    for biomass_technology in biomass:

        for supporting_technology in non_biomass:

            # Avoid creating a biomass + biogas pair automatically.
            # Both are fuel-replacement pathways and are generally
            # alternative thermal fuel choices rather than a meaningful
            # default hybrid.
            if _is_biogas_technology(supporting_technology):
                continue

            hybrid = [
                biomass_technology,
                supporting_technology,
            ]

            scenarios.append(
                _pathway(
                    hybrid,
                    pathway_type="biomass_hybrid",
                    reason=(
                        "Biomass is combined with another feasible "
                        "technology to form a mixed pathway."
                    ),
                    metadata={
                        "biomass_aware": True,
                        "biomass_metadata_available": (
                            _has_biomass_metadata(biomass_technology)
                        ),
                    },
                )
            )

            if len(scenarios) >= maximum_scenarios:
                return scenarios[:maximum_scenarios]

    return scenarios[:maximum_scenarios]


# ---------------------------------------------------------------------------
# Generic scenario generation
# ---------------------------------------------------------------------------


def generate_candidate_pathways(
    feasible_technologies: list[Any],
    minimum_scenarios: int = 3,
    maximum_scenarios: int = 5,
    *,
    include_biomass_scenarios: bool = True,
) -> list[dict[str, Any]]:
    """
    Generate 3–5 meaningful candidate technology pathways.

    Generation order
    ----------------
    1. Biomass-aware pathways, when biomass candidates are present.
    2. Single-technology pathways.
    3. Two-technology hybrid pathways.

    Biomass is not treated as a special financial decision here. The
    scenario engine simply preserves biomass-related technical
    information supplied by the technology layer.

    Parameters
    ----------
    feasible_technologies:
        Technical outputs that have already passed feasibility checks.

    minimum_scenarios:
        Minimum number of candidate pathways required.

    maximum_scenarios:
        Maximum number of candidate pathways to return.

    include_biomass_scenarios:
        Enables biomass-aware scenario generation.

    Returns
    -------
    list[dict[str, Any]]
        Candidate pathways preserving technology provenance.
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

    technology_records = normalize_feasible_technologies(
        feasible_technologies
    )

    if len(technology_records) < minimum_scenarios:
        raise ValueError(
            f"At least {minimum_scenarios} unique feasible technologies "
            f"are required to generate {minimum_scenarios} "
            f"candidate pathways."
        )

    candidates: list[dict[str, Any]] = []

    # ---------------------------------------------------------
    # 1. Biomass-aware scenarios
    # ---------------------------------------------------------

    if include_biomass_scenarios:
        biomass_candidates = _generate_biomass_scenarios(
            technology_records,
            maximum_scenarios=maximum_scenarios,
        )

        for scenario in biomass_candidates:
            if scenario not in candidates:
                candidates.append(scenario)

            if len(candidates) >= maximum_scenarios:
                break

    # ---------------------------------------------------------
    # 2. Single-technology pathways
    # ---------------------------------------------------------

    if len(candidates) < maximum_scenarios:

        for technology in technology_records:

            pathway_type = "single_technology"

            if _is_biomass_technology(technology):
                pathway_type = "biomass_only"

            elif _is_biogas_technology(technology):
                pathway_type = "biogas_only"

            scenario = _pathway(
                [technology],
                pathway_type=pathway_type,
                metadata={
                    "biomass_aware": _is_biomass_technology(
                        technology
                    ),
                    "biogas_aware": _is_biogas_technology(
                        technology
                    ),
                },
            )

            if scenario not in candidates:
                candidates.append(scenario)

            if len(candidates) >= maximum_scenarios:
                break

    # ---------------------------------------------------------
    # 3. Two-technology hybrids
    # ---------------------------------------------------------

    if len(candidates) < maximum_scenarios:

        for technology_a, technology_b in combinations(
            technology_records,
            2,
        ):

            a_biomass = _is_biomass_technology(technology_a)
            b_biomass = _is_biomass_technology(technology_b)

            a_biogas = _is_biogas_technology(technology_a)
            b_biogas = _is_biogas_technology(technology_b)

            # Avoid pairing two alternative fuel technologies as a
            # default hybrid because the scenario would usually not
            # represent a meaningful pathway.
            if (
                (a_biomass and b_biogas)
                or (a_biogas and b_biomass)
            ):
                continue

            if a_biomass or b_biomass:
                pathway_type = "biomass_hybrid"
            elif a_biogas or b_biogas:
                pathway_type = "biogas_hybrid"
            else:
                pathway_type = "technology_hybrid"

            scenario = _pathway(
                [technology_a, technology_b],
                pathway_type=pathway_type,
                reason=(
                    "Two technically feasible technologies are "
                    "combined into a candidate pathway."
                ),
                metadata={
                    "biomass_aware": (
                        a_biomass or b_biomass
                    ),
                    "biogas_aware": (
                        a_biogas or b_biogas
                    ),
                },
            )

            if scenario not in candidates:
                candidates.append(scenario)

            if len(candidates) >= maximum_scenarios:
                break

    # ---------------------------------------------------------
    # 4. Minimum-scenario validation
    # ---------------------------------------------------------

    if len(candidates) < minimum_scenarios:
        raise ValueError(
            f"Only {len(candidates)} candidate pathways could "
            f"be generated; required at least "
            f"{minimum_scenarios}."
        )

    return candidates[:maximum_scenarios]


# ---------------------------------------------------------------------------
# Backward-compatible Biogas scenario
# ---------------------------------------------------------------------------


def generate_biogas_scenario(
    heat_demand_kwh_day: float,
    biogas_energy_content_kwh_m3: float,
    boiler_efficiency: float,
    biogas_emission_factor_kg_co2_m3: float,
) -> dict[str, Any]:
    """
    Generate the existing Biogas replacement scenario.

    This function is intentionally preserved for backward compatibility
    with the existing prototype and any current callers.

    It performs only the calculations already associated with the
    biogas scenario. It does not interact with the biomass engine.
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


# ---------------------------------------------------------------------------
# Optional convenience wrapper
# ---------------------------------------------------------------------------


def generate_scenarios(
    feasible_technologies: list[Any],
    minimum_scenarios: int = 3,
    maximum_scenarios: int = 5,
) -> list[dict[str, Any]]:
    """
    Compatibility wrapper for callers that use a generic
    `generate_scenarios(...)` function name.
    """

    return generate_candidate_pathways(
        feasible_technologies=feasible_technologies,
        minimum_scenarios=minimum_scenarios,
        maximum_scenarios=maximum_scenarios,
        include_biomass_scenarios=True,
    )


__all__ = [
    "normalize_feasible_technologies",
    "generate_candidate_pathways",
    "generate_scenarios",
    "generate_biogas_scenario",
]


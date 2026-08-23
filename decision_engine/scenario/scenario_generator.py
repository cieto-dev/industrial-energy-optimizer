

from __future__ import annotations

from itertools import combinations
from typing import Any

from .scenario_filter import filter_scenario_combinations
from .scenario_validator import validate_scenario


# ---------------------------------------------------------------------------
# Generic technology helpers
# ---------------------------------------------------------------------------


def _technology_id(item: Any) -> str:
    """
    Extract a technology identifier from supported input formats.

    Supported inputs
    ----------------
    "heat_pump"

    {"technology_id": "heat_pump"}

    {"id": "heat_pump"}

    {"technology": "heat_pump"}

    {"technology_name": "heat_pump"}
    """

    if isinstance(item, str):
        value = item.strip()

        if value:
            return value

    if isinstance(item, dict):
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
        f"Unable to determine technology ID from: {item!r}"
    )


def _technology_type(item: Any) -> str:
    """
    Infer a technology/resource type.

    Explicit metadata is preferred. The identifier is used only as a
    fallback for common biomass/biogas naming patterns.
    """

    if isinstance(item, dict):
        explicit_type = (
            item.get("technology_type")
            or item.get("type")
            or item.get("fuel_type")
            or item.get("resource_type")
        )

        if isinstance(explicit_type, str):
            explicit_type = explicit_type.strip().lower()

            if explicit_type:
                return explicit_type

    technology_id = _technology_id(item).lower()

    if "biomass" in technology_id:
        return "biomass"

    if "biogas" in technology_id:
        return "biogas"

    return "other"


def _technology_record(item: Any) -> dict[str, Any]:
    """
    Convert an upstream technology object into a stable internal record.

    Existing metadata is retained to preserve provenance and allow later
    modules to inspect upstream technical assumptions.
    """

    technology_id = _technology_id(item)

    record = dict(item) if isinstance(item, dict) else {}

    record.setdefault("technology_id", technology_id)
    record.setdefault(
        "technology_type",
        _technology_type(item),
    )

    return record


def _is_biomass(item: Any) -> bool:
    """Return True when the technology is biomass-based."""

    return _technology_type(item) == "biomass"


def _is_biogas(item: Any) -> bool:
    """Return True when the technology is biogas-based."""

    return _technology_type(item) == "biogas"


def _normalised_id(value: str) -> str:
    """Return a comparison-safe technology ID."""

    return value.strip().lower()


# ---------------------------------------------------------------------------
# Normalisation utilities
# ---------------------------------------------------------------------------


def normalize_feasible_technologies(
    feasible_technologies: list[Any],
) -> list[dict[str, Any]]:
    """
    Normalise upstream feasible technology outputs.

    Invalid records are ignored rather than fabricated or repaired.

    Deduplication is case-insensitive on technology_id while preserving
    the first supplied record.
    """

    if feasible_technologies is None:
        return []

    normalised: list[dict[str, Any]] = []
    seen: set[str] = set()

    for item in feasible_technologies:
        try:
            record = _technology_record(item)
        except ValueError:
            continue

        technology_id = record["technology_id"]
        comparison_id = _normalised_id(technology_id)

        if comparison_id in seen:
            continue

        seen.add(comparison_id)
        normalised.append(record)

    return normalised


# ---------------------------------------------------------------------------
# Biomass utilities
# ---------------------------------------------------------------------------


def _has_biomass_supply_metadata(
    technology: dict[str, Any],
) -> bool:
    """
    Determine whether biomass supply/resource metadata is present.

    This is deliberately metadata detection only. It does NOT claim that
    biomass is available or affordable; upstream technical/resource
    modules remain the source of truth for those facts.
    """

    if not _is_biomass(technology):
        return False

    recognised_fields = {
        "biomass_available",
        "available_biomass",
        "biomass_availability",
        "resource_available",
        "fuel_available",
        "annual_biomass_tonnes",
        "surplus_biomass_tonnes",
        "biomass_supply_reliability",
        "supply_reliability",
        "transport_distance_km",
        "delivered_biomass_cost",
        "fuel_cost",
        "biomass_source",
    }

    return any(
        field in technology
        for field in recognised_fields
    )


def _biomass_metadata(
    technology: dict[str, Any],
) -> dict[str, Any]:
    """Create explainable biomass metadata for a pathway."""

    return {
        "biomass_aware": True,
        "biomass_supply_metadata_present": (
            _has_biomass_supply_metadata(technology)
        ),
    }


# ---------------------------------------------------------------------------
# Pathway utilities
# ---------------------------------------------------------------------------


def build_pathway(
    technologies: list[dict[str, Any]],
    pathway_type: str,
    *,
    reason: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Build the shared pathway representation.

    Downstream finance/optimization metrics are intentionally omitted.

    The resulting pathway is compatible with the project's shared
    technology/pathway contract and retains provenance for explanation.
    """

    technology_ids = [
        technology["technology_id"]
        for technology in technologies
    ]

    technology_types = [
        technology.get("technology_type", "other")
        for technology in technologies
    ]

    pathway: dict[str, Any] = {
        "technologies": technology_ids,
        "technology_sequence": technology_ids,
        "pathway_type": pathway_type,
        "feasible": True,
        "provenance": {
            "technology_ids": technology_ids,
            "technology_types": technology_types,
        },
    }

    if reason:
        pathway["reason"] = reason

    if metadata:
        pathway["scenario_metadata"] = metadata

    return pathway


def _scenario_key(candidate: dict[str, Any]) -> tuple[str, ...]:
    """
    Build a deterministic comparison key for duplicate scenarios.

    Order is preserved because the technology sequence is meaningful for
    some future pathway representations.
    """

    sequence = candidate.get(
        "technology_sequence",
        candidate.get("technologies", []),
    )

    return tuple(
        _normalised_id(_technology_id(item))
        for item in sequence
    )


# ---------------------------------------------------------------------------
# Meaningful candidate generation
# ---------------------------------------------------------------------------


def generate_candidate_pathways(
    feasible_technologies: list[Any],
    minimum_scenarios: int = 3,
    maximum_scenarios: int = 5,
    *,
    include_biomass_scenarios: bool = True,
) -> list[dict[str, Any]]:
    """
    Generate a bounded set of meaningful candidate pathways.

    Generation priority
    -------------------
    1. biomass-only pathway when biomass is technically available
    2. other single-technology pathways
    3. meaningful two-technology hybrids

    Important
    ---------
    This function does not perform feasibility validation itself.

    It only combines technologies already supplied by the upstream
    technical engine. Detailed filtering and validation happen later in
    `generate_scenarios()`.

    Parameters
    ----------
    feasible_technologies:
        Technology outputs already considered technically feasible by the
        upstream engineering layer.

    minimum_scenarios:
        Minimum number of final candidates requested.

    maximum_scenarios:
        Hard upper bound to prevent uncontrolled combinatorial growth.

    include_biomass_scenarios:
        Whether biomass-aware pathway ordering should be used.

    Returns
    -------
    list[dict[str, Any]]
        Candidate pathway records.
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

    records = normalize_feasible_technologies(
        feasible_technologies
    )

    if not records:
        return []

    candidates: list[dict[str, Any]] = []

    # ---------------------------------------------------------
    # 1. Biomass-only candidates
    # ---------------------------------------------------------

    if include_biomass_scenarios:

        biomass_records = [
            record
            for record in records
            if _is_biomass(record)
        ]

        for biomass in biomass_records:

            candidates.append(
                build_pathway(
                    [biomass],
                    pathway_type="biomass_only",
                    reason=(
                        "Biomass pathway generated from a "
                        "technically feasible biomass technology."
                    ),
                    metadata=_biomass_metadata(
                        biomass
                    ),
                )
            )

            if len(candidates) >= maximum_scenarios:
                return candidates[:maximum_scenarios]

    # ---------------------------------------------------------
    # 2. Single technology candidates
    # ---------------------------------------------------------

    for technology in records:

        if _is_biomass(technology):
            pathway_type = "biomass_only"

        elif _is_biogas(technology):
            pathway_type = "biogas_only"

        else:
            pathway_type = "single_technology"

        candidate = build_pathway(
            [technology],
            pathway_type=pathway_type,
            metadata={
                "biomass_aware": _is_biomass(technology),
                "biogas_aware": _is_biogas(technology),
            },
        )

        candidates.append(candidate)

        if len(candidates) >= maximum_scenarios:
            return candidates[:maximum_scenarios]

    # ---------------------------------------------------------
    # 3. Meaningful two-technology hybrids
    # ---------------------------------------------------------

    for technology_a, technology_b in combinations(
        records,
        2,
    ):
        a_biomass = _is_biomass(technology_a)
        b_biomass = _is_biomass(technology_b)

        a_biogas = _is_biogas(technology_a)
        b_biogas = _is_biogas(technology_b)

        # Biomass and biogas are both alternative fuel pathways.
        # Do not manufacture a default hybrid between two fuel choices.
        if (a_biomass and b_biogas) or (
            a_biogas and b_biomass
        ):
            continue

        if a_biomass or b_biomass:
            pathway_type = "biomass_hybrid"

        elif a_biogas or b_biogas:
            pathway_type = "biogas_hybrid"

        else:
            pathway_type = "technology_hybrid"

        metadata: dict[str, Any] = {
            "biomass_aware": (
                a_biomass or b_biomass
            ),
            "biogas_aware": (
                a_biogas or b_biogas
            ),
        }

        if a_biomass:
            metadata.update(
                _biomass_metadata(
                    technology_a
                )
            )

        if b_biomass:
            metadata.update(
                _biomass_metadata(
                    technology_b
                )
            )

        candidates.append(
            build_pathway(
                [
                    technology_a,
                    technology_b,
                ],
                pathway_type=pathway_type,
                reason=(
                    "Hybrid pathway formed from two "
                    "technically feasible technologies."
                ),
                metadata=metadata,
            )
        )

        if len(candidates) >= maximum_scenarios:
            return candidates[:maximum_scenarios]

    return candidates[:maximum_scenarios]


# ---------------------------------------------------------------------------
# Generation utilities
# ---------------------------------------------------------------------------


def deduplicate_scenarios(
    scenarios: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    Remove duplicate scenario pathways while preserving order.
    """

    unique: list[dict[str, Any]] = []
    seen: set[tuple[str, ...]] = set()

    for scenario in scenarios:

        try:
            key = _scenario_key(scenario)
        except (TypeError, ValueError):
            continue

        if not key or key in seen:
            continue

        seen.add(key)
        unique.append(scenario)

    return unique


def validate_scenario_list_structure(
    scenarios: list[dict[str, Any]],
) -> None:
    """
    Validate the structural shape expected by downstream modules.

    Raises
    ------
    ValueError
        When a scenario is malformed.
    """

    for index, scenario in enumerate(scenarios):

        if not isinstance(scenario, dict):
            raise ValueError(
                f"Scenario at index {index} must be a dictionary."
            )

        sequence = scenario.get(
            "technology_sequence"
        )

        if sequence is None:
            sequence = scenario.get(
                "technologies"
            )

        if not isinstance(sequence, list):
            raise ValueError(
                f"Scenario at index {index} must contain a "
                "'technology_sequence' list."
            )

        if not sequence:
            raise ValueError(
                f"Scenario at index {index} contains no technologies."
            )


# ---------------------------------------------------------------------------
# Final public API
# ---------------------------------------------------------------------------


def generate_scenarios(
    feasible_technologies: list[Any],
    *,
    industry: str | None = None,
    minimum_scenarios: int = 3,
    maximum_scenarios: int = 5,
    include_biomass_scenarios: bool = True,
    strict: bool = False,
) -> dict[str, Any]:
    """
    Final public Scenario Generator API.

    Pipeline
    --------
    feasible technologies
        -> generate candidates
        -> deduplicate
        -> scenario filter
        -> scenario validation
        -> validated feasible scenarios

    Parameters
    ----------
    feasible_technologies:
        Upstream technology outputs that are already technically feasible.

    industry:
        Optional factory industry identifier used by the scenario filter
        when industry-specific technology rules are available.

    minimum_scenarios:
        Minimum number of VALID scenarios desired.

    maximum_scenarios:
        Maximum number of scenarios retained at each stage.

    include_biomass_scenarios:
        Enables biomass-aware candidate ordering.

    strict:
        If True, raise an exception when fewer than `minimum_scenarios`
        valid scenarios survive.

        If False, return all valid scenarios and an explanatory status.

    Returns
    -------
    dict[str, Any]

    Example
    -------
    {
        "scenarios": [...],
        "candidate_count": 5,
        "filtered_count": 4,
        "valid_count": 3,
        "rejected_count": 2,
        "feasible": True,
        "status": "ok",
        "rejections": [...]
    }

    Important
    ---------
    The returned `scenarios` list contains ONLY scenarios that survived
    both filtering and validation.

    No fabricated scenario is inserted merely to reach the requested
    minimum.
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

    # ---------------------------------------------------------
    # Stage 0 — normalise upstream inputs
    # ---------------------------------------------------------

    technology_records = normalize_feasible_technologies(
        feasible_technologies
    )

    if not technology_records:
        result = {
            "scenarios": [],
            "candidate_count": 0,
            "filtered_count": 0,
            "valid_count": 0,
            "rejected_count": 0,
            "feasible": False,
            "status": "no_feasible_technologies",
            "rejections": [],
            "industry": industry,
        }

        if strict:
            raise ValueError(
                "No feasible technologies were supplied; "
                "no scenarios can be generated."
            )

        return result

    # ---------------------------------------------------------
    # Stage 1 — candidate generation
    # ---------------------------------------------------------

    candidates = generate_candidate_pathways(
        technology_records,
        minimum_scenarios=minimum_scenarios,
        maximum_scenarios=maximum_scenarios,
        include_biomass_scenarios=include_biomass_scenarios,
    )

    candidates = deduplicate_scenarios(
        candidates
    )

    validate_scenario_list_structure(
        candidates
    )

    # ---------------------------------------------------------
    # Stage 2 — scenario filtering
    # ---------------------------------------------------------

    filtered = filter_scenario_combinations(
        candidates=candidates,
        industry=industry,
    )

    filtered = deduplicate_scenarios(
        filtered
    )

    # Keep the upper bound deterministic.
    filtered = filtered[:maximum_scenarios]

    # ---------------------------------------------------------
    # Stage 3 — detailed validation
    # ---------------------------------------------------------

    valid_scenarios: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []

    for candidate in filtered:

        is_valid, reasons = validate_scenario(
            candidate
        )

        if is_valid:

            # Force the downstream contract to explicitly state that
            # this scenario survived the complete generation pipeline.
            validated_candidate = dict(candidate)
            validated_candidate["feasible"] = True
            validated_candidate["validation"] = {
                "valid": True,
                "reasons": [],
            }

            valid_scenarios.append(
                validated_candidate
            )

        else:

            rejected.append(
                {
                    "stage": "validation",
                    "candidate": candidate,
                    "reasons": reasons,
                }
            )

    # ---------------------------------------------------------
    # Stage 4 — determine result state
    # ---------------------------------------------------------

    valid_count = len(valid_scenarios)

    if valid_count >= minimum_scenarios:
        status = "ok"
        feasible = True

    elif valid_count > 0:
        status = "partial"
        feasible = True

    else:
        status = "no_valid_scenarios"
        feasible = False

    # We do not invent additional scenarios when the validated
    # set is smaller than the requested minimum.
    if strict and valid_count < minimum_scenarios:
        raise ValueError(
            (
                f"Scenario generation produced only "
                f"{valid_count} valid scenario(s), but "
                f"{minimum_scenarios} were requested."
            )
        )

    return {
        "scenarios": valid_scenarios[:maximum_scenarios],
        "candidate_count": len(candidates),
        "filtered_count": len(filtered),
        "valid_count": valid_count,
        "rejected_count": len(rejected),
        "feasible": feasible,
        "status": status,
        "rejections": rejected,
        "industry": industry,
        "generator_config": {
            "minimum_scenarios": minimum_scenarios,
            "maximum_scenarios": maximum_scenarios,
            "include_biomass_scenarios": (
                include_biomass_scenarios
            ),
            "strict": strict,
        },
    }


# ---------------------------------------------------------------------------
# Backward-compatible Biogas API
# ---------------------------------------------------------------------------


def generate_biogas_scenario(
    heat_demand_kwh_day: float,
    biogas_energy_content_kwh_m3: float,
    boiler_efficiency: float,
    biogas_emission_factor_kg_co2_m3: float,
) -> dict[str, Any]:
    """
    Preserve the existing standalone biogas scenario API.

    This remains intentionally independent from the generic scenario
    orchestration API because it is a legacy/prototype calculation used
    by existing callers.
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
        heat_demand_kwh_day
        / boiler_efficiency
    )

    biogas_required_m3_day = (
        required_input_energy_kwh_day
        / biogas_energy_content_kwh_m3
    )

    co2_kg_day = (
        biogas_required_m3_day
        * biogas_emission_factor_kg_co2_m3
    )

    return {
        "scenario": "biogas_replacement",
        "replacement_technology": "biogas",
        "heat_demand_kwh_day": heat_demand_kwh_day,
        "biogas_required_m3_day": biogas_required_m3_day,
        "co2_kg_day": co2_kg_day,
        "co2_tco2_day": co2_kg_day / 1000.0,
        "feasible": True,
    }


# ---------------------------------------------------------------------------
# Public exports
# ---------------------------------------------------------------------------


__all__ = [
    "normalize_feasible_technologies",
    "build_pathway",
    "generate_candidate_pathways",
    "deduplicate_scenarios",
    "validate_scenario_list_structure",
    "generate_scenarios",
    "generate_biogas_scenario",
]




from __future__ import annotations

from dataclasses import dataclass, field
from itertools import combinations
from typing import Any, Iterable, Mapping, Sequence


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

DEFAULT_MIN_SCENARIOS = 3
DEFAULT_MAX_SCENARIOS = 5

PATHWAY_TYPES = {
    "single",
    "efficiency_plus_heat",
    "biomass_hybrid",
    "electrification_hybrid",
    "solar_hybrid",
    "storage_hybrid",
    "resource_hybrid",
}

THERMAL_TECH_KEYWORDS = (
    "boiler",
    "furnace",
    "heat_pump",
    "electric_boiler",
    "induction",
    "eaf",
    "plasma",
    "microwave",
    "rf_heater",
    "infrared",
    "mvr",
    "thermal",
    "biomass",
    "biogas",
)

EFFICIENCY_KEYWORDS = (
    "vfd",
    "motor",
    "whr",
    "waste_heat",
    "heat_recovery",
    "efficiency",
)

SOLAR_KEYWORDS = (
    "solar",
    "pv",
)

STORAGE_KEYWORDS = (
    "battery",
    "thermal_storage",
    "thermal_battery",
)

BIOMASS_KEYWORDS = (
    "biomass",
)


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class EvidenceFlags:
    """
    Summarizes upstream evidence available for a technology/pathway.

    This is deliberately descriptive rather than prescriptive.
    """

    technically_feasible: bool = False
    policy_eligible: bool = False

    resource_feasible: bool = True
    biomass_available: bool | None = None
    tariff_supported: bool | None = None
    industry_supported: bool = True
    financially_feasible: bool | None = None

    reasons: tuple[str, ...] = ()

    @property
    def fully_feasible(self) -> bool:
        """
        Return True only when all required upstream checks are satisfied.
        """

        if not self.technically_feasible:
            return False

        if not self.policy_eligible:
            return False

        if not self.resource_feasible:
            return False

        if not self.industry_supported:
            return False

        if self.biomech_unsupported():
            return False

        if self.financially_feasible is False:
            return False

        return True

    def biomech_unsupported(self) -> bool:
        """
        Biomass-specific validity helper.

        Biomass technologies require explicit availability evidence.
        A non-biomass technology is unaffected.
        """

        return self.biomass_available is False


@dataclass
class TechnologyCandidate:
    """
    Normalized technology candidate consumed by the hybrid generator.

    The generator supports dictionaries so it can connect cleanly to
    the current engineering engine without forcing a new domain model.
    """

    technology_id: str
    technology_type: str = "other"

    technically_feasible: bool = True
    policy_eligible: bool = True
    industry_supported: bool = True
    resource_feasible: bool = True

    biomass_available: bool | None = None
    tariff_supported: bool | None = None
    financially_feasible: bool | None = None

    capex_inr: float | None = None
    annual_cost_inr: float | None = None
    payback_years: float | None = None

    temperature_max_c: float | None = None
    required_capacity_kw: float | None = None

    evidence: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def normalized_id(self) -> str:
        return self.technology_id.strip().lower()

    @property
    def is_biomass(self) -> bool:
        return _contains_keyword(
            self.technology_id,
            BIOMASS_KEYWORDS,
        ) or self.technology_type.lower() == "biomass"

    @property
    def is_solar(self) -> bool:
        return _contains_keyword(
            self.technology_id,
            SOLAR_KEYWORDS,
        )

    @property
    def is_storage(self) -> bool:
        return _contains_keyword(
            self.technology_id,
            STORAGE_KEYWORDS,
        )

    @property
    def is_efficiency(self) -> bool:
        return _contains_keyword(
            self.technology_id,
            EFFICIENCY_KEYWORDS,
        )

    @property
    def is_thermal(self) -> bool:
        return _contains_keyword(
            self.technology_id,
            THERMAL_TECH_KEYWORDS,
        )

    @property
    def evidence_flags(self) -> EvidenceFlags:
        return EvidenceFlags(
            technically_feasible=self.technically_feasible,
            policy_eligible=self.policy_eligible,
            resource_feasible=self.resource_feasible,
            biomass_available=self.biomass_available,
            tariff_supported=self.tariff_supported,
            industry_supported=self.industry_supported,
            financially_feasible=self.financially_feasible,
            reasons=tuple(
                _extract_reasons(self.evidence)
            ),
        )

    @property
    def usable(self) -> bool:
        """
        Decide whether this technology can participate in a generated
        pathway.

        The scenario layer is intentionally strict:
        unsupported or rejected technologies must not re-enter through
        scenario generation.
        """

        if not self.technically_feasible:
            return False

        if not self.policy_eligible:
            return False

        if not self.industry_supported:
            return False

        if not self.resource_feasible:
            return False

        if self.financially_feasible is False:
            return False

        if self.is_biomass and self.biomass_available is False:
            return False

        return True


@dataclass
class HybridScenario:
    """
    Candidate transition pathway.

    This is deliberately lighter than the final Scenario domain model.
    Economics, emissions, reliability, and MCDA ranking remain downstream.
    """

    scenario_id: str
    factory_id: str
    technology_sequence: list[str]

    pathway_type: str

    feasible: bool = True

    rationale: list[str] = field(default_factory=list)
    provenance: dict[str, Any] = field(default_factory=dict)

    biomass_used: bool = False
    solar_used: bool = False
    storage_used: bool = False
    efficiency_used: bool = False

    upstream_evidence: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        """
        Convert to the project-friendly pathway contract.
        """

        return {
            "scenario_id": self.scenario_id,
            "factory_id": self.factory_id,
            "technologies": list(self.technology_sequence),
            "technology_sequence": list(self.technology_sequence),
            "pathway_type": self.pathway_type,
            "feasible": self.feasible,
            "rationale": list(self.rationale),
            "provenance": dict(self.provenance),
            "biomass_used": self.biomass_used,
            "solar_used": self.solar_used,
            "storage_used": self.storage_used,
            "efficiency_used": self.efficiency_used,
            "upstream_evidence": dict(self.upstream_evidence),
        }


# ---------------------------------------------------------------------------
# General helpers
# ---------------------------------------------------------------------------


def _contains_keyword(
    value: str,
    keywords: Iterable[str],
) -> bool:
    """
    Case-insensitive substring keyword check.
    """

    normalized = value.strip().lower()

    return any(
        keyword in normalized
        for keyword in keywords
    )


def _extract_reasons(
    evidence: Mapping[str, Any],
) -> list[str]:
    """
    Extract human-readable evidence/rejection reasons from upstream data.
    """

    if not evidence:
        return []

    result: list[str] = []

    for key in (
        "reason",
        "reasons",
        "rejection_reason",
        "rejection_reasons",
        "notes",
    ):
        value = evidence.get(key)

        if isinstance(value, str) and value.strip():
            result.append(value.strip())

        elif isinstance(value, Sequence) and not isinstance(value, str):
            result.extend(
                str(item).strip()
                for item in value
                if str(item).strip()
            )

    return result


def _first_present(
    mapping: Mapping[str, Any],
    keys: Sequence[str],
    default: Any = None,
) -> Any:
    """
    Return the first non-None value among candidate keys.
    """

    for key in keys:
        value = mapping.get(key)

        if value is not None:
            return value

    return default


def _coerce_bool(
    value: Any,
    default: bool | None = None,
) -> bool | None:
    """
    Safely normalize common boolean encodings.
    """

    if value is None:
        return default

    if isinstance(value, bool):
        return value

    if isinstance(value, (int, float)):
        return bool(value)

    if isinstance(value, str):
        normalized = value.strip().lower()

        if normalized in {
            "true",
            "yes",
            "y",
            "available",
            "eligible",
            "feasible",
            "supported",
            "pass",
        }:
            return True

        if normalized in {
            "false",
            "no",
            "n",
            "unavailable",
            "ineligible",
            "infeasible",
            "unsupported",
            "fail",
        }:
            return False

    return default


def _coerce_float(
    value: Any,
    default: float | None = None,
) -> float | None:
    """
    Safely normalize numeric values.
    """

    if value is None:
        return default

    if isinstance(value, bool):
        return default

    try:
        return float(value)
    except (TypeError, ValueError):
        return default


# ---------------------------------------------------------------------------
# Candidate normalization
# ---------------------------------------------------------------------------


def normalize_candidate(
    item: Any,
) -> TechnologyCandidate:
    """
    Normalize technology output from the existing technology engine.

    Supported inputs include:
        "TECH_BIOMASS_BOILER_1_10TPH"

    and dictionaries such as:
        {
            "technology_id": "...",
            "technically_feasible": True,
            ...
        }
    """

    if isinstance(item, str):
        technology_id = item.strip()

        if not technology_id:
            raise ValueError(
                "Technology ID cannot be empty."
            )

        return TechnologyCandidate(
            technology_id=technology_id,
        )

    if not isinstance(item, Mapping):
        raise TypeError(
            "Technology candidate must be a string or mapping."
        )

    technology_id = _first_present(
        item,
        (
            "technology_id",
            "id",
            "technology",
            "technology_name",
        ),
    )

    if not isinstance(technology_id, str):
        raise ValueError(
            f"Missing technology identifier in {item!r}"
        )

    technology_type = _first_present(
        item,
        (
            "technology_type",
            "type",
            "resource_type",
            "fuel_type",
        ),
        "other",
    )

    evidence = _first_present(
        item,
        (
            "evidence",
            "source_evidence",
            "technical_evidence",
        ),
        {},
    )

    metadata = _first_present(
        item,
        (
            "metadata",
            "scenario_metadata",
        ),
        {},
    )

    return TechnologyCandidate(
        technology_id=technology_id.strip(),
        technology_type=str(technology_type),
        technically_feasible=_coerce_bool(
            _first_present(
                item,
                (
                    "technically_feasible",
                    "technical_feasible",
                    "feasible",
                ),
            ),
            True,
        )
        is True,
        policy_eligible=_coerce_bool(
            _first_present(
                item,
                (
                    "policy_eligible",
                    "eligible",
                    "policy_feasible",
                ),
            ),
            True,
        )
        is not False,
        industry_supported=_coerce_bool(
            _first_present(
                item,
                (
                    "industry_supported",
                    "industry_compatible",
                    "sector_supported",
                ),
            ),
            True,
        )
        is not False,
        resource_feasible=_coerce_bool(
            _first_present(
                item,
                (
                    "resource_feasible",
                    "resource_available",
                    "resource_supported",
                ),
            ),
            True,
        )
        is not False,
        biomass_available=_coerce_bool(
            _first_present(
                item,
                (
                    "biomass_available",
                    "available_biomass",
                    "biomass_availability",
                ),
            )
        ),
        tariff_supported=_coerce_bool(
            _first_present(
                item,
                (
                    "tariff_supported",
                    "tariff_feasible",
                    "energy_price_supported",
                ),
            )
        ),
        financially_feasible=_coerce_bool(
            _first_present(
                item,
                (
                    "financially_feasible",
                    "finance_feasible",
                    "economic_feasible",
                ),
            )
        ),
        capex_inr=_coerce_float(
            _first_present(
                item,
                (
                    "capex_inr",
                    "capex",
                ),
            )
        ),
        annual_cost_inr=_coerce_float(
            _first_present(
                item,
                (
                    "annual_cost_inr",
                    "annual_opex_inr",
                    "annual_cost",
                ),
            )
        ),
        payback_years=_coerce_float(
            _first_present(
                item,
                (
                    "payback_years",
                    "payback",
                ),
            )
        ),
        temperature_max_c=_coerce_float(
            _first_present(
                item,
                (
                    "temperature_max_c",
                    "max_temperature_c",
                    "temperature_limit_c",
                ),
            )
        ),
        required_capacity_kw=_coerce_float(
            _first_present(
                item,
                (
                    "required_capacity_kw",
                    "capacity_kw",
                ),
            )
        ),
        evidence=dict(evidence)
        if isinstance(evidence, Mapping)
        else {},
        metadata=dict(metadata)
        if isinstance(metadata, Mapping)
        else {},
    )


def normalize_candidates(
    candidates: Iterable[Any],
) -> list[TechnologyCandidate]:
    """
    Normalize and deduplicate candidates.

    The first occurrence wins so upstream provenance remains stable.
    """

    normalized: list[TechnologyCandidate] = []
    seen: set[str] = set()

    for item in candidates:
        try:
            candidate = normalize_candidate(item)
        except (TypeError, ValueError):
            continue

        if candidate.normalized_id in seen:
            continue

        seen.add(candidate.normalized_id)

        if candidate.usable:
            normalized.append(candidate)

    return normalized


# ---------------------------------------------------------------------------
# Hybrid compatibility rules
# ---------------------------------------------------------------------------


def _has_full_load_thermal_technology(
    candidates: Sequence[TechnologyCandidate],
) -> bool:
    """
    Detect whether a pathway already contains a primary heat technology.
    """

    thermal_candidates = [
        item
        for item in candidates
        if item.is_thermal
    ]

    return bool(thermal_candidates)


def _is_primary_thermal(
    candidate: TechnologyCandidate,
) -> bool:
    """
    Determine whether a candidate is probably the main thermal supply.

    This is intentionally conservative and string/rule based.
    """

    identifier = candidate.technology_id.lower()

    primary_terms = (
        "boiler",
        "furnace",
        "heat_pump",
        "electric_boiler",
        "induction",
        "eaf",
        "plasma",
        "mvr",
        "thermal_battery",
    )

    return any(
        term in identifier
        for term in primary_terms
    )


def _compatible_pair(
    first: TechnologyCandidate,
    second: TechnologyCandidate,
) -> tuple[bool, str]:
    """
    Determine whether a two-technology hybrid is meaningful.

    The rules deliberately reject obvious nonsense while leaving
    detailed engineering compatibility to the scenario validator.
    """

    if first.normalized_id == second.normalized_id:
        return (
            False,
            "Duplicate technology in pathway.",
        )

    if (
        first.is_biomass
        and second.is_biomass
    ):
        return (
            False,
            "Duplicate biomass role; use one biomass pathway candidate.",
        )

    if (
        first.is_thermal
        and second.is_thermal
        and _is_primary_thermal(first)
        and _is_primary_thermal(second)
    ):
        return (
            False,
            "Two primary thermal technologies were combined without an explicit hybrid-load rule.",
        )

    if (
        first.is_biomass
        and second.technology_type.lower() == "biogas"
    ) or (
        second.is_biomass
        and first.technology_type.lower() == "biogas"
    ):
        return (
            False,
            "Biomass and biogas are treated as alternative fuel pathways unless an explicit multi-fuel rule exists.",
        )

    return True, ""


# ---------------------------------------------------------------------------
# Pathway classification
# ---------------------------------------------------------------------------


def classify_pathway(
    technologies: Sequence[TechnologyCandidate],
) -> str:
    """
    Assign a transparent pathway class.
    """

    if not technologies:
        return "single"

    biomass = any(
        item.is_biomass
        for item in technologies
    )

    solar = any(
        item.is_solar
        for item in technologies
    )

    storage = any(
        item.is_storage
        for item in technologies
    )

    efficiency = any(
        item.is_efficiency
        for item in technologies
    )

    if biomass and len(technologies) > 1:
        return "biomass_hybrid"

    if solar and len(technologies) > 1:
        return "solar_hybrid"

    if storage and len(technologies) > 1:
        return "storage_hybrid"

    if efficiency and any(
        item.is_thermal
        for item in technologies
    ):
        return "efficiency_plus_heat"

    if any(
        item.is_thermal
        for item in technologies
    ) and len(technologies) > 1:
        return "electrification_hybrid"

    if len(technologies) > 1:
        return "resource_hybrid"

    return "single"


# ---------------------------------------------------------------------------
# Evidence-aware pathway rules
# ---------------------------------------------------------------------------


def _pathway_resource_check(
    technologies: Sequence[TechnologyCandidate],
) -> tuple[bool, list[str]]:
    """
    Check resource-related evidence.

    Biomass is special: it should not enter a scenario merely because
    a biomass technology exists in the technology library.
    """

    reasons: list[str] = []

    for technology in technologies:
        if not technology.is_biomass:
            continue

        if technology.biomass_available is False:
            reasons.append(
                f"{technology.technology_id}: biomass availability failed upstream."
            )

        elif technology.biomass_available is None:
            reasons.append(
                f"{technology.technology_id}: biomass availability evidence is missing."
            )

    return (
        not reasons,
        reasons,
    )


def _pathway_tariff_check(
    technologies: Sequence[TechnologyCandidate],
) -> tuple[bool, list[str]]:
    """
    Validate tariff evidence where technology economics explicitly
    depend on electricity pricing.

    A missing tariff flag does not automatically reject a pathway,
    because the economics engine may calculate the tariff later.
    An explicit negative result does reject it.
    """

    reasons: list[str] = []

    for technology in technologies:
        if technology.tariff_supported is False:
            reasons.append(
                f"{technology.technology_id}: tariff/electricity-price feasibility failed upstream."
            )

    return (
        not reasons,
        reasons,
    )


def _pathway_finance_check(
    technologies: Sequence[TechnologyCandidate],
) -> tuple[bool, list[str]]:
    """
    Enforce explicit upstream financial infeasibility.

    Missing financial information is allowed because the economics
    layer owns final economic calculations.
    """

    reasons: list[str] = []

    for technology in technologies:
        if technology.financially_feasible is False:
            reasons.append(
                f"{technology.technology_id}: financial feasibility failed upstream."
            )

    return (
        not reasons,
        reasons,
    )


# ---------------------------------------------------------------------------
# Scenario construction
# ---------------------------------------------------------------------------


def _build_scenario(
    factory_id: str,
    technologies: Sequence[TechnologyCandidate],
    *,
    scenario_index: int,
    pathway_reason: str,
) -> HybridScenario:
    """
    Build a single candidate pathway with explainable provenance.
    """

    technology_ids = [
        technology.technology_id
        for technology in technologies
    ]

    pathway_type = classify_pathway(
        technologies
    )

    rationale = [
        pathway_reason,
        "All included technologies passed upstream usability checks.",
    ]

    resource_ok, resource_reasons = _pathway_resource_check(
        technologies
    )

    tariff_ok, tariff_reasons = _pathway_tariff_check(
        technologies
    )

    finance_ok, finance_reasons = _pathway_finance_check(
        technologies
    )

    all_reasons = [
        *resource_reasons,
        *tariff_reasons,
        *finance_reasons,
    ]

    feasible = (
        resource_ok
        and tariff_ok
        and finance_ok
    )

    if all_reasons:
        rationale.extend(all_reasons)

    evidence = {
        "technology_checks": {
            technology.technology_id: {
                "technically_feasible": (
                    technology.technically_feasible
                ),
                "policy_eligible": (
                    technology.policy_eligible
                ),
                "industry_supported": (
                    technology.industry_supported
                ),
                "resource_feasible": (
                    technology.resource_feasible
                ),
                "biomass_available": (
                    technology.biomass_available
                ),
                "tariff_supported": (
                    technology.tariff_supported
                ),
                "financially_feasible": (
                    technology.financially_feasible
                ),
                "evidence": dict(
                    technology.evidence
                ),
            }
            for technology in technologies
        }
    }

    return HybridScenario(
        scenario_id=f"HS-{scenario_index:03d}",
        factory_id=factory_id,
        technology_sequence=technology_ids,
        pathway_type=pathway_type,
        feasible=feasible,
        rationale=rationale,
        provenance={
            "source": "hybrid_scenario_generator",
            "technology_ids": technology_ids,
            "generation_reason": pathway_reason,
        },
        biomass_used=any(
            technology.is_biomass
            for technology in technologies
        ),
        solar_used=any(
            technology.is_solar
            for technology in technologies
        ),
        storage_used=any(
            technology.is_storage
            for technology in technologies
        ),
        efficiency_used=any(
            technology.is_efficiency
            for technology in technologies
        ),
        upstream_evidence=evidence,
    )


# ---------------------------------------------------------------------------
# Hybrid pattern generation
# ---------------------------------------------------------------------------


def _generate_priority_patterns(
    candidates: Sequence[TechnologyCandidate],
) -> list[tuple[list[TechnologyCandidate], str]]:
    """
    Generate only meaningful hybrid patterns.

    Priority:
        1. efficiency + thermal
        2. biomass + supporting technology
        3. solar + thermal
        4. thermal + storage
        5. generic compatible hybrid

    This ordering is intentional. It gives the optimizer meaningful
    transition structures instead of arbitrary combinations.
    """

    patterns: list[tuple[list[TechnologyCandidate], str]] = []

    efficiency = [
        item
        for item in candidates
        if item.is_efficiency
    ]

    thermal = [
        item
        for item in candidates
        if item.is_thermal
    ]

    biomass = [
        item
        for item in candidates
        if item.is_biomass
    ]

    solar = [
        item
        for item in candidates
        if item.is_solar
    ]

    storage = [
        item
        for item in candidates
        if item.is_storage
    ]

    # Efficiency + heat
    for first in efficiency:
        for second in thermal:
            valid, _ = _compatible_pair(
                first,
                second,
            )

            if valid:
                patterns.append(
                    (
                        [first, second],
                        "Efficiency improvement combined with a feasible thermal transition.",
                    )
                )

    # Biomass + support
    for first in biomass:
        support_candidates = [
            item
            for item in candidates
            if item.normalized_id != first.normalized_id
            and not item.is_biomass
            and not (
                item.is_thermal
                and _is_primary_thermal(item)
            )
        ]

        for second in support_candidates:
            valid, _ = _compatible_pair(
                first,
                second,
            )

            if valid:
                patterns.append(
                    (
                        [first, second],
                        "Biomass-based heat paired with a complementary feasible technology.",
                    )
                )

    # Solar + thermal
    for first in solar:
        for second in thermal:
            valid, _ = _compatible_pair(
                first,
                second,
            )

            if valid:
                patterns.append(
                    (
                        [second, first],
                        "Thermal technology supported by feasible solar-electric supply.",
                    )
                )

    # Thermal + storage
    for first in thermal:
        for second in storage:
            valid, _ = _compatible_pair(
                first,
                second,
            )

            if valid:
                patterns.append(
                    (
                        [first, second],
                        "Thermal pathway supported by compatible energy storage.",
                    )
                )

    # Generic compatible combinations
    for first, second in combinations(
        candidates,
        2,
    ):
        valid, _ = _compatible_pair(
            first,
            second,
        )

        if not valid:
            continue

        pattern = (
            [first, second],
            "Two feasible technologies form a complementary hybrid pathway.",
        )

        if pattern not in patterns:
            patterns.append(pattern)

    return patterns


# ---------------------------------------------------------------------------
# Main public API
# ---------------------------------------------------------------------------


def generate_hybrid_scenarios(
    factory: Mapping[str, Any],
    feasible_technologies: Sequence[Any],
    *,
    minimum_scenarios: int = DEFAULT_MIN_SCENARIOS,
    maximum_scenarios: int = DEFAULT_MAX_SCENARIOS,
    include_single_technology: bool = True,
) -> list[dict[str, Any]]:
    """
    Generate research-grounded hybrid scenarios.

    Parameters
    ----------
    factory:
        Factory input or factory-like mapping.

        Required:
            factory_id OR id

        Recommended:
            industry
            state/location
            process temperature
            budget
            biomass/resource metadata
            tariff metadata

        These values are preserved in provenance but are NOT recreated
        or guessed here.

    feasible_technologies:
        Technology outputs already screened by the technology and
        constraint/policy layers.

    minimum_scenarios:
        Minimum acceptable number of pathways.

    maximum_scenarios:
        Maximum number of pathways.

    include_single_technology:
        Whether a single technology pathway may be included as a
        fallback/benchmark.

    Returns
    -------
    list[dict[str, Any]]
        Feasible candidate pathways, ordered by generation priority.

    Raises
    ------
    ValueError
        If insufficient valid pathways can be generated.

    Design guarantee
    ----------------
    This function NEVER creates a pathway using a technology that is
    explicitly marked infeasible, policy-ineligible, resource-infeasible,
    or financially infeasible upstream.
    """

    if minimum_scenarios < 1:
        raise ValueError(
            "minimum_scenarios must be at least 1."
        )

    if maximum_scenarios < minimum_scenarios:
        raise ValueError(
            "maximum_scenarios cannot be smaller than minimum_scenarios."
        )

    factory_id = _first_present(
        factory,
        (
            "factory_id",
            "id",
        ),
    )

    if factory_id is None:
        factory_id = "FACTORY_UNSPECIFIED"

    candidates = normalize_candidates(
        feasible_technologies
    )

    if not candidates:
        raise ValueError(
            "No usable feasible technologies were provided."
        )

    scenarios: list[HybridScenario] = []

    # ------------------------------------------------------------------
    # 1. Single-technology candidates
    # ------------------------------------------------------------------

    if include_single_technology:
        for candidate in candidates:
            scenario = _build_scenario(
                str(factory_id),
                [candidate],
                scenario_index=len(scenarios) + 1,
                pathway_reason=(
                    "Single-techn​ology pathway retained as a direct "
                    "benchmark against hybrid alternatives."
                ),
            )

            if scenario.feasible:
                scenarios.append(
                    scenario
                )

            if len(scenarios) >= maximum_scenarios:
                break

    # ------------------------------------------------------------------
    # 2. Priority hybrid candidates
    # ------------------------------------------------------------------

    if len(scenarios) < maximum_scenarios:
        patterns = _generate_priority_patterns(
            candidates
        )

        for technologies, reason in patterns:
            scenario = _build_scenario(
                str(factory_id),
                technologies,
                scenario_index=len(scenarios) + 1,
                pathway_reason=reason,
            )

            if not scenario.feasible:
                continue

            duplicate = any(
                tuple(existing.technology_sequence)
                == tuple(scenario.technology_sequence)
                for existing in scenarios
            )

            if duplicate:
                continue

            scenarios.append(
                scenario
            )

            if len(scenarios) >= maximum_scenarios:
                break

    # ------------------------------------------------------------------
    # 3. Controlled three-technology hybrid
    # ------------------------------------------------------------------

    if len(scenarios) < maximum_scenarios:
        for first, second, third in combinations(
            candidates,
            3,
        ):
            pair_one_valid, _ = _compatible_pair(
                first,
                second,
            )
            pair_two_valid, _ = _compatible_pair(
                first,
                third,
            )
            pair_three_valid, _ = _compatible_pair(
                second,
                third,
            )

            if not (
                pair_one_valid
                and pair_two_valid
                and pair_three_valid
            ):
                continue

            technologies = [
                first,
                second,
                third,
            ]

            # At least one resource/efficiency/solar/storage role
            # should complement the primary technology.
            role_types = {
                (
                    "biomass"
                    if item.is_biomass
                    else "solar"
                    if item.is_solar
                    else "storage"
                    if item.is_storage
                    else "efficiency"
                    if item.is_efficiency
                    else "thermal"
                    if item.is_thermal
                    else "other"
                )
                for item in technologies
            }

            if len(role_types) < 2:
                continue

            scenario = _build_scenario(
                str(factory_id),
                technologies,
                scenario_index=len(scenarios) + 1,
                pathway_reason=(
                    "Three-technology hybrid retained because the "
                    "technologies provide complementary pathway roles."
                ),
            )

            if not scenario.feasible:
                continue

            duplicate = any(
                set(existing.technology_sequence)
                == set(scenario.technology_sequence)
                for existing in scenarios
            )

            if duplicate:
                continue

            scenarios.append(
                scenario
            )

            if len(scenarios) >= maximum_scenarios:
                break

    # ------------------------------------------------------------------
    # 4. Never fabricate scenarios just to hit the requested count
    # ------------------------------------------------------------------

    if len(scenarios) < minimum_scenarios:
        raise ValueError(
            "Unable to generate the requested number of feasible "
            "research-grounded scenarios. "
            f"Generated {len(scenarios)}, "
            f"required at least {minimum_scenarios}."
        )

    # Stable numbering after filtering
    result: list[dict[str, Any]] = []

    for index, scenario in enumerate(
        scenarios[:maximum_scenarios],
        start=1,
    ):
        scenario.scenario_id = (
            f"HS-{index:03d}"
        )

        result.append(
            scenario.as_dict()
        )

    return result


# ---------------------------------------------------------------------------
# Compatibility helpers
# ---------------------------------------------------------------------------


def generate_scenarios(
    feasible_technologies: Sequence[Any],
    *,
    factory: Mapping[str, Any] | None = None,
    minimum_scenarios: int = DEFAULT_MIN_SCENARIOS,
    maximum_scenarios: int = DEFAULT_MAX_SCENARIOS,
) -> list[dict[str, Any]]:
    """
    Compatibility wrapper.

    Existing callers can continue to call:

        generate_scenarios(feasible_technologies)

    while new pipeline code can provide factory context.
    """

    return generate_hybrid_scenarios(
        factory=factory or {},
        feasible_technologies=feasible_technologies,
        minimum_scenarios=minimum_scenarios,
        maximum_scenarios=maximum_scenarios,
    )


def generate_candidate_pathways(
    feasible_technologies: Sequence[Any],
    *,
    factory: Mapping[str, Any] | None = None,
    minimum_scenarios: int = DEFAULT_MIN_SCENARIOS,
    maximum_scenarios: int = DEFAULT_MAX_SCENARIOS,
) -> list[dict[str, Any]]:
    """
    Alias aligned with the repository architecture terminology.
    """

    return generate_hybrid_scenarios(
        factory=factory or {},
        feasible_technologies=feasible_technologies,
        minimum_scenarios=minimum_scenarios,
        maximum_scenarios=maximum_scenarios,
    )


__all__ = [
    "EvidenceFlags",
    "TechnologyCandidate",
    "HybridScenario",
    "normalize_candidate",
    "normalize_candidates",
    "classify_pathway",
    "generate_hybrid_scenarios",
    "generate_scenarios",
    "generate_candidate_pathways",
]


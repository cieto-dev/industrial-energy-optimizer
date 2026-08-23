"""
Explainability Engine for the Industrial Energy Transition Optimizer.

This module converts deterministic decision-engine outputs into an
evidence-backed explanation for the final recommendation.

Design principles
-----------------
1. Independent of the optimizer implementation.
2. No LLM is used for technical, financial, policy, or ranking decisions.
3. Every explanation reason is generated from observable inputs/results.
4. Evidence is represented explicitly so downstream reports can cite it.
5. Compatible with the existing Recommendation model.
6. Defensive against different dict/dataclass/Pydantic result shapes.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field, is_dataclass
from typing import Any, Iterable, Mapping, Optional, Sequence
import math


# ---------------------------------------------------------------------------
# Part 1: Evidence models
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Evidence:
    """A traceable source supporting an explanation claim."""

    source_id: str
    source_name: str
    claim: str
    citation: str
    category: str
    confidence: str = "medium"
    source_year: Optional[int] = None
    notes: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class Reason:
    """A human-readable recommendation reason."""

    code: str
    text: str
    category: str
    importance: str = "supporting"
    evidence_ids: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "code": self.code,
            "text": self.text,
            "category": self.category,
            "importance": self.importance,
            "evidence_ids": list(self.evidence_ids),
        }


@dataclass
class RecommendationExplanation:
    """
    Standalone explanation payload.

    This object is intentionally independent from models/recommendation.py.
    The Recommendation model can consume its fields without making the
    explanation engine depend on the optimizer, policy engine, or report layer.
    """

    headline: str
    summary: str

    why_selected: list[str] = field(default_factory=list)
    why_not_cheapest: Optional[str] = None
    why_others_rejected: list[dict[str, Any]] = field(default_factory=list)

    evidence: list[Evidence] = field(default_factory=list)
    reasons: list[Reason] = field(default_factory=list)

    mcda_rationale: Optional[str] = None
    policy_rationale: Optional[str] = None
    sensitivity_rationale: Optional[str] = None

    confidence: str = "medium"
    confidence_score: float = 0.5

    citation_map: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "headline": self.headline,
            "summary": self.summary,
            "why_selected": list(self.why_selected),
            "why_not_cheapest": self.why_not_cheapest,
            "why_others_rejected": list(self.why_others_rejected),
            "evidence": [item.to_dict() for item in self.evidence],
            "reasons": [item.to_dict() for item in self.reasons],
            "mcda_rationale": self.mcda_rationale,
            "policy_rationale": self.policy_rationale,
            "sensitivity_rationale": self.sensitivity_rationale,
            "confidence": self.confidence,
            "confidence_score": self.confidence_score,
            "citation_map": dict(self.citation_map),
        }


# ---------------------------------------------------------------------------
# Part 2: Evidence library
# ---------------------------------------------------------------------------


class EvidenceLibrary:
    """
    Central evidence registry used by the explanation rules.

    These sources are based on the project's uploaded research material.
    Claims are intentionally conservative: the engine cites the existence
    and relevance of the source rather than inventing technology-specific
    performance values that the source does not establish for every factory.
    """

    def __init__(self) -> None:
        self._items: dict[str, Evidence] = {}
        self._load_default_sources()

    def _register(self, evidence: Evidence) -> None:
        self._items[evidence.source_id] = evidence

    def _load_default_sources(self) -> None:
        self._register(
            Evidence(
                source_id="flexiheat_dst_2026",
                source_name="FlexiHeat-DST",
                claim=(
                    "Industrial power-to-heat technology selection can use "
                    "multi-criteria analysis across techno-economic and "
                    "environmental parameters."
                ),
                citation=(
                    "Ashabi et al. (2026), FlexiHeat-DST, "
                    "Energy Conversion and Management: X 30, 101631."
                ),
                category="technology_selection",
                confidence="high",
                source_year=2026,
            )
        )

        self._register(
            Evidence(
                source_id="mnre_giz_biomass_2026",
                source_name="MNRE-GIZ Biomass MSME Report",
                claim=(
                    "Biomass-based green steam and heat can be applied across "
                    "multiple MSME industrial sectors, with fuel availability, "
                    "pricing, supply-chain reliability, and boiler integration "
                    "being important considerations."
                ),
                citation=(
                    "MNRE/GIZ, Decarbonizing MSMEs: Use of Biomass for "
                    "Green Steam and Heat Applications."
                ),
                category="biomass",
                confidence="high",
                source_year=2026,
            )
        )

        self._register(
            Evidence(
                source_id="national_biomass_atlas",
                source_name="National Biomass Atlas of India",
                claim=(
                    "Biomass availability varies geographically and by crop "
                    "and residue type; regional availability must therefore "
                    "be considered when evaluating biomass pathways."
                ),
                citation="Sardar Swaran Singh National Institute of Bio-Energy, National Biomass Atlas.",
                category="biomass_resource",
                confidence="high",
                source_year=2018,
            )
        )

        self._register(
            Evidence(
                source_id="niti_msme_roadmap_2026",
                source_name="NITI Aayog Roadmap for Green Transition of MSMEs",
                claim=(
                    "MSME decarbonisation requires technology adoption, "
                    "affordable finance, sector-specific pathways, and "
                    "supporting institutional and policy mechanisms."
                ),
                citation="NITI Aayog, Roadmap for Green Transition of MSMEs, January 2026.",
                category="policy_finance",
                confidence="high",
                source_year=2026,
            )
        )

        self._register(
            Evidence(
                source_id="electrifying_industrial_heat_india_2026",
                source_name="Electrifying Industrial Heat in India",
                claim=(
                    "Electrified industrial heat can be economically competitive "
                    "with fossil and biomass heat in relevant temperature bands, "
                    "while the economics depend strongly on electricity sourcing "
                    "and technology type."
                ),
                citation=(
                    "Energy Innovation / IECC, Electrifying Industrial Heat in India: "
                    "Technologies and Policies to Transform Indian Manufacturing, April 2026."
                ),
                category="electrification",
                confidence="high",
                source_year=2026,
            )
        )

        self._register(
            Evidence(
                source_id="world_bank_feemp",
                source_name="World Bank FEEMP",
                claim=(
                    "MSME energy-efficiency investment is constrained by "
                    "financing barriers, information asymmetry, risk perception, "
                    "transaction costs, and limited uptake of available schemes."
                ),
                citation=(
                    "World Bank, India Financing Energy Efficiency at MSMEs "
                    "Project (FEEMP), Project P100530."
                ),
                category="finance",
                confidence="high",
                source_year=2019,
            )
        )

        self._register(
            Evidence(
                source_id="sidbi_annual_report_2024_25",
                source_name="SIDBI Annual Report 2024-25",
                claim=(
                    "SIDBI is the principal financial institution for promotion, "
                    "financing, and development of the MSME sector."
                ),
                citation="SIDBI, Annual Report 2024-25.",
                category="finance",
                confidence="high",
                source_year=2025,
            )
        )

        self._register(
            Evidence(
                source_id="ceew_msmse_cluster_2026",
                source_name="CEEW MSME Cluster Decarbonisation Research",
                claim=(
                    "Cluster-level decarbonisation can require balancing cost, "
                    "readiness, resource access, and enabling mechanisms."
                ),
                citation=(
                    "CEEW, Advancing India's Green Steel Transition: "
                    "Leveraging Industrial Clusters to Decarbonise Small and "
                    "Medium Enterprises, 2026."
                ),
                category="cluster_decarbonisation",
                confidence="medium",
                source_year=2026,
            )
        )

    def get(self, source_id: str) -> Optional[Evidence]:
        return self._items.get(source_id)

    def require(self, source_id: str) -> Evidence:
        evidence = self.get(source_id)
        if evidence is None:
            raise KeyError(f"Unknown evidence source: {source_id}")
        return evidence

    def all(self) -> list[Evidence]:
        return list(self._items.values())


# ---------------------------------------------------------------------------
# Part 3: Generic helpers
# ---------------------------------------------------------------------------


def _as_mapping(value: Any) -> dict[str, Any]:
    """Convert common Python/Pydantic result objects into a dictionary."""

    if value is None:
        return {}

    if isinstance(value, Mapping):
        return dict(value)

    if is_dataclass(value):
        return asdict(value)

    if hasattr(value, "model_dump"):
        return dict(value.model_dump())

    if hasattr(value, "dict"):
        return dict(value.dict())

    if hasattr(value, "__dict__"):
        return {
            key: val
            for key, val in vars(value).items()
            if not key.startswith("_")
        }

    return {}


def _get(value: Any, *keys: str, default: Any = None) -> Any:
    """Read the first available key/attribute from an object."""

    if value is None:
        return default

    mapping = _as_mapping(value)

    for key in keys:
        if key in mapping:
            return mapping[key]

        if hasattr(value, key):
            return getattr(value, key)

    return default


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        result = float(value)
        return result if math.isfinite(result) else default
    except (TypeError, ValueError):
        return default


def _format_pct(value: Any, decimals: int = 1) -> str:
    return f"{_safe_float(value):.{decimals}f}%"


def _format_inr(value: Any) -> str:
    amount = _safe_float(value)
    if amount >= 10_000_000:
        return f"₹{amount / 10_000_000:.2f} crore"
    if amount >= 100_000:
        return f"₹{amount / 100_000:.2f} lakh"
    return f"₹{amount:,.0f}"


def _normalise_sequence(value: Any) -> list[str]:
    if value is None:
        return []

    if isinstance(value, str):
        return [value]

    if isinstance(value, Sequence):
        return [str(item) for item in value]

    return [str(value)]


def _normalise_technologies(scenario: Any) -> list[str]:
    return _normalise_sequence(
        _get(
            scenario,
            "technology_sequence",
            "technologies",
            default=[],
        )
    )


def _scenario_id(scenario: Any) -> str:
    return str(
        _get(
            scenario,
            "scenario_id",
            "id",
            default="unknown_scenario",
        )
    )


def _scenario_score(scenario: Any) -> float:
    return _safe_float(
        _get(
            scenario,
            "composite_score",
            "score",
            default=0.0,
        )
    )


def _scenario_rank(scenario: Any, fallback: int = 0) -> int:
    value = _get(scenario, "rank", default=fallback)
    try:
        return int(value)
    except (TypeError, ValueError):
        return fallback


def _objective_scores(optimization: Any) -> dict[str, float]:
    recommendation = _get(optimization, "recommended", default=None)
    if recommendation is not None:
        nested = _get(recommendation, "objective_scores", default=None)
        if nested:
            return {
                str(key): _safe_float(value)
                for key, value in _as_mapping(nested).items()
            }

    ranked = _get(optimization, "ranked_scenarios", default=[])
    recommended_id = str(
        _get(
            optimization,
            "recommended_scenario_id",
            default="",
        )
    )

    for row in ranked or []:
        if _scenario_id(row) == recommended_id:
            nested = _get(row, "objective_scores", default={})
            return {
                str(key): _safe_float(value)
                for key, value in _as_mapping(nested).items()
            }

    return {}


def _find_recommended_scenario(optimization: Any, scenario: Any = None) -> dict[str, Any]:
    if scenario is not None:
        return _as_mapping(scenario)

    recommended_id = str(
        _get(
            optimization,
            "recommended_scenario_id",
            default="",
        )
    )

    ranked = _get(optimization, "ranked_scenarios", default=[])
    for row in ranked or []:
        if _scenario_id(row) == recommended_id:
            return _as_mapping(row)

    return {}


# ---------------------------------------------------------------------------
# Rule engine
# ---------------------------------------------------------------------------


class ExplanationRuleEngine:
    """
    Deterministic rules that turn decision-engine results into explanation
    reasons and source references.
    """

    def __init__(self, evidence_library: Optional[EvidenceLibrary] = None) -> None:
        self.evidence = evidence_library or EvidenceLibrary()

    def _reason(
        self,
        code: str,
        text: str,
        category: str,
        importance: str = "supporting",
        sources: Iterable[str] = (),
    ) -> Reason:
        source_ids = tuple(dict.fromkeys(sources))
        return Reason(
            code=code,
            text=text,
            category=category,
            importance=importance,
            evidence_ids=source_ids,
        )

    def explain_temperature_fit(
        self,
        factory: Any,
        scenario: Any,
    ) -> Optional[Reason]:
        temperature = _get(
            factory,
            "process_temperature_c",
            "temperature_c",
            "required_temperature_c",
        )

        if temperature is None:
            return None

        techs = _normalise_technologies(scenario)
        if not techs:
            return None

        return self._reason(
            "temperature_fit",
            (
                f"The recommended pathway is aligned with the factory's "
                f"required process temperature of {_safe_float(temperature):.0f}°C "
                f"through its selected technology sequence."
            ),
            "technical_fit",
            "primary",
            ["flexiheat_dst_2026"],
        )

    def explain_mcda_selection(
        self,
        optimization: Any,
        scenario: Any,
    ) -> Optional[Reason]:
        score = _scenario_score(scenario)
        rank = _scenario_rank(scenario, 1)
        objectives = _objective_scores(optimization)

        if not objectives and score <= 0:
            return None

        objective_text = ", ".join(
            f"{key.replace('_', ' ')}={value:.2f}"
            for key, value in objectives.items()
        )

        text = (
            f"The pathway is ranked #{rank} by the multi-criteria decision "
            f"analysis with a composite score of {score:.3f}"
        )

        if objective_text:
            text += f" ({objective_text})."

        return self._reason(
            "mcda_selection",
            text,
            "optimization",
            "primary",
            ["flexiheat_dst_2026"],
        )

    def explain_not_cheapest(
        self,
        optimization: Any,
    ) -> Optional[Reason]:
        recommended_id = _get(
            optimization,
            "recommended_scenario_id",
            default=None,
        )
        cheapest_id = _get(
            optimization,
            "cheapest_scenario_id",
            default=None,
        )

        if not recommended_id or not cheapest_id:
            return None

        if str(recommended_id) == str(cheapest_id):
            return self._reason(
                "also_cheapest",
                (
                    "The recommended pathway is also the least-cost pathway "
                    "under the current assumptions."
                ),
                "optimization",
                "supporting",
                ["flexiheat_dst_2026"],
            )

        rationale = _get(
            optimization,
            "why_not_always_cheapest",
            default="",
        )

        text = (
            "The recommendation is not simply the cheapest option; the "
            "optimizer balances multiple objectives rather than using a "
            "least-cost-only rule."
        )

        if rationale:
            text += f" {str(rationale)}"

        return self._reason(
            "not_least_cost_only",
            text,
            "optimization",
            "primary",
            ["flexiheat_dst_2026"],
        )

    def explain_emissions(
        self,
        scenario: Any,
    ) -> Optional[Reason]:
        reduction = _get(
            scenario,
            "co2_reduction_pct",
            "co2_reduction_percent",
            "emissions_reduction_pct",
        )

        if reduction is None:
            emission = _get(scenario, "emission", default=None)
            reduction = _get(
                emission,
                "co2_reduction_pct",
                "reduction_pct",
                default=None,
            )

        if reduction is None:
            return None

        value = _safe_float(reduction)

        return self._reason(
            "emissions_reduction",
            (
                f"The selected pathway is estimated to reduce CO₂ emissions "
                f"by {_format_pct(value)} relative to the modelled baseline."
            ),
            "environment",
            "primary",
            ["electrifying_industrial_heat_india_2026"],
        )

    def explain_fossil_reduction(
        self,
        scenario: Any,
    ) -> Optional[Reason]:
        reduction = _get(
            scenario,
            "fossil_fuel_reduction_pct",
            "fossil_reduction_pct",
            "fossil_reduction",
        )

        if reduction is None:
            return None

        value = _safe_float(reduction)

        return self._reason(
            "fossil_reduction",
            (
                f"The pathway is estimated to reduce fossil-fuel dependence "
                f"by {_format_pct(value)}."
            ),
            "energy_transition",
            "primary",
            [
                "mnre_giz_biomass_2026",
                "electrifying_industrial_heat_india_2026",
            ],
        )

    def explain_biomass(
        self,
        factory: Any,
        scenario: Any,
    ) -> Optional[Reason]:
        technologies = " ".join(_normalise_technologies(scenario)).lower()

        biomass_related = any(
            token in technologies
            for token in (
                "biomass",
                "pellet",
                "briquette",
                "biogas",
                "biofuel",
            )
        )

        if not biomass_related:
            return None

        location = _get(
            factory,
            "location",
            "district",
            "state",
            default="the factory location",
        )

        return self._reason(
            "biomass_resource",
            (
                f"The pathway includes a biomass-related option. For {location}, "
                "resource availability and delivered-fuel logistics should be "
                "considered before implementation."
            ),
            "resource_availability",
            "primary",
            [
                "mnre_giz_biomass_2026",
                "national_biomass_atlas",
            ],
        )

    def explain_electrification(
        self,
        scenario: Any,
    ) -> Optional[Reason]:
        technologies = " ".join(_normalise_technologies(scenario)).lower()

        electrical_terms = (
            "electric",
            "electrification",
            "heat pump",
            "induction",
            "resistance",
            "arc furnace",
            "plasma",
            "mvr",
            "infrared",
            "microwave",
            "radio frequency",
        )

        if not any(term in technologies for term in electrical_terms):
            return None

        return self._reason(
            "electrification_option",
            (
                "The pathway uses an electricity-driven industrial-heat "
                "technology whose suitability depends on process temperature, "
                "electricity cost, infrastructure, and operating requirements."
            ),
            "technology",
            "supporting",
            ["electrifying_industrial_heat_india_2026"],
        )

    def explain_finance(
        self,
        factory: Any,
        scenario: Any,
    ) -> Optional[Reason]:
        capex = _get(
            scenario,
            "capex_total_inr",
            "capex_inr",
            "capex",
            default=None,
        )

        if capex is None:
            financial = _get(scenario, "financial", default=None)
            capex = _get(
                financial,
                "capex_total_inr",
                "total_capex_inr",
                "capex_inr",
                default=None,
            )

        if capex is None:
            return None

        registration = _get(
            factory,
            "udyam_registered",
            "is_udyam_registered",
            default=None,
        )

        if registration is True:
            registration_text = " The factory is marked as Udyam-registered."
        else:
            registration_text = ""

        return self._reason(
            "financial_context",
            (
                f"The estimated capital requirement is {_format_inr(capex)}."
                f"{registration_text} Financing availability and scheme "
                "uptake should still be verified before investment."
            ),
            "finance",
            "supporting",
            [
                "niti_msme_roadmap_2026",
                "world_bank_feemp",
                "sidbi_annual_report_2024_25",
            ],
        )

    def explain_policy(
        self,
        policy: Any,
    ) -> Optional[Reason]:
        if policy is None:
            return None

        schemes = _get(
            policy,
            "eligible_schemes",
            "schemes",
            "matched_schemes",
            default=[],
        )

        if not schemes:
            return self._reason(
                "no_policy_benefit",
                (
                    "No applicable policy benefit is currently confirmed in "
                    "the supplied policy result."
                ),
                "policy",
                "supporting",
                ["niti_msme_roadmap_2026"],
            )

        names: list[str] = []
        for scheme in schemes:
            if isinstance(scheme, str):
                names.append(scheme)
                continue

            names.append(
                str(
                    _get(
                        scheme,
                        "scheme_name",
                        "name",
                        "scheme_id",
                        "id",
                        default="Unnamed scheme",
                    )
                )
            )

        return self._reason(
            "policy_support",
            (
                "The policy engine identified applicable support mechanisms: "
                + ", ".join(names)
                + ". Eligibility and benefit values remain subject to the "
                  "scheme-specific rules and verification."
            ),
            "policy",
            "primary",
            ["niti_msme_roadmap_2026"],
        )

    def explain_sensitivity(
        self,
        reliability: Any,
    ) -> Optional[Reason]:
        if reliability is None:
            return None

        p10 = _get(
            reliability,
            "payback_p10_years",
            "p10",
            default=None,
        )
        p50 = _get(
            reliability,
            "payback_p50_years",
            "p50",
            default=None,
        )
        p90 = _get(
            reliability,
            "payback_p90_years",
            "p90",
            default=None,
        )

        if p10 is None or p50 is None or p90 is None:
            return None

        return self._reason(
            "sensitivity",
            (
                "The recommendation was evaluated using uncertainty ranges "
                f"for payback: optimistic {_safe_float(p10):.2f} years, "
                f"median {_safe_float(p50):.2f} years, and adverse "
                f"{_safe_float(p90):.2f} years."
            ),
            "reliability",
            "primary",
            [
                "world_bank_feemp",
                "ceew_msmse_cluster_2026",
            ],
        )

    def build_reasons(
        self,
        factory: Any,
        scenario: Any,
        optimization: Any,
        policy: Any,
        reliability: Any,
    ) -> list[Reason]:
        candidates = [
            self.explain_temperature_fit(factory, scenario),
            self.explain_mcda_selection(optimization, scenario),
            self.explain_not_cheapest(optimization),
            self.explain_emissions(scenario),
            self.explain_fossil_reduction(scenario),
            self.explain_biomass(factory, scenario),
            self.explain_electrification(scenario),
            self.explain_finance(factory, scenario),
            self.explain_policy(policy),
            self.explain_sensitivity(reliability),
        ]

        return [item for item in candidates if item is not None]


# ---------------------------------------------------------------------------
# Part 4: Generator
# ---------------------------------------------------------------------------


class ExplainabilityEngine:
    """
    Generates the final recommendation explanation.

    Main public method:
        generate_explanation(factory, scenario, optimization, policy, reliability)

    The method does not perform optimization or policy eligibility itself.
    It only explains outputs produced by those modules.
    """

    VERSION = "1.0"

    def __init__(
        self,
        evidence_library: Optional[EvidenceLibrary] = None,
        rule_engine: Optional[ExplanationRuleEngine] = None,
    ) -> None:
        self.evidence_library = evidence_library or EvidenceLibrary()
        self.rules = rule_engine or ExplanationRuleEngine(
            self.evidence_library
        )

    def _build_evidence(
        self,
        reasons: Iterable[Reason],
    ) -> list[Evidence]:
        evidence: list[Evidence] = []
        seen: set[str] = set()

        for reason in reasons:
            for source_id in reason.evidence_ids:
                if source_id in seen:
                    continue

                item = self.evidence_library.get(source_id)
                if item is None:
                    continue

                seen.add(source_id)
                evidence.append(item)

        return evidence

    def _confidence_score(
        self,
        reasons: list[Reason],
        evidence: list[Evidence],
        optimization: Any,
        reliability: Any,
    ) -> float:
        """
        Deterministic confidence score based on evidence and available
        decision outputs.

        This is not statistical model confidence. It is a traceability /
        completeness indicator.
        """

        score = 0.35

        if reasons:
            score += min(0.20, len(reasons) * 0.025)

        high_confidence_evidence = sum(
            1 for item in evidence if item.confidence.lower() == "high"
        )

        score += min(0.20, high_confidence_evidence * 0.04)

        if _get(optimization, "recommended_scenario_id", default=None):
            score += 0.10

        if reliability is not None:
            if (
                _get(reliability, "payback_p10_years", default=None)
                is not None
                and _get(reliability, "payback_p90_years", default=None)
                is not None
            ):
                score += 0.10

        return min(1.0, max(0.0, score))

    @staticmethod
    def _confidence_label(score: float) -> str:
        if score >= 0.80:
            return "high"
        if score >= 0.60:
            return "medium-high"
        if score >= 0.40:
            return "medium"
        return "low"

    def _build_rejection_explanations(
        self,
        optimization: Any,
        recommended_id: str,
    ) -> list[dict[str, Any]]:
        ranked = _get(
            optimization,
            "ranked_scenarios",
            default=[],
        )

        output: list[dict[str, Any]] = []

        for index, row in enumerate(ranked or [], start=1):
            scenario_id = _scenario_id(row)

            if scenario_id == recommended_id:
                continue

            technologies = _normalise_technologies(row)
            score = _scenario_score(row)
            rank = _scenario_rank(row, index)

            rank_reason = str(
                _get(
                    row,
                    "rank_reason",
                    default="Lower overall MCDA score than the recommended pathway.",
                )
            )

            key_weakness = self._infer_key_weakness(row)

            output.append(
                {
                    "scenario_id": scenario_id,
                    "technology_sequence": technologies,
                    "reason": rank_reason,
                    "rank": rank,
                    "composite_score": score,
                    "key_weakness": key_weakness,
                }
            )

        return output

    @staticmethod
    def _infer_key_weakness(row: Any) -> str:
        objective_scores = _get(
            row,
            "objective_scores",
            default={},
        )
        scores = {
            str(key): _safe_float(value)
            for key, value in _as_mapping(objective_scores).items()
        }

        if not scores:
            return "Lower overall decision score"

        weakness_key = min(scores, key=scores.get)

        friendly = {
            "cost": "higher economic burden",
            "emissions": "weaker emissions performance",
            "risk": "higher operational or uncertainty risk",
        }

        return friendly.get(
            weakness_key,
            f"weaker {weakness_key.replace('_', ' ')} performance",
        )

    def _mcda_rationale(
        self,
        optimization: Any,
        scenario: Any,
    ) -> str:
        weights = _get(
            optimization,
            "weights_used",
            default={},
        )

        objectives = _get(
            scenario,
            "objective_scores",
            default=None,
        )

        if objectives is None:
            objectives = _objective_scores(optimization)

        weight_text = ", ".join(
            f"{key.replace('_', ' ')}={_safe_float(value):.0%}"
            for key, value in _as_mapping(weights).items()
        )

        score_text = ", ".join(
            f"{key.replace('_', ' ')}={_safe_float(value):.2f}"
            for key, value in _as_mapping(objectives).items()
        )

        if weight_text and score_text:
            return (
                f"The pathway was selected through weighted MCDA. "
                f"Weights used: {weight_text}. Objective scores: {score_text}."
            )

        rationale = _get(
            optimization,
            "why_not_always_cheapest",
            default=None,
        )

        return str(
            rationale
            or "The pathway was selected using multi-criteria ranking."
        )

    def _policy_rationale(self, policy: Any) -> str:
        if policy is None:
            return "No policy result was supplied."

        schemes = _get(
            policy,
            "eligible_schemes",
            "schemes",
            "matched_schemes",
            default=[],
        )

        benefit = _safe_float(
            _get(
                policy,
                "estimated_total_benefit_inr",
                "total_benefit_inr",
                "total_benefit",
                default=0.0,
            )
        )

        if not schemes:
            return (
                "No applicable scheme was identified in the supplied policy "
                "result."
            )

        names = []
        for scheme in schemes:
            if isinstance(scheme, str):
                names.append(scheme)
            else:
                names.append(
                    str(
                        _get(
                            scheme,
                            "scheme_name",
                            "name",
                            "scheme_id",
                            "id",
                            default="Unnamed scheme",
                        )
                    )
                )

        text = "Applicable policy mechanisms: " + ", ".join(names) + "."

        if benefit > 0:
            text += (
                f" The policy layer estimates a total benefit of "
                f"{_format_inr(benefit)}; this remains subject to "
                "scheme-specific convergence and eligibility checks."
            )

        return text

    def _sensitivity_rationale(self, reliability: Any) -> str:
        if reliability is None:
            return (
                "No reliability result was supplied, so uncertainty was not "
                "quantified by the explanation layer."
            )

        p10 = _get(reliability, "payback_p10_years", default=None)
        p50 = _get(reliability, "payback_p50_years", default=None)
        p90 = _get(reliability, "payback_p90_years", default=None)
        risks = _get(
            reliability,
            "top_risk_factors",
            default=[],
        )

        if p10 is None or p50 is None or p90 is None:
            return (
                "Reliability output was supplied, but complete payback "
                "percentile data was unavailable."
            )

        risk_text = ""
        if risks:
            risk_text = " Main risk drivers: " + ", ".join(
                str(item) for item in risks
            ) + "."

        return (
            f"Sensitivity analysis estimates payback at "
            f"{_safe_float(p10):.2f} years under optimistic conditions, "
            f"{_safe_float(p50):.2f} years at the median, and "
            f"{_safe_float(p90):.2f} years under adverse conditions."
            f"{risk_text}"
        )

    def _summary(
        self,
        factory: Any,
        scenario: Any,
        optimization: Any,
    ) -> str:
        sequence = _normalise_technologies(scenario)
        score = _scenario_score(scenario)

        industry = str(
            _get(
                factory,
                "industry",
                "industry_type",
                default="industrial",
            )
        )

        technology_text = (
            " → ".join(sequence)
            if sequence
            else "the selected technology pathway"
        )

        return (
            f"For the {industry} factory, the explainability engine identifies "
            f"'{technology_text}' as the recommended pathway. "
            f"The pathway has an MCDA composite score of {score:.3f}. "
            "The explanation is based on deterministic decision-engine "
            "outputs and traceable research evidence."
        )

    def generate_explanation(
        self,
        factory: Any,
        scenario: Any = None,
        optimization: Any = None,
        policy: Any = None,
        reliability: Any = None,
    ) -> RecommendationExplanation:
        """
        Generate the complete explanation object.

        Parameters
        ----------
        factory:
            Factory input/model.
        scenario:
            Recommended scenario. If omitted, it is recovered from optimizer.
        optimization:
            OptimizationResult.
        policy:
            PolicyResult / policy-engine output.
        reliability:
            Reliability/sensitivity output.
        """

        scenario_data = _find_recommended_scenario(
            optimization,
            scenario,
        )

        recommended_id = str(
            _get(
                optimization,
                "recommended_scenario_id",
                default=_scenario_id(scenario_data),
            )
        )

        reasons = self.rules.build_reasons(
            factory=factory,
            scenario=scenario_data,
            optimization=optimization,
            policy=policy,
            reliability=reliability,
        )

        evidence = self._build_evidence(reasons)

        why_selected = [reason.text for reason in reasons]

        why_not_cheapest = None
        for reason in reasons:
            if reason.code == "not_least_cost_only":
                why_not_cheapest = reason.text
                break

        score = self._confidence_score(
            reasons=reasons,
            evidence=evidence,
            optimization=optimization,
            reliability=reliability,
        )
        confidence = self._confidence_label(score)

        citation_map = {
            f"[{index}]": item.source_id
            for index, item in enumerate(evidence, start=1)
        }

        return RecommendationExplanation(
            headline=(
                f"Recommendation explanation for scenario "
                f"'{recommended_id}'"
            ),
            summary=self._summary(
                factory,
                scenario_data,
                optimization,
            ),
            why_selected=why_selected,
            why_not_cheapest=why_not_cheapest,
            why_others_rejected=self._build_rejection_explanations(
                optimization,
                recommended_id,
            ),
            evidence=evidence,
            reasons=reasons,
            mcda_rationale=self._mcda_rationale(
                optimization,
                scenario_data,
            ),
            policy_rationale=self._policy_rationale(policy),
            sensitivity_rationale=self._sensitivity_rationale(
                reliability
            ),
            confidence=confidence,
            confidence_score=round(score, 3),
            citation_map=citation_map,
        )

    def generate(
        self,
        factory: Any,
        scenario: Any = None,
        optimization: Any = None,
        policy: Any = None,
        reliability: Any = None,
    ) -> RecommendationExplanation:
        """Alias for generate_explanation()."""

        return self.generate_explanation(
            factory=factory,
            scenario=scenario,
            optimization=optimization,
            policy=policy,
            reliability=reliability,
        )


# ---------------------------------------------------------------------------
# Recommendation-model adapter
# ---------------------------------------------------------------------------


def build_recommendation_explanation(
    factory: Any,
    scenario: Any = None,
    optimization: Any = None,
    policy: Any = None,
    reliability: Any = None,
) -> RecommendationExplanation:
    """
    Convenience function for report_generator.py and API callers.
    """

    engine = ExplainabilityEngine()

    return engine.generate_explanation(
        factory=factory,
        scenario=scenario,
        optimization=optimization,
        policy=policy,
        reliability=reliability,
    )


def explanation_to_recommendation_fields(
    explanation: RecommendationExplanation,
) -> dict[str, Any]:
    """
    Convert the standalone explanation into the fields expected by the
    existing Recommendation model.

    This keeps the engine independent from models/recommendation.py while
    making integration straightforward.
    """

    policy_benefits = PolicyBenefitAdapter.from_explanation(explanation)

    sensitivity = SensitivityAdapter.from_explanation(explanation)

    return {
        "why_selected": explanation.why_selected,
        "why_others_rejected": explanation.why_others_rejected,
        "policy_benefits": policy_benefits,
        "sensitivity_notes": sensitivity,
    }


class PolicyBenefitAdapter:
    """Adapter for the existing Recommendation policy-benefit contract."""

    @staticmethod
    def from_explanation(
        explanation: RecommendationExplanation,
    ) -> dict[str, Any]:
        eligible = []

        policy_evidence = [
            item
            for item in explanation.evidence
            if item.category == "policy_finance"
        ]

        # This adapter intentionally does not invent scheme IDs.
        # The policy engine remains the source of truth for eligibility.
        for item in policy_evidence:
            eligible.append(item.source_id)

        return {
            "eligible_schemes": eligible,
            "estimated_total_benefit_inr": 0.0,
            "total_benefit_verified": False,
            "disclaimer": (
                "Estimated explanation-layer summary. Exact scheme eligibility "
                "and benefit values must come from the policy engine."
            ),
        }


class SensitivityAdapter:
    """Adapter for the existing Recommendation sensitivity contract."""

    @staticmethod
    def from_explanation(
        explanation: RecommendationExplanation,
    ) -> dict[str, Any]:
        sensitivity_text = explanation.sensitivity_rationale or ""

        return {
            "payback_p10_years": 0.0,
            "payback_p50_years": 0.0,
            "payback_p90_years": 0.0,
            "spread_ratio": 0.0,
            "top_risk_factors": [],
            "risk_interpretation": sensitivity_text,
        }


# ---------------------------------------------------------------------------
# Small utility exports
# ---------------------------------------------------------------------------


def list_evidence_sources() -> list[dict[str, Any]]:
    """Return the registered evidence library for debugging/reporting."""

    return [
        item.to_dict()
        for item in EvidenceLibrary().all()
    ]


__all__ = [
    "Evidence",
    "Reason",
    "RecommendationExplanation",
    "EvidenceLibrary",
    "ExplanationRuleEngine",
    "ExplainabilityEngine",
    "build_recommendation_explanation",
    "explanation_to_recommendation_fields",
    "PolicyBenefitAdapter",
    "SensitivityAdapter",
    "list_evidence_sources",
]
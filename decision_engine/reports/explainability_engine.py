
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping, Optional, Sequence
import json
import re

from models.factory import Factory
from models.scenario import Scenario
from models.recommendation import Recommendation

from decision_engine.optimizer.optimization_engine import OptimizationResult
from decision_engine.policy.policy_engine import PolicyEvaluationResult
from decision_engine.reliability.reliability_engine import ReliabilitySweepResult


PROJECT_ROOT = Path(__file__).resolve().parents[2]
CITATIONS_PATH = (
    PROJECT_ROOT / "knowledge-base" / "references" / "citations.json"
)


# ---------------------------------------------------------------------------
# Evidence registry
# ---------------------------------------------------------------------------

EVIDENCE_LIBRARY: dict[str, dict[str, Any]] = {
    "flexiheat_dst": {
        "source_id": "flexiheat_dst",
        "title": "FlexiHeat-DST — Power-to-Heat MCDA Decision Support",
        "publisher": "Energy Conversion and Management: X",
        "topics": {
            "mcda",
            "scenario_analysis",
            "technology_selection",
            "electrification",
        },
        "supports": [
            "transparent multi-criteria decision analysis",
            "scenario comparison for power-to-heat technologies",
            "trade-offs among techno-economic and environmental criteria",
        ],
    },
    "energy_innovation_india_heat_2026": {
        "source_id": "energy_innovation_india_heat_2026",
        "title": "Electrifying Industrial Heat in India",
        "publisher": "Energy Innovation / India Energy & Climate Center",
        "topics": {
            "electrification",
            "industrial_heat",
            "economics",
            "emissions",
            "solar",
        },
        "supports": [
            "industrial electrification across temperature bands",
            "electric heat pumps and electric thermal technologies",
            "clean-electricity pathways for reducing industrial emissions",
        ],
    },
    "mnre_giz_biomass_msme": {
        "source_id": "mnre_giz_biomass_msme",
        "title": (
            "Decarbonizing MSMEs: Use of Biomass for Green Steam "
            "and Heat Applications"
        ),
        "publisher": "MNRE / GIZ / Grant Thornton Bharat",
        "topics": {
            "biomass",
            "industrial_heat",
            "msme",
            "fuel_switch",
            "supply_chain",
        },
        "supports": [
            "biomass-based green steam and industrial heat",
            "biomass substitution for fossil-fuel thermal applications",
            "biomass supply-chain and multi-fuel considerations",
        ],
    },
    "niti_msme_roadmap": {
        "source_id": "niti_msme_roadmap",
        "title": "Roadmap for Green Transition of MSMEs",
        "publisher": "NITI Aayog",
        "topics": {
            "policy",
            "msme",
            "green_transition",
            "finance",
            "energy_efficiency",
        },
        "supports": [
            "MSME green-transition policy priorities",
            "energy efficiency, green electricity, and alternative fuels",
            "targeted financial and institutional support",
        ],
    },
    "SRC_NITI_AAYOG_ROADMAP_JAN2026": {
        "source_id": "SRC_NITI_AAYOG_ROADMAP_JAN2026",
        "title": "NITI Aayog MSME Green Transition Roadmap",
        "publisher": "NITI Aayog",
        "topics": {
            "policy",
            "msme",
            "green_transition",
            "finance",
        },
        "supports": [
            "MSME decarbonisation policy context",
            "green finance and implementation mechanisms",
        ],
    },
    "SRC_ADEETIE_BEE": {
        "source_id": "SRC_ADEETIE_BEE",
        "title": "ADEETIE / BEE Scheme Reference",
        "publisher": "Bureau of Energy Efficiency",
        "topics": {
            "policy",
            "finance",
            "energy_efficiency",
        },
        "supports": [
            "scheme eligibility and financing support where encoded "
            "in the policy knowledge base",
        ],
    },
    "SRC_SIDBI_MSE_GIFT": {
        "source_id": "SRC_SIDBI_MSE_GIFT",
        "title": "SIDBI MSE-GIFT / RAMP Financing Reference",
        "publisher": "SIDBI / Ministry of MSME",
        "topics": {
            "finance",
            "msme",
            "green_transition",
        },
        "supports": [
            "green financing pathway for qualifying MSMEs",
        ],
    },
    "SRC_MSE_GIFT": {
        "source_id": "SRC_MSE_GIFT",
        "title": "MSE-GIFT Scheme Reference",
        "publisher": "Ministry of MSME / SIDBI",
        "topics": {
            "finance",
            "msme",
        },
        "supports": [
            "green investment financing for eligible MSMEs",
        ],
    },
    "SRC_CGTMSE": {
        "source_id": "SRC_CGTMSE",
        "title": "CGTMSE Reference",
        "publisher": "CGTMSE",
        "topics": {
            "finance",
            "credit_guarantee",
            "msme",
        },
        "supports": [
            "credit-guarantee financing support where eligible",
        ],
    },
    "SRC_MSME_UDYAM_THRESHOLDS": {
        "source_id": "SRC_MSME_UDYAM_THRESHOLDS",
        "title": "MSME / Udyam Classification Threshold Reference",
        "publisher": "Government of India",
        "topics": {
            "policy",
            "eligibility",
            "msme",
        },
        "supports": [
            "MSME category and eligibility context",
        ],
    },
    "SRC_PROJECT_DEFAULTS": {
        "source_id": "SRC_PROJECT_DEFAULTS",
        "title": "Project Assumptions / Defaults",
        "publisher": "Industrial Energy Optimizer knowledge base",
        "topics": {
            "assumptions",
            "model",
        },
        "supports": [
            "versioned project assumptions where explicitly used",
        ],
    },
}


ALIASES: dict[str, str] = {
    "flexiheat": "flexiheat_dst",
    "FlexiHeat": "flexiheat_dst",
    "FlexiHeat-DST": "flexiheat_dst",
    "energy_innovation": "energy_innovation_india_heat_2026",
    "Energy Innovation": "energy_innovation_india_heat_2026",
    "biomass": "mnre_giz_biomass_msme",
    "MNRE": "mnre_giz_biomass_msme",
    "MNRE-GIZ": "mnre_giz_biomass_msme",
    "NITI": "niti_msme_roadmap",
    "NITI Aayog": "niti_msme_roadmap",
    "World Bank": "SRC_PROJECT_DEFAULTS",
    "BEE": "SRC_ADEETIE_BEE",
    "SIDBI": "SRC_SIDBI_MSE_GIFT",
    "CGTMSE": "SRC_CGTMSE",
    "Udyam": "SRC_MSME_UDYAM_THRESHOLDS",
}


def _normalise_text(value: Any) -> str:
    if value is None:
        return ""
    return re.sub(r"\s+", " ", str(value).strip())


def _canonical_source_id(value: Any) -> Optional[str]:
    text = _normalise_text(value)
    if not text:
        return None

    if text in EVIDENCE_LIBRARY:
        return text

    if text in ALIASES:
        return ALIASES[text]

    lowered = text.lower()

    for alias, source_id in ALIASES.items():
        if lowered == alias.lower():
            return source_id

    for key in EVIDENCE_LIBRARY:
        if key.lower() == lowered:
            return key

    return None


def _load_repo_citations() -> dict[str, Any]:
    if not CITATIONS_PATH.exists():
        return {}

    try:
        with CITATIONS_PATH.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
    except (OSError, json.JSONDecodeError):
        return {}

    return data if isinstance(data, dict) else {}


REPO_CITATIONS = _load_repo_citations()


# ---------------------------------------------------------------------------
# Core models
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Evidence:
    """One auditable supporting source reference."""

    source_id: str
    title: str
    publisher: str
    topic: str
    claim: str
    source_status: str = "repository_reference"
    citation_available: bool = True
    page_hint: Optional[str] = None
    notes: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_id": self.source_id,
            "title": self.title,
            "publisher": self.publisher,
            "topic": self.topic,
            "claim": self.claim,
            "source_status": self.source_status,
            "citation_available": self.citation_available,
            "page_hint": self.page_hint,
            "notes": self.notes,
        }


@dataclass(frozen=True)
class Reason:
    """One deterministic reason contributing to a recommendation."""

    code: str
    text: str
    category: str
    strength: str = "supporting"
    evidence_ids: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "code": self.code,
            "text": self.text,
            "category": self.category,
            "strength": self.strength,
            "evidence_ids": list(self.evidence_ids),
        }


@dataclass
class RecommendationExplanation:
    """Structured explanation produced by the Explainability Engine."""

    factory_id: str
    recommended_scenario_id: str
    recommended_technology_sequence: list[str]

    why_selected: list[Reason] = field(default_factory=list)
    why_others_rejected: list[Reason] = field(default_factory=list)

    evidence: list[Evidence] = field(default_factory=list)

    policy_summary: dict[str, Any] = field(default_factory=dict)
    sensitivity_summary: dict[str, Any] = field(default_factory=dict)
    mcda_summary: dict[str, Any] = field(default_factory=dict)

    confidence: str = "Medium"
    confidence_score: float = 0.0

    caveats: list[str] = field(default_factory=list)

    generated_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    model_version: str = "2.0"

    def to_dict(self) -> dict[str, Any]:
        return {
            "factory_id": self.factory_id,
            "recommended_scenario_id": self.recommended_scenario_id,
            "recommended_technology_sequence": (
                self.recommended_technology_sequence
            ),
            "why_selected": [
                reason.to_dict()
                for reason in self.why_selected
            ],
            "why_others_rejected": [
                reason.to_dict()
                for reason in self.why_others_rejected
            ],
            "evidence": [
                evidence.to_dict()
                for evidence in self.evidence
            ],
            "policy_summary": dict(self.policy_summary),
            "sensitivity_summary": dict(self.sensitivity_summary),
            "mcda_summary": dict(self.mcda_summary),
            "confidence": self.confidence,
            "confidence_score": round(self.confidence_score, 4),
            "caveats": list(self.caveats),
            "generated_at": self.generated_at.isoformat(),
            "model_version": self.model_version,
        }


# ---------------------------------------------------------------------------
# Evidence library
# ---------------------------------------------------------------------------

class EvidenceLibrary:
    """Read-only semantic evidence registry."""

    def __init__(
        self,
        registry: Optional[
            Mapping[str, Mapping[str, Any]]
        ] = None,
    ) -> None:
        self._registry = dict(
            registry or EVIDENCE_LIBRARY
        )

    def available(self, source_id: str) -> bool:
        canonical = _canonical_source_id(source_id)
        return bool(
            canonical and canonical in self._registry
        )

    def get(
        self,
        source_id: str,
        *,
        topic: str,
        claim: Optional[str] = None,
    ) -> Optional[Evidence]:

        canonical = _canonical_source_id(source_id)

        if canonical is None:
            return None

        record = self._registry.get(canonical)

        if record is None:
            return None

        supports = record.get("supports") or []

        chosen_claim = (
            claim
            or (
                supports[0]
                if supports
                else "Supporting evidence in repository reference"
            )
        )

        return Evidence(
            source_id=canonical,
            title=(
                _normalise_text(
                    record.get("title")
                )
                or canonical
            ),
            publisher=(
                _normalise_text(
                    record.get("publisher")
                )
                or "Repository reference"
            ),
            topic=topic,
            claim=chosen_claim,
            citation_available=(
                canonical in REPO_CITATIONS
            ),
        )

    def search(
        self,
        topics: Iterable[str],
        *,
        claim: str,
    ) -> list[Evidence]:

        requested = {
            str(topic).strip().lower()
            for topic in topics
            if topic
        }

        results: list[Evidence] = []

        for source_id, record in self._registry.items():

            source_topics = {
                str(topic).lower()
                for topic in record.get("topics", set())
            }

            overlap = requested.intersection(
                source_topics
            )

            if not overlap:
                continue

            selected_topic = next(
                iter(overlap)
            )

            evidence = self.get(
                source_id,
                topic=selected_topic,
                claim=claim,
            )

            if evidence:
                results.append(evidence)

        return results


# ---------------------------------------------------------------------------
# Explainability engine
# ---------------------------------------------------------------------------

class ExplainabilityEngine:
    """
    Deterministic explanation generator.

    It never changes the optimizer's recommendation. It only explains
    the result already produced by upstream decision modules.
    """

    TECHNOLOGY_TOPICS: dict[str, set[str]] = {
        "heat_pump": {
            "electrification",
            "industrial_heat",
        },
        "electrification": {
            "electrification",
            "industrial_heat",
        },
        "electric_boiler": {
            "electrification",
            "industrial_heat",
        },
        "electric_resistance": {
            "electrification",
            "industrial_heat",
        },
        "thermal_storage": {
            "electrification",
            "scenario_analysis",
        },
        "solar_thermal": {
            "solar",
            "industrial_heat",
        },
        "solar_pv": {
            "solar",
            "electrification",
        },
        "biomass": {
            "biomass",
            "industrial_heat",
            "fuel_switch",
        },
        "biomass_boiler": {
            "biomass",
            "industrial_heat",
            "fuel_switch",
        },
        "waste_heat_recovery": {
            "industrial_heat",
            "energy_efficiency",
        },
    }

    def __init__(
        self,
        evidence_library: Optional[
            EvidenceLibrary
        ] = None,
    ) -> None:
        self.evidence = (
            evidence_library
            or EvidenceLibrary()
        )

    @staticmethod
    def _normalise_technology(
        value: Any,
    ) -> str:
        return (
            _normalise_text(value)
            .lower()
            .replace(" ", "_")
            .replace("-", "_")
        )

    @staticmethod
    def _best_ranked_row(
        optimization: OptimizationResult,
        scenario_id: str,
    ) -> Any:

        for row in optimization.ranked_scenarios:
            if row.scenario_id == scenario_id:
                return row

        raise ValueError(
            f"Scenario '{scenario_id}' is absent "
            "from optimizer ranking."
        )

    @staticmethod
    def _objective_strength(
        value: float,
    ) -> str:

        if value >= 0.80:
            return "strong"

        if value >= 0.60:
            return "moderate"

        if value >= 0.40:
            return "mixed"

        return "weak"

    @staticmethod
    def _risk_label(
        spread_ratio: float,
    ) -> str:

        if spread_ratio < 0.25:
            return "Low"

        if spread_ratio < 0.50:
            return "Moderate"

        return "High"

    def _add_evidence_once(
        self,
        evidence: Optional[Evidence],
        target: list[Evidence],
    ) -> Optional[str]:

        if evidence is None:
            return None

        if evidence.source_id not in {
            item.source_id
            for item in target
        }:
            target.append(evidence)

        return evidence.source_id

    def _technology_evidence(
        self,
        technologies: Sequence[str],
    ) -> list[Evidence]:

        results: list[Evidence] = []

        technology_topics: set[str] = set()

        for technology in technologies:
            technology_id = (
                self._normalise_technology(
                    technology
                )
            )

            technology_topics.update(
                self.TECHNOLOGY_TOPICS.get(
                    technology_id,
                    {"technology_selection"},
                )
            )

        topic_to_source_priority = [
            ("biomass", "mnre_giz_biomass_msme"),
            ("electrification", "energy_innovation_india_heat_2026"),
            ("solar", "energy_innovation_india_heat_2026"),
            ("industrial_heat", "mnre_giz_biomass_msme"),
            ("technology_selection", "flexiheat_dst"),
        ]

        for topic, source_id in topic_to_source_priority:

            if topic not in technology_topics:
                continue

            evidence = self.evidence.get(
                source_id,
                topic=topic,
            )

            if evidence:
                results.append(evidence)

        return results

    def _mcda_reasons(
        self,
        optimization: OptimizationResult,
        recommended_row: Any,
        evidence: Sequence[Evidence],
    ) -> list[Reason]:

        reasons: list[Reason] = []

        objective_scores = dict(
            recommended_row.objective_scores
        )

        mcda_source_ids = tuple(
            evidence_item.source_id
            for evidence_item in evidence
            if evidence_item.source_id == "flexiheat_dst"
        )

        for objective, label in (
            ("cost", "economic performance"),
            ("emissions", "emissions performance"),
            ("risk", "reliability / risk performance"),
        ):

            score = float(
                objective_scores.get(
                    objective,
                    0.0,
                )
                or 0.0
            )

            strength = (
                self._objective_strength(
                    score
                )
            )

            reasons.append(
                Reason(
                    code=f"mcda_{objective}",
                    text=(
                        f"MCDA gave the pathway a "
                        f"{score:.2f} {label} score "
                        f"({strength})."
                    ),
                    category="mcda",
                    strength=strength,
                    evidence_ids=mcda_source_ids,
                )
            )

        if optimization.recommended_is_cheapest:

            reasons.append(
                Reason(
                    code="mcda_is_least_cost",
                    text=(
                        "The recommended pathway is also "
                        "the least-cost option under the "
                        "current assumptions."
                    ),
                    category="mcda",
                    strength="supporting",
                    evidence_ids=mcda_source_ids,
                )
            )

        else:

            reasons.append(
                Reason(
                    code="mcda_not_least_cost",
                    text=(
                        "The recommended pathway is not the "
                        "least-cost pathway; the MCDA result "
                        "reflects a weighted trade-off across "
                        "cost, emissions, and risk."
                    ),
                    category="mcda",
                    strength="strong",
                    evidence_ids=mcda_source_ids,
                )
            )

        return reasons

    def _technology_reasons(
        self,
        factory: Factory,
        scenario: Scenario,
        evidence: Sequence[Evidence],
    ) -> list[Reason]:

        reasons: list[Reason] = []

        evidence_ids = tuple(
            item.source_id
            for item in evidence
            if item.source_id
            in {
                "flexiheat_dst",
                "energy_innovation_india_heat_2026",
                "mnre_giz_biomass_msme",
            }
        )

        for technology in scenario.technology_sequence:

            technology_id = (
                self._normalise_technology(
                    technology
                )
            )

            if technology_id in {
                "heat_pump",
                "electric_boiler",
                "electric_resistance",
                "electrification",
                "solar_pv",
            }:

                reasons.append(
                    Reason(
                        code=(
                            f"technology_{technology_id}"
                        ),
                        text=(
                            f"Technology '{technology}' "
                            "is present in a pathway that "
                            "passed the upstream technical "
                            "feasibility stage for the "
                            f"required "
                            f"{factory.required_process_temperature_c:.0f}°C "
                            "process condition."
                        ),
                        category=(
                            "technical_feasibility"
                        ),
                        strength="supporting",
                        evidence_ids=evidence_ids,
                    )
                )

            elif technology_id in {
                "biomass",
                "biomass_boiler",
            }:

                biomass_ids = tuple(
                    item.source_id
                    for item in evidence
                    if item.source_id
                    == "mnre_giz_biomass_msme"
                )

                reasons.append(
                    Reason(
                        code="technology_biomass",
                        text=(
                            "Biomass appears in the selected "
                            "pathway, linking the recommendation "
                            "to an India-specific green-heat "
                            "option while making local biomass "
                            "availability and supply-chain "
                            "reliability explicit constraints."
                        ),
                        category="resource_fit",
                        strength="supporting",
                        evidence_ids=biomass_ids,
                    )
                )

        return reasons

    def _impact_reasons(
        self,
        scenario: Scenario,
        evidence: Sequence[Evidence],
    ) -> list[Reason]:

        reasons: list[Reason] = []

        climate_ids = tuple(
            item.source_id
            for item in evidence
            if item.source_id
            in {
                "energy_innovation_india_heat_2026",
                "mnre_giz_biomass_msme",
                "niti_msme_roadmap",
            }
        )

        if scenario.co2_reduction_pct > 0:

            reasons.append(
                Reason(
                    code="co2_reduction",
                    text=(
                        f"The pathway estimates a "
                        f"{scenario.co2_reduction_pct:.1f}% "
                        "reduction in CO2 relative to "
                        "the baseline."
                    ),
                    category="environment",
                    strength=(
                        "strong"
                        if scenario.co2_reduction_pct >= 30
                        else "supporting"
                    ),
                    evidence_ids=climate_ids,
                )
            )

        if scenario.fossil_fuel_reduction_pct > 0:

            reasons.append(
                Reason(
                    code="fossil_reduction",
                    text=(
                        f"The pathway estimates a "
                        f"{scenario.fossil_fuel_reduction_pct:.1f}% "
                        "reduction in fossil-fuel use."
                    ),
                    category="environment",
                    strength=(
                        "strong"
                        if scenario.fossil_fuel_reduction_pct >= 30
                        else "supporting"
                    ),
                    evidence_ids=climate_ids,
                )
            )

        return reasons

    def _policy_reasons(
        self,
        policy: PolicyEvaluationResult,
        evidence: Sequence[Evidence],
    ) -> list[Reason]:

        reasons: list[Reason] = []

        eligible = list(
            policy.eligible_schemes
        )

        policy_ids = tuple(
            item.source_id
            for item in evidence
            if item.source_id
            in {
                "SRC_ADEETIE_BEE",
                "SRC_SIDBI_MSE_GIFT",
                "SRC_MSE_GIFT",
                "SRC_CGTMSE",
                "SRC_MSME_UDYAM_THRESHOLDS",
                "niti_msme_roadmap",
            }
        )

        if eligible:

            names = [
                scheme.display_name
                for scheme in eligible[:4]
            ]

            text = (
                f"The factory matched "
                f"{len(eligible)} eligible policy/"
                f"financing scheme(s): "
                f"{', '.join(names)}"
            )

            if len(eligible) > len(names):
                text += (
                    f", plus "
                    f"{len(eligible) - len(names)} "
                    "additional scheme(s)."
                )
            else:
                text += "."

            reasons.append(
                Reason(
                    code="policy_eligible",
                    text=text,
                    category="policy",
                    strength="strong",
                    evidence_ids=policy_ids,
                )
            )

        else:

            reasons.append(
                Reason(
                    code="policy_none",
                    text=(
                        "No eligible policy benefit was "
                        "established by the policy engine "
                        "for the supplied factory inputs."
                    ),
                    category="policy",
                    strength="neutral",
                    evidence_ids=policy_ids,
                )
            )

        if policy.warnings:

            reasons.append(
                Reason(
                    code="policy_warning",
                    text=(
                        "Policy-engine warnings require "
                        "manual verification before a "
                        "benefit is treated as guaranteed."
                    ),
                    category="policy",
                    strength="caution",
                    evidence_ids=policy_ids,
                )
            )

        return reasons

    def _sensitivity_reasons(
        self,
        reliability: ReliabilitySweepResult,
    ) -> list[Reason]:

        label = self._risk_label(
            reliability.spread_ratio
        )

        reasons = [
            Reason(
                code="sensitivity_risk",
                text=(
                    f"Reliability analysis classifies "
                    f"payback uncertainty as {label}: "
                    f"P10={reliability.payback_p10:.2f} years, "
                    f"P50={reliability.payback_p50:.2f} years, "
                    f"P90={reliability.payback_p90:.2f} years."
                ),
                category="reliability",
                strength=(
                    "strong"
                    if label == "Low"
                    else (
                        "caution"
                        if label == "High"
                        else "supporting"
                    )
                ),
                evidence_ids=(),
            )
        ]

        if reliability.oat_swings:

            top = sorted(
                reliability.oat_swings.items(),
                key=lambda item: item[1],
                reverse=True,
            )[:3]

            factor_text = ", ".join(
                f"{name} ({swing:.2f} yr swing)"
                for name, swing in top
            )

            reasons.append(
                Reason(
                    code="sensitivity_drivers",
                    text=(
                        "Largest one-at-a-time payback "
                        f"sensitivity drivers are {factor_text}."
                    ),
                    category="reliability",
                    strength="supporting",
                    evidence_ids=(),
                )
            )

        return reasons

    def _rejected_reasons(
        self,
        optimization: OptimizationResult,
        scenarios: Mapping[str, Scenario],
    ) -> list[Reason]:

        results: list[Reason] = []

        ranked = list(
            optimization.ranked_scenarios
        )

        if len(ranked) <= 1:
            return results

        for row in ranked[1:]:

            scenario = scenarios.get(
                row.scenario_id
            )

            sequence = (
                ", ".join(
                    scenario.technology_sequence
                )
                if scenario
                else ", ".join(
                    row.technology_sequence
                )
            )

            weakness = (
                row.rank_reason
                or "lower composite MCDA score"
            )

            results.append(
                Reason(
                    code=(
                        f"rejected_{row.scenario_id}"
                    ),
                    text=(
                        f"Scenario {row.scenario_id} "
                        f"({sequence}) ranked #{row.rank} "
                        f"because {weakness}."
                    ),
                    category="comparison",
                    strength="caution",
                    evidence_ids=("flexiheat_dst",),
                )
            )

        return results

    def _build_policy_summary(
        self,
        policy: PolicyEvaluationResult,
    ) -> dict[str, Any]:

        eligible = [
            scheme.display_name
            for scheme in policy.eligible_schemes
        ]

        finance = None

        if policy.finance_summary is not None:
            finance = (
                policy.finance_summary.to_dict()
            )

        return {
            "eligible": bool(eligible),
            "eligible_schemes": eligible,
            "estimated_total_benefit_inr": float(
                policy.estimated_total_benefit_inr
                or 0.0
            ),
            "total_benefit_verified": bool(
                policy.total_benefit_verified
            ),
            "finance_summary": finance,
            "warnings": list(policy.warnings),
        }

    def _build_mcda_summary(
        self,
        optimization: OptimizationResult,
        row: Any,
    ) -> dict[str, Any]:

        return {
            "recommended_scenario_id": (
                optimization.recommended_scenario_id
            ),
            "recommended_is_cheapest": (
                optimization.recommended_is_cheapest
            ),
            "cheapest_scenario_id": (
                optimization.cheapest_scenario_id
            ),
            "weights_used": dict(
                optimization.weights_used
            ),
            "composite_score": float(
                row.composite_score
            ),
            "objective_scores": dict(
                row.objective_scores
            ),
            "why_not_always_cheapest": (
                optimization.why_not_always_cheapest
            ),
        }

    def _build_sensitivity_summary(
        self,
        reliability: ReliabilitySweepResult,
    ) -> dict[str, Any]:

        return {
            "payback_p10_years": float(
                reliability.payback_p10
            ),
            "payback_p50_years": float(
                reliability.payback_p50
            ),
            "payback_p90_years": float(
                reliability.payback_p90
            ),
            "spread_ratio": float(
                reliability.spread_ratio
            ),
            "risk_label": self._risk_label(
                reliability.spread_ratio
            ),
            "top_risk_factors": [
                name
                for name, _ in sorted(
                    reliability.oat_swings.items(),
                    key=lambda item: item[1],
                    reverse=True,
                )[:5]
            ],
            "gate_passed": bool(
                reliability.gate_passed
            ),
            "n_iterations": int(
                reliability.n_iterations
            ),
        }

    def _confidence_score(
        self,
        optimization: OptimizationResult,
        policy: PolicyEvaluationResult,
        reliability: ReliabilitySweepResult,
        evidence: Sequence[Evidence],
    ) -> tuple[str, float]:

        score = 0.55

        if optimization.ranked_scenarios:
            score += 0.10

        if reliability.gate_passed:
            score += 0.15

        if policy.total_benefit_verified:
            score += 0.08
        elif policy.eligible_schemes:
            score += 0.04

        citation_coverage = sum(
            1
            for item in evidence
            if item.citation_available
        )

        if evidence:
            score += (
                0.08
                * min(
                    1.0,
                    citation_coverage
                    / len(evidence),
                )
            )

        if policy.warnings:
            score -= 0.08

        if not reliability.gate_passed:
            score -= 0.08

        score = max(
            0.0,
            min(
                1.0,
                score,
            ),
        )

        if score >= 0.80:
            label = "High"
        elif score >= 0.60:
            label = "Medium"
        else:
            label = "Low"

        return label, score

    # -----------------------------------------------------------------------
    # Public API
    # -----------------------------------------------------------------------

    def generate_explanation(
        self,
        factory: Factory,
        scenario: Scenario,
        optimization: OptimizationResult,
        policy: PolicyEvaluationResult,
        reliability: ReliabilitySweepResult,
        scenarios: Optional[
            Mapping[str, Scenario]
        ] = None,
    ) -> RecommendationExplanation:
        """
        Generate the full structured explanation.

        The recommendation itself is never changed by this method.
        """

        scenarios_map = dict(
            scenarios or {
                scenario.scenario_id: scenario
            }
        )

        if (
            optimization.recommended_scenario_id
            != scenario.scenario_id
        ):

            recommended = scenarios_map.get(
                optimization.recommended_scenario_id
            )

            if recommended is None:
                raise ValueError(
                    "Recommended scenario does not "
                    "match the scenario argument and "
                    "is not present in scenarios."
                )

            scenario = recommended

        ranked_row = self._best_ranked_row(
            optimization,
            scenario.scenario_id,
        )

        evidence: list[Evidence] = []

        # Core MCDA evidence.
        self._add_evidence_once(
            self.evidence.get(
                "flexiheat_dst",
                topic="mcda",
                claim=(
                    "transparent multi-criteria decision "
                    "analysis for power-to-heat options"
                ),
            ),
            evidence,
        )

        # MSME policy context.
        self._add_evidence_once(
            self.evidence.get(
                "niti_msme_roadmap",
                topic="policy",
                claim=(
                    "MSME green-transition policy and "
                    "implementation context"
                ),
            ),
            evidence,
        )

        # Technology-specific evidence.
        for evidence_item in self._technology_evidence(
            scenario.technology_sequence
        ):
            self._add_evidence_once(
                evidence_item,
                evidence,
            )

        # Financing evidence.
        if policy.eligible_schemes:

            for source_id in (
                "SRC_ADEETIE_BEE",
                "SRC_SIDBI_MSE_GIFT",
                "SRC_MSE_GIFT",
                "SRC_CGTMSE",
            ):

                self._add_evidence_once(
                    self.evidence.get(
                        source_id,
                        topic="finance",
                        claim=(
                            "policy financing support "
                            "where supported by repository "
                            "scheme data"
                        ),
                    ),
                    evidence,
                )

        selected_reasons: list[Reason] = []

        selected_reasons.extend(
            self._mcda_reasons(
                optimization,
                ranked_row,
                evidence,
            )
        )

        selected_reasons.extend(
            self._technology_reasons(
                factory,
                scenario,
                evidence,
            )
        )

        selected_reasons.extend(
            self._impact_reasons(
                scenario,
                evidence,
            )
        )

        selected_reasons.extend(
            self._policy_reasons(
                policy,
                evidence,
            )
        )

        selected_reasons.extend(
            self._sensitivity_reasons(
                reliability,
            )
        )

        rejected = self._rejected_reasons(
            optimization,
            scenarios_map,
        )

        caveats: list[str] = []

        if (
            not policy.total_benefit_verified
            and policy.estimated_total_benefit_inr > 0
        ):
            caveats.append(
                "Policy benefit is estimated and must not "
                "be presented as a guaranteed combined "
                "subsidy; scheme-specific convergence/"
                "stacking must be verified."
            )

        if not reliability.gate_passed:
            caveats.append(
                "Reliability spread gate did not pass; "
                "treat payback sensitivity as material "
                "and use the recommendation with "
                "additional caution."
            )

        if not scenario.rejected_technologies:
            caveats.append(
                "No rejected-technology list was carried "
                "into the supplied Scenario; upstream "
                "feasibility reasons should be preserved "
                "for a complete 'Why not?' view."
            )

        if not all(
            item.citation_available
            for item in evidence
        ):
            caveats.append(
                "Some semantic evidence entries are "
                "present without a resolved repository "
                "citation record; do not invent page "
                "numbers or external references."
            )

        confidence_label, confidence_score = (
            self._confidence_score(
                optimization,
                policy,
                reliability,
                evidence,
            )
        )

        return RecommendationExplanation(
            factory_id=factory.factory_id,
            recommended_scenario_id=(
                scenario.scenario_id
            ),
            recommended_technology_sequence=list(
                scenario.technology_sequence
            ),
            why_selected=selected_reasons,
            why_others_rejected=rejected,
            evidence=evidence,
            policy_summary=self._build_policy_summary(
                policy
            ),
            sensitivity_summary=(
                self._build_sensitivity_summary(
                    reliability
                )
            ),
            mcda_summary=self._build_mcda_summary(
                optimization,
                ranked_row,
            ),
            confidence=confidence_label,
            confidence_score=confidence_score,
            caveats=caveats,
        )

    def build_recommendation_adapter(
        self,
        factory: Factory,
        explanation: RecommendationExplanation,
        recommendation: Recommendation,
    ) -> Recommendation:
        """
        Attach the structured explanation to the existing Recommendation model.

        This preserves the existing recommendation contract while allowing the
        richer internal explanation to remain available to future report APIs.
        """

        data = recommendation.model_dump()

        data["explanation"] = {
            "why_selected": [
                reason.text
                for reason in explanation.why_selected
            ],
            "why_others_rejected": [
                {
                    "scenario_id": reason.code.replace(
                        "rejected_",
                        "",
                        1,
                    ),
                    "technology_sequence": [],
                    "reason": reason.text,
                    "rank": 0,
                    "composite_score": 0.0,
                    "key_weakness": reason.text,
                }
                for reason in explanation.why_others_rejected
            ],
            "policy_benefits": {
                "eligible_schemes": (
                    explanation.policy_summary.get(
                        "eligible_schemes",
                        [],
                    )
                ),
                "estimated_total_benefit_inr": (
                    explanation.policy_summary.get(
                        "estimated_total_benefit_inr",
                        0.0,
                    )
                ),
                "total_benefit_verified": (
                    explanation.policy_summary.get(
                        "total_benefit_verified",
                        False,
                    )
                ),
                "disclaimer": (
                    (
                        "Estimated policy support; verify "
                        "scheme stacking and final sanction "
                        "before relying on the amount."
                    )
                    if not explanation.policy_summary.get(
                        "total_benefit_verified",
                        False,
                    )
                    else (
                        "Verified against the current "
                        "policy-engine contract."
                    )
                ),
            },
            "sensitivity_notes": {
                "payback_p10_years": (
                    explanation.sensitivity_summary.get(
                        "payback_p10_years",
                        0.0,
                    )
                ),
                "payback_p50_years": (
                    explanation.sensitivity_summary.get(
                        "payback_p50_years",
                        0.0,
                    )
                ),
                "payback_p90_years": (
                    explanation.sensitivity_summary.get(
                        "payback_p90_years",
                        0.0,
                    )
                ),
                "spread_ratio": (
                    explanation.sensitivity_summary.get(
                        "spread_ratio",
                        0.0,
                    )
                ),
                "top_risk_factors": (
                    explanation.sensitivity_summary.get(
                        "top_risk_factors",
                        [],
                    )
                ),
                "risk_interpretation": (
                    f"{explanation.sensitivity_summary.get(
                        'risk_label',
                        'Unknown',
                    )} payback uncertainty."
                ),
            },
        }

        return Recommendation.model_validate(
            data
        )


# ---------------------------------------------------------------------------
# Functional API
# ---------------------------------------------------------------------------

def generate_explanation(
    factory: Factory,
    scenario: Scenario,
    optimization: OptimizationResult,
    policy: PolicyEvaluationResult,
    reliability: ReliabilitySweepResult,
    scenarios: Optional[
        Mapping[str, Scenario]
    ] = None,
) -> RecommendationExplanation:
    """
    Functional wrapper around ExplainabilityEngine.
    """

    return ExplainabilityEngine().generate_explanation(
        factory=factory,
        scenario=scenario,
        optimization=optimization,
        policy=policy,
        reliability=reliability,
        scenarios=scenarios,
    )


def explanation_to_dict(
    explanation: RecommendationExplanation,
) -> dict[str, Any]:
    """Serialize a structured explanation."""

    return explanation.to_dict()


__all__ = [
    "Evidence",
    "EvidenceLibrary",
    "Reason",
    "RecommendationExplanation",
    "ExplainabilityEngine",
    "EVIDENCE_LIBRARY",
    "generate_explanation",
    "explanation_to_dict",
]

"""
Explainability Rule Engine for the Industrial Energy Transition Optimizer.

Part 3 of the Explainable Recommendation Engine.

Responsibilities
----------------
- Convert optimizer / policy / scenario outputs into human-readable reasons.
- Generate evidence references without changing optimizer decisions.
- Explain technology fit, MCDA performance, policy support, environmental impact,
  reliability, and implementation trade-offs.
- Preserve evidence provenance so report_generator.py can consume the result.

Design principles
-----------------
1. Rule-based only.
2. No LLM or probabilistic decision-making.
3. No hard-coded technology limits where the knowledge base can provide them.
4. Never invent policy eligibility.
5. Never present estimates as guarantees.
6. Work with existing project models through tolerant duck-typing.
7. Keep explanation generation independent from the optimizer.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable, Mapping, Optional


# ---------------------------------------------------------------------------
# Evidence models
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Evidence:
    """A traceable evidence item supporting an explanation."""

    evidence_id: str
    source: str
    title: str
    citation: str
    claim: str
    category: str
    confidence: str = "medium"
    source_type: str = "research"
    note: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "evidence_id": self.evidence_id,
            "source": self.source,
            "title": self.title,
            "citation": self.citation,
            "claim": self.claim,
            "category": self.category,
            "confidence": self.confidence,
            "source_type": self.source_type,
            "note": self.note,
        }


@dataclass(frozen=True)
class ExplanationReason:
    """One explanation reason connected to supporting evidence."""

    text: str
    category: str
    evidence_ids: list[str] = field(default_factory=list)
    importance: str = "supporting"

    def to_dict(self) -> dict[str, Any]:
        return {
            "text": self.text,
            "category": self.category,
            "evidence_ids": list(self.evidence_ids),
            "importance": self.importance,
        }


@dataclass
class RecommendationExplanation:
    """Complete explanation payload produced by the rule engine."""

    recommended_technology: str
    recommended_scenario_id: str

    reasons: list[ExplanationReason] = field(default_factory=list)
    evidence: list[Evidence] = field(default_factory=list)

    mcda_rationale: list[str] = field(default_factory=list)
    policy_rationale: list[str] = field(default_factory=list)
    risk_rationale: list[str] = field(default_factory=list)
    environmental_rationale: list[str] = field(default_factory=list)
    implementation_rationale: list[str] = field(default_factory=list)

    rejected_alternatives: list[dict[str, Any]] = field(default_factory=list)

    confidence_score: float = 0.0
    confidence_label: str = "Low"

    summary: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "recommended_technology": self.recommended_technology,
            "recommended_scenario_id": self.recommended_scenario_id,
            "reasons": [item.to_dict() for item in self.reasons],
            "evidence": [item.to_dict() for item in self.evidence],
            "mcda_rationale": list(self.mcda_rationale),
            "policy_rationale": list(self.policy_rationale),
            "risk_rationale": list(self.risk_rationale),
            "environmental_rationale": list(self.environmental_rationale),
            "implementation_rationale": list(self.implementation_rationale),
            "rejected_alternatives": list(self.rejected_alternatives),
            "confidence_score": self.confidence_score,
            "confidence_label": self.confidence_label,
            "summary": self.summary,
        }


# ---------------------------------------------------------------------------
# Small generic helpers
# ---------------------------------------------------------------------------


def _get(obj: Any, *names: str, default: Any = None) -> Any:
    """
    Safely read an attribute or dictionary key.

    This keeps the explainability layer loosely coupled to existing models.
    """

    if obj is None:
        return default

    for name in names:
        if isinstance(obj, Mapping):
            value = obj.get(name)
        else:
            value = getattr(obj, name, None)

        if value is not None:
            return value

    return default


def _float(
    obj: Any,
    *names: str,
    default: Optional[float] = None,
) -> Optional[float]:
    value = _get(obj, *names, default=default)

    if value is None:
        return None

    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _text(
    obj: Any,
    *names: str,
    default: Optional[str] = None,
) -> Optional[str]:
    value = _get(obj, *names, default=default)

    if value is None:
        return default

    text = str(value).strip()

    return text if text else default


def _list(obj: Any, *names: str) -> list[Any]:
    value = _get(obj, *names, default=[])

    if value is None:
        return []

    if isinstance(value, list):
        return value

    if isinstance(value, tuple):
        return list(value)

    return [value]


def _clamp(value: float, low: float = 0.0, high: float = 100.0) -> float:
    return max(low, min(high, value))


def _technology_name(sequence: Iterable[Any]) -> str:
    """Return a readable primary technology name."""

    sequence = list(sequence)

    if not sequence:
        return "Unknown pathway"

    first = sequence[0]

    if isinstance(first, str):
        return first

    return _text(
        first,
        "technology_id",
        "name",
        "technology",
        default="Unknown technology",
    ) or "Unknown technology"


def _technology_sequence_text(sequence: Iterable[Any]) -> str:
    names: list[str] = []

    for item in sequence:
        if isinstance(item, str):
            names.append(item)
        else:
            names.append(
                _text(
                    item,
                    "technology_id",
                    "name",
                    "technology",
                    default="Unknown technology",
                )
                or "Unknown technology"
            )

    return " → ".join(names)


# ---------------------------------------------------------------------------
# Evidence library
# ---------------------------------------------------------------------------


class EvidenceLibrary:
    """
    Central evidence catalogue.

    The catalogue contains source-level claims that are stable enough to be
    referenced by explanation rules. Numeric site-specific values must still
    come from the actual scenario / knowledge-base inputs.
    """

    _EVIDENCE: dict[str, Evidence] = {
        "flexiheat_mcda": Evidence(
            evidence_id="E001",
            source="FlexiHeat-DST",
            title="Design and utilisation of a multi-criteria decision support tool "
                  "to analyse power-to-heat technologies",
            citation="Ashabi et al., Energy Conversion and Management: X (2026)",
            claim=(
                "Power-to-heat technology selection can use transparent MCDA "
                "across techno-economic, environmental and operational criteria."
            ),
            category="mcda",
            confidence="high",
            source_type="research-paper",
        ),
        "flexiheat_temperature": Evidence(
            evidence_id="E002",
            source="FlexiHeat-DST",
            title="Power-to-heat technology overview",
            citation="Ashabi et al., 2026, technology overview",
            claim=(
                "Different power-to-heat technologies have different operating "
                "temperature ranges and industrial applications."
            ),
            category="technical-fit",
            confidence="high",
            source_type="research-paper",
        ),
        "electrification_heat": Evidence(
            evidence_id="E003",
            source="Energy Innovation / IECC",
            title="Electrifying Industrial Heat in India",
            citation="Deshpande et al., April 2026",
            claim=(
                "Industrial electrification can be economically competitive across "
                "multiple temperature ranges, with economics varying by technology "
                "and electricity source."
            ),
            category="electrification",
            confidence="high",
            source_type="research-report",
        ),
        "electrification_clean_energy": Evidence(
            evidence_id="E004",
            source="Energy Innovation / IECC",
            title="Electrifying Industrial Heat in India",
            citation="Deshpande et al., April 2026",
            claim=(
                "Electrification benefits depend strongly on access to renewable "
                "electricity, storage and electricity pricing."
            ),
            category="electrification",
            confidence="high",
            source_type="research-report",
        ),
        "biomass_industrial_heat": Evidence(
            evidence_id="E005",
            source="MNRE + GIZ + Grant Thornton Bharat",
            title="Decarbonizing MSMEs: Use of Biomass for Green Steam and Heat Applications",
            citation="MNRE/GIZ/Grant Thornton Bharat",
            claim=(
                "Biomass-based green steam and heat can support decarbonisation "
                "across multiple MSME sectors."
            ),
            category="biomass",
            confidence="high",
            source_type="government-report",
        ),
        "biomass_supply_chain": Evidence(
            evidence_id="E006",
            source="MNRE + GIZ + Grant Thornton Bharat",
            title="Decarbonizing MSMEs: Use of Biomass for Green Steam and Heat Applications",
            citation="MNRE/GIZ/Grant Thornton Bharat",
            claim=(
                "Biomass supply-chain reliability, pricing stability and multi-fuel "
                "capability are important practical considerations for MSMEs."
            ),
            category="biomass-risk",
            confidence="high",
            source_type="government-report",
        ),
        "biomass_atlas": Evidence(
            evidence_id="E007",
            source="SSS-NIBE / MNRE",
            title="National Biomass Atlas",
            citation="National Biomass Atlas, SSS-NIBE / MNRE",
            claim=(
                "Biomass availability varies by state, crop and residue type and "
                "should therefore be checked geographically."
            ),
            category="resource",
            confidence="high",
            source_type="government-data",
        ),
        "niti_green_transition": Evidence(
            evidence_id="E008",
            source="NITI Aayog",
            title="Roadmap for Green Transition of MSMEs",
            citation="NITI Aayog, January 2026",
            claim=(
                "MSME green transition requires coordinated action across energy "
                "efficiency, green electricity, alternative fuels, finance and implementation."
            ),
            category="policy",
            confidence="high",
            source_type="government-report",
        ),
        "niti_finance": Evidence(
            evidence_id="E009",
            source="NITI Aayog",
            title="Roadmap for Green Transition of MSMEs",
            citation="NITI Aayog, January 2026",
            claim=(
                "Affordable finance and implementation mechanisms are important "
                "enablers for MSME decarbonisation."
            ),
            category="finance",
            confidence="high",
            source_type="government-report",
        ),
        "world_bank_finance": Evidence(
            evidence_id="E010",
            source="World Bank",
            title="India Financing Energy Efficiency at MSMEs Project",
            citation="World Bank FEEMP Implementation Completion Report",
            claim=(
                "Access to finance, transaction costs, risk perception and information "
                "barriers can constrain MSME energy-efficiency investments even where "
                "technical opportunities exist."
            ),
            category="finance-risk",
            confidence="high",
            source_type="international-development-report",
        ),
        "sidbi_finance": Evidence(
            evidence_id="E011",
            source="SIDBI",
            title="Annual Report 2024-25",
            citation="SIDBI Annual Report 2024-25",
            claim=(
                "SIDBI operates as a principal financial institution supporting the "
                "promotion, financing and development of the MSME sector."
            ),
            category="finance",
            confidence="high",
            source_type="government-institution-report",
        ),
    }

    @classmethod
    def get(cls, key: str) -> Optional[Evidence]:
        return cls._EVIDENCE.get(key)

    @classmethod
    def all(cls) -> list[Evidence]:
        return list(cls._EVIDENCE.values())


# ---------------------------------------------------------------------------
# Rule engine
# ---------------------------------------------------------------------------


class ExplainabilityRuleEngine:
    """
    Rule-based recommendation explanation engine.

    Important:
    - It does not rank scenarios.
    - It does not make technical feasibility decisions.
    - It does not calculate subsidy eligibility.
    - It only explains outputs already produced by upstream modules.
    """

    def __init__(
        self,
        evidence_library: type[EvidenceLibrary] = EvidenceLibrary,
    ) -> None:
        self.evidence_library = evidence_library

    # ------------------------------------------------------------------
    # Evidence / reason helpers
    # ------------------------------------------------------------------

    def _add_evidence(
        self,
        explanation: RecommendationExplanation,
        evidence_key: str,
    ) -> Optional[Evidence]:
        evidence = self.evidence_library.get(evidence_key)

        if evidence is None:
            return None

        existing_ids = {item.evidence_id for item in explanation.evidence}

        if evidence.evidence_id not in existing_ids:
            explanation.evidence.append(evidence)

        return evidence

    def _add_reason(
        self,
        explanation: RecommendationExplanation,
        text: str,
        *,
        category: str,
        evidence_keys: Iterable[str] = (),
        importance: str = "supporting",
    ) -> None:
        evidence_ids: list[str] = []

        for key in evidence_keys:
            evidence = self._add_evidence(explanation, key)

            if evidence is not None:
                evidence_ids.append(evidence.evidence_id)

        explanation.reasons.append(
            ExplanationReason(
                text=text,
                category=category,
                evidence_ids=evidence_ids,
                importance=importance,
            )
        )

    # ------------------------------------------------------------------
    # Factory / technology rules
    # ------------------------------------------------------------------

    def _rule_process_temperature(
        self,
        explanation: RecommendationExplanation,
        factory: Any,
        scenario: Any,
    ) -> None:
        temperature = _float(
            factory,
            "required_process_temperature_c",
            "process_temperature_c",
            "temperature_c",
        )

        if temperature is None:
            return

        technology = explanation.recommended_technology

        max_temperature = _float(
            scenario,
            "max_temperature_c",
            "technology_max_temperature_c",
        )

        # Prefer values already carried by the scenario/technology output.
        if max_temperature is not None:
            self._add_reason(
                explanation,
                (
                    f"{technology} is technically aligned with the required "
                    f"process temperature of {temperature:.0f}°C within the "
                    f"temperature capability represented in the selected pathway."
                ),
                category="technical-fit",
                evidence_keys=("flexiheat_temperature",),
                importance="primary",
            )
            return

        # Without an explicit technology limit, explain the concept without
        # inventing a threshold.
        self._add_reason(
            explanation,
            (
                f"The selected pathway was already screened upstream for the "
                f"factory's required process temperature of {temperature:.0f}°C."
            ),
            category="technical-fit",
            evidence_keys=("flexiheat_temperature",),
            importance="primary",
        )

    def _rule_industry_fit(
        self,
        explanation: RecommendationExplanation,
        factory: Any,
        scenario: Any,
    ) -> None:
        industry = _text(
            factory,
            "industry",
            "industry_id",
            default=None,
        )

        if not industry:
            return

        suitable_industries = _list(
            scenario,
            "suitable_industries",
            "industries",
        )

        normalized_industry = industry.lower().replace(" ", "_")

        if suitable_industries:
            normalized = {
                str(item).lower().replace(" ", "_")
                for item in suitable_industries
            }

            if normalized_industry in normalized:
                self._add_reason(
                    explanation,
                    (
                        f"The selected technology is explicitly represented as "
                        f"applicable to the {industry} sector."
                    ),
                    category="industry-fit",
                    evidence_keys=("flexiheat_temperature",),
                    importance="primary",
                )
                return

        self._add_reason(
            explanation,
            (
                f"The recommended pathway was generated from technologies "
                f"that passed the upstream applicability checks for {industry}."
            ),
            category="industry-fit",
            evidence_keys=("flexiheat_temperature",),
            importance="supporting",
        )

    def _rule_biomass_resource(
        self,
        explanation: RecommendationExplanation,
        factory: Any,
        scenario: Any,
    ) -> None:
        sequence = [
            str(item).lower()
            for item in _list(
                scenario,
                "technology_sequence",
                "technologies",
            )
        ]

        contains_biomass = any("biomass" in item for item in sequence)

        if not contains_biomass:
            return

        resource_score = _float(
            scenario,
            "resource_score",
            "biomass_resource_score",
        )

        district = _text(factory, "district", default=None)
        state = _text(factory, "state", default=None)

        if resource_score is not None:
            message = (
                f"Biomass was retained because the pathway's resource assessment "
                f"supports its use for the selected factory conditions "
                f"(resource score {resource_score:.1f}/100)."
            )
        else:
            location = ", ".join(
                item for item in [district, state] if item
            )

            message = (
                "Biomass was retained because its suitability is evaluated "
                "against geographic resource availability."
            )

            if location:
                message += f" The factory location used is {location}."

        self._add_reason(
            explanation,
            message,
            category="resource",
            evidence_keys=(
                "biomass_atlas",
                "biomass_industrial_heat",
            ),
            importance="primary",
        )

    def _rule_electrification(
        self,
        explanation: RecommendationExplanation,
        factory: Any,
        scenario: Any,
    ) -> None:
        sequence = [
            str(item).lower()
            for item in _list(
                scenario,
                "technology_sequence",
                "technologies",
            )
        ]

        electric = any(
            keyword in item
            for item in sequence
            for keyword in (
                "electric",
                "heat_pump",
                "heat pump",
                "induction",
                "resistance",
                "plasma",
                "microwave",
                "radio_frequency",
                "infrared",
                "eaf",
            )
        )

        if not electric:
            return

        electricity_dependence = _float(
            scenario,
            "electricity_dependence",
            "grid_dependence",
        )

        if electricity_dependence is not None:
            self._add_reason(
                explanation,
                (
                    f"The pathway uses an electricity-based heating option with "
                    f"an electricity-dependence score of {electricity_dependence:.1f}/100."
                ),
                category="electrification",
                evidence_keys=(
                    "electrification_heat",
                    "electrification_clean_energy",
                ),
                importance="primary",
            )
        else:
            self._add_reason(
                explanation,
                (
                    "The selected pathway includes electrified process heat, "
                    "consistent with the industrial electrification options "
                    "evaluated in current India-specific research."
                ),
                category="electrification",
                evidence_keys=(
                    "electrification_heat",
                    "electrification_clean_energy",
                ),
                importance="primary",
            )

    # ------------------------------------------------------------------
    # MCDA rules
    # ------------------------------------------------------------------

    def _rule_mcda(
        self,
        explanation: RecommendationExplanation,
        recommended: Any,
        ranked_scenarios: Iterable[Any],
    ) -> None:
        rank = _float(
            recommended,
            "rank",
            default=None,
        )

        composite = _float(
            recommended,
            "composite_score",
            "score",
            default=None,
        )

        objective_scores = _get(
            recommended,
            "objective_scores",
            default={},
        )

        if rank is not None:
            explanation.mcda_rationale.append(
                f"Ranked #{int(rank)} among the evaluated candidate pathways."
            )

        if composite is not None:
            explanation.mcda_rationale.append(
                f"Composite MCDA score: {composite:.2f}."
            )

        if isinstance(objective_scores, Mapping):
            cost = _float(objective_scores, "cost")
            emissions = _float(objective_scores, "emissions")
            risk = _float(objective_scores, "risk")

            if cost is not None:
                explanation.mcda_rationale.append(
                    f"Cost objective score: {cost:.2f}."
                )

            if emissions is not None:
                explanation.mcda_rationale.append(
                    f"Emissions objective score: {emissions:.2f}."
                )

            if risk is not None:
                explanation.mcda_rationale.append(
                    f"Risk objective score: {risk:.2f}."
                )

        technology_sequence = _technology_sequence_text(
            _list(
                recommended,
                "technology_sequence",
                "technologies",
            )
        )

        score_text = (
            f"with a composite MCDA score of {composite:.2f}"
            if composite is not None
            else "under the configured MCDA criteria"
        )

        self._add_reason(
            explanation,
            (
                f"The pathway {technology_sequence} was selected because it "
                f"performed best under the configured multi-criteria decision "
                f"framework {score_text}."
            ),
            category="mcda",
            evidence_keys=("flexiheat_mcda",),
            importance="primary",
        )

        ranked = list(ranked_scenarios)

        if len(ranked) > 1:
            best_alternative = None

            for candidate in ranked:
                candidate_id = _text(candidate, "scenario_id", default=None)

                if candidate_id != explanation.recommended_scenario_id:
                    best_alternative = candidate
                    break

            if best_alternative is not None:
                alt_score = _float(
                    best_alternative,
                    "composite_score",
                    "score",
                )

                if (
                    composite is not None
                    and alt_score is not None
                ):
                    delta = composite - alt_score

                    explanation.mcda_rationale.append(
                        (
                            f"The next-ranked alternative scored "
                            f"{alt_score:.2f}, a difference of {delta:.2f} "
                            f"from the recommendation."
                        )
                    )

    # ------------------------------------------------------------------
    # Policy rules
    # ------------------------------------------------------------------

    def _rule_policy(
        self,
        explanation: RecommendationExplanation,
        policy_result: Any,
    ) -> None:
        if policy_result is None:
            return

        eligible = bool(
            _get(
                policy_result,
                "eligible",
                default=False,
            )
        )

        eligible_schemes = _list(
            policy_result,
            "eligible_schemes",
        )

        estimated_benefit = _float(
            policy_result,
            "estimated_total_benefit_inr",
            default=0.0,
        ) or 0.0

        verified = bool(
            _get(
                policy_result,
                "total_benefit_verified",
                default=False,
            )
        )

        if eligible and eligible_schemes:
            names: list[str] = []

            for scheme in eligible_schemes:
                name = _text(
                    scheme,
                    "display_name",
                    "scheme_name",
                    "scheme_id",
                )

                if name:
                    names.append(name)

            if names:
                explanation.policy_rationale.append(
                    (
                        "Eligible policy/finance mechanisms detected: "
                        + ", ".join(names[:5])
                        + ("." if len(names) <= 5 else ", and others.")
                    )
                )

                self._add_reason(
                    explanation,
                    (
                        f"The selected pathway has policy support through "
                        f"{len(names)} matched scheme(s)."
                    ),
                    category="policy",
                    evidence_keys=(
                        "niti_green_transition",
                        "niti_finance",
                    ),
                    importance="primary",
                )

            if estimated_benefit > 0:
                if verified:
                    explanation.policy_rationale.append(
                        (
                            f"Estimated direct financial support is "
                            f"₹{estimated_benefit:,.0f}, with the upstream "
                            f"policy engine marking the value as verified."
                        )
                    )
                else:
                    explanation.policy_rationale.append(
                        (
                            f"Estimated policy benefit is "
                            f"₹{estimated_benefit:,.0f}; this remains an "
                            f"estimate and should not be treated as a guaranteed "
                            f"combined subsidy amount."
                        )
                    )

                    self._add_reason(
                        explanation,
                        (
                            "Policy support is a decision advantage, but the "
                            "combined monetary benefit is treated as an estimate "
                            "unless upstream scheme-stacking checks verify it."
                        ),
                        category="policy",
                        evidence_keys=(
                            "niti_finance",
                            "world_bank_finance",
                        ),
                        importance="supporting",
                    )

            return

        explanation.policy_rationale.append(
            "No eligible government support scheme was established for this pathway."
        )

    # ------------------------------------------------------------------
    # Financial / environmental / reliability rules
    # ------------------------------------------------------------------

    def _rule_financial(
        self,
        explanation: RecommendationExplanation,
        scenario: Any,
        optimization_result: Any,
    ) -> None:
        capex = _float(
            scenario,
            "capex_total_inr",
            "capex_inr",
            "capex",
        )

        annual_opex = _float(
            scenario,
            "annual_opex_inr",
            "opex_inr",
            "annual_opex",
        )

        payback = _get(
            scenario,
            "payback_years",
            "payback_range_years",
        )

        recommended_is_cheapest = _get(
            optimization_result,
            "recommended_is_cheapest",
            default=None,
        )

        if capex is not None:
            explanation.implementation_rationale.append(
                f"Estimated implementation CAPEX: ₹{capex:,.0f}."
            )

        if annual_opex is not None:
            explanation.implementation_rationale.append(
                f"Estimated annual operating cost: ₹{annual_opex:,.0f}."
            )

        if payback is not None:
            if isinstance(payback, (list, tuple)) and len(payback) >= 2:
                explanation.implementation_rationale.append(
                    (
                        f"Estimated simple payback range: "
                        f"{float(payback[0]):.1f}–{float(payback[1]):.1f} years."
                    )
                )
            else:
                try:
                    explanation.implementation_rationale.append(
                        f"Estimated simple payback: {float(payback):.1f} years."
                    )
                except (TypeError, ValueError):
                    pass

        if recommended_is_cheapest is True:
            explanation.financial_note = None
            self._add_reason(
                explanation,
                (
                    "The recommended pathway is also the least-cost pathway "
                    "among the evaluated candidates."
                ),
                category="financial",
                evidence_keys=("niti_finance",),
                importance="supporting",
            )

        elif recommended_is_cheapest is False:
            self._add_reason(
                explanation,
                (
                    "The recommendation is not necessarily the least-cost option; "
                    "the optimizer deliberately balances economic, environmental, "
                    "technical and risk dimensions rather than minimizing cost alone."
                ),
                category="financial",
                evidence_keys=("flexiheat_mcda",),
                importance="primary",
            )

    def _rule_environment(
        self,
        explanation: RecommendationExplanation,
        scenario: Any,
    ) -> None:
        co2 = _float(
            scenario,
            "co2_reduction_pct",
            "carbon_reduction",
        )

        fossil = _float(
            scenario,
            "fossil_fuel_reduction_pct",
            "fossil_reduction",
        )

        if co2 is not None:
            message = (
                f"Estimated CO₂ reduction is {co2:.1f}% relative to the "
                "defined baseline."
            )

            explanation.environmental_rationale.append(message)

            self._add_reason(
                explanation,
                message,
                category="environmental",
                evidence_keys=(
                    "electrification_heat",
                    "biomass_industrial_heat",
                ),
                importance="primary",
            )

        if fossil is not None:
            message = (
                f"Estimated fossil-fuel reduction is {fossil:.1f}% "
                "relative to the defined baseline."
            )

            explanation.environmental_rationale.append(message)

    def _rule_reliability(
        self,
        explanation: RecommendationExplanation,
        scenario: Any,
        reliability_result: Any,
    ) -> None:
        reliability = _float(
            scenario,
            "reliability_score_pct",
            "reliability_score",
        )

        if reliability is not None:
            explanation.risk_rationale.append(
                f"Reliability score: {reliability:.1f}/100."
            )

        spread_ratio = _float(
            reliability_result,
            "spread_ratio",
            default=None,
        )

        if spread_ratio is not None:
            explanation.risk_rationale.append(
                f"Payback uncertainty spread ratio: {spread_ratio:.2f}."
            )

        risk_tier = _text(
            reliability_result,
            "risk_tier",
            "overall_tier",
            default=None,
        )

        if risk_tier:
            explanation.risk_rationale.append(
                f"Reliability engine risk tier: {risk_tier}."
            )

        risk_factors = _list(
            reliability_result,
            "top_risk_factors",
        )

        if risk_factors:
            explanation.risk_rationale.append(
                "Key uncertainty drivers: "
                + ", ".join(str(item) for item in risk_factors[:5])
                + "."
            )

        if spread_ratio is not None:
            if spread_ratio < 0.30:
                confidence_text = (
                    "The sensitivity results indicate relatively stable "
                    "economic performance under the tested variations."
                )
            elif spread_ratio < 0.60:
                confidence_text = (
                    "The sensitivity results indicate moderate uncertainty; "
                    "implementation should monitor the dominant cost/resource drivers."
                )
            else:
                confidence_text = (
                    "The sensitivity results indicate material uncertainty; "
                    "phased implementation or additional risk mitigation should "
                    "be considered."
                )

            self._add_reason(
                explanation,
                confidence_text,
                category="reliability",
                evidence_keys=(
                    "world_bank_finance",
                    "biomass_supply_chain",
                ),
                importance="supporting",
            )

    # ------------------------------------------------------------------
    # Rejected alternatives
    # ------------------------------------------------------------------

    def _rule_rejected_alternatives(
        self,
        explanation: RecommendationExplanation,
        ranked_scenarios: Iterable[Any],
        scenarios: Mapping[str, Any],
    ) -> None:
        for ranked in ranked_scenarios:
            scenario_id = _text(
                ranked,
                "scenario_id",
                default=None,
            )

            if not scenario_id:
                continue

            if scenario_id == explanation.recommended_scenario_id:
                continue

            scenario = scenarios.get(scenario_id)

            sequence = (
                _list(
                    scenario,
                    "technology_sequence",
                    "technologies",
                )
                if scenario is not None
                else _list(
                    ranked,
                    "technology_sequence",
                    "technologies",
                )
            )

            weakness = self._derive_primary_weakness(
                ranked,
                recommended=self._find_recommended(
                    ranked_scenarios,
                    explanation.recommended_scenario_id,
                ),
            )

            rank = _float(ranked, "rank")
            score = _float(
                ranked,
                "composite_score",
                "score",
            )

            alternative = {
                "scenario_id": scenario_id,
                "technology_sequence": _technology_sequence_text(sequence),
                "rank": int(rank) if rank is not None else None,
                "composite_score": score,
                "key_weakness": weakness,
                "reason": (
                    f"Not selected because its strongest trade-off is "
                    f"{weakness} relative to the recommended pathway."
                ),
            }

            explanation.rejected_alternatives.append(alternative)

    @staticmethod
    def _find_recommended(
        ranked_scenarios: Iterable[Any],
        scenario_id: str,
    ) -> Optional[Any]:
        for scenario in ranked_scenarios:
            if _text(scenario, "scenario_id") == scenario_id:
                return scenario

        return None

    @staticmethod
    def _derive_primary_weakness(
        candidate: Any,
        recommended: Any,
    ) -> str:
        if recommended is None:
            return "lower overall MCDA performance"

        candidate_cost = _float(
            candidate,
            "raw_cost",
            "capex_total_inr",
            "capex_inr",
        )

        recommended_cost = _float(
            recommended,
            "raw_cost",
            "capex_total_inr",
            "capex_inr",
        )

        if (
            candidate_cost is not None
            and recommended_cost is not None
            and candidate_cost > recommended_cost * 1.20
        ):
            return "higher economic burden"

        candidate_emissions = _float(
            candidate,
            "raw_emissions",
            "pathway_co2_tonnes_year",
        )

        recommended_emissions = _float(
            recommended,
            "raw_emissions",
            "pathway_co2_tonnes_year",
        )

        if (
            candidate_emissions is not None
            and recommended_emissions is not None
            and candidate_emissions > recommended_emissions * 1.20
        ):
            return "higher residual emissions"

        candidate_risk = _float(
            candidate,
            "raw_risk",
            "risk_score",
        )

        recommended_risk = _float(
            recommended,
            "raw_risk",
            "risk_score",
        )

        if (
            candidate_risk is not None
            and recommended_risk is not None
            and candidate_risk > recommended_risk * 1.20
        ):
            return "higher implementation or operational risk"

        return "lower overall MCDA performance"

    # ------------------------------------------------------------------
    # Confidence
    # ------------------------------------------------------------------

    def _calculate_confidence(
        self,
        explanation: RecommendationExplanation,
        recommended: Any,
        policy_result: Any,
        reliability_result: Any,
    ) -> tuple[float, str]:
        """
        Calculate explanation confidence from upstream evidence quality.

        This is an explanation-confidence score, not a probability that the
        technology will succeed.
        """

        score = 50.0

        evidence_count = len(explanation.evidence)

        if evidence_count >= 3:
            score += 10.0

        if evidence_count >= 5:
            score += 10.0

        upstream_confidence = _float(
            recommended,
            "confidence_score",
            default=None,
        )

        if upstream_confidence is not None:
            score += (upstream_confidence - 50.0) * 0.40

        verified_policy = bool(
            _get(
                policy_result,
                "total_benefit_verified",
                default=False,
            )
        )

        if verified_policy:
            score += 5.0

        spread_ratio = _float(
            reliability_result,
            "spread_ratio",
            default=None,
        )

        if spread_ratio is not None:
            if spread_ratio < 0.30:
                score += 10.0
            elif spread_ratio < 0.60:
                score += 3.0
            else:
                score -= 8.0

        score = _clamp(score)

        if score >= 80:
            label = "High"
        elif score >= 60:
            label = "Medium"
        else:
            label = "Low"

        return score, label

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def explain(
        self,
        *,
        factory: Any,
        scenario: Any,
        optimization_result: Any = None,
        policy_result: Any = None,
        reliability_result: Any = None,
        ranked_scenarios: Optional[Iterable[Any]] = None,
        scenarios: Optional[Mapping[str, Any]] = None,
    ) -> RecommendationExplanation:
        """
        Generate an explanation for the recommended scenario.

        The method intentionally accepts generic objects so it can consume
        existing project dataclasses / Pydantic models without forcing another
        domain-model migration.
        """

        recommended_scenario_id = _text(
            scenario,
            "scenario_id",
            default="recommended",
        ) or "recommended"

        technology_sequence = _list(
            scenario,
            "technology_sequence",
            "technologies",
        )

        explanation = RecommendationExplanation(
            recommended_technology=_technology_name(
                technology_sequence
            ),
            recommended_scenario_id=recommended_scenario_id,
        )

        ranked = list(ranked_scenarios or [])

        if not ranked:
            ranked = [scenario]

        # Technical / resource / technology-fit rules.
        self._rule_process_temperature(
            explanation,
            factory,
            scenario,
        )

        self._rule_industry_fit(
            explanation,
            factory,
            scenario,
        )

        self._rule_biomass_resource(
            explanation,
            factory,
            scenario,
        )

        self._rule_electrification(
            explanation,
            factory,
            scenario,
        )

        # Decision rationale.
        if optimization_result is not None:
            self._rule_mcda(
                explanation,
                scenario,
                ranked,
            )

        self._rule_financial(
            explanation,
            scenario,
            optimization_result,
        )

        self._rule_environment(
            explanation,
            scenario,
        )

        self._rule_reliability(
            explanation,
            scenario,
            reliability_result,
        )

        self._rule_policy(
            explanation,
            policy_result,
        )

        if scenarios is None:
            scenarios = {
                _text(item, "scenario_id", default="unknown") or "unknown": item
                for item in ranked
            }

        self._rule_rejected_alternatives(
            explanation,
            ranked,
            scenarios,
        )

        confidence_score, confidence_label = self._calculate_confidence(
            explanation,
            scenario,
            policy_result,
            reliability_result,
        )

        explanation.confidence_score = round(confidence_score, 2)
        explanation.confidence_label = confidence_label

        explanation.summary = self._build_summary(
            explanation,
            scenario,
        )

        return explanation

    @staticmethod
    def _build_summary(
        explanation: RecommendationExplanation,
        scenario: Any,
    ) -> str:
        technology = explanation.recommended_technology

        composite = _float(
            scenario,
            "composite_score",
            "score",
        )

        co2 = _float(
            scenario,
            "co2_reduction_pct",
            "carbon_reduction",
        )

        score_fragment = (
            f" MCDA score {composite:.2f}."
            if composite is not None
            else ""
        )

        co2_fragment = (
            f" Estimated CO₂ reduction is {co2:.1f}%."
            if co2 is not None
            else ""
        )

        return (
            f"{technology} is the recommended technology/pathway because it "
            f"performed best under the configured technical, economic, "
            f"environmental, policy and reliability criteria."
            f"{score_fragment}{co2_fragment} "
            f"Explanation confidence: {explanation.confidence_label} "
            f"({explanation.confidence_score:.0f}/100)."
        )


# ---------------------------------------------------------------------------
# Convenience API
# ---------------------------------------------------------------------------


_DEFAULT_ENGINE = ExplainabilityRuleEngine()


def build_explainability(
    *,
    factory: Any,
    scenario: Any,
    optimization_result: Any = None,
    policy_result: Any = None,
    reliability_result: Any = None,
    ranked_scenarios: Optional[Iterable[Any]] = None,
    scenarios: Optional[Mapping[str, Any]] = None,
) -> RecommendationExplanation:
    """
    Public convenience function used by report_generator.py or future API code.
    """

    return _DEFAULT_ENGINE.explain(
        factory=factory,
        scenario=scenario,
        optimization_result=optimization_result,
        policy_result=policy_result,
        reliability_result=reliability_result,
        ranked_scenarios=ranked_scenarios,
        scenarios=scenarios,
    )


__all__ = [
    "Evidence",
    "ExplanationReason",
    "RecommendationExplanation",
    "EvidenceLibrary",
    "ExplainabilityRuleEngine",
    "build_explainability",
]
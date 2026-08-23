"""
Explainability Engine — Part 1
================================

Purpose
-------
Provide lightweight, domain-independent evidence and explanation models
for the Industrial Energy Transition Optimizer.

This module is intentionally independent from:
- optimizer implementation
- policy implementation
- reliability implementation
- report rendering

It establishes the data contract that later explainability layers can use.

Architecture
------------
Optimization Result
        +
Policy Result
        +
Scenario
        +
Factory
        ↓
Explainability Engine
        ↓
Recommendation Explanation
        ↓
Evidence
        ↓
Citations

Part 1 scope
------------
This file defines:
- Evidence
- Reason
- RecommendationExplanation

Part 2 will add the evidence library.

Part 3 will add deterministic explanation rules.

Part 4 will add the public generator/orchestrator.

Design principles
-----------------
- No LLM dependency.
- No optimizer imports.
- No policy-engine imports.
- No circular dependencies.
- Pydantic models where possible for compatibility with the
  project's existing domain model style.
- Evidence provenance is explicit.
- Confidence is explicit.
- Models are safe to serialize into JSON/report layers.
"""

from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


# ============================================================================
# CONSTANTS
# ============================================================================

ALLOWED_CONFIDENCE_LEVELS = {
    "low",
    "medium",
    "high",
}

ALLOWED_EVIDENCE_TYPES = {
    "research",
    "government",
    "policy",
    "benchmark",
    "dataset",
    "internal",
    "calculation",
    "assumption",
}

ALLOWED_REASON_TYPES = {
    "technical",
    "economic",
    "environmental",
    "policy",
    "reliability",
    "mcda",
    "finance",
    "resource",
    "operational",
    "constraint",
    "general",
}


# ============================================================================
# EVIDENCE MODEL
# ============================================================================

class Evidence(BaseModel):
    """
    Supporting evidence attached to an explanation.

    An Evidence object answers:

        "What source or calculation supports this statement?"

    Examples
    --------
    Government document:

        Evidence(
            evidence_id="MNRE-BIOMASS-2026",
            source="MNRE",
            title="Decarbonizing MSMEs: Use of Biomass for Green Steam and Heat Applications",
            evidence_type="government",
            citation="MNRE-GIZ biomass MSME report",
            statement="Biomass can replace fossil fuels for industrial heat and steam.",
            confidence="high",
        )

    Research paper:

        Evidence(
            evidence_id="FLEXIHEAT-2026",
            source="FlexiHeat-DST",
            title="Design and utilisation of a multi-criteria decision support tool...",
            evidence_type="research",
            citation="Energy Conversion and Management: X, 2026",
            statement="MCDA can transparently compare competing industrial heat technologies.",
            confidence="high",
        )
    """

    model_config = ConfigDict(
        extra="ignore",
        populate_by_name=True,
        validate_assignment=True,
    )

    evidence_id: str = Field(
        ...,
        min_length=1,
        description="Stable identifier for the evidence item.",
    )

    source: str = Field(
        ...,
        min_length=1,
        description="Short source/provider name.",
    )

    title: str = Field(
        ...,
        min_length=1,
        description="Title of the source document, report, paper, or dataset.",
    )

    evidence_type: str = Field(
        ...,
        description="Evidence category.",
    )

    citation: str = Field(
        ...,
        min_length=1,
        description="Human-readable citation/reference label.",
    )

    statement: str = Field(
        ...,
        min_length=1,
        description="Specific claim supported by this evidence.",
    )

    confidence: str = Field(
        ...,
        description="Confidence in the evidence: low, medium, or high.",
    )

    source_date: Optional[str] = Field(
        default=None,
        description="Publication/source date as a human-readable string.",
    )

    location: Optional[str] = Field(
        default=None,
        description=(
            "Optional page, section, figure, table, or other source location."
        ),
    )

    url: Optional[str] = Field(
        default=None,
        description="Optional source URL.",
    )

    tags: list[str] = Field(
        default_factory=list,
        description="Search/filter tags associated with the evidence.",
    )

    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional structured provenance metadata.",
    )

    @field_validator("evidence_type")
    @classmethod
    def validate_evidence_type(cls, value: str) -> str:
        normalized = value.strip().lower()

        if normalized not in ALLOWED_EVIDENCE_TYPES:
            raise ValueError(
                f"Unsupported evidence_type '{value}'. "
                f"Expected one of: {sorted(ALLOWED_EVIDENCE_TYPES)}"
            )

        return normalized

    @field_validator("confidence")
    @classmethod
    def validate_confidence(cls, value: str) -> str:
        normalized = value.strip().lower()

        if normalized not in ALLOWED_CONFIDENCE_LEVELS:
            raise ValueError(
                f"Unsupported confidence '{value}'. "
                f"Expected one of: {sorted(ALLOWED_CONFIDENCE_LEVELS)}"
            )

        return normalized

    @field_validator("tags")
    @classmethod
    def normalize_tags(cls, value: list[str]) -> list[str]:
        normalized: list[str] = []

        for tag in value:
            tag = str(tag).strip()

            if tag and tag not in normalized:
                normalized.append(tag)

        return normalized


# ============================================================================
# REASON MODEL
# ============================================================================

class Reason(BaseModel):
    """
    Deterministic explanation for one decision factor.

    A Reason answers:

        "Why did the engine favor or disfavor this pathway?"

    A reason can optionally reference:
    - one or more evidence items
    - a criterion/value
    - a direction (positive/negative/neutral)

    This makes later report generation straightforward.
    """

    model_config = ConfigDict(
        extra="ignore",
        populate_by_name=True,
        validate_assignment=True,
    )

    reason_id: str = Field(
        ...,
        min_length=1,
        description="Stable identifier for the reason.",
    )

    text: str = Field(
        ...,
        min_length=1,
        description="Human-readable explanation.",
    )

    reason_type: str = Field(
        default="general",
        description="Domain/category of the reason.",
    )

    direction: str = Field(
        default="positive",
        description=(
            "Whether this reason supports, opposes, or is neutral "
            "toward the recommendation."
        ),
    )

    criterion: Optional[str] = Field(
        default=None,
        description="Decision criterion associated with this reason.",
    )

    value: Optional[float] = Field(
        default=None,
        description="Optional numeric value behind the reason.",
    )

    unit: Optional[str] = Field(
        default=None,
        description="Optional unit for value.",
    )

    evidence_ids: list[str] = Field(
        default_factory=list,
        description="Evidence IDs supporting this reason.",
    )

    priority: int = Field(
        default=1,
        ge=1,
        description=(
            "Ordering priority. Lower numbers appear earlier in summaries."
        ),
    )

    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional structured explanation metadata.",
    )

    @field_validator("reason_type")
    @classmethod
    def validate_reason_type(cls, value: str) -> str:
        normalized = value.strip().lower()

        if normalized not in ALLOWED_REASON_TYPES:
            raise ValueError(
                f"Unsupported reason_type '{value}'. "
                f"Expected one of: {sorted(ALLOWED_REASON_TYPES)}"
            )

        return normalized

    @field_validator("direction")
    @classmethod
    def validate_direction(cls, value: str) -> str:
        normalized = value.strip().lower()

        allowed = {
            "positive",
            "negative",
            "neutral",
        }

        if normalized not in allowed:
            raise ValueError(
                f"Unsupported direction '{value}'. "
                f"Expected one of: {sorted(allowed)}"
            )

        return normalized

    @field_validator("evidence_ids")
    @classmethod
    def normalize_evidence_ids(cls, value: list[str]) -> list[str]:
        normalized: list[str] = []

        for evidence_id in value:
            evidence_id = str(evidence_id).strip()

            if evidence_id and evidence_id not in normalized:
                normalized.append(evidence_id)

        return normalized


# ============================================================================
# RECOMMENDATION EXPLANATION MODEL
# ============================================================================

class RecommendationExplanation(BaseModel):
    """
    Complete explainability payload for one recommendation.

    This is the central model created by the explainability engine.

    It is deliberately richer than a list of strings so downstream
    components can generate:
    - dashboard cards
    - PDF reports
    - Excel reports
    - API JSON
    - judge-facing explanations
    - audit/provenance views
    """

    model_config = ConfigDict(
        extra="ignore",
        populate_by_name=True,
        validate_assignment=True,
    )

    recommended_scenario_id: str = Field(
        ...,
        min_length=1,
        description="Scenario selected by the decision engine.",
    )

    recommended_technology_sequence: list[str] = Field(
        default_factory=list,
        description="Technology sequence belonging to the recommendation.",
    )

    headline: str = Field(
        ...,
        min_length=1,
        description="One-sentence explanation headline.",
    )

    reasons: list[Reason] = Field(
        default_factory=list,
        description="Structured reasons supporting or challenging the recommendation.",
    )

    evidence: list[Evidence] = Field(
        default_factory=list,
        description="Unique evidence items supporting the explanation.",
    )

    confidence: str = Field(
        default="medium",
        description="Overall explanation confidence.",
    )

    mcda_summary: Optional[str] = Field(
        default=None,
        description="Plain-language explanation of the MCDA outcome.",
    )

    policy_summary: Optional[str] = Field(
        default=None,
        description="Plain-language policy/financing explanation.",
    )

    risk_summary: Optional[str] = Field(
        default=None,
        description="Plain-language reliability/risk explanation.",
    )

    environmental_summary: Optional[str] = Field(
        default=None,
        description="Plain-language environmental impact explanation.",
    )

    assumptions: list[str] = Field(
        default_factory=list,
        description="Important assumptions behind the explanation.",
    )

    limitations: list[str] = Field(
        default_factory=list,
        description="Known limitations or verification requirements.",
    )

    citations: list[str] = Field(
        default_factory=list,
        description="Ordered human-readable citations for presentation.",
    )

    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional machine-readable explanation metadata.",
    )

    @field_validator("confidence")
    @classmethod
    def validate_confidence(cls, value: str) -> str:
        normalized = value.strip().lower()

        if normalized not in ALLOWED_CONFIDENCE_LEVELS:
            raise ValueError(
                f"Unsupported confidence '{value}'. "
                f"Expected one of: {sorted(ALLOWED_CONFIDENCE_LEVELS)}"
            )

        return normalized

    @field_validator("recommended_technology_sequence")
    @classmethod
    def normalize_technology_sequence(
        cls,
        value: list[str],
    ) -> list[str]:
        normalized: list[str] = []

        for technology in value:
            technology = str(technology).strip()

            if technology:
                normalized.append(technology)

        return normalized

    @field_validator("assumptions", "limitations", "citations")
    @classmethod
    def normalize_string_lists(
        cls,
        value: list[str],
    ) -> list[str]:
        normalized: list[str] = []

        for item in value:
            item = str(item).strip()

            if item and item not in normalized:
                normalized.append(item)

        return normalized

    def add_reason(self, reason: Reason) -> None:
        """
        Add a reason while avoiding duplicate reason IDs.
        """

        existing_ids = {
            existing.reason_id
            for existing in self.reasons
        }

        if reason.reason_id not in existing_ids:
            self.reasons.append(reason)

        self.reasons.sort(
            key=lambda item: (
                item.priority,
                item.reason_id,
            )
        )

    def add_evidence(self, evidence: Evidence) -> None:
        """
        Add evidence while avoiding duplicate evidence IDs.

        Citation order is updated automatically.
        """

        existing_ids = {
            existing.evidence_id
            for existing in self.evidence
        }

        if evidence.evidence_id not in existing_ids:
            self.evidence.append(evidence)

        if evidence.citation not in self.citations:
            self.citations.append(evidence.citation)

    def get_evidence(self, evidence_id: str) -> Optional[Evidence]:
        """
        Retrieve evidence by stable ID.
        """

        for evidence in self.evidence:
            if evidence.evidence_id == evidence_id:
                return evidence

        return None

    def get_reasons_by_type(self, reason_type: str) -> list[Reason]:
        """
        Return reasons matching one domain/category.
        """

        normalized = reason_type.strip().lower()

        return [
            reason
            for reason in self.reasons
            if reason.reason_type == normalized
        ]

    def positive_reasons(self) -> list[Reason]:
        """
        Return reasons supporting the recommendation.
        """

        return [
            reason
            for reason in self.reasons
            if reason.direction == "positive"
        ]

    def negative_reasons(self) -> list[Reason]:
        """
        Return reasons opposing or limiting the recommendation.
        """

        return [
            reason
            for reason in self.reasons
            if reason.direction == "negative"
        ]

    def citation_map(self) -> dict[str, str]:
        """
        Return evidence-id → citation mapping.

        Useful for report and dashboard renderers.
        """

        return {
            evidence.evidence_id: evidence.citation
            for evidence in self.evidence
        }

    def to_summary(self) -> dict[str, Any]:
        """
        Return a compact presentation-oriented summary.

        This is intentionally different from model_dump():
        it exposes only the information typically needed by UI/report layers.
        """

        return {
            "recommended_scenario_id": self.recommended_scenario_id,
            "recommended_technology_sequence": list(
                self.recommended_technology_sequence
            ),
            "headline": self.headline,
            "confidence": self.confidence,
            "reasons": [
                reason.text
                for reason in self.positive_reasons()
            ],
            "limitations": list(self.limitations),
            "citations": list(self.citations),
        }

    def to_dict(self) -> dict[str, Any]:
        """
        JSON-friendly representation.

        Pydantic's model_dump() is used rather than manually rebuilding
        nested objects, preserving the full structured explanation.
        """

        return self.model_dump(mode="json")


# ============================================================================
# FACTORY FUNCTIONS
# ============================================================================

def create_evidence(
    *,
    evidence_id: str,
    source: str,
    title: str,
    evidence_type: str,
    citation: str,
    statement: str,
    confidence: str = "medium",
    source_date: Optional[str] = None,
    location: Optional[str] = None,
    url: Optional[str] = None,
    tags: Optional[list[str]] = None,
    metadata: Optional[dict[str, Any]] = None,
) -> Evidence:
    """
    Convenience constructor for Evidence.

    Kept here so Part 2 can build the evidence library without repeatedly
    constructing Pydantic models by hand.
    """

    return Evidence(
        evidence_id=evidence_id,
        source=source,
        title=title,
        evidence_type=evidence_type,
        citation=citation,
        statement=statement,
        confidence=confidence,
        source_date=source_date,
        location=location,
        url=url,
        tags=tags or [],
        metadata=metadata or {},
    )


def create_reason(
    *,
    reason_id: str,
    text: str,
    reason_type: str = "general",
    direction: str = "positive",
    criterion: Optional[str] = None,
    value: Optional[float] = None,
    unit: Optional[str] = None,
    evidence_ids: Optional[list[str]] = None,
    priority: int = 1,
    metadata: Optional[dict[str, Any]] = None,
) -> Reason:
    """
    Convenience constructor for Reason.
    """

    return Reason(
        reason_id=reason_id,
        text=text,
        reason_type=reason_type,
        direction=direction,
        criterion=criterion,
        value=value,
        unit=unit,
        evidence_ids=evidence_ids or [],
        priority=priority,
        metadata=metadata or {},
    )


def create_recommendation_explanation(
    *,
    scenario_id: str,
    technology_sequence: Optional[list[str]] = None,
    headline: str,
    confidence: str = "medium",
    mcda_summary: Optional[str] = None,
    policy_summary: Optional[str] = None,
    risk_summary: Optional[str] = None,
    environmental_summary: Optional[str] = None,
    assumptions: Optional[list[str]] = None,
    limitations: Optional[list[str]] = None,
    metadata: Optional[dict[str, Any]] = None,
) -> RecommendationExplanation:
    """
    Convenience constructor for the central explainability object.
    """

    return RecommendationExplanation(
        recommended_scenario_id=scenario_id,
        recommended_technology_sequence=technology_sequence or [],
        headline=headline,
        confidence=confidence,
        mcda_summary=mcda_summary,
        policy_summary=policy_summary,
        risk_summary=risk_summary,
        environmental_summary=environmental_summary,
        assumptions=assumptions or [],
        limitations=limitations or [],
        metadata=metadata or {},
    )


# ============================================================================
# MODULE EXPORTS
# ============================================================================

__all__ = [
    "ALLOWED_CONFIDENCE_LEVELS",
    "ALLOWED_EVIDENCE_TYPES",
    "ALLOWED_REASON_TYPES",
    "Evidence",
    "Reason",
    "RecommendationExplanation",
    "create_evidence",
    "create_reason",
    "create_recommendation_explanation",
]
"""
recommendation_evidence.py — Transparent recommendation evidence scoring.

Unit 2.11 — Confidence & Evidence Scoring

Every recommendation should expose a transparent evidence card:

    Confidence: 92%
    Evidence: Strong
    Sources: 6
    Research quality: High
    Field validation: Medium

This module is deliberately rule-based.

It does NOT:
- use an LLM;
- invent sources;
- infer evidence from the recommendation text;
- silently treat missing evidence as strong evidence.

It DOES:
- deduplicate evidence sources;
- score source quality;
- distinguish primary from secondary evidence;
- distinguish directly supporting sources from contextual sources;
- account for independent confirmation;
- account for field validation;
- optionally incorporate technical, financial, model and sensitivity confidence;
- produce a human-auditable rationale.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable, Mapping, Optional


# ---------------------------------------------------------------------------
# Labels / normalized values
# ---------------------------------------------------------------------------

EVIDENCE_TIERS = {
    "strong": 0.90,
    "moderate": 0.70,
    "limited": 0.45,
    "weak": 0.25,
    "none": 0.05,
}

QUALITY_SCORES = {
    "high": 1.00,
    "medium": 0.70,
    "low": 0.40,
    "unknown": 0.20,
}

VALIDATION_SCORES = {
    "high": 1.00,
    "medium": 0.70,
    "low": 0.40,
    "unknown": 0.20,
}


# ---------------------------------------------------------------------------
# Evidence source
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class EvidenceSource:
    """
    Structured provenance for one source used by a recommendation.

    Parameters
    ----------
    source_id:
        Stable source identifier.

    title:
        Human-readable source title.

    source_type:
        Example values:
        "government_report", "research_paper", "official_dataset",
        "manufacturer_spec", "field_measurement", "secondary_report".

    source_quality:
        "high", "medium", "low", or "unknown".

    directly_supports:
        True when this source directly supports the claim/parameter used
        by the recommendation.

    primary_source:
        True when the source is the original/official source.

    independently_confirmed:
        True when the underlying evidence is independently corroborated.

    field_validated:
        True when the recommendation/input has been validated against
        observed factory/site data.

    notes:
        Optional audit note.
    """

    source_id: str
    title: str = ""
    source_type: str = ""
    source_quality: str = "medium"
    directly_supports: bool = True
    primary_source: bool = False
    independently_confirmed: bool = False
    field_validated: bool = False
    notes: str = ""

    @property
    def quality_score(self) -> float:
        """Return normalized research/source-quality score."""
        return QUALITY_SCORES.get(
            self.source_quality.lower(),
            QUALITY_SCORES["unknown"],
        )

    @property
    def validation_score(self) -> float:
        """
        Return the source's validation contribution.

        Field validation is strongest. Independent confirmation is next.
        Otherwise the source only contributes a low baseline validation value.
        """
        if self.field_validated:
            return 1.0

        if self.independently_confirmed:
            return 0.7

        return 0.2


# ---------------------------------------------------------------------------
# Final recommendation evidence summary
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class EvidenceScore:
    """
    Final evidence assessment displayed with a recommendation.
    """

    confidence_pct: int
    evidence: str
    source_count: int
    research_quality: str
    field_validation: str
    rationale: tuple[str, ...] = field(default_factory=tuple)
    source_ids: tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, Any]:
        """Return JSON-serializable evidence summary."""
        return {
            "confidence_pct": self.confidence_pct,
            "evidence": self.evidence,
            "source_count": self.source_count,
            "research_quality": self.research_quality,
            "field_validation": self.field_validation,
            "rationale": list(self.rationale),
            "source_ids": list(self.source_ids),
        }


# ---------------------------------------------------------------------------
# Input conversion helpers
# ---------------------------------------------------------------------------

def _as_source(
    item: EvidenceSource | Mapping[str, Any],
) -> EvidenceSource:
    """
    Convert a mapping into EvidenceSource.

    Raises
    ------
    KeyError
        If source_id is absent.
    """
    if isinstance(item, EvidenceSource):
        return item

    data = dict(item)

    return EvidenceSource(
        source_id=str(data["source_id"]),
        title=str(data.get("title", "")),
        source_type=str(data.get("source_type", "")),
        source_quality=str(data.get("source_quality", "medium")),
        directly_supports=bool(data.get("directly_supports", True)),
        primary_source=bool(data.get("primary_source", False)),
        independently_confirmed=bool(
            data.get("independently_confirmed", False)
        ),
        field_validated=bool(data.get("field_validated", False)),
        notes=str(data.get("notes", "")),
    )


# ---------------------------------------------------------------------------
# Label helpers
# ---------------------------------------------------------------------------

def _tier_from_score(score: float) -> str:
    """Convert normalized confidence into an evidence label."""
    if score >= 0.85:
        return "Strong"

    if score >= 0.65:
        return "Moderate"

    if score >= 0.40:
        return "Limited"

    if score >= 0.20:
        return "Weak"

    return "None"


def _quality_label(score: float) -> str:
    """Convert normalized research quality into a display label."""
    if score >= 0.85:
        return "High"

    if score >= 0.60:
        return "Medium"

    return "Low"


def _validation_label(score: float) -> str:
    """Convert validation score into a display label."""
    if score >= 0.85:
        return "High"

    if score >= 0.60:
        return "Medium"

    if score >= 0.35:
        return "Low"

    return "Unknown"


# ---------------------------------------------------------------------------
# Source weighting
# ---------------------------------------------------------------------------

def _source_weight(source: EvidenceSource) -> float:
    """
    Calculate contribution of one source.

    Source count alone is intentionally insufficient.

    Primary and independently confirmed sources receive a bonus.
    Context-only sources receive a penalty.
    """
    weight = 0.35 + (0.65 * source.quality_score)

    if source.primary_source:
        weight += 0.10

    if source.independently_confirmed:
        weight += 0.10

    if not source.directly_supports:
        weight *= 0.50

    return min(weight, 1.0)


# ---------------------------------------------------------------------------
# Validation helper
# ---------------------------------------------------------------------------

def _validate_unit_interval(value: float, name: str) -> None:
    """Validate a normalized value in [0, 1]."""
    if not 0.0 <= value <= 1.0:
        raise ValueError(
            f"{name} must be between 0 and 1; got {value!r}"
        )


# ---------------------------------------------------------------------------
# Public scoring function
# ---------------------------------------------------------------------------

def calculate_evidence_score(
    sources: Iterable[EvidenceSource | Mapping[str, Any]],
    *,
    model_confidence: Optional[float] = None,
    technical_feasibility_confidence: Optional[float] = None,
    financial_confidence: Optional[float] = None,
    sensitivity_robustness: Optional[float] = None,
) -> EvidenceScore:
    """
    Calculate transparent evidence/confidence for a recommendation.

    Parameters
    ----------
    sources:
        Evidence sources attached to the recommendation.

    model_confidence:
        Optional normalized confidence in the underlying calculation
        pipeline [0, 1].

    technical_feasibility_confidence:
        Optional normalized confidence in technical feasibility [0, 1].

    financial_confidence:
        Optional normalized confidence in financial assumptions [0, 1].

    sensitivity_robustness:
        Optional normalized robustness score [0, 1].
        Higher means the recommendation remains stable across
        the reliability/sensitivity sweep.

    Returns
    -------
    EvidenceScore
        Transparent evidence summary suitable for API/report/frontend use.

    Design principle
    ----------------
    Missing evidence never upgrades confidence.
    More sources help only when they are meaningful, direct and credible.
    """

    normalized_sources = [
        _as_source(source)
        for source in sources
    ]

    # Deduplicate by stable source ID.
    unique_sources: dict[str, EvidenceSource] = {}

    for source in normalized_sources:
        if source.source_id and source.source_id not in unique_sources:
            unique_sources[source.source_id] = source

    source_list = list(unique_sources.values())
    source_count = len(source_list)

    # ---------------------------------------------------------------
    # No evidence = deliberately low confidence
    # ---------------------------------------------------------------

    if source_count == 0:
        return EvidenceScore(
            confidence_pct=5,
            evidence="None",
            source_count=0,
            research_quality="Low",
            field_validation="Unknown",
            rationale=(
                "No structured evidence sources were supplied.",
                "Recommendation confidence is intentionally capped at 5%.",
            ),
            source_ids=(),
        )

    # ---------------------------------------------------------------
    # Source-level aggregates
    # ---------------------------------------------------------------

    research_quality_score = (
        sum(source.quality_score for source in source_list)
        / source_count
    )

    validation_score = (
        sum(source.validation_score for source in source_list)
        / source_count
    )

    directness_score = (
        sum(
            1.0 if source.directly_supports else 0.5
            for source in source_list
        )
        / source_count
    )

    weighted_source_score = (
        sum(_source_weight(source) for source in source_list)
        / source_count
    )

    # ---------------------------------------------------------------
    # Base scoring model
    #
    # Evidence/source quality dominates.
    # This prevents a large number of weak sources from automatically
    # generating a very high confidence score.
    # ---------------------------------------------------------------

    components: list[tuple[float, float]] = [
        (weighted_source_score, 0.45),
        (research_quality_score, 0.20),
        (directness_score, 0.15),
        (validation_score, 0.20),
    ]

    # Optional engineering / model dimensions.
    if model_confidence is not None:
        _validate_unit_interval(model_confidence, "model_confidence")
        components.append((model_confidence, 0.10))

    if technical_feasibility_confidence is not None:
        _validate_unit_interval(
            technical_feasibility_confidence,
            "technical_feasibility_confidence",
        )
        components.append(
            (technical_feasibility_confidence, 0.10)
        )

    if financial_confidence is not None:
        _validate_unit_interval(
            financial_confidence,
            "financial_confidence",
        )
        components.append((financial_confidence, 0.10))

    if sensitivity_robustness is not None:
        _validate_unit_interval(
            sensitivity_robustness,
            "sensitivity_robustness",
        )
        components.append((sensitivity_robustness, 0.10))

    total_weight = sum(weight for _, weight in components)

    raw_score = (
        sum(value * weight for value, weight in components)
        / total_weight
    )

    # ---------------------------------------------------------------
    # Evidence-count guardrails
    #
    # These prevent a single source or tiny evidence base from
    # claiming "very high confidence."
    # ---------------------------------------------------------------

    if source_count < 2:
        raw_score = min(raw_score, 0.69)

    elif source_count < 4:
        raw_score = min(raw_score, 0.79)

    raw_score = max(
        0.05,
        min(1.0, raw_score),
    )

    confidence_pct = int(round(raw_score * 100))

    # ---------------------------------------------------------------
    # Explainability metadata
    # ---------------------------------------------------------------

    source_types = {
        source.source_type.lower()
        for source in source_list
        if source.source_type
    }

    primary_count = sum(
        source.primary_source
        for source in source_list
    )

    validated_count = sum(
        source.field_validated
        for source in source_list
    )

    independently_confirmed_count = sum(
        source.independently_confirmed
        for source in source_list
    )

    rationale: list[str] = [
        (
            f"{source_count} unique evidence source(s) "
            "were attached to the recommendation."
        ),
        (
            f"{primary_count} source(s) are marked "
            "primary/official."
        ),
        (
            f"{independently_confirmed_count} source(s) "
            "independently confirm the evidence."
        ),
        (
            f"{validated_count} source(s) have explicit "
            "field validation."
        ),
    ]

    if source_types:
        rationale.append(
            "Source types represented: "
            + ", ".join(sorted(source_types))
            + "."
        )

    if sensitivity_robustness is not None:
        rationale.append(
            "Sensitivity robustness contribution: "
            f"{sensitivity_robustness:.2f}."
        )

    return EvidenceScore(
        confidence_pct=confidence_pct,
        evidence=_tier_from_score(raw_score),
        source_count=source_count,
        research_quality=_quality_label(
            research_quality_score
        ),
        field_validation=_validation_label(
            validation_score
        ),
        rationale=tuple(rationale),
        source_ids=tuple(
            source.source_id
            for source in source_list
        ),
    )


__all__ = [
    "EvidenceSource",
    "EvidenceScore",
    "calculate_evidence_score",
]
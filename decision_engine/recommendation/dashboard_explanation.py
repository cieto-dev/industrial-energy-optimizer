
"""
dashboard_explanation.py
------------------------

Task 3.6 — Explainability Dashboard Data

Purpose
-------
Convert the existing recommendation/optimizer output into a compact,
frontend-ready explanation contract:

{
    "recommendation": "...",
    "reason": [...],
    "constraints": [...],
    "evidence": [...],
    "confidence": 0.91
}

Design principles
-----------------
- Deterministic: no LLM dependency.
- Uses only values already produced by upstream engines.
- Never invents technical, financial, policy, or evidence data.
- Preserves pathway provenance.
- Keeps frontend logic intentionally thin.
- Handles partial upstream results safely.
- Confidence is a bounded [0, 1] score derived from explicit signals.
"""

from __future__ import annotations

from typing import Any, Mapping, Sequence


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

DEFAULT_CONFIDENCE = 0.50

CONFIDENCE_BOUNDS = (0.0, 1.0)

MAX_REASONS = 6
MAX_CONSTRAINTS = 8
MAX_EVIDENCE = 8

# Evidence quality weights.
_EVIDENCE_CONFIDENCE_WEIGHT = {
    "high": 1.0,
    "medium": 0.75,
    "low": 0.50,
}

# Evidence type weights.
_EVIDENCE_TYPE_WEIGHT = {
    "government": 1.00,
    "policy": 0.95,
    "research": 0.90,
    "benchmark": 0.80,
    "dataset": 0.80,
    "calculation": 0.70,
    "internal": 0.65,
    "assumption": 0.45,
}


# ---------------------------------------------------------------------------
# Generic helpers
# ---------------------------------------------------------------------------

def _get(
    value: Any,
    *names: str,
    default: Any = None,
) -> Any:
    """Read the first available value from mappings or objects."""

    if value is None:
        return default

    for name in names:
        if isinstance(value, Mapping):
            candidate = value.get(name)
        else:
            candidate = getattr(value, name, None)

        if candidate is not None:
            return candidate

    return default


def _as_dict(value: Any) -> dict[str, Any]:
    """Convert common model/object shapes to a dictionary."""

    if value is None:
        return {}

    if isinstance(value, Mapping):
        return dict(value)

    if hasattr(value, "model_dump"):
        try:
            return dict(value.model_dump())
        except Exception:
            pass

    if hasattr(value, "dict"):
        try:
            return dict(value.dict())
        except Exception:
            pass

    if hasattr(value, "__dict__"):
        return dict(vars(value))

    return {}


def _list(value: Any) -> list[Any]:
    """Normalize optional iterable values into a list."""

    if value is None:
        return []

    if isinstance(value, list):
        return list(value)

    if isinstance(value, tuple):
        return list(value)

    if isinstance(value, set):
        return list(value)

    if isinstance(value, str):
        return [value]

    try:
        return list(value)
    except TypeError:
        return [value]


def _string_list(value: Any) -> list[str]:
    """Return clean, unique string values."""

    result: list[str] = []
    seen: set[str] = set()

    for item in _list(value):
        text = str(item).strip()

        if not text or text in seen:
            continue

        seen.add(text)
        result.append(text)

    return result


def _float(value: Any) -> float | None:
    """Safely convert a value to float."""

    if value is None:
        return None

    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _clamp(
    value: float,
    lower: float,
    upper: float,
) -> float:
    return max(lower, min(upper, value))


def _format_inr(value: float) -> str:
    """Format INR in a compact dashboard-friendly way."""

    absolute = abs(value)

    if absolute >= 10_000_000:
        return f"₹{value / 10_000_000:.2f} crore"

    if absolute >= 100_000:
        return f"₹{value / 100_000:.2f} lakh"

    return f"₹{value:,.0f}"


# ---------------------------------------------------------------------------
# Scenario helpers
# ---------------------------------------------------------------------------

def _scenario_id(scenario: Any) -> str | None:
    value = _get(
        scenario,
        "scenario_id",
        "id",
        "pathway_id",
    )

    if value is None:
        return None

    return str(value)


def _technology_sequence(scenario: Any) -> list[str]:
    value = _get(
        scenario,
        "technology_sequence",
        "technologies",
        "technology_pathway",
        default=[],
    )

    return _string_list(value)


def _composite_score(scenario: Any) -> float | None:
    return _float(
        _get(
            scenario,
            "composite_score",
            "score",
            "overall_score",
        )
    )


def _objective_scores(scenario: Any) -> dict[str, float]:
    raw = _get(
        scenario,
        "objective_scores",
        "criterion_scores",
        default={},
    )

    if not isinstance(raw, Mapping):
        return {}

    result: dict[str, float] = {}

    for key, value in raw.items():
        numeric = _float(value)

        if numeric is not None:
            result[str(key)] = numeric

    return result


def _is_feasible(scenario: Any) -> bool:
    explicit = _get(
        scenario,
        "feasible",
        "is_feasible",
        "technical_feasible",
    )

    if explicit is not None:
        if isinstance(explicit, bool):
            return explicit

        if isinstance(explicit, str):
            return explicit.strip().lower() not in {
                "false",
                "no",
                "failed",
                "rejected",
                "infeasible",
            }

        return bool(explicit)

    status = _get(
        scenario,
        "status",
        "constraint_status",
        "feasibility_status",
    )

    if isinstance(status, str):
        return status.strip().lower() not in {
            "failed",
            "rejected",
            "infeasible",
            "not_feasible",
        }

    return True


# ---------------------------------------------------------------------------
# Constraint extraction
# ---------------------------------------------------------------------------

def _extract_constraints(
    recommended: Any,
    constraints: Any = None,
) -> list[str]:
    """
    Extract explicit constraint information.

    Important:
    We do not invent missing constraints. An empty list means no explicit
    constraint message was supplied by the upstream engine.
    """

    result: list[str] = []

    candidates = [
        _get(
            recommended,
            "constraints",
            "constraint_reasons",
            "constraint_messages",
            "failed_constraints",
            "constraint_failures",
            "violations",
        ),
        _get(
            constraints,
            "constraints",
            "constraint_reasons",
            "constraint_messages",
            "failed_constraints",
            "constraint_failures",
            "violations",
        ),
        _get(
            constraints,
            "rejected_reasons",
            "rejection_reasons",
        ),
    ]

    for candidate in candidates:
        if isinstance(candidate, Mapping):
            for key, value in candidate.items():
                if isinstance(value, bool):
                    if value is False:
                        result.append(str(key))
                    continue

                if isinstance(value, Mapping):
                    passed = _get(
                        value,
                        "passed",
                        "feasible",
                        "valid",
                    )

                    if passed is False:
                        message = _get(
                            value,
                            "reason",
                            "message",
                            "description",
                            default=str(key),
                        )

                        result.append(str(message))

                else:
                    result.append(str(value))

        else:
            result.extend(_string_list(candidate))

    # If the selected scenario itself is infeasible, preserve that fact.
    if not _is_feasible(recommended):
        if not result:
            result.append(
                "Selected pathway is marked infeasible by the constraint layer."
            )

    return _dedupe(result)[:MAX_CONSTRAINTS]


# ---------------------------------------------------------------------------
# Reason extraction
# ---------------------------------------------------------------------------

def _collect_reason_candidates(
    recommendation: Any,
    recommended_scenario: Any,
    ranked_scenarios: Sequence[Any],
    baseline: Any,
    finance: Any,
    impact: Any,
    policy: Any,
    sensitivity: Any,
) -> list[str]:
    """Collect explicit and safely derivable reasons."""

    reasons: list[str] = []

    # Existing recommendation-builder explanation.
    explanation = _get(
        recommendation,
        "explanation",
        default=None,
    )

    reasons.extend(
        _string_list(
            _get(
                explanation,
                "why_selected",
                "reasons",
                default=[],
            )
        )
    )

    # Existing dashboard/recommendation payload fields.
    reasons.extend(
        _string_list(
            _get(
                recommendation,
                "reasons",
                "rank_reason",
                "optimizer_explanation",
                default=[],
            )
        )
    )

    # Explicit selected pathway metrics.
    composite = _composite_score(recommended_scenario)

    if composite is not None:
        reasons.append(
            f"Selected pathway achieved a composite score of {composite:.3f}."
        )

    technology_sequence = _technology_sequence(recommended_scenario)

    if technology_sequence:
        reasons.append(
            "Recommended pathway uses "
            + " → ".join(technology_sequence)
            + "."
        )

    # Ranking context.
    if ranked_scenarios:
        selected_id = _scenario_id(recommended_scenario)

        ranked_ids = [
            _scenario_id(item)
            for item in ranked_scenarios
        ]

        if selected_id in ranked_ids:
            rank = ranked_ids.index(selected_id) + 1

            reasons.append(
                f"Pathway ranked #{rank} among the evaluated candidate pathways."
            )

    # Cost comparison.
    selected_cost = _float(
        _get(
            recommended_scenario,
            "raw_cost",
            "lifecycle_cost",
            "total_cost",
            "annual_cost",
            default=None,
        )
    )

    if selected_cost is not None:
        reasons.append(
            f"Estimated pathway cost is {_format_inr(selected_cost)} under the "
            "configured assumptions."
        )

    # Annual savings.
    annual_savings = _float(
        _get(
            finance,
            "annual_savings_inr",
            "annual_savings",
            "annual_cost_savings_inr",
            default=None,
        )
    )

    if annual_savings is None:
        annual_savings = _float(
            _get(
                recommended_scenario,
                "annual_savings_inr",
                "annual_savings",
                default=None,
            )
        )

    if annual_savings is not None:
        reasons.append(
            f"Estimated annual operating savings are {_format_inr(annual_savings)}."
        )

    # CO2 reduction.
    co2_reduction = _float(
        _get(
            impact,
            "co2_reduction_pct",
            "carbon_reduction_pct",
            default=None,
        )
    )

    if co2_reduction is None:
        co2_reduction = _float(
            _get(
                recommended_scenario,
                "co2_reduction_pct",
                "carbon_reduction_pct",
                default=None,
            )
        )

    if co2_reduction is not None and co2_reduction > 0:
        reasons.append(
            f"Estimated CO2 reduction is {co2_reduction:.1f}% versus the configured baseline."
        )

    # Fossil reduction.
    fossil_reduction = _float(
        _get(
            impact,
            "fossil_fuel_reduction_pct",
            "fossil_reduction_pct",
            default=None,
        )
    )

    if fossil_reduction is None:
        fossil_reduction = _float(
            _get(
                recommended_scenario,
                "fossil_fuel_reduction_pct",
                "fossil_reduction_pct",
                default=None,
            )
        )

    if fossil_reduction is not None and fossil_reduction > 0:
        reasons.append(
            f"Estimated fossil-fuel dependence falls by approximately "
            f"{fossil_reduction:.1f}%."
        )

    # Policy support.
    eligible_schemes = _string_list(
        _get(
            policy,
            "eligible_schemes",
            "schemes",
            default=[],
        )
    )

    if eligible_schemes:
        reasons.append(
            "Policy analysis identified eligible support mechanisms: "
            + ", ".join(eligible_schemes[:3])
            + "."
        )

    # Sensitivity.
    risk_interpretation = _get(
        sensitivity,
        "risk_interpretation",
        default=None,
    )

    if risk_interpretation:
        reasons.append(str(risk_interpretation))

    # Baseline comparison.
    baseline_fuel = _get(
        baseline,
        "current_fuel",
        "fuel",
        "primary_fuel",
    )

    if baseline_fuel and technology_sequence:
        reasons.append(
            f"The pathway changes the current {baseline_fuel} energy pathway "
            "toward the selected technology sequence."
        )

    return _dedupe(reasons)[:MAX_REASONS]


# ---------------------------------------------------------------------------
# Evidence
# ---------------------------------------------------------------------------

def _flatten_evidence(value: Any) -> list[Any]:
    """Recursively collect evidence-like records."""

    result: list[Any] = []

    if value is None:
        return result

    if isinstance(value, Mapping):
        for key, item in value.items():
            normalized_key = str(key).strip().lower()

            if normalized_key in {
                "evidence",
                "evidence_items",
                "evidence_records",
                "sources",
                "source_records",
                "evidence_register",
            }:
                result.extend(_list(item))

            # Continue recursively because evidence may be nested.
            result.extend(_flatten_evidence(item))

    elif isinstance(value, (list, tuple, set)):
        for item in value:
            result.extend(_flatten_evidence(item))

    return result


def _normalize_evidence_item(item: Any) -> dict[str, Any]:
    """Normalize one evidence record for frontend use."""

    if isinstance(item, str):
        return {
            "source": item,
        }

    record = _as_dict(item)

    source = _get(
        record,
        "source",
        "provider",
        "organization",
        "publisher",
        "title",
    )

    title = _get(
        record,
        "title",
        "name",
        "document",
        "report",
    )

    statement = _get(
        record,
        "statement",
        "claim",
        "description",
        "text",
    )

    citation = _get(
        record,
        "citation",
        "reference",
        "citation_label",
    )

    location = _get(
        record,
        "location",
        "page",
        "section",
        "figure",
        "table",
    )

    confidence = str(
        _get(
            record,
            "confidence",
            "evidence_confidence",
            default="medium",
        )
    ).strip().lower()

    evidence_type = str(
        _get(
            record,
            "evidence_type",
            "type",
            "category",
            default="internal",
        )
    ).strip().lower()

    result: dict[str, Any] = {
        "source": str(source) if source is not None else "Unknown source",
        "title": str(title) if title is not None else "",
        "statement": str(statement) if statement is not None else "",
        "citation": str(citation) if citation is not None else "",
        "location": str(location) if location is not None else "",
        "confidence": confidence,
        "evidence_type": evidence_type,
    }

    url = _get(
        record,
        "url",
        "source_url",
        "link",
    )

    if url:
        result["url"] = str(url)

    evidence_id = _get(
        record,
        "evidence_id",
        "id",
        "claim_id",
    )

    if evidence_id:
        result["evidence_id"] = str(evidence_id)

    return result


def _evidence_quality(item: Mapping[str, Any]) -> float:
    """Compute a conservative evidence-quality score."""

    confidence = str(
        item.get(
            "confidence",
            "medium",
        )
    ).lower()

    evidence_type = str(
        item.get(
            "evidence_type",
            "internal",
        )
    ).lower()

    confidence_weight = _EVIDENCE_CONFIDENCE_WEIGHT.get(
        confidence,
        0.50,
    )

    type_weight = _EVIDENCE_TYPE_WEIGHT.get(
        evidence_type,
        0.60,
    )

    return (
        confidence_weight * 0.60
        + type_weight * 0.40
    )


def _extract_evidence(
    recommendation: Any,
    recommended_scenario: Any,
    baseline: Any,
    technology: Any,
    constraints: Any,
    finance: Any,
    impact: Any,
    policy: Any,
) -> list[dict[str, Any]]:
    """Extract and rank evidence records without inventing sources."""

    raw_items = _flatten_evidence(
        {
            "recommendation": recommendation,
            "scenario": recommended_scenario,
            "baseline": baseline,
            "technology": technology,
            "constraints": constraints,
            "finance": finance,
            "impact": impact,
            "policy": policy,
        }
    )

    normalized: list[dict[str, Any]] = []

    for item in raw_items:
        record = _normalize_evidence_item(item)

        # Ignore empty artificial shells.
        meaningful = any(
            record.get(field)
            for field in (
                "source",
                "title",
                "statement",
                "citation",
                "url",
            )
        )

        if meaningful:
            normalized.append(record)

    # Deduplicate.
    deduped: list[dict[str, Any]] = []
    seen: set[str] = set()

    for item in normalized:
        identity = "|".join(
            [
                item.get("source", ""),
                item.get("title", ""),
                item.get("citation", ""),
                item.get("statement", ""),
            ]
        )

        if identity in seen:
            continue

        seen.add(identity)
        deduped.append(item)

    # Highest-quality first.
    deduped.sort(
        key=_evidence_quality,
        reverse=True,
    )

    return deduped[:MAX_EVIDENCE]


# ---------------------------------------------------------------------------
# Confidence
# ---------------------------------------------------------------------------

def _confidence_from_signals(
    *,
    evidence: Sequence[Mapping[str, Any]],
    recommended: Any,
    ranked_scenarios: Sequence[Any],
    constraints: Any,
    finance: Any,
    impact: Any,
    policy: Any,
    sensitivity: Any,
) -> float:
    """
    Calculate a deterministic confidence score.

    Score components:
    - evidence quality
    - optimizer/ranking completeness
    - constraint validation
    - financial completeness
    - impact completeness
    - policy evidence
    - sensitivity availability

    This is a confidence in the *explanation quality*, not a probability
    that the investment will succeed.
    """

    score = 0.0
    total_weight = 0.0

    # 1. Evidence quality.
    evidence_weight = 0.30
    total_weight += evidence_weight

    if evidence:
        evidence_scores = [
            _evidence_quality(item)
            for item in evidence
        ]

        evidence_component = sum(evidence_scores) / len(evidence_scores)

        score += evidence_component * evidence_weight

    # 2. Ranking completeness.
    ranking_weight = 0.20
    total_weight += ranking_weight

    if ranked_scenarios:
        selected_id = _scenario_id(recommended)

        ranked_ids = {
            _scenario_id(item)
            for item in ranked_scenarios
        }

        ranking_component = (
            1.0
            if selected_id in ranked_ids
            else 0.50
        )

        if _composite_score(recommended) is not None:
            ranking_component = min(
                1.0,
                ranking_component + 0.15,
            )

        if _objective_scores(recommended):
            ranking_component = min(
                1.0,
                ranking_component + 0.15,
            )

        score += ranking_component * ranking_weight

    # 3. Constraints.
    constraint_weight = 0.15
    total_weight += constraint_weight

    if constraints is not None:
        status = str(
            _get(
                constraints,
                "status",
                default="",
            )
        ).lower()

        if status in {
            "success",
            "validated",
            "supported",
        }:
            constraint_component = 1.0
        elif status:
            constraint_component = 0.65
        else:
            constraint_component = 0.50

        score += constraint_component * constraint_weight

    # 4. Finance.
    finance_weight = 0.10
    total_weight += finance_weight

    finance_fields = [
        _get(finance, "capex_inr", "capex"),
        _get(finance, "annual_opex_inr", "annual_opex"),
        _get(finance, "annual_savings_inr", "annual_savings"),
        _get(
            finance,
            "payback_years",
            "payback_range_years",
            "payback",
        ),
    ]

    finance_component = (
        sum(item is not None for item in finance_fields)
        / len(finance_fields)
    )

    score += finance_component * finance_weight

    # 5. Impact.
    impact_weight = 0.10
    total_weight += impact_weight

    impact_fields = [
        _get(
            impact,
            "co2_reduction_pct",
            "carbon_reduction_pct",
        ),
        _get(
            impact,
            "fossil_fuel_reduction_pct",
            "fossil_reduction_pct",
        ),
    ]

    impact_component = (
        sum(item is not None for item in impact_fields)
        / len(impact_fields)
    )

    score += impact_component * impact_weight

    # 6. Policy.
    policy_weight = 0.05
    total_weight += policy_weight

    eligible = _get(
        policy,
        "eligible_schemes",
        "schemes",
    )

    if eligible is not None:
        score += policy_weight

    # 7. Sensitivity.
    sensitivity_weight = 0.10
    total_weight += sensitivity_weight

    if sensitivity is not None:
        risk = _get(
            sensitivity,
            "risk_interpretation",
            "top_risk_factors",
        )

        if risk is not None:
            score += sensitivity_weight
        else:
            score += sensitivity_weight * 0.50

    if total_weight <= 0:
        return DEFAULT_CONFIDENCE

    return round(
        _clamp(
            score / total_weight,
            *CONFIDENCE_BOUNDS,
        ),
        2,
    )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def build_dashboard_explanation(
    *,
    recommendation: Any,
    recommended_scenario: Any = None,
    ranked_scenarios: Sequence[Any] | None = None,
    baseline: Any = None,
    technology: Any = None,
    constraints: Any = None,
    finance: Any = None,
    impact: Any = None,
    policy: Any = None,
    sensitivity: Any = None,
) -> dict[str, Any]:
    """
    Build the exact frontend contract required by Task 3.6.

    Returns
    -------
    dict
        {
            "recommendation": str,
            "reason": list[str],
            "constraints": list[str],
            "evidence": list[dict],
            "confidence": float
        }

    Notes
    -----
    ``confidence`` measures explainability/evidence completeness. It is NOT
    an investment success probability.
    """

    recommendation_dict = _as_dict(recommendation)

    selected = (
        recommended_scenario
        if recommended_scenario is not None
        else _get(
            recommendation,
            "scenario",
            "recommended_scenario",
            default=None,
        )
    )

    if selected is None:
        selected = recommendation

    ranked = list(ranked_scenarios or [])

    # If only the recommendation object is available, preserve its own
    # identifier in a one-item ranking context.
    if not ranked:
        ranked = [selected]

    technology_sequence = _technology_sequence(selected)

    scenario_id = (
        _scenario_id(selected)
        or _scenario_id(recommendation)
        or _get(
            recommendation,
            "recommended_scenario_id",
            default=None,
        )
    )

    # ---------------------------------------------------------------
    # Recommendation headline
    # ---------------------------------------------------------------

    if technology_sequence:
        recommendation_text = (
            "Recommend "
            + " → ".join(technology_sequence)
        )
    elif scenario_id:
        recommendation_text = (
            f"Recommend pathway {scenario_id}"
        )
    else:
        recommendation_text = "Recommend the top-ranked feasible pathway"

    # Preserve any explicit upstream recommendation narrative.
    upstream_headline = _get(
        recommendation,
        "recommendation_text",
        "headline",
        "rank_reason",
        default=None,
    )

    if upstream_headline:
        recommendation_text = str(upstream_headline)

    # ---------------------------------------------------------------
    # Reasons
    # ---------------------------------------------------------------

    reasons = _collect_reason_candidates(
        recommendation=recommendation,
        recommended_scenario=selected,
        ranked_scenarios=ranked,
        baseline=baseline,
        finance=finance,
        impact=impact,
        policy=policy,
        sensitivity=sensitivity,
    )

    # ---------------------------------------------------------------
    # Constraints
    # ---------------------------------------------------------------

    constraint_messages = _extract_constraints(
        selected,
        constraints,
    )

    # ---------------------------------------------------------------
    # Evidence
    # ---------------------------------------------------------------

    evidence = _extract_evidence(
        recommendation=recommendation_dict,
        recommended_scenario=selected,
        baseline=baseline,
        technology=technology,
        constraints=constraints,
        finance=finance,
        impact=impact,
        policy=policy,
    )

    # ---------------------------------------------------------------
    # Confidence
    # ---------------------------------------------------------------

    confidence = _confidence_from_signals(
        evidence=evidence,
        recommended=selected,
        ranked_scenarios=ranked,
        constraints=constraints,
        finance=finance,
        impact=impact,
        policy=policy,
        sensitivity=sensitivity,
    )

    # ---------------------------------------------------------------
    # Final contract
    # ---------------------------------------------------------------

    return {
        "recommendation": recommendation_text,
        "reason": reasons,
        "constraints": constraint_messages,
        "evidence": evidence,
        "confidence": confidence,
    }


def build_dashboard_explanation_from_pipeline(
    *,
    pipeline: Mapping[str, Any],
) -> dict[str, Any]:
    """
    Convenience adapter for the existing /optimization/optimize pipeline.

    Expected structure:
        {
            "recommendation": ...,
            "ranked_pathways": [...],
            "technology_assessment": ...,
            "constraint_assessment": ...,
            "finance": ...,
            "biomass": ...,
            "knowledge_context": ...,
            ...
        }
    """

    return build_dashboard_explanation(
        recommendation=pipeline.get("recommendation"),
        recommended_scenario=(
            _get(
                pipeline.get("recommendation"),
                "scenario",
                default=None,
            )
        ),
        ranked_scenarios=pipeline.get(
            "ranked_pathways",
            [],
        ),
        baseline=pipeline.get(
            "baseline",
        ),
        technology=pipeline.get(
            "technology_assessment",
        ),
        constraints=pipeline.get(
            "constraint_assessment",
        ),
        finance=pipeline.get(
            "finance",
        ),
        impact=pipeline.get(
            "impact",
        ),
        policy=pipeline.get(
            "policy",
        ),
        sensitivity=pipeline.get(
            "sensitivity",
        ),
    )


def _dedupe(items: Sequence[str]) -> list[str]:
    """Deduplicate strings while keeping source order."""

    result: list[str] = []
    seen: set[str] = set()

    for item in items:
        normalized = str(item).strip()

        if not normalized or normalized in seen:
            continue

        seen.add(normalized)
        result.append(normalized)

    return result


__all__ = [
    "build_dashboard_explanation",
    "build_dashboard_explanation_from_pipeline",
]

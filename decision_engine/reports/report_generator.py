
"""
report_generator.py — Recommendation report generation and explainability
integration.

Purpose
-------
Assemble the final Recommendation object from the Decision Engine outputs:

- OptimizationResult
- PolicyEvaluationResult
- ReliabilitySweepResult
- Scenario data

The report layer is intentionally presentation-oriented. It does not perform
new optimization, financial modelling, or technical feasibility calculations.

Contract
--------
Input
-----
OptimizationResult
PolicyEvaluationResult
ReliabilitySweepResult
Scenario mapping

Output
------
Recommendation

The Recommendation contains:

- recommendation rationale
- rejected-scenario explanations
- policy-benefit summary
- sensitivity / uncertainty information
- confidence information when supplied by an explainability engine
- caveats and supporting evidence when supplied by an explainability engine

Design principles
-----------------
1. Keep the existing Recommendation schema compatible.
2. Never silently replace engine-derived values with report-layer estimates.
3. Keep explanations deterministic for identical engine outputs.
4. Preserve provenance through scenario IDs and technology sequences.
5. Treat policy stacking/combined benefits as estimates unless verified.
6. Do not fabricate evidence or confidence values when the upstream
   explainability contract is unavailable.

Source alignment
----------------
The project architecture defines the recommendation as the boundary between
technical reality and decision-making. The reporting layer therefore consumes
already-computed pathway, financial, policy, and reliability results and
explains them rather than changing them.

The current Recommendation model exposes the following explanation groups:

- why_selected
- why_others_rejected
- policy_benefits
- sensitivity_notes

This file also supports richer explainability payloads through a defensive
adapter so that a future/adjacent ExplainabilityEngine can be integrated
without breaking the current Recommendation model.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Iterable, List, Mapping, Optional

from decision_engine.optimizer.optimization_engine import OptimizationResult
from decision_engine.policy.policy_engine import PolicyEvaluationResult
from decision_engine.reliability.reliability_engine import ReliabilitySweepResult

from models.recommendation import (
    Explanation,
    PolicyBenefitSummary,
    Recommendation,
    RejectedScenarioExplanation,
    SensitivityAnalysis,
)
from models.scenario import Scenario


# ---------------------------------------------------------------------------
# Small utility helpers
# ---------------------------------------------------------------------------


def _safe_float(value: Any, default: float = 0.0) -> float:
    """Convert a value to float without allowing presentation code to fail."""
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _safe_int(value: Any, default: int = 0) -> int:
    """Convert a value to int without allowing presentation code to fail."""
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _get_mapping_value(
    obj: Any,
    name: str,
    default: Any = None,
) -> Any:
    """
    Read an attribute from an object or a key from a mapping.

    This lets the report generator tolerate dataclass/object/dict-based
    explainability payloads.
    """
    if obj is None:
        return default

    if isinstance(obj, Mapping):
        return obj.get(name, default)

    return getattr(obj, name, default)


def _format_percent(value: Any) -> str:
    """Return a human-readable percentage."""
    return f"{_safe_float(value):.1f}%"


# ---------------------------------------------------------------------------
# Explainability-engine compatibility helpers
# ---------------------------------------------------------------------------


def _resolve_explainability_payload(
    explainability_result: Any,
) -> Dict[str, Any]:
    """
    Normalize an optional ExplainabilityEngine result.

    Supported input shapes
    ----------------------
    The function deliberately accepts several equivalent representations:

    - None
    - pydantic model
    - dataclass
    - dict-like object
    - ordinary Python object exposing attributes

    No explainability values are invented here. Missing fields remain None.

    Expected richer fields, when available, include:
    - why_selected
    - why_others_rejected
    - supporting_evidence
    - policy_benefits
    - sensitivity_notes
    - confidence_score
    - confidence_level
    - caveats
    """
    if explainability_result is None:
        return {}

    field_names = (
        "why_selected",
        "why_others_rejected",
        "supporting_evidence",
        "policy_benefits",
        "sensitivity_notes",
        "confidence_score",
        "confidence_level",
        "caveats",
    )

    result: Dict[str, Any] = {}

    for field_name in field_names:
        value = _get_mapping_value(explainability_result, field_name, None)
        if value is not None:
            result[field_name] = value

    return result


def _normalize_string_list(value: Any) -> List[str]:
    """Normalize strings or iterables into a deterministic string list."""
    if value is None:
        return []

    if isinstance(value, str):
        return [value]

    if isinstance(value, Mapping):
        return [str(value)]

    try:
        return [str(item) for item in value]
    except TypeError:
        return [str(value)]


# ---------------------------------------------------------------------------
# Why-selected generation
# ---------------------------------------------------------------------------


def _generate_why_selected(
    optimization_result: OptimizationResult,
    policy_result: PolicyEvaluationResult,
    recommended_scenario: Scenario,
) -> List[str]:
    """
    Generate deterministic plain-language reasons for the recommendation.

    This is the compatibility fallback used when a richer explainability
    object is not yet available upstream.
    """
    reasons: List[str] = []

    recommended = next(
        (
            scenario
            for scenario in optimization_result.ranked_scenarios
            if scenario.scenario_id == optimization_result.recommended_scenario_id
        ),
        None,
    )

    if recommended is None:
        return [
            "The selected pathway is the optimizer's recommended feasible "
            "scenario, but detailed ranking information was unavailable."
        ]

    reasons.append(
        f"Ranked #{_safe_int(recommended.rank)} out of "
        f"{len(optimization_result.ranked_scenarios)} candidate pathways "
        "using multi-criteria analysis."
    )

    cost_score = _safe_float(
        recommended.objective_scores.get("cost", 0.0)
    )
    emissions_score = _safe_float(
        recommended.objective_scores.get("emissions", 0.0)
    )
    risk_score = _safe_float(
        recommended.objective_scores.get("risk", 0.0)
    )

    reasons.append(
        "Balanced objective scores were "
        f"cost={cost_score:.2f}, "
        f"emissions={emissions_score:.2f}, "
        f"risk={risk_score:.2f}."
    )

    if optimization_result.recommended_is_cheapest:
        reasons.append(
            "The recommended pathway is also the lowest-cost option among "
            "the ranked alternatives."
        )
    else:
        why_not_cheapest = str(
            getattr(
                optimization_result,
                "why_not_always_cheapest",
                "",
            )
            or ""
        ).strip()

        if why_not_cheapest:
            reasons.append(
                "The recommendation is not purely cost-minimizing because "
                f"{why_not_cheapest}"
            )
        else:
            reasons.append(
                "The recommendation trades some economic advantage for "
                "stronger performance on the other optimization objectives."
            )

    eligible_schemes = list(
        getattr(policy_result, "eligible_schemes", None) or []
    )

    if getattr(policy_result, "eligible", False) and eligible_schemes:
        scheme_names = [
            str(getattr(scheme, "display_name", scheme))
            for scheme in eligible_schemes
        ]

        preview = ", ".join(scheme_names[:3])

        if len(scheme_names) > 3:
            preview += f" and {len(scheme_names) - 3} others"

        reasons.append(
            f"Eligible policy schemes include: {preview}."
        )

    benefit = _safe_float(
        getattr(
            policy_result,
            "estimated_total_benefit_inr",
            0.0,
        )
    )

    if benefit > 0:
        reasons.append(
            "The policy evaluation estimates additional financial support "
            f"of approximately ₹{benefit:,.0f}, subject to the verification "
            "status reported below."
        )

    co2_reduction = _safe_float(
        getattr(
            recommended_scenario,
            "co2_reduction_pct",
            0.0,
        )
    )

    if co2_reduction > 0:
        reasons.append(
            f"Estimated CO2 reduction is {_format_percent(co2_reduction)}."
        )

    fossil_reduction = _safe_float(
        getattr(
            recommended_scenario,
            "fossil_fuel_reduction_pct",
            0.0,
        )
    )

    if fossil_reduction > 0:
        reasons.append(
            "Estimated fossil-fuel reduction is "
            f"{_format_percent(fossil_reduction)}."
        )

    return reasons


# ---------------------------------------------------------------------------
# Rejected scenario explanations
# ---------------------------------------------------------------------------


def _generate_why_others_rejected(
    optimization_result: OptimizationResult,
    scenarios: Dict[str, Scenario],
) -> List[RejectedScenarioExplanation]:
    """
    Explain each non-recommended scenario using its actual ranking metrics.

    The explanation intentionally identifies a single leading weakness rather
    than claiming that every alternative is universally inferior.

    The 1.2 ratio is a presentation-layer heuristic only. It must not be
    interpreted as a calibrated engineering or financial threshold.
    """
    rejected: List[RejectedScenarioExplanation] = []

    ranked = list(optimization_result.ranked_scenarios)

    if not ranked:
        return rejected

    recommended_ranked = next(
        (
            item
            for item in ranked
            if item.scenario_id == optimization_result.recommended_scenario_id
        ),
        ranked[0],
    )

    comparison_cost = max(
        _safe_float(recommended_ranked.raw_cost),
        0.0,
    )
    comparison_emissions = max(
        _safe_float(recommended_ranked.raw_emissions),
        0.0,
    )
    comparison_risk = max(
        _safe_float(recommended_ranked.raw_risk),
        0.0,
    )

    for ranked_scenario in ranked:
        if (
            ranked_scenario.scenario_id
            == optimization_result.recommended_scenario_id
        ):
            continue

        scenario = scenarios.get(ranked_scenario.scenario_id)

        if scenario is None:
            # Preserve the ranking information even when the scenario
            # dictionary is incomplete.
            technology_sequence: List[str] = []
        else:
            technology_sequence = list(
                getattr(
                    scenario,
                    "technology_sequence",
                    [],
                )
                or []
            )

        weakness = "lower overall composite score"

        raw_cost = _safe_float(ranked_scenario.raw_cost)
        raw_emissions = _safe_float(ranked_scenario.raw_emissions)
        raw_risk = _safe_float(ranked_scenario.raw_risk)

        if comparison_cost > 0 and raw_cost > comparison_cost * 1.2:
            weakness = "significantly higher cost"
        elif (
            comparison_emissions > 0
            and raw_emissions > comparison_emissions * 1.2
        ):
            weakness = "higher emissions"
        elif comparison_risk > 0 and raw_risk > comparison_risk * 1.2:
            weakness = "higher operational risk"

        rejected.append(
            RejectedScenarioExplanation(
                scenario_id=str(ranked_scenario.scenario_id),
                technology_sequence=technology_sequence,
                reason=(
                    f"Ranked #{_safe_int(ranked_scenario.rank)} because "
                    f"{weakness} reduced its overall decision score."
                ),
                rank=_safe_int(ranked_scenario.rank),
                composite_score=_safe_float(
                    ranked_scenario.composite_score
                ),
                key_weakness=weakness,
            )
        )

    return rejected


# ---------------------------------------------------------------------------
# Policy explanation
# ---------------------------------------------------------------------------


def _generate_policy_benefit_summary(
    policy_result: PolicyEvaluationResult,
) -> PolicyBenefitSummary:
    """
    Build the policy section and preserve verification status.

    Individual policy benefits may be sourced independently while the total
    stackable amount remains unverified. That distinction is intentionally
    visible in the final report.
    """
    eligible_schemes = list(
        getattr(policy_result, "eligible_schemes", None) or []
    )

    eligible_scheme_names = [
        str(getattr(scheme, "display_name", scheme))
        for scheme in eligible_schemes
    ]

    estimated_total = _safe_float(
        getattr(
            policy_result,
            "estimated_total_benefit_inr",
            0.0,
        )
    )

    total_verified = bool(
        getattr(
            policy_result,
            "total_benefit_verified",
            False,
        )
    )

    disclaimer = str(
        getattr(
            policy_result,
            "total_benefit_disclaimer",
            "",
        )
        or ""
    ).strip()

    if not disclaimer and not total_verified:
        disclaimer = (
            "Estimated combined benefit — subject to manual verification "
            "against scheme-specific convergence and stackability rules. "
            "Individual scheme benefits may be sourced independently while "
            "their combined total remains unverified."
        )

    return PolicyBenefitSummary(
        eligible_schemes=eligible_scheme_names,
        estimated_total_benefit_inr=estimated_total,
        total_benefit_verified=total_verified,
        disclaimer=disclaimer,
    )


# ---------------------------------------------------------------------------
# Sensitivity / reliability explanation
# ---------------------------------------------------------------------------


def _generate_sensitivity_analysis(
    reliability_result: ReliabilitySweepResult,
) -> SensitivityAnalysis:
    """
    Convert reliability-engine outputs into report-friendly language.

    The spread-ratio thresholds below are only reporting labels. They are not
    reliability-engine calibration thresholds.
    """
    spread_ratio = _safe_float(
        getattr(
            reliability_result,
            "spread_ratio",
            0.0,
        )
    )

    p10 = _safe_float(
        getattr(
            reliability_result,
            "payback_p10",
            0.0,
        )
    )
    p50 = _safe_float(
        getattr(
            reliability_result,
            "payback_p50",
            0.0,
        )
    )
    p90 = _safe_float(
        getattr(
            reliability_result,
            "payback_p90",
            0.0,
        )
    )

    if spread_ratio < 0.3:
        interpretation = (
            f"Payback uncertainty is relatively low: P10={p10:.2f} years, "
            f"P50={p50:.2f} years, P90={p90:.2f} years."
        )
    elif spread_ratio < 0.6:
        interpretation = (
            f"Payback uncertainty is moderate: P10={p10:.2f} years, "
            f"P50={p50:.2f} years, P90={p90:.2f} years."
        )
    else:
        interpretation = (
            f"Payback uncertainty is high: P10={p10:.2f} years, "
            f"P50={p50:.2f} years, P90={p90:.2f} years. "
            "Consider implementation or financing risk mitigation."
        )

    oat_swings = dict(
        getattr(
            reliability_result,
            "oat_swings",
            {},
        )
        or {}
    )

    sorted_risks = sorted(
        oat_swings.items(),
        key=lambda item: _safe_float(item[1]),
        reverse=True,
    )

    top_risk_factors = [
        str(variable)
        for variable, swing in sorted_risks[:5]
        if _safe_float(swing) > 0.5
    ]

    return SensitivityAnalysis(
        payback_p10_years=p10,
        payback_p50_years=p50,
        payback_p90_years=p90,
        spread_ratio=spread_ratio,
        top_risk_factors=top_risk_factors,
        risk_interpretation=interpretation,
    )


# ---------------------------------------------------------------------------
# Rich explainability overlays
# ---------------------------------------------------------------------------


def _apply_explainability_overlay(
    explanation: Explanation,
    explainability_result: Any,
) -> Explanation:
    """
    Overlay richer ExplainabilityEngine output where fields fit the current
    Recommendation contract.

    Important:
    ---------
    The current Recommendation model is intentionally not mutated here.
    Supporting evidence, confidence score, confidence level, and caveats are
    therefore preserved only when/if the Recommendation model is later
    extended to expose those fields.

    The function does, however, use richer engine output for fields already
    supported by the current model.
    """
    payload = _resolve_explainability_payload(explainability_result)

    richer_why_selected = _normalize_string_list(
        payload.get("why_selected")
    )
    if richer_why_selected:
        explanation.why_selected = richer_why_selected

    richer_rejected = payload.get("why_others_rejected")
    if richer_rejected:
        normalized_rejected: List[RejectedScenarioExplanation] = []

        for item in richer_rejected:
            if isinstance(item, RejectedScenarioExplanation):
                normalized_rejected.append(item)
                continue

            scenario_id = str(
                _get_mapping_value(item, "scenario_id", "")
            )
            technology_sequence = list(
                _get_mapping_value(
                    item,
                    "technology_sequence",
                    [],
                )
                or []
            )
            reason = str(
                _get_mapping_value(
                    item,
                    "reason",
                    "",
                )
            )
            rank = _safe_int(
                _get_mapping_value(item, "rank", 0)
            )
            composite_score = _safe_float(
                _get_mapping_value(
                    item,
                    "composite_score",
                    0.0,
                )
            )
            key_weakness = str(
                _get_mapping_value(
                    item,
                    "key_weakness",
                    "",
                )
            )

            if scenario_id:
                normalized_rejected.append(
                    RejectedScenarioExplanation(
                        scenario_id=scenario_id,
                        technology_sequence=technology_sequence,
                        reason=reason,
                        rank=rank,
                        composite_score=composite_score,
                        key_weakness=key_weakness,
                    )
                )

        if normalized_rejected:
            explanation.why_others_rejected = normalized_rejected

    return explanation


# ---------------------------------------------------------------------------
# Public report builder
# ---------------------------------------------------------------------------


def generate_recommendation(
    factory_id: str,
    factory_name: str,
    industry: str,
    state: str,
    optimization_result: OptimizationResult,
    policy_result: PolicyEvaluationResult,
    reliability_result: ReliabilitySweepResult,
    scenarios: Dict[str, Scenario],
    explainability_result: Optional[Any] = None,
) -> Recommendation:
    """
    Generate the final Recommendation object.

    Parameters
    ----------
    factory_id:
        Factory identifier.

    factory_name:
        Human-readable factory name.

    industry:
        Industrial sector.

    state:
        State/location.

    optimization_result:
        Output from the optimizer.

    policy_result:
        Output from the policy engine.

    reliability_result:
        Output from the reliability engine.

    scenarios:
        Mapping of scenario_id -> Scenario.

    explainability_result:
        Optional output from the standalone ExplainabilityEngine.

        This argument is deliberately optional so the current pipeline keeps
        working before the upstream explainability module is wired in.

    Returns
    -------
    Recommendation
        Complete report-ready recommendation.
    """
    recommended_scenario_id = (
        optimization_result.recommended_scenario_id
    )

    recommended_scenario = scenarios.get(
        recommended_scenario_id
    )

    if recommended_scenario is None:
        raise ValueError(
            f"Recommended scenario {recommended_scenario_id!r} "
            "was not found in the scenarios dictionary."
        )

    recommended_ranked = next(
        (
            ranked
            for ranked in optimization_result.ranked_scenarios
            if ranked.scenario_id == recommended_scenario_id
        ),
        None,
    )

    if recommended_ranked is None:
        raise ValueError(
            f"Recommended scenario {recommended_scenario_id!r} "
            "was not found in optimizer.ranked_scenarios."
        )

    why_selected = _generate_why_selected(
        optimization_result=optimization_result,
        policy_result=policy_result,
        recommended_scenario=recommended_scenario,
    )

    why_others_rejected = _generate_why_others_rejected(
        optimization_result=optimization_result,
        scenarios=scenarios,
    )

    policy_benefits = _generate_policy_benefit_summary(
        policy_result=policy_result,
    )

    sensitivity_notes = _generate_sensitivity_analysis(
        reliability_result=reliability_result,
    )

    explanation = Explanation(
        why_selected=why_selected,
        why_others_rejected=why_others_rejected,
        policy_benefits=policy_benefits,
        sensitivity_notes=sensitivity_notes,
    )

    explanation = _apply_explainability_overlay(
        explanation=explanation,
        explainability_result=explainability_result,
    )

    return Recommendation(
        factory_id=factory_id,
        factory_name=factory_name,
        industry=industry,
        state=state,
        recommended_scenario_id=recommended_scenario_id,
        recommended_technology_sequence=list(
            getattr(
                recommended_scenario,
                "technology_sequence",
                [],
            )
            or []
        ),
        capex_total_inr=_safe_float(
            getattr(
                recommended_scenario,
                "capex_total_inr",
                0.0,
            )
        ),
        annual_opex_inr=_safe_float(
            getattr(
                recommended_scenario,
                "annual_opex_inr",
                0.0,
            )
        ),
        payback_range_years=tuple(
            getattr(
                recommended_scenario,
                "payback_years",
                (0.0, 0.0),
            )
            or (0.0, 0.0)
        ),
        co2_reduction_pct=_safe_float(
            getattr(
                recommended_scenario,
                "co2_reduction_pct",
                0.0,
            )
        ),
        fossil_fuel_reduction_pct=_safe_float(
            getattr(
                recommended_scenario,
                "fossil_fuel_reduction_pct",
                0.0,
            )
        ),
        composite_score=_safe_float(
            recommended_ranked.composite_score
        ),
        objective_scores={
            str(key): _safe_float(value)
            for key, value in dict(
                recommended_ranked.objective_scores
            ).items()
        },
        recommended_is_cheapest=bool(
            optimization_result.recommended_is_cheapest
        ),
        explanation=explanation,
        generated_at=datetime.utcnow(),
    )


# ---------------------------------------------------------------------------
# Serialization helper
# ---------------------------------------------------------------------------


def recommendation_to_dict(
    recommendation: Recommendation,
) -> Dict[str, Any]:
    """
    Serialize the Recommendation in a Pydantic-version-compatible way.

    FastAPI/Pydantic may serialize the model automatically, but keeping this
    helper here makes report generation and testing deterministic and keeps
    the JSON boundary explicit.
    """
    if hasattr(recommendation, "model_dump"):
        return recommendation.model_dump()

    if hasattr(recommendation, "dict"):
        return recommendation.dict()

    raise TypeError(
        "Recommendation object does not expose model_dump() or dict()."
    )


__all__ = [
    "generate_recommendation",
    "recommendation_to_dict",
]

"""
report_generator.py — Report generation orchestrator (Sprint 3.4).

Purpose
-------
Integrate outputs from Optimizer (3.2), Policy Engine (3.3), and Reliability
Engine (3.1) to generate a comprehensive Recommendation object with
human-readable explanations.

Contract
--------
Input:  OptimizationResult, PolicyEvaluationResult, ReliabilitySweepResult,
        baseline data, and scenario data
Output: Recommendation model with why_selected, why_others_rejected,
        and sensitivity_notes

Key Requirements
----------------
- why_selected: Explain why the recommended pathway was chosen, pulling from
  MCDA output and policy eligibility
- why_others_rejected: Specific reasons for each non-selected option, not generic
- sensitivity_notes: Surface actual payback P10/P50/P90 and tornado ranking
- All numbers must have plain-language explanations
- estimated_total_benefit_inr must show total_benefit_verified status and disclaimer
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from datetime import datetime

from decision_engine.optimizer.optimization_engine import OptimizationResult
from decision_engine.policy.policy_engine import PolicyEvaluationResult
from decision_engine.reliability.reliability_engine import ReliabilitySweepResult
from models.recommendation import (
    Recommendation,
    Explanation,
    RejectedScenarioExplanation,
    PolicyBenefitSummary,
    SensitivityAnalysis,
)
from models.scenario import Scenario


def _generate_why_selected(
    optimization_result: OptimizationResult,
    policy_result: PolicyEvaluationResult,
    recommended_scenario: Scenario,
) -> List[str]:
    """
    Generate plain-language reasons for why the recommended scenario was selected.

    Combines MCDA ranking rationale with policy eligibility benefits.
    """
    reasons = []

    # MCDA-based reasons
    recommended = next(
        s
        for s in optimization_result.ranked_scenarios
        if s.scenario_id == optimization_result.recommended_scenario_id
    )

    reasons.append(
        f"Ranked #{recommended.rank} out of {len(optimization_result.ranked_scenarios)} "
        f"candidate pathways using multi-criteria analysis"
    )

    # Explain the objective scores
    cost_score = recommended.objective_scores.get("cost", 0)
    emissions_score = recommended.objective_scores.get("emissions", 0)
    risk_score = recommended.objective_scores.get("risk", 0)

    reasons.append(
        f"Achieved a balanced score across cost ({cost_score:.2f}), "
        f"emissions reduction ({emissions_score:.2f}), and operational risk ({risk_score:.2f})"
    )

    # Explain if it's not the cheapest
    if not optimization_result.recommended_is_cheapest:
        reasons.append(
            f"Selected over the cheapest option because it offers better "
            f"environmental benefits and/or lower risk: {optimization_result.why_not_always_cheapest}"
        )
    else:
        reasons.append(
            f"This option is also the most cost-effective, making it a clear winner "
            f"on both economic and environmental dimensions"
        )

    # Policy eligibility benefits
    if policy_result.eligible and len(policy_result.eligible_schemes) > 0:
        scheme_names = [s.display_name for s in policy_result.eligible_schemes]
        reasons.append(
            f"Eligible for {len(policy_result.eligible_schemes)} government financing schemes: "
            f"{', '.join(scheme_names[:3])}"
            + (f" and {len(scheme_names) - 3} others" if len(scheme_names) > 3 else "")
        )

        if policy_result.estimated_total_benefit_inr > 0:
            benefit_millions = policy_result.estimated_total_benefit_inr / 1_000_000
            reasons.append(
                f"Estimated government support reduces effective project cost by "
                f"approximately ₹{benefit_millions:.1f} million through subsidies and interest subventions"
            )

    # Environmental benefits
    if recommended_scenario.co2_reduction_pct > 0:
        reasons.append(
            f"Reduces CO2 emissions by {recommended_scenario.co2_reduction_pct:.1f}%, "
            f"contributing to climate compliance and sustainability goals"
        )

    if recommended_scenario.fossil_fuel_reduction_pct > 0:
        reasons.append(
            f"Decreases fossil fuel dependence by {recommended_scenario.fossil_fuel_reduction_pct:.1f}%, "
            f"improving energy security and reducing exposure to fuel price volatility"
        )

    return reasons


def _generate_why_others_rejected(
    optimization_result: OptimizationResult,
    scenarios: Dict[str, Scenario],
) -> List[RejectedScenarioExplanation]:
    """
    Generate specific rejection reasons for each non-recommended scenario.

    Focus on the key weakness rather than generic "less optimal" statements.
    """
    rejected = []

    for ranked in optimization_result.ranked_scenarios:
        if ranked.scenario_id == optimization_result.recommended_scenario_id:
            continue

        scenario = scenarios.get(ranked.scenario_id)
        if scenario is None:
            continue

        # Determine the primary weakness
        # NOTE: 1.2 (20% worse) is a presentation-layer heuristic for picking which
        # weakness to surface in plain language — not a sourced/calibrated threshold.
        weakness = "lower overall score"
        if ranked.raw_cost > optimization_result.ranked_scenarios[0].raw_cost * 1.2:
            weakness = "significantly higher cost"
        elif ranked.raw_emissions > optimization_result.ranked_scenarios[0].raw_emissions * 1.2:
            weakness = "lower emissions reduction"
        elif ranked.raw_risk > optimization_result.ranked_scenarios[0].raw_risk * 1.2:
            weakness = "higher operational risk"

        explanation = RejectedScenarioExplanation(
            scenario_id=ranked.scenario_id,
            technology_sequence=scenario.technology_sequence,
            reason=f"Ranked #{ranked.rank} with {weakness}",
            rank=ranked.rank,
            composite_score=ranked.composite_score,
            key_weakness=weakness,
        )
        rejected.append(explanation)

    return rejected


def _generate_policy_benefit_summary(
    policy_result: PolicyEvaluationResult,
) -> PolicyBenefitSummary:
    """
    Generate policy benefit summary with verification status and disclaimer.

    Ensures the total_benefit_verified flag and disclaimer travel with the
    estimated_total_benefit_inr value.
    """
    eligible_scheme_names = [s.display_name for s in policy_result.eligible_schemes]

    disclaimer = ""
    if not policy_result.total_benefit_verified:
        disclaimer = (
            "Estimated combined benefit — subject to manual verification against "
            "scheme-specific convergence rules; individual scheme benefits are "
            "independently sourced, their combined stackability is not."
        )

    return PolicyBenefitSummary(
        eligible_schemes=eligible_scheme_names,
        estimated_total_benefit_inr=policy_result.estimated_total_benefit_inr,
        total_benefit_verified=policy_result.total_benefit_verified,
        disclaimer=disclaimer,
    )


def _generate_sensitivity_analysis(
    reliability_result: ReliabilitySweepResult,
) -> SensitivityAnalysis:
    """
    Generate sensitivity analysis from reliability engine output.

    Converts technical P10/P50/P90 and tornado ranking into plain language.
    """
    # Generate plain-language risk interpretation
    # NOTE: 0.3 / 0.6 spread-ratio cutoffs below are presentation-layer heuristics
    # for labeling low/moderate/high risk in the narrative — not sourced from the
    # reliability engine's own thresholds, just chosen for readable tiering here.
    if reliability_result.spread_ratio < 0.3:
        risk_level = "low"
        interpretation = (
            f"Payback period is relatively stable (P10-P90 spread: {reliability_result.spread_ratio:.2f}). "
            f"The recommendation is robust to typical market variations."
        )
    elif reliability_result.spread_ratio < 0.6:
        risk_level = "moderate"
        interpretation = (
            f"Payback period has moderate uncertainty (P10-P90 spread: {reliability_result.spread_ratio:.2f}). "
            f"Monitor key risk factors listed below during implementation."
        )
    else:
        risk_level = "high"
        interpretation = (
            f"Payback period is sensitive to market conditions (P10-P90 spread: {reliability_result.spread_ratio:.2f}). "
            f"Consider phased implementation or risk mitigation strategies."
        )

    # Extract top risk factors from OAT swings
    sorted_risks = sorted(
        reliability_result.oat_swings.items(), key=lambda x: x[1], reverse=True
    )
    # NOTE: 0.5 is a presentation-layer cutoff for "worth naming as a top risk
    # factor" in the narrative — not a sourced/calibrated sensitivity threshold.
    top_risk_factors = [var for var, swing in sorted_risks[:5] if swing > 0.5]

    return SensitivityAnalysis(
        payback_p10_years=reliability_result.payback_p10,
        payback_p50_years=reliability_result.payback_p50,
        payback_p90_years=reliability_result.payback_p90,
        spread_ratio=reliability_result.spread_ratio,
        top_risk_factors=top_risk_factors,
        risk_interpretation=interpretation,
    )


def generate_recommendation(
    factory_id: str,
    factory_name: str,
    industry: str,
    state: str,
    optimization_result: OptimizationResult,
    policy_result: PolicyEvaluationResult,
    reliability_result: ReliabilitySweepResult,
    scenarios: Dict[str, Scenario],
) -> Recommendation:
    """
    Generate a comprehensive Recommendation from decision engine outputs.

    Parameters
    ----------
    factory_id : str
        Factory identifier
    factory_name : str
        Factory name for display
    industry : str
        Industry sector
    state : str
        State location
    optimization_result : OptimizationResult
        Output from decision_engine.optimizer (3.2)
    policy_result : PolicyEvaluationResult
        Output from decision_engine.policy (3.3)
    reliability_result : ReliabilitySweepResult
        Output from decision_engine.reliability (3.1)
    scenarios : Dict[str, Scenario]
        Mapping of scenario_id to Scenario objects

    Returns
    -------
    Recommendation
        Complete recommendation with human-readable explanations
    """
    # Get the recommended scenario
    recommended_scenario = scenarios.get(optimization_result.recommended_scenario_id)
    if recommended_scenario is None:
        raise ValueError(
            f"Recommended scenario {optimization_result.recommended_scenario_id} "
            f"not found in scenarios dictionary"
        )

    # Generate explanation components
    why_selected = _generate_why_selected(
        optimization_result, policy_result, recommended_scenario
    )
    why_others_rejected = _generate_why_others_rejected(
        optimization_result, scenarios
    )
    policy_benefits = _generate_policy_benefit_summary(policy_result)
    sensitivity_notes = _generate_sensitivity_analysis(reliability_result)

    explanation = Explanation(
        why_selected=why_selected,
        why_others_rejected=why_others_rejected,
        policy_benefits=policy_benefits,
        sensitivity_notes=sensitivity_notes,
    )

    # Get recommended scenario for MCDA data
    recommended_ranked = next(
        s
        for s in optimization_result.ranked_scenarios
        if s.scenario_id == optimization_result.recommended_scenario_id
    )

    return Recommendation(
        factory_id=factory_id,
        factory_name=factory_name,
        industry=industry,
        state=state,
        recommended_scenario_id=optimization_result.recommended_scenario_id,
        recommended_technology_sequence=recommended_scenario.technology_sequence,
        capex_total_inr=recommended_scenario.capex_total_inr,
        annual_opex_inr=recommended_scenario.annual_opex_inr,
        payback_range_years=recommended_scenario.payback_years,
        co2_reduction_pct=recommended_scenario.co2_reduction_pct,
        fossil_fuel_reduction_pct=recommended_scenario.fossil_fuel_reduction_pct,
        composite_score=recommended_ranked.composite_score,
        objective_scores=dict(recommended_ranked.objective_scores),
        recommended_is_cheapest=optimization_result.recommended_is_cheapest,
        explanation=explanation,
        generated_at=datetime.utcnow(),
    )
"""
Unit tests for the explainability / recommendation report generator.

Covers:
- why_selected generation
- why_others_rejected generation
- policy benefit explanation
- sensitivity explanation
- complete Recommendation construction
- validation of invalid recommended scenario IDs

The tests intentionally use lightweight fake optimizer/policy/reliability
objects matching the public attributes consumed by report_generator.py.
"""

from __future__ import annotations

import os
import sys
from types import SimpleNamespace

import pytest

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from decision_engine.reports.report_generator import (
    _generate_policy_benefit_summary,
    _generate_sensitivity_analysis,
    _generate_why_others_rejected,
    _generate_why_selected,
    generate_recommendation,
)
from models.recommendation import (
    Explanation,
    PolicyBenefitSummary,
    Recommendation,
    RejectedScenarioExplanation,
    SensitivityAnalysis,
)
from models.scenario import ObjectiveScores, Scenario


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _scenario(
    scenario_id: str,
    technologies: list[str],
    *,
    capex: float = 1_000_000,
    opex: float = 500_000,
    co2_reduction: float = 50.0,
    fossil_reduction: float = 40.0,
    payback: tuple[float, float] = (2.0, 3.0),
) -> Scenario:
    return Scenario(
        scenario_id=scenario_id,
        factory_id="factory-001",
        technology_sequence=technologies,
        capex_total_inr=capex,
        annual_opex_inr=opex,
        fossil_fuel_reduction_pct=fossil_reduction,
        co2_reduction_pct=co2_reduction,
        payback_years=payback,
        reliability_score_pct=90.0,
        financing_eligible_schemes=["scheme-a"],
        rejected_technologies=[],
        objective_scores=ObjectiveScores(
            cost=0.8,
            emissions=0.9,
            risk=0.85,
        ),
    )


def _ranked(
    scenario_id: str,
    *,
    rank: int,
    composite_score: float,
    raw_cost: float,
    raw_emissions: float,
    raw_risk: float,
    is_recommended: bool = False,
    is_cheapest: bool = False,
    objective_scores: dict[str, float] | None = None,
    rank_reason: str = "Balanced performance across objectives",
):
    return SimpleNamespace(
        scenario_id=scenario_id,
        technology_sequence=["technology-x"],
        rank=rank,
        composite_score=composite_score,
        raw_cost=raw_cost,
        raw_emissions=raw_emissions,
        raw_risk=raw_risk,
        is_recommended=is_recommended,
        is_cheapest=is_cheapest,
        objective_scores=objective_scores
        or {
            "cost": 0.80,
            "emissions": 0.90,
            "risk": 0.85,
        },
        rank_reason=rank_reason,
    )


def _optimization_result(
    *,
    recommended_id: str = "scenario-clean",
    recommended_is_cheapest: bool = False,
    cheapest_id: str = "scenario-cheap",
):
    ranked = [
        _ranked(
            "scenario-clean",
            rank=1,
            composite_score=0.91,
            raw_cost=6_000_000,
            raw_emissions=120.0,
            raw_risk=0.12,
            is_recommended=True,
            is_cheapest=False,
            objective_scores={
                "cost": 0.78,
                "emissions": 0.97,
                "risk": 0.91,
            },
            rank_reason="Better emissions and lower risk outweighed the higher cost",
        ),
        _ranked(
            "scenario-balanced",
            rank=2,
            composite_score=0.77,
            raw_cost=5_500_000,
            raw_emissions=260.0,
            raw_risk=0.28,
            is_recommended=False,
            is_cheapest=False,
            objective_scores={
                "cost": 0.84,
                "emissions": 0.72,
                "risk": 0.76,
            },
        ),
        _ranked(
            "scenario-cheap",
            rank=3,
            composite_score=0.68,
            raw_cost=4_000_000,
            raw_emissions=700.0,
            raw_risk=0.55,
            is_recommended=False,
            is_cheapest=True,
            objective_scores={
                "cost": 1.00,
                "emissions": 0.30,
                "risk": 0.40,
            },
        ),
    ]

    return SimpleNamespace(
        recommended_scenario_id=recommended_id,
        cheapest_scenario_id=cheapest_id,
        recommended_is_cheapest=recommended_is_cheapest,
        ranked_scenarios=ranked,
        why_not_always_cheapest=(
            "Recommended 'scenario-clean' is not the cheapest "
            "(cheapest is 'scenario-cheap'). Better emissions and lower "
            "risk outweighed the higher cost."
        ),
    )


def _policy_result(
    *,
    eligible: bool = True,
    scheme_names: list[str] | None = None,
    total_benefit: float = 250_000.0,
    verified: bool = False,
):
    schemes = [
        SimpleNamespace(display_name=name)
        for name in (scheme_names or ["MSE-GIFT", "ADEETIE"])
    ]

    return SimpleNamespace(
        eligible=eligible,
        eligible_schemes=schemes,
        estimated_total_benefit_inr=total_benefit,
        total_benefit_verified=verified,
    )


def _reliability_result(
    *,
    p10: float = 1.8,
    p50: float = 2.6,
    p90: float = 3.3,
    spread_ratio: float = 0.30,
    oat_swings: dict[str, float] | None = None,
):
    return SimpleNamespace(
        payback_p10=p10,
        payback_p50=p50,
        payback_p90=p90,
        spread_ratio=spread_ratio,
        oat_swings=oat_swings
        or {
            "electricity_tariff": 0.85,
            "fuel_price": 0.72,
            "production_volume": 0.40,
            "capex_overrun": 0.30,
            "solar_capacity_factor": 0.20,
        },
    )


# ---------------------------------------------------------------------------
# why_selected
# ---------------------------------------------------------------------------


def test_generate_why_selected_mentions_rank_and_objective_scores():
    optimization = _optimization_result()
    policy = _policy_result()
    scenario = _scenario(
        "scenario-clean",
        ["energy_efficiency", "biomass_boiler"],
        co2_reduction=82.0,
        fossil_reduction=76.0,
    )

    reasons = _generate_why_selected(
        optimization,
        policy,
        scenario,
    )

    combined = " ".join(reasons)

    assert "Ranked #1 out of 3" in combined
    assert "cost (0.78)" in combined
    assert "emissions reduction (0.97)" in combined
    assert "operational risk (0.91)" in combined


def test_generate_why_selected_explains_non_cheapest_recommendation():
    optimization = _optimization_result(
        recommended_is_cheapest=False,
    )
    policy = _policy_result()
    scenario = _scenario(
        "scenario-clean",
        ["heat_pump"],
        co2_reduction=90.0,
        fossil_reduction=88.0,
    )

    reasons = _generate_why_selected(
        optimization,
        policy,
        scenario,
    )

    combined = " ".join(reasons).lower()

    assert "cheapest option" in combined
    assert "environmental benefits" in combined or "lower risk" in combined


def test_generate_why_selected_handles_cheapest_winner():
    optimization = _optimization_result(
        recommended_id="scenario-cheap",
        recommended_is_cheapest=True,
        cheapest_id="scenario-cheap",
    )

    optimization.ranked_scenarios = [
        _ranked(
            "scenario-cheap",
            rank=1,
            composite_score=0.95,
            raw_cost=4_000_000,
            raw_emissions=200.0,
            raw_risk=0.12,
            is_recommended=True,
            is_cheapest=True,
        ),
        _ranked(
            "scenario-other",
            rank=2,
            composite_score=0.70,
            raw_cost=6_000_000,
            raw_emissions=300.0,
            raw_risk=0.30,
        ),
    ]

    policy = _policy_result()
    scenario = _scenario(
        "scenario-cheap",
        ["energy_efficiency"],
        co2_reduction=70.0,
        fossil_reduction=65.0,
    )

    reasons = _generate_why_selected(
        optimization,
        policy,
        scenario,
    )

    combined = " ".join(reasons).lower()

    assert "also the most cost-effective" in combined


def test_generate_why_selected_includes_policy_information_when_eligible():
    optimization = _optimization_result()
    policy = _policy_result(
        eligible=True,
        scheme_names=["MSE-GIFT", "ADEETIE", "Green Finance Scheme"],
        total_benefit=1_500_000.0,
    )
    scenario = _scenario(
        "scenario-clean",
        ["biomass_boiler"],
        co2_reduction=80.0,
        fossil_reduction=75.0,
    )

    reasons = _generate_why_selected(
        optimization,
        policy,
        scenario,
    )

    combined = " ".join(reasons)

    assert "MSE-GIFT" in combined
    assert "ADEETIE" in combined
    assert "Green Finance Scheme" in combined
    assert "1.5 million" in combined


def test_generate_why_selected_includes_environmental_and_fossil_reduction():
    optimization = _optimization_result()
    policy = _policy_result()
    scenario = _scenario(
        "scenario-clean",
        ["electrification"],
        co2_reduction=63.5,
        fossil_reduction=58.2,
    )

    reasons = _generate_why_selected(
        optimization,
        policy,
        scenario,
    )

    combined = " ".join(reasons)

    assert "Reduces CO2 emissions by 63.5%" in combined
    assert "Decreases fossil fuel dependence by 58.2%" in combined


def test_generate_why_selected_still_works_when_policy_is_not_eligible():
    optimization = _optimization_result()
    policy = _policy_result(
        eligible=False,
        scheme_names=[],
        total_benefit=0.0,
    )
    scenario = _scenario(
        "scenario-clean",
        ["waste_heat_recovery"],
        co2_reduction=45.0,
        fossil_reduction=35.0,
    )

    reasons = _generate_why_selected(
        optimization,
        policy,
        scenario,
    )

    combined = " ".join(reasons)

    assert "Ranked #1 out of 3" in combined
    assert "Reduces CO2 emissions by 45.0%" in combined


# ---------------------------------------------------------------------------
# why_others_rejected
# ---------------------------------------------------------------------------


def test_generate_why_others_rejected_skips_recommended_scenario():
    optimization = _optimization_result()

    scenarios = {
        "scenario-clean": _scenario(
            "scenario-clean",
            ["heat_pump"],
        ),
        "scenario-balanced": _scenario(
            "scenario-balanced",
            ["biomass_boiler"],
        ),
        "scenario-cheap": _scenario(
            "scenario-cheap",
            ["coal_boiler"],
        ),
    }

    rejected = _generate_why_others_rejected(
        optimization,
        scenarios,
    )

    ids = [item.scenario_id for item in rejected]

    assert "scenario-clean" not in ids
    assert set(ids) == {"scenario-balanced", "scenario-cheap"}


def test_generate_why_others_rejected_returns_typed_explanations():
    optimization = _optimization_result()

    scenarios = {
        "scenario-clean": _scenario(
            "scenario-clean",
            ["heat_pump"],
        ),
        "scenario-balanced": _scenario(
            "scenario-balanced",
            ["biomass_boiler"],
        ),
        "scenario-cheap": _scenario(
            "scenario-cheap",
            ["coal_boiler"],
        ),
    }

    rejected = _generate_why_others_rejected(
        optimization,
        scenarios,
    )

    assert all(
        isinstance(item, RejectedScenarioExplanation)
        for item in rejected
    )


def test_generate_why_others_rejected_contains_rank_and_weakness():
    optimization = _optimization_result()

    scenarios = {
        "scenario-clean": _scenario(
            "scenario-clean",
            ["heat_pump"],
        ),
        "scenario-balanced": _scenario(
            "scenario-balanced",
            ["biomass_boiler"],
        ),
        "scenario-cheap": _scenario(
            "scenario-cheap",
            ["coal_boiler"],
        ),
    }

    rejected = _generate_why_others_rejected(
        optimization,
        scenarios,
    )

    for item in rejected:
        assert item.rank >= 2
        assert item.composite_score < 0.91
        assert item.reason
        assert item.key_weakness


def test_generate_why_others_rejected_ignores_missing_scenario_object():
    optimization = _optimization_result()

    scenarios = {
        "scenario-clean": _scenario(
            "scenario-clean",
            ["heat_pump"],
        ),
        "scenario-balanced": _scenario(
            "scenario-balanced",
            ["biomass_boiler"],
        ),
        # scenario-cheap intentionally missing
    }

    rejected = _generate_why_others_rejected(
        optimization,
        scenarios,
    )

    ids = [item.scenario_id for item in rejected]

    assert ids == ["scenario-balanced"]


# ---------------------------------------------------------------------------
# Policy benefits
# ---------------------------------------------------------------------------


def test_policy_benefit_summary_preserves_scheme_names_and_amount():
    policy = _policy_result(
        scheme_names=["MSE-GIFT", "ADEETIE"],
        total_benefit=450_000.0,
        verified=False,
    )

    result = _generate_policy_benefit_summary(policy)

    assert isinstance(result, PolicyBenefitSummary)
    assert result.eligible_schemes == ["MSE-GIFT", "ADEETIE"]
    assert result.estimated_total_benefit_inr == pytest.approx(450_000.0)
    assert result.total_benefit_verified is False
    assert "subject to manual verification" in result.disclaimer


def test_policy_benefit_summary_uses_verified_flag():
    policy = _policy_result(
        scheme_names=["Scheme A"],
        total_benefit=100_000.0,
        verified=True,
    )

    result = _generate_policy_benefit_summary(policy)

    assert result.total_benefit_verified is True
    assert result.estimated_total_benefit_inr == pytest.approx(100_000.0)
    assert result.disclaimer == ""


def test_policy_benefit_summary_handles_no_eligible_schemes():
    policy = _policy_result(
        eligible=False,
        scheme_names=[],
        total_benefit=0.0,
        verified=False,
    )

    result = _generate_policy_benefit_summary(policy)

    assert result.eligible_schemes == []
    assert result.estimated_total_benefit_inr == pytest.approx(0.0)
    assert result.total_benefit_verified is False


# ---------------------------------------------------------------------------
# Sensitivity analysis
# ---------------------------------------------------------------------------


def test_sensitivity_analysis_maps_p10_p50_p90():
    reliability = _reliability_result(
        p10=1.7,
        p50=2.4,
        p90=3.9,
        spread_ratio=0.35,
    )

    result = _generate_sensitivity_analysis(reliability)

    assert isinstance(result, SensitivityAnalysis)
    assert result.payback_p10_years == pytest.approx(1.7)
    assert result.payback_p50_years == pytest.approx(2.4)
    assert result.payback_p90_years == pytest.approx(3.9)
    assert result.spread_ratio == pytest.approx(0.35)


def test_sensitivity_analysis_low_spread_is_low_risk():
    reliability = _reliability_result(
        p10=2.0,
        p50=2.5,
        p90=2.9,
        spread_ratio=0.20,
    )

    result = _generate_sensitivity_analysis(reliability)

    assert "stable" in result.risk_interpretation.lower()
    assert "robust" in result.risk_interpretation.lower()


def test_sensitivity_analysis_moderate_spread_is_moderate_risk():
    reliability = _reliability_result(
        p10=1.5,
        p50=2.5,
        p90=3.9,
        spread_ratio=0.40,
    )

    result = _generate_sensitivity_analysis(reliability)

    assert "moderate uncertainty" in result.risk_interpretation.lower()


def test_sensitivity_analysis_high_spread_is_high_risk():
    reliability = _reliability_result(
        p10=1.0,
        p50=2.0,
        p90=3.8,
        spread_ratio=0.80,
    )

    result = _generate_sensitivity_analysis(reliability)

    assert "sensitive to market conditions" in result.risk_interpretation.lower()


def test_sensitivity_analysis_only_reports_oat_swings_above_threshold():
    reliability = _reliability_result(
        oat_swings={
            "electricity_tariff": 0.90,
            "fuel_price": 0.70,
            "production_volume": 0.50,
            "capex_overrun": 0.49,
            "solar_capacity_factor": 0.10,
        }
    )

    result = _generate_sensitivity_analysis(reliability)

    assert "electricity_tariff" in result.top_risk_factors
    assert "fuel_price" in result.top_risk_factors
    assert "production_volume" not in result.top_risk_factors
    assert "capex_overrun" not in result.top_risk_factors
    assert "solar_capacity_factor" not in result.top_risk_factors


# ---------------------------------------------------------------------------
# Complete Recommendation
# ---------------------------------------------------------------------------


def test_generate_recommendation_builds_complete_model():
    optimization = _optimization_result()

    policy = _policy_result(
        scheme_names=["MSE-GIFT", "ADEETIE"],
        total_benefit=800_000.0,
        verified=False,
    )

    reliability = _reliability_result(
        p10=1.9,
        p50=2.7,
        p90=3.6,
        spread_ratio=0.63,
    )

    scenarios = {
        "scenario-clean": _scenario(
            "scenario-clean",
            ["energy_efficiency", "heat_pump"],
            capex=6_000_000,
            opex=900_000,
            co2_reduction=85.0,
            fossil_reduction=80.0,
            payback=(1.9, 3.6),
        ),
        "scenario-balanced": _scenario(
            "scenario-balanced",
            ["biomass_boiler"],
            capex=5_500_000,
            opex=1_100_000,
            co2_reduction=65.0,
            fossil_reduction=60.0,
            payback=(2.5, 4.0),
        ),
        "scenario-cheap": _scenario(
            "scenario-cheap",
            ["coal_boiler"],
            capex=4_000_000,
            opex=1_400_000,
            co2_reduction=15.0,
            fossil_reduction=0.0,
            payback=(1.2, 2.2),
        ),
    }

    result = generate_recommendation(
        factory_id="factory-001",
        factory_name="Textile Unit A",
        industry="textile",
        state="Tamil Nadu",
        optimization_result=optimization,
        policy_result=policy,
        reliability_result=reliability,
        scenarios=scenarios,
    )

    assert isinstance(result, Recommendation)

    assert result.factory_id == "factory-001"
    assert result.factory_name == "Textile Unit A"
    assert result.industry == "textile"
    assert result.state == "Tamil Nadu"

    assert result.recommended_scenario_id == "scenario-clean"
    assert result.recommended_technology_sequence == [
        "energy_efficiency",
        "heat_pump",
    ]

    assert result.capex_total_inr == pytest.approx(6_000_000)
    assert result.annual_opex_inr == pytest.approx(900_000)
    assert result.payback_range_years == (1.9, 3.6)

    assert result.co2_reduction_pct == pytest.approx(85.0)
    assert result.fossil_fuel_reduction_pct == pytest.approx(80.0)

    assert result.composite_score == pytest.approx(0.91)
    assert result.recommended_is_cheapest is False

    assert isinstance(result.explanation, Explanation)
    assert result.explanation.why_selected
    assert len(result.explanation.why_others_rejected) == 2
    assert isinstance(
        result.explanation.policy_benefits,
        PolicyBenefitSummary,
    )
    assert isinstance(
        result.explanation.sensitivity_notes,
        SensitivityAnalysis,
    )


def test_generate_recommendation_contains_all_non_recommended_scenarios():
    optimization = _optimization_result()

    policy = _policy_result()
    reliability = _reliability_result()

    scenarios = {
        "scenario-clean": _scenario(
            "scenario-clean",
            ["heat_pump"],
        ),
        "scenario-balanced": _scenario(
            "scenario-balanced",
            ["biomass_boiler"],
        ),
        "scenario-cheap": _scenario(
            "scenario-cheap",
            ["coal_boiler"],
        ),
    }

    result = generate_recommendation(
        factory_id="factory-001",
        factory_name="Factory A",
        industry="textile",
        state="Maharashtra",
        optimization_result=optimization,
        policy_result=policy,
        reliability_result=reliability,
        scenarios=scenarios,
    )

    rejected_ids = {
        item.scenario_id
        for item in result.explanation.why_others_rejected
    }

    assert rejected_ids == {"scenario-balanced", "scenario-cheap"}


def test_generate_recommendation_raises_for_missing_recommended_scenario():
    optimization = _optimization_result(
        recommended_id="scenario-does-not-exist"
    )
    policy = _policy_result()
    reliability = _reliability_result()

    scenarios = {
        "scenario-clean": _scenario(
            "scenario-clean",
            ["heat_pump"],
        ),
    }

    with pytest.raises(
        ValueError,
        match="Recommended scenario scenario-does-not-exist not found",
    ):
        generate_recommendation(
            factory_id="factory-001",
            factory_name="Factory A",
            industry="textile",
            state="Gujarat",
            optimization_result=optimization,
            policy_result=policy,
            reliability_result=reliability,
            scenarios=scenarios,
        )


def test_generated_recommendation_is_json_serializable():
    optimization = _optimization_result()
    policy = _policy_result()
    reliability = _reliability_result()

    scenarios = {
        "scenario-clean": _scenario(
            "scenario-clean",
            ["heat_pump"],
        ),
        "scenario-balanced": _scenario(
            "scenario-balanced",
            ["biomass_boiler"],
        ),
        "scenario-cheap": _scenario(
            "scenario-cheap",
            ["coal_boiler"],
        ),
    }

    result = generate_recommendation(
        factory_id="factory-001",
        factory_name="Factory A",
        industry="textile",
        state="Tamil Nadu",
        optimization_result=optimization,
        policy_result=policy,
        reliability_result=reliability,
        scenarios=scenarios,
    )

    payload = result.model_dump(mode="json")

    assert isinstance(payload, dict)
    assert payload["factory_id"] == "factory-001"
    assert payload["recommended_scenario_id"] == "scenario-clean"
    assert "explanation" in payload
    assert "why_selected" in payload["explanation"]
    assert "why_others_rejected" in payload["explanation"]
    assert "policy_benefits" in payload["explanation"]
    assert "sensitivity_notes" in payload["explanation"]
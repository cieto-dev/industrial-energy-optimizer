"""
test_recommendations.py — Gate tests for Sprint 3.4 Reports.

Gate (ROADMAP.md Sprint 3.4):
Human-readable explanation produced that a non-expert can understand.

Key tests:
- Report generator produces valid Recommendation object
- why_selected contains plain-language explanations
- why_others_rejected has specific reasons, not generic
- sensitivity_notes contains actual P10/P50/P90 and tornado ranking
- Disclaimer appears in policy benefits when total_benefit_verified is False
- PDF and Excel generation work without errors
"""

import os
import sys
import tempfile
from pathlib import Path

import pytest

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _REPO_ROOT)

from decision_engine.reports.report_generator import (
    generate_recommendation,
    _generate_why_selected,
    _generate_why_others_rejected,
    _generate_policy_benefit_summary,
    _generate_sensitivity_analysis,
)
from decision_engine.optimizer.optimization_engine import (
    OptimizationResult,
    optimize,
    ScenarioMetrics,
)
from decision_engine.policy.policy_engine import (
    PolicyEngine,
    PolicyEvaluationResult,
)
from decision_engine.reliability.reliability_engine import (
    ReliabilitySweepResult,
    BaseCaseInputs,
    run_reliability_sweep,
)
from models.recommendation import Recommendation
from models.scenario import Scenario


def _create_mock_optimization_result():
    """Create a mock OptimizationResult for testing."""
    # Create sample scenarios
    scenarios = [
        ScenarioMetrics(
            scenario_id="biomass_boiler",
            technology_sequence=["biomass"],
            capex_inr=15_000_000,
            annual_opex_inr=8_000_000,
            pathway_co2_tonnes_year=500,
            co2_reduction_pct=30,
            spread_ratio=0.4,
            risk_tier="moderate",
            reliability_score_pct=75,
        ),
        ScenarioMetrics(
            scenario_id="solar_thermal",
            technology_sequence=["solar_thermal"],
            capex_inr=12_000_000,
            annual_opex_inr=10_000_000,
            pathway_co2_tonnes_year=600,
            co2_reduction_pct=20,
            spread_ratio=0.5,
            risk_tier="moderate",
            reliability_score_pct=70,
        ),
    ]

    return optimize(scenarios)


def _create_mock_policy_result():
    """Create a mock PolicyEvaluationResult for testing."""
    from decision_engine.policy import tamil_nadu_textile_small_udyam_factory

    factory = tamil_nadu_textile_small_udyam_factory()
    return PolicyEngine().evaluate(factory)


def _create_mock_reliability_result():
    """Create a mock ReliabilitySweepResult for testing."""
    return ReliabilitySweepResult(
        payback_p10=2.5,
        payback_p50=3.5,
        payback_p90=5.0,
        spread_ratio=0.71,
        raw_distribution=[2.5, 3.0, 3.5, 4.0, 5.0],
        oat_swings={
            "fuel_price": 1.5,
            "production_volume": 1.0,
            "solar_capacity_factor": 0.5,
        },
        metadata={"n_iterations": 100, "confidence_widening": "standard"},
        n_iterations=100,
        gate_passed=True,
    )


def _create_mock_scenarios():
    """Create mock Scenario objects for testing."""
    return {
        "biomass_boiler": Scenario(
            scenario_id="biomass_boiler",
            factory_id="TEST_FACTORY",
            technology_sequence=["biomass"],
            capex_total_inr=15_000_000,
            annual_opex_inr=8_000_000,
            fossil_fuel_reduction_pct=40,
            co2_reduction_pct=30,
            payback_years=(2.5, 4.0),
            reliability_score_pct=75,
            financing_eligible_schemes=["ADEETIE", "MSE_GIFT"],
            rejected_technologies=[],
            objective_scores={
                "cost": 0.8,
                "emissions": 0.7,
                "risk": 0.75,
            },
        ),
        "solar_thermal": Scenario(
            scenario_id="solar_thermal",
            factory_id="TEST_FACTORY",
            technology_sequence=["solar_thermal"],
            capex_total_inr=12_000_000,
            annual_opex_inr=10_000_000,
            fossil_fuel_reduction_pct=25,
            co2_reduction_pct=20,
            payback_years=(3.0, 5.0),
            reliability_score_pct=70,
            financing_eligible_schemes=["ADEETIE"],
            rejected_technologies=[],
            objective_scores={
                "cost": 0.9,
                "emissions": 0.5,
                "risk": 0.6,
            },
        ),
    }


def test_generate_recommendation_creates_valid_object():
    """Test that generate_recommendation produces a valid Recommendation object."""
    optimization_result = _create_mock_optimization_result()
    policy_result = _create_mock_policy_result()
    reliability_result = _create_mock_reliability_result()
    scenarios = _create_mock_scenarios()

    recommendation = generate_recommendation(
        factory_id="TEST_FACTORY",
        factory_name="Test Factory",
        industry="textile",
        state="Tamil Nadu",
        optimization_result=optimization_result,
        policy_result=policy_result,
        reliability_result=reliability_result,
        scenarios=scenarios,
    )

    assert isinstance(recommendation, Recommendation)
    assert recommendation.factory_id == "TEST_FACTORY"
    assert recommendation.factory_name == "Test Factory"
    assert recommendation.industry == "textile"
    assert recommendation.state == "Tamil Nadu"
    assert recommendation.recommended_scenario_id == optimization_result.recommended_scenario_id


def test_why_selected_contains_plain_language_explanations():
    """Test that why_selected contains plain-language explanations."""
    optimization_result = _create_mock_optimization_result()
    policy_result = _create_mock_policy_result()
    scenarios = _create_mock_scenarios()
    recommended_scenario = scenarios[optimization_result.recommended_scenario_id]

    why_selected = _generate_why_selected(
        optimization_result, policy_result, recommended_scenario
    )

    assert len(why_selected) > 0
    # Check that explanations are plain language, not technical jargon
    for reason in why_selected:
        assert len(reason) > 10  # Not too short
        assert any(
            word in reason.lower()
            for word in [
                "ranked", "score", "cost", "emissions", "eligible",
                "reduces", "reduction", "fossil", "policy", "financial",
                "support", "benefit", "co2"
            ]
        ), f"Reason should contain plain language: {reason}"


def test_why_others_rejected_has_specific_reasons():
    """Test that why_others_rejected has specific reasons, not generic."""
    optimization_result = _create_mock_optimization_result()
    scenarios = _create_mock_scenarios()

    why_others_rejected = _generate_why_others_rejected(
        optimization_result, scenarios
    )

    assert len(why_others_rejected) > 0

    for rejected in why_others_rejected:
        # Check that reason is specific, not generic
        assert rejected.reason != "less optimal"
        assert rejected.reason != "not recommended"
        assert any(
            word in rejected.key_weakness.lower()
            for word in ["cost", "emissions", "risk", "higher", "lower"]
        ), f"Key weakness should be specific: {rejected.key_weakness}"
        assert rejected.rank > 0
        assert rejected.composite_score >= 0


def test_sensitivity_notes_contains_actual_p10_p50_p90():
    """Test that sensitivity_notes contains actual P10/P50/P90 and tornado ranking."""
    reliability_result = _create_mock_reliability_result()

    sensitivity_notes = _generate_sensitivity_analysis(reliability_result)

    assert sensitivity_notes.payback_p10_years == reliability_result.payback_p10
    assert sensitivity_notes.payback_p50_years == reliability_result.payback_p50
    assert sensitivity_notes.payback_p90_years == reliability_result.payback_p90
    assert sensitivity_notes.spread_ratio == reliability_result.spread_ratio

    # Check that tornado ranking is present
    assert len(sensitivity_notes.top_risk_factors) > 0
    assert "fuel_price" in sensitivity_notes.top_risk_factors

    # Check that risk interpretation is plain language
    assert len(sensitivity_notes.risk_interpretation) > 20
    assert any(
        word in sensitivity_notes.risk_interpretation.lower()
        for word in ["payback", "stable", "uncertainty", "risk"]
    )


def test_policy_benefit_summary_contains_disclaimer_when_unverified():
    """Test that disclaimer appears when total_benefit_verified is False."""
    policy_result = _create_mock_policy_result()

    policy_benefits = _generate_policy_benefit_summary(policy_result)

    assert policy_benefits.total_benefit_verified is False
    assert len(policy_benefits.disclaimer) > 0
    assert "manual verification" in policy_benefits.disclaimer.lower()
    assert "scheme-specific convergence" in policy_benefits.disclaimer.lower()


def test_recommendation_contains_all_required_fields():
    """Test that Recommendation contains all required fields."""
    optimization_result = _create_mock_optimization_result()
    policy_result = _create_mock_policy_result()
    reliability_result = _create_mock_reliability_result()
    scenarios = _create_mock_scenarios()

    recommendation = generate_recommendation(
        factory_id="TEST_FACTORY",
        factory_name="Test Factory",
        industry="textile",
        state="Tamil Nadu",
        optimization_result=optimization_result,
        policy_result=policy_result,
        reliability_result=reliability_result,
        scenarios=scenarios,
    )

    # Check top-level fields
    assert recommendation.factory_id == "TEST_FACTORY"
    assert recommendation.factory_name == "Test Factory"
    assert recommendation.industry == "textile"
    assert recommendation.state == "Tamil Nadu"
    assert recommendation.recommended_scenario_id is not None
    assert len(recommendation.recommended_technology_sequence) > 0

    # Check economic fields
    assert recommendation.capex_total_inr > 0
    assert recommendation.annual_opex_inr > 0
    assert len(recommendation.payback_range_years) == 2

    # Check environmental fields
    assert recommendation.co2_reduction_pct >= 0
    assert recommendation.fossil_fuel_reduction_pct >= 0

    # Check MCDA fields
    assert recommendation.composite_score >= 0
    assert "cost" in recommendation.objective_scores
    assert "emissions" in recommendation.objective_scores
    assert "risk" in recommendation.objective_scores

    # Check explanation fields
    assert len(recommendation.explanation.why_selected) > 0
    assert len(recommendation.explanation.why_others_rejected) >= 0
    assert recommendation.explanation.policy_benefits is not None
    assert recommendation.explanation.sensitivity_notes is not None


def test_pdf_report_generation():
    """Test that PDF report generation works without errors."""
    from decision_engine.reports.pdf_report import generate_pdf_report

    optimization_result = _create_mock_optimization_result()
    policy_result = _create_mock_policy_result()
    reliability_result = _create_mock_reliability_result()
    scenarios = _create_mock_scenarios()

    recommendation = generate_recommendation(
        factory_id="TEST_FACTORY",
        factory_name="Test Factory",
        industry="textile",
        state="Tamil Nadu",
        optimization_result=optimization_result,
        policy_result=policy_result,
        reliability_result=reliability_result,
        scenarios=scenarios,
    )

    with tempfile.TemporaryDirectory() as temp_dir:
        output_path = Path(temp_dir) / "test_report.pdf"
        result_path = generate_pdf_report(recommendation, output_path)

        assert result_path.exists()
        assert result_path.stat().st_size > 0  # File is not empty


def test_excel_report_generation():
    """Test that Excel report generation works without errors."""
    from decision_engine.reports.excel_report import generate_excel_report

    optimization_result = _create_mock_optimization_result()
    policy_result = _create_mock_policy_result()
    reliability_result = _create_mock_reliability_result()
    scenarios = _create_mock_scenarios()

    recommendation = generate_recommendation(
        factory_id="TEST_FACTORY",
        factory_name="Test Factory",
        industry="textile",
        state="Tamil Nadu",
        optimization_result=optimization_result,
        policy_result=policy_result,
        reliability_result=reliability_result,
        scenarios=scenarios,
    )

    with tempfile.TemporaryDirectory() as temp_dir:
        output_path = Path(temp_dir) / "test_report.xlsx"
        result_path = generate_excel_report(
            recommendation, optimization_result, output_path
        )

        assert result_path.exists()
        assert result_path.stat().st_size > 0  # File is not empty


def test_human_readable_explanations():
    """Gate test: explanations are human-readable for non-experts."""
    optimization_result = _create_mock_optimization_result()
    policy_result = _create_mock_policy_result()
    reliability_result = _create_mock_reliability_result()
    scenarios = _create_mock_scenarios()

    recommendation = generate_recommendation(
        factory_id="TEST_FACTORY",
        factory_name="Test Factory",
        industry="textile",
        state="Tamil Nadu",
        optimization_result=optimization_result,
        policy_result=policy_result,
        reliability_result=reliability_result,
        scenarios=scenarios,
    )

    # Check why_selected is human-readable
    for reason in recommendation.explanation.why_selected:
        # Should not contain raw variable names or technical jargon
        assert "scenario_id" not in reason.lower()
        assert "objective_scores" not in reason.lower()
        assert "capex_inr" not in reason.lower()
        # Should contain plain language
        assert len(reason.split()) >= 5  # Minimum reasonable length

    # Check why_others_rejected is specific and human-readable
    for rejected in recommendation.explanation.why_others_rejected:
        assert rejected.reason != "less optimal"
        assert rejected.key_weakness != "low score"
        # Should be specific
        assert any(
            word in rejected.key_weakness.lower()
            for word in ["cost", "emissions", "risk", "higher", "lower"]
        )

    # Check sensitivity_notes is human-readable
    sensitivity = recommendation.explanation.sensitivity_notes
    assert sensitivity.risk_interpretation
    assert "payback" in sensitivity.risk_interpretation.lower()
    assert len(sensitivity.risk_interpretation) > 20


def test_disclaimer_appears_in_recommendation():
    """Test that disclaimer appears in recommendation when benefit is unverified."""
    optimization_result = _create_mock_optimization_result()
    policy_result = _create_mock_policy_result()
    reliability_result = _create_mock_reliability_result()
    scenarios = _create_mock_scenarios()

    recommendation = generate_recommendation(
        factory_id="TEST_FACTORY",
        factory_name="Test Factory",
        industry="textile",
        state="Tamil Nadu",
        optimization_result=optimization_result,
        policy_result=policy_result,
        reliability_result=reliability_result,
        scenarios=scenarios,
    )

    # Check that disclaimer is present in policy benefits
    assert not recommendation.explanation.policy_benefits.total_benefit_verified
    assert len(recommendation.explanation.policy_benefits.disclaimer) > 0
    assert "manual verification" in recommendation.explanation.policy_benefits.disclaimer.lower()
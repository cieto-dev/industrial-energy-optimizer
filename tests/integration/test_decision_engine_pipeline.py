from __future__ import annotations

import pytest

from decision_engine.baseline.baseline_engine import compute_baseline
from decision_engine.optimizer.optimization_engine import (
    ScenarioMetrics,
    optimize,
)

pytestmark = pytest.mark.integration


def _make_candidates() -> list[ScenarioMetrics]:
    """Create deterministic optimizer candidates for integration tests."""
    return [
        ScenarioMetrics(
            scenario_id="integration_efficiency",
            technology_sequence=["efficiency_upgrade"],
            capex_inr=800_000,
            annual_opex_inr=800_000,
            pathway_co2_tonnes_year=900,
            co2_reduction_pct=10.0,
            spread_ratio=0.55,
            supply_reliability=90.0,
        ),
        ScenarioMetrics(
            scenario_id="integration_biomass",
            technology_sequence=["biomass_boiler"],
            capex_inr=2_800_000,
            annual_opex_inr=1_400_000,
            pathway_co2_tonnes_year=320,
            co2_reduction_pct=60.0,
            spread_ratio=0.28,
            supply_reliability=80.0,
        ),
        ScenarioMetrics(
            scenario_id="integration_solar",
            technology_sequence=["solar_thermal", "electric_backup"],
            capex_inr=4_500_000,
            annual_opex_inr=900_000,
            pathway_co2_tonnes_year=180,
            co2_reduction_pct=90.0,
            spread_ratio=0.16,
            supply_reliability=100.0,
        ),
    ]


def test_baseline_is_deterministic(sample_factory) -> None:
    """
    The same factory input must produce the same baseline every time.
    """
    baseline_1 = compute_baseline(sample_factory)
    baseline_2 = compute_baseline(sample_factory)

    assert baseline_1 == baseline_2


def test_baseline_contains_sane_values(sample_factory) -> None:
    """
    Baseline output must remain physically meaningful.
    """
    baseline = compute_baseline(sample_factory)

    assert baseline.annual_thermal_energy_mj >= 0
    assert baseline.annual_electricity_kwh >= 0
    assert baseline.annual_fuel_cost_inr >= 0
    assert baseline.annual_electricity_cost_inr >= 0
    assert baseline.annual_co2_tonnes >= 0


def test_optimizer_is_deterministic() -> None:
    """
    Identical scenario inputs must produce identical rankings.
    """
    candidates_1 = _make_candidates()
    candidates_2 = _make_candidates()

    result_1 = optimize(candidates_1)
    result_2 = optimize(candidates_2)

    assert result_1.recommended_scenario_id == (
        result_2.recommended_scenario_id
    )

    assert result_1.ranked_scenarios == result_2.ranked_scenarios


def test_optimizer_returns_all_candidate_scenarios() -> None:
    """
    No candidate should silently disappear during optimization.
    """
    result = optimize(_make_candidates())

    ranked_ids = [
        item.scenario_id
        for item in result.ranked_scenarios
    ]

    assert len(ranked_ids) == 3
    assert set(ranked_ids) == {
        "integration_efficiency",
        "integration_biomass",
        "integration_solar",
    }


def test_optimizer_assigns_valid_ranks() -> None:
    """
    Ranking must be 1..N with no duplicate ranks.
    """
    result = optimize(_make_candidates())

    ranks = [
        item.rank
        for item in result.ranked_scenarios
    ]

    assert sorted(ranks) == [1, 2, 3]


def test_optimizer_marks_exactly_one_recommendation() -> None:
    """
    Exactly one scenario must be marked as recommended.
    """
    result = optimize(_make_candidates())

    recommended = [
        item
        for item in result.ranked_scenarios
        if item.is_recommended
    ]

    assert len(recommended) == 1
    assert (
        recommended[0].scenario_id
        == result.recommended_scenario_id
    )


def test_optimizer_rejects_duplicate_scenario_ids() -> None:
    candidates = _make_candidates()

    candidates[1].scenario_id = candidates[0].scenario_id

    with pytest.raises(ValueError, match="Duplicate"):
        optimize(candidates)


def test_optimizer_requires_multiple_candidates() -> None:
    with pytest.raises(ValueError):
        optimize(_make_candidates()[:1])


def test_optimizer_rejects_empty_candidate_list() -> None:
    with pytest.raises(ValueError):
        optimize([])
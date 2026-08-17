"""
test_optimizer.py — Gate tests for Sprint 3.2 Optimizer / MCDA.

Gate requirements (from ROADMAP.md Sprint 3.2):
1. Ranking must NOT always pick the cheapest scenario.
2. Recommended scenario is explainably not always the cheapest.
3. Scores are the three DOMAIN_MODEL objectives: cost, emissions, risk.

Test structure
--------------
Three candidate pathways after economics + emissions + reliability:

  cheap_fossil
    - Lowest CAPEX / OPEX (lifecycle cost winner)
    - Highest remaining CO2
    - Highest reliability spread (risk)

  balanced_biomass
    - Mid CAPEX
    - Mid CO2
    - Mid risk

  expensive_solar
    - Highest CAPEX
    - Lowest pathway CO2
    - Lowest risk

Under default weights (cost 0.40, emissions 0.35, risk 0.25) the
cheapest fossil option must lose. Under Weights.cost_only() it must win.
That pair of assertions is the differentiator the roadmap requires.
"""

import os
import sys

import pytest

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _REPO_ROOT)

from decision_engine.optimizer.mcda import (
    COST_HORIZON_YEARS,
    ScenarioMetrics,
    lifecycle_cost,
    score_scenarios,
)
from decision_engine.optimizer.optimization_engine import (
    cheapest_by_lifecycle,
    optimize,
)
from decision_engine.optimizer.weights import (
    CRITERIA,
    Weights,
    default_weights,
)


def _three_pathways() -> list[ScenarioMetrics]:
    return [
        ScenarioMetrics(
            scenario_id="cheap_fossil",
            technology_sequence=["efficiency_upgrade"],
            capex_inr=800_000,
            annual_opex_inr=800_000,
            pathway_co2_tonnes_year=900.0,
            spread_ratio=0.55,
        ),
        ScenarioMetrics(
            scenario_id="balanced_biomass",
            technology_sequence=["biomass_boiler"],
            capex_inr=2_800_000,
            annual_opex_inr=1_400_000,
            pathway_co2_tonnes_year=320.0,
            spread_ratio=0.28,
        ),
        ScenarioMetrics(
            scenario_id="expensive_solar",
            technology_sequence=["solar_thermal", "electric_backup"],
            capex_inr=4_500_000,
            annual_opex_inr=900_000,
            pathway_co2_tonnes_year=180.0,
            spread_ratio=0.16,
        ),
    ]


def test_default_weights_are_documented_and_sum_to_one():
    weights = default_weights()
    assert weights.cost == pytest.approx(0.40)
    assert weights.emissions == pytest.approx(0.35)
    assert weights.risk == pytest.approx(0.25)
    assert abs(sum(weights.as_dict().values()) - 1.0) < 1e-9


def test_weights_reject_negative_and_unnormalised():
    with pytest.raises(ValueError):
        Weights(cost=-0.1, emissions=0.6, risk=0.5)
    with pytest.raises(ValueError):
        Weights(cost=0.5, emissions=0.5, risk=0.5)


def test_cheapest_is_cheap_fossil():
    candidates = _three_pathways()
    assert cheapest_by_lifecycle(candidates) == "cheap_fossil"
    costs = {m.scenario_id: lifecycle_cost(m) for m in candidates}
    assert costs["cheap_fossil"] < costs["balanced_biomass"]
    assert costs["cheap_fossil"] < costs["expensive_solar"]
    # sanity: 10-year horizon is applied
    cheap = candidates[0]
    assert costs["cheap_fossil"] == (
        cheap.capex_inr + cheap.annual_opex_inr * COST_HORIZON_YEARS
    )


def test_default_mcda_does_not_pick_cheapest():
    result = optimize(_three_pathways())
    assert result.cheapest_scenario_id == "cheap_fossil"
    assert result.recommended_scenario_id != "cheap_fossil"
    assert result.recommended_is_cheapest is False
    assert "not the cheapest" in result.why_not_always_cheapest.lower()


def test_cost_only_weights_do_pick_cheapest():
    result = optimize(_three_pathways(), weights=Weights.cost_only())
    assert result.recommended_scenario_id == "cheap_fossil"
    assert result.recommended_is_cheapest is True


def test_emissions_heavy_weights_prefer_lowest_co2():
    result = optimize(
        _three_pathways(),
        weights={"cost": 0.10, "emissions": 0.80, "risk": 0.10},
    )
    assert result.recommended_scenario_id == "expensive_solar"


def test_objective_scores_match_domain_model_keys():
    result = optimize(_three_pathways())
    for row in result.ranked_scenarios:
        assert set(row.objective_scores) == set(CRITERIA)
        for value in row.objective_scores.values():
            assert 0.0 <= value <= 1.0
        assert row.rank >= 1
    assert result.ranked_scenarios[0].is_recommended is True
    assert result.ranked_scenarios[0].rank == 1


def test_score_scenarios_preserves_input_order():
    scored = score_scenarios(_three_pathways())
    assert [s.scenario_id for s in scored] == [
        "cheap_fossil",
        "balanced_biomass",
        "expensive_solar",
    ]


def test_nested_engine_objects_are_accepted():
    class FakeFinancial:
        capex_estimate = 1_000_000
        proposed_annual_opex = 500_000

    class FakeEmission:
        pathway_co2_tonnes_year = 400.0

    class FakeRiskHigh:
        spread_ratio = 0.62
        overall_tier = "VERY_HIGH"

    class FakeRiskLow:
        spread_ratio = 0.14
        overall_tier = "LOW"

    class FakeFinancialExpensive:
        capex_estimate = 3_000_000
        proposed_annual_opex = 400_000

    class FakeEmissionLow:
        pathway_co2_tonnes_year = 100.0

    candidates = [
        ScenarioMetrics(
            scenario_id="nested_cheap_dirty",
            technology_sequence=["coal"],
            financial=FakeFinancial(),
            emission=FakeEmission(),
            risk_score=FakeRiskHigh(),
        ),
        ScenarioMetrics(
            scenario_id="nested_clean",
            technology_sequence=["heat_pump"],
            financial=FakeFinancialExpensive(),
            emission=FakeEmissionLow(),
            risk_score=FakeRiskLow(),
        ),
    ]
    result = optimize(candidates)
    assert result.cheapest_scenario_id == "nested_cheap_dirty"
    assert result.recommended_scenario_id == "nested_clean"


def test_requires_at_least_two_candidates():
    with pytest.raises(ValueError):
        optimize(_three_pathways()[:1])


def test_duplicate_scenario_ids_rejected():
    dup = _three_pathways()
    dup[1].scenario_id = "cheap_fossil"
    with pytest.raises(ValueError, match="Duplicate"):
        optimize(dup)

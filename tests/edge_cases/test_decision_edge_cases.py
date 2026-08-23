from __future__ import annotations

import pytest

from decision_engine.optimizer.optimization_engine import (
    ScenarioMetrics,
    optimize,
)
from decision_engine.optimizer.weights import Weights

from models.factory import Factory, Quantity

pytestmark = pytest.mark.edge


def _valid_factory(**overrides):
    data = dict(
        factory_id="EDGE-001",
        name="Edge Factory",
        industry="textile",
        state="Tamil Nadu",
        district="Coimbatore",
        production_per_day=Quantity(
            value=1000,
            unit="kg/day",
        ),
        operating_hours_per_day=8,
        operating_days_per_year=300,
        current_fuel="coal",
        fuel_consumption=Quantity(
            value=100,
            unit="kg/day",
        ),
        electricity_consumption_kwh_day=1000,
        required_process_temperature_c=180,
        roof_area_sqm=1000,
        available_land_sqm=2000,
        budget_inr=5_000_000,
        grid_reliability_pct=95,
        msme_classification="small",
        udyam_registered=True,
        udyam_number="EDGE-UDYAM",
        annual_turnover_inr=20_000_000,
        plant_and_machinery_or_equipment_investment_inr=8_000_000,
        project_type="energy_efficiency",
        project_cost_inr=2_000_000,
        loan_amount_inr=None,
        existing_or_new_project="existing",
        brownfield_or_greenfield="brownfield",
        cluster_name=None,
        cluster_is_adeetie_identified=None,
        annual_energy_savings_percent=10,
        special_category=None,
    )

    data.update(overrides)
    return Factory(**data)


@pytest.mark.parametrize(
    "temperature",
    [0, 1, 180, 1000, 1800],
)
def test_factory_temperature_boundary_values_are_constructible(
    temperature: float,
) -> None:
    factory = _valid_factory(
        required_process_temperature_c=temperature,
    )

    assert factory.required_process_temperature_c == temperature


def test_zero_budget_is_allowed_by_domain_schema() -> None:
    factory = _valid_factory(budget_inr=0)

    assert factory.budget_inr == 0


def test_zero_electricity_consumption_is_allowed() -> None:
    factory = _valid_factory(
        electricity_consumption_kwh_day=0,
    )

    assert factory.electricity_consumption_kwh_day == 0


def test_zero_roof_area_is_allowed() -> None:
    factory = _valid_factory(roof_area_sqm=0)

    assert factory.roof_area_sqm == 0


def test_negative_budget_is_rejected() -> None:
    with pytest.raises(Exception):
        _valid_factory(budget_inr=-1)


def test_negative_temperature_is_rejected() -> None:
    with pytest.raises(Exception):
        _valid_factory(
            required_process_temperature_c=-0.1,
        )


def test_grid_reliability_above_100_is_rejected() -> None:
    with pytest.raises(Exception):
        _valid_factory(
            grid_reliability_pct=100.1,
        )


def test_optimizer_handles_equal_costs_without_crashing() -> None:
    candidates = [
        ScenarioMetrics(
            scenario_id="a",
            technology_sequence=["a"],
            capex_inr=1000,
            annual_opex_inr=100,
            pathway_co2_tonnes_year=100,
            co2_reduction_pct=10.0,
            spread_ratio=0.2,
            supply_reliability=90.0,
        ),
        ScenarioMetrics(
            scenario_id="b",
            technology_sequence=["b"],
            capex_inr=1000,
            annual_opex_inr=100,
            pathway_co2_tonnes_year=90,
            co2_reduction_pct=20.0,
            spread_ratio=0.2,
            supply_reliability=90.0,
        ),
    ]

    result = optimize(candidates)

    assert result.recommended_scenario_id in {"a", "b"}


def test_optimizer_rejects_single_candidate() -> None:
    candidate = ScenarioMetrics(
        scenario_id="only",
        technology_sequence=["only"],
        capex_inr=1000,
        annual_opex_inr=100,
        pathway_co2_tonnes_year=100,
        co2_reduction_pct=50.0,
        spread_ratio=0.2,
        supply_reliability=90.0,
    )

    with pytest.raises(ValueError):
        optimize([candidate])


def test_empty_candidate_list_is_rejected() -> None:
    with pytest.raises(ValueError):
        optimize([])


def test_negative_weight_is_rejected() -> None:
    with pytest.raises(ValueError):
        Weights(
            financial=-0.1,
            carbon_reduction=0.6,
            risk=0.5,
        )


def test_weight_sum_must_equal_one() -> None:
    with pytest.raises(ValueError):
        Weights(
            financial=0.3,
            carbon_reduction=0.3,
            risk=0.3,
        )


def test_optimizer_does_not_mutate_input_candidates() -> None:
    candidates = [
        ScenarioMetrics(
            scenario_id="a",
            technology_sequence=["a"],
            capex_inr=1000,
            annual_opex_inr=100,
            pathway_co2_tonnes_year=100,
            co2_reduction_pct=10.0,
            spread_ratio=0.2,
            supply_reliability=90.0,
        ),
        ScenarioMetrics(
            scenario_id="b",
            technology_sequence=["b"],
            capex_inr=2000,
            annual_opex_inr=100,
            pathway_co2_tonnes_year=80,
            co2_reduction_pct=20.0,
            spread_ratio=0.1,
            supply_reliability=90.0,
        ),
    ]

    before = [
        (
            item.scenario_id,
            list(item.technology_sequence),
            item.capex_inr,
            item.annual_opex_inr,
            item.pathway_co2_tonnes_year,
        )
        for item in candidates
    ]

    optimize(candidates)

    after = [
        (
            item.scenario_id,
            list(item.technology_sequence),
            item.capex_inr,
            item.annual_opex_inr,
            item.pathway_co2_tonnes_year,
        )
        for item in candidates
    ]

    assert before == after
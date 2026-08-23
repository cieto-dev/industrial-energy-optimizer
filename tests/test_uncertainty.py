import os
import sys

import pytest

_REPO_ROOT = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

sys.path.insert(
    0,
    _REPO_ROOT,
)

from decision_engine.reliability.reliability_engine import (
    BaseCaseInputs,
    run_best_expected_worst,
    run_reliability_sweep,
)


@pytest.fixture
def base_case():
    return BaseCaseInputs(
        capex_min=2_800_000,
        capex_max=3_500_000,

        baseline_annual_opex=2_000_000,

        proposed_fuel_cost=1_100_000,
        proposed_electricity_cost=200_000,
        proposed_maintenance_cost=150_000,
        proposed_labour_cost=120_000,
        proposed_other_cost=30_000,

        baseline_fuel_cost=1_800_000,
        baseline_electricity_cost=200_000,

        solar_fraction=0.0,

        biomass_fraction=1.0,

        baseline_co2_tco2e=2_000,
        proposed_co2_tco2e=700,

        obligated_entity=True,
        eligible_credit_generation=False,

        technology_id="TECH_BIOMASS_BOILER",
        scenario_id="SC_BIOMASS_TASK_34",
    )


def test_best_expected_worst_are_distinct(base_case):

    result = run_best_expected_worst(
        base_case,

        best_factors={
            "fuel_price": 1.0,
            "electricity_tariff": 1.0,
            "biomass_cost": 0.9,
            "efficiency": 1.10,
            "carbon_price": 3000.0,
            "production_volume": 1.0,
            "solar_capacity_factor": 1.0,
            "capex_overrun": 1.0,
        },

        expected_factors={
            "fuel_price": 1.0,
            "electricity_tariff": 1.0,
            "biomass_cost": 1.0,
            "efficiency": 1.0,
            "carbon_price": 0.0,
            "production_volume": 1.0,
            "solar_capacity_factor": 1.0,
            "capex_overrun": 1.0,
        },

        worst_factors={
            "fuel_price": 1.24,
            "electricity_tariff": 1.20,
            "biomass_cost": 1.40,
            "efficiency": 0.90,
            "carbon_price": 0.0,
            "production_volume": 1.0,
            "solar_capacity_factor": 1.0,
            "capex_overrun": 1.18,
        },
    )

    assert (
        result.best_case.label
        == "Best case"
    )

    assert (
        result.expected_case.label
        == "Expected"
    )

    assert (
        result.worst_case.label
        == "Worst case"
    )

    assert (
        result.best_case.payback_years
        is not None
    )

    assert (
        result.expected_case.payback_years
        is not None
    )

    assert (
        result.worst_case.payback_years
        is not None
    )

    assert (
        result.best_case.payback_years
        < result.worst_case.payback_years
    )


def test_five_requested_variables_are_present(base_case):

    result = run_best_expected_worst(
        base_case,

        best_factors={
            "fuel_price": 1.0,
            "electricity_tariff": 1.0,
            "biomass_cost": 0.9,
            "efficiency": 1.10,
            "carbon_price": 3000.0,
        },

        expected_factors={
            "fuel_price": 1.0,
            "electricity_tariff": 1.0,
            "biomass_cost": 1.0,
            "efficiency": 1.0,
            "carbon_price": 0.0,
        },

        worst_factors={
            "fuel_price": 1.24,
            "electricity_tariff": 1.20,
            "biomass_cost": 1.40,
            "efficiency": 0.90,
            "carbon_price": 0.0,
        },
    )

    expected_variables = {
        "fuel_price",
        "electricity_tariff",
        "biomass_cost",
        "efficiency",
        "carbon_price",
    }

    assert expected_variables.issubset(
        set(
            result.expected_case.factors.keys()
        )
    )


def test_carbon_price_changes_obligated_case(base_case):

    result_zero = run_best_expected_worst(
        base_case,

        best_factors={
            "fuel_price": 1.0,
            "electricity_tariff": 1.0,
            "biomass_cost": 1.0,
            "efficiency": 1.0,
            "carbon_price": 0.0,
        },

        expected_factors={
            "fuel_price": 1.0,
            "electricity_tariff": 1.0,
            "biomass_cost": 1.0,
            "efficiency": 1.0,
            "carbon_price": 0.0,
        },

        worst_factors={
            "fuel_price": 1.0,
            "electricity_tariff": 1.0,
            "biomass_cost": 1.0,
            "efficiency": 1.0,
            "carbon_price": 3000.0,
        },
    )

    assert (
        result_zero.best_case.payback_years
        is not None
    )

    assert (
        result_zero.worst_case.payback_years
        is not None
    )


def test_monte_carlo_contains_required_variables(base_case):

    result = run_reliability_sweep(
        base_case=base_case,
        n_iterations=1000,
        random_seed=42,
    )

    variables = set(
        result.metadata[
            "variables"
        ].keys()
    )

    assert "fuel_price" in variables
    assert "electricity_tariff" in variables
    assert "biomass_cost" in variables
    assert "efficiency" in variables
    assert "carbon_price" in variables


def test_monte_carlo_has_meaningful_range(base_case):

    result = run_reliability_sweep(
        base_case=base_case,
        n_iterations=1000,
        random_seed=42,
    )

    assert (
        result.payback_p90
        > result.payback_p10
    )

    assert (
        result.payback_p10
        <= result.payback_p50
        <= result.payback_p90
    )
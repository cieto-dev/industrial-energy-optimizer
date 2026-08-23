from __future__ import annotations

import json
from pathlib import Path

import pytest

from decision_engine.optimizer.optimization_engine import (
    ScenarioMetrics,
    optimize,
)

pytestmark = pytest.mark.regression


REGRESSION_FILE = (
    Path(__file__).resolve().parents[2]
    / "tests"
    / "regression"
    / "golden_optimizer_cases.json"
)


def _candidates() -> list[ScenarioMetrics]:
    return [
        ScenarioMetrics(
            scenario_id="cheap_fossil",
            technology_sequence=["efficiency_upgrade"],
            capex_inr=800_000,
            annual_opex_inr=800_000,
            pathway_co2_tonnes_year=900,
            co2_reduction_pct=10.0,
            spread_ratio=0.55,
            supply_reliability=90.0,
        ),
        ScenarioMetrics(
            scenario_id="balanced_biomass",
            technology_sequence=["biomass_boiler"],
            capex_inr=2_800_000,
            annual_opex_inr=1_400_000,
            pathway_co2_tonnes_year=320,
            co2_reduction_pct=60.0,
            spread_ratio=0.28,
            supply_reliability=80.0,
        ),
        ScenarioMetrics(
            scenario_id="expensive_solar",
            technology_sequence=["solar_thermal", "electric_backup"],
            capex_inr=4_500_000,
            annual_opex_inr=900_000,
            pathway_co2_tonnes_year=180,
            co2_reduction_pct=90.0,
            spread_ratio=0.16,
            supply_reliability=100.0,
        ),
    ]


def test_default_optimizer_regression_contract() -> None:
    result = optimize(_candidates())

    assert result.cheapest_scenario_id == "cheap_fossil"
    assert result.recommended_scenario_id != "cheap_fossil"

    ranked_ids = [
        item.scenario_id
        for item in result.ranked_scenarios
    ]

    assert ranked_ids
    assert len(ranked_ids) == 3
    assert len(set(ranked_ids)) == 3


def test_cost_only_regression_contract() -> None:
    from decision_engine.optimizer.weights import Weights

    result = optimize(
        _candidates(),
        weights=Weights.from_mapping({"financial": 1.0}),
    )

    assert result.recommended_scenario_id == "cheap_fossil"


def test_regression_case_file_is_valid_if_present() -> None:
    if not REGRESSION_FILE.exists():
        pytest.skip("Golden regression file not created yet.")

    payload = json.loads(
        REGRESSION_FILE.read_text(encoding="utf-8")
    )

    assert isinstance(payload, dict)
    assert payload.get("cases")
    assert isinstance(payload["cases"], list)


def test_optimizer_output_is_json_serializable() -> None:
    result = optimize(_candidates())

    payload = result.model_dump() if hasattr(
        result,
        "model_dump",
    ) else result.__dict__

    encoded = json.dumps(
        payload,
        default=str,
        sort_keys=True,
    )

    assert encoded
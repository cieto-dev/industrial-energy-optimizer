import pytest
from unittest.mock import MagicMock
from decision_engine.reliability.hardened_risk_score import score_hardened_risk


def test_score_hardened_risk_solar_thermal_perfect_match():
    # Setup mock baseline
    baseline = MagicMock()
    baseline.firm_recommendation_blocked = False
    baseline.firm_recommendation_blocked_reasons = []

    # Setup tech record
    tech_record = {
        "technology_id": "TECH_SOLAR_THERMAL",
        "status": "verified",
        "performance_parameters": {
            "efficiency_percent": {"value": 50.0, "confidence": "High"},
            "maximum_process_temperature_c": {"value": 250}
        },
        "operational_constraints": {
            "requires_solar_resource": True
        },
        "economic_parameters": {
            "opex_fixed_percent_capex": {"value": 1.5}
        }
    }

    # Execute
    result = score_hardened_risk(
        sweep_result=None,
        technology_record=tech_record,
        baseline=baseline,
        required_process_temp_c=80.0
    )

    # Verify component scores
    assert result.temperature_match_score == 100.0  # 250 >= 80
    assert result.technology_maturity_score == 90.0  # verified + High
    assert result.production_continuity_score == 70.0  # requires_solar_resource = True
    assert result.fuel_logistics_score == 90.0  # no biomass
    assert result.grid_dependency_score == 100.0  # no grid
    assert result.maintenance_complexity_score == 90.0  # 1.5 <= 2.0

    # Composite score shouldn't be blocked for solar thermal risk
    assert result.composite_risk_score > 40.0
    assert result.firm_recommendation_blocked is False


def test_score_hardened_risk_blocked_threshold():
    # Setup mock baseline
    baseline = MagicMock()
    baseline.firm_recommendation_blocked = False
    baseline.firm_recommendation_blocked_reasons = []

    # Setup high risk tech
    tech_record = {
        "technology_id": "TECH_HIGH_RISK",
        "status": "estimated",
        "performance_parameters": {
            "efficiency_percent": {"value": 50.0, "confidence": "Low"},
            "maximum_process_temperature_c": {"value": 50.0} # mismatched temp
        },
        "operational_constraints": {
            "requires_biomass_supply": True,
            "requires_grid": True
        },
        "economic_parameters": {
            "opex_fixed_percent_capex": {"value": 10.0} # high maintenance
        }
    }
    
    # Mock sweep result with high spread
    sweep = MagicMock()
    sweep.spread_ratio = 1.5 # Huge spread -> score 0
    sweep.overall_tier = "VERY_HIGH"

    # Execute with required process temp much higher than max
    result = score_hardened_risk(
        sweep_result=sweep,
        technology_record=tech_record,
        baseline=baseline,
        required_process_temp_c=250.0
    )

    # Component check
    assert result.temperature_match_score == 20.0  # (50/250) * 100
    assert result.maintenance_complexity_score == 30.0 # > 5.0
    assert result.fuel_logistics_score == 40.0 # biomass
    assert result.payback_uncertainty_score == 0.0 # 100 - (1.5-1)*200

    # Should be blocked due to low composite score
    assert result.composite_risk_score < 40.0
    assert result.firm_recommendation_blocked is True
    assert any("Composite reliability score" in r for r in result.blocking_reasons)

import pytest
from decision_engine.baseline.models import BaselineProfile
from decision_engine.economics.models import CapexResult
from decision_engine.economics.economics_engine_v2 import calculate_economics_v2

def test_calculate_economics_v2_blocked_baseline():
    """Test that a blocked baseline immediately returns a blocked FinancialModel."""
    from unittest.mock import MagicMock
    # Setup blocked baseline
    baseline = MagicMock()
    baseline.firm_recommendation_blocked = True
    baseline.firm_recommendation_blocked_reasons = ["Baseline data is incomplete."]
    baseline.annual_total_energy_cost_inr = 1500000
    baseline.annual_fuel_cost_inr = 1000000
    baseline.annual_electricity_cost_inr = 500000
    baseline.data_quality_warnings = []
    baseline.parameter_confidence_summary = {}

    # Execute
    result = calculate_economics_v2(
        baseline=baseline,
        technology_id="TECH_WHR",
        scenario_id="scenario_1",
        proposed_opex_inputs={"fuel_cost": 800000},
        capacity=100,
        usd_to_inr=83.5
    )

    # Verify
    assert result.firm_recommendation_blocked is True
    assert "Baseline data is incomplete." in result.firm_recommendation_blocked_reasons
    assert result.capex.status == "unavailable"
    assert result.payback_min_years is None


def test_calculate_economics_v2_null_capex():
    """Test that null CAPEX in KB (like Biomass) sets a data gap and blocks the recommendation."""
    from unittest.mock import MagicMock
    # Setup unblocked baseline
    baseline = MagicMock()
    baseline.firm_recommendation_blocked = False
    baseline.firm_recommendation_blocked_reasons = []
    baseline.annual_total_energy_cost_inr = 1500000
    baseline.annual_fuel_cost_inr = 1000000
    baseline.annual_electricity_cost_inr = 500000
    baseline.data_quality_warnings = []
    baseline.parameter_confidence_summary = {}

    # TECH_BIOMASS_BOILER has null CAPEX in KB
    result = calculate_economics_v2(
        baseline=baseline,
        technology_id="TECH_BIOMASS_BOILER",
        scenario_id="scenario_2",
        proposed_opex_inputs={"fuel_cost": 500000},
        capacity=1000,
        usd_to_inr=83.5
    )

    # Verify
    assert result.firm_recommendation_blocked is True
    assert any("CAPEX" in reason for reason in result.firm_recommendation_blocked_reasons)
    
    # Check data gap flags
    capex_gap = next((flag for flag in result.data_gap_flags if flag.field == "capex"), None)
    assert capex_gap is not None
    assert capex_gap.severity == "blocking"
    assert capex_gap.reason == "null_value"
    
    # Ensure point estimates are null
    assert result.capex.status == "unavailable"
    assert result.payback_min_years is None
    assert result.roi_min_pct is None
    assert result.npv_min_inr is None

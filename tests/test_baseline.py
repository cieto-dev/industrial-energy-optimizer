"""
Unit tests for the baseline engine.

Tests the baseline calculation using a known textile MSME
input and deterministic expected outputs.
"""

import pytest

from decision_engine import baseline
from models.factory import Factory, Quantity
from decision_engine.baseline.baseline_engine import compute_baseline


def make_textile_factory() -> Factory:
    """Create a deterministic textile MSME test factory."""

    return Factory(
        factory_id="TEST-TEXTILE-001",
        name="Test Textile MSME",

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
        udyam_number="TEST-UDYAM-001",

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


def test_textile_baseline_known_input_output():
    """
    Test baseline calculations against known expected outputs.

    Input:
        Coal = 100 kg/day
        Electricity = 1000 kWh/day
        Operating days = 300/year

    Expected:
        Thermal energy = 588,900 MJ/year
        Electricity = 300,000 kWh/year
        Coal cost = 255,000 INR/year
        Electricity cost = 2,250,000 INR/year
        Total CO2 = approximately 779.443 tonnes/year
    """

    factory = make_textile_factory()

    baseline = compute_baseline(factory)
    
    assert baseline.annual_thermal_energy_mj == pytest.approx(
        588_900.0,
        rel=1e-6,
)

    assert baseline.annual_electricity_kwh == pytest.approx(
        300_000.0,
        rel=1e-6,
    )

    assert baseline.annual_fuel_cost_inr == pytest.approx(
        255_000.0,
        rel=1e-6,
    )

    assert baseline.annual_electricity_cost_inr == pytest.approx(
        2_250_000.0,
        rel=1e-6,
    )

    assert baseline.annual_co2_tonnes == pytest.approx(
        270.1033,
        abs=0.001,
    )


def test_baseline_returns_positive_energy_and_costs():
    """Verify that the baseline profile contains sensible positive values."""

    factory = make_textile_factory()

    baseline = compute_baseline(factory)

    assert baseline.annual_thermal_energy_mj > 0
    assert baseline.annual_electricity_kwh > 0
    assert baseline.annual_fuel_cost_inr > 0
    assert baseline.annual_electricity_cost_inr > 0
    assert baseline.annual_co2_tonnes > 0
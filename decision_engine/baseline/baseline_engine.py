import json
from pathlib import Path
from models.factory import Factory
from decision_engine.baseline.models import BaselineProfile
from decision_engine.baseline.energy_calculator import (
    calculate_annual_thermal_demand,
    calculate_annual_electricity_demand
)
from decision_engine.baseline.fuel_calculator import calculate_annual_energy_cost
from decision_engine.baseline._units import standardize_daily_consumption
from decision_engine.emissions.emission_engine import calculate_fuel_emissions
from decision_engine.emissions.emission_factors import get_emission_factor

BASE_DIR = Path(__file__).resolve().parents[2]

def compute_baseline(factory: Factory) -> BaselineProfile:
    # 1. Energy
    annual_thermal_mj = calculate_annual_thermal_demand(factory)
    annual_elec_kwh = calculate_annual_electricity_demand(factory)
    
    fuel = factory.current_fuel.lower().strip()
    ef_data = get_emission_factor(fuel)
    
    # 2. Consumption in base units
    daily_consumption = standardize_daily_consumption(
        factory.fuel_consumption.value,
        factory.fuel_consumption.unit,
        ef_data["input_unit"]
    )
    annual_fuel_base = daily_consumption * factory.operating_days_per_year
    
    # 3. Economics
    costs = calculate_annual_energy_cost(factory, annual_fuel_base, annual_elec_kwh)
    
    # 4. Emissions
    # Calculate fuel emissions (we pass annual consumption to get annual output directly)
    fuel_emissions = calculate_fuel_emissions(fuel, annual_fuel_base)
    # The return dict has keys like 'co2_tco2_day' which now represents annual because of the input
    fuel_co2_tonnes = fuel_emissions["co2_tco2_day"] 
    
    # Calculate electricity emissions
    try:
        grid_file = BASE_DIR / "knowledge-base" / "emissions" / "grid_factors.json"
        with open(grid_file, "r", encoding="utf-8") as f:
            grid_data = json.load(f)
            grid_factor = grid_data["default_factor"]["value"] # kgCO2e/kWh
    except Exception:
        grid_factor = 0.7117
        
    elec_co2_kg = annual_elec_kwh * grid_factor
    elec_co2_tonnes = elec_co2_kg / 1000.0
    
    total_co2_tonnes = fuel_co2_tonnes + elec_co2_tonnes
    
    return BaselineProfile(
        annual_thermal_energy_mj=annual_thermal_mj,
        annual_electricity_kwh=annual_elec_kwh,
        annual_fuel_cost_inr=costs["annual_fuel_cost_inr"],
        annual_electricity_cost_inr=costs["annual_electricity_cost_inr"],
        annual_co2_tonnes=total_co2_tonnes
    )

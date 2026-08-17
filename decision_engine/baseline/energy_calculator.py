from models.factory import Factory
from decision_engine.baseline._units import standardize_daily_consumption
from decision_engine.emissions.emission_engine import calculate_fuel_emissions
from decision_engine.emissions.emission_factors import get_emission_factor

def calculate_annual_thermal_demand(factory: Factory) -> float:
    """
    Calculates annual thermal energy demand in MJ.
    """
    fuel_id = factory.current_fuel.lower().strip()
    
    # Get the expected input unit for this fuel
    ef_data = get_emission_factor(fuel_id)
    target_unit = ef_data["input_unit"]
    
    # Convert given consumption to target unit
    consumption_in_target = standardize_daily_consumption(
        factory.fuel_consumption.value,
        factory.fuel_consumption.unit,
        target_unit
    )
    
    # We use emission_engine to compute energy_tj_day
    emissions_data = calculate_fuel_emissions(fuel_id, consumption_in_target)
    energy_tj_day = emissions_data["energy_tj_day"]
    
    annual_energy_tj = energy_tj_day * factory.operating_days_per_year
    annual_energy_mj = annual_energy_tj * 1_000_000
    
    return annual_energy_mj

def calculate_annual_electricity_demand(factory: Factory) -> float:
    """
    Calculates annual electricity demand in kWh.
    """
    return factory.electricity_consumption_kwh_day * factory.operating_days_per_year

import json
from pathlib import Path
from models.factory import Factory

BASE_DIR = Path(__file__).resolve().parents[2]

FUEL_PRICES_FILE = BASE_DIR / "knowledge-base" / "finance" / "fuel_prices.json"
ELEC_TARIFFS_FILE = BASE_DIR / "knowledge-base" / "finance" / "electricity_tariffs.json"

def _load_json(path):
    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)

def get_fuel_price(fuel: str) -> float:
    fuel_mapping = {
        "coal": "FUEL_COAL",
        "diesel": "FUEL_DIESEL_HSD",
        "lpg": "FUEL_LPG",
        "natural_gas": "FUEL_NATURAL_GAS_PNG",
        "biomass": "FUEL_BIOMASS"
    }
    
    if fuel in ["biogas", "furnace_oil"]:
        raise ValueError("no price data for this fuel")
        
    fuel_id = fuel_mapping.get(fuel)
    if not fuel_id:
        raise ValueError(f"Unknown fuel mapping for {fuel}")
        
    prices_data = _load_json(FUEL_PRICES_FILE)["entities"]
    if fuel_id not in prices_data:
        raise ValueError(f"Fuel ID {fuel_id} not found in fuel_prices.json")
        
    params = prices_data[fuel_id]["parameters"]
    
    if "price_delivered_msme_estimate" in params:
        return params["price_delivered_msme_estimate"]["value"]
    elif "price_retail_reference" in params:
        return params["price_retail_reference"]["value"]
    elif "price_briquettes_industrial" in params:
        return params["price_briquettes_industrial"]["value"]
    
    for key, data in params.items():
        if key.startswith("price_") and data.get("value") is not None:
            return data["value"]
            
    raise ValueError(f"Could not determine a price for {fuel_id}")

def get_electricity_tariff(state: str) -> float:
    tariffs_data = _load_json(ELEC_TARIFFS_FILE)["entities"]
    
    for t_id, data in tariffs_data.items():
        params = data.get("parameters", {})
        
        appl1 = params.get("energy_charge_inr_per_kwh", {}).get("applicability", {})
        if appl1.get("state") == state:
            return params["energy_charge_inr_per_kwh"]["value"]
            
        appl2 = params.get("energy_charge_inr_per_kvah", {}).get("applicability", {})
        if appl2.get("state") == state:
            return params["energy_charge_inr_per_kvah"]["value"]
            
    raise ValueError(f"Missing state in electricity tariffs: {state}")

def calculate_annual_energy_cost(factory: Factory, annual_fuel_base: float, annual_electricity_kwh: float) -> dict:
    fuel_id = factory.current_fuel.lower().strip()
    
    fuel_price = get_fuel_price(fuel_id)
    annual_fuel_cost = fuel_price * annual_fuel_base
    
    elec_tariff = get_electricity_tariff(factory.state)
    annual_elec_cost = elec_tariff * annual_electricity_kwh
    
    # TODO: demand_charge_inr_per_kva_month is already in the tariff data and can be added once Factory captures contracted_demand_kva.
    
    return {
        "annual_fuel_cost_inr": annual_fuel_cost,
        "annual_electricity_cost_inr": annual_elec_cost,
        "total_energy_cost_inr": annual_fuel_cost + annual_elec_cost
    }

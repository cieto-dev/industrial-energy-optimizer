from pydantic import BaseModel

class BaselineProfile(BaseModel):
    """
    Immutable current-state baseline profile of the Factory.
    All pathways are evaluated against this baseline.
    """
    annual_thermal_energy_mj: float
    annual_electricity_kwh: float
    annual_fuel_cost_inr: float
    annual_electricity_cost_inr: float
    annual_co2_tonnes: float

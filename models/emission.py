from pydantic import BaseModel

class EmissionModel(BaseModel):
    baseline_co2_tonnes_year: float
    pathway_co2_tonnes_year: float
    reduction_pct: float
    grid_emission_factor_used: float

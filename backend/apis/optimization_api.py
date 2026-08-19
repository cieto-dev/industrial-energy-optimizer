from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Optional, Any, Dict

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))


router = APIRouter(
    prefix="/optimization",
    tags=["Optimization"]
)


class FactoryProfileRequest(BaseModel):
    """Accept the full factory profile the frontend sends."""
    factory_id: Optional[str] = None
    name: Optional[str] = None
    industry: str
    state: str
    district: Optional[str] = None
    current_fuel: str
    required_process_temperature_c: float
    production_per_day: Optional[Dict[str, Any]] = None
    operating_hours_per_day: Optional[float] = None
    operating_days_per_year: Optional[float] = None
    fuel_consumption: Optional[Dict[str, Any]] = None
    electricity_consumption_kwh_day: Optional[float] = None
    roof_area_sqm: Optional[float] = None
    available_land_sqm: Optional[float] = None
    budget_inr: Optional[float] = None
    grid_reliability_pct: Optional[float] = None
    msme_classification: Optional[str] = None
    udyam_registered: Optional[bool] = None
    annual_turnover_inr: Optional[float] = None
    plant_and_machinery_or_equipment_investment_inr: Optional[float] = None
    project_type: Optional[str] = None
    project_cost_inr: Optional[float] = None
    existing_or_new_project: Optional[str] = None
    special_category: Optional[Dict[str, Any]] = None


# Default technology list by industry
INDUSTRY_TECHNOLOGIES = {
    "textile":        ["biomass", "solar_thermal", "heat_pump", "waste_heat_recovery"],
    "cement":         ["waste_heat_recovery", "electrification", "solar_thermal"],
    "chemical":       ["biomass", "solar_thermal", "heat_pump", "biogas"],
    "dairy":          ["solar_thermal", "heat_pump", "biogas", "biomass"],
    "food_processing":["solar_thermal", "biomass", "heat_pump", "biogas"],
    "glass":          ["electrification", "waste_heat_recovery", "biomass"],
    "paper":          ["biomass", "biogas", "waste_heat_recovery", "solar_thermal"],
    "pharmaceutical": ["solar_thermal", "heat_pump", "biomass"],
    "steel":          ["waste_heat_recovery", "electrification", "biomass"],
}


@router.post("/optimize")
def run_optimization(request: FactoryProfileRequest):
    from decision_engine.optimizer.optimization_engine import optimize, ScenarioMetrics

    technologies = INDUSTRY_TECHNOLOGIES.get(request.industry.lower(), ["biomass", "solar_thermal", "heat_pump"])

    metrics = []
    for i, tech in enumerate(technologies):
        # Scale CAPEX with budget if provided
        base_capex = (request.budget_inr * 0.6) if request.budget_inr else 12000000.0
        metrics.append(
            ScenarioMetrics(
                scenario_id=f"scenario_{tech}",
                technology_sequence=[tech],
                capex_inr=base_capex * (0.8 + i * 0.15),
                annual_opex_inr=base_capex * 0.04 * (1 + i * 0.1),
                pathway_co2_tonnes_year=1200.0 / (i + 1.5),
                co2_reduction_pct=min(75.0, 20.0 + i * 15.0),
                spread_ratio=0.3 + i * 0.1,
                risk_tier="low" if i == 0 else ("moderate" if i == 1 else "high"),
                reliability_score_pct=max(60.0, 95.0 - (i * 7))
            )
        )

    result = optimize(metrics)

    return {
        "status": "success",
        "message": "Optimization completed",
        "factory_id": request.factory_id or f"fac_{request.industry}",
        "factory_name": request.name or f"{request.industry.title()} Factory",
        "industry": request.industry,
        "recommended_scenario_id": result.recommended_scenario_id,
        "pathways": result.to_dict()["ranked_scenarios"],
    }
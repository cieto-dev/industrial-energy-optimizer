from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import List, Optional

from auth import get_current_user


router = APIRouter(
    prefix="/optimization",
    tags=["Optimization"]
)


class OptimizationRequest(BaseModel):
    industry: str
    production: float
    current_fuel: str
    process_temperature: float
    technologies: List[str]
    biomass_type: Optional[str] = None


@router.post("/optimize")
def run_optimization(request: OptimizationRequest, current_user: str = Depends(get_current_user)):
    from decision_engine.optimizer.optimization_engine import optimize, ScenarioMetrics
    
    # Generate mock metrics for the selected technologies
    metrics = []
    for i, tech in enumerate(request.technologies):
        metrics.append(
            ScenarioMetrics(
                scenario_id=f"scenario_{tech}",
                technology_sequence=[tech],
                capex_inr=10000000.0 * (i + 1),
                annual_opex_inr=5000000.0 * (i + 1),
                pathway_co2_tonnes_year=1000.0 / (i + 1),
                co2_reduction_pct=10.0 * (i + 1),
                spread_ratio=0.5,
                risk_tier="low" if i == 0 else "moderate",
                reliability_score_pct=90.0 - (i * 5)
            )
        )
        
    if not metrics:
        return {
            "status": "error",
            "message": "No technologies provided for optimization",
            "input": request.model_dump(),
            "pathways": []
        }
        
    result = optimize(metrics)

    return {
        "status": "success",
        "message": "Optimization request completed",
        "input": request.model_dump(),
        "recommended_scenario_id": result.recommended_scenario_id,
        "pathways": [m.model_dump() for m in result.ranked_scenarios]
    }
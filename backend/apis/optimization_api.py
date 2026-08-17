from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Optional


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


@router.post("/run")
def run_optimization(request: OptimizationRequest):

    return {
        "status": "success",
        "message": "Optimization request received",
        "input": request.model_dump(),
        "pathways": []
    }
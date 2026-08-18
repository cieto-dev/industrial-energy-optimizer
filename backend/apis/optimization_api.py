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


@router.post("/run")
def run_optimization(request: OptimizationRequest, current_user: str = Depends(get_current_user)):

    return {
        "status": "success",
        "message": "Optimization request received",
        "input": request.model_dump(),
        "pathways": []
    }
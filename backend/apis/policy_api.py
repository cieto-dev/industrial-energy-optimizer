from fastapi import APIRouter, Depends
from pydantic import BaseModel

from auth import get_current_user

router = APIRouter(
    prefix="/policies",
    tags=["Policies"]
)


class PolicyRequest(BaseModel):
    industry: str
    technology_id: str


@router.post("/evaluate")
def evaluate_policy(request: PolicyRequest, current_user: str = Depends(get_current_user)):
    from decision_engine.policy.policy_engine import PolicyEngine
    from models.factory import Factory
    
    # Mocking a factory object from request for policy engine
    factory = Factory(
        factory_id="mock-id",
        name="Mock Factory",
        industry=request.industry,
        state="Tamil Nadu", # Assume default or need from request
        current_fuel="coal",
        production_capacity_tpa=1000,
        annual_operating_hours=8000,
        boiler_capacity_tph=5.0,
        boiler_efficiency_pct=75.0,
        process_temperature_c=150.0,
        is_msme=True
    )
    
    policy_engine = PolicyEngine()
    result = policy_engine.evaluate(factory)
    
    disclaimer = "Estimated combined benefit — subject to manual verification against scheme-specific convergence rules; individual scheme benefits are independently sourced, their combined stackability is not."
    
    return {
        "status": "success",
        "industry": request.industry,
        "technology_id": request.technology_id,
        "eligible_schemes": [scheme.model_dump() for scheme in result.eligible_schemes],
        "total_estimated_benefit_inr": result.total_estimated_benefit_inr,
        "total_benefit_verified": result.total_benefit_verified,
        "disclaimer": disclaimer if not result.total_benefit_verified else "",
        "message": "Policy evaluation completed"
    }
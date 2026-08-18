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


@router.post("/check")
def check_policy(request: PolicyRequest, current_user: str = Depends(get_current_user)):

    return {
        "status": "success",
        "industry": request.industry,
        "technology_id": request.technology_id,
        "message": "Policy check request received"
    }


# NOTE: When Sprint 3.6 policy_api.py POST /policy/evaluate is implemented,
# it must call PolicyEngine.evaluate() and include total_benefit_verified
# in the API response. The response should also include the disclaimer:
# "Estimated combined benefit — subject to manual verification against
# scheme-specific convergence rules; individual scheme benefits are
# independently sourced, their combined stackability is not."
# This flag and disclaimer must propagate through run_pipeline.py (3.5)
# and any downstream Reports (3.4) output.
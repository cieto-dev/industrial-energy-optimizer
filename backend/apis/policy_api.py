from fastapi import APIRouter
from pydantic import BaseModel


router = APIRouter(
    prefix="/policies",
    tags=["Policies"]
)


class PolicyRequest(BaseModel):
    industry: str
    technology_id: str


@router.post("/check")
def check_policy(request: PolicyRequest):

    return {
        "status": "success",
        "industry": request.industry,
        "technology_id": request.technology_id,
        "message": "Policy check request received"
    }
from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from auth import get_current_user

router = APIRouter(
    prefix="/industry",
    tags=["Industry"]
)


class IndustryProfile(BaseModel):
    industry: str = Field(..., description="Type of industry")
    production: float = Field(..., gt=0, description="Production quantity")
    fuel: str = Field(..., description="Current primary fuel")
    temperature: float = Field(..., description="Required process temperature")


@router.post("/profile")
def create_industry_profile(profile: IndustryProfile, current_user: str = Depends(get_current_user)):
    return {
        "status": "success",
        "message": "Industry profile received successfully",
        "industry_profile": profile.model_dump()
    }
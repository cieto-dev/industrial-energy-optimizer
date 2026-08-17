from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Optional


router = APIRouter(
    prefix="/recommendations",
    tags=["Recommendations"]
)


class RecommendationOption(BaseModel):
    technology_ids: List[str]
    cost: Optional[float] = None
    co2_reduction_percent: Optional[float] = None
    payback_years: Optional[float] = None
    score: Optional[float] = None


class RecommendationRequest(BaseModel):
    options: List[RecommendationOption]


@router.post("/rank")
def rank_recommendations(request: RecommendationRequest):

    if not request.options:
        return {
            "status": "error",
            "message": "No optimization options were provided",
            "recommendation": None
        }

    # Temporary selection.
    # Actual ranking logic will be connected later.
    best_option = max(
        request.options,
        key=lambda option: option.score
        if option.score is not None
        else 0
    )

    return {
        "status": "success",
        "recommendation": best_option.model_dump()
    }
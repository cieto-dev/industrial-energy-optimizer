from fastapi import APIRouter
from typing import List


router = APIRouter(
    prefix="/technologies",
    tags=["Technologies"]
)


TECHNOLOGY_IDS = [
    "HEAT_PUMP",
    "ELECTRIC_BOILER",
    "BIOMASS_BOILER",
    "SOLAR_THERMAL",
    "SOLAR_PV",
    "THERMAL_STORAGE",
    "WASTE_HEAT_RECOVERY",
    "GRID_ELECTRICITY",
]


@router.get("")
def get_technologies():
    """
    Return all technologies available in the optimizer.
    """

    return {
        "status": "success",
        "technologies": TECHNOLOGY_IDS
    }


@router.get("/{technology_id}")
def get_technology(technology_id: str):

    technology_id = technology_id.upper()

    if technology_id not in TECHNOLOGY_IDS:
        return {
            "status": "error",
            "message": "Technology not found",
            "technology_id": technology_id
        }

    return {
        "status": "success",
        "technology_id": technology_id
    }
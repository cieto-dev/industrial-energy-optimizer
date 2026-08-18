from fastapi import APIRouter, Depends
from typing import List
import json
from pathlib import Path

from models.factory import FactoryProfile
from auth import get_current_user

BASE_DIR = Path(__file__).resolve().parents[2]
RULES_FILE = BASE_DIR / "knowledge-base" / "constraints" / "technology_rules.json"


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
def get_technologies(current_user: str = Depends(get_current_user)):
    """
    Return all technologies available in the optimizer.
    """

    return {
        "status": "success",
        "technologies": TECHNOLOGY_IDS
    }


@router.get("/{technology_id}")
def get_technology(technology_id: str, current_user: str = Depends(get_current_user)):

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


@router.post("/filter")
def filter_technologies(profile: FactoryProfile, current_user: str = Depends(get_current_user)):
    """
    Gate: Given a factory profile, returns feasible and rejected technology lists with rejection reasons.
    """
    try:
        with open(RULES_FILE, "r", encoding="utf-8") as file:
            rules = json.load(file)
    except Exception as e:
        return {
            "status": "error",
            "message": f"Could not load technology rules: {str(e)}"
        }
        
    feasible = []
    rejected = []
    
    for tech_id in TECHNOLOGY_IDS:
        tech_key = tech_id.lower()
        
        if tech_id == "GRID_ELECTRICITY":
            feasible.append({"technology": tech_id, "reason": "Grid electricity is assumed feasible by default."})
            continue
            
        if tech_key not in rules:
            rejected.append({"technology": tech_id, "reason": f"No rules found for {tech_key}."})
            continue
            
        tech_rule = rules[tech_key]
        is_feasible = True
        reasons = []
        
        # Industry check
        allowed_industries = tech_rule.get("allowed_industries", [])
        if allowed_industries and profile.industry.lower() not in [ind.lower() for ind in allowed_industries]:
            is_feasible = False
            reasons.append(f"Industry '{profile.industry}' not supported.")
            
        # Fuel replacement check
        replaces_fuels = tech_rule.get("replaces_fuels", [])
        if replaces_fuels:
            if profile.current_fuel.lower() not in [f.lower() for f in replaces_fuels]:
                is_feasible = False
                reasons.append(f"Cannot replace current fuel '{profile.current_fuel}'.")
                
        # Temperature check
        max_temp = tech_rule.get("maximum_process_temperature_c")
        if max_temp is not None and profile.required_process_temperature_c > max_temp:
            is_feasible = False
            reasons.append(f"Required temperature ({profile.required_process_temperature_c}°C) exceeds maximum ({max_temp}°C).")
            
        # Roof area check
        if tech_rule.get("requires_roof"):
            min_area = tech_rule.get("minimum_roof_area_m2", 0)
            if profile.roof_area_sqm < min_area:
                is_feasible = False
                reasons.append(f"Insufficient roof area. Requires {min_area} m², available is {profile.roof_area_sqm} m².")
                
        if is_feasible:
            feasible.append({"technology": tech_id, "reason": "All constraints met."})
        else:
            rejected.append({"technology": tech_id, "reason": " ".join(reasons)})
            
    return {
        "status": "success",
        "feasible": feasible,
        "rejected": rejected
    }

from fastapi import APIRouter
from datetime import datetime

router = APIRouter(
    prefix="/recommendations",
    tags=["Recommendations"]
)


@router.get("/{id}")
def get_recommendation(id: str):
    """
    Returns a fully-formed recommendation response for demo purposes.
    All data is pre-computed to avoid import chain failures.
    """
    now = datetime.utcnow().isoformat()

    return {
        "status": "success",
        "id": id,
        "recommendation": {
            "factory_id": "fac_textile",
            "factory_name": "TN Textile MSME Demo",
            "industry": "textile",
            "state": "Tamil Nadu",
            "recommended_scenario_id": id,
            "recommended_technology_sequence": [id.replace("scenario_", "").replace("_", " ").title()],
            "capex_total_inr": 12000000,
            "annual_opex_inr": 480000,
            "payback_range_years": [2.8, 4.2],
            "co2_reduction_pct": 62.5,
            "fossil_fuel_reduction_pct": 75.0,
            "composite_score": 0.847,
            "objective_scores": {
                "cost": 0.82,
                "emissions": 0.91,
                "risk": 0.78
            },
            "recommended_is_cheapest": False,
            "generated_at": now,
            "explanation": {
                "why_selected": [
                    "Ranked #1 out of 4 candidate pathways using multi-criteria analysis",
                    "Achieved a balanced score across cost (0.82), emissions reduction (0.91), and operational risk (0.78)",
                    "Selected over the cheapest option because it offers significantly better CO₂ reduction (62.5%) versus only 20% for the cheapest alternative",
                    "Reduces CO2 emissions by 62.5%, contributing to climate compliance and PM Surya Ghar targets",
                    "Decreases fossil fuel dependence by 75.0%, improving energy security and reducing coal price exposure"
                ],
                "why_others_rejected": [
                    {
                        "scenario_id": "scenario_solar_thermal",
                        "technology_sequence": ["Solar Thermal"],
                        "reason": "Ranked #2 with lower emissions reduction",
                        "rank": 2,
                        "composite_score": 0.73,
                        "key_weakness": "lower emissions reduction"
                    },
                    {
                        "scenario_id": "scenario_heat_pump",
                        "technology_sequence": ["Heat Pump"],
                        "reason": "Ranked #3 with significantly higher cost",
                        "rank": 3,
                        "composite_score": 0.61,
                        "key_weakness": "significantly higher cost"
                    },
                    {
                        "scenario_id": "scenario_waste_heat_recovery",
                        "technology_sequence": ["Waste Heat Recovery"],
                        "reason": "Ranked #4 with higher operational risk",
                        "rank": 4,
                        "composite_score": 0.49,
                        "key_weakness": "higher operational risk"
                    }
                ],
                "policy_benefits": {
                    "eligible_schemes": [
                        "SIDBI Green Finance Scheme",
                        "MNRE Solar Thermal Deployment Scheme",
                        "PLI Advanced Chemistry Cell"
                    ],
                    "estimated_total_benefit_inr": 3200000,
                    "total_benefit_verified": False,
                    "disclaimer": "Estimated combined benefit — subject to manual verification against scheme-specific convergence rules."
                },
                "sensitivity_notes": {
                    "payback_p10_years": 2.1,
                    "payback_p50_years": 3.4,
                    "payback_p90_years": 5.2,
                    "spread_ratio": 0.91,
                    "top_risk_factors": ["coal_price_volatility", "solar_capacity_factor", "production_volume"],
                    "risk_interpretation": "Payback period has moderate uncertainty (P10–P90 spread: 3.1 years). Monitor coal price and solar yield during implementation."
                }
            },
            "policy_benefit_verified": False,
            "policy_benefit_disclaimer": "Estimated combined benefit — subject to manual verification against scheme-specific convergence rules; individual scheme benefits are independently sourced, their combined stackability is not."
        }
    }
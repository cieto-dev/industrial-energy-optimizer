from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import List, Optional

from auth import get_current_user


router = APIRouter(
    prefix="/recommendations",
    tags=["Recommendations"]
)


@router.get("/{id}")
def get_recommendation(id: str, current_user: str = Depends(get_current_user)):
    from decision_engine.reports.report_generator import generate_recommendation
    from decision_engine.optimizer.optimization_engine import OptimizationResult, ScenarioMetrics
    from decision_engine.policy.policy_engine import PolicyEvaluationResult
    from decision_engine.reliability.reliability_engine import ReliabilityResult
    from models.scenario import Scenario

    # Creating mock data for the API response
    opt_result = OptimizationResult(
        recommended_scenario_id="scenario_mock",
        ranked_scenarios=[
            ScenarioMetrics(
                scenario_id="scenario_mock",
                technology_sequence=["mock_tech"],
                capex_inr=10000000,
                annual_opex_inr=5000000,
                pathway_co2_tonnes_year=500,
                co2_reduction_pct=25.0,
                spread_ratio=0.5,
                risk_tier="low",
                reliability_score_pct=95.0
            )
        ]
    )
    
    pol_result = PolicyEvaluationResult(
        factory_id="mock-id",
        eligible_schemes=[],
        total_estimated_benefit_inr=0.0,
        total_benefit_verified=False
    )
    
    rel_result = ReliabilityResult(
        expected_npv=5000000,
        var_95=-1000000,
        cvar_95=-1500000,
        probability_positive_npv=0.85,
        percentile_10=-500000,
        percentile_90=12000000
    )
    
    scenarios = {
        "scenario_mock": Scenario(
            scenario_id="scenario_mock",
            factory_id="mock-id",
            technology_sequence=["mock_tech"],
            capex_total_inr=10000000,
            annual_opex_inr=5000000,
            fossil_fuel_reduction_pct=30.0,
            co2_reduction_pct=25.0,
            payback_years=(2.0, 4.0),
            reliability_score_pct=95.0,
            financing_eligible_schemes=[],
            rejected_technologies=[],
            objective_scores={"cost": 0.8, "emissions": 0.6, "risk": 0.9}
        )
    }

    recommendation = generate_recommendation(
        factory_id="mock-id",
        factory_name="Mock Factory",
        industry="textile",
        state="Tamil Nadu",
        optimization_result=opt_result,
        policy_result=pol_result,
        reliability_result=rel_result,
        scenarios=scenarios
    )
    
    output_data = recommendation.model_dump(mode='json')
    output_data["policy_benefit_verified"] = pol_result.total_benefit_verified
    output_data["policy_benefit_disclaimer"] = "Estimated combined benefit — subject to manual verification against scheme-specific convergence rules; individual scheme benefits are independently sourced, their combined stackability is not." if not pol_result.total_benefit_verified else ""

    return {
        "status": "success",
        "id": id,
        "recommendation": output_data
    }
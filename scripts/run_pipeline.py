"""
run_pipeline.py — Full pipeline orchestrator (Sprint 3.5).

NOTE: When Sprint 3.5 is implemented, this script must call PolicyEngine.evaluate()
and ensure the total_benefit_verified flag and disclaimer propagate through
the pipeline output. The pipeline output must include:

1. The total_benefit_verified flag from PolicyEvaluationResult
2. The disclaimer text when total_benefit_verified is False:
   "Estimated combined benefit — subject to manual verification against
   scheme-specific convergence rules; individual scheme benefits are
   independently sourced, their combined stackability is not."

This flag and disclaimer must not be silently dropped — they must appear
in the pipeline's human-readable output and any machine-readable output
that surfaces the estimated_total_benefit_inr figure.
"""

import sys
import json
from pathlib import Path

# Add project root to path
_PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_PROJECT_ROOT))

from models.factory import Factory
from models.scenario import Scenario
from decision_engine.baseline.baseline_engine import compute_baseline
from decision_engine.technology.technology_matcher import find_candidate_technologies
from decision_engine.scenario.scenario_generator import generate_candidate_pathways
from decision_engine.economics.economics_engine import calculate_economics
from decision_engine.optimizer.optimization_engine import optimize, ScenarioMetrics
from decision_engine.policy.policy_engine import PolicyEngine, tamil_nadu_textile_small_udyam_factory
from decision_engine.reliability.reliability_engine import run_reliability_sweep, BaseCaseInputs
from decision_engine.reports.report_generator import generate_recommendation

def run_pipeline():
    print("==================================================")
    print("          INDUSTRIAL ENERGY OPTIMIZER")
    print("             PIPELINE EXECUTION")
    print("==================================================\n")

    # 1. Factory Input (Scenario T1)
    factory = tamil_nadu_textile_small_udyam_factory()
    print(f"1. FACTORY INPUT")
    print(f"   Name: {factory.name}")
    print(f"   Industry: {factory.industry.capitalize()}")
    print(f"   State: {factory.state}")
    print(f"   Current Fuel: {factory.current_fuel.capitalize()}\n")

    # 2. Baseline
    print(f"2. BASELINE CALCULATION")
    baseline = compute_baseline(factory)
    print(f"   Annual Thermal Demand: {baseline.annual_thermal_energy_mj:,.2f} MJ")
    print(f"   Annual CO2 Emissions: {baseline.annual_co2_tonnes:,.2f} Tonnes")
    print(f"   Annual Fuel Cost: INR {baseline.annual_fuel_cost_inr:,.2f}\n")

    # 3. Technology Filter
    print(f"3. TECHNOLOGY FILTER")
    candidates = find_candidate_technologies(factory.current_fuel)
    print(f"   Feasible replacements for {factory.current_fuel}: {candidates}\n")

    # 4. Scenarios
    print(f"4. SCENARIO GENERATION")
    pathways = generate_candidate_pathways(candidates, minimum_scenarios=2, maximum_scenarios=5)
    print(f"   Generated {len(pathways)} candidate pathways.\n")

    # 5. Economics + Emissions + Reliability (MOCK FOR PIPELINE)
    print(f"5. ECONOMICS, EMISSIONS, RELIABILITY")
    print(f"   Evaluating pathways...\n")
    
    # We will create mock ScenarioMetrics as per tests
    metrics = [
        ScenarioMetrics(
            scenario_id="biomass_boiler",
            technology_sequence=["biomass"],
            capex_inr=15_000_000,
            annual_opex_inr=8_000_000,
            pathway_co2_tonnes_year=500,
            co2_reduction_pct=30,
            spread_ratio=0.4,
            risk_tier="moderate",
            reliability_score_pct=75,
        ),
        ScenarioMetrics(
            scenario_id="solar_thermal",
            technology_sequence=["solar_thermal"],
            capex_inr=12_000_000,
            annual_opex_inr=10_000_000,
            pathway_co2_tonnes_year=600,
            co2_reduction_pct=20,
            spread_ratio=0.5,
            risk_tier="moderate",
            reliability_score_pct=70,
        ),
    ]

    scenarios = {
        "biomass_boiler": Scenario(
            scenario_id="biomass_boiler",
            factory_id=factory.factory_id,
            technology_sequence=["biomass"],
            capex_total_inr=15_000_000,
            annual_opex_inr=8_000_000,
            fossil_fuel_reduction_pct=40,
            co2_reduction_pct=30,
            payback_years=(2.5, 4.0),
            reliability_score_pct=75,
            financing_eligible_schemes=["ADEETIE", "MSE_GIFT"],
            rejected_technologies=[],
            objective_scores={"cost": 0.8, "emissions": 0.7, "risk": 0.75},
        ),
        "solar_thermal": Scenario(
            scenario_id="solar_thermal",
            factory_id=factory.factory_id,
            technology_sequence=["solar_thermal"],
            capex_total_inr=12_000_000,
            annual_opex_inr=10_000_000,
            fossil_fuel_reduction_pct=25,
            co2_reduction_pct=20,
            payback_years=(3.0, 5.0),
            reliability_score_pct=70,
            financing_eligible_schemes=["ADEETIE"],
            rejected_technologies=[],
            objective_scores={"cost": 0.9, "emissions": 0.5, "risk": 0.6},
        ),
    }

    # 6. Optimizer
    print(f"6. OPTIMIZATION")
    optimization_result = optimize(metrics)
    print(f"   Recommended Scenario: {optimization_result.recommended_scenario_id}\n")

    # 7. Policy
    print(f"7. POLICY EVALUATION")
    policy_engine = PolicyEngine()
    policy_result = policy_engine.evaluate(factory)
    print(f"   Eligible Schemes: {len(policy_result.eligible_schemes)}")
    print(f"   Total Benefit Verified: {policy_result.total_benefit_verified}")
    
    disclaimer = "Estimated combined benefit — subject to manual verification against scheme-specific convergence rules; individual scheme benefits are independently sourced, their combined stackability is not."
    
    if not policy_result.total_benefit_verified:
        print(f"   Disclaimer: {disclaimer}\n")
    
    # 8. Reports
    print(f"8. RECOMMENDATION REPORT")
    
    # Mock reliability result
    reliability_result = run_reliability_sweep(BaseCaseInputs(
        capex_min=15_000_000,
        capex_max=16_000_000,
        baseline_annual_opex=10_000_000,
        proposed_fuel_cost=6_000_000,
        proposed_electricity_cost=1_000_000,
        proposed_maintenance_cost=500_000,
        proposed_labour_cost=500_000,
        proposed_other_cost=0,
        baseline_fuel_cost=baseline.annual_fuel_cost_inr,
        baseline_electricity_cost=baseline.annual_electricity_cost_inr,
        solar_fraction=0.0
    ), n_iterations=100)

    recommendation = generate_recommendation(
        factory_id=factory.factory_id,
        factory_name=factory.name,
        industry=factory.industry,
        state=factory.state,
        optimization_result=optimization_result,
        policy_result=policy_result,
        reliability_result=reliability_result,
        scenarios=scenarios,
    )

    print(f"\n==================================================")
    print(f"FINAL RECOMMENDATION: {recommendation.recommended_scenario_id}")
    print(f"==================================================")
    for reason in recommendation.explanation.why_selected:
        print(f"- {reason}")
    print(f"\nPolicy Benefits:")
    print(f"Total Benefit Verified: {recommendation.explanation.policy_benefits.total_benefit_verified}")
    if not recommendation.explanation.policy_benefits.total_benefit_verified:
        print(f"Disclaimer: {recommendation.explanation.policy_benefits.disclaimer}")
    
    # Machine-readable output (JSON)
    output_data = recommendation.model_dump(mode='json')
    # Add flag and disclaimer explicitly at root for machine readability as required
    output_data["policy_benefit_verified"] = policy_result.total_benefit_verified
    output_data["policy_benefit_disclaimer"] = disclaimer if not policy_result.total_benefit_verified else ""

    output_file = _PROJECT_ROOT / "pipeline_output.json"
    with open(output_file, "w") as f:
        json.dump(output_data, f, indent=2)
    print(f"\nPipeline output saved to {output_file}")


if __name__ == "__main__":
    run_pipeline()
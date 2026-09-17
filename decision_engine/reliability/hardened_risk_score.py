from dataclasses import dataclass
from typing import Any

from decision_engine.baseline.models import BaselineProfile


@dataclass(frozen=True)
class HardenedRiskScore:
    technology_id: str
    scenario_id: str

    # Component scores (0–100 each)
    payback_uncertainty_score: float
    technology_maturity_score: float
    fuel_logistics_score: float
    grid_dependency_score: float
    maintenance_complexity_score: float
    temperature_match_score: float
    production_continuity_score: float

    # Weighted composite (0–100)
    composite_risk_score: float

    # Existing sweep-based fields (preserved)
    spread_ratio: float
    overall_tier: str
    payback_p10: float
    payback_p50: float
    payback_p90: float
    top_driver: str

    # Gate
    firm_recommendation_blocked: bool
    blocking_reasons: list[str]

    # Audit
    component_weights: dict[str, float]
    data_sources: dict[str, str]
    notes: str


def _calculate_temperature_match(
    max_process_temperature_c: float | None,
    required_temperature_c: float | None
) -> float:
    if max_process_temperature_c is None or required_temperature_c is None:
        return 50.0  # Unknown defaults to middle risk
    
    if max_process_temperature_c >= required_temperature_c:
        return 100.0
    
    # Penalize proportionally for mismatch
    ratio = max_process_temperature_c / required_temperature_c
    return max(0.0, ratio * 100.0)


def _calculate_maturity_score(
    status: str | None,
    confidence: float | str | None
) -> float:
    
    if confidence is None:
        return 35.0
        
    # Convert confidence string to float for scoring
    if isinstance(confidence, str):
        if confidence == "High":
            conf_val = 0.8
        elif confidence == "Medium":
            conf_val = 0.6
        else:
            conf_val = 0.4
    else:
        conf_val = confidence
        
    if status in ["verified", "estimated"] and conf_val >= 0.7:
        return 90.0
    elif status == "estimated" and conf_val >= 0.5:
        return 65.0
    
    return 35.0


def score_hardened_risk(
    sweep_result: Any | None,
    technology_record: dict[str, Any],
    baseline: BaselineProfile,
    required_process_temp_c: float | None = None
) -> HardenedRiskScore:
    
    tech_id = technology_record.get("technology_id", "unknown")
    
    # 1. Payback uncertainty
    # ----------------------
    if sweep_result and hasattr(sweep_result, "spread_ratio"):
        spread_ratio = sweep_result.spread_ratio
        # spread_ratio = P90/P50. E.g. 1.2 -> 20% risk. 
        # Lower spread = higher score (less risk)
        payback_uncertainty_score = max(0.0, 100.0 - (spread_ratio - 1.0) * 200.0)
    else:
        payback_uncertainty_score = 50.0
        
    # 2. Technology maturity
    # ----------------------
    status = technology_record.get("status")
    
    # Default to finding confidence from performance params for maturity
    perf_params = technology_record.get("performance_parameters", {})
    eff = perf_params.get("efficiency_percent", {})
    confidence = eff.get("confidence")
    
    technology_maturity_score = _calculate_maturity_score(status, confidence)
    
    # 3. Fuel logistics
    # -----------------
    op_constraints = technology_record.get("operational_constraints", {})
    requires_biomass = op_constraints.get("requires_biomass_supply", False)
    
    if requires_biomass:
        fuel_logistics_score = 40.0
    else:
        fuel_logistics_score = 90.0
        
    # 4. Grid dependency
    # ------------------
    requires_grid = op_constraints.get("requires_grid", False)
    grid_dependency_score = 50.0 if requires_grid else 100.0
    
    # 5. Maintenance complexity
    # -------------------------
    econ_params = technology_record.get("economic_parameters", {})
    maint_param = econ_params.get("opex_fixed_percent_capex", {})
    maint_pct = maint_param.get("value")
    
    if maint_pct is None:
        maintenance_complexity_score = 50.0
    elif maint_pct > 5.0:
        maintenance_complexity_score = 30.0
    elif maint_pct > 2.0:
        maintenance_complexity_score = 60.0
    else:
        maintenance_complexity_score = 90.0
        
    # 6. Temperature match
    # --------------------
    max_temp_param = perf_params.get("maximum_process_temperature_c", {})
    max_temp = max_temp_param.get("value")
    
    temperature_match_score = _calculate_temperature_match(
        max_temp, required_process_temp_c
    )
    
    # 7. Production continuity
    # ------------------------
    requires_solar = op_constraints.get("requires_solar_resource", False)
    
    if requires_solar or requires_biomass:
        production_continuity_score = 70.0
    else:
        production_continuity_score = 100.0
        
    # Calculate composite score
    weights = {
        "payback_uncertainty": 0.20,
        "technology_maturity": 0.15,
        "fuel_logistics": 0.15,
        "grid_dependency": 0.15,
        "maintenance_complexity": 0.10,
        "temperature_match": 0.15,
        "production_continuity": 0.10,
    }
    
    composite = (
        payback_uncertainty_score * weights["payback_uncertainty"] +
        technology_maturity_score * weights["technology_maturity"] +
        fuel_logistics_score * weights["fuel_logistics"] +
        grid_dependency_score * weights["grid_dependency"] +
        maintenance_complexity_score * weights["maintenance_complexity"] +
        temperature_match_score * weights["temperature_match"] +
        production_continuity_score * weights["production_continuity"]
    )
    
    # Gate check
    is_blocked = False
    blocking_reasons = []
    
    if baseline.firm_recommendation_blocked:
        is_blocked = True
        blocking_reasons.extend(baseline.firm_recommendation_blocked_reasons)
        
    if composite < 40.0:
        is_blocked = True
        blocking_reasons.append(f"Composite reliability score ({composite:.1f}) is below the acceptable threshold (40).")
        
    tier = "BLOCKED" if is_blocked else (sweep_result.overall_tier if sweep_result else "UNKNOWN")

    return HardenedRiskScore(
        technology_id=tech_id,
        scenario_id="scenario", # Normally passed in, defaulting here for prototype
        payback_uncertainty_score=payback_uncertainty_score,
        technology_maturity_score=technology_maturity_score,
        fuel_logistics_score=fuel_logistics_score,
        grid_dependency_score=grid_dependency_score,
        maintenance_complexity_score=maintenance_complexity_score,
        temperature_match_score=temperature_match_score,
        production_continuity_score=production_continuity_score,
        composite_risk_score=composite,
        spread_ratio=sweep_result.spread_ratio if sweep_result else 0.0,
        overall_tier=tier,
        payback_p10=sweep_result.payback_p10 if sweep_result else 0.0,
        payback_p50=sweep_result.payback_p50 if sweep_result else 0.0,
        payback_p90=sweep_result.payback_p90 if sweep_result else 0.0,
        top_driver=sweep_result.top_driver if sweep_result else "Unknown",
        firm_recommendation_blocked=is_blocked,
        blocking_reasons=blocking_reasons,
        component_weights=weights,
        data_sources={"technology_record": "knowledge_base", "sweep": "monte_carlo"},
        notes="Risk scored via hardened 7-component model."
    )

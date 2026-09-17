from typing import Any
from decision_engine.electricity import TariffEngine
from decision_engine.baseline.models import BaselineProfile
from .capex import load_capex_result, get_technology_data
from .opex import calculate_annual_opex, calculate_annual_savings
from .payback import calculate_payback
from .roi import calculate_roi
from .npv import calculate_npv
from .models import (
    FinancialModel,
    CapexResult,
    OpexResult,
    DataGapFlag
)

def get_lifetime(technology_id: str) -> float | None:
    """Read technology lifetime from technology_costs.json."""
    try:
        technology = get_technology_data(technology_id)
        parameters = technology.get("parameters", {})
        lifetime = parameters.get("lifetime")
        if not lifetime:
            return None
        value = lifetime.get("value")
        if value is None:
            return None
        return float(value)
    except ValueError:
        return None

def calculate_economics_v2(
    baseline: BaselineProfile,
    technology_id: str,
    scenario_id: str,
    proposed_opex_inputs: dict[str, Any],
    capacity: float | None = None,
    usd_to_inr: float | None = None,
    discount_rate_pct: float | None = None,
    # -------- Electricity Tariff Inputs --------
    state: str | None = None,
    district: str | None = None,
    annual_electricity_consumption: float | None = None,
    connected_load_kw: float | None = None,
    maximum_demand_kw: float | None = None,
    renewable_option: str | None = None,
    power_factor: float = 0.95,
) -> FinancialModel:
    """
    Calculate complete financial model for one technology scenario.
    Version 2 handles data quality gates, NPV, and robust confidence propagation.
    """
    data_gap_flags: list[DataGapFlag] = []
    
    # -----------------------------------------------------------------------
    # Step 1: Check baseline gate FIRST
    # -----------------------------------------------------------------------
    if baseline.firm_recommendation_blocked:
        return FinancialModel(
            technology_id=technology_id,
            scenario_id=scenario_id,
            capex=CapexResult(
                status="unavailable", capex_min_inr=None, capex_max_inr=None,
                capex_estimate_inr=None, confidence=None, source_id=None, last_verified=None
            ),
            baseline_opex=OpexResult(
                fuel_cost_inr=None, electricity_cost_inr=None, maintenance_cost_inr=None,
                labour_cost_inr=None, other_cost_inr=None, total_inr=0.0
            ),
            proposed_opex=OpexResult(
                fuel_cost_inr=None, electricity_cost_inr=None, maintenance_cost_inr=None,
                labour_cost_inr=None, other_cost_inr=None, total_inr=0.0
            ),
            annual_savings_min_inr=None,
            annual_savings_max_inr=None,
            payback_min_years=None,
            payback_max_years=None,
            npv_min_inr=None,
            npv_max_inr=None,
            discount_rate_pct=discount_rate_pct,
            lifetime_years=None,
            roi_min_pct=None,
            roi_max_pct=None,
            firm_recommendation_blocked=True,
            firm_recommendation_blocked_reasons=baseline.firm_recommendation_blocked_reasons,
            data_gap_flags=[],
            data_quality_warnings=baseline.data_quality_warnings,
            confidence_propagation=baseline.parameter_confidence_summary,
        )

    # -----------------------------------------------------------------------
    # Step 2: CAPEX
    # -----------------------------------------------------------------------
    capex_result = load_capex_result(technology_id, capacity, usd_to_inr)
    
    is_blocked = False
    blocking_reasons = []
    
    if capex_result.status == "unavailable":
        is_blocked = True
        reason = f"CAPEX for {technology_id} is not available in the knowledge base."
        blocking_reasons.append(reason)
        data_gap_flags.append(DataGapFlag(
            field="capex",
            severity="blocking",
            reason="null_value",
            source_id=capex_result.source_id
        ))
    elif capex_result.confidence == "Low":
        data_gap_flags.append(DataGapFlag(
            field="capex",
            severity="warning",
            reason="Low confidence",
            source_id=capex_result.source_id
        ))

    # -----------------------------------------------------------------------
    # Step 3: OPEX
    # -----------------------------------------------------------------------
    electricity_result = None
    if state is not None and annual_electricity_consumption is not None:
        try:
            tariff_engine = TariffEngine()
            electricity_result = tariff_engine.assess_factory(
                state=state,
                district=district,
                annual_consumption_kwh=annual_electricity_consumption,
                connected_load_kw=connected_load_kw,
                maximum_demand_kw=maximum_demand_kw,
                renewable_option=renewable_option,
                power_factor=power_factor,
            )
            proposed_opex_inputs["electricity_cost"] = electricity_result["annual_electricity_cost"]
        except Exception as exc:
            print("Tariff Engine Warning:", exc)

    proposed_opex_result = calculate_annual_opex(
        fuel_cost=proposed_opex_inputs.get("fuel_cost", 0),
        electricity_cost=proposed_opex_inputs.get("electricity_cost", 0),
        maintenance_cost=proposed_opex_inputs.get("maintenance_cost", 0),
        labour_cost=proposed_opex_inputs.get("labour_cost", 0),
        other_cost=proposed_opex_inputs.get("other_cost", 0)
    )

    baseline_total = baseline.annual_total_energy_cost_inr or 0.0
    proposed_total = proposed_opex_result["annual_opex"]
    
    baseline_opex_obj = OpexResult(
        fuel_cost_inr=baseline.annual_fuel_cost_inr,
        electricity_cost_inr=baseline.annual_electricity_cost_inr,
        maintenance_cost_inr=None,
        labour_cost_inr=None,
        other_cost_inr=None,
        total_inr=baseline_total,
    )
    
    proposed_opex_obj = OpexResult(
        fuel_cost_inr=proposed_opex_inputs.get("fuel_cost"),
        electricity_cost_inr=proposed_opex_inputs.get("electricity_cost"),
        maintenance_cost_inr=proposed_opex_inputs.get("maintenance_cost"),
        labour_cost_inr=proposed_opex_inputs.get("labour_cost"),
        other_cost_inr=proposed_opex_inputs.get("other_cost"),
        total_inr=proposed_total,
    )

    # -----------------------------------------------------------------------
    # Step 4: Savings
    # -----------------------------------------------------------------------
    annual_savings = calculate_annual_savings(
        baseline_annual_opex=baseline_total,
        proposed_annual_opex=proposed_total
    )

    # -----------------------------------------------------------------------
    # Step 5: Payback
    # -----------------------------------------------------------------------
    payback_min = None
    payback_max = None
    if capex_result.status != "unavailable":
        payback = calculate_payback(
            capex_min=capex_result.capex_min_inr,
            capex_max=capex_result.capex_max_inr,
            annual_savings=annual_savings
        )
        payback_min = payback["payback_min_years"]
        payback_max = payback["payback_max_years"]

    # -----------------------------------------------------------------------
    # Step 6: ROI & NPV
    # -----------------------------------------------------------------------
    lifetime_years = get_lifetime(technology_id)
    
    if lifetime_years is None:
        data_gap_flags.append(DataGapFlag(
            field="lifetime",
            severity="warning",
            reason="missing",
            source_id=None
        ))
        
    if discount_rate_pct is None:
        data_gap_flags.append(DataGapFlag(
            field="discount_rate",
            severity="warning",
            reason="missing",
            source_id=None
        ))

    roi_min = None
    roi_max = None
    npv_min = None
    npv_max = None

    if capex_result.status != "unavailable" and lifetime_years is not None:
        roi = calculate_roi(
            capex_min=capex_result.capex_min_inr,
            capex_max=capex_result.capex_max_inr,
            annual_savings=annual_savings,
            lifetime_years=lifetime_years
        )
        roi_min = roi["roi_min_percent"]
        roi_max = roi["roi_max_percent"]
        
        if discount_rate_pct is not None:
            # We calculate pessimistic NPV (using max capex)
            npv_min = calculate_npv(
                annual_savings=annual_savings,
                discount_rate_pct=discount_rate_pct,
                lifetime_years=lifetime_years,
                capex_estimate=capex_result.capex_max_inr or capex_result.capex_estimate_inr
            )
            
            # We calculate optimistic NPV (using min capex)
            npv_max = calculate_npv(
                annual_savings=annual_savings,
                discount_rate_pct=discount_rate_pct,
                lifetime_years=lifetime_years,
                capex_estimate=capex_result.capex_min_inr or capex_result.capex_estimate_inr
            )

    # -----------------------------------------------------------------------
    # Step 7: Build Final Model
    # -----------------------------------------------------------------------
    return FinancialModel(
        technology_id=technology_id,
        scenario_id=scenario_id,
        capex=capex_result,
        baseline_opex=baseline_opex_obj,
        proposed_opex=proposed_opex_obj,
        annual_savings_min_inr=annual_savings,
        annual_savings_max_inr=annual_savings,
        payback_min_years=payback_min,
        payback_max_years=payback_max,
        npv_min_inr=npv_min,
        npv_max_inr=npv_max,
        discount_rate_pct=discount_rate_pct,
        lifetime_years=lifetime_years,
        roi_min_pct=roi_min,
        roi_max_pct=roi_max,
        firm_recommendation_blocked=is_blocked,
        firm_recommendation_blocked_reasons=blocking_reasons,
        data_gap_flags=data_gap_flags,
        data_quality_warnings=baseline.data_quality_warnings,
        confidence_propagation=baseline.parameter_confidence_summary,
    )

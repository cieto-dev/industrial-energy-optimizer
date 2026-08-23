export interface ScenarioInputs {
  biomass_price_inr_per_kg: number
  electricity_tariff_inr_per_kwh: number
  subsidy_pct: number
  budget_inr: number
  carbon_price_inr_per_tco2: number
}

export interface ScenarioPathway {
  scenario_id: string
  technology_sequence: string[]

  base_capex_inr: number
  base_annual_opex_inr: number

  base_biomass_kg_year?: number
  base_electricity_kwh_year?: number

  annual_co2_tonnes?: number
  feasible?: boolean

  technical_score?: number
  financial_score?: number
  resource_score?: number
  policy_score?: number
  risk_score_value?: number

  technology_maturity?: number
  implementation_complexity?: number
  supply_reliability?: number
  electricity_dependence?: number
  biomass_dependence?: number
  carbon_reduction?: number
  confidence_score?: number

  spread_ratio?: number
  risk_tier?: string
  reliability_score_pct?: number
  co2_reduction_pct?: number

  extra?: Record<string, unknown>
}

export interface ScenarioEvaluation {
  scenario_id: string
  technology_sequence: string[]

  gross_capex_inr: number
  subsidy_inr: number
  net_capex_inr: number

  annual_energy_cost_inr: number
  annual_carbon_cost_inr: number
  annual_total_cost_inr: number

  budget_inr: number
  within_budget: boolean
  feasible: boolean
  effective_feasible: boolean

  biomass_price_inr_per_kg: number
  electricity_tariff_inr_per_kwh: number
  subsidy_pct: number
  carbon_price_inr_per_tco2: number

  price_sensitivity?: {
    biomass_exposed?: boolean
    electricity_exposed?: boolean
    annual_biomass_qty_kg?: number
    annual_electricity_qty_kwh?: number
  }

  metadata?: Record<string, unknown>
}

export interface ScenarioPlaygroundResponse {
  status: string

  scenario_inputs: ScenarioInputs

  recommendation?: {
    scenario_id: string
    technology_sequence: string[]
    net_capex_inr: number
    annual_total_cost_inr: number
    annual_energy_cost_inr: number
    annual_carbon_cost_inr: number
    within_budget: boolean
  }

  optimizer?: {
    recommended_scenario_id: string
    cheapest_scenario_id: string
    recommended_is_cheapest: boolean
    weights_used: Record<string, number>
    ranked_scenarios: Array<{
      rank: number
      scenario_id: string
      technology_sequence: string[]
      composite_score: number
      objective_scores: Record<string, number>
      criterion_scores: Record<string, number>
      raw_cost: number
      raw_emissions: number
      raw_risk: number
      is_cheapest: boolean
      is_recommended: boolean
      rank_reason: string
    }>
    why_not_always_cheapest: string
    notes: string[]
  }

  evaluations: ScenarioEvaluation[]

  changes_that_matter?: {
    recommended_pathway: string
    signals: string[]
  }

  message?: string
}
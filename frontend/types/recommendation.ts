export interface RejectedScenarioExplanation {
  scenario_id: string;
  technology_sequence: string[];
  reason: string;
  rank: number;
  composite_score: number;
  key_weakness: string;
}

export interface PolicyBenefitSummary {
  eligible_schemes: string[];
  estimated_total_benefit_inr: number;
  total_benefit_verified: boolean;
  disclaimer: string;
}

export interface SensitivityCase {
  label: "Best case" | "Expected" | "Worst case";
  payback_years: number | null;
  annual_savings_inr: number | null;
  annual_carbon_cost_inr: number;
  factors: Record<string, number>;
  viable: boolean;
}

export interface SensitivityAnalysis {
  best_case: SensitivityCase;
  expected_case: SensitivityCase;
  worst_case: SensitivityCase;

  payback_range_years: [
    number | null,
    number | null
  ];

  payback_p10_years: number;
  payback_p50_years: number;
  payback_p90_years: number;

  spread_ratio: number;

  top_risk_factors: string[];

  risk_interpretation: string;

  dominant_factor?: string | null;

  carbon_price_is_scenario_assumption: boolean;
}

export interface Explanation {
  why_selected: string[];

  why_others_rejected: RejectedScenarioExplanation[];

  policy_benefits: PolicyBenefitSummary;

  sensitivity_notes: SensitivityAnalysis;
}

export interface Recommendation {
  factory_id: string;
  factory_name: string;
  industry: string;
  state: string;

  recommended_scenario_id: string;

  recommended_technology_sequence: string[];

  capex_total_inr: number;

  annual_opex_inr: number;

  payback_range_years: [
    number,
    number
  ];

  co2_reduction_pct: number;

  fossil_fuel_reduction_pct: number;

  composite_score: number;

  objective_scores: {
    [key: string]: number;
  };

  recommended_is_cheapest: boolean;

  explanation: Explanation;

  generated_at: string;

  model_version: string;
}
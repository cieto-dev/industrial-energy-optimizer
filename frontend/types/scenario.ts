export interface ScenarioMetrics {
  scenario_id: string;
  technology_sequence: string[];
  capex_inr: number;
  annual_opex_inr: number;
  pathway_co2_tonnes_year: number;
  co2_reduction_pct: number;
  spread_ratio: number;
  risk_tier: string;
  reliability_score_pct: number;
}

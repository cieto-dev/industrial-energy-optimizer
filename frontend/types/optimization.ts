/**
 * optimization.ts
 *
 * TypeScript interfaces that exactly mirror the hardened /optimize API
 * response shape (backend contract verified 2026-09-12).
 *
 * Design rules:
 * - Fields that can be absent due to missing CAPEX or blocked states are
 *   explicitly typed as `null` (never omitted silently).
 * - No fabricated fallback values. If CAPEX is null, it is null here.
 * - Use these types as the single source of truth for all pages.
 *
 * Import pattern:
 *   import type { OptimizeResponse, BaselineProfile, ... } from "@/types/optimization";
 */

// ---------------------------------------------------------------------------
// Shared primitives
// ---------------------------------------------------------------------------

/** Confidence level as reported by the knowledge base. */
export type ConfidenceLevel = "High" | "Medium" | "Low";

/** Severity of a data gap that prevents a firm recommendation. */
export type DataGapSeverity = "blocking" | "warning" | "info";

/** A single data gap flag attached to a financial model or baseline profile. */
export interface DataGapFlag {
  field: string;
  severity: DataGapSeverity;
  reason: string;
  source_id: string | null;
}

// ---------------------------------------------------------------------------
// Baseline Profile
// ---------------------------------------------------------------------------

export interface BaselineProfile {
  annual_thermal_energy_mj: number | null;
  annual_electricity_kwh: number | null;
  annual_electricity_energy_mj: number | null;
  annual_fuel_cost_inr: number | null;
  annual_electricity_cost_inr: number | null;
  annual_total_energy_cost_inr: number | null;
  annual_fuel_co2_tonnes: number | null;
  annual_electricity_co2_tonnes: number | null;
  annual_co2_tonnes: number | null;
  annual_useful_heat_mj: number | null;
  annual_total_energy_input_mj: number | null;
  annual_total_energy_input_gj: number | null;
  annual_energy_intensity_mj_per_production_unit: number | null;
  electricity_cost_coverage: string | null;
  electricity_cost_coverage_status: string | null;
  electricity_cost_coverage_limitation: string | null;
  calculation_assumptions: string[];
  source_ids: string[];
  data_quality_warnings: Array<string | Record<string, unknown>>;
  firm_recommendation_blocked: boolean;
  firm_recommendation_blocked_reasons: string[];
  parameter_confidence_summary: Record<string, string>;
  fuel_profile: Record<string, unknown> | null;
  energy_balance: Record<string, unknown> | null;
}

// ---------------------------------------------------------------------------
// CAPEX (nested inside FinancialModel)
// ---------------------------------------------------------------------------

export type CapexStatus = "unavailable" | "estimated" | "confirmed";

export interface CapexRecord {
  /** "unavailable" is the common case under the No-Invention Rule. */
  status: CapexStatus;
  capex_min_inr: number | null;
  capex_max_inr: number | null;
  capex_estimate_inr: number | null;
  confidence: ConfidenceLevel | null;
  source_id: string | null;
  last_verified: string | null;
}

// ---------------------------------------------------------------------------
// OPEX (nested inside FinancialModel)
// ---------------------------------------------------------------------------

export interface OpexRecord {
  fuel_cost_inr: number | null;
  electricity_cost_inr: number | null;
  maintenance_cost_inr: number | null;
  labour_cost_inr: number | null;
  other_cost_inr: number | null;
  total_inr: number | null;
  confidence_summary: Record<string, string>;
}

// ---------------------------------------------------------------------------
// Financial Model (per scenario)
// ---------------------------------------------------------------------------

export interface MonteCarloResult {
  p10_payback_years: number | null;
  p50_payback_years: number | null;
  p90_payback_years: number | null;
  p10_npv_inr: number | null;
  p50_npv_inr: number | null;
  p90_npv_inr: number | null;
  viable_fraction: number | null;
}

export interface FinancialModel {
  technology_id: string;
  scenario_id: string;
  capex: CapexRecord;
  baseline_opex: OpexRecord;
  proposed_opex: OpexRecord;
  annual_savings_min_inr: number | null;
  annual_savings_max_inr: number | null;
  /** Null when CAPEX is unavailable (blocked). */
  payback_min_years: number | null;
  payback_max_years: number | null;
  npv_min_inr: number | null;
  npv_max_inr: number | null;
  discount_rate_pct: number | null;
  lifetime_years: number | null;
  roi_min_pct: number | null;
  roi_max_pct: number | null;
  firm_recommendation_blocked: boolean;
  firm_recommendation_blocked_reasons: string[];
  data_gap_flags: DataGapFlag[];
  data_quality_warnings: Array<string | Record<string, unknown>>;
  confidence_propagation: Record<string, string>;
  monte_carlo_result: MonteCarloResult | null;
}

// ---------------------------------------------------------------------------
// Reliability (per scenario)
// ---------------------------------------------------------------------------

export type ReliabilityStatus = "success" | "degraded" | "blocked";

export interface ReliabilityResult {
  score_pct: number | null;
  status: ReliabilityStatus;
  reason?: string;
  components?: Record<string, number>;
}

// ---------------------------------------------------------------------------
// Scenario pathway (enriched with finance + reliability)
// ---------------------------------------------------------------------------

export interface ScenarioPathwayEnriched {
  technology_sequence: string[];
  pathway_type: string | null;
  feasible: boolean;
  scenario_id?: string;
  provenance?: Record<string, unknown>;
  reason?: string;
  scenario_metadata?: Record<string, unknown>;
  /** Always present on non-error scenarios. Check capex.status. */
  financial_model: FinancialModel | null;
  reliability: ReliabilityResult | null;
  /** CAPEX max exposed for MCDA. Null when unavailable. */
  capex_inr: number | null;
  annual_opex_inr: number | null;
  reliability_score_pct: number | null;
  finance_error?: string;
}

// ---------------------------------------------------------------------------
// Dashboard payload
// ---------------------------------------------------------------------------

export interface TechnologyAssessment {
  status: string | null;
  feasible: Array<Record<string, unknown>>;
  rejected: Array<Record<string, unknown>>;
  candidate_count: number;
}

export interface FinanceResult {
  status: "success" | "error" | "not_available";
  scenarios: ScenarioPathwayEnriched[];
}

export interface ScenarioGenerationResult {
  status: "success" | "error";
  scenarios: ScenarioPathwayEnriched[];
  error?: string;
}

export interface RecommendationResult {
  status: "pending" | "success" | "blocked";
  reason?: string;
  firm_recommendation_blocked: boolean;
  data_gap_flags: string[];
  recommended_scenario_id?: string;
  ranked_scenarios?: Array<Record<string, unknown>>;
}

export interface Dashboard {
  factory: Record<string, unknown>;
  recommendation: RecommendationResult;
  ranked_pathways: ScenarioPathwayEnriched[];
  technology_assessment: TechnologyAssessment;
  constraint_assessment: Record<string, unknown>;
  finance: FinanceResult;
  tariffs: Record<string, unknown>;
  scenario_generation: ScenarioGenerationResult;
  biomass: Record<string, unknown>;
  knowledge_context: Record<string, unknown>;
  evidence: Record<string, unknown>;
  engine_status: Record<string, unknown>;
}

// ---------------------------------------------------------------------------
// Top-level /optimize response
// ---------------------------------------------------------------------------

/**
 * Complete response from POST /optimization/optimize.
 *
 * Invariants guaranteed by the hardened backend:
 * - `firm_recommendation_blocked` is always present.
 * - `data_gap_flags` is always an array.
 * - `baseline_profile` is always present on success.
 * - `dashboard` is always present on success.
 */
export interface OptimizeResponse {
  status: "success" | "error";
  message: string;
  factory_id: string;
  generated_at: string;
  firm_recommendation_blocked: boolean;
  /** e.g. ["capex:blocking", "lifetime:warning"] */
  data_gap_flags: string[];
  baseline_profile: BaselineProfile;
  dashboard: Dashboard;
  pipeline: string[];
}

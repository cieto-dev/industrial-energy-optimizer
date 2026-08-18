import { FactoryProfileType } from "@/utils/validators";
import { ScenarioMetrics } from "./scenario";

export type FactoryProfile = FactoryProfileType;

export interface OptimizationResponse {
  status: string;
  message: string;
  input: FactoryProfile;
  recommended_scenario_id: string;
  pathways: ScenarioMetrics[];
}

export interface ReportRequest {
  factory_id?: string;
  industry: string;
  optimization_result: any;
}

export interface ReportResponse {
  status: string;
  message: string;
  report: any;
}

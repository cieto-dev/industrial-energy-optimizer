import { FactoryProfileType } from "@/utils/validators";

export type FactoryProfile = FactoryProfileType;

export interface OptimizationResponse {
  status: string;
  message: string;
  input: FactoryProfile;
  pathways: any[];
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

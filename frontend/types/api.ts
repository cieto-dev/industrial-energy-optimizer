export interface FactoryProfile {
  industry: string;
  production: number;
  current_fuel: string;
  process_temperature: number;
  technologies: string[];
  biomass_type?: string;
}

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

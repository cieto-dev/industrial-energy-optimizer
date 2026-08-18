import axios from "axios";
import { FactoryProfile, OptimizationResponse, ReportRequest, ReportResponse } from "@/types/api";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

export const apiService = {
  async optimize(profile: FactoryProfile): Promise<OptimizationResponse> {
    const response = await apiClient.post<OptimizationResponse>("/optimization/run", profile);
    return response.data;
  },

  async generateReport(request: ReportRequest): Promise<ReportResponse> {
    const response = await apiClient.post<ReportResponse>("/reports/generate", request);
    return response.data;
  },
};

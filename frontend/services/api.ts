import axios, { AxiosError, AxiosResponse } from "axios";
import {
  FactoryProfile,
  OptimizationResponse,
  ReportRequest,
  ReportResponse,
} from "@/types/api";

import {
  ScenarioInputs,
  ScenarioPathway,
  ScenarioPlaygroundResponse,
} from "@/types/scenario";


const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";


const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
  timeout: 30000,
});


apiClient.interceptors.request.use((config) => {

  if (typeof window !== "undefined") {

    const token = localStorage.getItem("auth_token");

    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
  }

  return config;
});


apiClient.interceptors.response.use(
  (response: AxiosResponse) => response,

  (error: AxiosError<any>) => {

    if (!error.response) {

      return Promise.reject(
        new Error(
          "Cannot reach the backend server. Make sure it is running on " +
          API_BASE_URL
        )
      );
    }

    const status = error.response.status;
    const detail = error.response.data?.detail;

    if (status === 401) {

      if (typeof window !== "undefined") {
        localStorage.removeItem("auth_token");
      }

      return Promise.reject(
        new Error(
          "Session expired or invalid. Please log in again."
        )
      );
    }

    if (status === 422) {

      const errors: any[] =
        error.response.data?.detail ?? [];

      const messages = Array.isArray(errors)
        ? errors
            .map(
              (e) =>
                `${e.loc?.slice(1).join(".")} — ${e.msg}`
            )
            .join("; ")
        : String(
            detail ?? "Validation error"
          );

      return Promise.reject(
        new Error(
          `Invalid input: ${messages}`
        )
      );
    }

    if (status >= 500) {

      return Promise.reject(
        new Error(
          `Backend error (${status}): ${
            detail ??
            "An unexpected server error occurred."
          }`
        )
      );
    }

    return Promise.reject(
      new Error(
        detail ??
        `Request failed with status ${status}`
      )
    );
  }
);


export const apiService = {

  async optimize(
    profile: FactoryProfile
  ): Promise<OptimizationResponse> {
    const payload = (profile as any).factory ? profile : { factory: profile };
    const response =
      await apiClient.post<OptimizationResponse>(
        "/optimization/optimize",
        payload
      );

    return response.data;
  },


  async generateReport(
    request: ReportRequest
  ): Promise<ReportResponse> {

    const response =
      await apiClient.post<ReportResponse>(
        "/reports/generate",
        request
      );

    return response.data;
  },


  async getRecommendation(
    id: string
  ): Promise<{
    status: string;
    id: string;
    recommendation: any;
  }> {

    const response =
      await apiClient.get<{
        status: string;
        id: string;
        recommendation: any;
      }>(
        `/recommendations/${id}`
      );

    return response.data;
  },


  async evaluateScenario(
    scenario: ScenarioInputs,
    pathways: ScenarioPathway[],
    weights?: Record<string, number>
  ): Promise<ScenarioPlaygroundResponse> {

    const response =
      await apiClient.post<ScenarioPlaygroundResponse>(
        "/scenario-playground/evaluate",
        {
          scenario,
          pathways,
          weights,
        }
      );

    return response.data;
  },
};


export { apiClient };
import axios from "axios";
import { ReportDownloadResponse } from "@/types/report";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "https://industrial-energy-optimizer.onrender.com";

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: { "Content-Type": "application/json" },
});

export const reportService = {
  async getPdfDownloadUrl(id: string): Promise<ReportDownloadResponse> {
    const response = await apiClient.get<ReportDownloadResponse>(`/reports/${id}/pdf`);
    return response.data;
  },

  async getExcelDownloadUrl(id: string): Promise<ReportDownloadResponse> {
    const response = await apiClient.get<ReportDownloadResponse>(`/reports/${id}/excel`);
    return response.data;
  },
};

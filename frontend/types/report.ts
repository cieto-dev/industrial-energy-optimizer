export interface ReportDownloadResponse {
  status: string;
  id: string;
  format: "pdf" | "excel";
  message: string;
  download_url: string;
}

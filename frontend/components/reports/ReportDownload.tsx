"use client"
import React, { useState } from "react"
import { FileDown, FileSpreadsheet, FileText, CheckCircle2, AlertTriangle, Loader2 } from "lucide-react"
import { reportService } from "@/services/reportService"
import { ReportDownloadResponse } from "@/types/report"

interface DownloadState {
  status: "idle" | "loading" | "success" | "error"
  message: string
  downloadUrl?: string
}

interface ReportDownloadProps {
  reportId: string
}

export function ReportDownload({ reportId }: ReportDownloadProps) {
  const [pdfState, setPdfState] = useState<DownloadState>({ status: "idle", message: "" })
  const [excelState, setExcelState] = useState<DownloadState>({ status: "idle", message: "" })

  const handleDownload = async (format: "pdf" | "excel") => {
    const setState = format === "pdf" ? setPdfState : setExcelState
    setState({ status: "loading", message: "Generating report…" })

    try {
      const res: ReportDownloadResponse =
        format === "pdf"
          ? await reportService.getPdfDownloadUrl(reportId)
          : await reportService.getExcelDownloadUrl(reportId)

      if (res.status === "success") {
        setState({ status: "success", message: res.message, downloadUrl: res.download_url })
        // Trigger browser download automatically
        const link = document.createElement("a")
        link.href = `${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}${res.download_url}`
        link.download = format === "pdf" ? `report-${reportId}.pdf` : `report-${reportId}.xlsx`
        link.target = "_blank"
        document.body.appendChild(link)
        link.click()
        document.body.removeChild(link)
      } else {
        setState({ status: "error", message: res.message || "Unexpected error from server." })
      }
    } catch (err: any) {
      setState({
        status: "error",
        message: err?.response?.data?.detail || "Failed to contact backend. Is the server running?",
      })
    }
  }

  const renderButton = (
    format: "pdf" | "excel",
    state: DownloadState,
    label: string,
    icon: React.ReactNode,
    accent: string
  ) => (
    <div className="flex flex-col gap-2">
      <button
        onClick={() => handleDownload(format)}
        disabled={state.status === "loading"}
        className={`
          group relative flex items-center gap-3 rounded-xl border-2 px-6 py-4 text-left
          transition-all duration-200 w-full
          ${state.status === "success"
            ? "border-green-500 bg-green-50 dark:bg-green-950/20 text-green-700 dark:text-green-300"
            : state.status === "error"
            ? "border-destructive bg-destructive/5 text-destructive"
            : `border-border hover:border-${accent}-500 hover:bg-${accent}-50 dark:hover:bg-${accent}-950/20 hover:shadow-md`
          }
          disabled:opacity-70 disabled:cursor-not-allowed
        `}
        aria-label={`Download ${label}`}
        id={`download-${format}-btn`}
      >
        <div className={`
          flex h-12 w-12 shrink-0 items-center justify-center rounded-lg
          ${state.status === "success" ? "bg-green-100 dark:bg-green-900" :
            state.status === "error"   ? "bg-destructive/10" :
            `bg-${accent}-100 dark:bg-${accent}-900/30`}
        `}>
          {state.status === "loading" ? (
            <Loader2 className="h-6 w-6 animate-spin" />
          ) : state.status === "success" ? (
            <CheckCircle2 className="h-6 w-6 text-green-600 dark:text-green-400" />
          ) : state.status === "error" ? (
            <AlertTriangle className="h-6 w-6 text-destructive" />
          ) : (
            icon
          )}
        </div>
        <div className="flex-1">
          <p className="font-semibold text-base">{label}</p>
          <p className="text-sm text-muted-foreground">
            {state.status === "idle"    ? `Click to generate & download .${format === "pdf" ? "pdf" : "xlsx"}` :
             state.status === "loading" ? "Generating…" :
             state.status === "success" ? "Downloaded — click again to refresh" :
             state.message}
          </p>
        </div>
        {state.status === "idle" && (
          <FileDown className="h-5 w-5 text-muted-foreground group-hover:text-foreground transition-colors shrink-0" />
        )}
      </button>
    </div>
  )

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
      {renderButton(
        "pdf",
        pdfState,
        "PDF Report",
        <FileText className="h-6 w-6 text-red-600 dark:text-red-400" />,
        "red"
      )}
      {renderButton(
        "excel",
        excelState,
        "Excel Report",
        <FileSpreadsheet className="h-6 w-6 text-emerald-600 dark:text-emerald-400" />,
        "emerald"
      )}
    </div>
  )
}

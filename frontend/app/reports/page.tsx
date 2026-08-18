"use client"
import React, { useEffect, useState } from "react"
import { Loader2 } from "lucide-react"

import { Sidebar } from "@/components/layout/Sidebar"
import { Navbar } from "@/components/layout/Navbar"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/reports/common/Card"

import { apiService } from "@/services/api"
import { Recommendation } from "@/types/recommendation"
import { ReportPreview } from "@/components/reports/ReportPreview"
import { ReportDownload } from "@/components/reports/ReportDownload"

export default function ReportsPage() {
  const [recommendation, setRecommendation] = useState<Recommendation | null>(null)
  const [reportId, setReportId] = useState<string>("mock-id")
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    async function loadData() {
      try {
        setIsLoading(true)
        // Retrieve the stored optimization result to derive an ID
        const saved = localStorage.getItem("last_optimization")
        let recId = "mock-id"
        if (saved) {
          const parsed = JSON.parse(saved)
          if (parsed.recommended_scenario_id) recId = parsed.recommended_scenario_id
        }
        setReportId(recId)

        const res = await apiService.getRecommendation(recId)
        if (res.status === "success" && res.recommendation) {
          setRecommendation(res.recommendation as Recommendation)
        } else {
          setError("Could not load recommendation data for preview.")
        }
      } catch (err: any) {
        console.error(err)
        setError("Error communicating with backend.")
      } finally {
        setIsLoading(false)
      }
    }
    loadData()
  }, [])

  const shell = (children: React.ReactNode) => (
    <div className="flex h-screen overflow-hidden">
      <Sidebar />
      <div className="flex flex-1 flex-col overflow-hidden">
        <Navbar />
        <main className="flex-1 overflow-y-auto bg-background p-6">
          <div className="mx-auto max-w-4xl">{children}</div>
        </main>
      </div>
    </div>
  )

  if (isLoading) {
    return shell(
      <div className="flex flex-col items-center justify-center h-64 gap-3">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
        <p className="text-muted-foreground text-sm">Loading report preview…</p>
      </div>
    )
  }

  if (error || !recommendation) {
    return shell(
      <div className="bg-destructive/10 text-destructive p-4 rounded-md">
        {error || "Unknown error."}
      </div>
    )
  }

  return shell(
    <div className="space-y-8">
      {/* Page header */}
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Export Report</h1>
        <p className="text-muted-foreground mt-1">
          Download the full recommendation report as PDF or Excel.
        </p>
      </div>

      {/* Download buttons */}
      <Card>
        <CardHeader className="border-b pb-3">
          <CardTitle>Download</CardTitle>
        </CardHeader>
        <CardContent className="pt-5">
          <ReportDownload reportId={reportId} />
          <p className="text-xs text-muted-foreground mt-4">
            The PDF report includes charts, policy details, and sensitivity analysis.
            The Excel file includes a scenario comparison sheet and raw figures for further analysis.
          </p>
        </CardContent>
      </Card>

      {/* Preview */}
      <div>
        <h2 className="text-lg font-semibold mb-4">Report Preview</h2>
        <ReportPreview recommendation={recommendation} />
      </div>
    </div>
  )
}

"use client"
import React, { useEffect, useState } from "react"
import { Loader2 } from "lucide-react"

import { apiService } from "@/services/api"
import { Recommendation } from "@/types/recommendation"
import { ReportPreview } from "@/components/reports/ReportPreview"
import { ReportDownload } from "@/components/reports/ReportDownload"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/reports/common/Card"

export default function ReportsPage() {
  const [recommendation, setRecommendation] = useState<Recommendation | null>(null)
  const [reportId, setReportId] = useState<string>("mock-id")
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    async function loadData() {
      try {
        setIsLoading(true)
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

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-full p-6">
        <div className="flex flex-col items-center gap-3">
          <Loader2 className="h-8 w-8 animate-spin text-emerald-400" />
          <p className="text-zinc-400 text-sm">Loading report preview…</p>
        </div>
      </div>
    )
  }

  if (error || !recommendation) {
    return (
      <div className="p-6">
        <div className="bg-red-500/10 text-red-400 border border-red-500/20 p-4 rounded-xl">
          {error || "Unknown error."}
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-full bg-background text-foreground p-6">
      <div className="mx-auto max-w-4xl space-y-8">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-foreground">Export Report</h1>
          <p className="text-muted-foreground mt-1">Download the full recommendation report as PDF or Excel.</p>
        </div>

        <Card className="border-border/50 bg-card shadow-sm">
          <CardHeader className="border-b border-border/40 pb-3">
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

        <div>
          <h2 className="text-lg font-semibold mb-4 text-foreground">Report Preview</h2>
          <ReportPreview recommendation={recommendation} />
        </div>
      </div>
    </div>
  )
}

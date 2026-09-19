"use client"

import React, { useEffect, useState } from "react"
import { Printer, ArrowLeft, Loader2, AlertTriangle, FileText } from "lucide-react"
import Link from "next/link"

import type { OptimizeResponse } from "@/types/optimization"
import { ResultsView } from "@/components/results/ResultsView"
import { BlockedState } from "@/components/results/BlockedState"

const STORAGE_KEY = "last_optimize_result"

export default function ReportPage() {
  const [result, setResult] = useState<OptimizeResponse | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    try {
      const raw = localStorage.getItem(STORAGE_KEY)
      if (!raw) {
        setError("No analysis results found. Run an assessment first to generate results.")
        return
      }
      const parsed: OptimizeResponse = JSON.parse(raw)

      if (
        typeof parsed.firm_recommendation_blocked !== "boolean" ||
        !Array.isArray(parsed.data_gap_flags) ||
        !parsed.baseline_profile
      ) {
        setError("Stored result is from an older API version. Please re-run the assessment.")
        return
      }

      setResult(parsed)
    } catch {
      setError("Could not parse the stored analysis result. Please re-run the assessment.")
    } finally {
      setIsLoading(false)
    }
  }, [])

  if (isLoading) {
    return (
      <div className="flex h-[50vh] items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    )
  }

  if (error || !result) {
    return (
      <div className="flex h-[50vh] items-center justify-center">
        <div className="rounded-lg border border-destructive/30 bg-destructive/5 p-6 max-w-md">
          <div className="flex items-start gap-3">
            <AlertTriangle className="h-5 w-5 text-destructive mt-0.5" />
            <div className="space-y-2">
              <h3 className="text-sm font-semibold text-foreground">Error Loading Report</h3>
              <p className="text-sm text-foreground-muted">{error}</p>
              <Link href="/assessment" className="inline-flex items-center gap-1.5 text-sm font-medium hover:underline">
                <ArrowLeft className="h-4 w-4" /> Return to Assessment
              </Link>
            </div>
          </div>
        </div>
      </div>
    )
  }

  const factoryRaw = result.dashboard?.factory as Record<string, unknown> | undefined
  const factoryLabel = factoryRaw
    ? [factoryRaw.name, factoryRaw.industry, factoryRaw.state].filter(Boolean).join(" · ")
    : undefined

  const generatedAt = result.generated_at
    ? new Date(result.generated_at).toLocaleString("en-IN", {
        day: "numeric", month: "short", year: "numeric", hour: "2-digit", minute: "2-digit"
      })
    : null

  return (
    <main className="min-h-screen bg-background">
      {/* Print-only header */}
      <div className="hidden print:block mb-8 pb-4 border-b border-border/50">
        <div className="flex justify-between items-end">
          <div>
            <h1 className="text-3xl font-black text-foreground">Urjiva Decarbonization Report</h1>
            <p className="text-muted-foreground mt-1">Generated: {generatedAt}</p>
          </div>
          <div className="text-right">
            <p className="font-bold text-foreground">{factoryRaw?.name as string || "Industrial Facility"}</p>
            <p className="text-sm text-muted-foreground">{factoryRaw?.state as string || ""}</p>
          </div>
        </div>
      </div>

      {/* Screen-only header */}
      <div className="print:hidden sticky top-0 z-50 border-b border-border bg-background/80 backdrop-blur-md">
        <div className="mx-auto flex h-16 max-w-6xl items-center justify-between px-4 sm:px-6">
          <div className="flex items-center gap-4">
            <Link
              href="/results"
              className="inline-flex h-9 items-center justify-center rounded-md border border-border bg-surface px-3 text-sm font-medium shadow-sm transition-colors hover:bg-muted"
            >
              <ArrowLeft className="mr-2 h-4 w-4" />
              Back
            </Link>
            <div>
              <h1 className="text-sm font-bold text-foreground">Investment Grade Report</h1>
              <p className="text-xs text-muted-foreground">{factoryLabel}</p>
            </div>
          </div>
          <button
            onClick={() => window.print()}
            className="inline-flex h-9 items-center justify-center rounded-md bg-foreground px-4 text-sm font-medium text-background shadow-sm transition-colors hover:bg-foreground/90"
          >
            <Printer className="mr-2 h-4 w-4" />
            Print Report
          </button>
        </div>
      </div>

      <div className="mx-auto max-w-6xl px-4 py-8 sm:px-6 print:px-0 print:py-0">
        {result.firm_recommendation_blocked ? (
          <BlockedState
            dataGapFlags={result.data_gap_flags}
            baseline={result.baseline_profile}
            factoryLabel={factoryLabel}
            dashboard={result.dashboard}
          />
        ) : (
          <ResultsView
            dashboard={result.dashboard}
            baseline={result.baseline_profile}
            factoryLabel={factoryLabel}
          />
        )}
      </div>
    </main>
  )
}

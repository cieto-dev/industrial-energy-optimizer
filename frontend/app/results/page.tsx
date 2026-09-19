"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import {
  Loader2,
  RefreshCw,
  AlertTriangle,
  Clock,
  ArrowLeft,
  FileText,
} from "lucide-react";
import type { OptimizeResponse } from "@/types/optimization";
import { BlockedState } from "@/components/results/BlockedState";
import { ResultsView } from "@/components/results/ResultsView";
import { DashboardCharts } from "@/components/dashboard/DashboardCharts";
import { BarChart2 } from "lucide-react";

// ---------------------------------------------------------------------------
// Storage key written by the assessment page after a successful /optimize call
// ---------------------------------------------------------------------------
const STORAGE_KEY = "last_optimize_result";

// ---------------------------------------------------------------------------
// Loading skeleton
// ---------------------------------------------------------------------------

function LoadingSkeleton() {
  return (
    <div className="space-y-6 animate-pulse">
      <div className="h-20 rounded-lg bg-muted" />
      <div className="grid grid-cols-4 gap-4">
        {[...Array(4)].map((_, i) => (
          <div key={i} className="h-24 rounded-lg bg-muted" />
        ))}
      </div>
      <div className="h-64 rounded-lg bg-muted" />
    </div>
  );
}

// ---------------------------------------------------------------------------
// Error state
// ---------------------------------------------------------------------------

function ErrorState({ message }: { message: string }) {
  return (
    <div className="rounded-lg border border-destructive/30 bg-destructive/5 p-6">
      <div className="flex items-start gap-3">
        <AlertTriangle className="h-5 w-5 text-destructive flex-shrink-0 mt-0.5" />
        <div className="space-y-2">
          <h3 className="text-sm font-semibold text-foreground">
            Could not load results
          </h3>
          <p className="text-sm text-foreground-muted">{message}</p>
          <Link
            href="/assessment"
            className="inline-flex items-center gap-1.5 text-sm font-medium text-foreground underline-offset-4 hover:underline"
          >
            <ArrowLeft className="h-4 w-4" />
            Return to assessment to run a new analysis
          </Link>
        </div>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Page
// ---------------------------------------------------------------------------

/**
 * ResultsPage — /results
 *
 * Reads the last /optimize response from localStorage (written by the
 * assessment page), then branches immediately on firm_recommendation_blocked:
 *
 *   true  → BlockedState (data gaps, honest explanation, baseline shown)
 *   false → ResultsView  (ranked pathways, comparison strip, baseline)
 *
 * How the page gets data:
 *   The assessment page calls POST /optimization/optimize, stores the full
 *   response as JSON in localStorage under STORAGE_KEY = "last_optimize_result",
 *   then redirects here. This page reads and renders it.
 *
 *   If nothing is in storage, we show a prompt to run an assessment first.
 */
export default function ResultsPage() {
  const [result, setResult] = useState<OptimizeResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeView, setActiveView] = useState<"analysis" | "visualizations">("analysis");

  useEffect(() => {
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      if (!raw) {
        setError(
          "No analysis results found. Run an assessment first to generate results."
        );
        return;
      }
      const parsed: OptimizeResponse = JSON.parse(raw);

      // Basic shape validation — confirm the hardened contract fields exist.
      if (
        typeof parsed.firm_recommendation_blocked !== "boolean" ||
        !Array.isArray(parsed.data_gap_flags) ||
        !parsed.baseline_profile
      ) {
        setError(
          "Stored result is from an older API version. Please re-run the assessment to get a fresh analysis."
        );
        return;
      }

      setResult(parsed);
    } catch {
      setError(
        "Could not parse the stored analysis result. Please re-run the assessment."
      );
    } finally {
      setIsLoading(false);
    }
  }, []);

  // Build a human-readable factory label for headings.
  const factoryRaw = result?.dashboard?.factory as Record<string, unknown> | undefined;
  const factoryLabel = factoryRaw
    ? [factoryRaw.name, factoryRaw.industry, factoryRaw.state]
        .filter(Boolean)
        .join(" · ")
    : undefined;

  const generatedAt = result?.generated_at
    ? new Date(result.generated_at).toLocaleString("en-IN", {
        day: "numeric",
        month: "short",
        year: "numeric",
        hour: "2-digit",
        minute: "2-digit",
      })
    : null;

  return (
    <div className="min-h-full bg-background">
      {/* Subtle grid background */}
      <div className="fixed inset-0 z-0 opacity-[0.025] pointer-events-none"
        style={{
          backgroundImage: `linear-gradient(currentColor 1px, transparent 1px),
            linear-gradient(90deg, currentColor 1px, transparent 1px)`,
          backgroundSize: "2rem 2rem",
        }}
      />

      <div className="relative z-10 max-w-5xl mx-auto px-4 sm:px-6 py-8 sm:py-12">
        {/* ---------------------------------------------------------------- */}
        {/* Page header                                                        */}
        {/* ---------------------------------------------------------------- */}
        <div className="flex items-start justify-between gap-4 mb-8 flex-wrap">
          <div>
            <div className="flex items-center gap-2 text-xs text-foreground-muted mb-2">
              <Link
                href="/dashboard"
                className="hover:text-foreground transition-colors flex items-center gap-1"
              >
                <ArrowLeft className="h-3.5 w-3.5" />
                Dashboard
              </Link>
              <span>/</span>
              <span>Results</span>
            </div>
            <div className="flex items-center gap-4">
              <h1 className="text-2xl font-bold tracking-tight text-foreground">
                {result?.firm_recommendation_blocked
                  ? "Preliminary Analysis"
                  : "Optimization Results"}
              </h1>
              {result && (
                <div className="flex items-center rounded-lg bg-muted p-1 hidden sm:flex">
                  <button
                    onClick={() => setActiveView("analysis")}
                    className={`px-3 py-1.5 text-xs font-medium rounded-md transition-all ${
                      activeView === "analysis"
                        ? "bg-background text-foreground shadow-sm"
                        : "text-muted-foreground hover:text-foreground"
                    }`}
                  >
                    Analysis
                  </button>
                  <button
                    onClick={() => setActiveView("visualizations")}
                    className={`flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-md transition-all ${
                      activeView === "visualizations"
                        ? "bg-background text-foreground shadow-sm"
                        : "text-muted-foreground hover:text-foreground"
                    }`}
                  >
                    <BarChart2 className="w-3.5 h-3.5" />
                    Visualizations
                  </button>
                </div>
              )}
            </div>
            {factoryLabel && (
              <p className="mt-1 text-sm text-foreground-muted">{factoryLabel}</p>
            )}
          </div>

          <div className="flex items-center gap-3 flex-wrap">
            {generatedAt && (
              <span className="inline-flex items-center gap-1.5 text-xs text-foreground-muted">
                <Clock className="h-3.5 w-3.5" />
                Analysed {generatedAt}
              </span>
            )}
            <Link
              href="/assessment"
              className="inline-flex items-center gap-1.5 rounded-md border border-border px-3 py-1.5 text-xs font-medium text-foreground hover:bg-surface transition-colors"
            >
              <RefreshCw className="h-3.5 w-3.5" />
              Re-run
            </Link>
            {result && (
              <Link
                href="/reports"
                className="inline-flex items-center gap-1.5 rounded-md bg-foreground px-3 py-1.5 text-xs font-medium text-background hover:bg-foreground/90 transition-colors"
              >
                <FileText className="h-3.5 w-3.5" />
                Full report
              </Link>
            )}
          </div>
        </div>

        {/* ---------------------------------------------------------------- */}
        {/* Main content — branch on state                                    */}
        {/* ---------------------------------------------------------------- */}
        {isLoading && <LoadingSkeleton />}

        {!isLoading && error && <ErrorState message={error} />}

        {!isLoading && !error && result && (
          <>
            {activeView === "visualizations" ? (
              <DashboardCharts 
                dashboard={result.dashboard} 
                baseline={result.baseline_profile}
                factoryContext={{
                  state: factoryRaw?.state as string,
                  district: factoryRaw?.district as string,
                  industry: factoryRaw?.industry as string,
                  factory_name: factoryRaw?.name as string,
                  cluster_name: factoryRaw?.cluster_name as string,
                }}
              />
            ) : result.firm_recommendation_blocked ? (
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

            {/* Pipeline transparency footer */}
            <div className="mt-12 pt-6 border-t border-border">
              <details className="group">
                <summary className="flex items-center gap-2 cursor-pointer text-xs font-medium text-foreground-muted hover:text-foreground transition-colors list-none">
                  <span className="group-open:rotate-90 transition-transform inline-block">›</span>
                  Analysis pipeline
                </summary>
                <div className="mt-3 flex flex-wrap gap-1.5">
                  {result.pipeline.map((stage, i) => (
                    <React.Fragment key={stage}>
                      <span className="text-xs font-mono text-foreground-muted bg-muted px-2 py-0.5 rounded">
                        {stage}
                      </span>
                      {i < result.pipeline.length - 1 && (
                        <span className="text-xs text-foreground-muted self-center">→</span>
                      )}
                    </React.Fragment>
                  ))}
                </div>
                <p className="mt-2 text-xs text-foreground-muted">
                  Factory ID:{" "}
                  <span className="font-mono">{result.factory_id}</span>
                </p>
              </details>
            </div>
          </>
        )}
      </div>
    </div>
  );
}

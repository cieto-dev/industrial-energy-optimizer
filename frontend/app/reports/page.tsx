"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import {
  FileText,
  FileSpreadsheet,
  Download,
  ArrowLeft,
  AlertTriangle,
  Clock,
  ShieldCheck,
} from "lucide-react";
import type { OptimizeResponse } from "@/types/optimization";
import { BaselineSummary } from "@/components/results/BaselineSummary";
import { RecommendationCard } from "@/components/dashboard/RecommendationCard";
import { RejectionLog } from "@/components/dashboard/RejectionLog";

export default function ReportsPage() {
  const [result, setResult] = useState<OptimizeResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    try {
      const raw = localStorage.getItem("last_optimize_result");
      if (!raw) {
        setError("No analysis results found. Please run an assessment first.");
        return;
      }
      setResult(JSON.parse(raw));
    } catch {
      setError("Failed to load results for report generation.");
    }
  }, []);

  if (error || !result) {
    return (
      <div className="min-h-full bg-background p-8 flex items-center justify-center">
        <div className="max-w-md w-full bg-surface border border-border p-6 rounded-lg text-center">
          <AlertTriangle className="h-8 w-8 text-amber-500 mx-auto mb-4" />
          <h2 className="text-lg font-semibold text-foreground mb-2">
            No Data Available
          </h2>
          <p className="text-sm text-foreground-muted mb-6">
            {error || "Loading..."}
          </p>
          <Link
            href="/assessment"
            className="inline-flex items-center gap-2 rounded-md bg-foreground px-4 py-2 text-sm font-medium text-background"
          >
            Go to Assessment
          </Link>
        </div>
      </div>
    );
  }

  const factoryRaw = result.dashboard?.factory as Record<string, unknown> | undefined;
  const factoryLabel = factoryRaw
    ? [factoryRaw.name, factoryRaw.industry, factoryRaw.state]
        .filter(Boolean)
        .join(" · ")
    : undefined;

  return (
    <div className="min-h-full bg-background">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 py-8 sm:py-12">
        {/* Header */}
        <div className="mb-8 print:hidden">
          <div className="flex items-center gap-2 text-xs text-foreground-muted mb-4">
            <Link
              href="/results"
              className="hover:text-foreground transition-colors flex items-center gap-1"
            >
              <ArrowLeft className="h-3.5 w-3.5" />
              Back to Results
            </Link>
            <span>/</span>
            <span>Export</span>
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-foreground">
            Bank-Grade Report Export
          </h1>
          <p className="text-sm text-foreground-muted mt-2">
            Generate offline copies of the decarbonization analysis for internal
            review and project financing.
          </p>
        </div>

        {/* Pending State Banner */}
        <div className="mb-8 rounded-lg border border-amber-200 dark:border-amber-800 bg-amber-50 dark:bg-amber-950/40 p-5 flex items-start gap-3 print:hidden">
          <Clock className="h-5 w-5 text-amber-600 dark:text-amber-400 mt-0.5 flex-shrink-0" />
          <div>
            <h3 className="text-sm font-semibold text-amber-900 dark:text-amber-100">
              Report generation pending — data contract ready
            </h3>
            <p className="text-sm text-amber-800 dark:text-amber-300 mt-1">
              The frontend data contract has been hardened and is ready to stream
              to the PDF/Excel engines. Backend file generation endpoints are
              currently in development and will be activated shortly. No data
              is fabricated in the meantime. Click "Print to PDF" to generate a client-side export.
            </p>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-12 print:hidden">
          {/* PDF Export Card */}
          <div className="rounded-lg border border-border bg-surface p-6 flex flex-col">
            <div className="flex items-center gap-3 mb-4">
              <div className="p-2 bg-rose-100 dark:bg-rose-900/30 rounded-lg">
                <FileText className="h-6 w-6 text-rose-600 dark:text-rose-400" />
              </div>
              <div>
                <h3 className="text-base font-semibold text-foreground">
                  Executive PDF Report
                </h3>
                <p className="text-xs text-foreground-muted">
                  For management & board review
                </p>
              </div>
            </div>
            <ul className="text-sm text-foreground-muted space-y-2 mb-6 flex-1">
              <li className="flex items-start gap-2">
                <ShieldCheck className="h-4 w-4 text-emerald-500 mt-0.5 flex-shrink-0" />
                <span>Executive summary & pathway rankings</span>
              </li>
              <li className="flex items-start gap-2">
                <ShieldCheck className="h-4 w-4 text-emerald-500 mt-0.5 flex-shrink-0" />
                <span>Methodology & confidence declarations</span>
              </li>
              <li className="flex items-start gap-2">
                <ShieldCheck className="h-4 w-4 text-emerald-500 mt-0.5 flex-shrink-0" />
                <span>Clear No-Invention / bounded-ranges disclaimer</span>
              </li>
            </ul>
            <button
              onClick={() => window.print()}
              className="w-full inline-flex items-center justify-center gap-2 rounded-md bg-foreground px-4 py-2.5 text-sm font-medium text-background hover:bg-foreground/90 transition-colors print:hidden"
            >
              <Download className="h-4 w-4" />
              Print to PDF
            </button>
          </div>

          {/* Excel Export Card */}
          <div className="rounded-lg border border-border bg-surface p-6 flex flex-col">
            <div className="flex items-center gap-3 mb-4">
              <div className="p-2 bg-emerald-100 dark:bg-emerald-900/30 rounded-lg">
                <FileSpreadsheet className="h-6 w-6 text-emerald-600 dark:text-emerald-400" />
              </div>
              <div>
                <h3 className="text-base font-semibold text-foreground">
                  Data Extract (Excel)
                </h3>
                <p className="text-xs text-foreground-muted">
                  For engineering & finance teams
                </p>
              </div>
            </div>
            <ul className="text-sm text-foreground-muted space-y-2 mb-6 flex-1">
              <li className="flex items-start gap-2">
                <ShieldCheck className="h-4 w-4 text-emerald-500 mt-0.5 flex-shrink-0" />
                <span>Raw baseline consumption data</span>
              </li>
              <li className="flex items-start gap-2">
                <ShieldCheck className="h-4 w-4 text-emerald-500 mt-0.5 flex-shrink-0" />
                <span>Detailed per-scenario CAPEX & OPEX models</span>
              </li>
              <li className="flex items-start gap-2">
                <ShieldCheck className="h-4 w-4 text-emerald-500 mt-0.5 flex-shrink-0" />
                <span>Full structured data gap flags</span>
              </li>
            </ul>
            <button
              disabled
              className="w-full inline-flex items-center justify-center gap-2 rounded-md border border-border px-4 py-2.5 text-sm font-medium text-foreground hover:bg-surface transition-colors opacity-50 cursor-not-allowed"
            >
              <Download className="h-4 w-4" />
              Download Excel (Pending)
            </button>
          </div>
        </div>

        {/* Methodology & Confidence Preview */}
        <div>
          <h2 className="text-lg font-semibold text-foreground mb-4 border-b border-border pb-2 print:hidden">
            Report Preview: Methodology & Confidence
          </h2>
          <h2 className="hidden print:block text-2xl font-bold text-foreground mb-6 border-b border-border pb-4">
            Industrial Decarbonization Assessment
          </h2>
          
          <div className="space-y-6">
            {/* Disclaimer */}
            <div className="bg-surface-muted border border-border rounded-lg p-5 break-inside-avoid">
              <h4 className="text-xs font-bold uppercase tracking-wider text-foreground-muted mb-2">
                System Disclaimer: No-Invention Rule
              </h4>
              <p className="text-sm text-foreground-muted leading-relaxed">
                All financial figures within this report represent rigorous estimations based on standard IPCC emission factors, historical industrial benchmarks, and the user's explicit inputs. 
                <strong> The Urjiva Engine adheres strictly to a "No-Invention" rule.</strong> Where a specific capital expenditure (CAPEX) or financial parameter is not available in the proprietary knowledge base, it is explicitly marked as unavailable rather than fabricated. 
                In these instances, validated vendor quotes must be provided to unlock definitive simple payback, ROI, and NPV calculations.
                <strong> Once real CAPEX data is ingested or entered, the ranges will automatically collapse into firm payback and NPV figures.</strong>
              </p>
            </div>

            {/* Baseline Preview */}
            <div>
              <h4 className="text-xs font-bold uppercase tracking-wider text-foreground-muted mb-3">
                Verified Baseline Profile
              </h4>
              <BaselineSummary baseline={result.baseline_profile} factoryLabel={factoryLabel} />
            </div>
            
            {/* Data Gaps Preview */}
            {result.data_gap_flags.length > 0 && (
              <div className="break-inside-avoid">
                <h4 className="text-xs font-bold uppercase tracking-wider text-foreground-muted mb-3">
                  Identified Data Gaps & Confidence Limitations
                </h4>
                <div className="bg-surface border border-border rounded-lg overflow-hidden divide-y divide-border">
                  {result.data_gap_flags.map((flag, idx) => {
                    const [field, severity] = flag.split(":");
                    return (
                      <div key={idx} className="p-4 flex items-center justify-between">
                        <div className="flex items-center gap-3">
                          <span className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${
                            severity === "blocking" ? "bg-amber-100 text-amber-800 dark:bg-amber-900/50 dark:text-amber-200" : "bg-slate-100 text-slate-800 dark:bg-slate-800 dark:text-slate-300"
                          }`}>
                            {severity.toUpperCase()}
                          </span>
                          <span className="text-sm font-medium text-foreground capitalize">
                            {field.replace(/_/g, " ")}
                          </span>
                        </div>
                        <span className="text-sm text-foreground-muted text-right max-w-sm">
                          {severity === "blocking" ? "Requires vendor quote / user input to proceed with financial modeling." : "May reduce overall confidence of the model."}
                        </span>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}

            {/* Technical Ranking */}
            {result.dashboard?.finance?.scenarios && result.dashboard.finance.scenarios.length > 0 && (
              <div className="pt-4 break-inside-avoid">
                <h4 className="text-xs font-bold uppercase tracking-wider text-foreground-muted mb-3">
                  Preliminary Technical Rankings
                </h4>
                <div className="space-y-4">
                  {result.dashboard.finance.scenarios.slice(0, 3).map((pathway, idx) => (
                    <RecommendationCard 
                      key={idx} 
                      pathway={pathway} 
                      baseline={result.baseline_profile} 
                      factoryContext={{
                        state: (factoryRaw?.state as string) || "",
                        district: (factoryRaw?.district as string) || "",
                        industry: (factoryRaw?.industry as string) || "",
                        factory_name: (factoryRaw?.name as string) || "",
                        cluster_name: "",
                        special_category: {},
                      }} 
                      rank={idx + 1} 
                    />
                  ))}
                </div>
              </div>
            )}

            {/* Rejection Log */}
            {result.dashboard?.finance?.scenarios && result.dashboard.technology_assessment?.rejected && (
              <div className="pt-4 break-inside-avoid">
                <h4 className="text-xs font-bold uppercase tracking-wider text-foreground-muted mb-3">
                  Rejection Reasons & Decision Log
                </h4>
                <RejectionLog 
                  pathways={result.dashboard.finance.scenarios} 
                  rejectedTechs={result.dashboard.technology_assessment.rejected} 
                />
              </div>
            )}
          </div>
        </div>

      </div>
    </div>
  );
}

"use client";

import React from "react";
import Link from "next/link";
import {
  Lock,
  AlertTriangle,
  ArrowLeft,
  ChevronRight,
  Database,
  Info,
} from "lucide-react";
import type { BaselineProfile, Dashboard } from "@/types/optimization";
import { BaselineSummary } from "./BaselineSummary";
import { RecommendationCard } from "@/components/dashboard/RecommendationCard";

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

/** Map raw data_gap_flags tags to user-readable copy. */
function describeFlagTag(tag: string): {
  field: string;
  severity: "blocking" | "warning";
  description: string;
  action: string;
} {
  const [field, severity] = tag.split(":");
  const isBlocking = severity === "blocking";

  const descriptions: Record<string, { description: string; action: string }> =
    {
      capex: {
        description:
          "Capital expenditure (CAPEX) for one or more candidate technologies is not available in the knowledge base. Without a CAPEX estimate, payback period, NPV, and ROI cannot be calculated.",
        action:
          "Provide a vendor quote or indicative CAPEX figure in the assessment form.",
      },
      lifetime: {
        description:
          "Asset lifetime assumption is missing. Without this, NPV and levelised cost calculations cannot run.",
        action:
          "Specify the expected equipment lifetime (typically 15–25 years for thermal systems).",
      },
      discount_rate: {
        description:
          "Discount rate is not set. This affects NPV and IRR calculations.",
        action:
          "Enter your weighted average cost of capital (WACC) or a project hurdle rate.",
      },
      baseline_fuel: {
        description:
          "Fuel consumption data is insufficient to set a reliable cost baseline.",
        action:
          "Enter annual fuel consumption from your last energy audit or utility bills.",
      },
      electricity: {
        description:
          "Electricity consumption or tariff data is incomplete or covers partial demand.",
        action:
          "Provide monthly electricity bills or connected load data.",
      },
    };

  const info = descriptions[field] ?? {
    description: `The '${field}' field is missing or incomplete.`,
    action: "Complete the relevant section of the assessment form.",
  };

  return {
    field,
    severity: isBlocking ? "blocking" : "warning",
    description: info.description,
    action: info.action,
  };
}

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface BlockedStateProps {
  dataGapFlags: string[];
  baseline: BaselineProfile;
  factoryLabel?: string;
  dashboard?: Dashboard;
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

/**
 * BlockedState
 *
 * Rendered when firm_recommendation_blocked is true.
 *
 * Shows:
 *  1. A clear, non-alarming explanation of WHY the system cannot issue a
 *     firm recommendation.
 *  2. Structured list of each data gap with field, severity, and action.
 *  3. The verified baseline profile (to show real work was done).
 *  4. Primary CTA: return to assessment to fix the gaps.
 */
export function BlockedState({
  dataGapFlags,
  baseline,
  factoryLabel,
  dashboard,
}: BlockedStateProps) {
  const blockingFlags = dataGapFlags.filter((f) =>
    f.includes(":blocking")
  );
  const warningFlags = dataGapFlags.filter((f) =>
    f.includes(":warning")
  );

  const parsedFlags = dataGapFlags.map(describeFlagTag);

  return (
    <div className="space-y-8">
      {/* ------------------------------------------------------------------ */}
      {/* Status banner                                                        */}
      {/* ------------------------------------------------------------------ */}
      <div className="rounded-lg border border-amber-200 dark:border-amber-800 bg-amber-50 dark:bg-amber-950/40 p-5">
        <div className="flex items-start gap-3">
          <div className="mt-0.5 flex-shrink-0 rounded-md bg-amber-100 dark:bg-amber-900 p-1.5">
            <Lock className="h-4 w-4 text-amber-700 dark:text-amber-300" />
          </div>
          <div className="space-y-1">
            <h2 className="text-base font-semibold text-amber-900 dark:text-amber-100">
              Preliminary Analysis — Firm Recommendation Blocked
            </h2>
            <p className="text-sm text-amber-800 dark:text-amber-300 leading-relaxed max-w-2xl">
              The engine has completed the baseline and technology feasibility
              assessment, but cannot issue a firm financial recommendation
              because one or more required data inputs are unavailable.{" "}
              {blockingFlags.length > 0 && (
                <>
                  <strong>{blockingFlags.length} blocking gap
                  {blockingFlags.length !== 1 ? "s" : ""}</strong>{" "}
                  must be resolved before payback, NPV, or ROI figures can be
                  calculated honestly.
                </>
              )}
            </p>
          </div>
        </div>

        {/* Gap count chips */}
        <div className="mt-4 flex items-center gap-3 flex-wrap">
          {blockingFlags.length > 0 && (
            <span className="inline-flex items-center gap-1.5 rounded-full border border-amber-300 dark:border-amber-700 bg-white dark:bg-amber-900/40 px-3 py-1 text-xs font-medium text-amber-800 dark:text-amber-200">
              <AlertTriangle className="h-3 w-3" />
              {blockingFlags.length} blocking gap{blockingFlags.length !== 1 ? "s" : ""}
            </span>
          )}
          {warningFlags.length > 0 && (
            <span className="inline-flex items-center gap-1.5 rounded-full border border-border bg-surface px-3 py-1 text-xs font-medium text-foreground-muted">
              <Info className="h-3 w-3" />
              {warningFlags.length} warning{warningFlags.length !== 1 ? "s" : ""}
            </span>
          )}
          <span className="text-xs text-amber-700 dark:text-amber-400">
            The baseline numbers below are sound and can be used independently.
          </span>
        </div>
      </div>

      {/* ------------------------------------------------------------------ */}
      {/* Preliminary Technical Rankings                                       */}
      {/* ------------------------------------------------------------------ */}
      {dashboard?.finance?.scenarios && dashboard.finance.scenarios.length > 0 && (
        <div className="mt-8">
          <h3 className="text-xl font-bold text-foreground mb-2">
            Preliminary Technical Ranking
          </h3>
          <p className="text-sm text-foreground-muted mb-6">
            These pathways are structurally feasible based on your temperature requirements and reliability parameters. The engine has ranked them on operational suitability to ensure production continuity.
          </p>
          <div className="space-y-4">
            {dashboard.finance.scenarios.slice(0, 3).map((pathway, idx) => {
              const factoryRaw = dashboard.factory as Record<string, unknown> | undefined;
              const factoryContext = {
                state: (factoryRaw?.state as string) || "",
                district: (factoryRaw?.district as string) || "",
                industry: (factoryRaw?.industry as string) || "",
                factory_name: (factoryRaw?.name as string) || "",
                cluster_name: "",
                special_category: {},
              };
              return (
                <RecommendationCard key={idx} pathway={pathway} baseline={baseline} factoryContext={factoryContext} rank={idx + 1} />
              )
            })}
          </div>
        </div>
      )}

      {/* ------------------------------------------------------------------ */}
      {/* Data gap details                                                     */}
      {/* ------------------------------------------------------------------ */}
      {parsedFlags.length > 0 && (
        <div className="mt-12 pt-8 border-t border-border">
          <h3 className="text-sm font-semibold text-foreground mb-3 flex items-center gap-2">
            <Database className="h-4 w-4 text-foreground-muted" />
            Missing Data Required for Financial Recommendation
          </h3>
          <div className="divide-y divide-border rounded-lg border border-border overflow-hidden">
            {parsedFlags.map((flag, i) => (
              <div
                key={i}
                className="grid grid-cols-[auto_1fr] gap-0"
              >
                {/* Severity stripe */}
                <div
                  className={`w-1 flex-shrink-0 ${
                    flag.severity === "blocking"
                      ? "bg-amber-400"
                      : "bg-slate-300 dark:bg-slate-600"
                  }`}
                />
                <div className="p-4 bg-surface">
                  <div className="flex items-start justify-between gap-4 flex-wrap">
                    <div className="space-y-1 flex-1 min-w-0">
                      <div className="flex items-center gap-2 flex-wrap">
                        <span className="font-mono text-xs font-semibold text-foreground uppercase tracking-wider">
                          {flag.field}
                        </span>
                        <span
                          className={`text-[11px] font-medium rounded-full px-2 py-0.5 ${
                            flag.severity === "blocking"
                              ? "bg-amber-100 text-amber-800 dark:bg-amber-900 dark:text-amber-200"
                              : "bg-muted text-muted-foreground"
                          }`}
                        >
                          {flag.severity}
                        </span>
                      </div>
                      <p className="text-sm text-foreground-muted leading-relaxed">
                        {flag.description}
                      </p>
                    </div>
                    <div className="text-right shrink-0">
                      <p className="text-xs font-medium text-foreground mb-0.5">
                        How to fix
                      </p>
                      <p className="text-xs text-foreground-muted max-w-[200px] text-right">
                        {flag.action}
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}


      {/* ------------------------------------------------------------------ */}
      {/* Baseline (always show — it is sound)                                */}
      {/* ------------------------------------------------------------------ */}
      <BaselineSummary baseline={baseline} factoryLabel={factoryLabel} />

      {/* ------------------------------------------------------------------ */}
      {/* CTA                                                                  */}
      {/* ------------------------------------------------------------------ */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center gap-3 pt-2">
        <Link
          href="/assessment"
          className="inline-flex items-center gap-2 rounded-md bg-foreground px-4 py-2.5 text-sm font-medium text-background hover:bg-foreground/90 transition-colors"
        >
          Provide missing data
          <ChevronRight className="h-4 w-4" />
        </Link>
        <Link
          href="/dashboard"
          className="inline-flex items-center gap-2 rounded-md border border-border px-4 py-2.5 text-sm font-medium text-foreground hover:bg-surface transition-colors"
        >
          <ArrowLeft className="h-4 w-4" />
          Back to dashboard
        </Link>
        <p className="text-xs text-foreground-muted mt-1 sm:mt-0 sm:ml-2">
          No numbers have been fabricated. Payback and CAPEX will appear once
          data gaps are resolved.
        </p>
      </div>
    </div>
  );
}

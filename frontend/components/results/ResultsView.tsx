"use client";

import React from "react";
import Link from "next/link";
import {
  CheckCircle2,
  TrendingDown,
  Layers,
  ArrowRight,
  ChevronRight,
} from "lucide-react";
import type {
  BaselineProfile,
  Dashboard,
  ScenarioPathwayEnriched,
} from "@/types/optimization";
import { RangeDisplay } from "@/components/ui/RangeDisplay";
import { ConfidenceBadge } from "@/components/ui/ConfidenceBadge";
import { BaselineSummary } from "./BaselineSummary";

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function fmtINR(v: number | null | undefined): string {
  if (v == null) return "—";
  if (v >= 1_00_00_000) return `₹${(v / 1_00_00_000).toFixed(1)} Cr`;
  if (v >= 1_00_000) return `₹${(v / 1_00_000).toFixed(1)} L`;
  return `₹${v.toLocaleString("en-IN")}`;
}

export function techLabel(seq: string[]): string {
  return seq
    .map((t) =>
      t
        .replace(/_/g, " ")
        .replace(/\b\w/g, (c) => c.toUpperCase())
    )
    .join(" + ");
}

// ---------------------------------------------------------------------------
// Pathway comparison row (baseline vs recommended vs #2)
// ---------------------------------------------------------------------------

interface CompareRowProps {
  label: string;
  baseline: React.ReactNode;
  recommended: React.ReactNode;
  alternative?: React.ReactNode;
  highlight?: boolean;
}

function CompareRow({
  label,
  baseline,
  recommended,
  alternative,
  highlight,
}: CompareRowProps) {
  return (
    <div
      className={`grid grid-cols-[160px_1fr_1fr_1fr] gap-px text-sm ${
        highlight ? "bg-emerald-50/50 dark:bg-emerald-950/20" : ""
      }`}
    >
      <div className="px-4 py-3 text-xs font-medium uppercase tracking-wide text-foreground-muted self-center">
        {label}
      </div>
      <div className="px-4 py-3 bg-surface text-foreground-muted font-mono">
        {baseline}
      </div>
      <div
        className={`px-4 py-3 font-mono font-semibold ${
          highlight
            ? "bg-emerald-50 dark:bg-emerald-950/30 text-emerald-800 dark:text-emerald-300"
            : "bg-surface text-foreground"
        }`}
      >
        {recommended}
      </div>
      <div className="px-4 py-3 bg-surface text-foreground-muted font-mono">
        {alternative ?? "—"}
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Recommended pathway card
// ---------------------------------------------------------------------------

interface PathwayCardProps {
  pathway: ScenarioPathwayEnriched;
  rank: number;
  isRecommended?: boolean;
}

export function PathwayCard({ pathway, rank, isRecommended }: PathwayCardProps) {
  const fm = pathway.financial_model;
  const rel = pathway.reliability;

  const capexBlocked = !fm || fm.capex.status === "unavailable";
  const paybackBlocked =
    !fm || fm.payback_min_years == null || fm.payback_max_years == null;
  const savingsBlocked =
    !fm ||
    fm.annual_savings_min_inr == null ||
    fm.annual_savings_max_inr == null;

  return (
    <div
      className={`rounded-lg border overflow-hidden ${
        isRecommended
          ? "border-foreground/30 ring-1 ring-foreground/10"
          : "border-border"
      }`}
    >
      {/* Header */}
      <div
        className={`flex items-center justify-between px-5 py-3.5 ${
          isRecommended ? "bg-foreground text-background" : "bg-surface"
        }`}
      >
        <div className="flex items-center gap-2.5">
          <span
            className={`text-xs font-medium tabular-nums ${
              isRecommended ? "text-background/60" : "text-foreground-muted"
            }`}
          >
            #{rank}
          </span>
          <h4
            className={`text-sm font-semibold ${
              isRecommended ? "text-background" : "text-foreground"
            }`}
          >
            {techLabel(pathway.technology_sequence)}
          </h4>
        </div>
        <div className="flex items-center gap-4">
          {isRecommended && (
            <span className="inline-flex items-center gap-1 text-xs font-medium text-background/80">
              <CheckCircle2 className="h-3.5 w-3.5" />
              MCDA ranked #1
            </span>
          )}
          <Link
            href={`/recommendations/${pathway.scenario_id || pathway.technology_sequence.join("-")}`}
            className={`text-xs font-medium hover:underline underline-offset-4 ${
              isRecommended ? "text-background" : "text-accent"
            }`}
          >
            View details →
          </Link>
        </div>
      </div>

      {/* Metrics */}
      <div className="grid grid-cols-1 sm:grid-cols-3 divide-y sm:divide-y-0 sm:divide-x divide-border bg-surface">
        <div className="p-4">
          <RangeDisplay
            label="CAPEX"
            value={
              !capexBlocked && fm
                ? [fm.capex.capex_min_inr!, fm.capex.capex_max_inr!]
                : null
            }
            formatAsINR
            isBlocked={capexBlocked}
            blockedReason={
              capexBlocked
                ? "Not in knowledge base"
                : undefined
            }
            confidence={fm?.capex.confidence ?? undefined}
          />
        </div>
        <div className="p-4">
          <RangeDisplay
            label="Annual savings"
            value={
              !savingsBlocked && fm
                ? [fm.annual_savings_min_inr!, fm.annual_savings_max_inr!]
                : null
            }
            formatAsINR
            isBlocked={savingsBlocked}
            blockedReason={
              savingsBlocked && capexBlocked
                ? "Requires CAPEX input"
                : "Data unavailable"
            }
          />
        </div>
        <div className="p-4">
          <RangeDisplay
            label="Simple payback"
            value={
              !paybackBlocked && fm
                ? [fm.payback_min_years!, fm.payback_max_years!]
                : null
            }
            unit="years"
            decimalPlaces={1}
            isBlocked={paybackBlocked}
            blockedReason={
              paybackBlocked && capexBlocked
                ? "Requires CAPEX input"
                : "Data unavailable"
            }
          />
        </div>
      </div>

      {/* Reliability / data gap chips */}
      <div className="px-5 py-3 border-t border-border bg-surface-muted flex flex-wrap gap-2 items-center">
        {rel?.status === "blocked" && (
          <span className="text-xs text-foreground-muted">
            Reliability sweep: {rel.reason ?? "blocked (CAPEX required)"}
          </span>
        )}
        {rel?.status === "success" && rel.score_pct != null && (
          <span className="text-xs font-medium text-foreground">
            Reliability {rel.score_pct.toFixed(0)}%
          </span>
        )}
        {(fm?.data_gap_flags ?? []).slice(0, 3).map((dgf, i) => (
          <span
            key={i}
            className={`inline-flex items-center rounded-full px-2 py-0.5 text-[11px] font-medium ${
              dgf.severity === "blocking"
                ? "bg-amber-100 text-amber-800 dark:bg-amber-900 dark:text-amber-200"
                : "bg-muted text-muted-foreground"
            }`}
          >
            {dgf.field}: {dgf.severity}
          </span>
        ))}
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Props
// ---------------------------------------------------------------------------

interface ResultsViewProps {
  dashboard: Dashboard;
  baseline: BaselineProfile;
  factoryLabel?: string;
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

/**
 * ResultsView
 *
 * Rendered when firm_recommendation_blocked is FALSE.
 * Shows the 30-second view:
 *  1. Recommended pathway + key metrics (with honest RangeDisplay).
 *  2. Comparison strip: Baseline vs Recommended vs #2 alternative.
 *  3. Baseline summary (reused from BlockedState).
 *
 * All numbers flow from the API. No fabricated values.
 */
export function ResultsView({
  dashboard,
  baseline,
  factoryLabel,
}: ResultsViewProps) {
  const allPathways = dashboard.finance?.scenarios ?? [];

  // Best-effort: use MCDA ranked_pathways, fall back to finance scenarios
  const rankedPathways: ScenarioPathwayEnriched[] =
    (dashboard.ranked_pathways?.length > 0
      ? dashboard.ranked_pathways
      : allPathways
    ).slice(0, 3);

  const recommended = rankedPathways[0] ?? null;
  const alternative = rankedPathways[1] ?? null;

  if (!recommended) {
    return (
      <div className="rounded-lg border border-border bg-surface p-8 text-center">
        <p className="text-sm text-foreground-muted">
          No ranked pathways available. The optimizer may not have had enough
          numeric inputs to rank scenarios.
        </p>
        <Link
          href="/assessment"
          className="mt-4 inline-flex items-center gap-1.5 text-sm font-medium text-foreground underline-offset-4 hover:underline"
        >
          Return to assessment
          <ArrowRight className="h-4 w-4" />
        </Link>
      </div>
    );
  }

  // ----- Baseline cost for comparison strip -----
  const baselineCost = baseline.annual_total_energy_cost_inr;
  const recFM = recommended.financial_model;
  const altFM = alternative?.financial_model;

  const recOpex = recFM?.proposed_opex.total_inr;
  const altOpex = altFM?.proposed_opex.total_inr;

  const recPaybackMin = recFM?.payback_min_years;
  const recPaybackMax = recFM?.payback_max_years;
  const altPaybackMin = altFM?.payback_min_years;
  const altPaybackMax = altFM?.payback_max_years;

  return (
    <div className="space-y-8">
      {/* ------------------------------------------------------------------ */}
      {/* Section: Recommended pathway                                         */}
      {/* ------------------------------------------------------------------ */}
      <div>
        <div className="flex items-center gap-2 mb-4">
          <CheckCircle2 className="h-4 w-4 text-emerald-600" />
          <h2 className="text-base font-semibold text-foreground">
            Recommended Pathway
          </h2>
        </div>

        <div className="space-y-3">
          <PathwayCard pathway={recommended} rank={1} isRecommended />
          {alternative && (
            <PathwayCard pathway={alternative} rank={2} />
          )}
        </div>

        {rankedPathways.length === 0 && (
          <p className="text-xs text-foreground-muted mt-2">
            MCDA could not rank pathways — not enough numeric cost/emissions
            data. Resolve CAPEX gaps and re-run.
          </p>
        )}
      </div>

      {/* ------------------------------------------------------------------ */}
      {/* Section: Comparison strip                                            */}
      {/* ------------------------------------------------------------------ */}
      <div>
        <div className="flex items-center gap-2 mb-4">
          <Layers className="h-4 w-4 text-foreground-muted" />
          <h2 className="text-base font-semibold text-foreground">
            Pathway Comparison
          </h2>
        </div>

        <div className="rounded-lg border border-border overflow-hidden">
          {/* Column headers */}
          <div className="grid grid-cols-[160px_1fr_1fr_1fr] bg-surface-muted text-xs font-semibold uppercase tracking-wide text-foreground-muted divide-x divide-border border-b border-border">
            <div className="px-4 py-2.5" />
            <div className="px-4 py-2.5">Baseline (current)</div>
            <div className="px-4 py-2.5 text-foreground">
              Recommended ↗
            </div>
            <div className="px-4 py-2.5">
              {alternative
                ? `Alt. #2: ${techLabel(alternative.technology_sequence).substring(0, 24)}`
                : "—"}
            </div>
          </div>

          <div className="divide-y divide-border">
            <CompareRow
              label="Technology"
              baseline="Current system"
              recommended={techLabel(recommended.technology_sequence)}
              alternative={
                alternative
                  ? techLabel(alternative.technology_sequence)
                  : undefined
              }
              highlight
            />
            <CompareRow
              label="Annual energy cost"
              baseline={fmtINR(baselineCost)}
              recommended={
                recOpex != null ? fmtINR(recOpex) : "—"
              }
              alternative={
                altOpex != null ? fmtINR(altOpex) : "—"
              }
            />
            <CompareRow
              label="Payback period"
              baseline="—"
              recommended={
                recPaybackMin != null && recPaybackMax != null
                  ? `${recPaybackMin.toFixed(1)}–${recPaybackMax.toFixed(1)} yrs`
                  : "CAPEX required"
              }
              alternative={
                altPaybackMin != null && altPaybackMax != null
                  ? `${altPaybackMin.toFixed(1)}–${altPaybackMax.toFixed(1)} yrs`
                  : "—"
              }
            />
            <CompareRow
              label="CAPEX"
              baseline="—"
              recommended={
                recFM?.capex.status === "unavailable"
                  ? "Not in KB"
                  : fmtINR(recFM?.capex.capex_max_inr)
              }
              alternative={
                altFM?.capex.status === "unavailable"
                  ? "Not in KB"
                  : altFM
                  ? fmtINR(altFM.capex.capex_max_inr)
                  : "—"
              }
            />
          </div>
        </div>

        <p className="mt-2 text-xs text-foreground-muted">
          "Not in KB" = CAPEX not available in the knowledge base. Provide a
          vendor quote to unlock payback and NPV calculations.
        </p>
      </div>

      {/* ------------------------------------------------------------------ */}
      {/* Section: Baseline summary                                            */}
      {/* ------------------------------------------------------------------ */}
      <div>
        <div className="flex items-center gap-2 mb-4">
          <TrendingDown className="h-4 w-4 text-foreground-muted" />
          <h2 className="text-base font-semibold text-foreground">
            Verified Baseline
          </h2>
        </div>
        <BaselineSummary baseline={baseline} factoryLabel={factoryLabel} />
      </div>

      {/* ------------------------------------------------------------------ */}
      {/* Footer CTA                                                           */}
      {/* ------------------------------------------------------------------ */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center gap-3 pt-2 border-t border-border">
        <Link
          href="/assessment"
          className="inline-flex items-center gap-2 rounded-md border border-border px-4 py-2.5 text-sm font-medium text-foreground hover:bg-surface transition-colors"
        >
          <ArrowRight className="h-4 w-4" />
          Add missing data (CAPEX / lifetime)
        </Link>
        <p className="text-xs text-foreground-muted">
          Ranges will narrow once CAPEX is provided. All displayed figures are
          from the knowledge base or your inputs — none are fabricated.
        </p>
      </div>
    </div>
  );
}

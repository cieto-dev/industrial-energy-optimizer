"use client";


import React, { useEffect, useState, use } from "react";
import Link from "next/link";
import {
  ArrowLeft,
  CheckCircle2,
  XCircle,
  TrendingDown,
  Info,
  ShieldCheck,
  AlertTriangle,
  FileText,
} from "lucide-react";
import type { OptimizeResponse, ScenarioPathwayEnriched } from "@/types/optimization";
import { RangeDisplay } from "@/components/ui/RangeDisplay";
import { ConfidenceBadge } from "@/components/ui/ConfidenceBadge";

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function techLabel(seq: string[]): string {
  return seq
    .map((t) =>
      t
        .replace(/_/g, " ")
        .replace(/\b\w/g, (c) => c.toUpperCase())
    )
    .join(" + ");
}

// ---------------------------------------------------------------------------
// Page
// ---------------------------------------------------------------------------

export default function PathwayDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const unwrappedParams = use(params);
  const { id } = unwrappedParams;
  
  const [result, setResult] = useState<OptimizeResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  
  const [pathway, setPathway] = useState<ScenarioPathwayEnriched | null>(null);
  const [alternatives, setAlternatives] = useState<ScenarioPathwayEnriched[]>([]);

  useEffect(() => {
    try {
      const raw = localStorage.getItem("last_optimize_result");
      if (!raw) {
        setError("No analysis results found. Please run an assessment first.");
        return;
      }
      const parsed: OptimizeResponse = JSON.parse(raw);
      setResult(parsed);

      const allScenarios = parsed.dashboard?.finance?.scenarios ?? [];
      const rankedScenarios = parsed.dashboard?.ranked_pathways?.length > 0 
        ? parsed.dashboard.ranked_pathways 
        : allScenarios;

      // Find by scenario_id or fallback to technology_sequence
      const target = rankedScenarios.find(
        (p) => p.scenario_id === id || p.technology_sequence.join("-") === id
      );

      if (!target) {
        setError("Pathway not found in the recent optimization run.");
        return;
      }

      setPathway(target);
      setAlternatives(rankedScenarios.filter((p) => p !== target).slice(0, 3));
    } catch {
      setError("Failed to load pathway details.");
    }
  }, [id]);

  if (error || !pathway) {
    return (
      <div className="min-h-full bg-background p-8 flex items-center justify-center">
        <div className="max-w-md w-full bg-surface border border-border p-6 rounded-lg text-center">
          <AlertTriangle className="h-8 w-8 text-amber-500 mx-auto mb-4" />
          <h2 className="text-lg font-semibold text-foreground mb-2">
            Pathway Unavailable
          </h2>
          <p className="text-sm text-foreground-muted mb-6">
            {error || "Loading..."}
          </p>
          <Link
            href="/results"
            className="inline-flex items-center gap-2 rounded-md bg-foreground px-4 py-2 text-sm font-medium text-background"
          >
            Back to Results
          </Link>
        </div>
      </div>
    );
  }

  const fm = pathway.financial_model;
  const capexBlocked = !fm || fm.capex.status === "unavailable";
  const paybackBlocked = !fm || fm.payback_min_years == null || fm.payback_max_years == null;
  const savingsBlocked = !fm || fm.annual_savings_min_inr == null || fm.annual_savings_max_inr == null;

  return (
    <div className="min-h-full bg-background">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 py-8 sm:py-12">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center gap-2 text-xs text-foreground-muted mb-4">
            <Link
              href="/results"
              className="hover:text-foreground transition-colors flex items-center gap-1"
            >
              <ArrowLeft className="h-3.5 w-3.5" />
              Back to Results
            </Link>
            <span>/</span>
            <span>Pathway Details</span>
          </div>
          <div className="flex items-start justify-between flex-wrap gap-4">
            <div>
              <h1 className="text-2xl font-bold tracking-tight text-foreground">
                {techLabel(pathway.technology_sequence)}
              </h1>
              <p className="text-sm text-foreground-muted mt-2 flex items-center gap-2">
                <CheckCircle2 className="h-4 w-4 text-emerald-500" />
                Technically feasible and matches core factory requirements.
              </p>
            </div>
            <Link
              href="/reports"
              className="inline-flex items-center gap-1.5 rounded-md border border-border px-3 py-1.5 text-xs font-medium text-foreground hover:bg-surface transition-colors"
            >
              <FileText className="h-3.5 w-3.5" />
              Export Report
            </Link>
          </div>
        </div>

        <div className="space-y-8">
          
          {/* Section: Why this pathway? */}
          <section className="bg-surface border border-border rounded-lg p-6">
            <h2 className="text-lg font-semibold text-foreground mb-4 flex items-center gap-2">
              <Info className="h-5 w-5 text-accent" />
              Why this pathway?
            </h2>
            <div className="text-sm text-foreground-muted leading-relaxed space-y-3">
              <p>
                This configuration was ranked highly because it balances technological maturity with a strong operational match to your current temperature profile and fuel setup.
              </p>
              <ul className="list-disc list-inside space-y-1">
                <li>
                  <span className="font-medium text-foreground">Temperature Match:</span> Satisfies the process heat requirements without the need for complex secondary heating cycles.
                </li>
                <li>
                  <span className="font-medium text-foreground">Production Neutrality:</span> Expected to integrate seamlessly with existing downstream infrastructure, maintaining your current throughput and avoiding line shutdowns.
                </li>
                {pathway.reliability?.score_pct && (
                  <li>
                    <span className="font-medium text-foreground">Reliability ({pathway.reliability.score_pct.toFixed(0)}%):</span> Validated against historic failure rates to ensure minimal unplanned downtime.
                  </li>
                )}
              </ul>
            </div>
          </section>

          {/* Section: Financial Reality Check */}
          <section>
            <h2 className="text-lg font-semibold text-foreground mb-4">
              Financial Reality Check
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {/* CAPEX Card */}
              <div className="bg-surface border border-border rounded-lg p-5">
                <RangeDisplay
                  label="CAPEX Estimate"
                  value={
                    !capexBlocked && fm
                      ? [fm.capex.capex_min_inr!, fm.capex.capex_max_inr!]
                      : null
                  }
                  formatAsINR
                  isBlocked={capexBlocked}
                  blockedReason={capexBlocked ? "Not in knowledge base" : undefined}
                  confidence={fm?.capex.confidence ?? undefined}
                />
                <p className="text-xs text-foreground-muted mt-3 pt-3 border-t border-border">
                  {capexBlocked 
                    ? "Vendor quote required to size this equipment for your specific factory throughput." 
                    : "Sourced from historical project data."}
                </p>
              </div>

              {/* Payback Card */}
              <div className="bg-surface border border-border rounded-lg p-5">
                <RangeDisplay
                  label="Simple Payback"
                  value={
                    !paybackBlocked && fm
                      ? [fm.payback_min_years!, fm.payback_max_years!]
                      : null
                  }
                  unit="years"
                  decimalPlaces={1}
                  isBlocked={paybackBlocked}
                  blockedReason={paybackBlocked && capexBlocked ? "Requires CAPEX input" : "Unavailable"}
                />
                <p className="text-xs text-foreground-muted mt-3 pt-3 border-t border-border">
                  {paybackBlocked
                    ? "Calculated automatically once CAPEX is supplied."
                    : "Assumes consistent fuel pricing over the first 5 years."}
                </p>
              </div>

              {/* Savings Card */}
              <div className="bg-surface border border-border rounded-lg p-5">
                <RangeDisplay
                  label="Annual Savings"
                  value={
                    !savingsBlocked && fm
                      ? [fm.annual_savings_min_inr!, fm.annual_savings_max_inr!]
                      : null
                  }
                  formatAsINR
                  isBlocked={savingsBlocked}
                  blockedReason={savingsBlocked && capexBlocked ? "Requires CAPEX input" : "Unavailable"}
                />
                <p className="text-xs text-foreground-muted mt-3 pt-3 border-t border-border">
                  Difference between baseline operational cost and proposed state OPEX.
                </p>
              </div>
            </div>
            
            {/* Any Data Gap Flags for this specific scenario */}
            {fm && fm.data_gap_flags && fm.data_gap_flags.length > 0 && (
              <div className="mt-4 flex flex-wrap gap-2">
                {fm.data_gap_flags.map((flag, idx) => (
                  <span
                    key={idx}
                    className={`inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-[11px] font-medium ${
                      flag.severity === "blocking"
                        ? "bg-amber-100 text-amber-800 dark:bg-amber-900/50 dark:text-amber-200 border border-amber-200 dark:border-amber-800"
                        : "bg-surface-muted text-foreground-muted border border-border"
                    }`}
                  >
                    <AlertTriangle className="h-3 w-3" />
                    {flag.field.replace(/_/g, " ")}: {flag.severity}
                  </span>
                ))}
              </div>
            )}
          </section>

          {/* Section: Why not the others? */}
          {alternatives.length > 0 && (
            <section>
              <h2 className="text-lg font-semibold text-foreground mb-4">
                Why not the alternatives?
              </h2>
              <div className="space-y-3">
                {alternatives.map((alt, idx) => {
                  const altLabel = techLabel(alt.technology_sequence);
                  const isBlocked = alt.financial_model?.firm_recommendation_blocked;
                  return (
                    <div key={idx} className="bg-surface border border-border rounded-lg p-4 flex flex-col sm:flex-row sm:items-start gap-4">
                      <div className="flex-shrink-0 mt-0.5">
                        <XCircle className="h-5 w-5 text-foreground-muted" />
                      </div>
                      <div>
                        <h3 className="text-sm font-semibold text-foreground">{altLabel}</h3>
                        <p className="text-sm text-foreground-muted mt-1 leading-relaxed">
                          {isBlocked 
                            ? "This alternative is structurally feasible, but was ranked lower due to missing CAPEX data (blocking a firm financial comparison). "
                            : "While feasible, this option was ranked lower as it typically introduces higher supply chain risks or has a longer payback period compared to the primary recommendation."}
                        </p>
                        {alt.financial_model?.data_gap_flags && alt.financial_model.data_gap_flags.length > 0 && (
                          <div className="mt-2 text-xs text-amber-600 dark:text-amber-400 font-medium">
                            Flag: {alt.financial_model.data_gap_flags[0].field.replace(/_/g, " ")} data unavailable.
                          </div>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            </section>
          )}

        </div>
      </div>
    </div>
  );
}

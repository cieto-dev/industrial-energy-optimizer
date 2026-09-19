"use client";

import React from "react";
import Link from "next/link";
import {
  CheckCircle2,
  TrendingDown,
  Layers,
  ArrowRight,
} from "lucide-react";
import type {
  BaselineProfile,
  Dashboard,
  ScenarioPathwayEnriched,
} from "@/types/optimization";
import { BaselineSummary } from "./BaselineSummary";

// Import the refactored dashboard components
import { RecommendationCard } from "@/components/dashboard/RecommendationCard";
import { DashboardCharts } from "@/components/dashboard/DashboardCharts";
import { ScenarioComparison } from "@/components/dashboard/ScenarioComparison";
import { RejectionLog } from "@/components/dashboard/RejectionLog";

interface ResultsViewProps {
  dashboard: Dashboard;
  baseline: BaselineProfile;
  factoryLabel?: string;
}

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
    );

  const recommended = rankedPathways[0] ?? null;

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

  // Construct FactoryContext for the components
  const factoryRaw = dashboard.factory as Record<string, unknown> | undefined;
  const factoryContext = {
    state: (factoryRaw?.state as string) || "",
    district: (factoryRaw?.district as string) || "",
    industry: (factoryRaw?.industry as string) || "",
    factory_name: (factoryRaw?.name as string) || "",
    cluster_name: "", // Can be filled if available in future
    special_category: {}, // Can be filled if available in future
  };

  const rejectedTechs = dashboard.technology_assessment?.rejected ?? [];

  return (
    <div className="space-y-12">
      {/* ------------------------------------------------------------------ */}
      {/* 1. Primary Recommendation Card                                     */}
      {/* ------------------------------------------------------------------ */}
      <section>
        <div className="flex items-center gap-2 mb-4">
          <CheckCircle2 className="h-5 w-5 text-emerald-600" />
          <h2 className="text-lg font-bold text-foreground">
            Analysis & Recommendations
          </h2>
        </div>
        <RecommendationCard 
          pathway={recommended} 
          baseline={baseline} 
          factoryContext={factoryContext} 
          rank={1}
        />
        
        {rankedPathways.length === 0 && (
          <p className="text-xs text-foreground-muted mt-2">
            MCDA could not rank pathways — not enough numeric cost/emissions
            data. Resolve CAPEX gaps and re-run.
          </p>
        )}
      </section>

      {/* ------------------------------------------------------------------ */}
      {/* 2. Visual Dashboards (Charts, Sankey, etc.)                        */}
      {/* ------------------------------------------------------------------ */}
      <section>
         <DashboardCharts 
           dashboard={dashboard}
           baseline={baseline}
           factoryContext={factoryContext}
         />
      </section>

      {/* ------------------------------------------------------------------ */}
      {/* 3. Scenario Comparison Matrix                                      */}
      {/* ------------------------------------------------------------------ */}
      <section>
        <div className="flex items-center gap-2 mb-4">
          <Layers className="h-5 w-5 text-emerald-600" />
          <h2 className="text-lg font-bold text-foreground">
            Pathway Comparison
          </h2>
        </div>
        <ScenarioComparison pathways={rankedPathways} />
      </section>

      {/* ------------------------------------------------------------------ */}
      {/* 4. Explainability: Rejection Log (Why not X)                       */}
      {/* ------------------------------------------------------------------ */}
      <section>
        <RejectionLog pathways={rankedPathways} rejectedTechs={rejectedTechs} />
      </section>

      {/* ------------------------------------------------------------------ */}
      {/* 5. Verified Baseline Summary                                       */}
      {/* ------------------------------------------------------------------ */}
      <section>
        <div className="flex items-center gap-2 mb-4">
          <TrendingDown className="h-5 w-5 text-emerald-600" />
          <h2 className="text-lg font-bold text-foreground">
            Verified Baseline
          </h2>
        </div>
        <BaselineSummary baseline={baseline} factoryLabel={factoryLabel} />
      </section>

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

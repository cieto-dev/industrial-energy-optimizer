"use client";

import React from "react";
import {
  Flame,
  Zap,
  CloudCog,
  IndianRupee,
  CheckCircle2,
  AlertTriangle,
} from "lucide-react";
import type { BaselineProfile } from "@/types/optimization";
import { ConfidenceBadge } from "@/components/ui/ConfidenceBadge";
import { RangeDisplay } from "@/components/ui/RangeDisplay";

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function fmtINR(v: number | null | undefined): string {
  if (v == null) return "—";
  if (v >= 1_00_00_000) return `₹${(v / 1_00_00_000).toFixed(1)} Cr`;
  if (v >= 1_00_000) return `₹${(v / 1_00_000).toFixed(1)} L`;
  return `₹${v.toLocaleString("en-IN")}`;
}

function fmtNum(v: number | null | undefined, decimals = 0): string {
  if (v == null) return "—";
  return v.toFixed(decimals);
}

// ---------------------------------------------------------------------------
// Stat cell (immutable — only shows real numbers)
// ---------------------------------------------------------------------------

interface StatCellProps {
  label: string;
  value: string;
  unit?: string;
  sub?: string;
  icon?: React.ReactNode;
  confidence?: "High" | "Medium" | "Low";
  isNull?: boolean;
}

function StatCell({
  label,
  value,
  unit,
  sub,
  icon,
  confidence,
  isNull,
}: StatCellProps) {
  return (
    <div className="flex flex-col gap-1">
      <div className="flex items-center gap-1.5 text-xs font-medium uppercase tracking-wide text-foreground-muted">
        {icon && <span className="opacity-70">{icon}</span>}
        {label}
      </div>
      <div className="flex items-baseline gap-1.5 flex-wrap">
        <span
          className={`text-2xl font-bold tabular-nums ${
            isNull ? "text-foreground-muted" : "text-foreground"
          }`}
        >
          {isNull ? "—" : value}
        </span>
        {!isNull && unit && (
          <span className="text-sm text-foreground-muted">{unit}</span>
        )}
        {confidence && !isNull && (
          <ConfidenceBadge confidence={confidence} className="self-center" />
        )}
      </div>
      {sub && (
        <p className="text-xs text-foreground-muted leading-snug">{sub}</p>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

interface BaselineSummaryProps {
  baseline: BaselineProfile;
  factoryLabel?: string;
}

/**
 * BaselineSummary
 *
 * Renders the core verified baseline numbers. Used in both the blocked state
 * (to show the user the system did real work) and the normal results view
 * (as the comparison baseline).
 *
 * All numbers come directly from the API. None are fabricated here.
 */
export function BaselineSummary({
  baseline,
  factoryLabel,
}: BaselineSummaryProps) {
  const hasWarnings =
    Array.isArray(baseline.data_quality_warnings) &&
    baseline.data_quality_warnings.length > 0;

  const isBlocked = baseline.firm_recommendation_blocked;

  return (
    <div className="border border-border rounded-lg overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between px-5 py-3.5 border-b border-border bg-surface">
        <div className="flex items-center gap-2.5">
          <div className="h-2 w-2 rounded-full bg-emerald-500" />
          <h3 className="text-sm font-semibold text-foreground">
            Verified Baseline Profile
            {factoryLabel && (
              <span className="font-normal text-foreground-muted ml-1.5">
                — {factoryLabel}
              </span>
            )}
          </h3>
        </div>
        {isBlocked ? (
          <span className="inline-flex items-center gap-1 text-xs font-medium text-amber-600 dark:text-amber-400">
            <AlertTriangle className="h-3.5 w-3.5" />
            Baseline quality gate: pending
          </span>
        ) : (
          <span className="inline-flex items-center gap-1 text-xs font-medium text-emerald-600 dark:text-emerald-400">
            <CheckCircle2 className="h-3.5 w-3.5" />
            Quality gate passed
          </span>
        )}
      </div>

      {/* Stats grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-4 p-5">
        <div className="p-2">
          <StatCell
            label="Annual energy cost"
            value={fmtINR(baseline.annual_total_energy_cost_inr)}
            icon={<IndianRupee className="h-3.5 w-3.5" />}
            confidence="High"
            isNull={baseline.annual_total_energy_cost_inr == null}
            sub="Fuel + electricity"
          />
        </div>
        <div className="p-2">
          <StatCell
            label="Annual CO₂"
            value={fmtNum(baseline.annual_co2_tonnes, 0)}
            unit="tCO₂"
            icon={<CloudCog className="h-3.5 w-3.5" />}
            confidence={
              baseline.annual_fuel_co2_tonnes != null ? "High" : undefined
            }
            isNull={baseline.annual_co2_tonnes == null}
            sub="Scope 1 + 2 combustion"
          />
        </div>
        <div className="p-2">
          <StatCell
            label="Fuel cost"
            value={fmtINR(baseline.annual_fuel_cost_inr)}
            icon={<Flame className="h-3.5 w-3.5" />}
            isNull={baseline.annual_fuel_cost_inr == null}
          />
        </div>
        <div className="p-2">
          <StatCell
            label="Electricity cost"
            value={fmtINR(baseline.annual_electricity_cost_inr)}
            icon={<Zap className="h-3.5 w-3.5" />}
            isNull={baseline.annual_electricity_cost_inr == null}
            sub={
              baseline.electricity_cost_coverage_limitation ??
              baseline.electricity_cost_coverage_status ??
              undefined
            }
          />
        </div>
      </div>

      {/* Assumptions / warnings footer */}
      {(hasWarnings ||
        (Array.isArray(baseline.calculation_assumptions) &&
          baseline.calculation_assumptions.length > 0)) && (
        <div className="px-5 py-3 border-t border-border bg-surface-muted">
          {hasWarnings && (
            <div className="flex items-start gap-2 text-xs text-amber-700 dark:text-amber-400 mb-1">
              <AlertTriangle className="h-3.5 w-3.5 flex-shrink-0 mt-0.5" />
              <span>
                {baseline.data_quality_warnings
                  .slice(0, 3)
                  .map((w) => (typeof w === "string" ? w : JSON.stringify(w)))
                  .join(" · ")}
              </span>
            </div>
          )}
          {Array.isArray(baseline.calculation_assumptions) &&
            baseline.calculation_assumptions.length > 0 && (
              <p className="text-xs text-foreground-muted">
                <span className="font-medium">Assumptions: </span>
                {baseline.calculation_assumptions.slice(0, 3).join(" · ")}
              </p>
            )}
        </div>
      )}
    </div>
  );
}

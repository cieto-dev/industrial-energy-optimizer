"use client";

import React from "react";
import type { ConfidenceLevel } from "@/types/optimization";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface ConfidenceBadgeProps {
  confidence: ConfidenceLevel;
  /** Optional prefix label, e.g. "NCV:" or "Source:" */
  label?: string;
  /** Tooltip text shown on hover (title attribute). */
  tooltip?: string;
  /** Extra CSS classes to forward to the wrapper span. */
  className?: string;
}

// ---------------------------------------------------------------------------
// Style map — calm, technical palette. Not marketing colours.
//   High  → muted emerald (positive signal, not loud green)
//   Medium → amber (caution, not warning)
//   Low   → muted rose/slate (concern, not alarming red)
// ---------------------------------------------------------------------------

const STYLE_MAP: Record<
  ConfidenceLevel,
  { dot: string; pill: string; text: string }
> = {
  High: {
    dot: "bg-emerald-500",
    pill: "bg-emerald-50 border border-emerald-200 text-emerald-800 dark:bg-emerald-950 dark:border-emerald-800 dark:text-emerald-300",
    text: "High",
  },
  Medium: {
    dot: "bg-amber-400",
    pill: "bg-amber-50 border border-amber-200 text-amber-800 dark:bg-amber-950 dark:border-amber-800 dark:text-amber-300",
    text: "Medium",
  },
  Low: {
    dot: "bg-rose-400",
    pill: "bg-rose-50 border border-rose-200 text-rose-800 dark:bg-rose-950 dark:border-rose-800 dark:text-rose-300",
    text: "Low",
  },
};

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

/**
 * ConfidenceBadge
 *
 * A small, inline badge that communicates data confidence without
 * marketing drama. Designed to sit next to any numeric metric.
 *
 * @example
 *   <ConfidenceBadge confidence="High" label="NCV:" tooltip="IPCC 2006 default" />
 *   <ConfidenceBadge confidence="Low" />
 */
export function ConfidenceBadge({
  confidence,
  label,
  tooltip,
  className = "",
}: ConfidenceBadgeProps) {
  const styles = STYLE_MAP[confidence];

  return (
    <span
      className={`inline-flex items-center gap-1.5 ${className}`}
      title={tooltip}
    >
      {label && (
        <span className="text-xs text-foreground-muted font-medium">
          {label}
        </span>
      )}
      <span
        className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[11px] font-medium leading-none ${styles.pill}`}
      >
        <span
          className={`inline-block h-1.5 w-1.5 rounded-full ${styles.dot} flex-shrink-0`}
          aria-hidden="true"
        />
        {styles.text}
      </span>
    </span>
  );
}

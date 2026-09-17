"use client";

import React from "react";
import { AlertCircle } from "lucide-react";
import type { ConfidenceLevel } from "@/types/optimization";
import { ConfidenceBadge } from "./ConfidenceBadge";

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

/**
 * Format a single INR value compactly.
 * ≥ 1 Cr → "X.X Cr", ≥ 1 L → "X.X L", else "₹N"
 */
function formatINR(value: number): string {
  if (value >= 1_00_00_000) {
    return `₹${(value / 1_00_00_000).toFixed(1)} Cr`;
  }
  if (value >= 1_00_000) {
    return `₹${(value / 1_00_000).toFixed(1)} L`;
  }
  return `₹${value.toLocaleString("en-IN")}`;
}

/**
 * Format a range [low, high] into a readable string.
 * If low === high (single-point), returns just one value.
 */
function formatRange(
  low: number,
  high: number,
  unit?: string,
  formatter?: (v: number) => string
): string {
  const fmt = formatter ?? ((v: number) => v.toLocaleString("en-IN"));
  const suffix = unit ? ` ${unit}` : "";

  if (Math.abs(high - low) < 0.001) {
    return `${fmt(low)}${suffix}`;
  }
  return `${fmt(low)}${suffix} – ${fmt(high)}${suffix}`;
}

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

type RangeValue = [number, number] | null;

export interface RangeDisplayProps {
  /**
   * The numeric range [low, high].
   * Pass null when data is genuinely unavailable (CAPEX not in KB, etc.).
   */
  value: RangeValue;

  /** Unit label appended after each bound (e.g. "years", "tCO₂"). */
  unit?: string;

  /** Descriptive label rendered above or beside the range. */
  label?: string;

  /**
   * When true, renders the blocked state even if `value` is non-null.
   * Use this when the economics engine has set firm_recommendation_blocked.
   */
  isBlocked?: boolean;

  /**
   * Explanation shown in the blocked state.
   * Default: "Data not available"
   */
  blockedReason?: string;

  /**
   * Whether to format numbers as INR (₹X L / ₹X Cr).
   * When false, uses plain toLocaleString.
   */
  formatAsINR?: boolean;

  /**
   * Decimal places when not using INR formatting.
   * Default: 1
   */
  decimalPlaces?: number;

  /** Optional confidence badge rendered alongside the range. */
  confidence?: ConfidenceLevel;

  /** Extra CSS classes for the wrapper element. */
  className?: string;
}

// ---------------------------------------------------------------------------
// Sub-components
// ---------------------------------------------------------------------------

/** Rendered when value is null or isBlocked is true. */
function BlockedState({ reason }: { reason: string }) {
  return (
    <span className="inline-flex items-center gap-1.5 text-foreground-muted">
      <AlertCircle
        className="h-3.5 w-3.5 text-amber-500 flex-shrink-0"
        aria-hidden="true"
      />
      <span className="text-sm font-medium">{reason}</span>
    </span>
  );
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

/**
 * RangeDisplay
 *
 * Renders a [low, high] numeric range honestly.
 * - Valid range → "₹60L – ₹95L" or "3.2 – 6.8 years"
 * - Null / blocked → shows a clear unavailable message (never a fake number).
 *
 * @example
 *   // CAPEX range
 *   <RangeDisplay
 *     label="Estimated CAPEX"
 *     value={null}
 *     isBlocked
 *     blockedReason="CAPEX not in knowledge base"
 *     formatAsINR
 *   />
 *
 *   // Payback range
 *   <RangeDisplay
 *     label="Simple payback"
 *     value={[3.2, 6.8]}
 *     unit="years"
 *     confidence="Medium"
 *   />
 *
 *   // Annual savings
 *   <RangeDisplay
 *     label="Annual savings"
 *     value={[4500000, 6900000]}
 *     formatAsINR
 *     confidence="High"
 *   />
 */
export function RangeDisplay({
  value,
  unit,
  label,
  isBlocked = false,
  blockedReason = "Data not available",
  formatAsINR = false,
  decimalPlaces = 1,
  confidence,
  className = "",
}: RangeDisplayProps) {
  const showBlocked = isBlocked || value === null;

  const formattedRange =
    !showBlocked && value !== null
      ? formatAsINR
        ? formatRange(value[0], value[1], undefined, formatINR)
        : formatRange(
            value[0],
            value[1],
            unit,
            (v) => v.toFixed(decimalPlaces)
          )
      : null;

  return (
    <div className={`flex flex-col gap-0.5 ${className}`}>
      {label && (
        <span className="text-xs font-medium uppercase tracking-wide text-foreground-muted">
          {label}
        </span>
      )}

      <div className="flex items-baseline gap-2 flex-wrap">
        {showBlocked ? (
          <BlockedState reason={blockedReason} />
        ) : (
          <>
            <span className="text-base font-semibold text-foreground tabular-nums">
              {formattedRange}
              {/* Unit suffix for non-INR formatting (already in formattedRange for INR) */}
              {!formatAsINR && unit && (
                <span className="ml-1 text-sm font-normal text-foreground-muted">
                  {unit}
                </span>
              )}
            </span>

            {confidence && (
              <ConfidenceBadge
                confidence={confidence}
                className="self-center"
              />
            )}
          </>
        )}
      </div>
    </div>
  );
}

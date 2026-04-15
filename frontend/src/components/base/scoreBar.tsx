/**
 * ScoreBar — horizontal 0–100 bar with threshold-driven colour.
 *
 * The "label | filled pill | number" row from LossTab's group frequency /
 * severity indicators. Configurable thresholds and colour stops so the
 * same primitive can render "higher is worse" (frequency) and "higher is
 * better" (any positive metric).
 */

"use client";

import "@/app/globals.css";
import { formatNumber } from "@/lib/format";

export interface ScoreBarThreshold {
  /** Inclusive upper bound. First matching entry wins. */
  at: number;
  /** CSS value for `backgroundColor`, e.g. `"var(--dsi-negative)"`. */
  color: string;
}

export interface ScoreBarProps {
  /** Numeric score. Clamped to [min, max] for the bar width. */
  value: number;
  /** Label on the left. Optional. */
  label?: React.ReactNode;
  /**
   * Thresholds from lowest `at` to highest. The first whose `at >= value`
   * chooses the colour. Default: >70 negative, >40 warning, else positive.
   */
  thresholds?: ScoreBarThreshold[];
  /** Domain min. Default 0. */
  min?: number;
  /** Domain max. Default 100. */
  max?: number;
  /** Decimals for the numeric readout. Default 1. */
  decimals?: number;
  /** Hide the numeric readout on the right. Default false. */
  hideValue?: boolean;
  /** Label column width — Tailwind class e.g. "w-10". Default "w-10". */
  labelWidth?: string;
}

const DEFAULT_THRESHOLDS: ScoreBarThreshold[] = [
  { at: 40, color: "var(--dsi-positive)" },
  { at: 70, color: "var(--dsi-warning)" },
  { at: Infinity, color: "var(--dsi-negative)" },
];

function pickColor(value: number, thresholds: ScoreBarThreshold[]): string {
  for (const t of thresholds) {
    if (value <= t.at) return t.color;
  }
  return thresholds[thresholds.length - 1]?.color ?? "var(--dsi-muted)";
}

export default function ScoreBar({
  value,
  label,
  thresholds = DEFAULT_THRESHOLDS,
  min = 0,
  max = 100,
  decimals = 1,
  hideValue = false,
  labelWidth = "w-10",
}: ScoreBarProps) {
  const span = max - min || 1;
  const pct = Math.min(100, Math.max(2, ((value - min) / span) * 100));
  const color = pickColor(value, thresholds);

  return (
    <div className="flex items-center gap-2">
      {label !== undefined && (
        <span className={`text-[10px] opacity-50 shrink-0 ${labelWidth}`}>{label}</span>
      )}
      <div className="flex-1 h-1.5 bg-dsi-background rounded-full overflow-hidden">
        <div
          className="h-full rounded-full transition-all"
          style={{ width: `${pct}%`, backgroundColor: color }}
        />
      </div>
      {!hideValue && (
        <span className="text-[10px] font-bold w-8 text-right">
          {formatNumber(value, decimals)}
        </span>
      )}
    </div>
  );
}

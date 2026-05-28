"use client";

import { cn } from "@/lib/utils";

interface CohortBarProps {
  /** Subject value. */
  value: number;
  /** Cohort median. */
  median: number;
  /** Cohort top-decile mark. */
  topDecile: number;
  /** [min, max] range of the cohort. */
  range: [number, number];
  /** Label shown on the YOU pin. */
  youLabel?: string;
  className?: string;
}

/**
 * Horizontal distribution strip: full range with a green top-decile band,
 * a vertical median tick, and a labeled YOU pin. Custom SVG — recharts
 * doesn't give us this exact shape without a lot of overrides.
 */
export function CohortBar({
  value,
  median,
  topDecile,
  range,
  youLabel = "YOU",
  className,
}: CohortBarProps) {
  const [lo, hi] = range;
  const span = hi - lo || 1;
  const pct = (v: number) => ((v - lo) / span) * 100;
  const youAt = Math.max(2, Math.min(98, pct(value)));
  const medianAt = Math.max(0, Math.min(100, pct(median)));
  const topAt = Math.max(0, Math.min(100, pct(topDecile)));

  return (
    <div className={cn("relative", className)}>
      <div className="relative h-3 overflow-hidden rounded-full bg-surface-sunken">
        {/* Top-decile band */}
        <div
          className="absolute inset-y-0 bg-pos-soft"
          style={{ left: `${topAt}%`, right: 0 }}
        />
        {/* Median tick */}
        <div
          className="absolute inset-y-0 w-px bg-ink-mute"
          style={{ left: `${medianAt}%` }}
        />
      </div>
      {/* YOU pin */}
      <div
        className="absolute -top-1.5 flex -translate-x-1/2 flex-col items-center"
        style={{ left: `${youAt}%` }}
      >
        <div className="rounded-full bg-info px-1.5 py-0.5 text-[10px] font-semibold leading-none text-white">
          {youLabel}
        </div>
        <div className="h-3 w-px bg-info" />
      </div>
      <div className="mt-1.5 flex justify-between text-[10px] text-ink-mute tabular-nums">
        <span>{lo}</span>
        <span>median {median}</span>
        <span>top 10% {topDecile}</span>
        <span>{hi}</span>
      </div>
    </div>
  );
}

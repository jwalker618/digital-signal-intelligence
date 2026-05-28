"use client";

import { cn } from "@/lib/utils";
import { formatCurrency } from "@/lib/format";

export interface PremiumSlice {
  /** Display label for the line. */
  line: string;
  amount: number;
  /** Optional color override; otherwise picked from LINE_COLOR. */
  color?: string;
}

/**
 * Color per coverage line — single source of truth. Tints are deliberately
 * muted so the stacked bar reads as a textured whole, not a rainbow.
 * Unknown lines fall back to --color-ink-mute.
 */
const LINE_COLOR: Record<string, string> = {
  Cyber: "var(--color-info)",
  "Professional Indemnity": "var(--color-aux)",
  "D&O": "var(--color-pos)",
  Property: "var(--color-warn)",
  "General Liability": "var(--color-spot)",
  "Workers Compensation": "var(--color-rule-strong)",
  Auto: "var(--color-ink-soft)",
  Umbrella: "var(--color-neg)",
  Crime: "var(--color-info-deep)",
  EPL: "var(--color-aux)",
  "Product Liability": "var(--color-warn)",
};

function colorFor(slice: PremiumSlice): string {
  return slice.color ?? LINE_COLOR[slice.line] ?? "var(--color-ink-mute)";
}

function compactUsd(n: number): string {
  if (Math.abs(n) >= 1_000_000) return `$${(n / 1_000_000).toFixed(1)}M`;
  if (Math.abs(n) >= 1_000) return `$${Math.round(n / 1_000)}K`;
  return formatCurrency(n);
}

interface PremiumBreakdownProps {
  slices: PremiumSlice[];
  /** Show this many; overflow folds into "+N more". */
  maxVisible?: number;
  /** Height of the stacked bar in px. */
  barHeight?: number;
  className?: string;
}

export function PremiumBreakdown({
  slices,
  maxVisible = 4,
  barHeight = 14,
  className,
}: PremiumBreakdownProps) {
  const sorted = [...slices].sort((a, b) => b.amount - a.amount);
  const total = sorted.reduce((s, p) => s + p.amount, 0);
  const visible = sorted.slice(0, maxVisible);
  const rest = sorted.slice(maxVisible);
  const restAmount = rest.reduce((s, p) => s + p.amount, 0);

  return (
    <div className={cn("flex flex-col gap-3", className)}>
      <div
        className="flex w-full overflow-hidden rounded-full bg-surface-sunken"
        style={{ height: barHeight }}
        role="img"
        aria-label={`Premium breakdown, total ${compactUsd(total)}`}
      >
        {visible.map((s) => (
          <div
            key={s.line}
            style={{
              width: `${(s.amount / total) * 100}%`,
              background: colorFor(s),
            }}
            title={`${s.line} — ${formatCurrency(s.amount)}`}
          />
        ))}
        {restAmount > 0 && (
          <div
            style={{
              width: `${(restAmount / total) * 100}%`,
              background: "var(--color-ink-mute)",
            }}
            title={`+${rest.length} more — ${formatCurrency(restAmount)}`}
          />
        )}
      </div>
      <ul className="grid grid-cols-2 gap-x-4 gap-y-1 text-[12px]">
        {visible.map((s) => (
          <li key={s.line} className="flex items-center gap-2">
            <span
              className="inline-block h-2 w-2 rounded-full"
              style={{ background: colorFor(s) }}
            />
            <span className="flex-1 text-ink-soft">{s.line}</span>
            <span className="font-semibold text-ink tabular-nums">
              {compactUsd(s.amount)}
            </span>
          </li>
        ))}
        {rest.length > 0 && (
          <li className="flex items-center gap-2">
            <span className="inline-block h-2 w-2 rounded-full bg-ink-mute" />
            <span className="flex-1 text-ink-soft">+{rest.length} more</span>
            <span className="font-semibold text-ink tabular-nums">
              {compactUsd(restAmount)}
            </span>
          </li>
        )}
      </ul>
    </div>
  );
}

"use client";

import { useMemo } from "react";
import { cn } from "@/lib/utils";
import { formatCurrency } from "@/lib/format";

/**
 * Chart-local waterfall item. Pages map their domain drivers (strengths /
 * drags / opportunities) into this before passing it in.
 */
export interface WaterfallItem {
  id: string;
  label: string;
  /** Signed dollar value: base + final are absolute; pos/opp are deltas. */
  value: number;
  type: "base" | "pos" | "opp" | "final";
}

const TYPE_COLOR: Record<WaterfallItem["type"], string> = {
  base: "var(--color-ink)",
  pos: "var(--color-pos)",
  opp: "var(--color-spot)",
  final: "var(--color-info)",
};

function compactUsd(n: number): string {
  const abs = Math.abs(n);
  const sign = n < 0 ? "−" : "";
  if (abs >= 1_000_000) return `${sign}$${(abs / 1_000_000).toFixed(1)}M`;
  if (abs >= 1_000) return `${sign}$${Math.round(abs / 1_000)}K`;
  return formatCurrency(n);
}

/**
 * Walk items left-to-right tracking the running cumulative. Base/final draw
 * from 0; intermediate steps draw between consecutive cumulatives.
 */
function waterfallRunning(items: WaterfallItem[]) {
  let acc = 0;
  return items.map((it) => {
    if (it.type === "base" || it.type === "final") {
      acc = it.value;
      return { id: it.id, start: 0, end: it.value, type: it.type };
    }
    const start = acc;
    const end = acc + it.value;
    acc = end;
    return { id: it.id, start, end, type: it.type };
  });
}

interface WaterfallProps {
  items: WaterfallItem[];
  height?: number;
}

/**
 * Premium build-up waterfall. Base bar, then each strength/opportunity step,
 * then a final total bar. Custom SVG so we can render connectors between
 * steps — recharts can't draw cross-bar connectors out of the box.
 */
export function Waterfall({ items, height = 260 }: WaterfallProps) {
  const segments = useMemo(() => waterfallRunning(items), [items]);
  const maxVal = Math.max(...segments.flatMap((s) => [s.start, s.end]));
  const labels = items;

  // Layout
  const padX = 40;
  const padTop = 16;
  const padBottom = 56;
  const innerHeight = height - padTop - padBottom;
  const barWidth = 56;
  const gap = 24;
  const totalWidth = padX * 2 + segments.length * barWidth + (segments.length - 1) * gap;

  const yOf = (v: number) =>
    padTop + innerHeight - (v / maxVal) * innerHeight;

  return (
    <div className="overflow-x-auto">
      <svg
        viewBox={`0 0 ${totalWidth} ${height}`}
        width="100%"
        height={height}
        role="img"
        aria-label="Premium waterfall"
      >
        {/* Baseline rule */}
        <line
          x1={padX}
          x2={totalWidth - padX}
          y1={padTop + innerHeight}
          y2={padTop + innerHeight}
          stroke="var(--color-rule)"
        />
        {segments.map((s, i) => {
          const x = padX + i * (barWidth + gap);
          const top = Math.min(yOf(s.start), yOf(s.end));
          const bottom = Math.max(yOf(s.start), yOf(s.end));
          const barH = Math.max(2, bottom - top);
          const fill = TYPE_COLOR[s.type];
          const label = labels[i]!;
          const valueText =
            s.type === "base" || s.type === "final"
              ? compactUsd(label.value)
              : `${label.value > 0 ? "+" : ""}${compactUsd(label.value)}`;
          // Connector to next segment
          const next = segments[i + 1];
          return (
            <g key={s.id}>
              <rect
                x={x}
                y={top}
                width={barWidth}
                height={barH}
                rx={4}
                fill={fill}
                opacity={s.type === "opp" ? 0.9 : 1}
              />
              {/* Bar label (value) */}
              <text
                x={x + barWidth / 2}
                y={top - 6}
                textAnchor="middle"
                fontSize={11}
                fontWeight={700}
                fill="var(--color-ink)"
                className="tabular-nums"
              >
                {valueText}
              </text>
              {/* Axis label */}
              <text
                x={x + barWidth / 2}
                y={padTop + innerHeight + 18}
                textAnchor="middle"
                fontSize={11}
                fill="var(--color-ink-soft)"
              >
                {label.label}
              </text>
              {next && (
                <line
                  x1={x + barWidth}
                  x2={x + barWidth + gap}
                  y1={yOf(s.end)}
                  y2={yOf(s.end)}
                  stroke="var(--color-rule-strong)"
                  strokeDasharray="2 3"
                />
              )}
            </g>
          );
        })}
      </svg>
    </div>
  );
}

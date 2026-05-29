"use client";

import { memo } from "react";
import {
  Area,
  AreaChart,
  CartesianGrid,
  ReferenceDot,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
/**
 * Chart-local input shape. Pages map their domain score history into this
 * before passing it in — keeps the chart decoupled from API types.
 */
export interface ScorePoint {
  label: string;
  value: number;
  /** Mark a point for the highlight dot: previous-period vs current. */
  marker?: "prev" | "now";
}

interface ScoreHistoryProps {
  history: ScorePoint[];
  color?: string;
  height?: number;
}

/**
 * Annotated quarterly score history. Highlights the `prev` and `now` points
 * so the headline narrative ("724 → 735") is grounded in the chart.
 */
export const ScoreHistory = memo(function ScoreHistory({
  history,
  color = "var(--color-info)",
  height = 220,
}: ScoreHistoryProps) {
  const data = history.map((p) => ({
    label: p.label,
    value: p.value,
    marker: p.marker,
  }));
  const min = Math.min(...data.map((d) => d.value));
  const max = Math.max(...data.map((d) => d.value));
  const pad = Math.max(20, Math.round((max - min) * 0.15));
  const prev = data.find((d) => d.marker === "prev");
  const now = data.find((d) => d.marker === "now");

  return (
    <div style={{ height }}>
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={data} margin={{ top: 16, right: 24, left: 0, bottom: 8 }}>
          <defs>
            <linearGradient id="scorefill" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor={color} stopOpacity={0.22} />
              <stop offset="100%" stopColor={color} stopOpacity={0} />
            </linearGradient>
          </defs>
          <CartesianGrid stroke="var(--color-rule)" vertical={false} />
          <XAxis
            dataKey="label"
            tick={{ fontSize: 11, fill: "var(--color-ink-mute)" }}
            tickLine={false}
            axisLine={{ stroke: "var(--color-rule)" }}
            interval="preserveStartEnd"
          />
          <YAxis
            domain={[min - pad, max + pad]}
            tick={{ fontSize: 11, fill: "var(--color-ink-mute)" }}
            tickLine={false}
            axisLine={false}
            width={36}
          />
          <Tooltip
            cursor={{ stroke: "var(--color-rule-strong)", strokeDasharray: 3 }}
            contentStyle={{
              background: "var(--color-surface)",
              border: "1px solid var(--color-rule)",
              borderRadius: 10,
              fontSize: 12,
            }}
            labelStyle={{ color: "var(--color-ink-soft)" }}
            itemStyle={{ color: "var(--color-ink)" }}
            formatter={(v: number) => [v, "Score"]}
          />
          <Area
            type="monotone"
            dataKey="value"
            stroke={color}
            strokeWidth={2}
            fill="url(#scorefill)"
            isAnimationActive={false}
          />
          {prev && (
            <ReferenceDot
              x={prev.label}
              y={prev.value}
              r={5}
              fill="var(--color-surface)"
              stroke={color}
              strokeWidth={2}
              label={{
                position: "top",
                value: `${prev.value}`,
                fill: "var(--color-ink-mute)",
                fontSize: 11,
              }}
            />
          )}
          {now && (
            <ReferenceDot
              x={now.label}
              y={now.value}
              r={6}
              fill={color}
              stroke="var(--color-surface)"
              strokeWidth={2}
              label={{
                position: "top",
                value: `${now.value}`,
                fill: "var(--color-ink)",
                fontSize: 12,
                fontWeight: 700,
              }}
            />
          )}
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
});

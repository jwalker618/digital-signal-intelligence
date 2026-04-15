"use client";

/**
 * BenchmarkBarChart — categorical bars with one subject bar highlighted and
 * a dashed reference line at the subject's own value.
 *
 * Used across LossTab (Cohort Benchmarking) and ExposureTab (Band
 * Benchmarking, Exposure by Final Tier). All three share the same layout:
 * bars coloured as peer except the bar whose category == subject, a
 * reference line for the subject's value with a right-positioned label,
 * and an optional `n=...` count annotation above each bar.
 */

import {
  BarChart,
  Bar,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip as RechartsTooltip,
  ResponsiveContainer,
  ReferenceLine,
  Label,
} from "recharts";

import { formatNumber } from "@/lib/format";
import { tooltipStyle } from "@/lib/chartConfig";

export interface BenchmarkBarChartProps<T extends Record<string, unknown>> {
  data: T[];
  /** Field name on `T` for the x-axis category. */
  categoryKey: keyof T & string;
  /** Field name on `T` for the bar value. */
  valueKey: keyof T & string;
  /**
   * Category value that should be highlighted as "the subject" — matched
   * against `data[i][categoryKey]`. Bars match → subject colour, else peer.
   */
  subjectCategory?: string | number | null;
  /** Subject's own numeric value (for the reference line). */
  subjectValue?: number;
  /** Decimal places used in the reference-line label. Default 3. */
  subjectValueDecimals?: number;
  /**
   * Optional field on `T` for per-bar peer count — if provided, each bar
   * gets an `n=<count>` annotation above it and the tooltip label shows
   * `Category (n=N)`.
   */
  peerCountKey?: keyof T & string;
  /** Human-readable name for the bar value in the tooltip. */
  valueName?: string;
  /** Format the bar value in the tooltip. Default: 3 decimals + "x". */
  formatValue?: (value: number) => string;
  /** Y-axis domain override. Default "auto", "auto". */
  yDomain?: [number | "auto", number | "auto"];
  /** Truncate long category labels to this length. Default 15. */
  maxCategoryLength?: number;
  /** Chart height in px. Default 300. */
  height?: number;
  /** Shown when `data` is empty. */
  emptyMessage?: string;
}

export default function BenchmarkBarChart<T extends Record<string, unknown>>({
  data,
  categoryKey,
  valueKey,
  subjectCategory,
  subjectValue,
  subjectValueDecimals = 3,
  peerCountKey,
  valueName,
  formatValue = (v) => `${formatNumber(v, 3)}x`,
  yDomain = ["auto", "auto"],
  maxCategoryLength = 15,
  height = 300,
  emptyMessage = "No data available.",
}: BenchmarkBarChartProps<T>) {
  if (!data || data.length === 0) {
    return (
      <div
        className="flex items-center justify-center opacity-50 italic text-sm"
        style={{ height }}
      >
        {emptyMessage}
      </div>
    );
  }

  return (
    <div className="pl-dsi-pad pr-dsi-pad w-full" style={{ height }}>
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data} margin={{ top: 0, right: 0, bottom: 20, left: -20 }}>
          <CartesianGrid
            strokeDasharray="3 3"
            vertical={false}
            stroke="var(--dsi-chart-grid)"
            opacity={0.5}
          />
          <XAxis
            dataKey={categoryKey}
            stroke="var(--dsi-chart-axis)"
            tick={{ fill: "var(--dsi-chart-axis)", fontSize: 11 }}
            interval={0}
            tickFormatter={(val: string) =>
              typeof val === "string" && val.length > maxCategoryLength
                ? val.substring(0, maxCategoryLength) + "..."
                : val
            }
          />
          <YAxis
            stroke="var(--dsi-chart-axis)"
            tick={{ fill: "var(--dsi-chart-axis)", fontSize: 12 }}
            domain={yDomain}
          />
          <RechartsTooltip
            contentStyle={tooltipStyle}
            cursor={{ fill: "var(--dsi-chart-tooltip-bg)", opacity: 0.4 }}
            formatter={(value: unknown, name: string) => [
              formatValue(Number(value)),
              valueName ?? name,
            ]}
            labelFormatter={(label) => {
              if (!peerCountKey) return String(label);
              const match = data.find((d) => d[categoryKey] === label);
              const n = match?.[peerCountKey] as number | undefined;
              return n !== undefined ? `${label} (n=${n})` : String(label);
            }}
          />

          {subjectValue !== undefined && (
            <ReferenceLine
              y={subjectValue}
              stroke="var(--dsi-chart-subject)"
              strokeDasharray="6 3"
              strokeWidth={2}
            >
              <Label
                value={`Subject ${formatNumber(subjectValue, subjectValueDecimals)}`}
                position="right"
                fill="var(--dsi-chart-subject)"
                fontSize={11}
              />
            </ReferenceLine>
          )}

          <Bar
            dataKey={valueKey}
            radius={[4, 4, 0, 0]}
            label={
              peerCountKey
                ? // eslint-disable-next-line @typescript-eslint/no-explicit-any
                  ({ x, y, width, index }: any) => {
                    const entry = data[index];
                    const n = entry?.[peerCountKey] as number | undefined;
                    if (n === undefined) return <g />;
                    return (
                      <text
                        x={x + width / 2}
                        y={y - 6}
                        textAnchor="middle"
                        fill="var(--dsi-chart-axis)"
                        fontSize={10}
                      >
                        n={n}
                      </text>
                    );
                  }
                : undefined
            }
          >
            {data.map((entry, index) => (
              <Cell
                key={`cell-${index}`}
                fill={
                  entry[categoryKey] === subjectCategory
                    ? "var(--dsi-chart-subject)"
                    : "var(--dsi-chart-peer)"
                }
              />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

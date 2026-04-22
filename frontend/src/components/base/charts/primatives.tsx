"use client";

import {
  BarChart,
  Bar,
  Cell,
  ScatterChart,
  Scatter,
  XAxis,
  YAxis,
  Label,
  CartesianGrid,
  Tooltip as RechartsTooltip,
  ResponsiveContainer,
  ReferenceLine,
} from "recharts";

import { formatNumber } from "@/lib/format";
import { getDecisionColor, tooltipStyle } from "@/lib/chartConfig";

/** BENCHMARK CHART---------------------------------------------------------------------------------------------- */

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

/**
 * Used across LossTab (Cohort Benchmarking) and ExposureTab (Band
 * Benchmarking, Exposure by Final Tier). All three share the same layout:
 * bars coloured as peer except the bar whose category == subject, a
 * reference line for the subject's value with a right-positioned label,
 * and an optional `n=...` count annotation above each bar.
 */
export const BenchmarkBarChart = <T extends Record<string, unknown>>({
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
}: BenchmarkBarChartProps<T>) => {
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
            stroke="var(--dsi-outline)"
            opacity={0.5}
          />
          <XAxis
            dataKey={categoryKey}
            stroke="var(--dsi-contrast-background)"
            tick={{ fill: "var(--dsi-contrast-background)", fontSize: 11 }}
            interval={0}
            tickFormatter={(val: string) =>
              typeof val === "string" && val.length > maxCategoryLength
                ? val.substring(0, maxCategoryLength) + "..."
                : val
            }
          />
          <YAxis
            stroke="var(--dsi-contrast-background)"
            tick={{ fill: "var(--dsi-contrast-background)", fontSize: 12 }}
            domain={yDomain}
          />
          <RechartsTooltip
            contentStyle={tooltipStyle}
            cursor={{ fill: "var(--dsi-selected)", opacity: 0.4 }}
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
              stroke="var(--dsi-selected)"
              strokeDasharray="6 3"
              strokeWidth={2}
            >
              <Label
                value={`Subject ${formatNumber(subjectValue, subjectValueDecimals)}`}
                position="right"
                fill="var(--dsi-selected)"
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
                        fill="var(--dsi-contrast-background)"
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
                    ? "var(--dsi-selected)"
                    : "var(--dsi-analysis)"
                }
              />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

/** PEER SCATTER CHART---------------------------------------------------------------------------------------------- */

export interface PeerPoint {
  x: number;
  y: number;
  /** Drives dot colour via getDecisionColor. */
  decision?: string;
}

interface PeerScatterChartProps {
  points: PeerPoint[];
  /** Active submission — rendered as a star and used for the crosshair. */
  subject: { x: number; y: number };
  xLabel: string;
  yLabel: string;
  /** Axis names shown in the tooltip. */
  xName?: string;
  yName?: string;
  /** Tooltip value formatter. Default: 1-decimal number. */
  formatValue?: (value: number) => string;
  /** Chart height in px. Default 400. */
  height?: number;
  /** Render the approve/refer/decline/unknown legend above the chart. */
  showDecisionLegend?: boolean;
}

const LEGEND = [
  { label: "Approve", dotClass: "bg-dsi-approve" },
  { label: "Refer", dotClass: "bg-dsi-refer" },
  { label: "Decline", dotClass: "bg-dsi-decline" },
  { label: "Unknown", dotClass: "bg-dsi-muted" },
];


/**
 * Template for the pattern used by LossTab (propensity × severity) and
 * ExposureTab (magnitude × composite-score):
 *
 *   • Peer submissions plotted as dots, coloured by their decision.
 *   • Active submission plotted as a star.
 *   • Dashed ReferenceLines mark the subject's x and y values.
 *   • Optional decision-colour legend row rendered above the chart.
 *
 * Callers pre-map their data to `{ x, y, decision? }` so the primitive
 * stays agnostic of domain field names.
 */

export const PeerScatterChart = ({
  points,
  subject,
  xLabel,
  yLabel,
  xName = "X",
  yName = "Y",
  formatValue = (v) => formatNumber(v, 1),
  height = 400,
  showDecisionLegend = true,
}: PeerScatterChartProps) => {
  return (
    <>
      {showDecisionLegend && (
        <div className="flex items-center gap-4 text-xs pl-dsi-pad pr-dsi-pad pb-2 opacity-70">
          {LEGEND.map((l) => (
            <span key={l.label} className="flex items-center gap-1">
              <span className={`inline-block w-2 h-2 rounded-full ${l.dotClass}`} />
              {l.label}
            </span>
          ))}
        </div>
      )}

      <div className="pl-dsi-pad pr-dsi-pad w-full relative" style={{ height }}>
        <ResponsiveContainer width="100%" height="100%">
          <ScatterChart margin={{ top: 10, right: 30, bottom: 20, left: 0 }}>
            <CartesianGrid
              strokeDasharray="3 3"
              stroke="var(--dsi-outline)"
              opacity={0.5}
            />
            <XAxis
              type="number"
              dataKey="x"
              name={xName}
              stroke="var(--dsi-contrast-background)"
              tick={{ fill: "var(--dsi-contrast-background)", fontSize: 12 }}
              label={{
                value: xLabel,
                position: "insideBottom",
                offset: -15,
                fill: "var(--dsi-contrast-background)",
                fontSize: 12,
              }}
            />
            <YAxis
              type="number"
              dataKey="y"
              name={yName}
              stroke="var(--dsi-contrast-background)"
              tick={{ fill: "var(--dsi-contrast-background)", fontSize: 12 }}
              label={{
                value: yLabel,
                angle: -90,
                position: "insideLeft",
                fill: "var(--dsi-contrast-background)",
                fontSize: 12,
              }}
            />
            <RechartsTooltip
              cursor={{ strokeDasharray: "3 3" }}
              contentStyle={tooltipStyle}
              formatter={(value: unknown, name: string) => [
                formatValue(Number(value)),
                name,
              ]}
            />

            {/* Subject crosshair */}
            <ReferenceLine
              x={subject.x}
              stroke="var(--dsi-selected)"
              strokeDasharray="4 4"
              strokeOpacity={0.6}
            />
            <ReferenceLine
              y={subject.y}
              stroke="var(--dsi-selected)"
              strokeDasharray="4 4"
              strokeOpacity={0.6}
            />

            {/* Peer points coloured per decision */}
            {points.map((p, idx) => (
              <Scatter
                key={`peer-${idx}`}
                data={[p]}
                fill={getDecisionColor(p.decision)}
                fillOpacity={0.5}
                isAnimationActive={false}
              />
            ))}

            {/* Active subject as a star */}
            <Scatter
              name="Active Submission"
              data={[subject]}
              fill="var(--dsi-selected)"
              shape="star"
            />
          </ScatterChart>
        </ResponsiveContainer>
      </div>
    </>
  );
}

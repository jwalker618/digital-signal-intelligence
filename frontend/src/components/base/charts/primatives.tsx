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

/** DISTRIBUTION BAR CHART---------------------------------------------------------------------------------------------- */

export interface DistributionBarChartProps<T extends Record<string, unknown>> {
  data: T[];
  /** Field name on `T` for the x-axis category. */
  categoryKey: keyof T & string;
  /** Field name on `T` for the bar value (typically a count). */
  valueKey: keyof T & string;
  /**
   * Per-bar colour resolver. Called once per row.
   * Default: every bar painted `generate-selected`.
   */
  colorFor?: (entry: T, index: number) => string;
  /** Human-readable name for the bar value in the tooltip. */
  valueName?: string;
  /** Tooltip value formatter. Default: 0-decimal number. */
  formatValue?: (value: number) => string;
  /** Y-axis domain override. Default "auto", "auto". */
  yDomain?: [number | "auto", number | "auto"];
  /** Chart height in px. Default 200. */
  height?: number;
  /** Shown when `data` is empty. */
  emptyMessage?: string;
}

/**
 * Plain category → count bar chart. Used by the WorldEngineView tier
 * distributions: one bar per tier, coloured by the caller's
 * tier-index → colour map. Complements `BenchmarkBarChart`, which
 * exists for the subject-vs-peer comparison pattern and isn't the
 * right fit when every bar is its own "category".
 */
export const DistributionBarChart = <T extends Record<string, unknown>>({
  data,
  categoryKey,
  valueKey,
  colorFor = () => "var(--generate-selected)",
  valueName,
  formatValue = (v) => formatNumber(v, 0),
  yDomain = ["auto", "auto"],
  height = 200,
  emptyMessage = "No data available.",
}: DistributionBarChartProps<T>) => {
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
    <div className="w-full" style={{ height }}>
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data} margin={{ top: 5, right: 10, bottom: 5, left: -20 }}>
          <CartesianGrid
            strokeDasharray="3 3"
            stroke="var(--generate-outline)"
            opacity={0.3}
          />
          <XAxis
            dataKey={categoryKey}
            stroke="var(--generate-contrast-background)"
            tick={{ fill: "var(--generate-contrast-background)", fontSize: 11 }}
          />
          <YAxis
            stroke="var(--generate-contrast-background)"
            tick={{ fill: "var(--generate-contrast-background)", fontSize: 11 }}
            domain={yDomain}
          />
          <RechartsTooltip
            contentStyle={tooltipStyle}
            cursor={{ fill: "var(--generate-selected)", opacity: 0.2 }}
            formatter={(value: unknown, name: string) => [
              formatValue(Number(value)),
              valueName ?? name,
            ]}
          />
          <Bar dataKey={valueKey} radius={[4, 4, 0, 0]}>
            {data.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={colorFor(entry, index)} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
};

/** HORIZONTAL BAR LIST---------------------------------------------------------------------------------------------- */

export interface HorizontalBarListRow {
  label: string;
  /** Bar width as a 0–100 percent. */
  percent: number;
  /** Right-aligned annotation, e.g. "12 (30%)". */
  valueLabel?: React.ReactNode;
}

export interface HorizontalBarListProps {
  rows: HorizontalBarListRow[];
  /** Optional cap — takes the first N rows. */
  limit?: number;
  /** Tailwind class for the label column width. Default "w-24". */
  labelWidth?: string;
  /** Tailwind class for the value column width. Default "w-16". */
  valueWidth?: string;
  emptyMessage?: string;
}

/**
 * Stacked label / progress-bar / value rows — the "Sector Concentration"
 * pattern in WorldEngineView, generalised. Pre-compute `percent`
 * (0-100) and the right-hand `valueLabel` on the calling side so the
 * primitive stays domain-agnostic.
 */
export const HorizontalBarList = ({
  rows,
  limit,
  labelWidth = "w-24",
  valueWidth = "w-16",
  emptyMessage = "No data available.",
}: HorizontalBarListProps) => {
  const shown = limit ? rows.slice(0, limit) : rows;
  if (shown.length === 0) {
    return <p className="generate-user-message">{emptyMessage}</p>;
  }
  return (
    <div className="space-y-2">
      {shown.map((r) => (
        <div key={r.label} className="flex items-center gap-3">
          <span
            className={`text-xs truncate opacity-70 ${labelWidth}`}
            title={r.label}
          >
            {r.label}
          </span>
          <div className="flex-1 h-4 bg-generate-background rounded-full overflow-hidden">
            <div
              className="h-full rounded-full bg-generate-selected/40"
              style={{ width: `${Math.max(0, Math.min(100, r.percent))}%` }}
            />
          </div>
          {r.valueLabel !== undefined && (
            <span className={`text-xs font-bold text-right ${valueWidth}`}>
              {r.valueLabel}
            </span>
          )}
        </div>
      ))}
    </div>
  );
};

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
    <div className="pl-generate-pad pr-generate-pad w-full" style={{ height }}>
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data} margin={{ top: 0, right: 0, bottom: 20, left: -20 }}>
          <CartesianGrid
            strokeDasharray="3 3"
            vertical={false}
            stroke="var(--generate-outline)"
            opacity={0.5}
          />
          <XAxis
            dataKey={categoryKey}
            stroke="var(--generate-contrast-background)"
            tick={{ fill: "var(--generate-contrast-background)", fontSize: 11 }}
            interval={0}
            tickFormatter={(val: string) =>
              typeof val === "string" && val.length > maxCategoryLength
                ? val.substring(0, maxCategoryLength) + "..."
                : val
            }
          />
          <YAxis
            stroke="var(--generate-contrast-background)"
            tick={{ fill: "var(--generate-contrast-background)", fontSize: 12 }}
            domain={yDomain}
          />
          <RechartsTooltip
            contentStyle={tooltipStyle}
            cursor={{ fill: "var(--generate-selected)", opacity: 0.4 }}
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
              stroke="var(--generate-selected)"
              strokeDasharray="6 3"
              strokeWidth={2}
            >
              <Label
                value={`Subject ${formatNumber(subjectValue, subjectValueDecimals)}`}
                position="right"
                fill="var(--generate-selected)"
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
                        fill="var(--generate-contrast-background)"
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
                    ? "var(--generate-selected)"
                    : "var(--generate-analysis)"
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
  { label: "Approve", dotClass: "bg-generate-approve" },
  { label: "Refer", dotClass: "bg-generate-refer" },
  { label: "Decline", dotClass: "bg-generate-decline" },
  { label: "Unknown", dotClass: "bg-generate-muted" },
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
        <div className="flex items-center gap-4 text-xs pl-generate-pad pr-generate-pad pb-2 opacity-70">
          {LEGEND.map((l) => (
            <span key={l.label} className="flex items-center gap-1">
              <span className={`inline-block w-2 h-2 rounded-full ${l.dotClass}`} />
              {l.label}
            </span>
          ))}
        </div>
      )}

      <div className="pl-generate-pad pr-generate-pad w-full relative" style={{ height }}>
        <ResponsiveContainer width="100%" height="100%">
          <ScatterChart margin={{ top: 10, right: 30, bottom: 20, left: 0 }}>
            <CartesianGrid
              strokeDasharray="3 3"
              stroke="var(--generate-outline)"
              opacity={0.5}
            />
            <XAxis
              type="number"
              dataKey="x"
              name={xName}
              stroke="var(--generate-contrast-background)"
              tick={{ fill: "var(--generate-contrast-background)", fontSize: 12 }}
              label={{
                value: xLabel,
                position: "insideBottom",
                offset: -15,
                fill: "var(--generate-contrast-background)",
                fontSize: 12,
              }}
            />
            <YAxis
              type="number"
              dataKey="y"
              name={yName}
              stroke="var(--generate-contrast-background)"
              tick={{ fill: "var(--generate-contrast-background)", fontSize: 12 }}
              label={{
                value: yLabel,
                angle: -90,
                position: "insideLeft",
                fill: "var(--generate-contrast-background)",
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
              stroke="var(--generate-selected)"
              strokeDasharray="4 4"
              strokeOpacity={0.6}
            />
            <ReferenceLine
              y={subject.y}
              stroke="var(--generate-selected)"
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
              fill="var(--generate-selected)"
              shape="star"
            />
          </ScatterChart>
        </ResponsiveContainer>
      </div>
    </>
  );
}

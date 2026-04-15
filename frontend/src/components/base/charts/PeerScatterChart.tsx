"use client";

/**
 * PeerScatterChart — cohort/peer scatter with subject crosshair.
 *
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

import {
  ScatterChart,
  Scatter,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip as RechartsTooltip,
  ResponsiveContainer,
  ReferenceLine,
} from "recharts";

import { formatNumber } from "@/lib/format";
import { getDecisionColor, tooltipStyle } from "@/lib/chartConfig";

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

export default function PeerScatterChart({
  points,
  subject,
  xLabel,
  yLabel,
  xName = "X",
  yName = "Y",
  formatValue = (v) => formatNumber(v, 1),
  height = 400,
  showDecisionLegend = true,
}: PeerScatterChartProps) {
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
              stroke="var(--dsi-chart-grid)"
              opacity={0.5}
            />
            <XAxis
              type="number"
              dataKey="x"
              name={xName}
              stroke="var(--dsi-chart-axis)"
              tick={{ fill: "var(--dsi-chart-axis)", fontSize: 12 }}
              label={{
                value: xLabel,
                position: "insideBottom",
                offset: -15,
                fill: "var(--dsi-chart-axis)",
                fontSize: 12,
              }}
            />
            <YAxis
              type="number"
              dataKey="y"
              name={yName}
              stroke="var(--dsi-chart-axis)"
              tick={{ fill: "var(--dsi-chart-axis)", fontSize: 12 }}
              label={{
                value: yLabel,
                angle: -90,
                position: "insideLeft",
                fill: "var(--dsi-chart-axis)",
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
              stroke="var(--dsi-chart-subject)"
              strokeDasharray="4 4"
              strokeOpacity={0.6}
            />
            <ReferenceLine
              y={subject.y}
              stroke="var(--dsi-chart-subject)"
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
              fill="var(--dsi-chart-subject)"
              shape="star"
            />
          </ScatterChart>
        </ResponsiveContainer>
      </div>
    </>
  );
}

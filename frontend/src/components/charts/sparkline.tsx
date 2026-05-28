"use client";

import { Area, AreaChart, ResponsiveContainer } from "recharts";

interface SparklineProps {
  points: number[];
  color?: string;
  height?: number;
  className?: string;
}

/**
 * Tiny inline trend line. Auto-scales to min/max; no axes.
 * Default color is `--color-info` so it reads as a neutral fact.
 */
export function Sparkline({
  points,
  color = "var(--color-info)",
  height = 28,
  className,
}: SparklineProps) {
  const data = points.map((value, i) => ({ i, value }));
  return (
    <div className={className} style={{ height }}>
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={data} margin={{ top: 2, bottom: 2, left: 0, right: 0 }}>
          <defs>
            <linearGradient id="sparkfill" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor={color} stopOpacity={0.22} />
              <stop offset="100%" stopColor={color} stopOpacity={0} />
            </linearGradient>
          </defs>
          <Area
            type="monotone"
            dataKey="value"
            stroke={color}
            strokeWidth={1.5}
            fill="url(#sparkfill)"
            isAnimationActive={false}
            dot={false}
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}

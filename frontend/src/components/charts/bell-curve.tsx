"use client";

import { memo, useMemo } from "react";

/**
 * Chart-local cohort shape. Domain entities (e.g. PeersResponse) get mapped
 * into this at the page level so the chart stays decoupled from API types.
 */
export interface PeerCohort {
  mean: number;
  sd: number;
  median: number;
  topDecile: number;
  range: [number, number];
  /** Subject's value within the distribution. */
  you: number;
}

interface BellCurveProps {
  cohort: PeerCohort;
  height?: number;
}

/** Sample a unit-peak normal PDF across the cohort range. */
function bellCurve(cohort: PeerCohort, samples = 100) {
  const [lo, hi] = cohort.range;
  const span = hi - lo;
  if (span <= 0) return [];
  const out: { x: number; y: number }[] = [];
  for (let i = 0; i <= samples; i++) {
    const x = lo + (span * i) / samples;
    const z = (x - cohort.mean) / cohort.sd;
    const y =
      (1 / (cohort.sd * Math.sqrt(2 * Math.PI))) * Math.exp(-0.5 * z * z);
    out.push({ x, y });
  }
  const peak = Math.max(...out.map((p) => p.y), 1e-9);
  return out.map((p) => ({ x: p.x, y: p.y / peak }));
}

function youPosition(cohort: PeerCohort): number {
  const [lo, hi] = cohort.range;
  if (hi - lo <= 0) return 0.5;
  return Math.max(0, Math.min(1, (cohort.you - lo) / (hi - lo)));
}

/**
 * Cohort distribution with a YOU pin. SVG path is computed locally — no
 * recharts roundtrip needed for this simple shape.
 */
function BellCurveImpl({ cohort, height = 160 }: BellCurveProps) {
  const points = useMemo(() => bellCurve(cohort, 100), [cohort]);
  const youAt = useMemo(() => youPosition(cohort), [cohort]);

  const padX = 24;
  const padY = 12;
  const W = 600;
  const H = height;
  const innerW = W - padX * 2;
  const innerH = H - padY * 2 - 26;
  const path = points
    .map((p, i) => {
      const x = padX + (i / (points.length - 1)) * innerW;
      const y = padY + innerH - p.y * innerH;
      return `${i === 0 ? "M" : "L"} ${x.toFixed(1)} ${y.toFixed(1)}`;
    })
    .join(" ");
  const closed = `${path} L ${padX + innerW} ${padY + innerH} L ${padX} ${padY + innerH} Z`;

  const youX = padX + youAt * innerW;
  const youYIdx = Math.round(youAt * (points.length - 1));
  const youY = padY + innerH - (points[youYIdx]?.y ?? 0) * innerH;

  const medianAt = (cohort.median - cohort.range[0]) / (cohort.range[1] - cohort.range[0]);
  const medianX = padX + medianAt * innerW;
  const topAt = (cohort.topDecile - cohort.range[0]) / (cohort.range[1] - cohort.range[0]);
  const topX = padX + topAt * innerW;

  return (
    <svg viewBox={`0 0 ${W} ${H}`} width="100%" height={H} role="img" aria-label="Cohort distribution">
      <defs>
        <linearGradient id="bellfill" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor="var(--color-info)" stopOpacity={0.18} />
          <stop offset="100%" stopColor="var(--color-info)" stopOpacity={0} />
        </linearGradient>
      </defs>
      {/* Top-decile shaded zone */}
      <rect
        x={topX}
        y={padY}
        width={padX + innerW - topX}
        height={innerH}
        fill="var(--color-pos-soft)"
        opacity={0.7}
      />
      {/* Curve fill */}
      <path d={closed} fill="url(#bellfill)" />
      {/* Curve stroke */}
      <path d={path} fill="none" stroke="var(--color-info)" strokeWidth={1.5} />
      {/* Median tick */}
      <line
        x1={medianX}
        x2={medianX}
        y1={padY}
        y2={padY + innerH}
        stroke="var(--color-ink-mute)"
        strokeDasharray="3 3"
      />
      <text x={medianX} y={padY - 2} textAnchor="middle" fontSize={10} fill="var(--color-ink-mute)">
        median
      </text>
      {/* YOU pin */}
      <line x1={youX} x2={youX} y1={youY} y2={padY + innerH} stroke="var(--color-info)" strokeWidth={1.5} />
      <circle cx={youX} cy={youY} r={5} fill="var(--color-surface)" stroke="var(--color-info)" strokeWidth={2} />
      <rect
        x={youX - 18}
        y={youY - 22}
        width={36}
        height={16}
        rx={8}
        fill="var(--color-info)"
      />
      <text x={youX} y={youY - 11} textAnchor="middle" fontSize={10} fontWeight={700} fill="#fff">
        YOU
      </text>
      {/* X axis ticks */}
      <text x={padX} y={H - 4} fontSize={10} fill="var(--color-ink-mute)">
        {cohort.range[0]}
      </text>
      <text x={padX + innerW} y={H - 4} textAnchor="end" fontSize={10} fill="var(--color-ink-mute)">
        {cohort.range[1]}
      </text>
    </svg>
  );
}

export const BellCurve = memo(BellCurveImpl);

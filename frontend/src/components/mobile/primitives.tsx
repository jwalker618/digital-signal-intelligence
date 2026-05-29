"use client";

import { memo, type ReactNode } from "react";
import { ChevronRight } from "lucide-react";

export type Tone = "ink" | "info" | "spot" | "pos" | "neg" | "warn" | "aux";

export const TONE_BG: Record<Tone, string> = {
  ink: "var(--color-surface-sunken)",
  info: "var(--color-info-soft)",
  spot: "var(--color-spot-soft)",
  pos: "var(--color-pos-soft)",
  neg: "var(--color-neg-soft)",
  warn: "var(--color-warn-soft)",
  aux: "var(--color-aux-soft)",
};

export const TONE_FG: Record<Tone, string> = {
  ink: "var(--color-ink)",
  info: "var(--color-info-deep)",
  spot: "var(--color-spot-deep)",
  pos: "var(--color-pos)",
  neg: "var(--color-neg)",
  warn: "var(--color-warn)",
  aux: "var(--color-aux)",
};

export const TONE_BASE: Record<Tone, string> = {
  ink: "var(--color-ink)",
  info: "var(--color-info)",
  spot: "var(--color-spot)",
  pos: "var(--color-pos)",
  neg: "var(--color-neg)",
  warn: "var(--color-warn)",
  aux: "var(--color-aux)",
};

export function Section({
  title,
  link,
  onLink,
}: {
  title: string;
  link?: string;
  onLink?: () => void;
}) {
  return (
    <div className="dsi-sect">
      <h3>{title}</h3>
      {link && (
        <button
          type="button"
          className="dsi-sect-link"
          onClick={onLink}
          style={{ background: "transparent", border: 0 }}
        >
          {link}
          <ChevronRight size={15} />
        </button>
      )}
    </div>
  );
}

export const Chip = memo(function Chip({
  tone,
  icon,
  children,
}: {
  tone: Tone;
  icon?: ReactNode;
  children: ReactNode;
}) {
  return (
    <span
      className="dsi-chip"
      style={{ background: TONE_BG[tone], color: TONE_FG[tone] }}
    >
      {icon}
      {children}
    </span>
  );
});

/* 14-point inline sparkline. Returns a self-contained SVG block. */
export const Sparkline = memo(function Sparkline({
  data,
  stroke,
  w = 150,
  h = 42,
}: {
  data: number[];
  stroke: string;
  w?: number;
  h?: number;
}) {
  if (!data || data.length < 2) {
    return <svg width={w} height={h} viewBox={`0 0 ${w} ${h}`} aria-hidden />;
  }
  const min = Math.min(...data);
  const max = Math.max(...data);
  const span = max - min || 1;
  const step = w / (data.length - 1);
  const pts = data.map(
    (v, i): [number, number] => [i * step, h - 4 - ((v - min) / span) * (h - 8)],
  );
  const line = pts
    .map((p, i) => (i ? "L" : "M") + p[0].toFixed(1) + " " + p[1].toFixed(1))
    .join(" ");
  const area = `${line} L${w} ${h} L0 ${h} Z`;
  const gid = `mob-spark-${data.length}-${Math.round(data[data.length - 1] ?? 0)}`;
  return (
    <svg
      width={w}
      height={h}
      viewBox={`0 0 ${w} ${h}`}
      style={{ display: "block", overflow: "visible" }}
      aria-hidden
    >
      <defs>
        <linearGradient id={gid} x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" stopColor={stroke} stopOpacity="0.18" />
          <stop offset="1" stopColor={stroke} stopOpacity="0" />
        </linearGradient>
      </defs>
      <path d={area} fill={`url(#${gid})`} />
      <path
        d={line}
        fill="none"
        stroke={stroke}
        strokeWidth="2.2"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <circle
        cx={pts[pts.length - 1][0]}
        cy={pts[pts.length - 1][1]}
        r={3.2}
        fill={stroke}
      />
    </svg>
  );
});

/* 124×124 score ring, 0..1 fraction. */
export function SignalRing({
  frac,
  value,
  caption,
  tone = "info",
}: {
  frac: number;
  value: string | number;
  caption: string;
  tone?: Tone;
}) {
  const R = 52;
  const C = 2 * Math.PI * R;
  const dash = Math.max(0.02, Math.min(1, frac)) * C;
  return (
    <div style={{ position: "relative", width: 124, height: 124, flexShrink: 0 }}>
      <svg
        width="124"
        height="124"
        viewBox="0 0 124 124"
        style={{ transform: "rotate(-90deg)" }}
      >
        <circle
          cx="62"
          cy="62"
          r={R}
          fill="none"
          stroke="var(--color-surface-sunken)"
          strokeWidth="9"
        />
        <circle
          cx="62"
          cy="62"
          r={R}
          fill="none"
          stroke={TONE_BASE[tone]}
          strokeWidth="9"
          strokeLinecap="round"
          strokeDasharray={`${dash} ${C}`}
          style={{ transition: "stroke-dasharray .9s cubic-bezier(.3,.7,.3,1)" }}
        />
      </svg>
      <div
        style={{
          position: "absolute",
          inset: 0,
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
        }}
      >
        <div className="dsi-ring-num">{value}</div>
        <div className="dsi-ring-cap">{caption}</div>
      </div>
    </div>
  );
}

/* Hash a string to a stable hue for avatar backgrounds. */
export function avatarColor(s: string): number {
  let h = 0;
  for (let i = 0; i < s.length; i++) h = (h * 31 + s.charCodeAt(i)) % 360;
  return h;
}

import { formatCurrency } from "@/lib/format";

/** $185,200 → "$185k". Falls back to full currency under $1k. */
export function kFmt(v: number | null | undefined): string {
  if (v == null) return "—";
  const abs = Math.abs(v);
  if (abs >= 1_000_000) return `$${(v / 1_000_000).toFixed(abs >= 10_000_000 ? 0 : 1)}M`;
  if (abs >= 1_000) return `$${Math.round(v / 1_000)}k`;
  return formatCurrency(v);
}

/** Tier → tone key (matches the design's tierColor). */
export function tierTone(t: number | null | undefined): "pos" | "info" | "warn" | "neg" | "mute" {
  if (t == null) return "mute";
  if (t <= 2) return "pos";
  if (t === 3) return "info";
  if (t === 4) return "warn";
  return "neg";
}

export const TIER_BG: Record<string, string> = {
  pos: "bg-pos-soft text-pos",
  info: "bg-info-soft text-info",
  warn: "bg-warn-soft text-warn",
  neg: "bg-neg-soft text-neg",
  mute: "bg-surface-elev text-ink-mute",
};

export function decisionTone(
  d: string | null | undefined,
): "pos" | "spot" | "neg" | "mute" {
  const dec = (d ?? "").toLowerCase();
  if (dec === "approve") return "pos";
  if (dec === "refer") return "spot";
  if (dec === "decline") return "neg";
  return "mute";
}

export function pct(v: number | null | undefined, digits = 0): string {
  return v == null ? "—" : `${(v * 100).toFixed(digits)}%`;
}

// Explicit tone → class maps (Tailwind JIT can't see interpolated names).
export const DOT_BG: Record<string, string> = {
  pos: "bg-pos",
  spot: "bg-spot",
  neg: "bg-neg",
  info: "bg-info",
  warn: "bg-warn",
  mute: "bg-ink-mute",
};

export const NUM_TEXT: Record<string, string> = {
  pos: "text-pos",
  spot: "text-spot",
  neg: "text-neg",
  info: "text-info",
  warn: "text-warn",
  mute: "text-ink-mute",
};

export const BAR_BG: Record<string, string> = {
  pos: "bg-pos",
  info: "bg-info",
  warn: "bg-warn",
  neg: "bg-neg",
  mute: "bg-rule",
};

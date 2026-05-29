// Shared tier → tone mapping. Tiers 1–2 are healthy (pos), 3 neutral
// (info), 4 caution (warn), 5+ poor (neg). Centralised so the carrier
// pipeline, client/broker workbenches and book views all render tier
// chips identically. Tailwind JIT needs literal class strings, hence the
// explicit maps.

export type TierTone = "pos" | "info" | "warn" | "neg" | "mute";

export function tierToneOf(tier: number | null | undefined): TierTone {
  if (tier == null) return "mute";
  if (tier <= 2) return "pos";
  if (tier === 3) return "info";
  if (tier === 4) return "warn";
  return "neg";
}

/** Soft-filled chip (tinted bg + tone text) — the tier badge. */
export const TIER_CHIP: Record<TierTone, string> = {
  pos: "bg-pos-soft text-pos",
  info: "bg-info-soft text-info",
  warn: "bg-warn-soft text-warn",
  neg: "bg-neg-soft text-neg",
  mute: "bg-surface-elev text-ink-mute",
};

/** Solid bar fill — tier-distribution bars. */
export const TIER_BAR: Record<TierTone, string> = {
  pos: "bg-pos",
  info: "bg-info",
  warn: "bg-warn",
  neg: "bg-neg",
  mute: "bg-rule",
};

/** Plain tone text — tier-distribution counts. */
export const TIER_TEXT: Record<TierTone, string> = {
  pos: "text-pos",
  info: "text-info",
  warn: "text-warn",
  neg: "text-neg",
  mute: "text-ink-mute",
};

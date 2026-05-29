// Client-workbench display helpers. Tier + compact-currency logic is
// shared app-wide (lib/tier, lib/coerce); re-exported here under the
// names the CW tabs already import so there's a single source of truth.
import { compactCurrency } from "@/lib/coerce";
import { tierToneOf, TIER_CHIP, TIER_BAR } from "@/lib/tier";

/** $185,200 → "$185k" (shared compact currency). */
export const kFmt = compactCurrency;

/** Tier → tone key (shared). */
export const tierTone = tierToneOf;
/** Soft tier badge bg+text (shared). */
export const TIER_BG = TIER_CHIP;
/** Solid tier bar bg (shared). */
export const BAR_BG = TIER_BAR;

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

// Tone → class maps that include `spot` (pipeline-state dots / numbers) —
// broader than the tier maps, so kept local.
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

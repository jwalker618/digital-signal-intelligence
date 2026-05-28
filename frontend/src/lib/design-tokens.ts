/**
 * Visual design vocabulary — used by primitives and charts as variant keys.
 *
 * Kept separate from domain types in @/types/portal so the design system
 * stays decoupled from the API contract.
 */

export type Tone =
  | "info" // teal — informative hero facts (score, premium, percentile)
  | "spot" // coral — awaiting / urgent action / opportunities
  | "pos" // green — strengths, savings
  | "aux" // blue — secondary informative
  | "warn" // amber — caution
  | "neg" // red — bad
  | "mute"; // neutral

/** Tailwind utility lookups keyed by tone, for one-line styling. */
export const TONE_BG: Record<Tone, string> = {
  info: "bg-info",
  spot: "bg-spot",
  pos: "bg-pos",
  aux: "bg-aux",
  warn: "bg-warn",
  neg: "bg-neg",
  mute: "bg-ink-mute",
};

export const TONE_TEXT: Record<Tone, string> = {
  info: "text-info",
  spot: "text-spot",
  pos: "text-pos",
  aux: "text-aux",
  warn: "text-warn",
  neg: "text-neg",
  mute: "text-ink-mute",
};

/** Maps the existing portalTone helper's tone vocabulary to ours. */
export function portalToneToTone(
  t: "positive" | "warning" | "negative" | "muted",
): Tone {
  return t === "positive" ? "pos" : t === "warning" ? "warn" : t === "negative" ? "neg" : "mute";
}

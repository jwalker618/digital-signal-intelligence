/**
 * Shared status → colour mappings.
 *
 * Single source of truth for decision / action / tone → (bg, text)
 * Tailwind class pairs. Consumed by `StatusPill` (and any ad-hoc callsite
 * that needs matching foreground + background classes).
 */

import {
  LucideIcon,
  ShieldCheck,
  ShieldQuestionMark,
  ShieldX,
} from "lucide-react";

export interface StatusPaletteEntry {
  text: string;
  bg: string;
}


/** Decision outcomes — big coloured banner / pill. */
export const DECISION_PALETTE: Record<string, StatusPaletteEntry> = {
  approve: { text: "text-dsi-approve", bg: "bg-dsi-approve",  },
  refer:   { text: "text-dsi-refer", bg: "bg-dsi-refer",     },
  decline: { text: "text-dsi-decline", bg: "bg-dsi-decline",  },
  pending: { text: "text-dsi-muted", bg: "bg-dsi-muted",       },
};

/**
 * Submission header card — decision → (bg, icon) pair.
 *
 * Different shape than the {text, bg} palettes because the submission
 * header shows a large shield icon alongside the banner; the icon maps
 * 1:1 with the decision.
 */
export type Decision = "approve" | "refer" | "decline" | "pending";

export interface DecisionVisual {
  bg: string;
  icon: LucideIcon;
}

export const SUBMISSION_DECISION: Record<Decision, DecisionVisual> = {
  approve: { bg: "bg-dsi-approve", icon: ShieldCheck },
  refer:   { bg: "bg-dsi-refer",   icon: ShieldQuestionMark },
  decline: { bg: "bg-dsi-decline", icon: ShieldX },
  pending: { bg: "bg-dsi-muted",   icon: ShieldQuestionMark },
};

/** Signal/condition actions — used in badges and row tags. */
export const ACTION_PALETTE: Record<string, StatusPaletteEntry> = {
  modifier:      { bg: "bg-dsi-info/15",     text: "text-dsi-info"     },
  referral:      { bg: "bg-dsi-refer/15",  text: "text-dsi-refer"  },
  refer:         { bg: "bg-dsi-refer/15",  text: "text-dsi-refer"  },
  tier_override: { bg: "bg-dsi-decline/15", text: "text-dsi-decline" },
  flag:          { bg: "bg-dsi-muted/15",    text: "text-dsi-muted"    },
  note:          { bg: "bg-dsi-muted/15",    text: "text-dsi-muted"    },
};

/** Health / lifecycle statuses — used by admin + world-engine dashboards. */
export const HEALTH_PALETTE: Record<string, StatusPaletteEntry> = {
  green:          { bg: "bg-dsi-approve/15", text: "text-dsi-approve" },
  healthy:        { bg: "bg-dsi-approve/15", text: "text-dsi-approve" },
  ok:             { bg: "bg-dsi-approve/15", text: "text-dsi-approve" },
  deployed:       { bg: "bg-dsi-approve/15", text: "text-dsi-approve" },
  approved:       { bg: "bg-dsi-approve/15", text: "text-dsi-approve" },
  active:         { bg: "bg-dsi-approve/15", text: "text-dsi-approve" },

  amber:          { bg: "bg-dsi-refer/15",  text: "text-dsi-refer"  },
  warning:        { bg: "bg-dsi-refer/15",  text: "text-dsi-refer"  },
  pending_review: { bg: "bg-dsi-refer/15",  text: "text-dsi-refer"  },
  validating:     { bg: "bg-dsi-refer/15",  text: "text-dsi-refer"  },
  calibrating:    { bg: "bg-dsi-refer/15",  text: "text-dsi-refer"  },
  provisional:    { bg: "bg-dsi-info/15",     text: "text-dsi-info"     },

  red:            { bg: "bg-dsi-decline/15", text: "text-dsi-decline" },
  critical:       { bg: "bg-dsi-decline/15", text: "text-dsi-decline" },
  rejected:       { bg: "bg-dsi-decline/15", text: "text-dsi-decline" },
  locked:         { bg: "bg-dsi-decline/15", text: "text-dsi-decline" },
  error:          { bg: "bg-dsi-decline/15", text: "text-dsi-decline" },

  info:           { bg: "bg-dsi-info/15",     text: "text-dsi-info"     },

  draft:          { bg: "bg-dsi-muted/15",    text: "text-dsi-muted"    },
  archived:       { bg: "bg-dsi-muted/15",    text: "text-dsi-muted"    },
  superseded:     { bg: "bg-dsi-muted/15",    text: "text-dsi-muted"    },
  inactive:       { bg: "bg-dsi-muted/15",    text: "text-dsi-muted"    },
  candidate:      { bg: "bg-dsi-muted/15",    text: "text-dsi-muted"    },
  deprecated:     { bg: "bg-dsi-muted/15",    text: "text-dsi-muted"    },
};

/** Generic tone — for ad-hoc pills not tied to a domain enum. */
export const TONE_PALETTE: Record<string, StatusPaletteEntry> = {
  positive: { bg: "bg-dsi-approve/15", text: "text-dsi-approve" },
  negative: { bg: "bg-dsi-decline/15", text: "text-dsi-decline" },
  warning:  { bg: "bg-dsi-refer/15",  text: "text-dsi-refer"  },
  info:     { bg: "bg-dsi-info/15",     text: "text-dsi-info"     },
  muted:    { bg: "bg-dsi-muted/15",    text: "text-dsi-muted"    },
};

/**
 * Look up an entry in the supplied palette with case-insensitive key
 * matching. Returns the "muted" fallback if the key is absent.
 */
export function getStatusStyle(
  palette: Record<string, StatusPaletteEntry>,
  key: string | null | undefined,
): StatusPaletteEntry {
  if (!key) return TONE_PALETTE.muted;
  return palette[key.toLowerCase()] ?? TONE_PALETTE.muted;
}

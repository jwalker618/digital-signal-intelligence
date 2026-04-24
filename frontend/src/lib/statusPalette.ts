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
  approve: { text: "text-generate-approve", bg: "bg-generate-approve",  },
  refer:   { text: "text-generate-refer", bg: "bg-generate-refer",     },
  decline: { text: "text-generate-decline", bg: "bg-generate-decline",  },
  pending: { text: "text-generate-muted", bg: "bg-generate-muted",       },
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
  approve: { bg: "bg-generate-approve", icon: ShieldCheck },
  refer:   { bg: "bg-generate-refer",   icon: ShieldQuestionMark },
  decline: { bg: "bg-generate-decline", icon: ShieldX },
  pending: { bg: "bg-generate-muted",   icon: ShieldQuestionMark },
};

/** Signal/condition actions — used in badges and row tags. */
export const ACTION_PALETTE: Record<string, StatusPaletteEntry> = {
  modifier:      { bg: "bg-generate-info/15",     text: "text-generate-info"     },
  referral:      { bg: "bg-generate-refer/15",  text: "text-generate-refer"  },
  refer:         { bg: "bg-generate-refer/15",  text: "text-generate-refer"  },
  tier_override: { bg: "bg-generate-decline/15", text: "text-generate-decline" },
  flag:          { bg: "bg-generate-muted/15",    text: "text-generate-muted"    },
  note:          { bg: "bg-generate-muted/15",    text: "text-generate-muted"    },
};

/** Health / lifecycle statuses — used by admin + world-engine dashboards. */
export const HEALTH_PALETTE: Record<string, StatusPaletteEntry> = {
  green:          { bg: "bg-generate-approve/15", text: "text-generate-approve" },
  healthy:        { bg: "bg-generate-approve/15", text: "text-generate-approve" },
  ok:             { bg: "bg-generate-approve/15", text: "text-generate-approve" },
  deployed:       { bg: "bg-generate-approve/15", text: "text-generate-approve" },
  approved:       { bg: "bg-generate-approve/15", text: "text-generate-approve" },
  active:         { bg: "bg-generate-approve/15", text: "text-generate-approve" },

  amber:          { bg: "bg-generate-refer/15",  text: "text-generate-refer"  },
  warning:        { bg: "bg-generate-refer/15",  text: "text-generate-refer"  },
  pending_review: { bg: "bg-generate-refer/15",  text: "text-generate-refer"  },
  validating:     { bg: "bg-generate-refer/15",  text: "text-generate-refer"  },
  calibrating:    { bg: "bg-generate-refer/15",  text: "text-generate-refer"  },
  provisional:    { bg: "bg-generate-info/15",     text: "text-generate-info"     },

  red:            { bg: "bg-generate-decline/15", text: "text-generate-decline" },
  critical:       { bg: "bg-generate-decline/15", text: "text-generate-decline" },
  rejected:       { bg: "bg-generate-decline/15", text: "text-generate-decline" },
  locked:         { bg: "bg-generate-decline/15", text: "text-generate-decline" },
  error:          { bg: "bg-generate-decline/15", text: "text-generate-decline" },

  info:           { bg: "bg-generate-info/15",     text: "text-generate-info"     },

  draft:          { bg: "bg-generate-muted/15",    text: "text-generate-muted"    },
  archived:       { bg: "bg-generate-muted/15",    text: "text-generate-muted"    },
  superseded:     { bg: "bg-generate-muted/15",    text: "text-generate-muted"    },
  inactive:       { bg: "bg-generate-muted/15",    text: "text-generate-muted"    },
  candidate:      { bg: "bg-generate-muted/15",    text: "text-generate-muted"    },
  deprecated:     { bg: "bg-generate-muted/15",    text: "text-generate-muted"    },
};

/** Generic tone — for ad-hoc pills not tied to a domain enum. */
export const TONE_PALETTE: Record<string, StatusPaletteEntry> = {
  positive: { bg: "bg-generate-approve/15", text: "text-generate-approve" },
  negative: { bg: "bg-generate-decline/15", text: "text-generate-decline" },
  warning:  { bg: "bg-generate-refer/15",  text: "text-generate-refer"  },
  info:     { bg: "bg-generate-info/15",     text: "text-generate-info"     },
  muted:    { bg: "bg-generate-muted/15",    text: "text-generate-muted"    },
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

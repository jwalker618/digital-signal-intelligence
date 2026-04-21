/**
 * Shared status → colour mappings.
 *
 * Single source of truth for decision / action / tone → (bg, text)
 * Tailwind class pairs. Consumed by `StatusPill` (and any ad-hoc callsite
 * that needs matching foreground + background classes).
 */

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

/** Signal/condition actions — used in badges and row tags. */
export const ACTION_PALETTE: Record<string, StatusPaletteEntry> = {
  modifier:      { bg: "bg-dsi-info/15",     text: "text-dsi-info"     },
  referral:      { bg: "bg-dsi-warning/15",  text: "text-dsi-warning"  },
  refer:         { bg: "bg-dsi-warning/15",  text: "text-dsi-warning"  },
  tier_override: { bg: "bg-dsi-negative/15", text: "text-dsi-negative" },
  flag:          { bg: "bg-dsi-muted/15",    text: "text-dsi-muted"    },
  note:          { bg: "bg-dsi-muted/15",    text: "text-dsi-muted"    },
};

/** Health / lifecycle statuses — used by admin + world-engine dashboards. */
export const HEALTH_PALETTE: Record<string, StatusPaletteEntry> = {
  green:          { bg: "bg-dsi-positive/15", text: "text-dsi-positive" },
  healthy:        { bg: "bg-dsi-positive/15", text: "text-dsi-positive" },
  ok:             { bg: "bg-dsi-positive/15", text: "text-dsi-positive" },
  deployed:       { bg: "bg-dsi-positive/15", text: "text-dsi-positive" },
  approved:       { bg: "bg-dsi-positive/15", text: "text-dsi-positive" },
  active:         { bg: "bg-dsi-positive/15", text: "text-dsi-positive" },

  amber:          { bg: "bg-dsi-warning/15",  text: "text-dsi-warning"  },
  warning:        { bg: "bg-dsi-warning/15",  text: "text-dsi-warning"  },
  pending_review: { bg: "bg-dsi-warning/15",  text: "text-dsi-warning"  },
  validating:     { bg: "bg-dsi-warning/15",  text: "text-dsi-warning"  },
  calibrating:    { bg: "bg-dsi-warning/15",  text: "text-dsi-warning"  },

  red:            { bg: "bg-dsi-negative/15", text: "text-dsi-negative" },
  critical:       { bg: "bg-dsi-negative/15", text: "text-dsi-negative" },
  rejected:       { bg: "bg-dsi-negative/15", text: "text-dsi-negative" },
  locked:         { bg: "bg-dsi-negative/15", text: "text-dsi-negative" },
  error:          { bg: "bg-dsi-negative/15", text: "text-dsi-negative" },

  info:           { bg: "bg-dsi-info/15",     text: "text-dsi-info"     },

  draft:          { bg: "bg-dsi-muted/15",    text: "text-dsi-muted"    },
  archived:       { bg: "bg-dsi-muted/15",    text: "text-dsi-muted"    },
  superseded:     { bg: "bg-dsi-muted/15",    text: "text-dsi-muted"    },
  inactive:       { bg: "bg-dsi-muted/15",    text: "text-dsi-muted"    },
};

/** Generic tone — for ad-hoc pills not tied to a domain enum. */
export const TONE_PALETTE: Record<string, StatusPaletteEntry> = {
  positive: { bg: "bg-dsi-positive/15", text: "text-dsi-positive" },
  negative: { bg: "bg-dsi-negative/15", text: "text-dsi-negative" },
  warning:  { bg: "bg-dsi-warning/15",  text: "text-dsi-warning"  },
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

/**
 * Shared status → colour mappings.
 *
 * Consolidates the DECISION_STYLE / ACTION_COLORS maps that were duplicated
 * across SummarySAFE, ReferralTab, LossTab, ExposureTab and the cards
 * module. Each entry yields a background class and a text class; apply them
 * together to get the muted pill look used throughout the workbench.
 */

export interface StatusPaletteEntry {
  bg: string;
  text: string;
}

/** Decision outcomes — big coloured banner / pill. */
export const DECISION_PALETTE: Record<string, StatusPaletteEntry> = {
  approve: { bg: "bg-dsi-approve/15", text: "text-dsi-positive" },
  refer:   { bg: "bg-dsi-refer/15",   text: "text-dsi-warning"  },
  decline: { bg: "bg-dsi-decline/15", text: "text-dsi-negative" },
  pending: { bg: "bg-dsi-muted/15",   text: "text-dsi-muted"    },
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

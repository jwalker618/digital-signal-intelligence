// v8.1 — client portal tone helpers.
//
// Translates internal carrier-side constructs (numeric tier, raw
// percentile) into client-friendly status / framing. Centralised so
// the same vocabulary applies across every client portal surface.
//
// Carrier-side pages should NOT use these helpers -- underwriters
// see the raw values.

export type TierStatus = {
  /** Short status label for badges and headers. */
  label: string;
  /** Longer descriptor for tooltips and subtext. */
  description: string;
  /** Tone tied to TONE_PALETTE for visual treatment. */
  tone: "positive" | "warning" | "negative" | "muted";
};

/**
 * Map a numeric tier to a client-friendly status. Tier numbers are
 * internal -- they vary across carriers and feel rank-y to clients
 * who shouldn't be benchmarked against each other in raw form.
 */
export function tierStatus(tier: number | null | undefined): TierStatus {
  if (tier == null) {
    return {
      label: "Pending assessment",
      description: "Your coverage is being assessed.",
      tone: "muted",
    };
  }
  if (tier <= 2) {
    return {
      label: "Preferred",
      description: "Best terms available for your profile.",
      tone: "positive",
    };
  }
  if (tier === 3) {
    return {
      label: "Standard",
      description: "Standard market terms.",
      tone: "muted",
    };
  }
  if (tier === 4) {
    return {
      label: "Under review",
      description: "Underwriter is reviewing additional context.",
      tone: "warning",
    };
  }
  return {
    label: "Capacity constrained",
    description: "Carrier appetite is limited for this profile.",
    tone: "negative",
  };
}


/**
 * Positive framing for percentile rank. Always describes the share
 * of peers the entity is AHEAD of, rather than the share below them.
 * Examples:
 *   73 -> "Top 27% of your cohort"
 *   50 -> "Mid-cohort"
 *   25 -> "Bottom 25% of your cohort -- room to lift"  (used sparingly)
 *
 * For "always positive" presentation on summary surfaces, prefer
 * `peerStandingPositive` below.
 */
export function peerStanding(percentile: number | null | undefined): string {
  if (percentile == null) return "Insufficient peer data";
  const aheadOf = Math.round(percentile);
  if (aheadOf >= 90) return `Top ${100 - aheadOf}% of your cohort`;
  if (aheadOf >= 75) return `Top quartile of your cohort`;
  if (aheadOf >= 50) return `Above the cohort median`;
  if (aheadOf >= 25) return `Approaching the cohort median`;
  return `Room to lift toward cohort median`;
}


/**
 * Strongest positive framing: even bottom-quartile cohorts are
 * described in terms of headroom / opportunity. Used on the
 * client-facing overview where shame-y phrasing would undermine the
 * portal's value proposition.
 */
export function peerStandingPositive(percentile: number | null | undefined): string {
  if (percentile == null) return "Cohort being built — comparison coming soon";
  const aheadOf = Math.round(percentile);
  if (aheadOf >= 90) return `You're in the top ${Math.max(1, 100 - aheadOf)}% of comparable peers`;
  if (aheadOf >= 75) return "You're in the top quartile of comparable peers";
  if (aheadOf >= 50) return "You're outperforming the typical peer";
  if (aheadOf >= 25) return "You're tracking close to your peer cohort";
  return "Clear headroom to lift toward peer norms";
}


/**
 * Reframe a premium-drag dollar value as opportunity-to-save. Used
 * on action plan and signal driver surfaces so the message is
 * forward-looking ("you can save") rather than punitive ("you're
 * paying extra").
 */
export type OpportunityFraming = {
  amount: number;       // absolute dollars
  framing: string;      // "Opportunity to save $18k" or similar
};

export function opportunityFromDrag(dragUsd: number): OpportunityFraming {
  const amount = Math.abs(dragUsd);
  return {
    amount,
    framing: `Opportunity to save ${formatCurrency(amount)}`,
  };
}

function formatCurrency(n: number): string {
  if (n >= 1_000_000) return `$${(n / 1_000_000).toFixed(1)}M`;
  if (n >= 10_000) return `$${Math.round(n / 1000)}k`;
  return `$${Math.round(n)}`;
}

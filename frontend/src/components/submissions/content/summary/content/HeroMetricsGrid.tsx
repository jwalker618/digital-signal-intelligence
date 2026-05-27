"use client";

/**
 * Hero numbers row for SubmissionHeaderCard — composite score, tier,
 * currency, recommended premium/limit, gross premium.
 */

import { useDsiStore } from "@/store/dsiStore";
import { formatNumber, formatText } from "@/lib/format";
import { StatsGrid } from "@/components/base/content/primatives";

export default function HeroMetricsGrid() {
  const { activeQuote, activeVersion, activeCommercial } = useDsiStore();
  if (!activeVersion) return null;

  return (
    <StatsGrid
      columns={[
        {
          width: "10%",
          label: "Final Composite Score",
          value: formatNumber(activeVersion.final_composite_score, 1),
        },
        {
          width: "20%",
          label: "Final Tier",
          value: `T${activeVersion.final_tier} (${activeVersion.tier_label})`,
        },
        {
          width: "10%",
          label: "Currency",
          value: formatText(activeCommercial?.base_currency, "upper", "tbc"),
        },
        {
          width: "15%",
          label: "Recommended Technical Premium",
          value: formatNumber(activeQuote?.recommended_premium, 0),
        },
        {
          width: "15%",
          label: "Recommended Technical Limit",
          value: formatNumber(activeQuote?.recommended_limit, 0),
        },
        {
          width: "15%",
          label: "Gross Premium",
          value: formatNumber(activeCommercial?.gross_premium, 0),
        },
      ]}
    />
  );
}

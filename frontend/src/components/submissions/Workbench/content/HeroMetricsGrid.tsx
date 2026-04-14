"use client";

/**
 * Hero numbers row for SubmissionHeaderCard — composite score, tier,
 * currency, recommended premium/limit, gross premium.
 */

import { useDsiStore } from "@/store/dsiStore";
import { formatNumber, formatText } from "@/lib/format";

export default function HeroMetricsGrid() {
  const { activeQuote, activeVersion, activeCommercial } = useDsiStore() as any;
  if (!activeVersion) return null;

  return (
    <div className="grid grid-cols-[10%_20%_10%_15%_15%_15%]">
      {/* row 1 — headers */}
      <div className="dsi-grid-table-header">Final Composite Score</div>
      <div className="dsi-grid-table-header">Final Tier</div>
      <div className="dsi-grid-table-header">Currency</div>
      <div className="dsi-grid-table-header">Recommended Technical Premium</div>
      <div className="dsi-grid-table-header">Recommended Technical Limit</div>
      <div className="dsi-grid-table-header border-r-0">Gross Premium</div>

      {/* row 2 — values */}
      <div className="dsi-grid-table-item">
        {formatNumber(activeVersion.final_composite_score, 1)}
      </div>
      <div className="dsi-grid-table-item">
        T{activeVersion.final_tier} ({activeVersion.tier_label})
      </div>
      <div className="dsi-grid-table-item">
        {formatText(activeCommercial?.base_currency, "upper", "tbc")}
      </div>
      <div className="dsi-grid-table-item">
        {formatNumber(activeQuote?.recommended_premium, 0)}
      </div>
      <div className="dsi-grid-table-item">
        {formatNumber(activeQuote?.recommended_limit, 0)}
      </div>
      <div className="dsi-grid-table-item border-r-0">
        {formatNumber(activeCommercial?.gross_premium, 0)}
      </div>
    </div>
  );
}

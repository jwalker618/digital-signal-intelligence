"use client";

/**
 * Commercial terms summary — entity, premium, currency, distribution.
 * Body content for a StandardCard titled "Commercial Summary".
 */

import { useDsiStore } from "@/store/dsiStore";
import { formatNumber, formatText } from "@/lib/format";
import { LabelValueList } from "@/components/base/content/primatives";

export default function CommercialSummary() {
  const { activeCommercial } = useDsiStore();

  if (!activeCommercial) {
    return <p className="generate-comment-message">No commercial terms available</p>;
  }

  return (
    <LabelValueList
      rows={[
        { label: "Entity", value: formatText(activeCommercial.entity_name || "N/A", "upper") },
        { label: "Offered Premium", value: formatNumber(activeCommercial.offered_premium, 0) },
        { label: "Gross Premium", value: formatNumber(activeCommercial.gross_premium, 0) },
        { label: "Currency", value: formatText(activeCommercial.base_currency || "USD", "upper") },
        { label: "Distribution", value: formatText(activeCommercial.distribution_type || "N/A", "upper") },
      ]}
    />
  );
}

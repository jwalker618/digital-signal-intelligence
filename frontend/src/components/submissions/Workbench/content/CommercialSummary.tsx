"use client";

/**
 * Commercial terms summary — entity, premium, currency, distribution.
 * Body content for a StandardCard titled "Commercial Summary".
 */

import { useDsiStore } from "@/store/dsiStore";
import { formatNumber } from "@/lib/format";
import { LabelValueList } from "@/components/base/content/primatives";

export default function CommercialSummary() {
  const { activeCommercial } = useDsiStore() as any;

  if (!activeCommercial) {
    return <p className="generate-user-message">No commercial terms available</p>;
  }

  return (
    <LabelValueList
      rows={[
        { label: "Entity", value: activeCommercial.entity_name || "N/A" },
        { label: "Offered Premium", value: formatNumber(activeCommercial.offered_premium, 0) },
        { label: "Gross Premium", value: formatNumber(activeCommercial.gross_premium, 0) },
        { label: "Currency", value: activeCommercial.base_currency || "USD" },
        { label: "Distribution", value: activeCommercial.distribution_type || "N/A" },
      ]}
    />
  );
}

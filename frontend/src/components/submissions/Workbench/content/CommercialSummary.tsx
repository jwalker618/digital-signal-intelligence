"use client";

/**
 * Commercial terms summary — entity, premium, currency, distribution.
 * Body content for a StandardCard(titled "Commercial Summary").
 */

import { useDsiStore } from "@/store/dsiStore";
import { formatNumber } from "@/lib/format";

interface Row {
  label: string;
  value: React.ReactNode;
}

export default function CommercialSummary() {
  const { activeCommercial } = useDsiStore() as any;

  if (!activeCommercial) {
    return <p className="dsi-user-message">No commercial terms available</p>;
  }

  const rows: Row[] = [
    { label: "Entity", value: activeCommercial.entity_name || "N/A" },
    { label: "Offered Premium", value: formatNumber(activeCommercial.offered_premium, 0) },
    { label: "Gross Premium", value: formatNumber(activeCommercial.gross_premium, 0) },
    { label: "Currency", value: activeCommercial.base_currency || "USD" },
    { label: "Distribution", value: activeCommercial.distribution_type || "N/A" },
  ];

  return (
    <div>
      {rows.map((r) => (
        <div key={r.label} className="flex justify-between">
          <span className="dsi-analysis-description">{r.label}</span>
          <span className="dsi-analysis-item">{r.value}</span>
        </div>
      ))}
    </div>
  );
}

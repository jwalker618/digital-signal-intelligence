"use client";

/**
 * Risk terms summary — deductible, SIR, aggregate limit, coverage terms.
 * Body content for a StandardCard(titled "Risk Terms Summary").
 */

import { useDsiStore } from "@/store/dsiStore";
import { formatNumber } from "@/lib/format";

interface Row {
  label: string;
  value: React.ReactNode;
}

export default function RiskTermsSummary() {
  const { activeRisk } = useDsiStore() as any;

  if (!activeRisk) {
    return <p className="dsi-user-message">No risk terms available</p>;
  }

  const coverageCount = activeRisk.coverage_terms
    ? `${Object.keys(activeRisk.coverage_terms).length} terms`
    : "N/A";

  const rows: Row[] = [
    { label: "Deductible Type", value: activeRisk.deductible_type || "N/A" },
    { label: "Deductible Amount", value: formatNumber(activeRisk.deductible_amount, 0) },
    { label: "SIR", value: formatNumber(activeRisk.sir_amount, 0, "n/a") },
    { label: "Aggregate Limit", value: formatNumber(activeRisk.aggregate_limit, 0, "n/a") },
    { label: "Coverage Terms", value: coverageCount },
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

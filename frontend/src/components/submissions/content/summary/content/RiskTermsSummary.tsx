"use client";

/**
 * Risk terms summary — deductible, SIR, aggregate limit, coverage terms.
 * Body content for a StandardCard titled "Risk Terms Summary".
 */

import { useDsiStore } from "@/store/dsiStore";
import { formatNumber, formatText } from "@/lib/format";
import { LabelValueList } from "@/components/base/content/primatives";

export default function RiskTermsSummary() {
  const { activeRisk } = useDsiStore();

  if (!activeRisk) {
    return <p className="generate-comment-message">No risk terms available</p>;
  }

  const coverageCount = activeRisk.coverage_terms
    ? `${Object.keys(activeRisk.coverage_terms).length} terms`
    : "N/A";

  return (
    <LabelValueList
      rows={[
        { label: "Deductible Type", value: formatText(activeRisk.deductible_type, "upper") || "N/A" },
        { label: "Deductible Amount", value: formatNumber(activeRisk.deductible_amount, 0) },
        { label: "SIR", value: formatNumber(activeRisk.sir_amount, 0, "n/a") },
        { label: "Aggregate Limit", value: formatNumber(activeRisk.aggregate_limit, 0, "n/a") },
        { label: "Coverage Terms", value: coverageCount },
      ]}
    />
  );
}

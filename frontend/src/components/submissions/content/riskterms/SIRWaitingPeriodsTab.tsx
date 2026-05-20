"use client";

import { useDsiStore } from "@/store/dsiStore";
import SectionCard from "@/components/shared/SectionCard";
import { MetricCard, LabelValueList } from "@/components/base/content/primatives";
import { Clock, Shield, DollarSign } from "lucide-react";
import { formatCurrency, formatNumber, formatText } from "@/lib/format";

export default function SIRWaitingPeriodsTab() {
  const { activeSubmission, activeQuote, activeVersion, activeRisk } = useDsiStore();

  if (!activeSubmission || !activeVersion) return null;

  const rt = activeRisk;

  return (
    <div className="w-full no-scrollbar pb-12 pt-generate-pad">
    
      <SectionCard icon={Shield} title="Self-Insured Retention (SIR)">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 px-generate-pad py-4">
          <MetricCard
            tone={rt.sir_applies ? "warning" : undefined}
            label="SIR Applies"
            value={rt.sir_applies ? "YES" : "No"}
          />
          <MetricCard
            label="SIR Amount"
            value={rt.sir_amount != null ? formatCurrency(rt.sir_amount) : "N/A"}
          />
          <MetricCard label="Deductible Currency" value={rt.deductible_currency || "USD"} />
        </div>
      </SectionCard>

      <SectionCard icon={Clock} title="Waiting Periods">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 px-generate-pad py-4">
          <MetricCard
            tone={rt.waiting_period_hours ? "info" : undefined}
            label="Waiting Period"
            value={rt.waiting_period_hours != null ? `${rt.waiting_period_hours} hours` : "None"}
            subtext={
              rt.waiting_period_hours != null && rt.waiting_period_hours > 0
                ? `(${formatNumber(rt.waiting_period_hours / 24, 1)} days)`
                : undefined
            }
          />
          <MetricCard
            label="Waiting Period Type"
            value={formatText(rt.waiting_period_type, "capitalize", "N/A")}
          />
        </div>
      </SectionCard>

      <SectionCard icon={DollarSign} title="Context">
        <LabelValueList
          className="px-generate-pad py-4"
          rows={[
            { label: "Deductible Type", value: formatText(rt.deductible_type, "capitalize", "N/A") },
            { label: "Deductible Amount", value: formatCurrency(rt.deductible_amount) },
            { label: "Deductible Basis", value: formatText(rt.deductible_basis, "capitalize", "N/A") },
          ]}
        />
      </SectionCard>
    </div>
  );
}

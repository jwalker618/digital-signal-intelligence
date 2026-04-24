"use client";

import { useDsiStore } from "@/store/dsiStore";
import SectionCard from "@/components/shared/SectionCard";
import KeyDetailsBar from "@/components/base/keyDetailsBar";
import { MetricCard, LabelValueList } from "@/components/base/content/primatives";
import { RefreshCw, Layers, DollarSign } from "lucide-react";
import { formatCurrency, formatPercent, formatText } from "@/lib/format";

export default function AggregateReinstatementTab() {
  const { activeSubmission, activeQuote, activeVersion, activeRisk } = useDsiStore();

  if (!activeSubmission || !activeVersion) return null;

  const rt = activeRisk;
  const reinstatementsSubtext =
    rt.reinstatements != null && rt.reinstatements > 0
      ? rt.reinstatements === 1
        ? "1 reinstatement available"
        : `${rt.reinstatements} reinstatements available`
      : undefined;

  return (
    <div className="w-full no-scrollbar animate-in fade-in duration-500 pb-12 pt-3">
      <KeyDetailsBar
        status={activeQuote?.status}
        validFrom={activeQuote?.valid_from}
        validUntil={activeQuote?.valid_until}
        boundAt={activeQuote?.bound_at}
        policyNumber={activeQuote?.policy_number}
        submissionCode={activeSubmission?.submission_code}
        quoteCode={activeQuote?.quote_code}
      />

      <SectionCard icon={Layers} title="Aggregate Limits">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 px-generate-pad py-4">
          <MetricCard tone="selected" label="Aggregate Limit" value={formatCurrency(rt.aggregate_limit)} />
          <MetricCard label="Aggregate Deductible" value={formatCurrency(rt.aggregate_deductible)} />
          <MetricCard
            label="Aggregate Basis"
            value={formatText(rt.aggregate_basis, "capitalize", "N/A")}
          />
        </div>
      </SectionCard>

      <SectionCard icon={RefreshCw} title="Reinstatement Provisions">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 px-generate-pad py-4">
          <MetricCard
            tone={rt.reinstatements ? "info" : undefined}
            label="Reinstatements"
            value={rt.reinstatements != null ? rt.reinstatements : "N/A"}
            subtext={reinstatementsSubtext}
          />
          <MetricCard
            label="Reinstatement Rate"
            value={rt.reinstatement_rate != null ? formatPercent(rt.reinstatement_rate) : "N/A"}
            subtext={rt.reinstatement_rate != null ? "of original premium per reinstatement" : undefined}
          />
        </div>
      </SectionCard>

      {(rt.attachment_point != null || rt.layer_limit != null) && (
        <SectionCard icon={DollarSign} title="Layer Details">
          <LabelValueList
            className="px-generate-pad py-4"
            rows={[
              { label: "Attachment Point", value: formatCurrency(rt.attachment_point) },
              { label: "Layer Limit", value: formatCurrency(rt.layer_limit) },
            ]}
          />
        </SectionCard>
      )}
    </div>
  );
}

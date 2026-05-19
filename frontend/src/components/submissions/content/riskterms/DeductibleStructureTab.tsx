"use client";

import { useDsiStore } from "@/store/dsiStore";
import SectionCard from "@/components/shared/SectionCard";
import KeyDetailsBar from "@/components/base/keyDetailsBar";
import { MetricCard, LabelValueList } from "@/components/base/content/primatives";
import { Layers, DollarSign, Shield } from "lucide-react";
import { formatCurrency, formatText } from "@/lib/format";

const DEDUCTIBLE_TYPE_LABEL: Record<string, string> = {
  per_occurrence: "Per Occurrence",
  aggregate: "Aggregate",
  each_and_every: "Each & Every",
};

export default function DeductibleStructureTab() {
  const { activeSubmission, activeQuote, activeVersion, activeRisk } = useDsiStore();

  if (!activeSubmission || !activeVersion) return null;

  const rt = activeRisk;
  const subLimits = (rt.sub_limits ?? {}) as Record<string, unknown>;

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

      <SectionCard icon={Layers} title="Deductible Overview">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 px-generate-pad py-4">
          <MetricCard
            tone="selected"
            label="Deductible Type"
            value={DEDUCTIBLE_TYPE_LABEL[rt.deductible_type] || rt.deductible_type || "N/A"}
          />
          <MetricCard label="Deductible Amount" value={formatCurrency(rt.deductible_amount)} />
          <MetricCard label="Currency" value={rt.deductible_currency || "USD"} />
          <MetricCard label="Basis" value={formatText(rt.deductible_basis, "capitalize", "N/A")} />
        </div>
      </SectionCard>

      {(rt.attachment_point != null || rt.layer_limit != null) && (
        <SectionCard icon={Shield} title="Attachment & Layer">
          <LabelValueList
            className="px-generate-pad py-4"
            rows={[
              { label: "Attachment Point", value: formatCurrency(rt.attachment_point) },
              { label: "Layer Limit", value: formatCurrency(rt.layer_limit) },
            ]}
          />
        </SectionCard>
      )}

      {Object.keys(subLimits).length > 0 && (
        <SectionCard icon={DollarSign} title="Sub-Limits">
          <LabelValueList
            className="px-generate-pad py-4"
            rows={Object.entries(subLimits).map(([key, value]) => ({
              key,
              label: formatText(key, "capitalize"),
              value: typeof value === "number" ? formatCurrency(value) : String(value),
            }))}
          />
        </SectionCard>
      )}
    </div>
  );
}

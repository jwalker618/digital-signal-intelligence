"use client";

import { useDsiStore } from "@/store/dsiStore";
import { CardGrid, StandardCard } from "@/components/base/cards";
import { MetricCard, LabelValueList } from "@/components/base/content/primatives";
import { Layers, DollarSign, Shield } from "lucide-react";
import { formatCurrency, formatText } from "@/lib/format";

const DEDUCTIBLE_TYPE_LABEL: Record<string, string> = {
  per_occurrence: "Per Occurrence",
  aggregate: "Aggregate",
  each_and_every: "Each & Every",
};

export default function DeductibleStructureTab() {
  const { activeSubmission, activeVersion, activeRisk } = useDsiStore();

  if (!activeSubmission || !activeVersion) return null;

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const rt = activeRisk as any;
  const subLimits = (rt.sub_limits ?? {}) as Record<string, unknown>;

  return (
    <div className="w-full pb-12 pt-generate-pad">
      <CardGrid cols="grid-cols-1" className="gap-4">

        <StandardCard lucideIcon={Layers} title="Deductible Overview">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-generate-pad py-2">
            <MetricCard
              tone="selected"
              label="Deductible Type"
              value={DEDUCTIBLE_TYPE_LABEL[rt.deductible_type] || rt.deductible_type || "N/A"}
            />
            <MetricCard label="Deductible Amount" value={formatCurrency(rt.deductible_amount)} />
            <MetricCard label="Currency" value={rt.deductible_currency || "USD"} />
            <MetricCard label="Basis" value={formatText(rt.deductible_basis, "capitalize", "N/A")} />
          </div>
        </StandardCard>

        {(rt.attachment_point != null || rt.layer_limit != null) && (
          <StandardCard lucideIcon={Shield} title="Attachment & Layer">
            <LabelValueList
              className="py-2"
              rows={[
                { label: "Attachment Point", value: formatCurrency(rt.attachment_point) },
                { label: "Layer Limit", value: formatCurrency(rt.layer_limit) },
              ]}
            />
          </StandardCard>
        )}

        {Object.keys(subLimits).length > 0 && (
          <StandardCard lucideIcon={DollarSign} title="Sub-Limits">
            <LabelValueList
              className="py-2"
              rows={Object.entries(subLimits).map(([key, value]) => ({
                key,
                label: formatText(key, "capitalize"),
                value: typeof value === "number" ? formatCurrency(value) : String(value),
              }))}
            />
          </StandardCard>
        )}

      </CardGrid>
    </div>
  );
}

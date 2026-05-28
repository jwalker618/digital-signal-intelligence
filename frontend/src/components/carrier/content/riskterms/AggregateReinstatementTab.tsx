"use client";

import { useDsiStore } from "@/store/dsiStore";
import { CardGrid, StandardCard } from "@/components/base/cards";
import { MetricCard, LabelValueList } from "@/components/base/content/primatives";
import { RefreshCw, Layers, DollarSign } from "lucide-react";
import { formatCurrency, formatPercent, formatText } from "@/lib/format";

export default function AggregateReinstatementTab() {
  const { activeSubmission, activeVersion, activeRisk } = useDsiStore();

  if (!activeSubmission || !activeVersion) return null;

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const rt = activeRisk as any;
  const reinstatementsSubtext =
    rt.reinstatements != null && rt.reinstatements > 0
      ? rt.reinstatements === 1
        ? "1 reinstatement available"
        : `${rt.reinstatements} reinstatements available`
      : undefined;

  return (
    <div className="w-full pb-12 pt-generate-pad">
      <CardGrid cols="grid-cols-1" className="gap-4">

        <StandardCard lucideIcon={Layers} title="Aggregate Limits">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-generate-pad py-2">
            <MetricCard tone="selected" label="Aggregate Limit" value={formatCurrency(rt.aggregate_limit)} />
            <MetricCard label="Aggregate Deductible" value={formatCurrency(rt.aggregate_deductible)} />
            <MetricCard
              label="Aggregate Basis"
              value={formatText(rt.aggregate_basis, "capitalize", "N/A")}
            />
          </div>
        </StandardCard>

        <StandardCard lucideIcon={RefreshCw} title="Reinstatement Provisions">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-generate-pad py-2">
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
        </StandardCard>

        {(rt.attachment_point != null || rt.layer_limit != null) && (
          <StandardCard lucideIcon={DollarSign} title="Layer Details">
            <LabelValueList
              className="py-2"
              rows={[
                { label: "Attachment Point", value: formatCurrency(rt.attachment_point) },
                { label: "Layer Limit", value: formatCurrency(rt.layer_limit) },
              ]}
            />
          </StandardCard>
        )}

      </CardGrid>
    </div>
  );
}

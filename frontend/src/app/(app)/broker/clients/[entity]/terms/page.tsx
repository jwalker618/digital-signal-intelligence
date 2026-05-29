"use client";

import { Scale } from "lucide-react";
import { Card } from "@/components/ui/card";
import { Chip } from "@/components/ui/chip";
import { WorkArea } from "@/components/ui/work-area";
import { LabelRow } from "@/components/ui/label-row";
import { formatCurrency } from "@/lib/format";
import { useClientWorkbench } from "../_lib/context";
import { decisionTone } from "../_lib/helpers";

export default function RiskTermsPage() {
  const cw = useClientWorkbench();
  if (!cw) return null;

  return (
    <WorkArea className="lg:grid-cols-3">
      {cw.coverages.map((c) => (
        <Card
          key={c.code}
          header={`${c.line} · risk terms`}
          icon={Scale}
          pad="md"
          headerRight={
            <Chip variant={decisionTone(c.decision)} size="sm">
              {c.decision ?? "—"}
            </Chip>
          }
        >
          <LabelRow
            label="Deductible"
            value={c.deductible != null ? <span className="font-mono">{formatCurrency(c.deductible)}</span> : "—"}
          />
          <LabelRow
            label="SIR"
            value={
              c.sir_applies
                ? c.sir_amount != null
                  ? formatCurrency(c.sir_amount)
                  : "Yes"
                : "No"
            }
          />
          <LabelRow
            label="Waiting period"
            value={c.waiting_period_hours != null ? `${c.waiting_period_hours} hours` : "—"}
          />
          <LabelRow
            label="Aggregate"
            value={c.aggregate_limit != null ? <span className="font-mono">{formatCurrency(c.aggregate_limit)}</span> : "—"}
          />
          <LabelRow
            label="Reinstatements"
            value={
              c.reinstatements != null
                ? c.reinstatements <= 0
                  ? "None"
                  : `${c.reinstatements}${c.reinstatement_rate != null ? ` · ${Math.round(c.reinstatement_rate * 100)}% of premium` : ""}`
                : "—"
            }
          />
          <LabelRow label="Trigger" value={c.coverage_trigger ?? "—"} />
          <LabelRow label="Extensions" value={c.extensions_count ?? "—"} />
          <LabelRow label="Exclusions" value={c.exclusions_count ?? "—"} />
          <LabelRow
            label="Sub-limits"
            value={c.sub_limits_label ? <span className="font-mono">{c.sub_limits_label}</span> : "—"}
          />
        </Card>
      ))}
    </WorkArea>
  );
}

"use client";

import { BarChart3, Layers, RefreshCw } from "lucide-react";
import { Card } from "@/components/ui/card";
import { WorkArea } from "@/components/ui/work-area";
import { Micro } from "@/components/ui/typography";
import { KpiSnug } from "@/components/ui/kpi-snug";
import { LabelRow } from "@/components/ui/label-row";
import { PageLoading } from "@/components/base/pageStates";
import { useDsiStore, type ApiRecord } from "@/store/dsiStore";
import { formatCurrency, formatText } from "@/lib/format";
import { numOrNull, strOrNull } from "@/lib/coerce";

/* ============================================================
 * Aggregate & Reinstatement — mirrors reim_wb_c.jsx WbAggregate.
 *
 * Three rows:
 *   1. Aggregate limits (3 KPIs)
 *   2. Reinstatement provisions (2 KPIs with subcaptions)
 *   3. Layer detail (2-col DefList)
 * ============================================================ */

export default function AggregateAndReinstatementPage() {
  const risk = useDsiStore((s) => s.activeRisk) as ApiRecord | null;

  if (!risk) {
    return (
      <>
        <PageLoading />
      </>
    );
  }

  const aggLimit = numOrNull(risk.aggregate_limit);
  const aggDed = numOrNull(risk.aggregate_deductible);
  const aggBasis = strOrNull(risk.aggregate_basis);
  const reinstatements = numOrNull(risk.reinstatements);
  const reinstateRate = numOrNull(risk.reinstatement_rate);
  const attachment = numOrNull(risk.attachment_point);
  const layerLimit = numOrNull(risk.layer_limit);

  return (
    <>
      <WorkArea>
        <Card header="Aggregate limits" icon={Layers} pad="md">
          <div className="grid grid-cols-3 gap-4">
            <KpiSnug
              label="Aggregate limit"
              value={aggLimit != null ? formatCurrency(aggLimit) : "—"}
              tone="info"
            />
            <KpiSnug
              label="Aggregate deductible"
              value={aggDed != null ? formatCurrency(aggDed) : "—"}
            />
            <KpiSnug
              label="Basis"
              value={
                aggBasis ? formatText(aggBasis.replace(/_/g, " "), "capitalize") : "—"
              }
            />
          </div>
        </Card>

        <Card header="Reinstatement provisions" icon={RefreshCw} pad="md">
          <div className="grid grid-cols-2 gap-4">
            <KpiSnug
              label="Reinstatements"
              value={reinstatements != null ? String(reinstatements) : "—"}
              delta={
                reinstatements != null ? (
                  <Micro>available during period</Micro>
                ) : undefined
              }
            />
            <KpiSnug
              label="Rate"
              value={
                reinstateRate != null ? `${(reinstateRate * 100).toFixed(0)}%` : "—"
              }
              delta={
                reinstateRate != null ? (
                  <Micro>of original premium per reinstatement</Micro>
                ) : undefined
              }
            />
          </div>
        </Card>

        <Card header="Layer detail" icon={BarChart3} pad="md">
          <div className="grid gap-4 md:grid-cols-2">
            <LabelRow
              label="Attachment point"
              value={attachment != null ? formatCurrency(attachment) : "—"}
            />
            <LabelRow
              label="Layer limit"
              value={layerLimit != null ? formatCurrency(layerLimit) : "—"}
            />
            <LabelRow
              label="Position"
              value={
                attachment != null && attachment <= 0
                  ? "Primary · ground-up"
                  : attachment != null
                    ? "Excess"
                    : "—"
              }
            />
          </div>
        </Card>
      </WorkArea>
    </>
  );
}



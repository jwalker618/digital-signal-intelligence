"use client";

import { Clock, Shield } from "lucide-react";
import { Card } from "@/components/ui/card";
import { WorkArea } from "@/components/ui/work-area";
import { Micro } from "@/components/ui/typography";
import { KpiSnug } from "@/components/ui/kpi-snug";
import { PageLoading } from "@/components/base/pageStates";
import { useDsiStore, type ApiRecord } from "@/store/dsiStore";
import { formatCurrency, formatText } from "@/lib/format";
import { numOrNull, strOrNull, boolOrNull } from "@/lib/coerce";

/* ============================================================
 * SIR & Waiting Periods — mirrors reim_wb_c.jsx WbSir.
 *
 * Two rows:
 *   1. Self-insured retention — 3 KPIs + footer explanation
 *   2. Waiting periods — 3 KPIs
 * ============================================================ */

export default function SirAndWaitingPage() {
  const risk = useDsiStore((s) => s.activeRisk) as ApiRecord | null;

  if (!risk) {
    return (
      <>
        <PageLoading />
      </>
    );
  }

  const sirApplies = boolOrNull(risk.sir_applies);
  const sirAmount = numOrNull(risk.sir_amount);
  const deductibleAmount = numOrNull(risk.deductible_amount);
  const sirCurrency = strOrNull(risk.deductible_currency) ?? "USD";

  const waitingHours = numOrNull(risk.waiting_period_hours);
  const waitingType = strOrNull(risk.waiting_period_type);

  return (
    <>
      <WorkArea>
        <Card header="Self-insured retention" icon={Shield} pad="md">
          <div className="grid grid-cols-3 gap-4">
            <KpiSnug
              label="SIR applies"
              value={sirApplies != null ? (sirApplies ? "Yes" : "No") : "—"}
            />
            <KpiSnug
              label="Amount"
              value={sirAmount != null ? formatCurrency(sirAmount) : "—"}
            />
            <KpiSnug label="Currency" value={sirCurrency} />
          </div>
          {sirApplies === false && deductibleAmount != null && (
            <Micro className="mt-3.5 block border-t border-rule pt-3">
              No self-insured retention is structured into this risk. The standard{" "}
              <strong>{formatCurrency(deductibleAmount)}</strong> deductible applies
              per occurrence (see Deductible Structure).
            </Micro>
          )}
        </Card>

        <Card header="Waiting periods" icon={Clock} pad="md">
          <div className="grid grid-cols-3 gap-4">
            <KpiSnug
              label="Period"
              value={waitingHours != null ? `${waitingHours} hours` : "—"}
              delta={
                waitingHours != null ? (
                  <Micro>{(waitingHours / 24).toFixed(2)} days</Micro>
                ) : undefined
              }
            />
            <KpiSnug
              label="Type"
              value={
                waitingType
                  ? formatText(waitingType.replace(/_/g, " "), "capitalize")
                  : "—"
              }
            />
            <KpiSnug label="Trigger" value="Time deductible" />
          </div>
        </Card>
      </WorkArea>
    </>
  );
}




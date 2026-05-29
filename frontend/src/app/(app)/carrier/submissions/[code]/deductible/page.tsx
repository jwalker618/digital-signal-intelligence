"use client";

import { Layers, MinusCircle } from "lucide-react";
import { WorkbenchTopbar } from "@/components/chrome/workbench-topbar";
import { Card } from "@/components/ui/card";
import { WorkArea } from "@/components/ui/work-area";
import { Body, Micro } from "@/components/ui/typography";
import { KpiSnug } from "@/components/ui/kpi-snug";
import { PageLoading } from "@/components/base/pageStates";
import { useDsiStore, type ApiRecord } from "@/store/dsiStore";
import { formatCurrency, formatText } from "@/lib/format";

/* ============================================================
 * Deductible Structure — mirrors reim_wb_c.jsx WbDeductible.
 *
 * Two rows:
 *   1. Deductible — 4 KPIs (Type / Amount / Currency / Basis)
 *   2. Sub-limits — flat list of label / amount rows from sub_limits JSONB
 * ============================================================ */

export default function DeductibleStructurePage() {
  const risk = useDsiStore((s) => s.activeRisk) as ApiRecord | null;

  if (!risk) {
    return (
      <>
        <WorkbenchTopbar activeTabLabel="Deductible Structure" />
        <PageLoading />
      </>
    );
  }

  const type = strOrNull(risk.deductible_type);
  const amount = numOrNull(risk.deductible_amount);
  const currency = strOrNull(risk.deductible_currency) ?? "USD";
  const basis = strOrNull(risk.deductible_basis);
  const subLimits = Array.isArray(risk.sub_limits)
    ? (risk.sub_limits as ApiRecord[])
    : [];

  return (
    <>
      <WorkbenchTopbar activeTabLabel="Deductible Structure" />
      <WorkArea>
        <Card header="Deductible" icon={Layers} pad="md">
          <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
            <KpiSnug
              label="Type"
              value={type ? formatText(type.replace(/_/g, " "), "capitalize") : "—"}
            />
            <KpiSnug
              label="Amount"
              value={amount != null ? formatCurrency(amount) : "—"}
            />
            <KpiSnug label="Currency" value={currency} />
            <KpiSnug
              label="Basis"
              value={basis ? formatText(basis.replace(/_/g, " "), "capitalize") : "—"}
            />
          </div>
        </Card>

        <Card
          header={`Sub-limits · ${subLimits.length}`}
          icon={MinusCircle}
          pad="md"
        >
          {subLimits.length === 0 ? (
            <Body className="italic">No sub-limits recorded.</Body>
          ) : (
            subLimits.map((s, i) => {
              const peril = strOrNull(s.peril ?? s.label ?? s.name);
              const sub = numOrNull(s.sub_limit ?? s.amount);
              const subDed = numOrNull(s.sub_deductible);
              return (
                <div
                  key={`${peril}-${i}`}
                  className={`flex items-baseline justify-between py-2.5 ${
                    i < subLimits.length - 1 ? "border-b border-rule" : ""
                  }`}
                >
                  <span className="text-[13px]">
                    {peril ? formatText(peril.replace(/_/g, " "), "capitalize") : "—"}
                    {subDed != null && (
                      <Micro className="ml-2 inline">
                        ded {formatCurrency(subDed)}
                      </Micro>
                    )}
                  </span>
                  <span className="font-mono text-[13px] font-bold tabular-nums">
                    {sub != null ? formatCurrency(sub) : "—"}
                  </span>
                </div>
              );
            })
          )}
        </Card>
      </WorkArea>
    </>
  );
}

function numOrNull(v: unknown): number | null {
  if (v == null) return null;
  const n = Number(v);
  return Number.isFinite(n) ? n : null;
}

function strOrNull(v: unknown): string | null {
  if (v == null) return null;
  const s = String(v).trim();
  return s.length > 0 ? s : null;
}

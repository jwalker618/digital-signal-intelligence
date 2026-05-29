"use client";

import { Clock, Layers, Shield } from "lucide-react";
import { WorkbenchTopbar } from "@/components/chrome/workbench-topbar";
import { Card } from "@/components/ui/card";
import { NumDisplay, Body, Micro } from "@/components/ui/typography";
import { MiniKpi } from "@/components/ui/mini-kpi";
import { LabelRow } from "@/components/ui/label-row";
import { PageLoading } from "@/components/base/pageStates";
import { LooseRecordCard } from "@/components/base/loose-record";
import { useDsiStore } from "@/store/dsiStore";
import { formatCurrency } from "@/lib/format";

export default function SirPage() {
  const ver = useDsiStore((s) => s.activeVersion);
  const risk = useDsiStore((s) => s.activeRisk);
  const sub = useDsiStore((s) => s.activeSubmission);

  if (!sub) {
    return (
      <>
        <WorkbenchTopbar activeTabLabel="SIR & Waiting Periods" />
        <PageLoading message="Loading SIR detail…" />
      </>
    );
  }

  const fpd = (ver?.final_premium_detail ?? {}) as Record<string, unknown>;
  // RiskTermsDBRecord: sir_amount / deductible_amount / layer_limit; JSONB detail preferred when present
  const sir = Number(risk?.sir_amount ?? fpd.sir ?? 0);
  const deductible = Number(fpd.deductible ?? risk?.deductible_amount ?? 0);
  const limit = Number(fpd.limit ?? risk?.layer_limit ?? 0);
  const waitingHours = Number(risk?.waiting_period_hours ?? 0);
  // waiting_periods list not exposed by RiskTermsDBRecord; single waiting_period_hours used below
  const waitingPeriods =
    (risk?.waiting_periods as Array<Record<string, unknown>> | undefined) ?? [];

  return (
    <>
      <WorkbenchTopbar activeTabLabel="SIR & Waiting Periods" />
      <div className="flex-1 overflow-y-auto px-9 py-7">
        <div className="mx-auto grid max-w-[1080px] gap-6">
          {/* Self-insured retention */}
          <Card header="Self-insured retention" icon={Shield} pad="md">
            <div className="grid grid-cols-2 gap-6 sm:grid-cols-3">
              <MiniKpi label="SIR applies" value={sir > 0 ? "Yes" : "No"} />
              <MiniKpi
                label="Amount"
                value={sir > 0 ? formatCurrency(sir) : "—"}
              />
              <MiniKpi label="Currency" value={String(risk?.deductible_currency ?? "USD")} />
            </div>
            {sir === 0 && deductible > 0 && (
              <Micro className="mt-3 block border-t border-rule pt-3">
                No self-insured retention is structured into this risk. The{" "}
                {formatCurrency(deductible)} deductible applies (see Deductible
                Structure).
              </Micro>
            )}
          </Card>

          {/* Layer visualization */}
          {(sir > 0 || deductible > 0 || limit > 0) && (
            <Card header="Layer cascade" icon={Layers} pad="lg">
              <div className="space-y-2">
                {sir > 0 && (
                  <LayerRow
                    label="Self-insured retention (SIR)"
                    value={formatCurrency(sir)}
                    sub="Insured absorbs first"
                    tone="warn"
                  />
                )}
                {deductible > 0 && (
                  <LayerRow
                    label="Deductible"
                    value={formatCurrency(deductible)}
                    sub="Insured contribution per claim"
                    tone="warn"
                  />
                )}
                {limit > 0 && (
                  <LayerRow
                    label="Carrier limit"
                    value={formatCurrency(limit)}
                    sub="Excess of SIR + deductible"
                    tone="pos"
                  />
                )}
              </div>
            </Card>
          )}

          {/* Waiting periods */}
          <Card header="Waiting periods" icon={Clock} pad="md" className="space-y-3">
            {waitingPeriods.length === 0 && waitingHours === 0 ? (
              <Body className="italic">No waiting period configured.</Body>
            ) : waitingPeriods.length > 0 ? (
              <ul className="divide-y divide-rule">
                {waitingPeriods.map((w, i) => (
                  <li
                    key={i}
                    className="flex items-baseline justify-between gap-3 py-2.5"
                  >
                    <div>
                      <p className="text-[13.5px] font-medium text-ink">
                        {String(w.name ?? w.coverage ?? "—")}
                      </p>
                      {w.note && (
                        <Micro className="mt-0.5 block">
                          {String(w.note)}
                        </Micro>
                      )}
                    </div>
                    <span className="font-semibold tabular-nums text-ink">
                      {w.hours != null
                        ? `${w.hours}h`
                        : w.days != null
                          ? `${w.days}d`
                          : "—"}
                    </span>
                  </li>
                ))}
              </ul>
            ) : (
              <LabelRow
                label="Waiting period"
                value={`${waitingHours} hours`}
              />
            )}
          </Card>

          <LooseRecordCard
            title="Detail"
            data={risk as Record<string, unknown> | null}
            fields={[
              { key: "sir_amount", label: "SIR", kind: "currency", hideIfEmpty: true },
              {
                key: "annual_aggregate_sir",
                label: "Annual aggregate SIR",
                kind: "currency",
                hideIfEmpty: true,
              },
              { key: "waiting_period_hours", label: "Waiting period (hours)", hideIfEmpty: true },
              { key: "retro_date", label: "Retro date", kind: "date", hideIfEmpty: true },
            ]}
          />
        </div>
      </div>
    </>
  );
}

function LayerRow({
  label,
  value,
  sub,
  tone,
}: {
  label: string;
  value: string;
  sub: string;
  tone: "pos" | "warn";
}) {
  return (
    <div
      className={`flex items-baseline justify-between gap-3 rounded-card border px-4 py-3 ${
        tone === "pos"
          ? "border-pos bg-pos-soft"
          : "border-warn bg-warn-soft"
      }`}
    >
      <div>
        <p className="text-[14px] font-semibold text-ink">{label}</p>
        <Micro>{sub}</Micro>
      </div>
      <NumDisplay size="md">{value}</NumDisplay>
    </div>
  );
}

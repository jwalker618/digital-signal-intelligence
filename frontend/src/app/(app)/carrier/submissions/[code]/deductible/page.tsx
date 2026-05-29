"use client";

import { Layers, MinusCircle } from "lucide-react";
import { WorkbenchTopbar } from "@/components/chrome/workbench-topbar";
import { Card } from "@/components/ui/card";
import { Chip } from "@/components/ui/chip";
import { Eyebrow, NumDisplay, Micro } from "@/components/ui/typography";
import { MiniKpi } from "@/components/ui/mini-kpi";
import { PageLoading } from "@/components/base/pageStates";
import { LooseRecordCard } from "@/components/base/loose-record";
import { useDsiStore } from "@/store/dsiStore";
import { formatCurrency } from "@/lib/format";
import { cn } from "@/lib/utils";

export default function DeductiblePage() {
  const ver = useDsiStore((s) => s.activeVersion);
  const risk = useDsiStore((s) => s.activeRisk);
  const sub = useDsiStore((s) => s.activeSubmission);

  if (!sub) {
    return (
      <>
        <WorkbenchTopbar activeTabLabel="Deductible Structure" />
        <PageLoading message="Loading deductible structure…" />
      </>
    );
  }

  const fpd = (ver?.final_premium_detail ?? {}) as Record<string, unknown>;
  const boundDeductible = Number(fpd.deductible ?? risk?.deductible ?? 0);
  const dedFactor = Number(fpd.deductible_factor ?? 1);

  const bands =
    (risk?.deductible_bands as Array<Record<string, unknown>> | undefined) ??
    (risk?.deductible_options as Array<Record<string, unknown>> | undefined) ??
    [];

  return (
    <>
      <WorkbenchTopbar activeTabLabel="Deductible Structure" />
      <div className="flex-1 overflow-y-auto px-9 py-7">
        <div className="mx-auto grid max-w-[1080px] gap-6">
          {/* Deductible */}
          <Card header="Deductible" icon={Layers} pad="md">
            <div className="grid grid-cols-2 gap-6 sm:grid-cols-4">
              <MiniKpi
                label="Type"
                value={
                  risk?.deductible_type
                    ? String(risk.deductible_type)
                    : "Per occurrence"
                }
              />
              <MiniKpi
                label="Amount"
                value={
                  boundDeductible > 0 ? formatCurrency(boundDeductible) : "—"
                }
              />
              <MiniKpi label="Currency" value={String(risk?.currency ?? "USD")} />
              <MiniKpi
                label="Basis"
                value={
                  risk?.deductible_basis
                    ? String(risk.deductible_basis)
                    : "Each claim"
                }
              />
            </div>
          </Card>

          {/* Bound deductible */}
          <Card variant="info" pad="lg" className="grid gap-6 sm:grid-cols-3">
            <div>
              <Eyebrow className="text-info-deep dark:text-info">
                Bound deductible
              </Eyebrow>
              <NumDisplay size="xl" className="mt-2 block">
                {boundDeductible > 0 ? formatCurrency(boundDeductible) : "—"}
              </NumDisplay>
            </div>
            <div>
              <Eyebrow>Applied factor</Eyebrow>
              <p className="mt-2 font-display text-[28px] font-semibold tabular-nums text-ink">
                ×{dedFactor.toFixed(3)}
              </p>
              <Micro className="mt-1 block">
                {dedFactor > 1
                  ? "premium loaded"
                  : dedFactor < 1
                    ? "premium credit"
                    : "neutral"}
              </Micro>
            </div>
            <div>
              <Eyebrow>Currency</Eyebrow>
              <p className="mt-2 font-display text-[28px] font-semibold tabular-nums text-ink">
                {String(risk?.currency ?? "USD")}
              </p>
            </div>
          </Card>

          {/* Band table */}
          {bands.length > 0 ? (
            <Card
              header={`Deductible options · ${bands.length}`}
              icon={MinusCircle}
              pad="none"
              className="overflow-hidden"
            >
              <table className="w-full table-fixed text-[13px]">
                <thead>
                  <tr className="border-b border-rule bg-surface-sunken/60 text-left">
                    <ColHead width="w-[28%]">Deductible</ColHead>
                    <ColHead width="w-[20%]">Factor</ColHead>
                    <ColHead width="w-[28%]">Premium</ColHead>
                    <ColHead width="w-[24%]">Selected</ColHead>
                  </tr>
                </thead>
                <tbody>
                  {bands.map((b, i) => {
                    const ded = Number(b.deductible ?? b.value ?? 0);
                    const factor = Number(b.factor ?? 1);
                    const premium = Number(b.premium ?? 0);
                    const isBound = Math.abs(ded - boundDeductible) < 0.01;
                    return (
                      <tr
                        key={i}
                        className={cn(
                          "border-b border-rule last:border-0 hover:bg-surface-sunken/40",
                          isBound && "bg-info-soft/50",
                        )}
                      >
                        <td className="px-5 py-2.5 font-semibold tabular-nums text-ink">
                          {formatCurrency(ded)}
                        </td>
                        <td className="px-5 py-2.5 tabular-nums text-ink-soft">
                          ×{factor.toFixed(3)}
                        </td>
                        <td className="px-5 py-2.5 tabular-nums text-ink">
                          {premium > 0 ? formatCurrency(premium) : "—"}
                        </td>
                        <td className="px-5 py-2.5">
                          {isBound && (
                            <Chip variant="info" size="sm">
                              Bound
                            </Chip>
                          )}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </Card>
          ) : (
            <LooseRecordCard
              title="Deductible terms"
              data={risk as Record<string, unknown> | null}
              fields={[
                { key: "deductible", label: "Deductible", kind: "currency" },
                { key: "deductible_factor", label: "Factor", kind: "factor" },
                { key: "deductible_type", label: "Type" },
                { key: "deductible_basis", label: "Basis" },
                { key: "waiting_period_hours", label: "Waiting period (hours)" },
              ]}
            />
          )}
        </div>
      </div>
    </>
  );
}

function ColHead({
  width,
  children,
}: {
  width: string;
  children: React.ReactNode;
}) {
  return (
    <th
      className={`px-5 py-2.5 text-[11px] font-semibold uppercase tracking-[0.08em] text-ink-mute ${width}`}
    >
      {children}
    </th>
  );
}

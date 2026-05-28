"use client";

import { RefreshCw } from "lucide-react";
import { WorkbenchTopbar } from "@/components/chrome/workbench-topbar";
import { Card } from "@/components/ui/card";
import { Chip } from "@/components/ui/chip";
import { Eyebrow, NumDisplay, Body, Micro } from "@/components/ui/typography";
import { LabelRow } from "@/components/ui/label-row";
import { PageLoading } from "@/components/base/pageStates";
import { LooseRecordCard } from "@/components/base/loose-record";
import { useDsiStore } from "@/store/dsiStore";
import { formatCurrency } from "@/lib/format";
import { cn } from "@/lib/utils";

export default function AggregatePage() {
  const ver = useDsiStore((s) => s.activeVersion);
  const risk = useDsiStore((s) => s.activeRisk);
  const sub = useDsiStore((s) => s.activeSubmission);

  if (!sub) {
    return (
      <>
        <WorkbenchTopbar activeTabLabel="Aggregate & Reinstatement" />
        <PageLoading message="Loading aggregate detail…" />
      </>
    );
  }

  const fpd = (ver?.final_premium_detail ?? {}) as Record<string, unknown>;
  const limit = Number(fpd.limit ?? risk?.limit ?? 0);
  const aggregate = Number(fpd.aggregate ?? risk?.aggregate_limit ?? limit);
  const reinstatementCount = Number(
    risk?.reinstatements ?? risk?.reinstatement_count ?? 0,
  );
  const reinstatementPremiumPct = Number(
    risk?.reinstatement_premium_pct ?? risk?.reinstatement_premium ?? 0,
  );
  const usedToDate = Number(risk?.aggregate_used_usd ?? 0);
  const usedPct = aggregate > 0 ? Math.min(1, usedToDate / aggregate) : 0;

  return (
    <>
      <WorkbenchTopbar activeTabLabel="Aggregate & Reinstatement" />
      <div className="flex-1 overflow-y-auto px-9 py-7">
        <div className="mx-auto grid max-w-[1080px] gap-6">
          <header>
            <Eyebrow>Risk terms</Eyebrow>
            <h1 className="mt-1 font-display text-[28px] font-semibold leading-tight text-ink">
              Aggregate & reinstatement
            </h1>
            <Body className="mt-2">
              How the annual cap sits relative to the per-occurrence limit,
              and what it costs to restore capacity after a loss.
            </Body>
          </header>

          {/* Aggregate vs per-occurrence */}
          <div className="grid gap-4 md:grid-cols-3">
            <Card pad="md" variant="info">
              <Eyebrow className="text-info-deep dark:text-info">
                Per occurrence
              </Eyebrow>
              <NumDisplay size="lg" className="mt-2 block">
                {limit > 0 ? formatCurrency(limit) : "—"}
              </NumDisplay>
            </Card>
            <Card pad="md">
              <Eyebrow>Annual aggregate</Eyebrow>
              <NumDisplay size="lg" className="mt-2 block">
                {aggregate > 0 ? formatCurrency(aggregate) : "—"}
              </NumDisplay>
              <Micro className="mt-1 block">
                {aggregate >= limit * 2
                  ? "≥ 2× per-occurrence"
                  : aggregate > limit
                    ? "> per-occurrence"
                    : "= per-occurrence"}
              </Micro>
            </Card>
            <Card pad="md">
              <Eyebrow>Reinstatements</Eyebrow>
              <NumDisplay size="lg" className="mt-2 block">
                {reinstatementCount}
              </NumDisplay>
              {reinstatementPremiumPct > 0 && (
                <Micro className="mt-1 block">
                  {reinstatementPremiumPct.toFixed(0)}% of annual premium each
                </Micro>
              )}
            </Card>
          </div>

          {/* Usage meter */}
          {aggregate > 0 && (
            <Card pad="md">
              <header className="mb-3 flex items-baseline justify-between">
                <Eyebrow>Aggregate erosion</Eyebrow>
                <span className="text-[13px] tabular-nums text-ink-soft">
                  {formatCurrency(usedToDate)} of {formatCurrency(aggregate)}
                </span>
              </header>
              <div className="h-3 overflow-hidden rounded-full bg-surface-sunken">
                <div
                  className={cn(
                    "h-full",
                    usedPct > 0.75
                      ? "bg-neg"
                      : usedPct > 0.4
                        ? "bg-warn"
                        : "bg-pos",
                  )}
                  style={{ width: `${usedPct * 100}%` }}
                />
              </div>
              <Micro className="mt-2 block">
                {usedPct > 0.75
                  ? "Aggregate nearly exhausted — reinstatement or new placement needed."
                  : usedPct > 0.4
                    ? "Aggregate partially drawn — track closely."
                    : "Healthy aggregate headroom."}
              </Micro>
            </Card>
          )}

          {/* Reinstatement detail */}
          {reinstatementCount > 0 && (
            <Card pad="md" className="flex items-start gap-3">
              <RefreshCw size={16} className="mt-0.5 shrink-0 text-info" />
              <div className="flex-1">
                <Eyebrow>Reinstatement provision</Eyebrow>
                <Body className="mt-1.5">
                  {reinstatementCount} reinstatement
                  {reinstatementCount === 1 ? "" : "s"} available
                  {reinstatementPremiumPct > 0 &&
                    ` at ${reinstatementPremiumPct.toFixed(0)}% of the annual premium`}
                  . Each restores the per-occurrence limit; the annual
                  aggregate cap remains the upper bound.
                </Body>
              </div>
            </Card>
          )}

          <LooseRecordCard
            title="Detail"
            data={risk as Record<string, unknown> | null}
            fields={[
              {
                key: "aggregate_limit",
                label: "Aggregate limit",
                kind: "currency",
                hideIfEmpty: true,
              },
              {
                key: "aggregate_basis",
                label: "Aggregate basis",
                hideIfEmpty: true,
              },
              {
                key: "stop_loss_attachment",
                label: "Stop-loss attachment",
                kind: "currency",
                hideIfEmpty: true,
              },
              {
                key: "stop_loss_premium",
                label: "Stop-loss premium",
                kind: "currency",
                hideIfEmpty: true,
              },
            ]}
          />
        </div>
      </div>
    </>
  );
}

"use client";

import { BarChart3, Layers, RefreshCw } from "lucide-react";
import { WorkbenchTopbar } from "@/components/chrome/workbench-topbar";
import { Card } from "@/components/ui/card";
import { Eyebrow, NumDisplay, Body, Micro } from "@/components/ui/typography";
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
  // RiskTermsDBRecord: layer_limit (per-occ), aggregate_limit, reinstatements, reinstatement_rate
  const limit = Number(fpd.limit ?? risk?.layer_limit ?? 0);
  const aggregate = Number(fpd.aggregate ?? risk?.aggregate_limit ?? limit);
  const reinstatementCount = Number(risk?.reinstatements ?? 0);
  // reinstatement_rate is a fraction (e.g. 1.0 = 100% of annual premium); display as a percentage
  const reinstatementPremiumPct = Number(risk?.reinstatement_rate ?? 0) * 100;
  // aggregate_used_usd / erosion-to-date is not exposed by RiskTermsDBRecord; only shown if JSONB detail carries it
  const usedToDate = Number(fpd.aggregate_used ?? 0);
  const hasUsage = usedToDate > 0;
  const usedPct = aggregate > 0 ? Math.min(1, usedToDate / aggregate) : 0;

  return (
    <>
      <WorkbenchTopbar activeTabLabel="Aggregate & Reinstatement" />
      <div className="flex-1 overflow-y-auto px-9 py-7">
        <div className="mx-auto grid max-w-[1080px] gap-6">
          {/* Aggregate limits */}
          <Card header="Aggregate limits" icon={Layers} pad="md">
            <div className="grid gap-6 md:grid-cols-3">
              <div>
                <Eyebrow className="text-info-deep dark:text-info">
                  Per occurrence
                </Eyebrow>
                <NumDisplay size="lg" className="mt-2 block text-info">
                  {limit > 0 ? formatCurrency(limit) : "—"}
                </NumDisplay>
              </div>
              <div>
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
              </div>
              <div>
                <Eyebrow>Reinstatements</Eyebrow>
                <NumDisplay size="lg" className="mt-2 block">
                  {reinstatementCount}
                </NumDisplay>
                {reinstatementPremiumPct > 0 && (
                  <Micro className="mt-1 block">
                    {reinstatementPremiumPct.toFixed(0)}% of annual premium each
                  </Micro>
                )}
              </div>
            </div>
          </Card>

          {/* Usage meter — only when erosion-to-date is actually available (JSONB) */}
          {aggregate > 0 && hasUsage && (
            <Card
              header="Aggregate erosion"
              icon={BarChart3}
              headerRight={
                <span className="tabular-nums">
                  {formatCurrency(usedToDate)} of {formatCurrency(aggregate)}
                </span>
              }
              pad="md"
            >
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
            <Card header="Reinstatement provisions" icon={RefreshCw} pad="md">
              <div className="flex-1">
                <Body>
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

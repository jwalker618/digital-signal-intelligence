"use client";

import { ArrowDown, Calculator } from "lucide-react";
import { WorkbenchTopbar } from "@/components/chrome/workbench-topbar";
import { Card } from "@/components/ui/card";
import { Chip } from "@/components/ui/chip";
import { Eyebrow, NumDisplay, Body, Micro } from "@/components/ui/typography";
import { MiniKpi } from "@/components/ui/mini-kpi";
import { PageLoading } from "@/components/base/pageStates";
import { useDsiStore } from "@/store/dsiStore";
import { formatCurrency, formatPercent } from "@/lib/format";
import { cn } from "@/lib/utils";

interface BuildStep {
  id: string;
  label: string;
  detail?: string;
  multiplier: number;
  /** Running total after this step. */
  cumulative: number;
}

/**
 * Premium Assembly — narrates the build-up from base premium through each
 * applied modifier to the final recommended premium. Vertical "story"
 * layout: each step shows the multiplier, the cumulative running total,
 * and the dollar delta it added.
 */
export default function PremiumAssemblyPage() {
  const ver = useDsiStore((s) => s.activeVersion);
  const commercial = useDsiStore((s) => s.activeCommercial);

  if (!ver) {
    return (
      <>
        <WorkbenchTopbar activeTabLabel="Premium Assembly" />
        <PageLoading message="Loading pricing data…" />
      </>
    );
  }

  const base = Number(ver.base_premium ?? 0);
  const finalPremium = Number(ver.final_premium ?? base);
  const lossMod = Number(ver.loss_combined_modifier ?? 1);
  const expMod = Number(ver.exposure_modifier ?? 1);
  const ilf = Number(ver.ilf_factor ?? 1);
  const fpd = (ver.final_premium_detail ?? {}) as Record<string, unknown>;
  const dedFactor = Number(fpd.deductible_factor ?? 1);

  const steps: BuildStep[] = [];
  let running = base;
  if (lossMod !== 1) {
    running = running * lossMod;
    steps.push({
      id: "loss",
      label: "Loss modifier",
      detail: "Frequency × severity vs. cohort",
      multiplier: lossMod,
      cumulative: running,
    });
  }
  if (expMod !== 1) {
    running = running * expMod;
    steps.push({
      id: "exp",
      label: "Exposure modifier",
      detail: "Size and complexity",
      multiplier: expMod,
      cumulative: running,
    });
  }
  if (ilf !== 1) {
    running = running * ilf;
    steps.push({
      id: "ilf",
      label: "ILF",
      detail: "Increased limit factor for the bound limit",
      multiplier: ilf,
      cumulative: running,
    });
  }
  if (dedFactor !== 1) {
    running = running * dedFactor;
    steps.push({
      id: "ded",
      label: "Deductible factor",
      detail: "Adjustment for the bound retention",
      multiplier: dedFactor,
      cumulative: running,
    });
  }

  const totalChange = base > 0 ? (finalPremium - base) / base : 0;

  const netPremium = commercial?.net_premium ?? null;
  const grossPremium = commercial?.gross_premium ?? null;
  const offeredPremium = commercial?.offered_premium ?? null;

  return (
    <>
      <WorkbenchTopbar activeTabLabel="Premium Assembly" />
      <div className="flex-1 overflow-y-auto px-9 py-7">
        <div className="mx-auto grid max-w-[920px] gap-6">
          {/* Hero — the answer first, math below */}
          {(offeredPremium != null ||
            netPremium != null ||
            grossPremium != null) && (
            <Card variant="info" pad="lg">
              <div className="grid items-end gap-6 md:grid-cols-[1.4fr_auto_auto_auto]">
                <div>
                  <Eyebrow className="text-info-deep dark:text-info">
                    Offered premium
                  </Eyebrow>
                  <NumDisplay size="xl" className="mt-2 block text-info">
                    {offeredPremium != null
                      ? formatCurrency(offeredPremium)
                      : grossPremium != null
                        ? formatCurrency(grossPremium)
                        : "—"}
                  </NumDisplay>
                </div>
                <MiniKpi
                  label="Net premium"
                  value={netPremium != null ? formatCurrency(netPremium) : "—"}
                />
                <MiniKpi
                  label="Gross premium"
                  value={
                    grossPremium != null ? formatCurrency(grossPremium) : "—"
                  }
                />
                <MiniKpi
                  label="Technical premium"
                  value={formatCurrency(finalPremium)}
                />
              </div>
            </Card>
          )}

          {/* Base */}
          <Card header="Premium build-up" icon={Calculator} pad="lg" className="space-y-1">
            <Micro className="block">Base premium</Micro>
            <NumDisplay size="xl">{formatCurrency(base)}</NumDisplay>
            <Micro className="block">starting point before modifiers</Micro>
          </Card>

          {/* Steps */}
          {steps.length === 0 ? (
            <Card pad="md" variant="info">
              <Body>
                No modifiers applied — the final premium equals the base.
              </Body>
            </Card>
          ) : (
            <div className="space-y-3">
              {steps.map((s, i) => {
                const prev = i === 0 ? base : steps[i - 1]!.cumulative;
                const delta = s.cumulative - prev;
                return (
                  <div key={s.id} className="space-y-2">
                    <ArrowDown
                      size={14}
                      className="mx-auto text-ink-mute"
                      aria-hidden
                    />
                    <Card
                      pad="md"
                      className={cn(
                        "grid gap-3 md:grid-cols-[1.5fr_auto_auto]",
                      )}
                    >
                      <div>
                        <p className="text-[14px] font-semibold text-ink">
                          {s.label}
                        </p>
                        {s.detail && <Micro className="block">{s.detail}</Micro>}
                      </div>
                      <div className="self-end md:self-auto">
                        <Micro className="block">Multiplier</Micro>
                        <span
                          className={cn(
                            "font-semibold tabular-nums",
                            s.multiplier > 1
                              ? "text-neg"
                              : s.multiplier < 1
                                ? "text-pos"
                                : "text-ink",
                          )}
                        >
                          ×{s.multiplier.toFixed(3)}
                        </span>
                      </div>
                      <div className="self-end text-right md:self-auto">
                        <Micro className="block">After</Micro>
                        <span className="font-semibold tabular-nums text-ink">
                          {formatCurrency(s.cumulative)}
                        </span>
                        <Chip
                          variant={delta > 0 ? "neg" : delta < 0 ? "pos" : "mute"}
                          size="sm"
                          className="ml-2"
                        >
                          {delta > 0 ? "+" : ""}
                          {formatCurrency(delta)}
                        </Chip>
                      </div>
                    </Card>
                  </div>
                );
              })}
            </div>
          )}

          {/* Final */}
          <ArrowDown size={14} className="mx-auto text-ink-mute" aria-hidden />
          <Card variant="info" pad="lg" className="space-y-2">
            <div className="flex items-baseline justify-between">
              <Eyebrow className="text-info-deep dark:text-info">
                Final premium
              </Eyebrow>
              <Chip
                variant={totalChange > 0 ? "neg" : totalChange < 0 ? "pos" : "mute"}
                size="sm"
              >
                {totalChange > 0 ? "+" : ""}
                {formatPercent(totalChange, 1)} from base
              </Chip>
            </div>
            <NumDisplay size="xl">{formatCurrency(finalPremium)}</NumDisplay>
            <Micro className="block">
              Difference: {totalChange >= 0 ? "+" : ""}
              {formatCurrency(finalPremium - base)} vs. base
            </Micro>
          </Card>
        </div>
      </div>
    </>
  );
}

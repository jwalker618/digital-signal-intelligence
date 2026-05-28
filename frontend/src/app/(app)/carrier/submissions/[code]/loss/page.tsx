"use client";

import { useEffect, useState } from "react";
import { AlertTriangle, TrendingDown, TrendingUp } from "lucide-react";
import { WorkbenchTopbar } from "@/components/chrome/workbench-topbar";
import { Card } from "@/components/ui/card";
import { Chip } from "@/components/ui/chip";
import { Eyebrow, NumDisplay, Body, Micro } from "@/components/ui/typography";
import { LabelRow } from "@/components/ui/label-row";
import { Sparkline } from "@/components/charts/sparkline";
import { PageError, PageLoading } from "@/components/base/pageStates";
import { useDsiStore } from "@/store/dsiStore";
import { formatCurrency, formatPercent } from "@/lib/format";

export default function LossAssessmentPage() {
  const sub = useDsiStore((s) => s.activeSubmission);
  const ver = useDsiStore((s) => s.activeVersion);
  const fetchLoss = useDsiStore((s) => s.fetchLossAnalytics);
  const trend = useDsiStore((s) => s.lossTrendDistribution);
  const cohort = useDsiStore((s) => s.lossCohortBenchmarks);
  const scatter = useDsiStore((s) => s.lossScatterData);

  const [state, setState] = useState<"loading" | "ok" | "error">("loading");
  const [err, setErr] = useState<string | null>(null);

  const coverage = sub?.coverage as string | undefined;
  useEffect(() => {
    if (!coverage) return;
    setState("loading");
    fetchLoss(coverage)
      .then(() => setState("ok"))
      .catch((e) => {
        setErr(e instanceof Error ? e.message : String(e));
        setState("error");
      });
  }, [coverage, fetchLoss]);

  if (!sub) {
    return (
      <>
        <WorkbenchTopbar activeTabLabel="Loss Assessment" />
        <PageLoading message="Loading submission…" />
      </>
    );
  }
  if (state === "loading") {
    return (
      <>
        <WorkbenchTopbar activeTabLabel="Loss Assessment" />
        <PageLoading message="Loading loss analytics…" />
      </>
    );
  }
  if (state === "error") {
    return (
      <>
        <WorkbenchTopbar activeTabLabel="Loss Assessment" />
        <PageError message={err ?? "Unknown error"} />
      </>
    );
  }

  const lossPropensity = Number(ver?.loss_propensity_score ?? 0);
  const severityPropensity = Number(ver?.severity_propensity_score ?? 0);
  const lossBand = String(ver?.loss_propensity_band ?? "");
  const lossTrend = String(ver?.loss_trend_direction ?? "");
  const lossMod = Number(ver?.loss_combined_modifier ?? 1);

  const trendPoints = (trend ?? [])
    .map((p) =>
      Number(
        (p as Record<string, unknown>).intensity ??
          (p as Record<string, unknown>).value ??
          0,
      ),
    )
    .filter((n) => !Number.isNaN(n));

  return (
    <>
      <WorkbenchTopbar activeTabLabel="Loss Assessment" />
      <div className="flex-1 overflow-y-auto px-9 py-7">
        <div className="mx-auto grid max-w-[1280px] gap-6">
          <header>
            <Eyebrow>Technical assessment</Eyebrow>
            <h1 className="mt-1 font-display text-[28px] font-semibold leading-tight text-ink">
              Loss assessment
            </h1>
            <Body className="mt-2">
              How this submission's loss profile compares to cohort, and the
              modifier flowing into the premium.
            </Body>
          </header>

          {/* Hero metrics */}
          <div className="grid gap-4 md:grid-cols-4">
            <Card pad="md" variant="info">
              <Eyebrow className="text-info-deep dark:text-info">
                Loss propensity
              </Eyebrow>
              <NumDisplay size="lg" className="mt-2 block">
                {lossPropensity > 0 ? lossPropensity.toFixed(0) : "—"}
              </NumDisplay>
              {lossBand && (
                <Chip
                  variant={
                    /low|good/i.test(lossBand)
                      ? "pos"
                      : /high|elev/i.test(lossBand)
                        ? "neg"
                        : "warn"
                  }
                  size="sm"
                  className="mt-2"
                >
                  {lossBand}
                </Chip>
              )}
            </Card>
            <Card pad="md">
              <Eyebrow>Severity propensity</Eyebrow>
              <NumDisplay size="lg" className="mt-2 block">
                {severityPropensity > 0 ? severityPropensity.toFixed(0) : "—"}
              </NumDisplay>
            </Card>
            <Card pad="md">
              <Eyebrow>Trend direction</Eyebrow>
              <p className="mt-2 flex items-center gap-2 text-[18px] font-semibold text-ink">
                {/improv|down|easing/i.test(lossTrend) ? (
                  <TrendingDown size={16} className="text-pos" />
                ) : /rising|wors|up/i.test(lossTrend) ? (
                  <TrendingUp size={16} className="text-neg" />
                ) : null}
                {lossTrend || "—"}
              </p>
            </Card>
            <Card pad="md" variant={lossMod > 1 ? "neg" : lossMod < 1 ? "pos" : "default"}>
              <Eyebrow
                className={lossMod > 1 ? "text-neg" : lossMod < 1 ? "text-pos" : ""}
              >
                Premium modifier
              </Eyebrow>
              <NumDisplay size="lg" className="mt-2 block">
                ×{lossMod.toFixed(3)}
              </NumDisplay>
              <Micro className="mt-1 block">
                {lossMod !== 1 ? formatPercent(lossMod - 1, 1) : "neutral"}
              </Micro>
            </Card>
          </div>

          {/* Sparkline trend */}
          {trendPoints.length > 0 && (
            <Card pad="md">
              <header className="mb-3 flex items-baseline justify-between">
                <Eyebrow>Loss intensity trend</Eyebrow>
                <Micro>{trendPoints.length} quarters</Micro>
              </header>
              <Sparkline
                points={trendPoints}
                height={80}
                color="var(--color-warn)"
              />
            </Card>
          )}

          {/* Cohort benchmarks */}
          {cohort.length > 0 && (
            <Card pad="md" className="overflow-hidden p-0">
              <header className="border-b border-rule px-5 py-3.5">
                <Eyebrow>Cohort benchmarks</Eyebrow>
              </header>
              <table className="w-full table-fixed text-[13px]">
                <thead>
                  <tr className="border-b border-rule bg-surface-sunken/60 text-left">
                    <ColHead width="w-[34%]">Metric</ColHead>
                    <ColHead width="w-[22%]">You</ColHead>
                    <ColHead width="w-[22%]">Cohort</ColHead>
                    <ColHead width="w-[22%]">Delta</ColHead>
                  </tr>
                </thead>
                <tbody>
                  {cohort.map((c, i) => {
                    const r = c as Record<string, unknown>;
                    const you = Number(r.value ?? r.entity_value ?? 0);
                    const peer = Number(r.cohort ?? r.cohort_value ?? r.peer ?? 0);
                    const delta = you - peer;
                    return (
                      <tr
                        key={i}
                        className="border-b border-rule last:border-0 hover:bg-surface-sunken/40"
                      >
                        <td className="px-5 py-2.5 text-ink">
                          {String(r.label ?? r.name ?? r.metric ?? "—")}
                        </td>
                        <td className="px-5 py-2.5 font-semibold tabular-nums text-ink">
                          {you.toLocaleString()}
                        </td>
                        <td className="px-5 py-2.5 tabular-nums text-ink-soft">
                          {peer.toLocaleString()}
                        </td>
                        <td
                          className={`px-5 py-2.5 tabular-nums ${
                            delta > 0
                              ? "text-neg"
                              : delta < 0
                                ? "text-pos"
                                : "text-ink-mute"
                          }`}
                        >
                          {delta > 0 ? "+" : ""}
                          {delta.toLocaleString()}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </Card>
          )}

          {cohort.length === 0 && scatter.length === 0 && (
            <Card pad="lg" className="flex items-start gap-3">
              <AlertTriangle size={18} className="mt-0.5 shrink-0 text-warn" />
              <div>
                <Eyebrow>No loss analytics</Eyebrow>
                <Body className="mt-1">
                  Either the backend hasn't computed loss analytics for this
                  coverage yet, or the API returned an empty response.
                </Body>
              </div>
            </Card>
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

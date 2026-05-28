"use client";

import { useEffect, useState } from "react";
import { Globe } from "lucide-react";
import { WorkbenchTopbar } from "@/components/chrome/workbench-topbar";
import { Card } from "@/components/ui/card";
import { Chip } from "@/components/ui/chip";
import { Eyebrow, NumDisplay, Body, Micro } from "@/components/ui/typography";
import { PageError, PageLoading } from "@/components/base/pageStates";
import { useDsiStore } from "@/store/dsiStore";
import { formatCurrency, formatPercent } from "@/lib/format";

export default function ExposureAssessmentPage() {
  const sub = useDsiStore((s) => s.activeSubmission);
  const ver = useDsiStore((s) => s.activeVersion);
  const fetchExp = useDsiStore((s) => s.fetchExposureAnalytics);
  const tier = useDsiStore((s) => s.exposureTierDistribution);
  const band = useDsiStore((s) => s.exposureBandBenchmarks);

  const [state, setState] = useState<"loading" | "ok" | "error">("loading");
  const [err, setErr] = useState<string | null>(null);

  const coverage = sub?.coverage as string | undefined;
  useEffect(() => {
    if (!coverage) return;
    setState("loading");
    fetchExp(coverage)
      .then(() => setState("ok"))
      .catch((e) => {
        setErr(e instanceof Error ? e.message : String(e));
        setState("error");
      });
  }, [coverage, fetchExp]);

  if (!sub)
    return (
      <>
        <WorkbenchTopbar activeTabLabel="Exposure Assessment" />
        <PageLoading message="Loading submission…" />
      </>
    );
  if (state === "loading")
    return (
      <>
        <WorkbenchTopbar activeTabLabel="Exposure Assessment" />
        <PageLoading message="Loading exposure analytics…" />
      </>
    );
  if (state === "error")
    return (
      <>
        <WorkbenchTopbar activeTabLabel="Exposure Assessment" />
        <PageError message={err ?? "Unknown error"} />
      </>
    );

  const exposureValue = Number(ver?.exposure_value ?? 0);
  const exposureBand = String(ver?.exposure_band_label ?? "");
  const sizeScore = Number(ver?.exposure_size_score ?? 0);
  const complexityScore = Number(ver?.exposure_complexity_score ?? 0);
  const expMod = Number(ver?.exposure_modifier ?? 1);

  return (
    <>
      <WorkbenchTopbar activeTabLabel="Exposure Assessment" />
      <div className="flex-1 overflow-y-auto px-9 py-7">
        <div className="mx-auto grid max-w-[1280px] gap-6">
          <header>
            <Eyebrow>Technical assessment</Eyebrow>
            <h1 className="mt-1 flex items-center gap-3 font-display text-[28px] font-semibold leading-tight text-ink">
              <Globe size={22} className="text-info" />
              Exposure assessment
            </h1>
            <Body className="mt-2">
              Aggregate exposure value, size and complexity scores, and the
              modifier that flows into the premium.
            </Body>
          </header>

          {/* Hero */}
          <Card variant="info" pad="lg" className="grid gap-6 sm:grid-cols-3">
            <div>
              <Eyebrow className="text-info-deep dark:text-info">
                Aggregate exposure
              </Eyebrow>
              <NumDisplay size="xl" className="mt-2 block">
                {exposureValue > 0 ? formatCurrency(exposureValue) : "—"}
              </NumDisplay>
              {exposureBand && (
                <Chip variant="info" size="sm" className="mt-2">
                  {exposureBand}
                </Chip>
              )}
            </div>
            <div>
              <Eyebrow>Size score</Eyebrow>
              <NumDisplay size="lg" className="mt-2 block">
                {sizeScore > 0 ? sizeScore.toFixed(0) : "—"}
              </NumDisplay>
            </div>
            <div>
              <Eyebrow>Complexity score</Eyebrow>
              <NumDisplay size="lg" className="mt-2 block">
                {complexityScore > 0 ? complexityScore.toFixed(0) : "—"}
              </NumDisplay>
            </div>
          </Card>

          {/* Modifier */}
          <Card
            pad="md"
            variant={expMod > 1 ? "neg" : expMod < 1 ? "pos" : "default"}
          >
            <div className="flex items-baseline justify-between">
              <Eyebrow
                className={
                  expMod > 1 ? "text-neg" : expMod < 1 ? "text-pos" : ""
                }
              >
                Exposure premium modifier
              </Eyebrow>
              <NumDisplay size="lg">×{expMod.toFixed(3)}</NumDisplay>
            </div>
            <Micro className="mt-1 block">
              {expMod !== 1
                ? `${formatPercent(expMod - 1, 1)} adjustment to premium`
                : "neutral — no exposure-driven adjustment"}
            </Micro>
          </Card>

          {/* Band benchmarks */}
          {band.length > 0 && (
            <Card pad="md" className="overflow-hidden p-0">
              <header className="border-b border-rule px-5 py-3.5">
                <Eyebrow>Band benchmarks ({band.length})</Eyebrow>
              </header>
              <table className="w-full table-fixed text-[13px]">
                <thead>
                  <tr className="border-b border-rule bg-surface-sunken/60 text-left">
                    <ColHead width="w-[36%]">Band</ColHead>
                    <ColHead width="w-[22%]">You</ColHead>
                    <ColHead width="w-[22%]">Cohort mean</ColHead>
                    <ColHead width="w-[20%]">Population</ColHead>
                  </tr>
                </thead>
                <tbody>
                  {band.map((b, i) => {
                    const r = b as Record<string, unknown>;
                    return (
                      <tr
                        key={i}
                        className="border-b border-rule last:border-0 hover:bg-surface-sunken/40"
                      >
                        <td className="px-5 py-2.5 text-ink">
                          {String(r.label ?? r.band ?? "—")}
                        </td>
                        <td className="px-5 py-2.5 font-semibold tabular-nums text-ink">
                          {r.value != null
                            ? Number(r.value).toLocaleString()
                            : "—"}
                        </td>
                        <td className="px-5 py-2.5 tabular-nums text-ink-soft">
                          {r.cohort_mean != null
                            ? Number(r.cohort_mean).toLocaleString()
                            : "—"}
                        </td>
                        <td className="px-5 py-2.5 tabular-nums text-ink-soft">
                          {r.population != null
                            ? Number(r.population).toLocaleString()
                            : "—"}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </Card>
          )}

          {/* Tier distribution */}
          {tier.length > 0 && (
            <Card pad="md">
              <Eyebrow className="mb-3">Tier distribution</Eyebrow>
              <ul className="space-y-2">
                {tier.map((t, i) => {
                  const r = t as Record<string, unknown>;
                  const pct = Number(r.share_pct ?? r.share ?? 0);
                  return (
                    <li key={i}>
                      <div className="flex items-baseline justify-between text-[13px]">
                        <span className="font-medium text-ink">
                          Tier {String(r.tier ?? r.band ?? i + 1)}
                        </span>
                        <span className="font-semibold tabular-nums text-ink">
                          {pct.toFixed(1)}%
                        </span>
                      </div>
                      <div className="mt-1 h-1.5 overflow-hidden rounded-full bg-surface-sunken">
                        <div
                          className="h-full bg-info"
                          style={{ width: `${Math.min(100, pct)}%` }}
                        />
                      </div>
                    </li>
                  );
                })}
              </ul>
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

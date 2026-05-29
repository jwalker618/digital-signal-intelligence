"use client";

import Link from "next/link";
import { Suspense } from "react";
import { useSearchParams } from "next/navigation";
import { ArrowRight, FileDown } from "lucide-react";
import { Topbar } from "@/components/chrome/topbar";
import { Card } from "@/components/ui/card";
import { Chip } from "@/components/ui/chip";
import { Button } from "@/components/ui/button";
import { Eyebrow, NumDisplay, Body, Micro, Caption } from "@/components/ui/typography";
import { Waterfall } from "@/components/charts/waterfall";
import { PageError, PageLoading, RoleGate } from "@/components/base/pageStates";
import { useRoleScopedFetch } from "@/lib/useRoleScopedFetch";
import { fetchOverview, fetchSubmissionScore } from "@/lib/portalApi";
import { useAuthStore } from "@/store/authStore";
import { formatCurrency } from "@/lib/format";
import { cn } from "@/lib/utils";
import { LossOutlookCard } from "@/app/(app)/client/_components/LossOutlookCard";
import { ExposureCard } from "@/app/(app)/client/_components/ExposureCard";
import type {
  ClientCoverageEntry,
  ImpactBreakdown,
  OverviewResponse,
  ScoreResponse,
} from "@/types/portal";

export default function ClientDriversPage() {
  return (
    <Suspense fallback={<PageLoading />}>
      <DriversInner />
    </Suspense>
  );
}

function DriversInner() {
  const accessToken = useAuthStore((s) => s.accessToken);
  const user = useAuthStore((s) => s.user);
  const enabled = !!accessToken && user?.role === "CLIENT";
  const params = useSearchParams();
  const explicitCode = params.get("code");

  const overview = useRoleScopedFetch<OverviewResponse>({
    fetcher: () => fetchOverview(accessToken),
    enabled,
    deps: [accessToken],
  });

  const code =
    explicitCode ??
    (overview.data?.role === "CLIENT"
      ? overview.data.active_coverages[0]?.submission_code
      : undefined);

  const score = useRoleScopedFetch<ScoreResponse>({
    fetcher: () => fetchSubmissionScore(accessToken, code!),
    enabled: enabled && !!code,
    deps: [accessToken, code],
  });

  if (!user) return <PageLoading message="Signing in…" />;
  if (user.role && user.role !== "CLIENT") return <RoleGate expected="client" />;
  if (overview.loading) return <PageLoading />;
  if (overview.error) return <PageError message={overview.error} />;
  if (!overview.data || overview.data.role !== "CLIENT")
    return <RoleGate expected="client" />;
  if (!code) return <NoCoverage entityName={overview.data.entity_name} />;
  if (score.loading) return <PageLoading />;
  if (score.error) return <PageError message={score.error} />;
  if (!score.data) return <PageLoading />;

  return (
    <DriversBody
      entityName={overview.data.entity_name}
      score={score.data}
      hero={overview.data.active_coverages.find(
        (c) => c.submission_code === code,
      )}
      allCoverages={overview.data.active_coverages.map((c) => ({
        code: c.submission_code,
        coverage: c.coverage,
      }))}
      activeCode={code}
    />
  );
}

function NoCoverage({ entityName }: { entityName: string }) {
  return (
    <>
      <Topbar
        crumbs={["Client Portal", "Risk Insights"]}
        entity={entityName}
      />
      <div className="flex flex-1 items-start justify-center px-9 py-12">
        <Card pad="lg" className="max-w-md">
          <Eyebrow>No coverage selected</Eyebrow>
          <Body className="mt-2">
            Risk Insights scopes to a single coverage. Open one from{" "}
            <Link
              href="/client/coverages"
              className="font-semibold text-info hover:underline"
            >
              Coverages
            </Link>{" "}
            to view its premium build-up.
          </Body>
        </Card>
      </div>
    </>
  );
}

function sumDeltas(items: ImpactBreakdown["strengths"]): number {
  return items.reduce((sum, s) => sum + s.premium_delta_usd, 0);
}

function DriversBody({
  entityName,
  score,
  hero,
  allCoverages,
  activeCode,
}: {
  entityName: string;
  score: ScoreResponse;
  hero?: ClientCoverageEntry;
  allCoverages: { code: string; coverage: string }[];
  activeCode: string;
}) {
  const ib = score.impact_breakdown;
  const basePremium = ib?.base_premium ?? score.base_premium ?? 0;
  const finalPremium = ib?.final_premium ?? score.final_premium ?? 0;
  const strengthsDelta = ib ? sumDeltas(ib.strengths) : 0;
  const dragsDelta = ib ? sumDeltas(ib.drags) : 0;

  return (
    <>
      <Topbar
        crumbs={["Client Portal", "Risk Insights", score.coverage]}
        entity={entityName}
      />
      <div className="flex-1 overflow-y-auto px-9 py-7">
        <div className="mx-auto grid max-w-[1400px] gap-4">
          {/* ────────── ROW 1 — title strip ────────── */}
          <div className="flex flex-wrap items-end justify-between gap-4">
            <div>
              <Eyebrow>Risk insights</Eyebrow>
              <h1 className="mt-1.5 font-display text-[32px] font-semibold leading-none tracking-tight text-ink">
                Your premium, broken down to the signal
              </h1>
            </div>
            <CoveragePicker
              all={allCoverages}
              activeCode={activeCode}
              baseHref="/client/drivers"
            />
          </div>

          {/* ────────── ROW 2 — 4 headline math cards ────────── */}
          <div className="grid gap-3 md:grid-cols-4">
            <HeadlineCard
              variant="default"
              label="Base premium"
              valueText={basePremium > 0 ? formatCurrency(basePremium) : "—"}
              caption="Industry × revenue × limit"
            />
            <HeadlineCard
              variant="pos"
              label="Strengths"
              valueText={
                ib ? formatSigned(strengthsDelta) : "—"
              }
              caption={
                ib
                  ? `${ib.strengths.length} signal${ib.strengths.length === 1 ? "" : "s"} lowering your premium`
                  : "Pending"
              }
            />
            <HeadlineCard
              variant="spot"
              label="Opportunity"
              valueText={ib ? formatSigned(dragsDelta) : "—"}
              caption={
                ib
                  ? `${ib.drags.length} signal${ib.drags.length === 1 ? "" : "s"} to act on`
                  : "Pending"
              }
            />
            <HeadlineCard
              variant="info"
              label="Final premium"
              valueText={finalPremium > 0 ? formatCurrency(finalPremium) : "—"}
              caption="As quoted by your carrier"
            />
          </div>

          {/* ────────── ROW 3 — waterfall card ────────── */}
          {ib && (
            <Card pad="lg">
              <div className="mb-3 flex items-baseline justify-between gap-3">
                <div>
                  <Eyebrow>Premium build-up</Eyebrow>
                  <h3 className="mt-1.5 font-display text-[18px] font-semibold leading-tight text-ink">
                    From base to bound — every signal accounted for
                  </h3>
                </div>
                <div className="flex flex-wrap items-center gap-3.5">
                  <LegendDot color="bg-pos" label="Strengths" />
                  <LegendDot color="bg-spot" label="Opportunity" />
                  <LegendDot color="bg-ink" label="Premium" />
                </div>
              </div>
              <Waterfall
                items={[
                  {
                    id: "base",
                    label: "Base",
                    value: ib.base_premium,
                    type: "base",
                  },
                  ...ib.strengths.slice(0, 4).map((s) => ({
                    id: s.signal_key,
                    label: s.signal_label,
                    value: s.premium_delta_usd,
                    type: "pos" as const,
                  })),
                  ...ib.drags.slice(0, 4).map((d) => ({
                    id: d.signal_key,
                    label: d.signal_label,
                    value: d.premium_delta_usd,
                    type: "opp" as const,
                  })),
                  {
                    id: "final",
                    label: "Final",
                    value: ib.final_premium,
                    type: "final",
                  },
                ]}
                height={240}
              />
            </Card>
          )}

          {/* ────────── ROW 4 — loss / exposure / next move ────────── */}
          {/* Reuse the rich overview cards (12-quarter claims strip +
              cohort compare bars, market-scale YOU pin) — the hero
              coverage from /overview carries the data ScoreResponse lacks. */}
          <div className="grid gap-4 md:grid-cols-3">
            <LossOutlookCard hero={hero} />
            <ExposureCard hero={hero} />

            <Card variant="spot" pad="lg" className="flex flex-col gap-3">
              <div className="flex items-baseline justify-between">
                <div>
                  <Eyebrow className="text-spot">Your next move</Eyebrow>
                  <p className="mt-1 text-[20px] font-semibold leading-none text-spot-deep dark:text-spot">
                    {ib && dragsDelta > 0
                      ? `${formatSigned(-dragsDelta)} available`
                      : "—"}
                  </p>
                </div>
                {ib && (
                  <Chip variant="spot" size="sm">
                    {ib.drags.length} action{ib.drags.length === 1 ? "" : "s"}
                  </Chip>
                )}
              </div>
              <Caption>
                The opportunity signals above are each linked to a concrete
                remediation, prioritised by leverage (impact ÷ effort).
              </Caption>
              <div className="mt-auto flex gap-2">
                <Link href={`/client/actions?code=${activeCode}`}>
                  <Button variant="spot" size="sm">
                    See action plan <ArrowRight size={13} />
                  </Button>
                </Link>
                <Button variant="ghost" size="sm" disabled>
                  <FileDown size={13} /> Export PDF
                </Button>
              </div>
            </Card>
          </div>
        </div>
      </div>
    </>
  );
}

function formatSigned(value: number): string {
  const sign = value > 0 ? "+" : value < 0 ? "−" : "";
  const abs = Math.abs(value);
  return `${sign}${formatCurrency(abs)}`;
}

function HeadlineCard({
  variant,
  label,
  valueText,
  caption,
}: {
  variant: "default" | "pos" | "spot" | "info";
  label: string;
  valueText: string;
  caption: string;
}) {
  const eyebrowTone =
    variant === "pos"
      ? "text-pos"
      : variant === "spot"
        ? "text-spot"
        : variant === "info"
          ? "text-info-deep dark:text-info"
          : "";
  const valueTone =
    variant === "pos"
      ? "text-pos"
      : variant === "spot"
        ? "text-spot-deep dark:text-spot"
        : variant === "info"
          ? "text-info-deep dark:text-info"
          : "";
  return (
    <Card pad="md" variant={variant}>
      <Eyebrow className={eyebrowTone}>{label}</Eyebrow>
      <NumDisplay size="md" className={cn("mt-1.5 block", valueTone)}>
        {valueText}
      </NumDisplay>
      <Caption className="mt-1 block">{caption}</Caption>
    </Card>
  );
}

function LegendDot({ color, label }: { color: string; label: string }) {
  return (
    <span className="flex items-center gap-1.5 text-[11px] text-ink-mute">
      <span className={cn("h-2.5 w-2.5 rounded-sm", color)} />
      {label}
    </span>
  );
}

function CoveragePicker({
  all,
  activeCode,
  baseHref,
}: {
  all: { code: string; coverage: string }[];
  activeCode: string;
  baseHref: string;
}) {
  if (all.length <= 1) return null;
  return (
    <label className="flex items-center gap-2 text-[12.5px]">
      <span className="text-ink-mute">Coverage:</span>
      <select
        value={activeCode}
        onChange={(e) => {
          window.location.href = `${baseHref}?code=${e.target.value}`;
        }}
        className="rounded-btn border border-rule-strong bg-surface px-3 py-1.5 text-[13px] font-medium text-ink focus:border-info focus:outline-none focus:ring-2 focus:ring-info/30"
      >
        {all.map((c) => (
          <option key={c.code} value={c.code}>
            {c.coverage}
          </option>
        ))}
      </select>
    </label>
  );
}

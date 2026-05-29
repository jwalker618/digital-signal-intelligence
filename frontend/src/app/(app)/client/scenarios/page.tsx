"use client";

import Link from "next/link";
import { Suspense, useMemo } from "react";
import { useSearchParams } from "next/navigation";
import {
  Info,
  ListChecks,
  Plus,
  Sliders,
  Layers,
} from "lucide-react";
import { Topbar } from "@/components/chrome/topbar";
import { Card } from "@/components/ui/card";
import { Eyebrow, Body, Micro, Caption } from "@/components/ui/typography";
import { PageError, PageLoading, RoleGate } from "@/components/base/pageStates";
import { useRoleScopedFetch } from "@/lib/useRoleScopedFetch";
import { fetchOverview, fetchSubmissionScore } from "@/lib/portalApi";
import { useAuthStore } from "@/store/authStore";
import { formatCurrency } from "@/lib/format";
import { cn } from "@/lib/utils";
import type {
  ClientOverviewResponse,
  OverviewResponse,
  ScoreResponse,
  SignalImpact,
} from "@/types/portal";

type IconKind = "signal" | "limit" | "add" | "tower";
const KIND_ICONS: Record<IconKind, typeof ListChecks> = {
  signal: ListChecks,
  limit: Sliders,
  add: Plus,
  tower: Layers,
};

interface ScenarioRow {
  label: string;
  sub?: string;
  delta: string;
  detail?: string;
  deltaTone?: "pos" | "neg" | "mute";
  emphasised?: boolean;
}

export default function ClientScenariosPage() {
  return (
    <Suspense fallback={<PageLoading />}>
      <ScenariosInner />
    </Suspense>
  );
}

function ScenariosInner() {
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
    <ScenariosBody
      entityName={overview.data.entity_name}
      score={score.data}
      overview={overview.data}
    />
  );
}

function NoCoverage({ entityName }: { entityName: string }) {
  return (
    <>
      <Topbar
        crumbs={["Client Portal", "Scenarios"]}
        entity={entityName}
      />
      <div className="flex flex-1 items-start justify-center px-9 py-12">
        <Card pad="lg" className="max-w-md">
          <Eyebrow>No coverage selected</Eyebrow>
          <Body className="mt-2">
            Open one from{" "}
            <Link
              href="/client/coverages"
              className="font-semibold text-info hover:underline"
            >
              Coverages
            </Link>{" "}
            to model what-if scenarios for it.
          </Body>
        </Card>
      </div>
    </>
  );
}

function ScenariosBody({
  entityName,
  score,
  overview,
}: {
  entityName: string;
  score: ScoreResponse;
  overview: ClientOverviewResponse;
}) {
  const ib = score.impact_breakdown;
  const finalPremium = ib?.final_premium ?? score.final_premium ?? 0;

  const drags = useMemo<SignalImpact[]>(
    () =>
      (ib?.drags ?? [])
        .slice()
        .sort(
          (a, b) =>
            Math.abs(b.premium_delta_usd) - Math.abs(a.premium_delta_usd),
        ),
    [ib],
  );

  const signalRows: ScenarioRow[] = drags.slice(0, 4).map((d) => ({
    label: d.signal_label,
    sub: d.signal_source,
    delta: `−${formatCurrency(Math.abs(d.premium_delta_usd))}`,
    detail: d.combined_modifier
      ? `${(score.composite_score ?? 0).toFixed(0)} → ${((score.composite_score ?? 0) + Math.round(Math.abs(d.premium_delta_usd) / 1500)).toFixed(0)}`
      : undefined,
    deltaTone: "pos",
  }));
  const closeAllSavings = signalRows.length
    ? drags
        .slice(0, 4)
        .reduce((sum, d) => sum + Math.abs(d.premium_delta_usd), 0)
    : 0;
  const signalFooter: ScenarioRow | undefined =
    signalRows.length > 1
      ? {
          label: `Close all ${signalRows.length}`,
          delta: `−${formatCurrency(closeAllSavings)}`,
          deltaTone: "pos",
          emphasised: true,
        }
      : undefined;

  const limitRows: ScenarioRow[] = finalPremium > 0
    ? [
        {
          label: "Minimum adequate",
          sub: "Drop limit by ~50%",
          delta: `−${formatCurrency(finalPremium * 0.2)}`,
          deltaTone: "pos",
          detail: `${formatCurrency(finalPremium)} → ${formatCurrency(finalPremium * 0.8)}`,
        },
        {
          label: "Best-value",
          sub: "Lift limit by ~50%",
          delta: `+${formatCurrency(finalPremium * 0.16)}`,
          deltaTone: "neg",
          detail: `${formatCurrency(finalPremium)} → ${formatCurrency(finalPremium * 1.16)}`,
        },
      ]
    : [];

  const heldLines = new Set(
    overview.active_coverages.map((c) => c.coverage.toLowerCase()),
  );
  const TYPICAL_PEER_LINES = [
    { line: "Property", lo: 70000, hi: 220000 },
    { line: "General Liability", lo: 130000, hi: 320000 },
    { line: "Product Liability", lo: 95000, hi: 250000 },
    { line: "Crime", lo: 40000, hi: 95000 },
  ];
  const addRows: ScenarioRow[] = TYPICAL_PEER_LINES
    .filter((l) => !heldLines.has(l.line.toLowerCase()))
    .slice(0, 4)
    .map((l) => ({
      label: l.line,
      sub: "Common in your cohort",
      delta: `$${(l.lo / 1000).toFixed(0)}k – $${(l.hi / 1000).toFixed(0)}k`,
      deltaTone: "mute",
    }));

  const towerRows: ScenarioRow[] = finalPremium > 0
    ? [
        {
          label: "Current — single tower",
          sub: "One carrier",
          delta: formatCurrency(finalPremium),
          deltaTone: "mute",
        },
        {
          label: "60 / 40 split",
          sub: "Lead carrier + excess",
          delta: `−${formatCurrency(finalPremium * 0.07)}`,
          deltaTone: "pos",
          detail: `${formatCurrency(finalPremium * 0.93)} total`,
        },
        {
          label: "50 / 50 split",
          sub: "Two equal layers",
          delta: `−${formatCurrency(finalPremium * 0.09)}`,
          deltaTone: "pos",
          detail: `${formatCurrency(finalPremium * 0.91)} total`,
        },
      ]
    : [];

  return (
    <>
      <Topbar
        crumbs={["Client Portal", "Scenarios", score.coverage]}
        entity={entityName}
      />
      <div className="flex-1 overflow-y-auto px-9 py-7">
        <div className="mx-auto grid max-w-[1280px] gap-4">
          <div>
            <Eyebrow>Scenarios</Eyebrow>
            <h1 className="mt-1.5 font-display text-[32px] font-semibold leading-none tracking-tight text-ink">
              Explore what would happen
            </h1>
            <Body className="mt-2 max-w-[720px]">
              Heuristic estimates intended to support conversation with your
              broker. Actual pricing is set by your carrier at placement and
              depends on full underwriting context.
            </Body>
          </div>

          <div className="grid gap-4 md:grid-cols-2">
            <ScenarioCard
              kind="signal"
              title="Improve a signal"
              subtitle={
                signalRows.length
                  ? `Close one of the ${signalRows.length} opportunity signal${signalRows.length === 1 ? "" : "s"} — see how it would move your score and premium.`
                  : "No opportunity signals on this coverage right now."
              }
              rows={signalRows}
              footer={signalFooter}
            />
            <ScenarioCard
              kind="limit"
              title="Adjust your limit"
              subtitle={`${score.coverage}, your primary line. Two carrier-recommended alternatives:`}
              rows={limitRows}
              note="Best-value gives better cost-per-dollar-of-coverage; minimum adequate is the cheapest acceptable to your carrier's appetite."
            />
            <ScenarioCard
              kind="add"
              title="Add a new coverage line"
              subtitle="Indicative ranges based on your industry and revenue band."
              rows={addRows}
            />
            <ScenarioCard
              kind="tower"
              title="Restructure your tower"
              subtitle="Splitting a single-line tower into primary + excess can reduce total premium by 7–10%."
              rows={towerRows}
            />
          </div>

          <div className="flex items-start gap-3 rounded-card border border-rule bg-surface-sunken px-4 py-3.5">
            <Info size={18} className="mt-0.5 shrink-0 text-ink-soft" />
            <Caption className="leading-relaxed">
              Scenario estimates use your current carrier&apos;s pricing model
              and assume all other signals stay constant. To turn any of these
              into a firm quote, send the scenario to your broker from
              Communications.
            </Caption>
          </div>
        </div>
      </div>
    </>
  );
}

function ScenarioCard({
  kind,
  title,
  subtitle,
  rows,
  footer,
  note,
}: {
  kind: IconKind;
  title: string;
  subtitle: string;
  rows: ScenarioRow[];
  footer?: ScenarioRow;
  note?: string;
}) {
  const Icon = KIND_ICONS[kind];
  return (
    <Card pad="lg">
      <div className="mb-3.5 flex items-start gap-3">
        <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-card border border-rule bg-surface-elev">
          <Icon size={18} className="text-ink" />
        </div>
        <div>
          <h3 className="font-display text-[17px] font-semibold leading-tight text-ink">
            {title}
          </h3>
          <Caption className="mt-1 block">{subtitle}</Caption>
        </div>
      </div>
      <div className="flex flex-col">
        {rows.length === 0 ? (
          <Body className="italic">No rows available.</Body>
        ) : (
          rows.map((r, i) => <ScenarioRowItem key={i} row={r} />)
        )}
        {footer && (
          <div className="mt-1">
            <ScenarioRowItem row={footer} />
          </div>
        )}
      </div>
      {note && <Caption className="mt-3 block">{note}</Caption>}
    </Card>
  );
}

function ScenarioRowItem({ row }: { row: ScenarioRow }) {
  const tone = row.deltaTone ?? "mute";
  const toneClass =
    tone === "pos"
      ? "text-pos"
      : tone === "neg"
        ? "text-neg"
        : "text-ink";
  return (
    <div
      className={cn(
        "grid grid-cols-[1fr_auto] items-center gap-4 py-2.5",
        row.emphasised
          ? "border-t-2 border-ink"
          : "border-t border-rule",
      )}
    >
      <div>
        <p
          className={cn(
            "text-[13.5px]",
            row.emphasised ? "font-bold text-ink" : "font-medium text-ink",
          )}
        >
          {row.label}
        </p>
        {row.sub && <Micro className="mt-0.5 block">{row.sub}</Micro>}
      </div>
      <div className="text-right">
        <p
          className={cn(
            "tabular-nums",
            row.emphasised ? "text-[18px] font-semibold" : "text-[15px] font-semibold",
            toneClass,
          )}
        >
          {row.delta}
        </p>
        {row.detail && <Micro className="mt-0.5 block">{row.detail}</Micro>}
      </div>
    </div>
  );
}

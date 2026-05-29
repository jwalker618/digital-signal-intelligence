"use client";

import { ShieldAlert } from "lucide-react";
import { Topbar } from "@/components/chrome/topbar";
import {
  Body,
  Card,
  Caption,
  Chip,
  Eyebrow,
  KpiSnug,
  Micro,
} from "@/components/ui";
import { PageError, PageLoading, RoleGate } from "@/components/base/pageStates";
import { useRoleScopedFetch } from "@/lib/useRoleScopedFetch";
import { fetchAggregation } from "@/lib/portalApi";
import { useAuthStore } from "@/store/authStore";
import { formatCurrency } from "@/lib/format";
import { cn } from "@/lib/utils";
import type {
  AggregationResponse,
  CatPerilExposure,
  ConcentrationEntry,
} from "@/types/portal";

export default function BrokerAggregationPage() {
  const accessToken = useAuthStore((s) => s.accessToken);
  const user = useAuthStore((s) => s.user);
  const enabled = !!accessToken && user?.role === "BROKER";

  const { data, error, loading } = useRoleScopedFetch<AggregationResponse>({
    fetcher: () => fetchAggregation(accessToken),
    enabled,
    deps: [accessToken],
  });

  if (!user) return <PageLoading message="Signing in…" />;
  if (user.role && user.role !== "BROKER") return <RoleGate expected="broker" />;
  if (loading) return <PageLoading />;
  if (error) return <PageError message={error} />;
  if (!data) return <PageLoading />;

  return <AggBody data={data} />;
}

function AggBody({ data }: { data: AggregationResponse }) {
  const industries = [...data.industry_concentration].sort(
    (a, b) => b.share_pct - a.share_pct,
  );
  const lines = [...data.line_concentration].sort(
    (a, b) => b.share_pct - a.share_pct,
  );
  const divScore = Math.round(data.diversification_score);

  return (
    <>
      <Topbar
        crumbs={["Broker Portal", "Risk Aggregation"]}
        entity={data.broker_name}
      />
      <div className="flex-1 overflow-y-auto px-9 py-7">
        <div className="mx-auto grid max-w-[1400px] gap-4">
          {/* Title + KPIs */}
          <header className="flex flex-wrap items-end justify-between gap-6">
            <div>
              <Eyebrow>Risk aggregation</Eyebrow>
              <h1 className="mt-1.5 font-display text-[32px] font-semibold leading-tight tracking-tight text-ink">
                Where your book concentrates
              </h1>
              <Body className="mt-1.5">
                Industry and line concentration, plus how a peril event would propagate through
                your book.
              </Body>
            </div>
            <div className="flex flex-wrap gap-7">
              <KpiSnug
                label="Total premium"
                value={formatCurrency(data.total_premium_usd)}
              />
              <KpiSnug label="Industries" value={industries.length} />
              <KpiSnug label="Lines" value={lines.length} />
              <KpiSnug
                label="Diversification"
                value={`${divScore}/100`}
                tone="info"
              />
            </div>
          </header>

          {/* Diversification + narrative */}
          <Card variant="info" pad="lg">
            <div className="grid items-center gap-5 md:grid-cols-[160px_1fr]">
              <DiversificationGauge value={divScore} />
              <div>
                <Eyebrow className="text-info-deep dark:text-info">
                  Diversification score
                </Eyebrow>
                <h2 className="mt-1.5 text-[18px] font-semibold leading-snug text-ink">
                  {divScore >= 75
                    ? "Strongly diversified"
                    : divScore >= 50
                      ? "Reasonably diversified, with one concentration risk"
                      : divScore >= 25
                        ? "Concentrated — diversification work to do"
                        : "Heavily concentrated"}
                </h2>
                <Body className="mt-1.5 text-[13.5px]">
                  {data.diversification_note}
                </Body>
              </div>
            </div>
          </Card>

          {/* Concentration bars */}
          <div className="grid gap-4 lg:grid-cols-2">
            <ConcentrationCard
              title="Industry concentration"
              entries={industries}
            />
            <ConcentrationCard
              title="Coverage-line concentration"
              entries={lines}
            />
          </div>

          {/* CAT peril exposure */}
          {data.cat_peril_exposure.length > 0 && (
            <Card pad="lg">
              <div className="mb-4 flex items-baseline justify-between">
                <div>
                  <Eyebrow>CAT peril exposure</Eyebrow>
                  <h2 className="mt-1.5 text-[17px] font-semibold leading-tight text-ink">
                    How an event in each peril would propagate
                  </h2>
                </div>
                <Caption>Severity = % of book at meaningful exposure</Caption>
              </div>
              <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
                {data.cat_peril_exposure.map((p) => (
                  <PerilCard key={p.peril_slug} peril={p} />
                ))}
              </div>
            </Card>
          )}
        </div>
      </div>
    </>
  );
}

function DiversificationGauge({ value }: { value: number }) {
  const clamped = Math.max(0, Math.min(100, value));
  const endX = 10 + (clamped / 100) * 140;
  const endY = 75 - Math.sin((Math.PI * clamped) / 100) * 70;
  return (
    <svg viewBox="0 0 160 90" className="h-[90px] w-[160px]">
      <path
        d="M10,75 A 70,70 0 0,1 150,75"
        fill="none"
        className="stroke-surface-sunken"
        strokeWidth={12}
        strokeLinecap="round"
      />
      <path
        d={`M10,75 A 70,70 0 0,1 ${endX},${endY}`}
        fill="none"
        className="stroke-info"
        strokeWidth={12}
        strokeLinecap="round"
      />
      <text
        x={80}
        y={62}
        textAnchor="middle"
        className="fill-info-deep dark:fill-info"
        style={{ font: "700 28px var(--font-display, IBM Plex Sans)" }}
      >
        {Math.round(clamped)}
      </text>
      <text
        x={80}
        y={80}
        textAnchor="middle"
        className="fill-ink-soft"
        style={{ font: "10px var(--font-display, IBM Plex Sans)" }}
      >
        of 100
      </text>
    </svg>
  );
}

function ConcentrationCard({
  title,
  entries,
}: {
  title: string;
  entries: ConcentrationEntry[];
}) {
  const max = Math.max(...entries.map((e) => e.share_pct), 1);
  return (
    <Card pad="lg">
      <h3 className="mb-4 text-[16px] font-semibold text-ink">{title}</h3>
      <ul className="flex flex-col gap-2.5">
        {entries.slice(0, 8).map((e) => {
          const warn = e.share_pct > 30;
          return (
            <li key={`${e.dimension}-${e.value}`}>
              <div className="mb-1 flex items-baseline justify-between text-[13px]">
                <span className="truncate font-semibold text-ink">{e.value}</span>
                <span
                  className={cn(
                    "font-semibold tabular-nums",
                    warn ? "text-warn" : "text-ink",
                  )}
                >
                  {e.share_pct.toFixed(0)}%{" "}
                  <Micro className="font-normal">({e.count})</Micro>
                </span>
              </div>
              <div className="h-1.5 overflow-hidden rounded-full bg-surface-sunken">
                <div
                  className={cn("h-full", warn ? "bg-warn" : "bg-info")}
                  style={{ width: `${(e.share_pct / max) * 100}%` }}
                />
              </div>
            </li>
          );
        })}
      </ul>
    </Card>
  );
}

function PerilCard({ peril }: { peril: CatPerilExposure }) {
  const sev = peril.relative_severity * 100;
  const tone: "neg" | "warn" | "pos" =
    sev >= 60 ? "neg" : sev >= 40 ? "warn" : "pos";
  const toneText =
    tone === "neg" ? "text-neg" : tone === "warn" ? "text-warn" : "text-pos";
  const toneBg =
    tone === "neg" ? "bg-neg" : tone === "warn" ? "bg-warn" : "bg-pos";
  return (
    <div className="rounded-card border border-rule bg-surface-elev p-4">
      <div className="mb-2.5 flex items-center gap-2">
        <ShieldAlert size={15} className={toneText} />
        <span className="text-[13.5px] font-bold text-ink">{peril.peril_name}</span>
      </div>
      <Micro className="mb-0.5 block">Book-relative severity</Micro>
      <div className={cn("text-[26px] font-semibold tabular-nums leading-none", toneText)}>
        {Math.round(sev)}%
      </div>
      <div className="mt-1.5 h-1.5 overflow-hidden rounded-full bg-surface-sunken">
        <div className={cn("h-full", toneBg)} style={{ width: `${Math.min(100, sev)}%` }} />
      </div>
      <Micro className="mt-2 block">
        {peril.exposed_policy_count} polic
        {peril.exposed_policy_count === 1 ? "y" : "ies"} exposed ·{" "}
        {formatCurrency(peril.exposed_premium_usd)}
      </Micro>
      {peril.most_exposed_verticals.length > 0 && (
        <Caption className="mt-1 block text-[11px]">
          Top verticals:{" "}
          <strong className="text-ink">
            {peril.most_exposed_verticals.slice(0, 3).join(", ")}
          </strong>
        </Caption>
      )}
    </div>
  );
}


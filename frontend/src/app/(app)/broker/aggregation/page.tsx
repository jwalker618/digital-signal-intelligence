"use client";

import { Network, ShieldAlert, Sparkles } from "lucide-react";
import { Topbar } from "@/components/chrome/topbar";
import { Card } from "@/components/ui/card";
import { Chip } from "@/components/ui/chip";
import { Eyebrow, NumDisplay, Body, Micro } from "@/components/ui/typography";
import { PageError, PageLoading, RoleGate } from "@/components/base/pageStates";
import { useRoleScopedFetch } from "@/lib/useRoleScopedFetch";
import { fetchAggregation } from "@/lib/portalApi";
import { useAuthStore } from "@/store/authStore";
import { formatCurrency, formatPercent } from "@/lib/format";
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
  const divTone =
    data.diversification_score >= 75
      ? "pos"
      : data.diversification_score >= 50
        ? "info"
        : data.diversification_score >= 25
          ? "warn"
          : "neg";

  return (
    <>
      <Topbar
        crumbs={["Broker Portal", "Risk Aggregation"]}
        entity={data.broker_name}
      />
      <div className="flex-1 overflow-y-auto px-9 py-7">
        <div className="mx-auto grid max-w-[1400px] gap-6">
          <header>
            <Eyebrow>Concentration</Eyebrow>
            <h1 className="mt-1 font-display text-[32px] font-semibold leading-none tracking-tight text-ink">
              Risk Aggregation
            </h1>
          </header>

          {/* Hero: diversification + total premium */}
          <div className="grid gap-4 md:grid-cols-3">
            <Card variant="info" pad="lg">
              <Eyebrow className="text-info-deep dark:text-info">
                Total premium
              </Eyebrow>
              <NumDisplay size="xl" className="mt-2">
                {formatCurrency(data.total_premium_usd)}
              </NumDisplay>
            </Card>
            <Card variant={divTone} pad="lg">
              <Eyebrow>Diversification</Eyebrow>
              <NumDisplay size="xl" className="mt-2">
                {data.diversification_score.toFixed(0)}
              </NumDisplay>
              <Micro className="mt-1 block">/ 100</Micro>
            </Card>
            <Card pad="lg" className="col-span-1 md:col-span-1">
              <Eyebrow>Note</Eyebrow>
              <Body className="mt-2 text-[13.5px]">
                {data.diversification_note}
              </Body>
            </Card>
          </div>

          {/* Cat peril */}
          {data.cat_peril_exposure.length > 0 && (
            <section>
              <Eyebrow className="mb-3">Cat peril exposure</Eyebrow>
              <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
                {data.cat_peril_exposure.map((p) => (
                  <CatPerilCard key={p.peril_slug} peril={p} />
                ))}
              </div>
            </section>
          )}

          {/* Concentration tables */}
          <div className="grid gap-5 lg:grid-cols-2">
            <ConcentrationCard
              title="Industry concentration"
              icon={<Sparkles size={15} className="text-ink-mute" />}
              items={data.industry_concentration}
            />
            <ConcentrationCard
              title="Line concentration"
              icon={<Network size={15} className="text-ink-mute" />}
              items={data.line_concentration}
            />
          </div>
        </div>
      </div>
    </>
  );
}

function CatPerilCard({ peril }: { peril: CatPerilExposure }) {
  const severityTone =
    peril.relative_severity >= 0.75
      ? "neg"
      : peril.relative_severity >= 0.5
        ? "warn"
        : peril.relative_severity >= 0.25
          ? "info"
          : "pos";
  return (
    <Card pad="md" variant={severityTone} className="space-y-3">
      <header className="flex items-start justify-between">
        <div>
          <Eyebrow>Peril</Eyebrow>
          <h3 className="mt-0.5 text-[16px] font-semibold text-ink">
            {peril.peril_name}
          </h3>
        </div>
        <Chip variant={severityTone} size="sm">
          <ShieldAlert size={11} />
          {formatPercent(peril.relative_severity, 0)}
        </Chip>
      </header>
      <div className="grid grid-cols-2 gap-3 border-t border-rule pt-3 text-[12.5px]">
        <div>
          <Micro>Policies exposed</Micro>
          <p className="font-semibold tabular-nums text-ink">
            {peril.exposed_policy_count}
          </p>
        </div>
        <div>
          <Micro>Premium exposed</Micro>
          <p className="font-semibold tabular-nums text-ink">
            {formatCurrency(peril.exposed_premium_usd)}
          </p>
        </div>
      </div>
      {peril.most_exposed_verticals.length > 0 && (
        <div className="space-y-1">
          <Micro>Most-exposed verticals</Micro>
          <div className="flex flex-wrap gap-1.5">
            {peril.most_exposed_verticals.slice(0, 3).map((v) => (
              <Chip key={v} variant="mute" size="sm">
                {v}
              </Chip>
            ))}
          </div>
        </div>
      )}
    </Card>
  );
}

function ConcentrationCard({
  title,
  icon,
  items,
}: {
  title: string;
  icon: React.ReactNode;
  items: ConcentrationEntry[];
}) {
  const top = [...items].sort((a, b) => b.share_pct - a.share_pct).slice(0, 8);
  return (
    <Card pad="md" className="space-y-3">
      <header className="flex items-center gap-2">
        {icon}
        <Eyebrow>{title}</Eyebrow>
      </header>
      <ul className="space-y-2">
        {top.map((c, i) => (
          <li key={`${c.dimension}-${c.value}-${i}`}>
            <div className="flex items-baseline justify-between text-[13px]">
              <span className="truncate font-medium text-ink">{c.value}</span>
              <span className="font-semibold tabular-nums text-ink">
                {formatPercent(c.share_pct / 100, 1)}
              </span>
            </div>
            <div className="mt-1 h-1.5 overflow-hidden rounded-full bg-surface-sunken">
              <div
                className="h-full bg-info"
                style={{ width: `${Math.min(100, c.share_pct)}%` }}
              />
            </div>
            <Micro className="mt-1 block">
              {c.count} policies
              {c.note && <span className="ml-2">· {c.note}</span>}
            </Micro>
          </li>
        ))}
      </ul>
    </Card>
  );
}

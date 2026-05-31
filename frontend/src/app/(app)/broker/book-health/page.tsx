"use client";

import { ChartPie, Info, Layers, TrendingUp } from "lucide-react";
import { Topbar } from "@/components/chrome/topbar";
import {
  Body,
  Card,
  Caption,
  Eyebrow,
  KpiSnug,
  Micro,
  NumDisplay,
} from "@/components/ui";
import { PageError, PageLoading, RoleGate } from "@/components/base/pageStates";
import { useRoleScopedFetch } from "@/lib/useRoleScopedFetch";
import { fetchBookHealth } from "@/lib/portalApi";
import { useAuthStore } from "@/store/authStore";
import { formatCurrency, formatPercent } from "@/lib/format";
import { cn } from "@/lib/utils";
import { compactCurrency } from "@/lib/coerce";
import type { BookHealthResponse } from "@/types/portal";

export default function BrokerBookHealthPage() {
  const accessToken = useAuthStore((s) => s.accessToken);
  const user = useAuthStore((s) => s.user);
  const enabled = !!accessToken && user?.role === "BROKER";

  const { data, error, loading } = useRoleScopedFetch<BookHealthResponse>({
    fetcher: () => fetchBookHealth(accessToken),
    enabled,
    deps: [accessToken],
  });

  if (!user) return <PageLoading message="Signing in…" />;
  if (user.role && user.role !== "BROKER") return <RoleGate expected="broker" />;
  if (loading) return <PageLoading />;
  if (error) return <PageError message={error} />;
  if (!data) return <PageLoading />;

  return <HealthBody data={data} />;
}

interface BreakdownRow {
  name: string;
  share: number;
  premium: number;
  count: number;
}

// Premium-weighted breakdown (template's cards are premium-$ share, with
// the policy count as a secondary annotation).
function toBreakdownRows(
  premium: Record<string, number>,
  counts: Record<string, number>,
): BreakdownRow[] {
  const total = Object.values(premium).reduce((sum, n) => sum + n, 0);
  return Object.entries(premium)
    .map(([name, prem]) => ({
      name,
      share: total ? prem / total : 0,
      premium: prem,
      count: counts[name] ?? 0,
    }))
    .sort((a, b) => b.share - a.share);
}

function HealthBody({ data }: { data: BookHealthResponse }) {
  const lines = toBreakdownRows(data.lines_premium, data.lines_concentration);
  const verticals = toBreakdownRows(
    data.vertical_premium,
    data.vertical_concentration,
  );
  const tenureYears = (data.avg_tenure_months / 12).toFixed(1);

  return (
    <>
      <Topbar
        crumbs={["Broker Portal", "Book Health"]}
        entity={data.broker_name}
      />
      <div className="flex-1 overflow-y-auto px-9 py-7">
        <div className="grid gap-4">
          {/* Title + KPIs */}
          <header className="flex flex-wrap items-end justify-between gap-6">
            <div>
              <h1 className="mt-1.5 font-display text-[32px] font-semibold leading-tight tracking-tight text-ink">
                Retention, depth, profitability
              </h1>
              <Body className="mt-1.5">
                The business view of your book — beyond risk into the relationship and economics.
              </Body>
            </div>
            <div className="flex flex-wrap gap-7">
              <KpiSnug label="Clients" value={data.client_count} />
              <KpiSnug label="Policies" value={data.policy_count} />
              <KpiSnug
                label="Total premium"
                value={formatCurrency(data.total_premium_usd)}
              />
              <KpiSnug
                label="Est. commission"
                value={formatCurrency(data.total_estimated_commission_usd)}
                tone="pos"
              />
              <KpiSnug
                label="Cmsn yield"
                value={`${data.commission_yield_pct.toFixed(1)}%`}
              />
            </div>
          </header>

          {/* Three feature cards */}
          <div className="grid gap-4 md:grid-cols-3">
            <FeatureCard
              icon={<TrendingUp size={18} />}
              iconTone="pos"
              eyebrow="Retention"
              primary={`${data.retention_rate_pct.toFixed(1)}%`}
              primaryLabel="Annual retention rate"
              primaryTone="pos"
              bar={{ value: data.retention_rate_pct, min: 70, max: 100, tone: "pos" }}
              rows={[
                [
                  "Average tenure",
                  `${data.avg_tenure_months} mo`,
                  `~${tenureYears} yrs`,
                ],
                [
                  "Cross-sell ratio",
                  `${data.cross_sell_ratio_pct.toFixed(0)}%`,
                  "Share holding 3+ lines",
                ],
              ]}
              footer="Indicative — production wires actual renewal history."
            />
            <FeatureCard
              icon={<Layers size={18} />}
              iconTone="info"
              eyebrow="Depth of relationship"
              primary={data.avg_lines_per_client.toFixed(2)}
              primaryLabel="Avg lines per client"
              primaryTone="info"
              rows={[
                [
                  "Cross-sell (≥3 lines)",
                  `${data.cross_sell_ratio_pct.toFixed(0)}%`,
                  "Share holding 3+ lines",
                ],
                [
                  "Avg premium / client",
                  formatCurrency(data.avg_premium_per_client),
                  "Book-weighted average",
                ],
              ]}
              footer="Anchor clients carry multi-line relationships across the book."
            />
            <FeatureCard
              icon={<ChartPie size={18} />}
              iconTone="warn"
              eyebrow="Profitability"
              primary={`${data.commission_yield_pct.toFixed(1)}%`}
              primaryLabel="Commission yield"
              primaryTone="default"
              rows={[
                [
                  "Est. annual commission",
                  formatCurrency(data.total_estimated_commission_usd),
                  "Book-weighted",
                ],
                [
                  "Avg premium / client",
                  formatCurrency(data.avg_premium_per_client),
                  "Per-client mean",
                ],
              ]}
              footer="Production wires actual broker remuneration including contingents and overrides."
            />
          </div>

          {/* Breakdowns */}
          <div className="grid gap-4 lg:grid-cols-2">
            <BreakdownCard title="Premium by vertical" rows={verticals} />
            <BreakdownCard title="Premium by coverage line" rows={lines} />
          </div>

          {/* Footer note */}
          <div className="flex items-start gap-3 rounded-card border border-rule bg-surface-sunken px-4 py-3">
            <Info size={15} className="mt-0.5 shrink-0 text-ink-soft" />
            <Caption className="leading-relaxed">
              Retention and tenure are illustrative for the demo; commission yield and per-line /
              per-vertical breakdowns are computed live from the placed book. See Risk Aggregation
              for peril-level concentration narratives.
            </Caption>
          </div>
        </div>
      </div>
    </>
  );
}

type Tone = "pos" | "info" | "warn" | "default";

function toneText(t: Tone): string {
  return t === "pos"
    ? "text-pos"
    : t === "info"
      ? "text-info"
      : t === "warn"
        ? "text-warn"
        : "text-ink";
}

function toneBg(t: Tone): string {
  return t === "pos"
    ? "bg-pos"
    : t === "info"
      ? "bg-info"
      : t === "warn"
        ? "bg-warn"
        : "bg-ink";
}

function toneSoftBg(t: Tone): string {
  return t === "pos"
    ? "bg-pos-soft"
    : t === "info"
      ? "bg-info-soft"
      : t === "warn"
        ? "bg-warn-soft"
        : "bg-surface-sunken";
}

interface FeatureCardProps {
  icon: React.ReactNode;
  iconTone: Tone;
  eyebrow: string;
  primary: string;
  primaryLabel: string;
  primaryTone: Tone;
  bar?: { value: number; min: number; max: number; tone: Tone };
  rows: Array<[string, string, string]>;
  footer: string;
}

function FeatureCard({
  icon,
  iconTone,
  eyebrow,
  primary,
  primaryLabel,
  primaryTone,
  bar,
  rows,
  footer,
}: FeatureCardProps) {
  return (
    <Card pad="lg" className="flex flex-col gap-3.5">
      <div className="flex items-center gap-3">
        <div
          className={cn(
            "flex h-9 w-9 items-center justify-center rounded-md",
            toneSoftBg(iconTone),
            toneText(iconTone),
          )}
        >
          {icon}
        </div>
        <Eyebrow>{eyebrow}</Eyebrow>
      </div>
      <div>
        <NumDisplay
          size="xl"
          className={cn("block leading-none", toneText(primaryTone))}
        >
          {primary}
        </NumDisplay>
        <Caption className="mt-1 block">{primaryLabel}</Caption>
      </div>
      {bar && (
        <div className="h-1 overflow-hidden rounded-full bg-rule">
          <div
            className={cn("h-full", toneBg(bar.tone))}
            style={{
              width: `${Math.max(0, Math.min(100, ((bar.value - bar.min) / (bar.max - bar.min)) * 100))}%`,
            }}
          />
        </div>
      )}
      <div className="flex flex-col gap-2 border-t border-rule pt-3">
        {rows.map(([label, value, sub], i) => (
          <div key={i} className="flex items-start justify-between gap-3">
            <div>
              <div className="text-[12.5px] font-medium text-ink">{label}</div>
              <Micro className="mt-0.5 block">{sub}</Micro>
            </div>
            <div className="text-[14px] font-bold tabular-nums text-ink">{value}</div>
          </div>
        ))}
      </div>
      <Caption className="text-[11.5px]">{footer}</Caption>
    </Card>
  );
}

function BreakdownCard({
  title,
  rows,
}: {
  title: string;
  rows: BreakdownRow[];
}) {
  const max = Math.max(...rows.map((r) => r.share), 0.0001);
  return (
    <Card pad="lg">
      <h3 className="mb-4 text-[16px] font-semibold text-ink">{title}</h3>
      <ul className="flex flex-col gap-2.5">
        {rows.slice(0, 8).map((r) => (
          <li key={r.name}>
            <div className="mb-1 flex items-baseline justify-between gap-2 text-[13px]">
              <span className="truncate font-semibold text-ink">{r.name}</span>
              <span className="shrink-0 font-semibold tabular-nums text-ink">
                {compactCurrency(r.premium)}{" "}
                <span className="font-normal text-ink-soft">
                  ({formatPercent(r.share, 0)} · {r.count})
                </span>
              </span>
            </div>
            <div className="h-1.5 overflow-hidden rounded-full bg-surface-sunken">
              <div
                className="h-full bg-info"
                style={{ width: `${(r.share / max) * 100}%` }}
              />
            </div>
          </li>
        ))}
      </ul>
    </Card>
  );
}


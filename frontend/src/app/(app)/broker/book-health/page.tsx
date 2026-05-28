"use client";

import { ChartPie } from "lucide-react";
import { Topbar } from "@/components/chrome/topbar";
import { Card } from "@/components/ui/card";
import { Eyebrow, NumDisplay, Body, Micro } from "@/components/ui/typography";
import { PageError, PageLoading, RoleGate } from "@/components/base/pageStates";
import { useRoleScopedFetch } from "@/lib/useRoleScopedFetch";
import { fetchBookHealth } from "@/lib/portalApi";
import { useAuthStore } from "@/store/authStore";
import { formatCurrency, formatPercent } from "@/lib/format";
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

function HealthBody({ data }: { data: BookHealthResponse }) {
  const lines = Object.entries(data.lines_concentration).sort(
    (a, b) => b[1] - a[1],
  );
  const verticals = Object.entries(data.vertical_concentration).sort(
    (a, b) => b[1] - a[1],
  );

  return (
    <>
      <Topbar
        crumbs={["Broker Portal", "Book Health"]}
        entity={data.broker_name}
      />
      <div className="flex-1 overflow-y-auto px-9 py-7">
        <div className="mx-auto grid max-w-[1400px] gap-6">
          <header>
            <Eyebrow>Operational</Eyebrow>
            <h1 className="mt-1 font-display text-[32px] font-semibold leading-none tracking-tight text-ink">
              Book Health
            </h1>
            <Body className="mt-2">
              Premium, commission yield, retention, cross-sell — the metrics
              that move the practice.
            </Body>
          </header>

          {/* Hero stats */}
          <div className="grid gap-4 md:grid-cols-3">
            <Stat
              variant="info"
              label="Premium under management"
              value={formatCurrency(data.total_premium_usd)}
              emphasis
            />
            <Stat
              variant="pos"
              label="Estimated commission"
              value={formatCurrency(data.total_estimated_commission_usd)}
              caption={`${formatPercent(data.commission_yield_pct / 100, 1)} yield`}
              emphasis
            />
            <Stat
              variant="default"
              label="Clients"
              value={`${data.client_count}`}
              caption={`${data.policy_count} policies · ${data.avg_lines_per_client.toFixed(1)} lines / client`}
              emphasis
            />
          </div>

          {/* Operational ratios */}
          <Card pad="lg" className="grid gap-6 md:grid-cols-4">
            <Ratio
              label="Retention"
              value={formatPercent(data.retention_rate_pct / 100, 0)}
              tone={data.retention_rate_pct >= 85 ? "pos" : data.retention_rate_pct >= 70 ? "info" : "warn"}
            />
            <Ratio
              label="Cross-sell ratio"
              value={formatPercent(data.cross_sell_ratio_pct / 100, 0)}
              tone={data.cross_sell_ratio_pct >= 50 ? "pos" : "info"}
            />
            <Ratio
              label="Avg tenure"
              value={`${data.avg_tenure_months}mo`}
              tone="info"
            />
            <Ratio
              label="Avg premium / client"
              value={formatCurrency(data.avg_premium_per_client)}
              tone="info"
            />
          </Card>

          {/* Concentration */}
          <div className="grid gap-5 lg:grid-cols-2">
            <Card pad="md" className="space-y-3">
              <header className="flex items-center gap-2">
                <ChartPie size={15} className="text-ink-mute" />
                <Eyebrow>Lines mix</Eyebrow>
              </header>
              <DistributionList items={lines} />
            </Card>
            <Card pad="md" className="space-y-3">
              <header className="flex items-center gap-2">
                <ChartPie size={15} className="text-ink-mute" />
                <Eyebrow>Vertical mix</Eyebrow>
              </header>
              <DistributionList items={verticals} />
            </Card>
          </div>
        </div>
      </div>
    </>
  );
}

function Stat({
  variant,
  label,
  value,
  caption,
  emphasis,
}: {
  variant: "info" | "pos" | "default";
  label: string;
  value: string;
  caption?: string;
  emphasis?: boolean;
}) {
  return (
    <Card pad="lg" variant={variant}>
      <Eyebrow
        className={
          variant === "info"
            ? "text-info-deep dark:text-info"
            : variant === "pos"
              ? "text-pos"
              : ""
        }
      >
        {label}
      </Eyebrow>
      <NumDisplay size={emphasis ? "xl" : "lg"} className="mt-2 block">
        {value}
      </NumDisplay>
      {caption && <Micro className="mt-1 block">{caption}</Micro>}
    </Card>
  );
}

function Ratio({
  label,
  value,
  tone,
}: {
  label: string;
  value: string;
  tone: "pos" | "info" | "warn" | "neg";
}) {
  return (
    <div>
      <Micro className="block">{label}</Micro>
      <p
        className={`mt-1 font-display text-[24px] font-semibold leading-none tabular-nums ${
          tone === "pos"
            ? "text-pos"
            : tone === "info"
              ? "text-info"
              : tone === "warn"
                ? "text-warn"
                : "text-neg"
        }`}
      >
        {value}
      </p>
    </div>
  );
}

function DistributionList({
  items,
}: {
  items: [string, number][];
}) {
  const top = items.slice(0, 8);
  return (
    <ul className="space-y-2">
      {top.map(([name, share]) => (
        <li key={name}>
          <div className="flex items-baseline justify-between text-[13px]">
            <span className="truncate font-medium text-ink">{name}</span>
            <span className="font-semibold tabular-nums text-ink">
              {formatPercent(share, 1)}
            </span>
          </div>
          <div className="mt-1 h-1.5 overflow-hidden rounded-full bg-surface-sunken">
            <div
              className="h-full bg-info"
              style={{ width: `${Math.min(100, share * 100)}%` }}
            />
          </div>
        </li>
      ))}
    </ul>
  );
}

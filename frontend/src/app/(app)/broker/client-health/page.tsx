"use client";

import { Calendar, CheckCircle2, ChevronRight, TrendingDown, TrendingUp } from "lucide-react";
import { Topbar } from "@/components/chrome/topbar";
import {
  Body,
  Button,
  Card,
  Caption,
  Chip,
  Eyebrow,
  Micro,
  MiniKpi,
  NumDisplay,
} from "@/components/ui";
import { PageError, PageLoading, RoleGate } from "@/components/base/pageStates";
import { useRoleScopedFetch } from "@/lib/useRoleScopedFetch";
import { fetchClientHealth } from "@/lib/portalApi";
import { useAuthStore } from "@/store/authStore";
import { formatCurrency } from "@/lib/format";
import { cn } from "@/lib/utils";
import type { ClientHealthEntry, ClientHealthResponse } from "@/types/portal";

export default function BrokerClientHealthPage() {
  const accessToken = useAuthStore((s) => s.accessToken);
  const user = useAuthStore((s) => s.user);
  const enabled = !!accessToken && user?.role === "BROKER";

  const { data, error, loading } = useRoleScopedFetch<ClientHealthResponse>({
    fetcher: () => fetchClientHealth(accessToken),
    enabled,
    deps: [accessToken],
  });

  if (!user) return <PageLoading message="Signing in…" />;
  if (user.role && user.role !== "BROKER") return <RoleGate expected="broker" />;
  if (loading) return <PageLoading />;
  if (error) return <PageError message={error} />;
  if (!data) return <PageLoading />;

  return <Inner data={data} />;
}

function engagementTone(score: number): "pos" | "info" | "warn" | "spot" {
  if (score >= 80) return "pos";
  if (score >= 60) return "info";
  if (score >= 40) return "warn";
  return "spot";
}

function engagementBorder(score: number): string {
  if (score >= 80) return "border-l-pos";
  if (score >= 60) return "border-l-info";
  if (score >= 40) return "border-l-warn";
  return "border-l-spot";
}

function engagementText(score: number): string {
  if (score >= 80) return "text-pos";
  if (score >= 60) return "text-info";
  if (score >= 40) return "text-warn";
  return "text-spot";
}

function Inner({ data }: { data: ClientHealthResponse }) {
  const sorted = [...data.clients].sort(
    (a, b) => b.engagement_score - a.engagement_score,
  );

  const strong = data.clients.filter((c) => c.engagement_score >= 80).length;
  const quiet = data.clients.filter((c) => c.engagement_score < 40).length;
  const opps = data.clients.reduce((s, c) => s + c.opportunity_flags.length, 0);
  const risks = data.clients.reduce((s, c) => s + c.risk_flags.length, 0);
  const renewalSoon = data.clients.filter(
    (c) => c.next_renewal_in_days != null && c.next_renewal_in_days <= 60,
  ).length;
  const quietClients = data.clients.filter((c) => c.engagement_score < 40);

  return (
    <>
      <Topbar
        crumbs={["Broker Portal", "Client Health"]}
        entity={data.broker_name}
      />
      <div className="flex-1 overflow-y-auto px-9 py-7">
        <div className="grid gap-4">
          {/* Hero */}
          <header>
            <h1 className="mt-1.5 font-display text-[32px] font-semibold leading-tight tracking-tight text-ink">
              Engagement, opportunities, risks across your book
            </h1>
            <Body className="mt-2 max-w-[640px]">
              Engagement is a leading indicator — a client scoring &quot;Quiet&quot; or
              &quot;Dormant&quot; today is at elevated non-renewal risk in the next 6 months
              unless re-engaged.
            </Body>
          </header>

          {/* KPI row */}
          <div className="grid gap-3 sm:grid-cols-3 lg:grid-cols-6">
            <KpiCard label="Clients" value={data.clients.length} />
            <KpiCard label="Strong" value={strong} tone="pos" />
            <KpiCard label="Quiet / dormant" value={quiet} tone="spot" />
            <KpiCard label="Open opps" value={opps} tone="info" />
            <KpiCard label="Risk flags" value={risks} tone="neg" />
            <KpiCard label="Renewal ≤60d" value={renewalSoon} tone="warn" />
          </div>

          {/* Quiet client alert strip */}
          {quietClients.length > 0 && (
            <Card variant="spot" pad="lg">
              <div className="mb-3 flex items-baseline justify-between gap-3">
                <div>
                  <Eyebrow className="text-spot-deep dark:text-spot">
                    Quiet client alerts
                  </Eyebrow>
                  <h2 className="mt-1.5 text-[17px] font-semibold leading-tight text-ink">
                    {quietClients.length} client
                    {quietClients.length === 1 ? "" : "s"} showing dormant signals — proactive
                    touchpoint recommended
                  </h2>
                </div>
                <Chip variant="spot" size="sm">
                  {quietClients.length} flagged
                </Chip>
              </div>
              <div className="flex flex-col gap-2">
                {quietClients.map((c) => (
                  <div
                    key={c.entity_name}
                    className="grid items-center gap-3 rounded-card border border-rule bg-surface px-3.5 py-2.5 sm:grid-cols-[1.6fr_1fr_1fr_auto]"
                  >
                    <div>
                      <div className="text-[13px] font-semibold text-ink">
                        {c.entity_name}
                      </div>
                      <Micro className="mt-0.5 block">{c.vertical_name ?? "—"}</Micro>
                    </div>
                    <div>
                      <Micro className="block">engagement</Micro>
                      <span className="text-[14px] font-semibold text-spot">
                        {c.engagement_score.toFixed(0)} · {c.engagement_label}
                      </span>
                    </div>
                    <div>
                      <Micro className="block">renewal in</Micro>
                      <span
                        className={cn(
                          "text-[14px] font-semibold",
                          c.next_renewal_in_days != null &&
                            c.next_renewal_in_days <= 60
                            ? "text-warn"
                            : "text-ink",
                        )}
                      >
                        {c.next_renewal_in_days != null
                          ? `${c.next_renewal_in_days}d`
                          : "—"}
                      </span>
                    </div>
                    <Button variant="spot" size="sm">
                      Reach out →
                    </Button>
                  </div>
                ))}
              </div>
            </Card>
          )}

          {/* Client roster */}
          <section className="flex flex-col gap-3">
            <div className="flex items-baseline justify-between">
              <h2 className="text-[17px] font-semibold text-ink">
                Client roster · {data.clients.length}
              </h2>
              <Caption>Sorted by engagement, highest first</Caption>
            </div>
            {sorted.map((c) => (
              <ClientHealthCard key={c.entity_name} client={c} />
            ))}
          </section>
        </div>
      </div>
    </>
  );
}

function KpiCard({
  label,
  value,
  tone = "default",
}: {
  label: string;
  value: number;
  tone?: "pos" | "spot" | "info" | "neg" | "warn" | "default";
}) {
  const cls =
    tone === "pos"
      ? "text-pos"
      : tone === "spot"
        ? "text-spot"
        : tone === "info"
          ? "text-info"
          : tone === "neg"
            ? "text-neg"
            : tone === "warn"
              ? "text-warn"
              : "text-ink";
  return (
    <Card pad="md">
      <MiniKpi
        label={label}
        value={
          <span className={cn("text-[26px] tabular-nums", cls)}>{value}</span>
        }
      />
    </Card>
  );
}

function ClientHealthCard({ client }: { client: ClientHealthEntry }) {
  const tone = engagementTone(client.engagement_score);
  return (
    <Card
      pad="md"
      className={cn(
        "grid items-center gap-5 border-l-4 md:grid-cols-[1.5fr_1fr_1.6fr_28px]",
        engagementBorder(client.engagement_score),
      )}
    >
      {/* identity */}
      <div>
        <div className="mb-1 flex items-baseline gap-2.5">
          <span className="text-[15px] font-semibold text-ink">
            {client.entity_name}
          </span>
          {client.vertical_name && (
            <Chip variant="mute" size="sm">
              {client.vertical_name}
            </Chip>
          )}
        </div>
        <Micro className="block">
          {client.policy_count} polic{client.policy_count === 1 ? "y" : "ies"} ·{" "}
          {formatCurrency(client.total_premium_usd)} premium
        </Micro>
        {client.next_renewal_in_days != null && (
          <div
            className={cn(
              "mt-2 flex items-center gap-1.5 text-[12px]",
              client.next_renewal_in_days <= 60
                ? "font-semibold text-warn"
                : "text-ink-soft",
            )}
          >
            <Calendar size={12} />
            Renewal in {client.next_renewal_in_days}d
          </div>
        )}
      </div>

      {/* engagement */}
      <div>
        <Micro className="block">Engagement</Micro>
        <div className="mt-1 flex items-baseline gap-2">
          <NumDisplay
            size="md"
            className={cn("leading-none", engagementText(client.engagement_score))}
          >
            {client.engagement_score.toFixed(0)}
          </NumDisplay>
          <Caption>{client.engagement_label}</Caption>
        </div>
        <div className="mt-2 h-1 overflow-hidden rounded-full bg-rule">
          <div
            className={cn(
              "h-full",
              tone === "pos"
                ? "bg-pos"
                : tone === "info"
                  ? "bg-info"
                  : tone === "warn"
                    ? "bg-warn"
                    : "bg-spot",
            )}
            style={{ width: `${Math.max(0, Math.min(100, client.engagement_score))}%` }}
          />
        </div>
      </div>

      {/* opps + risks */}
      <div>
        {client.opportunity_flags.length > 0 && (
          <div className="mb-1.5">
            <div className="mb-1 flex items-center gap-1.5 text-[11.5px] font-bold text-info-deep dark:text-info">
              <TrendingUp size={11} /> OPPORTUNITIES · {client.opportunity_flags.length}
            </div>
            <Caption className="text-[12px]">
              {client.opportunity_flags.slice(0, 3).join(" · ")}
            </Caption>
          </div>
        )}
        {client.risk_flags.length > 0 && (
          <div>
            <div className="mb-1 flex items-center gap-1.5 text-[11.5px] font-bold text-neg">
              <TrendingDown size={11} /> RISKS · {client.risk_flags.length}
            </div>
            <Caption className="text-[12px]">
              {client.risk_flags.slice(0, 3).join(" · ")}
            </Caption>
          </div>
        )}
        {client.opportunity_flags.length === 0 && client.risk_flags.length === 0 && (
          <div className="flex items-center gap-1.5 text-pos">
            <CheckCircle2 size={14} />
            <span className="text-[13px] font-semibold">Clean status — no flags</span>
          </div>
        )}
      </div>

      <ChevronRight size={18} className="text-ink-mute" />
    </Card>
  );
}

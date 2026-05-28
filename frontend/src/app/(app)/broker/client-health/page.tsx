"use client";

import Link from "next/link";
import { useMemo, useState } from "react";
import {
  AlertTriangle,
  ArrowDownAZ,
  Calendar,
  HeartPulse,
  MessageSquare,
  Sparkles,
  TrendingDown,
} from "lucide-react";
import { Topbar } from "@/components/chrome/topbar";
import { Card } from "@/components/ui/card";
import { Chip } from "@/components/ui/chip";
import { Eyebrow, NumDisplay, Body, Micro } from "@/components/ui/typography";
import { ScoreBar } from "@/components/ui/score-bar";
import { PageError, PageLoading, RoleGate } from "@/components/base/pageStates";
import { useRoleScopedFetch } from "@/lib/useRoleScopedFetch";
import { fetchClientHealth } from "@/lib/portalApi";
import { useAuthStore } from "@/store/authStore";
import { formatCurrency } from "@/lib/format";
import { cn } from "@/lib/utils";
import type { ClientHealthEntry, ClientHealthResponse } from "@/types/portal";

type Sort = "engagement" | "premium" | "renewal" | "queries" | "name";

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

  return <Body0 data={data} />;
}

function Body0({ data }: { data: ClientHealthResponse }) {
  const [sort, setSort] = useState<Sort>("engagement");

  const sorted = useMemo(() => {
    const s = [...data.clients];
    if (sort === "engagement") s.sort((a, b) => a.engagement_score - b.engagement_score);
    else if (sort === "premium")
      s.sort((a, b) => b.total_premium_usd - a.total_premium_usd);
    else if (sort === "renewal")
      s.sort(
        (a, b) =>
          (a.next_renewal_in_days ?? Infinity) -
          (b.next_renewal_in_days ?? Infinity),
      );
    else if (sort === "queries")
      s.sort((a, b) => b.open_query_count - a.open_query_count);
    else s.sort((a, b) => a.entity_name.localeCompare(b.entity_name));
    return s;
  }, [data.clients, sort]);

  const atRisk = data.clients.filter((c) => c.risk_flags.length > 0).length;
  const opportunities = data.clients.filter(
    (c) => c.opportunity_flags.length > 0,
  ).length;
  const totalOpen = data.clients.reduce((s, c) => s + c.open_query_count, 0);

  return (
    <>
      <Topbar
        crumbs={["Broker Portal", "Client Health"]}
        entity={data.broker_name}
      />
      <div className="flex-1 overflow-y-auto px-9 py-7">
        <div className="mx-auto grid max-w-[1400px] gap-6">
          <header className="flex items-end justify-between gap-6">
            <div>
              <Eyebrow>Health</Eyebrow>
              <h1 className="mt-1 font-display text-[32px] font-semibold leading-none tracking-tight text-ink">
                Client Health
              </h1>
              <Body className="mt-2">
                Engagement, opportunities, and risk flags across the book.
                Lowest-engagement clients surface first by default.
              </Body>
            </div>
            <SortPicker value={sort} onChange={setSort} />
          </header>

          <div className="grid gap-4 sm:grid-cols-4">
            <SummaryTile label="Clients">{data.clients.length}</SummaryTile>
            <SummaryTile
              label="At-risk flags"
              tone={atRisk > 0 ? "neg" : undefined}
            >
              {atRisk}
            </SummaryTile>
            <SummaryTile
              label="Opportunity flags"
              tone={opportunities > 0 ? "pos" : undefined}
            >
              {opportunities}
            </SummaryTile>
            <SummaryTile
              label="Open queries"
              tone={totalOpen > 0 ? "spot" : undefined}
            >
              {totalOpen}
            </SummaryTile>
          </div>

          <div className="space-y-3">
            {sorted.map((c) => (
              <ClientCard key={c.entity_name} client={c} />
            ))}
          </div>
        </div>
      </div>
    </>
  );
}

function ClientCard({ client }: { client: ClientHealthEntry }) {
  const engagementTone =
    client.engagement_score >= 75
      ? "pos"
      : client.engagement_score >= 50
        ? "info"
        : client.engagement_score >= 25
          ? "warn"
          : "neg";

  const renewalChip =
    client.next_renewal_in_days == null
      ? null
      : client.next_renewal_in_days <= 60
        ? "spot"
        : client.next_renewal_in_days <= 120
          ? "warn"
          : "mute";

  return (
    <Card pad="md" className="grid gap-4 md:grid-cols-[1.4fr_1fr_1fr_auto]">
      {/* Identity + engagement */}
      <div>
        <div className="flex items-center gap-2">
          <h3 className="text-[16px] font-semibold text-ink">
            {client.entity_name}
          </h3>
          {client.vertical_name && (
            <Chip variant="mute" size="sm">
              {client.vertical_name}
            </Chip>
          )}
        </div>
        <div className="mt-2 flex items-center gap-2">
          <Chip variant={engagementTone} size="sm">
            <HeartPulse size={11} />
            {client.engagement_label}
          </Chip>
          <span className="text-[12px] tabular-nums text-ink-soft">
            {client.engagement_score.toFixed(0)} / 100
          </span>
        </div>
        <ScoreBar
          value={client.engagement_score}
          max={100}
          className="mt-2 max-w-[260px]"
          showValue={false}
          thresholds={[
            { at: 25, tone: "neg" },
            { at: 50, tone: "warn" },
            { at: 75, tone: "info" },
            { at: 100, tone: "pos" },
          ]}
        />
      </div>

      {/* Premium / policies */}
      <div className="space-y-1">
        <div>
          <Micro>Premium under management</Micro>
          <p className="text-[16px] font-semibold tabular-nums text-ink">
            {formatCurrency(client.total_premium_usd)}
          </p>
        </div>
        <Micro className="block">
          {client.policy_count} polic{client.policy_count === 1 ? "y" : "ies"}
        </Micro>
      </div>

      {/* Pulse */}
      <div className="space-y-1.5 text-[12.5px] text-ink-soft">
        {client.months_since_last_message != null && (
          <div className="flex items-center gap-1.5">
            <MessageSquare size={11} />
            Last message{" "}
            <span className="font-semibold text-ink">
              {client.months_since_last_message}mo
            </span>{" "}
            ago
          </div>
        )}
        {client.avg_response_hours != null && (
          <div className="flex items-center gap-1.5">
            <ArrowDownAZ size={11} />
            Avg response{" "}
            <span className="font-semibold text-ink">
              {client.avg_response_hours.toFixed(1)}h
            </span>
          </div>
        )}
        {client.open_query_count > 0 && (
          <Chip variant="spot" size="sm">
            {client.open_query_count} open quer
            {client.open_query_count === 1 ? "y" : "ies"}
          </Chip>
        )}
        {client.next_renewal_in_days != null && renewalChip && (
          <Chip variant={renewalChip} size="sm">
            <Calendar size={10} />
            Renewal in {client.next_renewal_in_days}d
          </Chip>
        )}
      </div>

      {/* Flags */}
      <div className="space-y-1.5 text-[12px] md:max-w-[260px]">
        {client.opportunity_flags.slice(0, 3).map((f, i) => (
          <FlagLine key={`o-${i}`} tone="pos" icon={Sparkles}>
            {f}
          </FlagLine>
        ))}
        {client.risk_flags.slice(0, 3).map((f, i) => (
          <FlagLine key={`r-${i}`} tone="neg" icon={AlertTriangle}>
            {f}
          </FlagLine>
        ))}
        {client.risk_flags.length === 0 &&
          client.opportunity_flags.length === 0 && (
            <Micro>No flags.</Micro>
          )}
      </div>
    </Card>
  );
}

function FlagLine({
  tone,
  icon: Icon,
  children,
}: {
  tone: "pos" | "neg";
  icon: typeof Sparkles;
  children: React.ReactNode;
}) {
  return (
    <div
      className={cn(
        "flex items-start gap-1.5",
        tone === "pos" ? "text-pos" : "text-neg",
      )}
    >
      <Icon size={11} className="mt-0.5 shrink-0" />
      <span>{children}</span>
    </div>
  );
}

function SortPicker({
  value,
  onChange,
}: {
  value: Sort;
  onChange: (s: Sort) => void;
}) {
  return (
    <label className="flex items-center gap-2 text-[12.5px]">
      <span className="text-ink-mute">Sort:</span>
      <select
        value={value}
        onChange={(e) => onChange(e.target.value as Sort)}
        className="rounded-btn border border-rule-strong bg-surface px-3 py-1.5 text-[13px] font-medium text-ink focus:border-info focus:outline-none focus:ring-2 focus:ring-info/30"
      >
        <option value="engagement">Engagement (low first)</option>
        <option value="premium">Premium (high first)</option>
        <option value="renewal">Renewal (soonest)</option>
        <option value="queries">Open queries</option>
        <option value="name">Name</option>
      </select>
    </label>
  );
}

function SummaryTile({
  label,
  tone,
  children,
}: {
  label: string;
  tone?: "pos" | "neg" | "spot" | "warn";
  children: React.ReactNode;
}) {
  const variant =
    tone === "pos"
      ? "pos"
      : tone === "neg"
        ? "neg"
        : tone === "spot"
          ? "spot"
          : tone === "warn"
            ? "warn"
            : "default";
  return (
    <Card pad="md" variant={variant}>
      <Micro
        className={cn(
          "block",
          tone === "spot" && "text-spot-deep dark:text-spot",
          tone === "pos" && "text-pos",
          tone === "neg" && "text-neg",
        )}
      >
        {label}
      </Micro>
      <div className="mt-2">
        <NumDisplay size="md">{children}</NumDisplay>
      </div>
    </Card>
  );
}

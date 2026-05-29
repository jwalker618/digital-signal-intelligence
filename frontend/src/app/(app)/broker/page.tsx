"use client";

import Link from "next/link";
import { useMemo } from "react";
import { AlertCircle, Briefcase, ChevronRight } from "lucide-react";
import { Topbar } from "@/components/chrome/topbar";
import {
  Body,
  Card,
  Caption,
  Chip,
  Eyebrow,
  Micro,
  NumDisplay,
} from "@/components/ui";
import { PageError, PageLoading, RoleGate } from "@/components/base/pageStates";
import { useRoleScopedFetch } from "@/lib/useRoleScopedFetch";
import { fetchOverview } from "@/lib/portalApi";
import { useAuthStore } from "@/store/authStore";
import { formatCurrency, formatText } from "@/lib/format";
import { tierStatus } from "@/lib/portalTone";
import { portalToneToTone } from "@/lib/design-tokens";
import { cn } from "@/lib/utils";
import type {
  BrokerOverviewResponse,
  ClientBookEntry,
  OverviewResponse,
} from "@/types/portal";

export default function BrokerBookPage() {
  const accessToken = useAuthStore((s) => s.accessToken);
  const user = useAuthStore((s) => s.user);
  const enabled = !!accessToken && user?.role === "BROKER";

  const { data, error, loading } = useRoleScopedFetch<OverviewResponse>({
    fetcher: () => fetchOverview(accessToken),
    enabled,
    deps: [accessToken],
  });

  if (!user) return <PageLoading message="Signing in…" />;
  if (user.role && user.role !== "BROKER") return <RoleGate expected="broker" />;
  if (loading) return <PageLoading />;
  if (error) return <PageError message={error} />;
  if (!data || data.role !== "BROKER") return <RoleGate expected="broker" />;

  return <BookBody data={data} />;
}

function BookBody({ data }: { data: BrokerOverviewResponse }) {
  const grouped = useMemo(() => {
    const m = new Map<string, ClientBookEntry[]>();
    for (const c of data.clients) {
      const list = m.get(c.entity_name) ?? [];
      list.push(c);
      m.set(c.entity_name, list);
    }
    return [...m.entries()].sort((a, b) => a[0].localeCompare(b[0]));
  }, [data.clients]);

  const totalPolicies = data.clients.length;
  const totalPremium = data.clients.reduce(
    (sum, c) => sum + (c.recommended_premium ?? 0),
    0,
  );
  const tierBuckets = useMemo(() => {
    const counts: Record<number, number> = { 1: 0, 2: 0, 3: 0, 4: 0, 5: 0 };
    for (const c of data.clients) {
      if (c.tier && counts[c.tier] != null) counts[c.tier] += 1;
    }
    return [1, 2, 3, 4, 5].map((t) => ({ t, n: counts[t] }));
  }, [data.clients]);
  const maxTier = Math.max(...tierBuckets.map((b) => b.n), 1);
  const avgScore = useMemo(() => {
    const scored = data.clients.filter((c) => c.composite_score != null);
    if (!scored.length) return null;
    return Math.round(
      scored.reduce((s, c) => s + (c.composite_score ?? 0), 0) / scored.length,
    );
  }, [data.clients]);

  return (
    <>
      <Topbar
        crumbs={["Broker Portal", "Book of Clients"]}
        entity={data.broker.name}
      />
      <div className="flex-1 overflow-y-auto px-9 py-7">
        <div className="mx-auto grid max-w-[1400px] gap-4">
          {/* Hero strip — broker identity + 4 KPIs */}
          <div className="grid gap-4 md:grid-cols-[1.6fr_1fr_1fr_1fr]">
            <Card pad="lg" className="flex items-center gap-4">
              <div className="flex h-16 w-16 shrink-0 items-center justify-center rounded-card bg-info-soft text-info-deep dark:text-info">
                <Briefcase size={28} />
              </div>
              <div className="min-w-0">
                <Eyebrow>Broker book</Eyebrow>
                <h1 className="mt-1 font-display text-[28px] font-semibold leading-tight tracking-tight text-ink">
                  {data.broker.name}
                </h1>
                <Caption className="mt-1.5 block">
                  {grouped.length} client{grouped.length === 1 ? "" : "s"} · {totalPolicies}{" "}
                  polic{totalPolicies === 1 ? "y" : "ies"} in force
                </Caption>
              </div>
            </Card>
            <Card pad="lg">
              <Eyebrow>Aggregate premium</Eyebrow>
              <NumDisplay size="lg" className="mt-1.5 block">
                {formatCurrency(totalPremium)}
              </NumDisplay>
              <Micro className="mt-1 block">annual</Micro>
            </Card>
            <Card pad="lg" variant="info">
              <Eyebrow className="text-info-deep dark:text-info">
                Avg signal score
              </Eyebrow>
              <NumDisplay size="lg" className="mt-1.5 block text-info-deep dark:text-info">
                {avgScore != null ? avgScore : "—"}
              </NumDisplay>
              <Micro className="mt-1 block">across the book</Micro>
            </Card>
            <Card pad="lg" variant={data.open_queries_count > 0 ? "spot" : "default"}>
              <Eyebrow
                className={
                  data.open_queries_count > 0
                    ? "text-spot-deep dark:text-spot"
                    : ""
                }
              >
                Awaiting you
              </Eyebrow>
              <NumDisplay
                size="lg"
                className={cn(
                  "mt-1.5 block",
                  data.open_queries_count > 0 && "text-spot-deep dark:text-spot",
                )}
              >
                {data.open_queries_count}
              </NumDisplay>
              <Micro className="mt-1 block">open queries</Micro>
            </Card>
          </div>

          {data.open_queries_count > 0 && (
            <Link
              href="/broker/communications"
              className="flex items-center gap-3 rounded-card border border-spot bg-spot-soft px-4 py-3 text-[13.5px] font-medium text-spot-deep transition hover:bg-spot hover:text-white dark:text-spot"
            >
              <AlertCircle size={16} />
              {data.open_queries_count} open quer
              {data.open_queries_count === 1 ? "y" : "ies"} awaiting reply
              <ChevronRight size={14} className="ml-auto" />
            </Link>
          )}

          {/* Book roster table */}
          <Card
            pad="none"
            header={`Book roster`}
            headerRight={
              <Chip variant="mute" size="sm">
                {totalPolicies} polic{totalPolicies === 1 ? "y" : "ies"}
              </Chip>
            }
          >
            {grouped.length === 0 ? (
              <div className="px-5 py-8 text-center">
                <Body className="italic">Your book is empty.</Body>
              </div>
            ) : (
              <table className="w-full text-[13px]">
                <thead>
                  <tr className="border-b border-rule bg-surface-sunken text-left">
                    <ColHead>Client</ColHead>
                    <ColHead>Coverage</ColHead>
                    <ColHead>Score</ColHead>
                    <ColHead>Tier</ColHead>
                    <ColHead>Percentile</ColHead>
                    <ColHead align="right">Premium</ColHead>
                    <ColHead>Status</ColHead>
                    <ColHead align="right" />
                  </tr>
                </thead>
                <tbody>
                  {grouped.flatMap(([client, items]) =>
                    items.map((c) => (
                      <BookRow key={c.submission_code} client={client} entry={c} />
                    )),
                  )}
                </tbody>
              </table>
            )}
          </Card>

          {/* Tier mix */}
          <div className="grid gap-4 lg:grid-cols-[1fr_1.4fr]">
            <Card pad="lg">
              <Eyebrow>Tier mix</Eyebrow>
              <h2 className="mt-1.5 text-[17px] font-semibold leading-tight text-ink">
                Risk quality across the book
              </h2>
              <div className="mt-4 flex h-[140px] items-end gap-3.5">
                {tierBuckets.map(({ t, n }) => {
                  const color =
                    t <= 2 ? "bg-pos" : t === 3 ? "bg-info" : t === 4 ? "bg-warn" : "bg-neg";
                  const numColor =
                    t <= 2
                      ? "text-pos"
                      : t === 3
                        ? "text-info"
                        : t === 4
                          ? "text-warn"
                          : "text-neg";
                  return (
                    <div key={t} className="flex flex-1 flex-col items-center gap-1.5">
                      <span className={cn("text-[15px] font-semibold tabular-nums", numColor)}>
                        {n}
                      </span>
                      <div
                        className={cn("w-full rounded-t-md", color)}
                        style={{
                          height: `${Math.max(4, (n / maxTier) * 100)}%`,
                          minHeight: 4,
                        }}
                      />
                      <Micro>Tier {t}</Micro>
                    </div>
                  );
                })}
              </div>
              <Caption className="mt-4 block border-t border-rule pt-3">
                Most of the book sits in the mid-tier band; outliers (tier 4–5) are worth a
                proactive touchpoint.
              </Caption>
            </Card>

            <Card pad="lg">
              <div className="flex items-baseline justify-between">
                <div>
                  <Eyebrow>Open queries</Eyebrow>
                  <h2 className="mt-1.5 text-[17px] font-semibold leading-tight text-ink">
                    Things waiting on you or your clients
                  </h2>
                </div>
                {data.open_queries_count > 0 && (
                  <Chip variant="spot" size="sm">
                    {data.open_queries_count} open
                  </Chip>
                )}
              </div>
              <div className="mt-4 flex flex-col gap-2">
                {data.clients
                  .filter(
                    (c) => c.referral_state && /awaiting/i.test(c.referral_state),
                  )
                  .slice(0, 4)
                  .map((c) => (
                    <div
                      key={c.submission_code}
                      className="grid grid-cols-[1fr_auto_auto] items-center gap-3 rounded-card border border-rule bg-surface-elev px-3.5 py-2.5"
                    >
                      <div className="min-w-0">
                        <div className="truncate text-[13px] font-semibold text-ink">
                          {c.entity_name}
                        </div>
                        <Micro className="mt-0.5 block truncate">
                          {c.coverage} · {c.submission_code}
                        </Micro>
                      </div>
                      <Chip
                        variant={
                          c.awaiting_party && /broker/i.test(c.awaiting_party)
                            ? "spot"
                            : "info"
                        }
                        size="sm"
                      >
                        {c.awaiting_party && /broker/i.test(c.awaiting_party)
                          ? "on you"
                          : "on client"}
                      </Chip>
                      <Micro>—</Micro>
                    </div>
                  ))}
                {data.open_queries_count === 0 && (
                  <Caption className="italic">No open queries.</Caption>
                )}
              </div>
            </Card>
          </div>
        </div>
      </div>
    </>
  );
}

function BookRow({
  client,
  entry,
}: {
  client: string;
  entry: ClientBookEntry;
}) {
  const tone = tierStatus(entry.tier);
  const chipTone = portalToneToTone(tone.tone);
  const awaiting =
    entry.referral_state && /awaiting/i.test(entry.referral_state);
  const tierColor =
    entry.tier == null
      ? "bg-surface-sunken text-ink-mute"
      : entry.tier <= 2
        ? "bg-pos-soft text-pos"
        : entry.tier === 3
          ? "bg-info-soft text-info"
          : entry.tier === 4
            ? "bg-warn-soft text-warn"
            : "bg-neg-soft text-neg";

  return (
    <tr className="border-b border-rule last:border-0 hover:bg-surface-sunken/40">
      <td className="px-5 py-2.5">
        <Link
          href={`/client/submissions/${entry.submission_code}`}
          className="block font-semibold text-ink hover:underline"
        >
          {client}
        </Link>
      </td>
      <td className="px-5 py-2.5 text-ink-soft">{entry.coverage}</td>
      <td className="px-5 py-2.5">
        {entry.composite_score != null ? (
          <span className="font-semibold tabular-nums text-info">
            {entry.composite_score.toFixed(0)}
          </span>
        ) : (
          <span className="text-ink-mute">—</span>
        )}
      </td>
      <td className="px-5 py-2.5">
        {entry.tier != null ? (
          <span
            className={cn(
              "inline-flex h-6 w-6 items-center justify-center rounded-md text-[12px] font-bold",
              tierColor,
            )}
          >
            {entry.tier}
          </span>
        ) : (
          <span className="text-ink-mute">—</span>
        )}
      </td>
      <td className="px-5 py-2.5 tabular-nums text-ink-soft">
        {entry.peer_percentile_rank != null
          ? `${Math.round(entry.peer_percentile_rank * 100)}th`
          : "—"}
      </td>
      <td className="px-5 py-2.5 text-right font-semibold tabular-nums text-ink">
        {entry.recommended_premium != null
          ? formatCurrency(entry.recommended_premium)
          : "—"}
      </td>
      <td className="px-5 py-2.5">
        <Chip variant={awaiting ? "spot" : chipTone} size="sm">
          {awaiting ? formatText(entry.referral_state ?? "", "capitalize") : tone.label}
        </Chip>
      </td>
      <td className="px-5 py-2.5 text-right">
        <Link
          href={`/client/submissions/${entry.submission_code}`}
          className="inline-flex items-center text-ink-mute hover:text-ink"
          aria-label={`Open ${entry.submission_code}`}
        >
          <ChevronRight size={16} />
        </Link>
      </td>
    </tr>
  );
}

function ColHead({
  children,
  align,
}: {
  children?: React.ReactNode;
  align?: "left" | "right";
}) {
  return (
    <th
      className={cn(
        "px-5 py-2 text-[11px] font-semibold uppercase tracking-[0.06em] text-ink-mute",
        align === "right" ? "text-right" : "text-left",
      )}
    >
      {children ?? null}
    </th>
  );
}

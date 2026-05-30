"use client";

import Link from "next/link";
import { useMemo, useState } from "react";
import { ChevronRight, MessageSquare } from "lucide-react";
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
import { fetchCommunications } from "@/lib/portalApi";
import { useAuthStore } from "@/store/authStore";
import { fmtRelative, cn } from "@/lib/utils";
import type {
  CommunicationItem,
  CommunicationsListResponse,
} from "@/types/portal";

type Awaiting = "all" | "broker" | "client" | "resolved";

export default function BrokerCommunicationsPage() {
  const accessToken = useAuthStore((s) => s.accessToken);
  const user = useAuthStore((s) => s.user);
  const enabled = !!accessToken && user?.role === "BROKER";

  const { data, error, loading } = useRoleScopedFetch<CommunicationsListResponse>({
    fetcher: () => fetchCommunications(accessToken),
    enabled,
    deps: [accessToken],
  });

  if (!user) return <PageLoading message="Signing in…" />;
  if (user.role && user.role !== "BROKER") return <RoleGate expected="broker" />;
  if (loading) return <PageLoading />;
  if (error) return <PageError message={error} />;
  if (!data) return <PageLoading />;

  return <CommsBody data={data} />;
}

function classifyAwaiting(
  item: CommunicationItem,
): "broker" | "client" | "resolved" | "other" {
  if (!item.is_open) return "resolved";
  if (item.awaiting_party && /broker|me/i.test(item.awaiting_party))
    return "broker";
  if (item.awaiting_party && /client|insured/i.test(item.awaiting_party))
    return "client";
  return "other";
}

function CommsBody({ data }: { data: CommunicationsListResponse }) {
  const [filter, setFilter] = useState<Awaiting>("all");
  const [line, setLine] = useState<string>("all");

  const onBroker = data.items.filter(
    (i) => classifyAwaiting(i) === "broker",
  ).length;
  const onClient = data.items.filter(
    (i) => classifyAwaiting(i) === "client",
  ).length;
  const resolved = data.items.filter((i) => !i.is_open).length;
  const totalOpen = data.items.length - resolved;

  // Distinct coverage lines for the Line filter pills.
  const lines = useMemo(
    () => [...new Set(data.items.map((i) => i.coverage).filter(Boolean))].sort(),
    [data.items],
  );

  const filtered = useMemo(() => {
    return data.items.filter((it) => {
      if (line !== "all" && it.coverage !== line) return false;
      const cls = classifyAwaiting(it);
      if (filter === "all") return cls !== "resolved";
      if (filter === "resolved") return cls === "resolved";
      return cls === filter;
    });
  }, [data.items, filter, line]);

  return (
    <>
      <Topbar crumbs={["Broker Portal", "Communications"]} />
      <div className="flex-1 overflow-y-auto px-9 py-7">
        <div className="grid gap-4">
          <header className="flex flex-wrap items-end justify-between gap-6">
            <div>
              <Eyebrow>Communications</Eyebrow>
              <h1 className="mt-1.5 font-display text-[32px] font-semibold leading-tight tracking-tight text-ink">
                Queries across your client book
              </h1>
            </div>
            <div className="flex flex-wrap gap-7">
              <KpiSnug label="Total open" value={totalOpen} />
              <KpiSnug label="Awaiting you" value={onBroker} tone="spot" />
              <KpiSnug label="Awaiting client" value={onClient} tone="info" />
              <KpiSnug label="Resolved" value={resolved} tone="pos" />
            </div>
          </header>

          {/* Filter pills */}
          <div className="flex flex-wrap items-center gap-2">
            <Micro className="mr-1">Awaiting:</Micro>
            <FilterChip
              label="All open"
              active={filter === "all"}
              onClick={() => setFilter("all")}
            />
            <FilterChip
              label="On me"
              active={filter === "broker"}
              onClick={() => setFilter("broker")}
            />
            <FilterChip
              label="On client"
              active={filter === "client"}
              onClick={() => setFilter("client")}
            />
            <FilterChip
              label="Resolved"
              active={filter === "resolved"}
              onClick={() => setFilter("resolved")}
            />
            {lines.length > 1 && (
              <>
                <Micro className="ml-3 mr-1">Line:</Micro>
                <FilterChip
                  label="All"
                  active={line === "all"}
                  onClick={() => setLine("all")}
                />
                {lines.map((ln) => (
                  <FilterChip
                    key={ln}
                    label={ln}
                    active={line === ln}
                    onClick={() => setLine(ln)}
                  />
                ))}
              </>
            )}
            <span className="ml-auto">
              <Caption>Sort: most recent</Caption>
            </span>
          </div>

          {/* Threads */}
          {filtered.length === 0 ? (
            <Card pad="lg" className="flex items-center gap-3">
              <MessageSquare size={20} className="text-ink-mute" />
              <div>
                <Eyebrow>No threads</Eyebrow>
                <Body className="mt-1">No threads match the filter.</Body>
              </div>
            </Card>
          ) : (
            <Card pad="none">
              <ul>
                {filtered.map((it, i) => (
                  <BrokerThreadRow
                    key={it.referral_code}
                    item={it}
                    first={i === 0}
                  />
                ))}
              </ul>
            </Card>
          )}
        </div>
      </div>
    </>
  );
}

function FilterChip({
  label,
  active,
  onClick,
}: {
  label: string;
  active: boolean;
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={cn(
        "rounded-chip border px-2.5 py-1 text-[11.5px] font-medium transition",
        active
          ? "border-ink bg-ink text-canvas"
          : "border-rule-strong bg-surface text-ink-soft hover:bg-surface-sunken",
      )}
    >
      {label}
    </button>
  );
}

function BrokerThreadRow({
  item,
  first,
}: {
  item: CommunicationItem;
  first: boolean;
}) {
  const cls = classifyAwaiting(item);
  const accent =
    cls === "broker"
      ? "bg-spot"
      : cls === "client"
        ? "bg-info"
        : cls === "resolved"
          ? "bg-transparent"
          : "bg-info";
  const chipTone: "spot" | "info" | "pos" | "mute" =
    cls === "broker"
      ? "spot"
      : cls === "client"
        ? "info"
        : cls === "resolved"
          ? "pos"
          : "info";
  const statusLabel =
    cls === "broker"
      ? "awaiting you"
      : cls === "client"
        ? "awaiting client"
        : cls === "resolved"
          ? "resolved"
          : "open";

  return (
    <li>
      <Link
        href={`/broker/communications/${item.referral_code}`}
        className={cn(
          "grid grid-cols-[4px_1.6fr_2.4fr_110px_110px_70px_28px] items-center gap-4 px-4 py-4 transition hover:bg-surface-sunken/40",
          !first && "border-t border-rule",
        )}
      >
        <span className={cn("h-10 w-1 rounded-sm", accent)} />
        <div>
          <div className="text-[13.5px] font-bold text-ink">
            {item.entity_name}
          </div>
          <Micro className="mt-0.5 block">
            {item.coverage} · {item.referral_code}
          </Micro>
        </div>
        <div className="min-w-0">
          <div className="truncate text-[13px] text-ink">
            {item.last_message_excerpt ? `"${item.last_message_excerpt}"` : "—"}
          </div>
        </div>
        <Chip variant="mute" size="sm">
          {item.coverage}
        </Chip>
        <Chip variant={chipTone} size="sm">
          {statusLabel}
        </Chip>
        <Micro className="text-right">{fmtRelative(item.last_message_at)}</Micro>
        <ChevronRight size={18} className="text-ink-mute" />
      </Link>
    </li>
  );
}

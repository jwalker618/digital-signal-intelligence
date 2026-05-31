"use client";

import Link from "next/link";
import { useState } from "react";
import { ChevronRight, MessageSquare, Paperclip } from "lucide-react";
import { Topbar } from "@/components/chrome/topbar";
import { Card } from "@/components/ui/card";
import { Chip } from "@/components/ui/chip";
import { Eyebrow, Body, Micro, Caption } from "@/components/ui/typography";
import { KpiSnug } from "@/components/ui/kpi-snug";
import { PageError, PageLoading, RoleGate } from "@/components/base/pageStates";
import { useRoleScopedFetch } from "@/lib/useRoleScopedFetch";
import { fetchCommunications } from "@/lib/portalApi";
import { useAuthStore } from "@/store/authStore";
import { fmtRelative } from "@/lib/utils";
import { formatText } from "@/lib/format";
import { cn } from "@/lib/utils";
import type {
  CommunicationItem,
  CommunicationsListResponse,
} from "@/types/portal";

type FilterKey = "open" | "all" | string;

export default function ClientCommunicationsPage() {
  const accessToken = useAuthStore((s) => s.accessToken);
  const user = useAuthStore((s) => s.user);
  const enabled = !!accessToken && user?.role === "CLIENT";

  const { data, error, loading } = useRoleScopedFetch<CommunicationsListResponse>({
    fetcher: () => fetchCommunications(accessToken),
    enabled,
    deps: [accessToken],
  });

  if (!user) return <PageLoading message="Signing in…" />;
  if (user.role && user.role !== "CLIENT") return <RoleGate expected="client" />;
  if (loading) return <PageLoading />;
  if (error) return <PageError message={error} />;
  if (!data) return <PageLoading />;

  return <CommsBody data={data} />;
}

function CommsBody({ data }: { data: CommunicationsListResponse }) {
  const [filter, setFilter] = useState<FilterKey>("open");

  const awaitingYou = data.items.filter(
    (i) => i.is_open && i.awaiting_party && /client|insured|you/i.test(i.awaiting_party),
  ).length;
  const inReview = data.items.filter(
    (i) => i.is_open && !(i.awaiting_party && /client|insured|you/i.test(i.awaiting_party)),
  ).length;
  const resolved = data.items.filter((i) => !i.is_open).length;

  const lines = Array.from(
    new Set(data.items.map((i) => i.coverage).filter(Boolean)),
  );

  const filtered = data.items.filter((i) => {
    if (filter === "open") return i.is_open;
    if (filter === "all") return true;
    return i.coverage === filter;
  });

  return (
    <>
      <Topbar
        crumbs={["Client Portal", "Communications"]}
      />
      <div className="flex-1 overflow-y-auto px-9 py-7">
        <div className="grid gap-4">
          {/* ────────── title + KPI strip ────────── */}
          <div className="flex flex-wrap items-end justify-between gap-6">
            <div>
              <h1 className="mt-1.5 font-display text-[32px] font-semibold leading-none tracking-tight text-ink">
                Queries from your carriers + broker
              </h1>
            </div>
            <div className="flex flex-wrap gap-7">
              <KpiSnug label="Open threads" value={data.open_count} />
              <KpiSnug
                label="Awaiting you"
                value={awaitingYou}
                tone={awaitingYou > 0 ? "spot" : "default"}
              />
              <KpiSnug label="In review" value={inReview} />
              <KpiSnug
                label="Resolved (30d)"
                value={resolved}
                tone={resolved > 0 ? "pos" : "default"}
              />
            </div>
          </div>

          {/* ────────── filter bar ────────── */}
          <div className="flex flex-wrap items-center gap-2">
            <Micro className="mr-1">Filter:</Micro>
            <FilterPill
              label="Open"
              active={filter === "open"}
              onClick={() => setFilter("open")}
            />
            <FilterPill
              label="All"
              active={filter === "all"}
              onClick={() => setFilter("all")}
            />
            {lines.slice(0, 4).map((line) => (
              <FilterPill
                key={line}
                label={line}
                active={filter === line}
                onClick={() => setFilter(line)}
              />
            ))}
            <div className="flex-1" />
            <Caption>Sort: most recent</Caption>
          </div>

          {/* ────────── threads card ────────── */}
          <Card pad="none" className="overflow-hidden">
            {filtered.length === 0 ? (
              <div className="flex items-center gap-3 px-5 py-6">
                <MessageSquare size={20} className="text-ink-mute" />
                <div>
                  <Eyebrow>No threads</Eyebrow>
                  <Body className="mt-1">
                    Nothing matches the current filter.
                  </Body>
                </div>
              </div>
            ) : (
              filtered.map((item, i) => (
                <ThreadRow
                  key={item.referral_code}
                  item={item}
                  first={i === 0}
                />
              ))
            )}
          </Card>
        </div>
      </div>
    </>
  );
}

function FilterPill({
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
        "inline-flex items-center gap-1.5 rounded-chip border px-2.5 py-1 text-[11.5px] font-medium transition",
        active
          ? "border-ink bg-ink text-canvas"
          : "border-rule bg-surface-sunken text-ink-soft hover:border-rule-strong",
      )}
    >
      {label}
    </button>
  );
}

function ThreadRow({
  item,
  first,
}: {
  item: CommunicationItem;
  first: boolean;
}) {
  const awaitingYou =
    item.is_open &&
    item.awaiting_party &&
    /client|insured|you/i.test(item.awaiting_party);
  const tone: "spot" | "info" | "pos" | "mute" = awaitingYou
    ? "spot"
    : !item.is_open
      ? "pos"
      : "info";
  const accent =
    tone === "spot"
      ? "bg-spot"
      : tone === "pos"
        ? "bg-pos"
        : tone === "info"
          ? "bg-info"
          : "bg-ink-mute";

  return (
    <Link
      href={`/client/communications/${item.referral_code}`}
      className={cn(
        "grid grid-cols-[4px_1fr_auto_20px] items-center gap-4 px-5 py-4 transition hover:bg-surface-sunken/40",
        !first && "border-t border-rule",
      )}
    >
      <span
        className={cn(
          "h-10 w-1 rounded-sm",
          item.is_open ? accent : "bg-transparent",
        )}
        aria-hidden
      />
      <div className="min-w-0">
        <div className="mb-1 flex flex-wrap items-baseline gap-2.5">
          <span className="text-[14px] font-semibold text-ink">
            {item.entity_name}
          </span>
          {item.last_message_direction && (
            <Micro>{formatText(item.last_message_direction, "upper")}</Micro>
          )}
          <Chip variant="mute" size="sm">
            {item.coverage}
          </Chip>
        </div>
        {item.last_message_excerpt && (
          <p className="truncate text-[13.5px] leading-snug text-ink">
            “{item.last_message_excerpt}”
          </p>
        )}
        {item.request_signal_evidence && (
          <div className="mt-1 flex items-center gap-1.5">
            <Paperclip size={12} className="text-ink-mute" />
            <code className="rounded bg-surface-sunken px-1.5 py-0.5 text-[11px] text-ink-soft">
              {item.request_signal_evidence}
            </code>
            <Micro>evidence requested</Micro>
          </div>
        )}
      </div>
      <div className="flex flex-col items-end gap-1.5">
        <Chip variant={tone === "mute" ? "mute" : tone} size="sm">
          {awaitingYou
            ? "awaiting you"
            : !item.is_open
              ? "resolved"
              : formatText(item.status, "capitalize")}
        </Chip>
        <Micro>{fmtRelative(item.last_message_at)}</Micro>
      </div>
      <ChevronRight size={18} className="text-ink-mute" />
    </Link>
  );
}

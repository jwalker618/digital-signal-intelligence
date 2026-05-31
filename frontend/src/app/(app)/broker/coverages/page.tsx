"use client";

import Link from "next/link";
import { useMemo, useState } from "react";
import { ChevronRight, ShieldCheck } from "lucide-react";
import { lineIcon } from "@/lib/coverageIcon";
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
import { fetchOverview } from "@/lib/portalApi";
import { useAuthStore } from "@/store/authStore";
import { formatCurrency, formatText } from "@/lib/format";
import { tierStatus } from "@/lib/portalTone";
import { portalToneToTone } from "@/lib/design-tokens";
import { cn } from "@/lib/utils";
import type { ClientBookEntry, OverviewResponse } from "@/types/portal";

type GroupKey = "line" | "client" | "carrier";
type StatusFilter = "all" | "bound" | "review" | "awaiting";

export default function BrokerCoveragesPage() {
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

  return <CoveragesBody data={data} />;
}

function matchesStatus(entry: ClientBookEntry, f: StatusFilter): boolean {
  if (f === "all") return true;
  const status = (entry.status ?? "").toLowerCase();
  const ref = (entry.referral_state ?? "").toLowerCase();
  if (f === "bound") return /bound/.test(status);
  if (f === "review") return /review/.test(status) || /review/.test(ref);
  if (f === "awaiting") return /awaiting/.test(ref) || /awaiting/.test(status);
  return true;
}

function CoveragesBody({
  data,
}: {
  data: Extract<OverviewResponse, { role: "BROKER" }>;
}) {
  const [group, setGroup] = useState<GroupKey>("line");
  const [status, setStatus] = useState<StatusFilter>("all");

  const filtered = useMemo(
    () => data.clients.filter((c) => matchesStatus(c, status)),
    [data.clients, status],
  );

  const totalPolicies = filtered.length;
  const totalPremium = filtered.reduce(
    (s, c) => s + (c.recommended_premium ?? 0),
    0,
  );
  const totalLines = useMemo(
    () => new Set(filtered.map((c) => c.coverage)).size,
    [filtered],
  );
  const inReview = filtered.filter(
    (c) =>
      /review|awaiting/i.test(c.status ?? "") ||
      /awaiting/i.test(c.referral_state ?? ""),
  ).length;

  const groups = useMemo(() => {
    const map = new Map<string, ClientBookEntry[]>();
    for (const c of filtered) {
      const key =
        group === "line"
          ? c.coverage
          : group === "client"
            ? c.entity_name
            : `Carrier — ${c.submission_code.slice(0, 8)}`;
      const list = map.get(key) ?? [];
      list.push(c);
      map.set(key, list);
    }
    return [...map.entries()]
      .map(([key, items]) => ({
        key,
        items,
        total: items.reduce((s, c) => s + (c.recommended_premium ?? 0), 0),
      }))
      .sort((a, b) => b.total - a.total);
  }, [filtered, group]);

  return (
    <>
      <Topbar
        crumbs={["Broker Portal", "Coverages"]}
        entity={data.broker.name}
      />
      <div className="flex-1 overflow-y-auto px-9 py-7">
        <div className="grid gap-4">
          {/* Title + KPIs */}
          <header className="flex flex-wrap items-end justify-between gap-6">
            <div>
              <h1 className="mt-1.5 font-display text-[32px] font-semibold leading-tight tracking-tight text-ink">
                Your book, grouped by line
              </h1>
              <Body className="mt-1.5">
                Every active policy across your client roster, organised by coverage line and
                ranked by premium share.
              </Body>
            </div>
            <div className="flex flex-wrap gap-7">
              <KpiSnug label="Policies" value={totalPolicies} />
              <KpiSnug label="Lines" value={totalLines} />
              <KpiSnug label="Annual premium" value={formatCurrency(totalPremium)} />
              <KpiSnug label="In review" value={inReview} tone="spot" />
            </div>
          </header>

          {/* Filters */}
          <div className="flex flex-wrap items-center gap-2">
            <Micro className="mr-1">Group by:</Micro>
            <FilterChip
              label="Line"
              active={group === "line"}
              onClick={() => setGroup("line")}
            />
            <FilterChip
              label="Client"
              active={group === "client"}
              onClick={() => setGroup("client")}
            />
            <FilterChip
              label="Carrier"
              active={group === "carrier"}
              onClick={() => setGroup("carrier")}
            />
            <span className="mx-2 h-4 w-px bg-rule" />
            <Micro className="mr-1">Status:</Micro>
            <FilterChip
              label="All"
              active={status === "all"}
              onClick={() => setStatus("all")}
            />
            <FilterChip
              label="Bound"
              active={status === "bound"}
              onClick={() => setStatus("bound")}
            />
            <FilterChip
              label="In review"
              active={status === "review"}
              onClick={() => setStatus("review")}
            />
            <FilterChip
              label="Awaiting"
              active={status === "awaiting"}
              onClick={() => setStatus("awaiting")}
            />
          </div>

          {/* Per-group cards */}
          {groups.length === 0 ? (
            <Card pad="lg" className="text-center">
              <Body className="italic">No coverages match the filters.</Body>
            </Card>
          ) : (
            <div className="flex flex-col gap-3.5">
              {groups.map((g) => {
                const GroupIcon = group === "line" ? lineIcon(g.key) : ShieldCheck;
                return (
                <Card key={g.key} pad="none" className="overflow-hidden">
                  <header className="flex items-center justify-between border-b border-rule bg-surface-elev px-5 py-3">
                    <div className="flex items-center gap-3">
                      <div className="flex h-8 w-8 items-center justify-center rounded-md border border-rule bg-surface">
                        <GroupIcon size={15} className="text-ink-soft" />
                      </div>
                      <h2 className="text-[16px] font-semibold text-ink">{g.key}</h2>
                      <Chip variant="mute" size="sm">
                        {g.items.length} polic{g.items.length === 1 ? "y" : "ies"}
                      </Chip>
                    </div>
                    <span className="text-[15px] font-semibold tabular-nums text-ink">
                      {formatCurrency(g.total)}
                    </span>
                  </header>
                  <div>
                    {g.items.map((p, i) => (
                      <CoverageRow
                        key={p.submission_code}
                        entry={p}
                        first={i === 0}
                      />
                    ))}
                  </div>
                </Card>
                );
              })}
            </div>
          )}
        </div>
      </div>
    </>
  );
}

function CoverageRow({
  entry,
  first,
}: {
  entry: ClientBookEntry;
  first: boolean;
}) {
  const tone = tierStatus(entry.tier);
  const chipTone = portalToneToTone(tone.tone);
  const awaiting =
    entry.referral_state && /awaiting/i.test(entry.referral_state);

  return (
    <Link
      href={`/client/submissions/${entry.submission_code}`}
      className={cn(
        "grid grid-cols-[2fr_1.4fr_70px_90px_110px_130px_28px] items-center gap-3 px-5 py-3 transition hover:bg-surface-sunken/40",
        !first && "border-t border-rule",
      )}
    >
      <div>
        <div className="font-semibold text-ink">{entry.entity_name}</div>
        <Micro className="mt-0.5 block">{entry.coverage}</Micro>
      </div>
      <Caption>{entry.submission_code}</Caption>
      <div>
        <Micro className="block">Score</Micro>
        {entry.composite_score != null ? (
          <span className="font-bold tabular-nums text-info">
            {entry.composite_score.toFixed(0)}
          </span>
        ) : (
          <span className="text-ink-mute">—</span>
        )}
      </div>
      <div>
        <Micro className="block">Tier</Micro>
        <span className="font-semibold text-ink">
          {entry.tier != null ? `Tier ${entry.tier}` : "—"}
        </span>
      </div>
      <div className="text-right">
        <Micro className="block">Premium</Micro>
        <span className="font-semibold tabular-nums text-ink">
          {entry.recommended_premium != null
            ? formatCurrency(entry.recommended_premium)
            : "—"}
        </span>
      </div>
      <Chip variant={awaiting ? "spot" : chipTone} size="sm">
        {awaiting
          ? formatText(entry.referral_state ?? "", "capitalize")
          : tone.label}
      </Chip>
      <ChevronRight size={16} className="text-ink-mute" />
    </Link>
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

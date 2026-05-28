"use client";

import Link from "next/link";
import { useMemo, useState } from "react";
import { Search, AlertCircle, Briefcase, ChevronRight } from "lucide-react";
import { Topbar } from "@/components/chrome/topbar";
import { Card } from "@/components/ui/card";
import { Chip } from "@/components/ui/chip";
import { Eyebrow, NumDisplay, Body, Micro } from "@/components/ui/typography";
import { ScoreBar } from "@/components/ui/score-bar";
import { PageError, PageLoading, RoleGate } from "@/components/base/pageStates";
import { useRoleScopedFetch } from "@/lib/useRoleScopedFetch";
import { fetchOverview } from "@/lib/portalApi";
import { useAuthStore } from "@/store/authStore";
import { formatCurrency, formatText } from "@/lib/format";
import { tierStatus } from "@/lib/portalTone";
import { portalToneToTone } from "@/lib/design-tokens";
import { cn, fmtRelative } from "@/lib/utils";
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
  const [query, setQuery] = useState("");

  const grouped = useMemo(() => {
    const m = new Map<string, ClientBookEntry[]>();
    for (const c of data.clients) {
      if (
        query &&
        !c.entity_name.toLowerCase().includes(query.toLowerCase()) &&
        !c.coverage.toLowerCase().includes(query.toLowerCase())
      ) {
        continue;
      }
      const list = m.get(c.entity_name) ?? [];
      list.push(c);
      m.set(c.entity_name, list);
    }
    return [...m.entries()].sort((a, b) => a[0].localeCompare(b[0]));
  }, [data.clients, query]);

  const totalPolicies = data.clients.length;
  const totalPremium = data.clients.reduce(
    (sum, c) => sum + (c.recommended_premium ?? 0),
    0,
  );
  const awaiting = data.clients.filter(
    (c) => c.referral_state && /awaiting/i.test(c.referral_state),
  ).length;

  return (
    <>
      <Topbar
        crumbs={["Broker Portal", "Book of Clients"]}
        entity={data.broker.name}
      />
      <div className="flex-1 overflow-y-auto px-9 py-7">
        <div className="mx-auto grid max-w-[1400px] gap-6">
          <header className="flex items-end justify-between gap-6">
            <div>
              <Eyebrow>Broker</Eyebrow>
              <h1 className="mt-1 font-display text-[36px] font-semibold leading-none tracking-tight text-ink">
                {data.broker.name}
              </h1>
              <Body className="mt-2">
                {grouped.length} client{grouped.length === 1 ? "" : "s"} ·{" "}
                {totalPolicies} placement{totalPolicies === 1 ? "" : "s"}
              </Body>
            </div>
            <div className="flex items-center gap-2 rounded-btn border border-rule-strong bg-surface px-3">
              <Search size={15} className="text-ink-mute" />
              <input
                type="search"
                placeholder="Filter clients or coverages…"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                className="h-10 w-72 border-0 bg-transparent text-[13.5px] text-ink placeholder:text-ink-mute focus:outline-none"
              />
            </div>
          </header>

          <div className="grid gap-4 sm:grid-cols-4">
            <SummaryTile label="Clients">{grouped.length}</SummaryTile>
            <SummaryTile label="Policies">{totalPolicies}</SummaryTile>
            <SummaryTile label="Premium under management" emphasis>
              {formatCurrency(totalPremium)}
            </SummaryTile>
            <SummaryTile
              label="Open queries"
              emphasis={data.open_queries_count > 0}
              variant={data.open_queries_count > 0 ? "spot" : "default"}
            >
              {data.open_queries_count}
            </SummaryTile>
          </div>

          {data.open_queries_count > 0 && (
            <Link
              href="/broker/communications"
              className="flex items-center gap-3 rounded-card border border-spot bg-spot-soft px-4 py-3 text-[13.5px] font-medium text-spot-deep transition hover:bg-spot hover:text-white dark:text-spot"
            >
              <AlertCircle size={16} />
              {data.open_queries_count} open quer{data.open_queries_count === 1 ? "y" : "ies"} awaiting reply
              <ChevronRight size={14} className="ml-auto" />
            </Link>
          )}

          {/* Client cards */}
          {grouped.length === 0 ? (
            <Card pad="lg" className="text-center">
              <Body className="italic">
                {query
                  ? `No clients or coverages match "${query}".`
                  : "Your book is empty."}
              </Body>
            </Card>
          ) : (
            <div className="space-y-5">
              {grouped.map(([clientName, coverages]) => (
                <ClientBlock
                  key={clientName}
                  clientName={clientName}
                  coverages={coverages}
                />
              ))}
            </div>
          )}
        </div>
      </div>
    </>
  );
}

function ClientBlock({
  clientName,
  coverages,
}: {
  clientName: string;
  coverages: ClientBookEntry[];
}) {
  const totalPremium = coverages.reduce(
    (sum, c) => sum + (c.recommended_premium ?? 0),
    0,
  );
  const awaiting = coverages.filter(
    (c) => c.referral_state && /awaiting/i.test(c.referral_state),
  ).length;

  return (
    <Card pad="md" className="overflow-hidden p-0">
      <header className="flex items-baseline justify-between gap-3 border-b border-rule px-5 py-3.5">
        <div className="flex items-center gap-3">
          <Briefcase size={15} className="text-ink-mute" />
          <h2 className="text-[16px] font-semibold text-ink">{clientName}</h2>
          <Chip variant="mute" size="sm">
            {coverages.length} polic{coverages.length === 1 ? "y" : "ies"}
          </Chip>
          {awaiting > 0 && (
            <Chip variant="spot" size="sm">
              <AlertCircle size={10} />
              {awaiting} awaiting
            </Chip>
          )}
        </div>
        <span className="text-[13px] font-semibold tabular-nums text-ink">
          {formatCurrency(totalPremium)}
        </span>
      </header>
      <table className="w-full table-fixed text-[13px]">
        <thead>
          <tr className="border-b border-rule bg-surface-sunken/60 text-left">
            <ColHead width="w-[26%]">Coverage</ColHead>
            <ColHead width="w-[16%]">Score</ColHead>
            <ColHead width="w-[18%]">Status</ColHead>
            <ColHead width="w-[14%]">Premium</ColHead>
            <ColHead width="w-[18%]">Updated</ColHead>
            <ColHead width="w-[8%]">{null}</ColHead>
          </tr>
        </thead>
        <tbody>
          {coverages.map((c) => (
            <CoverageRow key={c.submission_code} entry={c} />
          ))}
        </tbody>
      </table>
    </Card>
  );
}

function CoverageRow({ entry }: { entry: ClientBookEntry }) {
  const tone = tierStatus(entry.tier);
  const chipTone = portalToneToTone(tone.tone);
  const awaiting =
    entry.referral_state && /awaiting/i.test(entry.referral_state);

  return (
    <tr className="border-b border-rule last:border-0 hover:bg-surface-sunken/40">
      <td className="px-5 py-3">
        <Link
          href={`/client/submissions/${entry.submission_code}`}
          className="block"
        >
          <p className="font-medium text-ink">{entry.coverage}</p>
          <Micro className="mt-0.5 block font-mono">
            {entry.submission_code}
          </Micro>
        </Link>
      </td>
      <td className="px-5 py-3">
        {entry.composite_score != null ? (
          <div className="space-y-1">
            <span className="font-semibold tabular-nums text-ink">
              {entry.composite_score.toFixed(0)}
            </span>
            <ScoreBar
              value={entry.composite_score}
              max={1000}
              showValue={false}
              thresholds={[
                { at: 400, tone: "neg" },
                { at: 650, tone: "warn" },
                { at: 800, tone: "info" },
                { at: 1000, tone: "pos" },
              ]}
            />
          </div>
        ) : (
          <span className="text-ink-mute">—</span>
        )}
      </td>
      <td className="px-5 py-3">
        <Chip variant={awaiting ? "spot" : chipTone} size="sm">
          {awaiting
            ? formatText(entry.referral_state, "capitalize")
            : tone.label}
        </Chip>
      </td>
      <td className="px-5 py-3">
        <span className="font-semibold tabular-nums text-ink">
          {entry.recommended_premium != null
            ? formatCurrency(entry.recommended_premium)
            : "—"}
        </span>
      </td>
      <td className="px-5 py-3 text-ink-soft">
        {fmtRelative(entry.updated_at)}
      </td>
      <td className="px-5 py-3 text-right">
        <Link
          href={`/client/submissions/${entry.submission_code}`}
          className="inline-flex items-center text-ink-mute hover:text-ink"
        >
          <ChevronRight size={16} />
        </Link>
      </td>
    </tr>
  );
}

function SummaryTile({
  label,
  children,
  emphasis,
  variant = "default",
}: {
  label: string;
  children: React.ReactNode;
  emphasis?: boolean;
  variant?: "default" | "info" | "spot";
}) {
  return (
    <Card pad="md" variant={emphasis ? variant : "default"}>
      <Micro
        className={cn(
          "block",
          variant === "spot" && "text-spot-deep dark:text-spot",
        )}
      >
        {label}
      </Micro>
      <div className="mt-2">
        <NumDisplay size={emphasis ? "lg" : "md"}>{children}</NumDisplay>
      </div>
    </Card>
  );
}

function ColHead({
  width,
  children,
}: {
  width: string;
  children: React.ReactNode;
}) {
  return (
    <th
      className={`px-5 py-2.5 text-[11px] font-semibold uppercase tracking-[0.08em] text-ink-mute ${width}`}
    >
      {children}
    </th>
  );
}

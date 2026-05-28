"use client";

import Link from "next/link";
import { useMemo, useState } from "react";
import { ChevronRight, Search } from "lucide-react";
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
import { fmtRelative } from "@/lib/utils";
import type { ClientBookEntry, OverviewResponse } from "@/types/portal";

type SortField = "score" | "premium" | "client" | "coverage" | "updated";

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

function CoveragesBody({
  data,
}: {
  data: Extract<OverviewResponse, { role: "BROKER" }>;
}) {
  const [query, setQuery] = useState("");
  const [sort, setSort] = useState<SortField>("premium");
  const [coverageFilter, setCoverageFilter] = useState<string>("");

  const lineOptions = useMemo(
    () => Array.from(new Set(data.clients.map((c) => c.coverage))).sort(),
    [data.clients],
  );

  const filtered = useMemo(() => {
    return data.clients.filter((c) => {
      if (coverageFilter && c.coverage !== coverageFilter) return false;
      if (!query) return true;
      const q = query.toLowerCase();
      return (
        c.entity_name.toLowerCase().includes(q) ||
        c.coverage.toLowerCase().includes(q) ||
        c.submission_code.toLowerCase().includes(q)
      );
    });
  }, [data.clients, query, coverageFilter]);

  const sorted = useMemo(() => {
    const s = [...filtered];
    switch (sort) {
      case "score":
        s.sort((a, b) => (b.composite_score ?? -1) - (a.composite_score ?? -1));
        break;
      case "premium":
        s.sort(
          (a, b) => (b.recommended_premium ?? 0) - (a.recommended_premium ?? 0),
        );
        break;
      case "client":
        s.sort((a, b) => a.entity_name.localeCompare(b.entity_name));
        break;
      case "coverage":
        s.sort((a, b) => a.coverage.localeCompare(b.coverage));
        break;
      case "updated":
        s.sort((a, b) =>
          (b.updated_at ?? "").localeCompare(a.updated_at ?? ""),
        );
        break;
    }
    return s;
  }, [filtered, sort]);

  const totalPremium = sorted.reduce(
    (sum, c) => sum + (c.recommended_premium ?? 0),
    0,
  );

  return (
    <>
      <Topbar
        crumbs={["Broker Portal", "Coverages"]}
        entity={data.broker.name}
      />
      <div className="flex-1 overflow-y-auto px-9 py-7">
        <div className="mx-auto grid max-w-[1400px] gap-6">
          <header className="flex items-end justify-between gap-6">
            <div>
              <Eyebrow>Book</Eyebrow>
              <h1 className="mt-1 font-display text-[32px] font-semibold leading-none tracking-tight text-ink">
                Coverages
              </h1>
              <Body className="mt-2">
                Every policy across the book — sortable, filterable. Click a
                row for the submission detail.
              </Body>
            </div>
            <div className="flex items-center gap-2">
              <div className="flex items-center gap-2 rounded-btn border border-rule-strong bg-surface px-3">
                <Search size={15} className="text-ink-mute" />
                <input
                  type="search"
                  placeholder="Client, coverage, or code…"
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  className="h-10 w-64 border-0 bg-transparent text-[13.5px] text-ink placeholder:text-ink-mute focus:outline-none"
                />
              </div>
              <select
                value={coverageFilter}
                onChange={(e) => setCoverageFilter(e.target.value)}
                className="h-10 rounded-btn border border-rule-strong bg-surface px-3 text-[13px] font-medium text-ink focus:border-info focus:outline-none"
              >
                <option value="">All lines</option>
                {lineOptions.map((l) => (
                  <option key={l} value={l}>
                    {l}
                  </option>
                ))}
              </select>
            </div>
          </header>

          <div className="grid gap-4 sm:grid-cols-3">
            <Stat label="Policies">{sorted.length}</Stat>
            <Stat label="Premium" emphasis>
              {formatCurrency(totalPremium)}
            </Stat>
            <Stat label="Lines">{lineOptions.length}</Stat>
          </div>

          <Card pad="md" className="overflow-hidden p-0">
            <table className="w-full table-fixed text-[13px]">
              <thead>
                <tr className="border-b border-rule bg-surface-sunken text-left">
                  <ColHead
                    width="w-[22%]"
                    sort="client"
                    activeSort={sort}
                    onSort={setSort}
                  >
                    Client
                  </ColHead>
                  <ColHead
                    width="w-[18%]"
                    sort="coverage"
                    activeSort={sort}
                    onSort={setSort}
                  >
                    Coverage
                  </ColHead>
                  <ColHead
                    width="w-[14%]"
                    sort="score"
                    activeSort={sort}
                    onSort={setSort}
                  >
                    Score
                  </ColHead>
                  <ColHead width="w-[14%]">Status</ColHead>
                  <ColHead
                    width="w-[14%]"
                    sort="premium"
                    activeSort={sort}
                    onSort={setSort}
                  >
                    Premium
                  </ColHead>
                  <ColHead
                    width="w-[14%]"
                    sort="updated"
                    activeSort={sort}
                    onSort={setSort}
                  >
                    Updated
                  </ColHead>
                  <ColHead width="w-[4%]">{null}</ColHead>
                </tr>
              </thead>
              <tbody>
                {sorted.map((c) => (
                  <Row key={c.submission_code} entry={c} />
                ))}
              </tbody>
            </table>
            {sorted.length === 0 && (
              <div className="px-5 py-8 text-center">
                <Body className="italic">No coverages match the filters.</Body>
              </div>
            )}
          </Card>
        </div>
      </div>
    </>
  );
}

function Row({ entry }: { entry: ClientBookEntry }) {
  const tone = tierStatus(entry.tier);
  const chipTone = portalToneToTone(tone.tone);
  const awaiting =
    entry.referral_state && /awaiting/i.test(entry.referral_state);

  return (
    <tr className="border-b border-rule last:border-0 hover:bg-surface-sunken/40">
      <td className="px-5 py-3">
        <p className="font-medium text-ink">{entry.entity_name}</p>
        <Micro className="mt-0.5 block font-mono">{entry.submission_code}</Micro>
      </td>
      <td className="px-5 py-3 text-ink">{entry.coverage}</td>
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

function ColHead({
  width,
  sort,
  activeSort,
  onSort,
  children,
}: {
  width: string;
  sort?: SortField;
  activeSort?: SortField;
  onSort?: (s: SortField) => void;
  children: React.ReactNode;
}) {
  const isActive = sort && sort === activeSort;
  return (
    <th
      className={`px-5 py-2.5 text-[11px] font-semibold uppercase tracking-[0.08em] ${width} ${
        isActive ? "text-ink" : "text-ink-mute"
      }`}
    >
      {sort && onSort ? (
        <button
          type="button"
          onClick={() => onSort(sort)}
          className="cursor-pointer hover:text-ink"
        >
          {children}
          {isActive && <span className="ml-1">↓</span>}
        </button>
      ) : (
        children
      )}
    </th>
  );
}

function Stat({
  label,
  emphasis,
  children,
}: {
  label: string;
  emphasis?: boolean;
  children: React.ReactNode;
}) {
  return (
    <Card pad="md" variant={emphasis ? "info" : "default"}>
      <Micro
        className={
          emphasis ? "text-info-deep dark:text-info" : ""
        }
      >
        {label}
      </Micro>
      <div className="mt-2">
        <NumDisplay size={emphasis ? "lg" : "md"}>{children}</NumDisplay>
      </div>
    </Card>
  );
}

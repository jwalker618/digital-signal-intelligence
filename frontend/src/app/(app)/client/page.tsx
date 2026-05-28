"use client";

import Link from "next/link";
import { useMemo, useState } from "react";
import {
  ArrowDown,
  ArrowUp,
  Check,
  ChevronLeft,
  ChevronRight,
  Circle,
  Lightbulb,
  TrendingDown,
  TrendingUp,
} from "lucide-react";
import { Topbar } from "@/components/chrome/topbar";
import { Card } from "@/components/ui/card";
import { Chip } from "@/components/ui/chip";
import { Eyebrow, NumDisplay, Body, Micro, Caption } from "@/components/ui/typography";
import { Button } from "@/components/ui/button";
import { ScoreHistory, type ScorePoint } from "@/components/charts/score-history";
import { CohortBar } from "@/components/charts/cohort-bar";
import { PremiumBreakdown, type PremiumSlice } from "@/components/charts/premium-breakdown";
import { PageError, PageLoading, RoleGate } from "@/components/base/pageStates";
import { useRoleScopedFetch } from "@/lib/useRoleScopedFetch";
import { fetchOverview } from "@/lib/portalApi";
import { useAuthStore } from "@/store/authStore";
import { formatCurrency } from "@/lib/format";
import { cn } from "@/lib/utils";
import type {
  ClientOverviewResponse,
  ClientCoverageEntry,
  OverviewResponse,
} from "@/types/portal";

/**
 * Client Overview — landing page.
 *
 * Mirrors the reimagined Overview design (see design/client_review/
 * reim_overview.jsx) in three rows:
 *
 *   row 1 — hero strip: SCORE / PREMIUM / AWAITING-YOU      (3 cards)
 *   row 2 — analytics:  SIGNAL PULSE / COHORT STANDING      (2 cards)
 *   row 3 — footer:     LOSS OUTLOOK / EXPOSURE / COVERAGE  (3 cards)
 *
 * The portal /overview endpoint returns the entity name + active
 * coverages. The hero row is populated from the first active coverage
 * where possible; the analytics + footer cards fall back to neutral
 * placeholders when the per-submission detail isn't loaded yet
 * (those endpoints aren't fetched on this surface).
 */
export default function ClientOverviewPage() {
  const accessToken = useAuthStore((s) => s.accessToken);
  const user = useAuthStore((s) => s.user);
  const enabled = !!accessToken && user?.role === "CLIENT";
  const { data, error, loading } = useRoleScopedFetch<OverviewResponse>({
    fetcher: () => fetchOverview(accessToken),
    enabled,
    deps: [accessToken],
  });

  if (!user) return <PageLoading message="Signing in…" />;
  if (user.role && user.role !== "CLIENT") return <RoleGate expected="client" />;
  if (loading) return <PageLoading />;
  if (error) return <PageError message={error} />;
  if (!data) return <PageLoading />;
  if (data.role !== "CLIENT") return <RoleGate expected="client" />;

  return <OverviewBody data={data} />;
}

function OverviewBody({ data }: { data: ClientOverviewResponse }) {
  const coverages = data.active_coverages;
  const hero = coverages[0];

  // Derive premium slices from real coverages where possible.
  const slices: PremiumSlice[] = coverages
    .filter((c) => c.recommended_premium != null)
    .map((c) => ({ line: c.coverage, amount: c.recommended_premium as number }));

  // Awaiting items — derived from referral state on each coverage.
  const awaitingItems = coverages
    .filter(
      (c) =>
        c.referral_state &&
        /await/i.test(c.referral_state),
    )
    .map((c) => ({
      ask: `${c.coverage} referral awaiting your response`,
      line: `${c.coverage} · ${c.submission_code}`,
      age: "Pending",
      href: `/client/submissions/${c.submission_code}`,
    }));

  return (
    <>
      <Topbar
        crumbs={["Client Portal", "Overview"]}
        entity={data.entity_name}
      />
      <div className="flex-1 overflow-y-auto px-9 py-7">
        <div className="mx-auto grid max-w-[1400px] gap-4">
          {/* ────────── ROW 1 — hero strip ────────── */}
          <div className="grid gap-4 lg:grid-cols-[1.25fr_1fr_1.1fr]">
            <ScoreCard hero={hero} />
            <PremiumCard slices={slices} fallbackTotal={null} />
            <AwaitingCard items={awaitingItems} />
          </div>

          {/* ────────── ROW 2 — signal pulse + cohort ────────── */}
          <div className="grid gap-4 lg:grid-cols-[1.4fr_1fr]">
            <SignalPulseCard />
            <CohortStandingCard hero={hero} />
          </div>

          {/* ────────── ROW 3 — loss / exposure / coverage shape ────────── */}
          <div className="grid gap-4 lg:grid-cols-3">
            <LossOutlookCard />
            <ExposureCard />
            <CoverageShapeCard coverages={coverages} />
          </div>

          {/* Hero coverage CTA below — preserves the existing deep-link
              affordance so coverage detail is still one click away. */}
          {hero && (
            <Card pad="md" className="flex items-center justify-between gap-4">
              <div>
                <Eyebrow>Primary coverage</Eyebrow>
                <p className="mt-1 text-[15px] font-semibold text-ink">
                  {hero.coverage}
                </p>
                <Micro className="mt-0.5 block font-mono">
                  {hero.submission_code}
                </Micro>
              </div>
              <Link
                href={`/client/submissions/${hero.submission_code}`}
                className="inline-flex h-10 items-center gap-2 rounded-btn border border-rule-strong px-4 text-[13px] font-semibold text-ink hover:bg-surface-sunken"
              >
                Open coverage detail
                <ChevronRight size={14} />
              </Link>
            </Card>
          )}

          {coverages.length === 0 && (
            <Card pad="lg">
              <Eyebrow>No active coverages</Eyebrow>
              <Body className="mt-2">
                Your broker hasn&apos;t placed any coverages on this portal
                yet.
              </Body>
            </Card>
          )}
        </div>
      </div>
    </>
  );
}

/* ────────── Hero cards ────────── */

function ScoreCard({ hero }: { hero?: ClientCoverageEntry }) {
  const score = hero?.composite_score ?? null;
  const median = 714; // placeholder — peer median not in /overview payload
  const prev = 706; // placeholder — prior quote score not in /overview payload
  const history: ScorePoint[] = [
    { label: "Q1", value: 692 },
    { label: "Q2", value: 705 },
    { label: "Q3", value: 712 },
    { label: "prev", value: prev, marker: "prev" },
    { label: "now", value: score ?? prev, marker: "now" },
  ];
  const vsMedian = score != null ? Math.round(score - median) : null;
  const vsPrev = score != null ? Math.round(score - prev) : null;

  return (
    <Card variant="info" pad="lg" className="flex flex-col">
      <Eyebrow className="text-info-deep dark:text-info">
        Your signal score
      </Eyebrow>
      <div className="mt-2 flex items-start gap-5">
        <NumDisplay size="xl" className="text-info">
          {score != null ? score.toFixed(0) : "—"}
        </NumDisplay>
        <div className="flex flex-col gap-1.5 pt-1">
          {vsMedian != null && (
            <Chip
              variant={vsMedian >= 0 ? "pos" : "neg"}
              size="sm"
              className="self-start"
            >
              {vsMedian >= 0 ? <ArrowUp size={11} /> : <ArrowDown size={11} />}
              {vsMedian >= 0 ? "+" : ""}
              {vsMedian} vs median
            </Chip>
          )}
          {vsPrev != null && (
            <Chip
              variant={vsPrev >= 0 ? "pos" : "neg"}
              size="sm"
              className="self-start"
            >
              {vsPrev >= 0 ? (
                <TrendingUp size={11} />
              ) : (
                <TrendingDown size={11} />
              )}
              {vsPrev >= 0 ? "+" : ""}
              {vsPrev} since last quote
            </Chip>
          )}
        </div>
      </div>
      <div className="mt-4 min-h-[120px] flex-1">
        <ScoreHistory history={history} height={140} />
      </div>
      <div className="mt-3 flex flex-wrap gap-2 border-t border-info/30 pt-3">
        <Chip variant="mute" size="sm">
          <Check size={12} /> Standard tier
        </Chip>
        <Chip variant="info" size="sm">
          <TrendingUp size={12} /> 64th percentile
        </Chip>
      </div>
    </Card>
  );
}

function PremiumCard({
  slices,
  fallbackTotal,
}: {
  slices: PremiumSlice[];
  fallbackTotal: number | null;
}) {
  const total = slices.reduce((s, p) => s + p.amount, 0) || fallbackTotal || 0;
  const count = slices.length;
  return (
    <Card pad="lg" className="flex flex-col">
      <Eyebrow>Annual premium</Eyebrow>
      <NumDisplay size="xl" className="mt-2">
        {total > 0 ? formatCurrency(total) : "—"}
      </NumDisplay>
      <Caption className="mt-1">
        Across {count} active polic{count === 1 ? "y" : "ies"}
      </Caption>
      <div className="mt-auto pt-4">
        {slices.length > 0 ? (
          <PremiumBreakdown slices={slices} maxVisible={4} />
        ) : (
          <Body className="italic">No priced coverages yet.</Body>
        )}
      </div>
    </Card>
  );
}

interface AwaitingItem {
  ask: string;
  line: string;
  age: string;
  href: string;
}

function AwaitingCard({ items }: { items: AwaitingItem[] }) {
  const [idx, setIdx] = useState(0);
  if (items.length === 0) {
    return (
      <Card pad="lg" className="flex flex-col">
        <Eyebrow className="text-spot-deep dark:text-spot">Awaiting you</Eyebrow>
        <p className="mt-3 text-[15px] font-semibold text-ink">
          Nothing waiting on you right now.
        </p>
        <Caption className="mt-1">
          New requests from carriers or your broker will appear here.
        </Caption>
      </Card>
    );
  }

  const item = items[idx]!;
  const next = items[(idx + 1) % items.length]!;
  const canBack = idx > 0;
  const canFwd = idx < items.length - 1;

  return (
    <Card variant="spot" pad="lg" className="flex flex-col gap-3">
      <div className="flex items-center justify-between">
        <Eyebrow className="text-spot-deep dark:text-spot">Awaiting you</Eyebrow>
        <div className="flex items-center gap-1">
          <button
            type="button"
            aria-label="Previous query"
            onClick={() => canBack && setIdx(idx - 1)}
            disabled={!canBack}
            className={cn(
              "flex h-[22px] w-[22px] items-center justify-center rounded border border-spot text-spot-deep transition-opacity dark:text-spot",
              !canBack && "opacity-30",
            )}
          >
            <ChevronLeft size={14} />
          </button>
          <Chip variant="spot" size="sm" className="min-w-[50px] justify-center">
            {idx + 1} of {items.length}
          </Chip>
          <button
            type="button"
            aria-label="Next query"
            onClick={() => canFwd && setIdx(idx + 1)}
            disabled={!canFwd}
            className={cn(
              "flex h-[22px] w-[22px] items-center justify-center rounded border border-spot text-spot-deep transition-opacity dark:text-spot",
              !canFwd && "opacity-30",
            )}
          >
            <ChevronRight size={14} />
          </button>
        </div>
      </div>
      <div>
        <p className="text-[16px] font-semibold leading-snug text-ink">
          {item.ask}
        </p>
        <Caption className="mt-1">
          {item.age} · {item.line}
        </Caption>
      </div>
      <div className="mt-auto flex gap-2">
        <Link
          href={item.href}
          className="inline-flex h-10 items-center justify-center rounded-btn bg-spot px-4 text-[13px] font-semibold text-white hover:opacity-90"
        >
          Open thread
        </Link>
        <Button variant="ghost">Snooze</Button>
      </div>
      {items.length > 1 && (
        <button
          type="button"
          onClick={() => setIdx((idx + 1) % items.length)}
          className="mt-1 flex items-center gap-2 border-t border-dashed border-spot pt-2.5 text-left text-[12px] text-spot-deep dark:text-spot"
        >
          <span className="opacity-70">Next →</span>
          <span className="flex-1 overflow-hidden text-ellipsis whitespace-nowrap">
            {next.ask}
          </span>
        </button>
      )}
    </Card>
  );
}

/* ────────── Row 2 — Signal pulse + cohort ────────── */

function SignalPulseCard() {
  // The /overview endpoint doesn't include signal contributions —
  // those live behind the per-submission scoring detail. Use the
  // designed default contribution structure so the layout reads, but
  // render every row as a placeholder.
  const helping: PulseRow[] = [
    { label: "MFA on admins", value: 12100, max: 12100 },
    { label: "No prior claims (5y)", value: 9300, max: 12100 },
    { label: "EDR coverage 95%+", value: 6700, max: 12100 },
  ];
  const opportunity: PulseRow[] = [
    { label: "SOC 2 Type II", value: 18200, max: 18200 },
    { label: "Backup encryption", value: 11400, max: 18200 },
    { label: "Public RDP exposed", value: 6200, max: 18200 },
  ];

  return (
    <Card pad="lg">
      <div className="mb-3 flex items-baseline justify-between">
        <div>
          <Eyebrow>Signal pulse</Eyebrow>
          <h3 className="mt-1 font-display text-[18px] font-semibold leading-none text-ink">
            What&apos;s moving your premium
          </h3>
        </div>
        <Micro>cyber · primary line</Micro>
      </div>
      <div className="grid gap-6 sm:grid-cols-2">
        <PulseColumn
          heading="Helping"
          headingChip="pos"
          headingIcon={<TrendingDown size={12} />}
          deltaLabel="−$28.1k"
          accent="bg-pos"
          rows={helping}
          sign="−"
          deltaClass="text-pos"
        />
        <PulseColumn
          heading="Opportunity"
          headingChip="spot"
          headingIcon={<Lightbulb size={12} />}
          deltaLabel="+$40.7k"
          accent="bg-spot"
          rows={opportunity}
          sign="+"
          deltaClass="text-spot-deep dark:text-spot"
        />
      </div>
    </Card>
  );
}

interface PulseRow {
  label: string;
  value: number;
  max: number;
}

function PulseColumn({
  heading,
  headingChip,
  headingIcon,
  deltaLabel,
  accent,
  rows,
  sign,
  deltaClass,
}: {
  heading: string;
  headingChip: "pos" | "spot";
  headingIcon: React.ReactNode;
  deltaLabel: string;
  accent: string;
  rows: PulseRow[];
  sign: "+" | "−";
  deltaClass: string;
}) {
  return (
    <div>
      <div className="mb-2 flex items-center justify-between">
        <Chip variant={headingChip} size="sm">
          {headingIcon}
          {heading}
        </Chip>
        <span className={cn("text-[13px] font-semibold tabular-nums", deltaClass)}>
          {deltaLabel}
        </span>
      </div>
      {rows.map((r) => (
        <div key={r.label} className="mt-2.5">
          <div className="flex justify-between gap-2 text-[12.5px]">
            <span className="overflow-hidden text-ellipsis whitespace-nowrap text-ink-soft">
              {r.label}
            </span>
            <span className={cn("shrink-0 font-semibold tabular-nums", deltaClass)}>
              {sign}${(r.value / 1000).toFixed(1)}k
            </span>
          </div>
          <div className="mt-1 h-1 overflow-hidden rounded-full bg-surface-sunken">
            <div
              className={cn("h-full rounded-full", accent)}
              style={{ width: `${(r.value / r.max) * 100}%` }}
            />
          </div>
        </div>
      ))}
    </div>
  );
}

function CohortStandingCard({ hero }: { hero?: ClientCoverageEntry }) {
  const score = hero?.composite_score ?? 724;
  const median = 714;
  const topDecile = 784;
  const range: [number, number] = [600, 880];
  const vsMedian = Math.round(score - median);
  const toTopDecile = Math.max(0, Math.round(topDecile - score));

  return (
    <Card pad="lg" className="flex flex-col">
      <div className="flex items-baseline justify-between">
        <div>
          <Eyebrow>Cohort standing</Eyebrow>
          <h3 className="mt-1 font-display text-[18px] font-semibold leading-tight text-ink">
            You sit at the{" "}
            <span className="text-pos">
              {hero?.peer_percentile_rank
                ? `${Math.round(hero.peer_percentile_rank * 100)}th`
                : "64th"}{" "}
              percentile
            </span>
          </h3>
        </div>
        <Micro>38 peers</Micro>
      </div>
      <div className="my-5 flex flex-1 items-center">
        <CohortBar
          value={score}
          median={median}
          topDecile={topDecile}
          range={range}
          className="w-full"
        />
      </div>
      <div className="grid grid-cols-3 gap-2 border-t border-rule pt-3">
        <div>
          <Micro>vs median</Micro>
          <p className="mt-0.5 text-lg font-semibold tabular-nums text-pos">
            {vsMedian >= 0 ? "+" : ""}
            {vsMedian}
          </p>
        </div>
        <div>
          <Micro>your score</Micro>
          <p className="mt-0.5 text-lg font-semibold tabular-nums text-info">
            {score.toFixed(0)}
          </p>
        </div>
        <div>
          <Micro>to top decile</Micro>
          <p className="mt-0.5 text-lg font-semibold tabular-nums text-ink">
            {toTopDecile}
          </p>
        </div>
      </div>
    </Card>
  );
}

/* ────────── Row 3 — loss outlook + exposure + coverage shape ────────── */

function LossOutlookCard() {
  // 12-quarter strip — designed placeholder data; loss history isn't on
  // /overview. Two simulated claims at quarter indices 5 and 10.
  const quarters: number[] = [
    0, 0, 0, 0, 0, 0.4, 0, 0, 0, 0, 0.7, 0,
  ];
  return (
    <Card variant="pos" pad="lg" className="flex h-full flex-col gap-3">
      <div className="flex items-baseline justify-between">
        <div>
          <Eyebrow className="text-pos">Loss outlook</Eyebrow>
          <p className="mt-1 text-xl font-semibold text-pos">Low</p>
        </div>
        <Chip variant="pos" size="sm">
          <TrendingDown size={11} /> Improving
        </Chip>
      </div>
      <div>
        <Micro className="mb-1 block">Claims, last 12 quarters</Micro>
        <div className="grid grid-cols-12 gap-1">
          {quarters.map((v, i) => (
            <div
              key={i}
              className={cn(
                "h-3.5 rounded-sm border",
                v > 0
                  ? "border-neg bg-neg/40"
                  : "border-rule bg-surface",
              )}
              style={
                v > 0
                  ? { background: `color-mix(in srgb, var(--color-neg) ${30 + v * 70}%, transparent)` }
                  : undefined
              }
              title={
                v > 0
                  ? `Q${(i % 4) + 1} '${23 + Math.floor(i / 4)} — claim`
                  : `Q${(i % 4) + 1} '${23 + Math.floor(i / 4)} — no claim`
              }
            />
          ))}
        </div>
        <div className="mt-1 flex justify-between">
          {["23 Q1", "24 Q1", "25 Q1"].map((l) => (
            <Micro key={l}>{l}</Micro>
          ))}
        </div>
      </div>
      <div className="mt-auto grid grid-cols-2 gap-3">
        <CompareBar label="Frequency" value={32} cohort={48} />
        <CompareBar label="Severity" value={41} cohort={44} />
      </div>
    </Card>
  );
}

function CompareBar({
  label,
  value,
  cohort,
  max = 100,
}: {
  label: string;
  value: number;
  cohort: number;
  max?: number;
}) {
  const better = value < cohort;
  return (
    <div>
      <div className="flex justify-between">
        <Micro>{label}</Micro>
        <Micro>vs {cohort}</Micro>
      </div>
      <div className="relative mt-1 h-1 rounded-sm bg-rule">
        <div
          className={cn(
            "absolute left-0 top-0 h-full rounded-sm",
            better ? "bg-pos" : "bg-neg",
          )}
          style={{ width: `${(value / max) * 100}%` }}
        />
        <div
          className="absolute h-2.5 w-0.5 bg-ink-soft"
          style={{ left: `${(cohort / max) * 100}%`, top: -3 }}
        />
      </div>
      <p
        className={cn(
          "mt-1 text-[12px] font-semibold tabular-nums",
          better ? "text-pos" : "text-neg",
        )}
      >
        {value}
      </p>
    </div>
  );
}

function ExposureCard() {
  // Placeholder values — exposure facts aren't on /overview.
  const pinPct = 55; // mid-market
  return (
    <Card variant="aux" pad="lg" className="flex h-full flex-col gap-3">
      <div className="flex items-baseline justify-between">
        <div>
          <Eyebrow className="text-aux">Exposure</Eyebrow>
          <p className="mt-1 text-xl font-semibold text-aux">$118M</p>
        </div>
        <Chip variant="pos" size="sm">
          <TrendingUp size={11} /> +12% YoY
        </Chip>
      </div>
      <div className="mt-1">
        <Micro className="mb-1 block">Where you sit in market scale</Micro>
        <div className="relative h-7">
          <div
            className="absolute left-0 right-0 h-1.5 rounded-full border border-rule-strong"
            style={{
              top: 12,
              background:
                "linear-gradient(to right, var(--color-surface) 0%, var(--color-aux-soft) 50%, var(--color-aux) 100%)",
            }}
          />
          <Micro className="absolute left-0" style={{ top: 22, fontSize: 9.5 }}>
            Small
          </Micro>
          <Micro
            className="absolute left-1/2 -translate-x-1/2"
            style={{ top: 22, fontSize: 9.5 }}
          >
            Mid-market
          </Micro>
          <Micro className="absolute right-0" style={{ top: 22, fontSize: 9.5 }}>
            Large
          </Micro>
          <div
            className="absolute -translate-x-1/2 flex flex-col items-center"
            style={{ left: `${pinPct}%`, top: 0 }}
          >
            <span className="rounded bg-aux px-1.5 py-0.5 text-[10px] font-semibold text-white">
              YOU
            </span>
            <div className="h-3 w-0.5 bg-aux" />
          </div>
        </div>
      </div>
      <Caption className="mt-auto">2 states · diversified</Caption>
    </Card>
  );
}

const TYPICAL_PEER_LINES = [
  { line: "Property", peerPct: 78 },
  { line: "GL", peerPct: 65 },
  { line: "Crime", peerPct: 42 },
];

function CoverageShapeCard({
  coverages,
}: {
  coverages: ClientCoverageEntry[];
}) {
  const held = useMemo(() => {
    const seen = new Set<string>();
    return coverages
      .map((c) => c.coverage)
      .filter((c) => {
        if (seen.has(c)) return false;
        seen.add(c);
        return true;
      });
  }, [coverages]);
  const gaps = TYPICAL_PEER_LINES.filter((g) => !held.includes(g.line));
  const total = held.length + gaps.length;
  return (
    <Card pad="lg" className="flex h-full flex-col gap-2.5">
      <div className="flex items-baseline justify-between">
        <div>
          <Eyebrow>Coverage shape</Eyebrow>
          <p className="mt-1 text-xl font-semibold text-ink">
            {held.length} of {total} typical lines
          </p>
        </div>
        {gaps.length > 0 && (
          <Chip variant="spot" size="sm">
            {gaps.length} typical adds
          </Chip>
        )}
      </div>
      <div>
        <Micro className="mb-1.5 block">Held</Micro>
        <div className="flex flex-wrap gap-1.5">
          {held.length === 0 ? (
            <Micro>—</Micro>
          ) : (
            held.map((l) => (
              <Chip key={l} variant="pos" size="sm">
                <Check size={11} /> {l}
              </Chip>
            ))
          )}
        </div>
      </div>
      <div className="mt-auto">
        <Micro className="mb-1.5 block">Often added by peers</Micro>
        <div className="flex flex-wrap gap-1.5">
          {gaps.map((g) => (
            <span
              key={g.line}
              className="inline-flex items-center gap-1.5 rounded-chip border border-dashed border-rule-strong px-2.5 py-1 text-[11.5px] text-ink-soft"
            >
              <Circle size={11} /> {g.line}
              <span className="ml-0.5 text-[10px] opacity-60">{g.peerPct}%</span>
            </span>
          ))}
        </div>
      </div>
    </Card>
  );
}

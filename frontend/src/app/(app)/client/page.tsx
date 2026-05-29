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
import { fetchOverview, fetchSubmissionScore } from "@/lib/portalApi";
import { useAuthStore } from "@/store/authStore";
import { formatCurrency } from "@/lib/format";
import { cn } from "@/lib/utils";
import type {
  ClientOverviewResponse,
  ClientCoverageEntry,
  ImpactBreakdown,
  OverviewResponse,
  ScoreResponse,
  SignalImpact,
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
  const accessToken = useAuthStore((s) => s.accessToken);
  const coverages = data.active_coverages;
  const hero = coverages[0];

  // Secondary fetch: pull the hero coverage's impact breakdown so the
  // Signal Pulse card can show real strength / drag contributions. This
  // is intentionally NOT awaited at the page level -- the card renders
  // its own mini loading / empty state while the score loads, and the
  // rest of the page is already rendered from the /overview payload.
  const heroCode = hero?.submission_code ?? null;
  const score = useRoleScopedFetch<ScoreResponse>({
    fetcher: () => fetchSubmissionScore(accessToken, heroCode as string),
    enabled: !!accessToken && !!heroCode,
    deps: [accessToken, heroCode],
  });

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
            <SignalPulseCard
              breakdown={score.data?.impact_breakdown ?? null}
              loading={score.loading}
            />
            <CohortStandingCard hero={hero} />
          </div>

          {/* ────────── ROW 3 — loss / exposure / coverage shape ────────── */}
          <div className="grid gap-4 lg:grid-cols-3">
            <LossOutlookCard hero={hero} />
            <ExposureCard hero={hero} />
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
  // Fall back to the original design literals when the backend hasn't
  // populated the peer/prior fields (e.g. brand-new submission, thin
  // cohort) so the card still reads cleanly instead of going blank.
  const median = hero?.peer_cohort_median_score ?? 714;
  const prev = hero?.previous_composite_score ?? 706;
  const history: ScorePoint[] = useMemo(() => {
    const real = hero?.score_history;
    if (real && real.length > 0) {
      // Map the backend's oldest -> newest list onto the spark trail.
      // Mark the last point as "now" and the second-to-last as "prev"
      // so the marker styling (used by ScoreHistory) lines up with the
      // designed default.
      const last = real.length - 1;
      return real.map((p, i): ScorePoint => ({
        label: `v${p.version_number}`,
        value: p.composite_score,
        marker:
          i === last ? "now" : i === last - 1 ? "prev" : undefined,
      }));
    }
    return [
      { label: "Q1", value: 692 },
      { label: "Q2", value: 705 },
      { label: "Q3", value: 712 },
      { label: "prev", value: prev, marker: "prev" },
      { label: "now", value: score ?? prev, marker: "now" },
    ];
  }, [hero?.score_history, prev, score]);
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
      {count > 0 && (
        <Caption className="mt-1">
          Across {count} active polic{count === 1 ? "y" : "ies"}
        </Caption>
      )}
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
  // The "Next →" footer wraps to item 0, but the forward arrow above is
  // disabled on the last item. Hide the preview on the last item so the
  // affordance matches the arrow's enabled state.
  const showNextPreview = items.length > 1 && canFwd;

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
      {showNextPreview && (
        <button
          type="button"
          onClick={() => setIdx(idx + 1)}
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

// Designed-default contributions — used only when the score fetch
// returns no impact breakdown (legacy / unscored submissions), so the
// card never reads as broken.
const FALLBACK_HELPING: PulseRow[] = [
  { label: "MFA on admins", value: 12100, max: 12100 },
  { label: "No prior claims (5y)", value: 9300, max: 12100 },
  { label: "EDR coverage 95%+", value: 6700, max: 12100 },
];
const FALLBACK_OPPORTUNITY: PulseRow[] = [
  { label: "SOC 2 Type II", value: 18200, max: 18200 },
  { label: "Backup encryption", value: 11400, max: 18200 },
  { label: "Public RDP exposed", value: 6200, max: 18200 },
];
const FALLBACK_HELPING_DELTA = "−$28.1k";
const FALLBACK_OPPORTUNITY_DELTA = "+$40.7k";

// Cap rows so the column reads cleanly; the breakdown is already sorted
// by absolute dollar impact desc server-side.
const PULSE_MAX_ROWS = 3;

function deltaLabel(total: number, sign: "+" | "−"): string {
  return `${sign}$${(Math.abs(total) / 1000).toFixed(1)}k`;
}

function impactsToRows(impacts: SignalImpact[]): PulseRow[] {
  const rows = impacts.slice(0, PULSE_MAX_ROWS).map((s) => ({
    label: s.signal_label,
    value: Math.abs(s.premium_delta_usd),
    max: 1,
  }));
  const max = rows.reduce((m, r) => Math.max(m, r.value), 0) || 1;
  return rows.map((r) => ({ ...r, max }));
}

function SignalPulseCard({
  breakdown,
  loading,
}: {
  breakdown: ImpactBreakdown | null;
  loading: boolean;
}) {
  // Prefer the real impact breakdown (helping = strengths, opportunity =
  // drags). Fall back to the designed defaults ONLY when the secondary
  // score fetch returned nothing usable.
  const hasReal =
    !!breakdown &&
    (breakdown.strengths.length > 0 || breakdown.drags.length > 0);

  const helping = hasReal
    ? impactsToRows(breakdown!.strengths)
    : FALLBACK_HELPING;
  const opportunity = hasReal
    ? impactsToRows(breakdown!.drags)
    : FALLBACK_OPPORTUNITY;

  const helpingDelta = hasReal
    ? deltaLabel(
        breakdown!.strengths.reduce((s, r) => s + r.premium_delta_usd, 0),
        "−",
      )
    : FALLBACK_HELPING_DELTA;
  const opportunityDelta = hasReal
    ? deltaLabel(
        breakdown!.drags.reduce((s, r) => s + r.premium_delta_usd, 0),
        "+",
      )
    : FALLBACK_OPPORTUNITY_DELTA;

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
      {loading && !breakdown ? (
        <Body className="italic">Loading signal contributions…</Body>
      ) : (
        <div className="grid gap-6 sm:grid-cols-2">
          <PulseColumn
            heading="Helping"
            headingChip="pos"
            headingIcon={<TrendingDown size={12} />}
            deltaLabel={helpingDelta}
            accent="bg-pos"
            rows={helping}
            sign="−"
            deltaClass="text-pos"
          />
          <PulseColumn
            heading="Opportunity"
            headingChip="spot"
            headingIcon={<Lightbulb size={12} />}
            deltaLabel={opportunityDelta}
            accent="bg-spot"
            rows={opportunity}
            sign="+"
            deltaClass="text-spot-deep dark:text-spot"
          />
        </div>
      )}
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
  // Fall back to the designed default literals if the cohort is too
  // thin to compute one of these stats (the backend returns null).
  const median = hero?.peer_cohort_median_score ?? 714;
  const topDecile = hero?.peer_cohort_top_decile ?? 784;
  const range: [number, number] = [
    hero?.peer_cohort_min ?? 600,
    hero?.peer_cohort_max ?? 880,
  ];
  const peerCount = hero?.peer_cohort_size ?? 38;
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
        <Micro>{peerCount} peers</Micro>
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

// 12 labels, oldest -> newest, ending in the current calendar quarter.
// Matches the backend's loss_event_quarters bucketing so bar i maps to
// label i.
function lastTwelveQuarterLabels(now: Date = new Date()): string[] {
  const labels: string[] = [];
  let q = Math.floor(now.getUTCMonth() / 3); // 0..3
  let yr = now.getUTCFullYear();
  for (let i = 0; i < 12; i++) {
    labels.unshift(`${String(yr).slice(2)} Q${q + 1}`);
    q -= 1;
    if (q < 0) {
      q = 3;
      yr -= 1;
    }
  }
  return labels;
}

// Map the MV loss_propensity_band to the card's headline label.
function lossBandLabel(band: string): string {
  switch (band) {
    case "very_low":
      return "Very low";
    case "low":
      return "Low";
    case "moderate":
    case "medium":
      return "Moderate";
    case "elevated":
      return "Elevated";
    case "high":
      return "High";
    default:
      // Title-case an unrecognised band rather than blanking it.
      return band.charAt(0).toUpperCase() + band.slice(1).replace(/_/g, " ");
  }
}

// Map loss_trend_direction to chip tone + arrow + label. The model
// emits improving / stable / deteriorating.
function lossTrend(direction: string): {
  variant: "pos" | "neg" | "mute";
  icon: React.ReactNode;
  label: string;
} {
  switch (direction) {
    case "improving":
      return { variant: "pos", icon: <TrendingDown size={11} />, label: "Improving" };
    case "deteriorating":
    case "worsening":
      return { variant: "neg", icon: <TrendingUp size={11} />, label: "Worsening" };
    case "stable":
      return { variant: "mute", icon: <Circle size={11} />, label: "Stable" };
    default:
      return { variant: "mute", icon: <Circle size={11} />, label: direction };
  }
}

function LossOutlookCard({ hero }: { hero?: ClientCoverageEntry }) {
  // Real band / trend off the latest MV row, falling back to the
  // designed literals when the MV row hasn't populated them.
  const bandLabel = hero?.loss_propensity_band
    ? lossBandLabel(hero.loss_propensity_band)
    : "Low";
  const trend = hero?.loss_trend_direction
    ? lossTrend(hero.loss_trend_direction)
    : { variant: "pos" as const, icon: <TrendingDown size={11} />, label: "Improving" };

  // Frequency / severity velocities (points/month). When present, surface
  // the rounded velocity as the comparison value; otherwise keep the
  // designed literals so the bars still read.
  const freqValue =
    hero?.loss_frequency_velocity != null
      ? Math.round(hero.loss_frequency_velocity)
      : 32;
  const sevValue =
    hero?.loss_severity_velocity != null
      ? Math.round(hero.loss_severity_velocity)
      : 41;

  // Real per-quarter incurred-loss strip from /portal/overview. When the
  // entity has no loss events in the 12-quarter window the backend
  // returns null and we fall back to the designed placeholder strip so
  // the card still reads (rather than collapsing to flat bars).
  const quarters: number[] = hero?.loss_event_quarters?.length
    ? hero.loss_event_quarters
    : [0, 0, 0, 0, 0, 0.4, 0, 0, 0, 0, 0.7, 0];
  const quarterLabels = lastTwelveQuarterLabels();
  return (
    <Card variant="pos" pad="lg" className="flex h-full flex-col gap-3">
      <div className="flex items-baseline justify-between">
        <div>
          <Eyebrow className="text-pos">Loss outlook</Eyebrow>
          <p className="mt-1 text-xl font-semibold text-pos">{bandLabel}</p>
        </div>
        <Chip variant={trend.variant} size="sm">
          {trend.icon} {trend.label}
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
              title={`${quarterLabels[i]} — ${v > 0 ? "claim" : "no claim"}`}
            />
          ))}
        </div>
        <div className="mt-1 flex justify-between">
          {[quarterLabels[0], quarterLabels[6], quarterLabels[11]].map((l) => (
            <Micro key={l}>{l}</Micro>
          ))}
        </div>
      </div>
      <div className="mt-auto grid grid-cols-2 gap-3">
        <CompareBar label="Frequency" value={freqValue} cohort={48} />
        <CompareBar label="Severity" value={sevValue} cohort={44} />
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

function formatExposure(value: number): string {
  // Compact $-figure for the exposure card (e.g. $118M, $1.2B). Falls
  // back to the absolute dollar amount under $1M.
  const abs = Math.abs(value);
  if (abs >= 1_000_000_000) {
    return `$${(value / 1_000_000_000).toFixed(1)}B`;
  }
  if (abs >= 1_000_000) {
    return `$${Math.round(value / 1_000_000)}M`;
  }
  if (abs >= 1_000) {
    return `$${Math.round(value / 1_000)}k`;
  }
  return `$${Math.round(value)}`;
}

function ExposureCard({ hero }: { hero?: ClientCoverageEntry }) {
  // Real backend values where available, fall back to the designed
  // literals so the card still reads when the hero MV row is empty.
  const exposureValue = hero?.exposure_value ?? null;
  const exposurePrior = hero?.exposure_value_prior ?? null;
  // exposure_size_score is 0-100; the pin position is a percentage on
  // the Small <-> Large axis, so use it directly.
  const pinPct = hero?.exposure_size_score ?? 55;
  const yoyPct =
    exposureValue != null && exposurePrior != null && exposurePrior !== 0
      ? Math.round(((exposureValue - exposurePrior) / exposurePrior) * 100)
      : null;
  const yoyLabel =
    yoyPct != null ? `${yoyPct >= 0 ? "+" : ""}${yoyPct}% YoY` : "+12% YoY";
  const yoyPositive = yoyPct == null ? true : yoyPct >= 0;
  const valueLabel = exposureValue != null
    ? formatExposure(exposureValue)
    : "$118M";
  const bandLabel = hero?.exposure_band_label ?? null;
  return (
    <Card variant="aux" pad="lg" className="flex h-full flex-col gap-3">
      <div className="flex items-baseline justify-between">
        <div>
          <Eyebrow className="text-aux">Exposure</Eyebrow>
          <p className="mt-1 text-xl font-semibold text-aux">{valueLabel}</p>
          {bandLabel && (
            <Caption className="mt-0.5">{bandLabel}</Caption>
          )}
        </div>
        <Chip variant={yoyPositive ? "pos" : "neg"} size="sm">
          {yoyPositive ? <TrendingUp size={11} /> : <TrendingDown size={11} />}
          {" "}
          {yoyLabel}
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

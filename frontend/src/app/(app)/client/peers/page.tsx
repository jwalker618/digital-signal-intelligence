// Mirrors reim_peers (reimagined_b.jsx ReimPeers): header + You/median/top-decile
// KPIs, a cohort bell-curve with a context aside, and a signal-by-signal grid.
"use client";

import Link from "next/link";
import { Suspense } from "react";
import { useSearchParams } from "next/navigation";
import { ArrowRight, Check } from "lucide-react";
import { Topbar } from "@/components/chrome/topbar";
import { Card } from "@/components/ui/card";
import { Chip } from "@/components/ui/chip";
import { Eyebrow, Body, Micro, Caption } from "@/components/ui/typography";
import { BellCurve } from "@/components/charts/bell-curve";
import { PageError, PageLoading, RoleGate } from "@/components/base/pageStates";
import { useRoleScopedFetch } from "@/lib/useRoleScopedFetch";
import { fetchOverview, fetchSubmissionPeers } from "@/lib/portalApi";
import { useAuthStore } from "@/store/authStore";
import { cn } from "@/lib/utils";
import type {
  OverviewResponse,
  PeersResponse,
  SignalRankEntry,
} from "@/types/portal";

export default function ClientPeersPage() {
  return (
    <Suspense fallback={<PageLoading />}>
      <PeersInner />
    </Suspense>
  );
}

function PeersInner() {
  const accessToken = useAuthStore((s) => s.accessToken);
  const user = useAuthStore((s) => s.user);
  const enabled = !!accessToken && user?.role === "CLIENT";
  const params = useSearchParams();
  const explicitCode = params.get("code");

  const overview = useRoleScopedFetch<OverviewResponse>({
    fetcher: () => fetchOverview(accessToken),
    enabled,
    deps: [accessToken],
  });

  const code =
    explicitCode ??
    (overview.data?.role === "CLIENT"
      ? overview.data.active_coverages[0]?.submission_code
      : undefined);

  const peers = useRoleScopedFetch<PeersResponse>({
    fetcher: () => fetchSubmissionPeers(accessToken, code!),
    enabled: enabled && !!code,
    deps: [accessToken, code],
  });

  if (!user) return <PageLoading message="Signing in…" />;
  if (user.role && user.role !== "CLIENT") return <RoleGate expected="client" />;
  if (overview.loading) return <PageLoading />;
  if (overview.error) return <PageError message={overview.error} />;
  if (!overview.data || overview.data.role !== "CLIENT")
    return <RoleGate expected="client" />;
  if (!code) {
    return (
      <>
        <Topbar
          crumbs={["Client Portal", "Industry Benchmarks"]}
          entity={overview.data.entity_name}
        />
        <div className="flex flex-1 items-start justify-center px-9 py-12">
          <Card pad="lg" className="max-w-md">
            <Eyebrow>No coverage selected</Eyebrow>
            <Body className="mt-2">
              Open one from{" "}
              <Link
                href="/client/coverages"
                className="font-semibold text-info hover:underline"
              >
                Coverages
              </Link>{" "}
              to see how you compare to your peer cohort.
            </Body>
          </Card>
        </div>
      </>
    );
  }
  if (peers.loading) return <PageLoading />;
  if (peers.error) return <PageError message={peers.error} />;
  if (!peers.data) return <PageLoading />;

  return (
    <PeersBody entityName={overview.data.entity_name} peers={peers.data} />
  );
}

function PeersBody({
  entityName,
  peers,
}: {
  entityName: string;
  peers: PeersResponse;
}) {
  const you = peers.entity_score ?? 0;
  const mean = peers.cohort_mean_score ?? you;
  const median = peers.cohort_median_score ?? mean;
  const sd = 80;
  const topDecile = mean + 1.28 * sd;
  const range: [number, number] = [
    Math.max(0, Math.min(you, mean - 3 * sd)),
    Math.min(1000, Math.max(you, mean + 3 * sd)),
  ];
  const percentile = peers.peer_percentile_rank ?? null;
  const cohortSize = peers.cohort_size ?? null;
  const toTopDecile = Math.max(0, Math.round(topDecile - you));
  const peersAbove =
    cohortSize != null && percentile != null
      ? Math.round((cohortSize * (100 - percentile)) / 100)
      : null;
  const aheadOfMedian = you >= median;

  // Signal-by-signal: combine strengths + weaknesses, biggest deviation first.
  const signals: SignalRankEntry[] = peers.signal_ranking
    ? [...peers.signal_ranking.strengths, ...peers.signal_ranking.weaknesses]
        .sort((a, b) => Math.abs(b.z_score) - Math.abs(a.z_score))
        .slice(0, 8)
    : [];

  return (
    <>
      <Topbar
        crumbs={["Client Portal", "Industry Benchmarks", peers.coverage]}
        entity={entityName}
      />
      <div className="flex-1 overflow-y-auto px-9 py-7">
        <div className="grid gap-[18px]">
          {/* ── Row 1: heading + You / median / top-decile KPIs ── */}
          <div className="flex flex-wrap items-end justify-between gap-6">
            <div>
              <Eyebrow>Industry benchmarks</Eyebrow>
              <h1 className="mt-1.5 font-display text-[32px] font-semibold leading-tight tracking-tight text-ink">
                {cohortSize != null
                  ? `How you compare to ${cohortSize} peers in your cohort`
                  : "How you compare to your peer cohort"}
              </h1>
              <Caption className="mt-1.5 block">
                {peers.coverage} line
                {peers.cohort_id ? ` · cohort ${peers.cohort_id}` : ""}
              </Caption>
            </div>
            <div className="flex gap-3">
              <KpiCard label="You" value={you.toFixed(0)} variant="info" />
              <KpiCard label="cohort median" value={median.toFixed(0)} />
              <KpiCard label="top decile" value={topDecile.toFixed(0)} />
            </div>
          </div>

          {/* ── Row 2: bell-curve distribution + context aside ── */}
          <Card pad="lg">
            <div className="grid gap-7 lg:grid-cols-[1.5fr_1fr]">
              <div>
                <div className="mb-3 flex items-baseline justify-between">
                  <h3 className="font-display text-[18px] font-semibold leading-tight text-ink">
                    Distribution of cohort scores
                  </h3>
                  <Caption>{cohortSize ?? 0} peers</Caption>
                </div>
                <BellCurve
                  cohort={{ mean, sd, median, topDecile, range, you }}
                  height={200}
                />
                <Body className="mt-1">
                  {aheadOfMedian ? (
                    <>
                      You&apos;re outperforming the typical peer —{" "}
                      <span className="font-semibold text-info">
                        {toTopDecile} points of headroom
                      </span>{" "}
                      separate you from the top-decile profile.
                    </>
                  ) : (
                    <>
                      You sit below the cohort median —{" "}
                      <span className="font-semibold text-spot-deep dark:text-spot">
                        {Math.round(median - you)} points
                      </span>{" "}
                      would bring you to the typical peer.
                    </>
                  )}
                </Body>
              </div>

              {/* context aside */}
              <div className="flex flex-col gap-4 border-t border-rule pt-5 lg:border-l lg:border-t-0 lg:pl-5 lg:pt-0">
                <div>
                  <Eyebrow>How to read this</Eyebrow>
                  <Caption className="mt-1.5 block leading-relaxed">
                    Each peer in your cohort is one point under the curve. Your
                    score sits where the teal pin lands; the green band marks
                    where the top decile begins.
                  </Caption>
                </div>
                <div className="grid grid-cols-2 gap-3 border-t border-rule pt-3">
                  <ContextStat
                    label="cohort range"
                    value={`${Math.round(range[0])}–${Math.round(range[1])}`}
                  />
                  <ContextStat label="cohort std dev" value={`${sd} pts`} />
                  <ContextStat
                    label="peers above you"
                    value={
                      peersAbove != null && cohortSize != null
                        ? `${peersAbove} of ${cohortSize}`
                        : "—"
                    }
                  />
                  <ContextStat
                    label="to top decile"
                    value={`+${toTopDecile}`}
                    tone="spot"
                  />
                </div>
                <div className="mt-auto border-t border-rule pt-3">
                  <Caption className="mb-2 block">
                    Your action plan can help close that{" "}
                    {toTopDecile}-point headroom.
                  </Caption>
                  <Link
                    href="/client/actions"
                    className="inline-flex items-center gap-1.5 rounded-btn bg-spot px-3 py-2 text-[13px] font-semibold text-white transition hover:bg-spot-deep"
                  >
                    See action plan <ArrowRight size={14} />
                  </Link>
                </div>
              </div>
            </div>
          </Card>

          {/* ── Row 3: signal-by-signal ── */}
          {signals.length > 0 && (
            <Card pad="lg">
              <div className="mb-3.5 flex items-baseline justify-between">
                <div>
                  <h3 className="font-display text-[18px] font-semibold leading-tight text-ink">
                    Signals that set you apart from your peers
                  </h3>
                  <Caption className="mt-1 block">
                    how far each signal sits from the cohort average
                  </Caption>
                </div>
                <Chip variant="spot" size="sm">
                  opportunities highlighted
                </Chip>
              </div>
              <div className="grid gap-x-[18px] gap-y-3.5 md:grid-cols-2">
                {signals.map((s) => (
                  <PracticeBar key={s.signal_id} entry={s} />
                ))}
              </div>
            </Card>
          )}

          {peers.note && (
            <Caption className="block">{peers.note}</Caption>
          )}
        </div>
      </div>
    </>
  );
}

function KpiCard({
  label,
  value,
  variant,
}: {
  label: string;
  value: string;
  variant?: "info";
}) {
  const info = variant === "info";
  return (
    <Card
      pad="none"
      variant={info ? "info" : "default"}
      className="min-w-[100px] px-[18px] py-3.5"
    >
      <Eyebrow className={info ? "text-info-deep dark:text-info" : undefined}>
        {label}
      </Eyebrow>
      <p
        className={cn(
          "mt-1 font-display text-[24px] font-semibold leading-none tabular-nums",
          info ? "text-info-deep dark:text-info" : "text-ink",
        )}
      >
        {value}
      </p>
    </Card>
  );
}

function ContextStat({
  label,
  value,
  tone,
}: {
  label: string;
  value: string;
  tone?: "spot";
}) {
  return (
    <div>
      <Micro className="block">{label}</Micro>
      <p
        className={cn(
          "mt-0.5 text-[16px] font-semibold tabular-nums leading-none",
          tone === "spot" ? "text-spot-deep dark:text-spot" : "text-ink",
        )}
      >
        {value}
      </p>
    </div>
  );
}

/**
 * One signal row in the practices grid. z_score > 0 → you out-pace the cohort
 * (green "you"); z_score < 0 → an opportunity (coral). The bar fills by the
 * deviation magnitude, capped at 3σ.
 */
function PracticeBar({ entry }: { entry: SignalRankEntry }) {
  const ahead = entry.z_score >= 0;
  const fill = Math.min(100, Math.round((Math.abs(entry.z_score) / 3) * 100));
  return (
    <div>
      <div className="mb-1 flex items-baseline justify-between gap-2">
        <span className="flex min-w-0 items-center gap-1.5 text-[13px]">
          {ahead ? (
            <Chip variant="pos" size="sm">
              <Check size={10} /> you
            </Chip>
          ) : (
            <Chip variant="spot" size="sm">
              opportunity
            </Chip>
          )}
          <span className="truncate text-ink">{entry.signal_id}</span>
        </span>
        <span className="shrink-0 text-[13px] font-semibold tabular-nums text-ink">
          {entry.z_score > 0 ? "+" : ""}
          {entry.z_score.toFixed(1)}σ
        </span>
      </div>
      <div className="h-2 overflow-hidden rounded-sm bg-surface-sunken">
        <div
          className={cn("h-full", ahead ? "bg-pos" : "bg-spot")}
          style={{ width: `${Math.max(4, fill)}%` }}
        />
      </div>
    </div>
  );
}

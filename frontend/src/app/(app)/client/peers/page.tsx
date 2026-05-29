// No direct design counterpart; adapted from reim_overview.jsx (CohortStandingCard).
"use client";

import Link from "next/link";
import { Suspense } from "react";
import { useSearchParams } from "next/navigation";
import { ArrowDown, ArrowUp, TrendingDown, TrendingUp } from "lucide-react";
import { Topbar } from "@/components/chrome/topbar";
import { Card } from "@/components/ui/card";
import { Chip } from "@/components/ui/chip";
import { Eyebrow, Body, Micro, Caption } from "@/components/ui/typography";
import { CohortBar } from "@/components/charts/cohort-bar";
import { BellCurve } from "@/components/charts/bell-curve";
import { PageError, PageLoading, RoleGate } from "@/components/base/pageStates";
import { useRoleScopedFetch } from "@/lib/useRoleScopedFetch";
import { fetchOverview, fetchSubmissionPeers } from "@/lib/portalApi";
import { useAuthStore } from "@/store/authStore";
import { peerStandingPositive } from "@/lib/portalTone";
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
  const vsMedian = Math.round(you - median);
  const toTopDecile = Math.max(0, Math.round(topDecile - you));

  return (
    <>
      <Topbar
        crumbs={["Client Portal", "Industry Benchmarks", peers.coverage]}
        entity={entityName}
      />
      <div className="flex-1 overflow-y-auto px-9 py-7">
        <div className="mx-auto grid max-w-[1280px] gap-4">
          <div>
            <Eyebrow>Industry benchmarks</Eyebrow>
            <h1 className="mt-1.5 font-display text-[32px] font-semibold leading-none tracking-tight text-ink">
              {peers.coverage}
            </h1>
            {peers.cohort_id && (
              <Micro className="mt-2 block font-mono">
                cohort {peers.cohort_id}
              </Micro>
            )}
          </div>

          {/* hero: cohort standing card */}
          <Card pad="lg" className="flex flex-col">
            <div className="flex items-baseline justify-between">
              <div>
                <Eyebrow>Cohort standing</Eyebrow>
                <h3 className="mt-1.5 font-display text-[20px] font-semibold leading-tight text-ink">
                  You sit at the{" "}
                  <span className="text-pos">
                    {percentile != null
                      ? `${Math.round(percentile)}th percentile`
                      : peerStandingPositive(percentile)}
                  </span>
                </h3>
              </div>
              <Micro>{peers.cohort_size ?? 0} peers</Micro>
            </div>
            <div className="my-5 flex flex-1 items-center">
              <CohortBar
                value={you}
                median={median}
                topDecile={topDecile}
                range={range}
                className="w-full"
              />
            </div>
            <div className="grid grid-cols-3 gap-3 border-t border-rule pt-3">
              <Stat
                label="vs median"
                value={`${vsMedian >= 0 ? "+" : ""}${vsMedian}`}
                tone={vsMedian >= 0 ? "pos" : "neg"}
                icon={vsMedian >= 0 ? ArrowUp : ArrowDown}
              />
              <Stat
                label="your score"
                value={you.toFixed(0)}
                tone="info"
              />
              <Stat
                label="to top decile"
                value={toTopDecile.toString()}
              />
            </div>
          </Card>

          {/* distribution */}
          {peers.entity_score != null && peers.cohort_mean_score != null && (
            <Card pad="lg">
              <div className="mb-4 flex items-baseline justify-between">
                <div>
                  <Eyebrow>Cohort distribution</Eyebrow>
                  <h3 className="mt-1.5 font-display text-[17px] font-semibold leading-tight text-ink">
                    Where you fall on the curve
                  </h3>
                </div>
                <Micro>{peers.cohort_size ?? 0} peers</Micro>
              </div>
              <BellCurve
                cohort={{
                  mean,
                  sd,
                  median,
                  topDecile,
                  range,
                  you,
                }}
                height={200}
              />
            </Card>
          )}

          {peers.note && (
            <Card variant="aux" pad="md">
              <Eyebrow className="text-aux">Methodology</Eyebrow>
              <Body className="mt-1">{peers.note}</Body>
            </Card>
          )}

          {peers.signal_ranking && (
            <div className="grid gap-4 md:grid-cols-2">
              <SignalRankList
                title="You out-pace your peers on"
                accent="pos"
                items={peers.signal_ranking.strengths}
                icon={TrendingUp}
                empty="No standout strengths vs the cohort."
              />
              <SignalRankList
                title="Peers out-pace you on"
                accent="spot"
                items={peers.signal_ranking.weaknesses}
                icon={TrendingDown}
                empty="No standout weaknesses vs the cohort."
              />
            </div>
          )}
        </div>
      </div>
    </>
  );
}

function Stat({
  label,
  value,
  tone,
  icon: Icon,
}: {
  label: string;
  value: string;
  tone?: "pos" | "neg" | "info";
  icon?: typeof ArrowUp;
}) {
  const toneClass =
    tone === "pos"
      ? "text-pos"
      : tone === "neg"
        ? "text-neg"
        : tone === "info"
          ? "text-info"
          : "text-ink";
  return (
    <div>
      <Micro className="block">{label}</Micro>
      <p
        className={cn(
          "mt-0.5 flex items-center gap-1 text-[18px] font-semibold tabular-nums leading-none",
          toneClass,
        )}
      >
        {Icon && <Icon size={14} />} {value}
      </p>
    </div>
  );
}

function SignalRankList({
  title,
  accent,
  items,
  icon: Icon,
  empty,
}: {
  title: string;
  accent: "pos" | "spot";
  items: SignalRankEntry[];
  icon: typeof TrendingUp;
  empty: string;
}) {
  const sorted = [...items].sort(
    (a, b) => Math.abs(b.z_score) - Math.abs(a.z_score),
  );
  return (
    <Card pad="lg" variant={accent}>
      <header className="flex items-center justify-between">
        <Eyebrow
          className={
            accent === "pos" ? "text-pos" : "text-spot-deep dark:text-spot"
          }
        >
          {title}
        </Eyebrow>
        <Chip variant={accent} size="sm">
          <Icon size={11} />
          {items.length} signal{items.length === 1 ? "" : "s"}
        </Chip>
      </header>
      {items.length === 0 ? (
        <Body className="mt-3 italic">{empty}</Body>
      ) : (
        <ul className="mt-3 space-y-2">
          {sorted.slice(0, 8).map((s) => (
            <li
              key={s.signal_id}
              className="flex items-baseline justify-between gap-3 border-b border-rule/40 pb-2 last:border-0 last:pb-0"
            >
              <div className="min-w-0 flex-1">
                <p className="truncate text-[13.5px] font-medium text-ink">
                  {s.signal_id}
                </p>
                <Caption className="block">
                  You {s.entity_value.toFixed(1)} · cohort{" "}
                  {s.cohort_mean.toFixed(1)}
                </Caption>
              </div>
              <Chip variant={accent} size="sm">
                {s.z_score > 0 ? "+" : ""}
                {s.z_score.toFixed(1)}σ
              </Chip>
            </li>
          ))}
        </ul>
      )}
    </Card>
  );
}

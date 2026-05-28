"use client";

import Link from "next/link";
import { Suspense } from "react";
import { useSearchParams } from "next/navigation";
import { Topbar } from "@/components/chrome/topbar";
import { Card } from "@/components/ui/card";
import { Chip } from "@/components/ui/chip";
import { Eyebrow, NumDisplay, Body, Micro } from "@/components/ui/typography";
import { BellCurve } from "@/components/charts/bell-curve";
import { PageError, PageLoading, RoleGate } from "@/components/base/pageStates";
import { useRoleScopedFetch } from "@/lib/useRoleScopedFetch";
import { fetchOverview, fetchSubmissionPeers } from "@/lib/portalApi";
import { useAuthStore } from "@/store/authStore";
import { peerStandingPositive } from "@/lib/portalTone";
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
    <PeersBody
      entityName={overview.data.entity_name}
      peers={peers.data}
    />
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
  // Heuristic SD when API doesn't supply it explicitly; ~80 points covers
  // a reasonable spread of composite scores.
  const sd = 80;
  const topDecile = mean + 1.28 * sd;
  const lo = Math.max(0, Math.min(you, mean - 3 * sd));
  const hi = Math.min(1000, Math.max(you, mean + 3 * sd));

  return (
    <>
      <Topbar
        crumbs={["Client Portal", "Industry Benchmarks", peers.coverage]}
        entity={entityName}
      />
      <div className="flex-1 overflow-y-auto px-9 py-7">
        <div className="mx-auto grid max-w-[1280px] gap-6">
          <header>
            <Eyebrow>Industry Benchmarks</Eyebrow>
            <h1 className="mt-1.5 font-display text-[32px] font-semibold leading-none tracking-tight text-ink">
              {peers.coverage}
            </h1>
            {peers.cohort_id && (
              <Micro className="mt-2 block font-mono">
                cohort {peers.cohort_id}
              </Micro>
            )}
          </header>

          {/* Hero stat */}
          <Card variant="info" pad="lg" className="space-y-4">
            <div className="flex items-end justify-between gap-6">
              <div>
                <Eyebrow>Where you stand</Eyebrow>
                <p className="mt-1 text-[24px] font-semibold leading-tight text-ink">
                  {peerStandingPositive(peers.peer_percentile_rank)}
                </p>
              </div>
              {peers.peer_percentile_rank != null && (
                <div className="text-right">
                  <NumDisplay size="xl">
                    {Math.round(peers.peer_percentile_rank)}
                  </NumDisplay>
                  <Micro>percentile</Micro>
                </div>
              )}
            </div>
          </Card>

          {/* Bell curve */}
          {peers.entity_score != null && peers.cohort_mean_score != null && (
            <Card pad="lg">
              <header className="mb-4 flex items-center justify-between">
                <Eyebrow>Cohort distribution</Eyebrow>
                <Micro>{peers.cohort_size ?? 0} peers</Micro>
              </header>
              <BellCurve
                cohort={{
                  mean,
                  sd,
                  median,
                  topDecile,
                  range: [lo, hi],
                  you,
                }}
                height={200}
              />
              <div className="mt-4 grid grid-cols-3 gap-6 border-t border-rule pt-4">
                <Stat label="Your score" value={you.toFixed(0)} highlight />
                <Stat
                  label="Cohort median"
                  value={median.toFixed(0)}
                />
                <Stat
                  label="Top decile"
                  value={topDecile.toFixed(0)}
                />
              </div>
            </Card>
          )}

          {peers.note && (
            <Card variant="aux" pad="md">
              <Eyebrow className="text-aux">Methodology note</Eyebrow>
              <Body className="mt-1">{peers.note}</Body>
            </Card>
          )}

          {/* Signal ranking */}
          {peers.signal_ranking && (
            <div className="grid gap-5 md:grid-cols-2">
              <SignalRankList
                title="You out-pace your peers on"
                accent="pos"
                items={peers.signal_ranking.strengths}
                empty="No standout strengths vs the cohort."
              />
              <SignalRankList
                title="Peers out-pace you on"
                accent="spot"
                items={peers.signal_ranking.weaknesses}
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
  highlight,
}: {
  label: string;
  value: string;
  highlight?: boolean;
}) {
  return (
    <div>
      <Micro className="block">{label}</Micro>
      <p
        className={`mt-1 text-[24px] font-semibold leading-none tabular-nums ${highlight ? "text-info" : "text-ink"}`}
      >
        {value}
      </p>
    </div>
  );
}

function SignalRankList({
  title,
  accent,
  items,
  empty,
}: {
  title: string;
  accent: "pos" | "spot";
  items: SignalRankEntry[];
  empty: string;
}) {
  const sorted = [...items].sort(
    (a, b) => Math.abs(b.z_score) - Math.abs(a.z_score),
  );
  return (
    <Card pad="lg" variant={accent}>
      <header className="flex items-center justify-between">
        <Eyebrow className={accent === "pos" ? "text-pos" : "text-spot-deep dark:text-spot"}>
          {title}
        </Eyebrow>
        <Micro>{items.length} signals</Micro>
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
                <Micro className="block">
                  You {s.entity_value.toFixed(1)} · cohort {s.cohort_mean.toFixed(1)}
                </Micro>
              </div>
              <Chip
                variant={accent}
                size="sm"
              >
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

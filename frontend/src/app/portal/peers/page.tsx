"use client";

// v8 Phase 8 — /portal/peers
//
// Peer comparison detail: percentile rank, cohort stats, score
// distribution chart, and a narrative on where the entity sits.

import { useEffect, useMemo, useState } from "react";

import {
  AlertTriangle,
  Gauge,
  TrendingUpDown,
} from "lucide-react";

import ViewCanvas from "@/components/ViewCanvas";
import {
  CardGrid,
  StandardCard,
  SubmissionHeaderCard,
} from "@/components/base/cards";
import {
  InfoPanel,
  KpiTile,
  ScoreBar,
  StatsGrid,
} from "@/components/base/content/primatives";
import { DistributionBarChart } from "@/components/base/charts/primatives";

import { useAuthStore } from "@/store/authStore";
import { useDsiStore } from "@/store/dsiStore";
import {
  fetchOverview,
  fetchSubmissionPeers,
  fetchSubmissionScore,
} from "@/lib/portalApi";
import { formatNumber } from "@/lib/format";
import type {
  ClientOverviewResponse,
  PeersResponse,
  ScoreResponse,
} from "@/types/portal";


export default function PeersPage() {
  const accessToken = useAuthStore((s) => s.accessToken);
  const setActiveMenu = useDsiStore((s) => s.setActiveMenu);

  const [peers, setPeers] = useState<PeersResponse | null>(null);
  const [score, setScore] = useState<ScoreResponse | null>(null);
  const [entityName, setEntityName] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => { setActiveMenu("Peer Comparison"); }, [setActiveMenu]);

  useEffect(() => {
    let cancelled = false;
    async function load() {
      try {
        const overview = await fetchOverview(accessToken);
        if (cancelled) return;
        if (overview.role !== "CLIENT") {
          setError("Peer comparison view is currently for client users.");
          return;
        }
        const primary = (overview as ClientOverviewResponse).active_coverages[0];
        if (!primary) {
          setError("No active coverage to compare yet.");
          return;
        }
        setEntityName((overview as ClientOverviewResponse).entity_name);
        const [p, s] = await Promise.all([
          fetchSubmissionPeers(accessToken, primary.submission_code),
          fetchSubmissionScore(accessToken, primary.submission_code),
        ]);
        if (cancelled) return;
        setPeers(p); setScore(s);
      } catch (e) {
        if (!cancelled) setError(e instanceof Error ? e.message : String(e));
      }
    }
    if (accessToken) load();
    return () => { cancelled = true; };
  }, [accessToken]);

  if (error) return <ErrShell msg={error} />;
  if (!peers || !score) return <LoadShell />;

  if (peers.peer_percentile_rank == null) {
    return (
      <ViewCanvas>
        <CardGrid cols="grid-cols-1">
          <SubmissionHeaderCard
            decision="approve"
            title={`Peer Comparison — ${entityName ?? "Your entity"}`}
            subtitle="Where you sit against similar peers in your cohort"
            lucideIcon={TrendingUpDown}
          />
          <StandardCard title="Cohort not yet established" lucideIcon={AlertTriangle}>
            <p className="text-sm">
              {peers.note ?? "Not enough peer data to compute a percentile yet."}
            </p>
          </StandardCard>
        </CardGrid>
      </ViewCanvas>
    );
  }

  const subjectScore = score.composite_score ?? peers.entity_score ?? 0;

  return (
    <ViewCanvas>
      <CardGrid cols="grid-cols-1" className="gap-4">

        <SubmissionHeaderCard
          decision="approve"
          title={`Peer Comparison — ${entityName ?? "Your entity"}`}
          subtitle={`Cohort: ${peers.cohort_id ?? "unknown"} (${peers.cohort_size ?? 0} peers)`}
          lucideIcon={TrendingUpDown}
        >
          <StatsGrid
            columns={[
              { label: "Your score",      value: formatNumber(subjectScore, 0), align: "center" },
              { label: "Cohort average",  value: formatNumber(peers.cohort_mean_score ?? 0, 0), align: "center" },
              { label: "Cohort median",   value: formatNumber(peers.cohort_median_score ?? 0, 0), align: "center" },
              { label: "Percentile",      value: `${formatNumber(peers.peer_percentile_rank, 0)}th`, align: "center" },
            ]}
          />
        </SubmissionHeaderCard>

        <StandardCard title="Where you sit" lucideIcon={Gauge}>
          <div className="space-y-3 py-2">
            <p className="text-sm">{narrative(peers, subjectScore)}</p>
            <div>
              <span className="text-xs text-generate-text-placeholder">Percentile rank (0 = bottom, 100 = top)</span>
              <ScoreBar
                value={peers.peer_percentile_rank}
                min={0}
                max={100}
                decimals={0}
                thresholds={[
                  { at: 25, color: "var(--color-generate-text-bad)" },
                  { at: 50, color: "var(--color-generate-text-maybe)" },
                  { at: 75, color: "var(--color-generate-text-comment)" },
                  { at: Infinity, color: "var(--color-generate-text-good)" },
                ]}
              />
            </div>
          </div>
        </StandardCard>

        <StandardCard title="Cohort distribution" lucideIcon={TrendingUpDown}>
          <CohortDistributionViz peers={peers} subjectScore={subjectScore} />
        </StandardCard>

      </CardGrid>
    </ViewCanvas>
  );
}


function narrative(peers: PeersResponse, subjectScore: number): string {
  const pct = peers.peer_percentile_rank ?? 0;
  const mean = peers.cohort_mean_score ?? 0;
  const delta = subjectScore - mean;
  const sign = delta >= 0 ? "above" : "below";
  const where =
    pct >= 75 ? "in the top quartile" :
    pct >= 50 ? "above the median" :
    pct >= 25 ? "below the median" :
    "in the bottom quartile";
  return (
    `You rank in the ${formatNumber(pct, 0)}th percentile of ${peers.cohort_size ?? 0} ` +
    `peers in your cohort — ${where}. Your score of ${formatNumber(subjectScore, 0)} ` +
    `is ${formatNumber(Math.abs(delta), 0)} points ${sign} the cohort average.`
  );
}


function CohortDistributionViz({
  peers, subjectScore,
}: {
  peers: PeersResponse;
  subjectScore: number;
}) {
  // The API doesn't currently expose per-peer scores -- we render a
  // representative distribution around mean and median using a stylised
  // 7-bucket bar set. The subject's bar is highlighted. Real per-peer
  // histogram is a v8.1 follow-on.
  const mean = peers.cohort_mean_score ?? 720;
  const data = useMemo(() => buildBuckets(mean, peers.cohort_size ?? 30, subjectScore), [mean, peers.cohort_size, subjectScore]);

  return (
    <div className="py-2">
      <DistributionBarChart
        data={data}
        categoryKey="label"
        valueKey="count"
        colorFor={(entry) => (entry as { isSubject: boolean }).isSubject
          ? "var(--color-generate-text-comment)"
          : "var(--color-generate-text-outline)"
        }
        height={240}
        valueName="Peers"
      />
      <p className="text-xs text-generate-text-placeholder mt-2">
        Highlighted bar shows your score band. Distribution is illustrative
        (representative buckets around cohort mean).
      </p>
    </div>
  );
}

function buildBuckets(mean: number, cohortSize: number, subjectScore: number) {
  const stddev = 50;  // matches seed
  const buckets = 7;
  const bucketWidth = 50;
  const start = mean - (bucketWidth * Math.floor(buckets / 2));
  const result: Array<{ label: string; count: number; isSubject: boolean; lower: number; upper: number }> = [];

  for (let i = 0; i < buckets; i++) {
    const lower = start + i * bucketWidth;
    const upper = lower + bucketWidth;
    // Approximate normal-ish weight per bucket
    const mid = lower + bucketWidth / 2;
    const z = (mid - mean) / stddev;
    const weight = Math.exp(-(z * z) / 2);
    const count = Math.round((cohortSize / 6) * weight);
    const isSubject = subjectScore >= lower && subjectScore < upper;
    result.push({
      label: `${lower}-${upper}`,
      count,
      isSubject,
      lower,
      upper,
    });
  }
  return result;
}


function LoadShell() {
  return (
    <ViewCanvas>
      <CardGrid cols="grid-cols-1">
        <StandardCard title="Loading" lucideIcon={TrendingUpDown}>
          <p className="text-sm">Building peer comparison…</p>
        </StandardCard>
      </CardGrid>
    </ViewCanvas>
  );
}

function ErrShell({ msg }: { msg: string }) {
  return (
    <ViewCanvas>
      <CardGrid cols="grid-cols-1">
        <StandardCard title="Unable to load" lucideIcon={AlertTriangle}>
          <p className="text-sm text-generate-text-bad">{msg}</p>
        </StandardCard>
      </CardGrid>
    </ViewCanvas>
  );
}

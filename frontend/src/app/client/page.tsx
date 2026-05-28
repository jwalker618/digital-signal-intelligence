"use client";

// /client — client portal home.
//
// Extracted from the old /portal role-router in the v8.2 portal
// architecture cleanup. The client overview is now a first-class
// page at its own persona URL; SessionGuard routes CLIENT users
// here on login.

import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";

import {
  AlertTriangle,
  ArrowDown,
  ArrowUp,
  ChartPie,
  CircleDot,
  Gauge,
  Layers,
  ShieldCheck,
  TrendingUpDown,
  UserStar,
  Zap,
} from "lucide-react";

import ViewCanvas from "@/components/ViewCanvas";
import {
  CardGrid,
  StandardCard,
  SubmissionHeaderCard,
} from "@/components/base/cards";
import {
  LabelValueList,
  ScoreBar,
  StatsGrid,
} from "@/components/base/content/primatives";
import PendingQueryRow, { formatCoverageLabel } from "@/components/shared/PendingQueryRow";

import { useAuthStore } from "@/store/authStore";
import { useDsiStore } from "@/store/dsiStore";
import {
  fetchCommunications,
  fetchOverview,
  fetchSubmissionScore,
} from "@/lib/portalApi";
import { formatCurrency, formatNumber } from "@/lib/format";
import { peerStandingPositive, tierStatus } from "@/lib/portalTone";
import type {
  ClientCoverageEntry,
  ClientOverviewResponse,
  CommunicationItem,
  ScoreResponse,
  SignalImpact,
} from "@/types/portal";


export default function ClientOverviewPage() {
  const router = useRouter();
  const accessToken = useAuthStore((s) => s.accessToken);
  const userRole = useAuthStore((s) => s.user?.role ?? null);
  const setActiveMenu = useDsiStore((s) => s.setActiveMenu);

  const [data, setData] = useState<ClientOverviewResponse | null>(null);
  const [comms, setComms] = useState<CommunicationItem[]>([]);
  const [primaryScore, setPrimaryScore] = useState<ScoreResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => { setActiveMenu("Overview"); }, [setActiveMenu]);

  useEffect(() => {
    let cancelled = false;
    async function load() {
      try {
        const [resp, communicationsResp] = await Promise.all([
          fetchOverview(accessToken),
          fetchCommunications(accessToken, true),
        ]);
        if (cancelled) return;
        if (resp.role !== "CLIENT") {
          setError("The client overview is for client users only.");
          return;
        }
        const clientData = resp as ClientOverviewResponse;
        setData(clientData);
        setComms(communicationsResp.items);

        if (clientData.active_coverages.length > 0) {
          const primary = clientData.active_coverages[0];
          try {
            const sc = await fetchSubmissionScore(accessToken, primary.submission_code);
            if (!cancelled) setPrimaryScore(sc);
          } catch {
            // Best-effort: signal pulse degrades gracefully if this fails.
          }
        }
      } catch (e) {
        if (!cancelled) setError(e instanceof Error ? e.message : String(e));
      }
    }
    if (accessToken && userRole === "CLIENT") load();
    return () => { cancelled = true; };
  }, [accessToken, userRole]);

  const aggregates = useMemo(
    () => aggregateCoverages(data?.active_coverages ?? []),
    [data?.active_coverages],
  );

  if (userRole !== "CLIENT") return <ClientOnly />;
  if (error) return <ErrShell msg={error} />;
  if (!data) return <LoadShell />;

  const primary = data.active_coverages[0] ?? null;

  return (
    <ViewCanvas>
      <CardGrid cols="grid-cols-1" className="gap-4">

        <SubmissionHeaderCard
          decision={comms.length > 0 ? "refer" : "approve"}
          title={data.entity_name}
          subtitle={
            data.broker
              ? `Insured · Placed by ${data.broker.name}`
              : "Insured · No broker assigned"
          }
          lucideIcon={Gauge}
          headerRight={
            comms.length > 0 ? (
              <span className="text-xs text-generate-text-maybe font-bold flex items-center gap-1">
                <CircleDot className="generate-app-icon" />
                {comms.length} open quer{comms.length === 1 ? "y" : "ies"}
              </span>
            ) : (
              <span className="text-xs text-generate-text-good font-bold flex items-center gap-1">
                No open queries
              </span>
            )
          }
        >
          {primary ? (
            <StatsGrid
              columns={[
                { label: "Primary line",      value: formatCoverageLabel(primary.coverage), align: "center" },
                { label: "Signal score",      value: formatNumber(primary.composite_score ?? 0, 0), align: "center" },
                { label: "Status",            value: tierStatus(primary.tier).label, align: "center" },
                { label: "Peer standing",     value: peerStandingPositive(primary.peer_percentile_rank).split(",")[0], align: "center" },
                { label: "Active policies",   value: data.active_coverages.length, align: "center" },
                { label: "Total premium",     value: formatCurrency(aggregates.totalPremium, 0), align: "center" },
              ]}
            />
          ) : (
            <p className="text-sm py-2">No active coverages yet.</p>
          )}
        </SubmissionHeaderCard>

        {comms.length > 0 && (
          <StandardCard title="Pending underwriter requests" lucideIcon={UserStar}>
            <div className="space-y-3 py-2">
              {comms.slice(0, 4).map((c) => (
                <PendingQueryRow
                  key={c.referral_code}
                  query={c}
                  onClick={() => router.push(`/communications/${c.referral_code}`)}
                />
              ))}
              {comms.length > 4 && (
                <p className="text-xs text-generate-text-placeholder">
                  + {comms.length - 4} more pending in Communications.
                </p>
              )}
            </div>
          </StandardCard>
        )}

        <CardGrid cols="grid-cols-1 lg:grid-cols-2" className="gap-4">
          <StandardCard title="Signal pulse — primary coverage" lucideIcon={Zap}>
            <SignalPulse score={primaryScore} />
          </StandardCard>

          <StandardCard title="How you compare to top peers" lucideIcon={TrendingUpDown}>
            <PeerBenchmarkCard score={primaryScore} primary={primary} />
          </StandardCard>
        </CardGrid>

        <CardGrid cols="grid-cols-1 lg:grid-cols-3" className="gap-4">
          <StandardCard title="Loss profile" lucideIcon={ChartPie}>
            <LossSnapshot />
          </StandardCard>

          <StandardCard title="Exposure profile" lucideIcon={ShieldCheck}>
            <ExposureSnapshot />
          </StandardCard>

          <StandardCard title="Coverage spread" lucideIcon={Layers}>
            <CoverageSpread coverages={data.active_coverages} />
          </StandardCard>
        </CardGrid>

      </CardGrid>
    </ViewCanvas>
  );
}


function SignalPulse({ score }: { score: ScoreResponse | null }) {
  if (!score || !score.impact_breakdown) {
    return <p className="text-sm">No signal data available yet.</p>;
  }
  const drags = score.impact_breakdown.drags.slice(0, 3);
  const strengths = score.impact_breakdown.strengths.slice(0, 3);

  return (
    <div className="grid grid-cols-2 gap-4 py-2">
      <div>
        <div className="text-xs text-generate-text-good font-bold mb-2 flex items-center gap-1">
          <ArrowDown className="generate-app-icon" /> Helping you
        </div>
        {strengths.length === 0 ? (
          <p className="text-xs text-generate-text-placeholder">None identified yet.</p>
        ) : (
          strengths.map((s) => (
            <PulseRow key={s.signal_key} impact={s} positive />
          ))
        )}
      </div>
      <div>
        <div className="text-xs text-generate-text-bad font-bold mb-2 flex items-center gap-1">
          <ArrowUp className="generate-app-icon" /> Hurting you
        </div>
        {drags.length === 0 ? (
          <p className="text-xs text-generate-text-placeholder">None — clean profile.</p>
        ) : (
          drags.map((d) => (
            <PulseRow key={d.signal_key} impact={d} positive={false} />
          ))
        )}
      </div>
    </div>
  );
}

function PulseRow({ impact, positive }: { impact: SignalImpact; positive: boolean }) {
  return (
    <div className="flex justify-between text-sm py-1">
      <span className="truncate">{impact.signal_label}</span>
      <span className={positive ? "text-generate-text-good font-bold" : "text-generate-text-bad font-bold"}>
        {positive ? "−" : "+"}{formatCurrency(Math.abs(impact.premium_delta_usd), 0)}
      </span>
    </div>
  );
}


function PeerBenchmarkCard({
  score, primary,
}: {
  score: ScoreResponse | null;
  primary: ClientCoverageEntry | null;
}) {
  if (!score || !primary) {
    return <p className="text-sm">No peer data yet.</p>;
  }
  const drags = score.impact_breakdown?.drags ?? [];
  const pct = primary.peer_percentile_rank;
  const topPeerDifferences = drags.slice(0, 3).map((d) => d.signal_label);

  return (
    <div className="space-y-3 py-2">
      <div>
        <span className="text-xs text-generate-text-placeholder">Your percentile rank</span>
        {pct != null ? (
          <ScoreBar
            value={pct}
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
        ) : (
          <p className="text-xs">Insufficient peers.</p>
        )}
      </div>
      <div>
        <span className="text-xs text-generate-text-placeholder">
          What top-decile peers have that you don't
        </span>
        {topPeerDifferences.length === 0 ? (
          <p className="text-sm mt-1">
            You match the top-decile profile on the signals we measure.
          </p>
        ) : (
          <ul className="text-sm mt-1 space-y-0.5">
            {topPeerDifferences.map((d, i) => (
              <li key={i} className="flex items-center gap-2">
                <span className="text-generate-text-bad">●</span>
                {d}
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}


function LossSnapshot() {
  return (
    <LabelValueList
      variant="card"
      rows={[
        { label: "Loss propensity",   value: <span className="text-generate-text-good">Low</span> },
        { label: "Frequency trend",   value: <span className="text-generate-text-good">Improving</span> },
        { label: "Severity trend",    value: <span className="text-generate-text-maybe">Stable</span> },
        { label: "Last 36mo claims",  value: <span className="text-generate-text-input font-bold">2</span> },
        { label: "Avg severity",      value: <span className="text-generate-text-input font-bold">$42k</span> },
      ]}
    />
  );
}

function ExposureSnapshot() {
  return (
    <LabelValueList
      variant="card"
      rows={[
        { label: "Magnitude",         value: <span className="text-generate-text-maybe">Mid-market</span> },
        { label: "Complexity",        value: <span className="text-generate-text-good">Moderate</span> },
        { label: "Geographic spread", value: <span className="text-generate-text-input font-bold">2 states</span> },
        { label: "CAT zone exposure", value: <span className="text-generate-text-good">Low</span> },
        { label: "Concentration",     value: <span className="text-generate-text-good">Diversified</span> },
      ]}
    />
  );
}


function CoverageSpread({ coverages }: { coverages: ClientCoverageEntry[] }) {
  if (coverages.length === 0) {
    return <p className="text-sm">No active coverages yet.</p>;
  }
  const aggregates = aggregateCoverages(coverages);
  return (
    <LabelValueList
      variant="card"
      rows={[
        { label: "Active policies",   value: coverages.length },
        { label: "Coverage lines",    value: aggregates.uniqueLines },
        { label: "Total premium",     value: <span className="font-bold">{formatCurrency(aggregates.totalPremium, 0)}</span> },
        { label: "Average score",     value: formatNumber(aggregates.avgScore, 0) },
        { label: "Highest tier",      value: aggregates.highestTier ?? "—" },
        { label: "Lowest tier",       value: aggregates.lowestTier ?? "—" },
      ]}
    />
  );
}


function aggregateCoverages(coverages: ClientCoverageEntry[]) {
  const scored = coverages.filter((c) => c.composite_score != null);
  const tiers = coverages.map((c) => c.tier).filter((t): t is number => t != null);
  return {
    totalPremium: coverages.reduce((a, c) => a + (c.recommended_premium ?? 0), 0),
    avgScore: scored.length
      ? scored.reduce((a, c) => a + (c.composite_score ?? 0), 0) / scored.length
      : 0,
    uniqueLines: new Set(coverages.map((c) => c.coverage)).size,
    highestTier: tiers.length ? Math.min(...tiers) : null,
    lowestTier: tiers.length ? Math.max(...tiers) : null,
  };
}


function LoadShell() {
  return (
    <ViewCanvas>
      <CardGrid cols="grid-cols-1">
        <StandardCard title="Loading" lucideIcon={Gauge}>
          <p className="text-sm">Fetching your overview…</p>
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

function ClientOnly() {
  return (
    <ViewCanvas>
      <CardGrid cols="grid-cols-1">
        <StandardCard title="Insured-only" lucideIcon={AlertTriangle}>
          <p className="text-sm">This view is for insured client users only.</p>
        </StandardCard>
      </CardGrid>
    </ViewCanvas>
  );
}

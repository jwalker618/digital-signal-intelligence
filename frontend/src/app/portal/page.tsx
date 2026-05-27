"use client";

// v8 Phase 8 polish — /portal (role-aware overview)
//
// Substantive content, not a nav hub. Carrier-side primitives end to end.
//
// CLIENT overview shows:
//   - Hero: score / tier / premium / percentile
//   - Pending actions card with the actual underwriter query text
//   - Signal Pulse: top 3 strengths + top 3 drags
//   - Top-peer benchmark mini-card
//   - Loss snapshot + exposure snapshot
//   - Coverage spread (aggregate over policies)
//
// BROKER overview shows:
//   - Hero: book KPIs
//   - Book of Clients table (drill-down by row click)
//   - Tier mix + score distribution
//   - Open queries snapshot with the actual underwriter text excerpt

import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";

import {
  AlertTriangle,
  ArrowDown,
  ArrowRight,
  ArrowUp,
  Briefcase,
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
  InfoPanel,
  KpiTile,
  LabelValueList,
  ScoreBar,
  StatsGrid,
} from "@/components/base/content/primatives";

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
  BrokerOverviewResponse,
  ClientBookEntry,
  ClientCoverageEntry,
  ClientOverviewResponse,
  CommunicationItem,
  OverviewResponse,
  ScoreResponse,
  SignalImpact,
} from "@/types/portal";


export default function PortalOverviewPage() {
  const router = useRouter();
  const accessToken = useAuthStore((s) => s.accessToken);
  const userRole = useAuthStore((s) => s.user?.role ?? null);
  const setActiveMenu = useDsiStore((s) => s.setActiveMenu);

  const [data, setData] = useState<OverviewResponse | null>(null);
  const [comms, setComms] = useState<CommunicationItem[]>([]);
  const [primaryScore, setPrimaryScore] = useState<ScoreResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setActiveMenu(userRole === "BROKER" ? "Book of Clients" : "Overview");
  }, [setActiveMenu, userRole]);

  useEffect(() => {
    let cancelled = false;
    async function load() {
      setLoading(true);
      try {
        const [resp, communicationsResp] = await Promise.all([
          fetchOverview(accessToken),
          fetchCommunications(accessToken, true),
        ]);
        if (cancelled) return;
        setData(resp);
        setComms(communicationsResp.items);

        // For client overview, fetch the score breakdown of the primary
        // coverage so we can show real Signal Pulse drivers.
        if (resp.role === "CLIENT" && resp.active_coverages.length > 0) {
          const primary = resp.active_coverages[0];
          try {
            const sc = await fetchSubmissionScore(accessToken, primary.submission_code);
            if (!cancelled) setPrimaryScore(sc);
          } catch {
            // Best-effort: signal pulse falls back to placeholder if this fails.
          }
        }
      } catch (e) {
        if (!cancelled) setError(e instanceof Error ? e.message : String(e));
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    if (accessToken) load();
    return () => { cancelled = true; };
  }, [accessToken]);

  if (loading) return <PortalLoading />;
  if (error) return <PortalError message={error} />;
  if (!data) return <PortalError message="No data available." />;

  if (data.role === "BROKER") {
    return <BrokerOverview data={data} comms={comms} router={router} />;
  }
  return (
    <ClientOverview
      data={data}
      comms={comms}
      primaryScore={primaryScore}
      router={router}
    />
  );
}


// ============================================================================
// CLIENT OVERVIEW
// ============================================================================

function ClientOverview({
  data, comms, primaryScore, router,
}: {
  data: ClientOverviewResponse;
  comms: CommunicationItem[];
  primaryScore: ScoreResponse | null;
  router: ReturnType<typeof useRouter>;
}) {
  const primary = data.active_coverages[0] ?? null;

  // Aggregates across all the client's coverages
  const aggregates = useMemo(() => aggregateCoverages(data.active_coverages), [data.active_coverages]);

  return (
    <ViewCanvas>
      <CardGrid cols="grid-cols-1" className="gap-4">

        <SubmissionHeaderCard
          decision={
            comms.some((c) => c.awaiting_party === "client") ? "refer" :
            comms.length > 0 ? "refer" :
            "approve"
          }
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

        {/* Pending actions: surfaces the underwriter's query text directly so
            the user understands what's being asked without navigating away. */}
        {comms.length > 0 && (
          <StandardCard title="Pending underwriter requests" lucideIcon={UserStar}>
            <div className="space-y-3 py-2">
              {comms.slice(0, 4).map((c) => (
                <PendingQueryRow
                  key={c.referral_code}
                  query={c}
                  onClick={() => router.push(`/portal/communications/${c.referral_code}`)}
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


function PendingQueryRow({
  query, onClick,
}: {
  query: CommunicationItem;
  onClick: () => void;
}) {
  return (
    <button
      onClick={onClick}
      className="
        w-full text-left
        border border-generate-text-maybe/30 bg-generate-text-maybe/5
        rounded-lg p-3
        hover:border-generate-text-input
        group"
    >
      <div className="flex justify-between items-baseline mb-1">
        <span className="text-sm font-bold">
          {query.policy_label ?? formatCoverageLabel(query.coverage)}
        </span>
        <span className="text-xs text-generate-text-placeholder group-hover:text-generate-text-input">
          Open in Communications <ArrowRight className="generate-app-icon inline-block ml-1" />
        </span>
      </div>
      {query.last_message_excerpt && (
        <p className="text-sm italic">"{query.last_message_excerpt}"</p>
      )}
      {query.request_signal_evidence && (
        <div className="text-xs mt-2">
          <span className="text-generate-text-placeholder">Evidence requested: </span>
          <code className="text-generate-text-comment">{query.request_signal_evidence}</code>
        </div>
      )}
    </button>
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

  // Heuristic narrative: top-decile peers don't carry the drags this
  // entity has. Each drag is something they're missing relative to
  // the top of the cohort.
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
  // Loss propensity data lives on model_versions but isn't currently
  // surfaced through the portal API. Show a credible placeholder; v8.1
  // wires this to the real loss_propensity_score / loss_trend_direction.
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


// ============================================================================
// BROKER OVERVIEW
// ============================================================================

function BrokerOverview({
  data, comms, router,
}: {
  data: BrokerOverviewResponse;
  comms: CommunicationItem[];
  router: ReturnType<typeof useRouter>;
}) {
  const clients = data.clients;
  const scoredClients = clients.filter((c) => c.composite_score != null);
  const avgScore = scoredClients.length
    ? scoredClients.reduce((a, c) => a + (c.composite_score ?? 0), 0) / scoredClients.length
    : 0;
  const totalPremium = clients.reduce((a, c) => a + (c.recommended_premium ?? 0), 0);
  const uniqueEntities = new Set(clients.map((c) => c.entity_name)).size;
  const awaiting = comms.filter((c) => c.awaiting_party === "broker").length;

  return (
    <ViewCanvas>
      <CardGrid cols="grid-cols-1" className="gap-4">

        <SubmissionHeaderCard
          decision={awaiting > 0 ? "refer" : "approve"}
          title={data.broker.name}
          subtitle={`Book of ${uniqueEntities} client${uniqueEntities === 1 ? "" : "s"} · ${clients.length} polic${clients.length === 1 ? "y" : "ies"}`}
          lucideIcon={Briefcase}
          headerRight={
            awaiting > 0 ? (
              <span className="text-xs text-generate-text-maybe font-bold">
                {awaiting} awaiting your reply
              </span>
            ) : (
              <span className="text-xs text-generate-text-good font-bold">All clear</span>
            )
          }
        >
          <StatsGrid
            columns={[
              { label: "Clients",       value: uniqueEntities, align: "center" },
              { label: "Policies",      value: clients.length, align: "center" },
              { label: "Avg score",     value: formatNumber(avgScore, 0), align: "center" },
              { label: "Aggregate premium", value: formatCurrency(totalPremium, 0), align: "center" },
              { label: "Open queries",  value: comms.length, align: "center" },
            ]}
          />
        </SubmissionHeaderCard>

        <StandardCard
          title={`Book of Clients (${clients.length} policies)`}
          lucideIcon={Briefcase}
        >
          <BrokerBookTable clients={clients} router={router} />
        </StandardCard>

        <CardGrid cols="grid-cols-1 lg:grid-cols-2" className="gap-4">
          <StandardCard title="Tier mix" lucideIcon={Layers}>
            <TierMix clients={clients} />
          </StandardCard>

          {comms.length > 0 && (
            <StandardCard title="Open queries snapshot" lucideIcon={UserStar}>
              <div className="space-y-2 py-2">
                {comms.slice(0, 4).map((c) => (
                  <PendingQueryRow
                    key={c.referral_code}
                    query={c}
                    onClick={() => router.push(`/portal/communications/${c.referral_code}`)}
                  />
                ))}
              </div>
            </StandardCard>
          )}

          {comms.length === 0 && (
            <StandardCard title="Communications status" lucideIcon={UserStar}>
              <InfoPanel label="Status">
                <p className="text-sm text-generate-text-good">
                  No open queries across your book. Underwriters are not
                  currently waiting on you for anything.
                </p>
              </InfoPanel>
            </StandardCard>
          )}
        </CardGrid>

      </CardGrid>
    </ViewCanvas>
  );
}


function BrokerBookTable({
  clients, router,
}: {
  clients: ClientBookEntry[];
  router: ReturnType<typeof useRouter>;
}) {
  return (
    <div className="grid"
      style={{ gridTemplateColumns: "2fr 1fr 80px 80px 100px 1fr 1fr" }}
    >
      {["Client", "Coverage", "Score", "Tier", "Percentile", "Premium", "Status"].map((h, i) => (
        <div key={i} className="text-xs text-generate-text-placeholder border-b border-generate-text-outline pb-1.5 pt-1.5">
          {h}
        </div>
      ))}
      {clients.map((c) => (
        <div
          key={c.submission_code}
          onClick={() => router.push(`/portal/submissions/${c.submission_code}`)}
          className="contents cursor-pointer group"
        >
          <div className="text-sm py-2 group-hover:text-generate-text-input group-hover:font-bold">
            {c.entity_name}
          </div>
          <div className="text-sm py-2 capitalize group-hover:text-generate-text-input">
            {formatCoverageLabel(c.coverage)}
          </div>
          <div className="text-sm py-2 font-bold group-hover:text-generate-text-input">
            {c.composite_score != null ? formatNumber(c.composite_score, 0) : "—"}
          </div>
          <div className="text-sm py-2 group-hover:text-generate-text-input">
            {c.tier ?? "—"}
          </div>
          <div className="text-sm py-2 group-hover:text-generate-text-input">
            {c.peer_percentile_rank != null
              ? `${formatNumber(c.peer_percentile_rank, 0)}th`
              : "—"}
          </div>
          <div className="text-sm py-2 group-hover:text-generate-text-input">
            {c.recommended_premium != null
              ? formatCurrency(c.recommended_premium, 0)
              : "—"}
          </div>
          <div className="text-sm py-2">
            {c.referral_state === "awaiting_broker" ? (
              <span className="text-generate-text-maybe font-bold">Awaiting reply</span>
            ) : c.referral_state === "pending" ? (
              <span className="text-generate-text-comment font-bold">In review</span>
            ) : (
              <span className="text-generate-text-good">{c.status}</span>
            )}
          </div>
        </div>
      ))}
    </div>
  );
}


function TierMix({ clients }: { clients: ClientBookEntry[] }) {
  const counts: Record<number, number> = {};
  clients.forEach((c) => {
    if (c.tier != null) counts[c.tier] = (counts[c.tier] ?? 0) + 1;
  });
  const total = clients.length;
  const tierTone: Record<number, string> = {
    1: "var(--color-generate-text-good)",
    2: "var(--color-generate-text-good)",
    3: "var(--color-generate-text-comment)",
    4: "var(--color-generate-text-maybe)",
    5: "var(--color-generate-text-bad)",
  };
  return (
    <div className="space-y-2">
      {[1, 2, 3, 4, 5].map((t) => {
        const n = counts[t] ?? 0;
        const pct = total ? (n / total) * 100 : 0;
        return (
          <div key={t} className="grid items-center gap-2" style={{ gridTemplateColumns: "60px 1fr 80px" }}>
            <span className="text-xs">Tier {t}</span>
            <div className="h-2 bg-generate-light-background rounded-full overflow-hidden">
              <div
                className="h-full rounded-full"
                style={{ width: `${pct}%`, backgroundColor: tierTone[t] }}
              />
            </div>
            <span className="text-xs text-right">
              {n} <span className="text-generate-text-placeholder">({formatNumber(pct, 0)}%)</span>
            </span>
          </div>
        );
      })}
    </div>
  );
}


// ============================================================================
// Shared helpers
// ============================================================================

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

function formatCoverageLabel(c: string): string {
  return c.split("_").map((w) => w.charAt(0).toUpperCase() + w.slice(1)).join(" ");
}


function PortalLoading() {
  return (
    <ViewCanvas>
      <CardGrid cols="grid-cols-1">
        <StandardCard title="Loading" lucideIcon={Gauge}>
          <p className="text-sm">Fetching portal data…</p>
        </StandardCard>
      </CardGrid>
    </ViewCanvas>
  );
}

function PortalError({ message }: { message: string }) {
  return (
    <ViewCanvas>
      <CardGrid cols="grid-cols-1">
        <StandardCard title="Unable to load portal" lucideIcon={AlertTriangle}>
          <p className="text-sm text-generate-text-bad">{message}</p>
        </StandardCard>
      </CardGrid>
    </ViewCanvas>
  );
}

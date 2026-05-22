"use client";

// v8 Phase 8 — /portal (role-aware overview)
//
// BROKER view: book-of-clients table with score / tier / percentile /
// premium / status, plus a headline metrics strip.
//
// CLIENT view: hero submission header card + headline KPIs + an inline
// signal-impact summary linking to the dedicated pages.
//
// Uses the carrier-side primitives end-to-end -- ViewCanvas, CardGrid,
// StandardCard, KpiTile, SubmissionHeaderCard -- so the chrome matches.

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";

import {
  AlertTriangle,
  Briefcase,
  ChartPie,
  Gauge,
  Inbox,
  Layers,
  Lightbulb,
  ListChecks,
  TrendingUpDown,
  UserStar,
} from "lucide-react";

import ViewCanvas from "@/components/ViewCanvas";
import {
  CardGrid,
  StandardCard,
  SubmissionHeaderCard,
} from "@/components/base/cards";
import {
  KpiTile,
  LabelValueList,
} from "@/components/base/content/primatives";

import { useAuthStore } from "@/store/authStore";
import { useDsiStore } from "@/store/dsiStore";
import { fetchOverview } from "@/lib/portalApi";
import { formatCurrency, formatNumber } from "@/lib/format";
import type {
  BrokerOverviewResponse,
  ClientBookEntry,
  ClientCoverageEntry,
  ClientOverviewResponse,
  OverviewResponse,
} from "@/types/portal";


export default function PortalOverviewPage() {
  const router = useRouter();
  const accessToken = useAuthStore((s) => s.accessToken);
  const userRole = useAuthStore((s) => s.user?.role ?? null);
  const setActiveMenu = useDsiStore((s) => s.setActiveMenu);

  const [data, setData] = useState<OverviewResponse | null>(null);
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
        const resp = await fetchOverview(accessToken);
        if (!cancelled) setData(resp);
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

  if (data.role === "BROKER") return <BrokerOverview data={data} router={router} />;
  return <ClientOverview data={data} router={router} />;
}


// ----------------------------------------------------------------------------
// Loading / error states (ViewCanvas-wrapped so chrome stays consistent)
// ----------------------------------------------------------------------------

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


// ============================================================================
// BROKER OVERVIEW
// ============================================================================

function BrokerOverview({
  data, router,
}: {
  data: BrokerOverviewResponse;
  router: ReturnType<typeof useRouter>;
}) {
  const clients = data.clients;

  // Portfolio aggregates -- computed once for the header strip.
  const totalPremium = clients.reduce(
    (acc, c) => acc + (c.recommended_premium ?? 0), 0,
  );
  const scoredClients = clients.filter((c) => c.composite_score != null);
  const avgScore = scoredClients.length
    ? scoredClients.reduce((a, c) => a + (c.composite_score ?? 0), 0) / scoredClients.length
    : 0;
  const referredClients = clients.filter(
    (c) => c.referral_state === "awaiting_broker" || c.referral_state === "pending",
  ).length;
  const avgPercentile = clients
    .map((c) => c.peer_percentile_rank)
    .filter((p): p is number => p != null);
  const avgPct = avgPercentile.length
    ? avgPercentile.reduce((a, b) => a + b, 0) / avgPercentile.length
    : null;

  return (
    <ViewCanvas>
      <CardGrid cols="grid-cols-1" className="gap-4">

        <SubmissionHeaderCard
          decision="approve"
          title={data.broker.name}
          subtitle={`Book of ${clients.length} client${clients.length === 1 ? "" : "s"}`}
          headerRight={
            <div className="flex items-center gap-2 text-sm">
              <Inbox className="generate-app-icon" />
              <span>{data.open_queries_count} open quer{data.open_queries_count === 1 ? "y" : "ies"}</span>
            </div>
          }
          lucideIcon={Briefcase}
        >
          <div className="grid grid-cols-2 md:grid-cols-4 gap-6 py-2">
            <KpiTile
              label="Clients in book"
              value={formatNumber(clients.length, 0)}
              lucideIcon={Briefcase}
            />
            <KpiTile
              label="Average signal score"
              value={formatNumber(avgScore, 0)}
              variant="emphasis"
              lucideIcon={Gauge}
            />
            <KpiTile
              label="Aggregate premium"
              value={formatCurrency(totalPremium, 0)}
              lucideIcon={ChartPie}
            />
            <KpiTile
              label="Awaiting your reply"
              value={referredClients}
              subtext={referredClients > 0 ? "Action required" : "All clear"}
              lucideIcon={UserStar}
            />
          </div>
        </SubmissionHeaderCard>

        <StandardCard
          title={`Book of Clients (${clients.length})`}
          lucideIcon={Briefcase}
          headerRight={
            avgPct != null ? (
              <span className="text-xs text-generate-text-placeholder">
                Average peer rank: {formatNumber(avgPct, 0)}th
              </span>
            ) : undefined
          }
        >
          {clients.length === 0 ? (
            <p className="text-sm">No clients in your book yet.</p>
          ) : (
            <BrokerBookTable clients={clients} router={router} />
          )}
        </StandardCard>

        <CardGrid cols="grid-cols-1 lg:grid-cols-2" className="gap-4">
          <StandardCard title="Tier distribution" lucideIcon={Layers}>
            <TierDistribution clients={clients} />
          </StandardCard>

          <StandardCard title="Quick actions" lucideIcon={TrendingUpDown}>
            <LabelValueList
              variant="card"
              rows={[
                {
                  label: "Review open queries",
                  value: (
                    <button
                      onClick={() => router.push("/portal/queries")}
                      className="text-sm font-bold underline hover:text-generate-text-input"
                    >
                      {data.open_queries_count} pending →
                    </button>
                  ),
                },
                {
                  label: "Portfolio metrics",
                  value: (
                    <button
                      onClick={() => router.push("/portal/portfolio")}
                      className="text-sm font-bold underline hover:text-generate-text-input"
                    >
                      View →
                    </button>
                  ),
                },
                {
                  label: "Market conditions",
                  value: (
                    <button
                      onClick={() => router.push("/portal/market")}
                      className="text-sm font-bold underline hover:text-generate-text-input"
                    >
                      View →
                    </button>
                  ),
                },
              ]}
            />
          </StandardCard>
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
      style={{
        gridTemplateColumns: "2fr 1fr 80px 80px 100px 1fr 1fr",
      }}
    >
      {/* Headers */}
      {["Client", "Coverage", "Score", "Tier", "Percentile", "Premium", "Status"].map((h, i) => (
        <div key={i} className="text-xs border-b-1 border-generate-text-outline pb-1.5 pt-1.5 text-left first:pl-0 text-generate-text-placeholder">
          {h}
        </div>
      ))}
      {/* Rows */}
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
            {c.coverage}
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

function TierDistribution({ clients }: { clients: ClientBookEntry[] }) {
  const counts: Record<number, number> = {};
  clients.forEach((c) => {
    if (c.tier != null) counts[c.tier] = (counts[c.tier] ?? 0) + 1;
  });
  const max = Math.max(1, ...Object.values(counts));
  const tierLabels: Record<number, string> = {
    1: "Tier 1 — Preferred",
    2: "Tier 2 — Preferred",
    3: "Tier 3 — Standard",
    4: "Tier 4 — Refer",
    5: "Tier 5 — Decline",
  };
  const rows = [1, 2, 3, 4, 5].map((t) => ({
    label: tierLabels[t],
    count: counts[t] ?? 0,
  }));
  return (
    <div className="space-y-2">
      {rows.map((r) => (
        <div key={r.label} className="grid items-center gap-2"
          style={{ gridTemplateColumns: "1fr 80px" }}
        >
          <div className="flex items-center gap-2">
            <span className="text-xs w-40 truncate">{r.label}</span>
            <div className="flex-1 h-1.5 bg-generate-light-background rounded-full overflow-hidden">
              <div
                className="h-full rounded-full"
                style={{
                  width: `${(r.count / max) * 100}%`,
                  backgroundColor: "var(--color-generate-text-outline)",
                }}
              />
            </div>
          </div>
          <span className="text-xs font-bold text-right">{r.count}</span>
        </div>
      ))}
    </div>
  );
}


// ============================================================================
// CLIENT OVERVIEW
// ============================================================================

function ClientOverview({
  data, router,
}: {
  data: ClientOverviewResponse;
  router: ReturnType<typeof useRouter>;
}) {
  const primary = data.active_coverages[0] ?? null;

  return (
    <ViewCanvas>
      <CardGrid cols="grid-cols-1" className="gap-4">

        <SubmissionHeaderCard
          decision={primary?.referral_state === "awaiting_broker" ? "refer" : "approve"}
          title={data.entity_name}
          subtitle={
            data.broker
              ? `Placed by ${data.broker.name}`
              : "No broker assigned"
          }
          headerRight={
            primary?.referral_state === "awaiting_broker" ? (
              <span className="text-sm text-generate-text-maybe font-bold">
                Awaiting broker reply
              </span>
            ) : undefined
          }
          lucideIcon={Gauge}
        >
          {primary ? (
            <div className="grid grid-cols-2 md:grid-cols-4 gap-6 py-2">
              <KpiTile
                label="Signal score"
                value={formatNumber(primary.composite_score ?? 0, 0)}
                variant="emphasis"
                lucideIcon={Gauge}
              />
              <KpiTile
                label="Tier"
                value={primary.tier ?? "—"}
                subtext={tierSubtext(primary.tier)}
                lucideIcon={Layers}
              />
              <KpiTile
                label="Peer percentile"
                value={
                  primary.peer_percentile_rank != null
                    ? `${formatNumber(primary.peer_percentile_rank, 0)}th`
                    : "—"
                }
                subtext={pctSubtext(primary.peer_percentile_rank)}
                lucideIcon={TrendingUpDown}
              />
              <KpiTile
                label="Premium"
                value={
                  primary.recommended_premium != null
                    ? formatCurrency(primary.recommended_premium, 0)
                    : "—"
                }
                lucideIcon={ChartPie}
              />
            </div>
          ) : (
            <p className="text-sm py-2">No active coverages yet.</p>
          )}
        </SubmissionHeaderCard>

        <StandardCard
          title="Active Coverages"
          lucideIcon={Layers}
        >
          {data.active_coverages.length === 0 ? (
            <p className="text-sm">No active coverages yet.</p>
          ) : (
            <ClientCoverageList
              coverages={data.active_coverages}
              router={router}
            />
          )}
        </StandardCard>

        <CardGrid cols="grid-cols-1 md:grid-cols-3" className="gap-4">
          <PortalLinkCard
            title="Signal Drivers"
            icon={ListChecks}
            description="See what's helping and hurting your score — positive drivers, negative drivers, and the dollar impact of each."
            onClick={() => router.push("/portal/drivers")}
          />
          <PortalLinkCard
            title="Peer Comparison"
            icon={TrendingUpDown}
            description="How you compare to similar companies in your cohort — score distribution, top-3 strengths, top-3 weaknesses."
            onClick={() => router.push("/portal/peers")}
          />
          <PortalLinkCard
            title="Action Plan"
            icon={Lightbulb}
            description="Prioritised actions to improve your score, sorted by leverage. Effort, cost, and expected premium impact for each."
            onClick={() => router.push("/portal/actions")}
          />
        </CardGrid>

      </CardGrid>
    </ViewCanvas>
  );
}

function tierSubtext(tier?: number | null): string | undefined {
  if (tier == null) return undefined;
  if (tier <= 2) return "Preferred";
  if (tier === 3) return "Standard";
  if (tier === 4) return "Referred for underwriter review";
  return "Decline risk";
}

function pctSubtext(pct?: number | null): string | undefined {
  if (pct == null) return undefined;
  if (pct >= 75) return "Top quartile of peers";
  if (pct >= 50) return "Above median";
  if (pct >= 25) return "Below median";
  return "Bottom quartile";
}

function ClientCoverageList({
  coverages, router,
}: {
  coverages: ClientCoverageEntry[];
  router: ReturnType<typeof useRouter>;
}) {
  return (
    <div className="space-y-2">
      {coverages.map((c) => (
        <button
          key={c.submission_code}
          onClick={() => router.push(`/portal/submissions/${c.submission_code}`)}
          className="w-full grid items-center gap-4 text-left py-2 border-b-1 border-generate-text-outline hover:text-generate-text-input"
          style={{ gridTemplateColumns: "1fr 80px 80px 100px 1fr" }}
        >
          <span className="text-sm capitalize font-bold">{c.coverage}</span>
          <span className="text-sm">
            Score {c.composite_score != null ? formatNumber(c.composite_score, 0) : "—"}
          </span>
          <span className="text-sm">
            Tier {c.tier ?? "—"}
          </span>
          <span className="text-sm">
            {c.peer_percentile_rank != null
              ? `${formatNumber(c.peer_percentile_rank, 0)}th`
              : "—"}
          </span>
          <span className="text-sm text-right">
            {c.recommended_premium != null
              ? formatCurrency(c.recommended_premium, 0)
              : "—"}
          </span>
        </button>
      ))}
    </div>
  );
}

function PortalLinkCard({
  title, description, onClick, icon: Icon,
}: {
  title: string;
  description: string;
  onClick: () => void;
  icon: typeof Gauge;
}) {
  return (
    <button
      onClick={onClick}
      className="text-left group h-full"
    >
      <StandardCard title={title} lucideIcon={Icon}>
        <p className="text-sm py-2 group-hover:text-generate-text-input">
          {description}
        </p>
        <span className="text-xs font-bold underline group-hover:text-generate-text-input">
          Open →
        </span>
      </StandardCard>
    </button>
  );
}

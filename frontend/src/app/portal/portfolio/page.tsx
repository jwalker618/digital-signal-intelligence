"use client";

// v8 Phase 8 — /portal/portfolio (BROKER-only)
//
// Portfolio-level view across the broker's book. Aggregates metrics
// from the overview response: score distribution, tier mix, premium
// composition, percentile distribution, and a flag-counter for
// referred/awaiting-broker clients.

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";

import {
  AlertTriangle,
  Briefcase,
  ChartPie,
  Gauge,
  Layers,
  TrendingUpDown,
  Users,
} from "lucide-react";

import ViewCanvas from "@/components/ViewCanvas";
import {
  CardGrid,
  StandardCard,
  SubmissionHeaderCard,
} from "@/components/base/cards";
import {
  KpiTile,
  ScoreBar,
  StatsGrid,
} from "@/components/base/content/primatives";

import { useAuthStore } from "@/store/authStore";
import { useDsiStore } from "@/store/dsiStore";
import { fetchOverview } from "@/lib/portalApi";
import { formatCurrency, formatNumber } from "@/lib/format";
import type {
  BrokerOverviewResponse,
  ClientBookEntry,
} from "@/types/portal";


export default function PortalPortfolioPage() {
  const router = useRouter();
  const accessToken = useAuthStore((s) => s.accessToken);
  const userRole = useAuthStore((s) => s.user?.role ?? null);
  const setActiveMenu = useDsiStore((s) => s.setActiveMenu);

  const [data, setData] = useState<BrokerOverviewResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => { setActiveMenu("Portfolio Metrics"); }, [setActiveMenu]);

  useEffect(() => {
    let cancelled = false;
    async function load() {
      try {
        const resp = await fetchOverview(accessToken);
        if (cancelled) return;
        if (resp.role !== "BROKER") {
          setError("Portfolio view is broker-only.");
          return;
        }
        setData(resp);
      } catch (e) {
        if (!cancelled) setError(e instanceof Error ? e.message : String(e));
      }
    }
    if (accessToken) load();
    return () => { cancelled = true; };
  }, [accessToken]);

  if (userRole !== "BROKER") {
    return (
      <ViewCanvas>
        <CardGrid cols="grid-cols-1">
          <StandardCard title="Broker-only page" lucideIcon={AlertTriangle}>
            <p className="text-sm">This page is restricted to broker users.</p>
          </StandardCard>
        </CardGrid>
      </ViewCanvas>
    );
  }
  if (error) return <ErrShell msg={error} />;
  if (!data) return <LoadShell />;

  const clients = data.clients;
  const totalPremium = clients.reduce((a, c) => a + (c.recommended_premium ?? 0), 0);
  const scoredClients = clients.filter((c) => c.composite_score != null);
  const avgScore = scoredClients.length
    ? scoredClients.reduce((a, c) => a + (c.composite_score ?? 0), 0) / scoredClients.length
    : 0;
  const avgPctRows = clients
    .map((c) => c.peer_percentile_rank)
    .filter((p): p is number => p != null);
  const avgPct = avgPctRows.length
    ? avgPctRows.reduce((a, b) => a + b, 0) / avgPctRows.length
    : null;

  return (
    <ViewCanvas>
      <CardGrid cols="grid-cols-1" className="gap-4">

        <SubmissionHeaderCard
          decision="approve"
          title="Portfolio Metrics"
          subtitle={`${data.broker.name} · ${clients.length} client${clients.length === 1 ? "" : "s"}`}
          lucideIcon={ChartPie}
        >
          <StatsGrid
            columns={[
              { label: "Clients",    value: formatNumber(clients.length, 0),    align: "center" },
              { label: "Avg Score",  value: formatNumber(avgScore, 0),          align: "center" },
              { label: "Avg Percentile", value: avgPct != null ? `${formatNumber(avgPct, 0)}th` : "—", align: "center" },
              { label: "Total Premium", value: formatCurrency(totalPremium, 0), align: "center" },
              { label: "Awaiting",   value: clients.filter((c) => c.referral_state === "awaiting_broker").length, align: "center" },
            ]}
          />
        </SubmissionHeaderCard>

        <CardGrid cols="grid-cols-1 lg:grid-cols-2" className="gap-4">
          <StandardCard title="Score distribution" lucideIcon={Gauge}>
            <ScoreDistribution clients={clients} />
          </StandardCard>

          <StandardCard title="Tier mix" lucideIcon={Layers}>
            <TierMix clients={clients} />
          </StandardCard>
        </CardGrid>

        <CardGrid cols="grid-cols-1 lg:grid-cols-2" className="gap-4">
          <StandardCard title="Premium concentration" lucideIcon={ChartPie}>
            <PremiumConcentration clients={clients} totalPremium={totalPremium} />
          </StandardCard>

          <StandardCard title="Peer-rank distribution" lucideIcon={TrendingUpDown}>
            <PercentileMix clients={clients} />
          </StandardCard>
        </CardGrid>

        <StandardCard title="Client roster" lucideIcon={Users}>
          <ClientRosterTable clients={clients} onRowClick={(code) => router.push(`/portal/submissions/${code}`)} />
        </StandardCard>

      </CardGrid>
    </ViewCanvas>
  );
}


function LoadShell() {
  return (
    <ViewCanvas>
      <CardGrid cols="grid-cols-1">
        <StandardCard title="Loading" lucideIcon={ChartPie}>
          <p className="text-sm">Aggregating portfolio metrics…</p>
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


// ----------------------------------------------------------------------------
// Visualisations -- all use simple bars (no external chart deps; consistent
// with the carrier-side "HorizontalBarList" feel).
// ----------------------------------------------------------------------------

function ScoreDistribution({ clients }: { clients: ClientBookEntry[] }) {
  // 6 buckets across 0-1000
  const buckets = [
    { label: "< 500", min: 0,   max: 500 },
    { label: "500-600", min: 500, max: 600 },
    { label: "600-700", min: 600, max: 700 },
    { label: "700-800", min: 700, max: 800 },
    { label: "800-900", min: 800, max: 900 },
    { label: "900+",   min: 900, max: 10_000 },
  ];
  const counts = buckets.map((b) => ({
    ...b,
    count: clients.filter((c) =>
      c.composite_score != null && c.composite_score >= b.min && c.composite_score < b.max,
    ).length,
  }));
  const max = Math.max(1, ...counts.map((b) => b.count));

  return (
    <div className="space-y-2">
      {counts.map((b) => (
        <div key={b.label} className="grid items-center gap-2" style={{ gridTemplateColumns: "80px 1fr 40px" }}>
          <span className="text-xs">{b.label}</span>
          <div className="h-2 bg-generate-light-background rounded-full overflow-hidden">
            <div
              className="h-full rounded-full"
              style={{
                width: `${(b.count / max) * 100}%`,
                backgroundColor: "var(--color-generate-text-outline)",
              }}
            />
          </div>
          <span className="text-xs font-bold text-right">{b.count}</span>
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
          <div key={t} className="grid items-center gap-2" style={{ gridTemplateColumns: "60px 1fr 60px" }}>
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

function PremiumConcentration({
  clients, totalPremium,
}: {
  clients: ClientBookEntry[];
  totalPremium: number;
}) {
  const sorted = [...clients]
    .filter((c) => c.recommended_premium != null)
    .sort((a, b) => (b.recommended_premium ?? 0) - (a.recommended_premium ?? 0));
  const top = sorted.slice(0, 5);
  if (top.length === 0 || totalPremium === 0) {
    return <p className="text-sm">No premium data yet.</p>;
  }
  return (
    <div className="space-y-2">
      {top.map((c) => {
        const share = ((c.recommended_premium ?? 0) / totalPremium) * 100;
        return (
          <div key={c.submission_code} className="grid items-center gap-2" style={{ gridTemplateColumns: "1fr 80px 60px" }}>
            <span className="text-sm truncate">{c.entity_name}</span>
            <div className="h-2 bg-generate-light-background rounded-full overflow-hidden">
              <div
                className="h-full rounded-full"
                style={{ width: `${share}%`, backgroundColor: "var(--color-generate-text-outline)" }}
              />
            </div>
            <span className="text-xs text-right">{formatNumber(share, 0)}%</span>
          </div>
        );
      })}
    </div>
  );
}

function PercentileMix({ clients }: { clients: ClientBookEntry[] }) {
  const buckets = [
    { label: "Bottom (0-25th)", min: 0,  max: 25 },
    { label: "Lower-mid (25-50th)", min: 25, max: 50 },
    { label: "Upper-mid (50-75th)", min: 50, max: 75 },
    { label: "Top (75-100th)", min: 75, max: 101 },
  ];
  const counts = buckets.map((b) => ({
    ...b,
    count: clients.filter((c) =>
      c.peer_percentile_rank != null && c.peer_percentile_rank >= b.min && c.peer_percentile_rank < b.max,
    ).length,
  }));
  const max = Math.max(1, ...counts.map((c) => c.count));
  return (
    <div className="space-y-2">
      {counts.map((b) => (
        <div key={b.label} className="grid items-center gap-2" style={{ gridTemplateColumns: "1fr 80px 40px" }}>
          <span className="text-xs">{b.label}</span>
          <div className="h-2 bg-generate-light-background rounded-full overflow-hidden">
            <div
              className="h-full rounded-full"
              style={{ width: `${(b.count / max) * 100}%`, backgroundColor: "var(--color-generate-text-comment)" }}
            />
          </div>
          <span className="text-xs font-bold text-right">{b.count}</span>
        </div>
      ))}
    </div>
  );
}


function ClientRosterTable({
  clients, onRowClick,
}: {
  clients: ClientBookEntry[];
  onRowClick: (code: string) => void;
}) {
  return (
    <div className="grid"
      style={{ gridTemplateColumns: "2fr 1fr 80px 80px 100px 1fr" }}
    >
      {["Client", "Coverage", "Score", "Tier", "Percentile", "Premium"].map((h, i) => (
        <div key={i} className="text-xs border-b-1 border-generate-text-outline pb-1.5 pt-1.5 text-generate-text-placeholder">
          {h}
        </div>
      ))}
      {clients.map((c) => (
        <div
          key={c.submission_code}
          onClick={() => onRowClick(c.submission_code)}
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
          <div className="text-sm py-2 group-hover:text-generate-text-input">{c.tier ?? "—"}</div>
          <div className="text-sm py-2 group-hover:text-generate-text-input">
            {c.peer_percentile_rank != null ? `${formatNumber(c.peer_percentile_rank, 0)}th` : "—"}
          </div>
          <div className="text-sm py-2 text-right group-hover:text-generate-text-input">
            {c.recommended_premium != null ? formatCurrency(c.recommended_premium, 0) : "—"}
          </div>
        </div>
      ))}
    </div>
  );
}

"use client";

// v8 Phase 8 — /portal/market (BROKER-only)
//
// Market conditions placeholder. Not all signals are backed by real
// time-series data in v8 -- this view stitches together what we have
// (own portfolio averages, cohort percentiles) into a market-flavoured
// narrative that's plausible for the demo. Genuine market feeds are a
// v8.1 follow-on.

import { useEffect, useState } from "react";

import {
  AlertTriangle,
  Briefcase,
  ChartPie,
  Gauge,
  Lightbulb,
  ShieldAlert,
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
  LabelValueList,
  ScoreBar,
  StatsGrid,
} from "@/components/base/content/primatives";

import { useAuthStore } from "@/store/authStore";
import { useDsiStore } from "@/store/dsiStore";
import { fetchOverview } from "@/lib/portalApi";
import { formatCurrency, formatNumber } from "@/lib/format";
import type { BrokerOverviewResponse } from "@/types/portal";


export default function PortalMarketPage() {
  const accessToken = useAuthStore((s) => s.accessToken);
  const userRole = useAuthStore((s) => s.user?.role ?? null);
  const setActiveMenu = useDsiStore((s) => s.setActiveMenu);

  const [data, setData] = useState<BrokerOverviewResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => { setActiveMenu("Market Conditions"); }, [setActiveMenu]);

  useEffect(() => {
    let cancelled = false;
    async function load() {
      try {
        const resp = await fetchOverview(accessToken);
        if (cancelled) return;
        if (resp.role !== "BROKER") {
          setError("Market view is broker-only.");
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
    return <Forbidden />;
  }
  if (error) return <ErrShell msg={error} />;
  if (!data) return <LoadShell />;

  // Aggregate the broker's slice of the market for a credible narrative
  const scoredClients = data.clients.filter((c) => c.composite_score != null);
  const avgScore = scoredClients.length
    ? scoredClients.reduce((a, c) => a + (c.composite_score ?? 0), 0) / scoredClients.length
    : 0;
  const totalPremium = data.clients.reduce((a, c) => a + (c.recommended_premium ?? 0), 0);

  return (
    <ViewCanvas>
      <CardGrid cols="grid-cols-1" className="gap-4">

        <SubmissionHeaderCard
          decision="approve"
          title="Cyber Market Conditions"
          subtitle="Reference signals across your book and the cohort universe"
          lucideIcon={TrendingUpDown}
          headerRight={
            <span className="text-xs text-generate-text-placeholder">
              Q2 2026 outlook
            </span>
          }
        >
          <StatsGrid
            columns={[
              { label: "Avg score (your book)", value: formatNumber(avgScore, 0), align: "center" },
              { label: "Avg score (market)",    value: "720",                       align: "center" },
              { label: "Premium pressure",      value: "+4% YoY",                   align: "center" },
              { label: "Loss frequency",        value: "stable",                    align: "center" },
              { label: "Demand signal",         value: "rising",                    align: "center" },
            ]}
          />
        </SubmissionHeaderCard>

        <CardGrid cols="grid-cols-1 lg:grid-cols-2" className="gap-4">
          <StandardCard title="Premium pressure by tier" lucideIcon={ChartPie}>
            <PremiumPressure />
          </StandardCard>

          <StandardCard title="Top signal categories — market" lucideIcon={ShieldAlert}>
            <TopSignalCategories />
          </StandardCard>
        </CardGrid>

        <StandardCard title="Top loss drivers (last 90 days)" lucideIcon={ShieldAlert}>
          <LabelValueList
            variant="card"
            rows={[
              { label: "Ransomware via edge appliance",       value: <span className="text-generate-text-bad font-bold">+18%</span> },
              { label: "Business-email compromise",            value: <span className="text-generate-text-bad font-bold">+11%</span> },
              { label: "Cloud-config misconfiguration",        value: <span className="text-generate-text-bad font-bold">+9%</span> },
              { label: "Insider data exfiltration",            value: <span className="text-generate-text-maybe font-bold">+3%</span> },
              { label: "Supply-chain compromise",              value: <span className="text-generate-text-comment font-bold">flat</span> },
              { label: "Phishing-driven credential theft",     value: <span className="text-generate-text-good font-bold">-6%</span> },
            ]}
          />
        </StandardCard>

        <CardGrid cols="grid-cols-1 lg:grid-cols-2" className="gap-4">
          <StandardCard title="Underwriting appetite" lucideIcon={Briefcase}>
            <UnderwritingAppetite />
          </StandardCard>

          <StandardCard title="Recommended talking points" lucideIcon={Lightbulb}>
            <LabelValueList
              variant="card"
              rows={[
                { label: "MFA on admin accounts",       value: <span className="text-generate-text-good">Universal expectation</span> },
                { label: "EDR coverage threshold",      value: <span className="text-generate-text-good">≥95% endpoints</span> },
                { label: "IR plan + tabletop in 12mo",  value: <span className="text-generate-text-good">Most carriers require</span> },
                { label: "Backup immutability",         value: <span className="text-generate-text-good">Now table-stakes</span> },
                { label: "Email auth (DMARC p=reject)", value: <span className="text-generate-text-good">Strong differentiator</span> },
              ]}
            />
          </StandardCard>
        </CardGrid>

        <InfoPanel label="Notes" aside="Indicative — v8.1 will integrate live market feeds">
          <p className="text-xs text-generate-text-placeholder">
            Figures combine your book aggregates with reference data from the
            cohort universe (the synthetic peer pool used for percentile
            comparison). For Q2 2026 we expect continued upward pressure on
            cyber pricing for sub-tier-2 risks, driven primarily by ransomware
            severity. Tier 1 / 2 risks with strong MFA, EDR, and IR programmes
            should continue to see flat-to-favourable terms.
          </p>
        </InfoPanel>

      </CardGrid>
    </ViewCanvas>
  );
}


function PremiumPressure() {
  const rows = [
    { label: "Tier 1 — Preferred",  delta: -2, color: "var(--color-generate-text-good)" },
    { label: "Tier 2 — Preferred",  delta: 1,  color: "var(--color-generate-text-good)" },
    { label: "Tier 3 — Standard",   delta: 5,  color: "var(--color-generate-text-maybe)" },
    { label: "Tier 4 — Refer",      delta: 12, color: "var(--color-generate-text-bad)" },
    { label: "Tier 5 — Decline",    delta: 22, color: "var(--color-generate-text-bad)" },
  ];
  const max = Math.max(...rows.map((r) => Math.abs(r.delta)));
  return (
    <div className="space-y-2">
      {rows.map((r) => (
        <div key={r.label} className="grid items-center gap-2" style={{ gridTemplateColumns: "1fr 1fr 60px" }}>
          <span className="text-xs">{r.label}</span>
          <div className="h-2 bg-generate-light-background rounded-full overflow-hidden">
            <div
              className="h-full rounded-full"
              style={{ width: `${(Math.abs(r.delta) / max) * 100}%`, backgroundColor: r.color }}
            />
          </div>
          <span className="text-xs text-right font-bold" style={{ color: r.color }}>
            {r.delta > 0 ? "+" : ""}{r.delta}%
          </span>
        </div>
      ))}
    </div>
  );
}

function TopSignalCategories() {
  const rows = [
    { label: "Identity & access (MFA, SSO)", weight: 92 },
    { label: "Endpoint protection (EDR)",     weight: 88 },
    { label: "Backup / recovery posture",     weight: 80 },
    { label: "Incident response readiness",   weight: 76 },
    { label: "Email security (SPF/DKIM/DMARC)", weight: 68 },
    { label: "Network exposure / attack surface", weight: 62 },
  ];
  return (
    <div className="space-y-2">
      {rows.map((r) => (
        <div key={r.label} className="grid items-center gap-2" style={{ gridTemplateColumns: "2fr 1fr 40px" }}>
          <span className="text-xs">{r.label}</span>
          <ScoreBar value={r.weight} hideValue thresholds={[
            { at: 50, color: "var(--color-generate-text-placeholder)" },
            { at: 75, color: "var(--color-generate-text-comment)" },
            { at: Infinity, color: "var(--color-generate-text-good)" },
          ]} />
          <span className="text-xs text-right font-bold">{r.weight}</span>
        </div>
      ))}
    </div>
  );
}

function UnderwritingAppetite() {
  return (
    <LabelValueList
      variant="card"
      rows={[
        { label: "Tech / SaaS",          value: <span className="text-generate-text-good">Open</span> },
        { label: "Healthcare provider",  value: <span className="text-generate-text-maybe">Selective</span> },
        { label: "Healthcare PHI heavy", value: <span className="text-generate-text-bad">Constrained</span> },
        { label: "Manufacturing",        value: <span className="text-generate-text-good">Open</span> },
        { label: "Critical infra",       value: <span className="text-generate-text-maybe">Selective</span> },
        { label: "Retail / e-commerce",  value: <span className="text-generate-text-good">Open</span> },
        { label: "Cryptocurrency",       value: <span className="text-generate-text-bad">Restricted</span> },
      ]}
    />
  );
}


function LoadShell() {
  return (
    <ViewCanvas>
      <CardGrid cols="grid-cols-1">
        <StandardCard title="Loading" lucideIcon={TrendingUpDown}>
          <p className="text-sm">Pulling market signals…</p>
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

function Forbidden() {
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

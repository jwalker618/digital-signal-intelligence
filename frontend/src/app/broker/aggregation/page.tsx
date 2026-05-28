"use client";

// v8.2 Risk Aggregation — /broker/aggregation
//
// Sentrisk-flavoured book-level concentration analysis:
//   - Industry + line concentration cards (top-share, count, share %)
//   - CAT peril exposure (6 perils -> book share, top verticals)
//   - Diversification score with narrative

import { useEffect, useState } from "react";
import {
  AlertTriangle,
  Cloud,
  CloudOff,
  Flame,
  Network,
  ShieldAlert,
  Activity,
  Layers,
} from "lucide-react";

import ViewCanvas from "@/components/ViewCanvas";
import VerticalFilter from "@/components/broker/VerticalFilter";
import {
  CardGrid,
  StandardCard,
  SubmissionHeaderCard,
} from "@/components/base/cards";
import {
  InfoPanel,
  KpiTile,
  NoData,
  ScoreBar,
  StatsGrid,
} from "@/components/base/content/primatives";

import { useAuthStore } from "@/store/authStore";
import { useDsiStore } from "@/store/dsiStore";
import { fetchAggregation } from "@/lib/portalApi";
import { formatCurrency, formatNumber } from "@/lib/format";
import type {
  AggregationResponse,
  CatPerilExposure,
  ConcentrationEntry,
} from "@/types/portal";


const PERIL_ICONS: Record<string, typeof Cloud> = {
  "atlantic-hurricane": Cloud,
  "wildfire": Flame,
  "earthquake-cascadia": Activity,
  "cyber-ransomware-wave": ShieldAlert,
  "cloud-outage": CloudOff,
  "supply-chain-disruption": Network,
};


export default function AggregationPage() {
  const accessToken = useAuthStore((s) => s.accessToken);
  const userRole = useAuthStore((s) => s.user?.role ?? null);
  const setActiveMenu = useDsiStore((s) => s.setActiveMenu);

  const [data, setData] = useState<AggregationResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [selectedPeril, setSelectedPeril] = useState<string | null>(null);

  useEffect(() => { setActiveMenu("Risk Aggregation"); }, [setActiveMenu]);

  useEffect(() => {
    let cancelled = false;
    async function load() {
      try {
        const resp = await fetchAggregation(accessToken);
        if (!cancelled) setData(resp);
      } catch (e) {
        if (!cancelled) setError(e instanceof Error ? e.message : String(e));
      }
    }
    if (accessToken && userRole === "BROKER") load();
    return () => { cancelled = true; };
  }, [accessToken, userRole]);

  if (userRole !== "BROKER") return <BrokerOnly />;
  if (error) return <ErrShell msg={error} />;
  if (!data) return <LoadShell />;

  const activePeril = data.cat_peril_exposure.find((p) => p.peril_slug === selectedPeril);

  return (
    <ViewCanvas>
      <CardGrid cols="grid-cols-1" className="gap-4">

        <SubmissionHeaderCard
          decision={data.diversification_score >= 75 ? "approve" : "refer"}
          title="Risk Aggregation"
          subtitle="Where your book concentrates — and how a peril event would propagate"
          lucideIcon={Network}
        >
          <StatsGrid
            columns={[
              { label: "Total premium", value: formatCurrency(data.total_premium_usd, 0), align: "center" },
              { label: "Industries", value: data.industry_concentration.length, align: "center" },
              { label: "Lines", value: data.line_concentration.length, align: "center" },
              { label: "Perils watched", value: data.cat_peril_exposure.length, align: "center" },
              { label: "Diversification", value: `${data.diversification_score}/100`, align: "center" },
            ]}
          />
        </SubmissionHeaderCard>

        <VerticalFilter />

        <StandardCard
          title="Diversification"
          lucideIcon={Layers}
          headerRight={
            <span className="text-xs text-generate-text-placeholder">
              Composite score 0-100
            </span>
          }
        >
          <div className="space-y-3 py-2">
            <ScoreBar
              value={data.diversification_score}
              min={0}
              max={100}
              decimals={0}
              thresholds={[
                { at: 30, color: "var(--color-generate-text-bad)" },
                { at: 50, color: "var(--color-generate-text-maybe)" },
                { at: 75, color: "var(--color-generate-text-comment)" },
                { at: Infinity, color: "var(--color-generate-text-good)" },
              ]}
            />
            <p className="text-sm">{data.diversification_note}</p>
          </div>
        </StandardCard>

        <CardGrid cols="grid-cols-1 lg:grid-cols-2" className="gap-4">
          <StandardCard title="Industry concentration" lucideIcon={Layers}>
            <ConcentrationList entries={data.industry_concentration} />
          </StandardCard>

          <StandardCard title="Coverage-line concentration" lucideIcon={Layers}>
            <ConcentrationList entries={data.line_concentration} />
          </StandardCard>
        </CardGrid>

        <StandardCard
          title="CAT peril exposure"
          lucideIcon={ShieldAlert}
          headerRight={
            <span className="text-xs text-generate-text-placeholder">
              Click a peril for the impact narrative
            </span>
          }
        >
          <CardGrid cols="grid-cols-2 md:grid-cols-3" className="gap-3">
            {data.cat_peril_exposure.map((p) => (
              <PerilCard
                key={p.peril_slug}
                exposure={p}
                active={selectedPeril === p.peril_slug}
                onClick={() => setSelectedPeril(p.peril_slug === selectedPeril ? null : p.peril_slug)}
              />
            ))}
          </CardGrid>

          {activePeril && (
            <div className="mt-4 border-t-2 border-generate-text-comment/30 pt-4">
              <PerilNarrative exposure={activePeril} totalPremium={data.total_premium_usd} />
            </div>
          )}
        </StandardCard>

        <InfoPanel label="Sentrisk-flavoured" aside="v8.2 demo">
          <p className="text-xs">
            CAT peril impact is computed by multiplying each policy's
            premium by a per-(vertical, peril) exposure factor.
            Diversification blends industry-share concentration, line-
            share concentration, and the number of distinct
            verticals / lines present. Production wires real CAT
            modelling, geographic footprint, and per-policy peril
            attribution.
          </p>
        </InfoPanel>

      </CardGrid>
    </ViewCanvas>
  );
}


function ConcentrationList({ entries }: { entries: ConcentrationEntry[] }) {
  if (entries.length === 0) {
    return <NoData message="No data yet." />;
  }
  return (
    <div className="space-y-2 py-2">
      {entries.map((e) => (
        <div
          key={e.value}
          className="grid items-center gap-3"
          style={{ gridTemplateColumns: "1fr 100px 80px" }}
        >
          <div>
            <div className="text-sm font-bold">{e.value}</div>
            {e.note && (
              <div className="text-xs text-generate-text-bad mt-0.5">{e.note}</div>
            )}
          </div>
          <div>
            <ScoreBar
              value={e.share_pct}
              min={0}
              max={100}
              decimals={0}
              hideValue
              thresholds={[
                { at: 25, color: "var(--color-generate-text-good)" },
                { at: 50, color: "var(--color-generate-text-comment)" },
                { at: 70, color: "var(--color-generate-text-maybe)" },
                { at: Infinity, color: "var(--color-generate-text-bad)" },
              ]}
            />
          </div>
          <div className="text-right text-sm">
            <span className="font-bold">{e.share_pct.toFixed(0)}%</span>
            <span className="text-xs text-generate-text-placeholder ml-1">
              ({e.count})
            </span>
          </div>
        </div>
      ))}
    </div>
  );
}


function PerilCard({
  exposure, active, onClick,
}: {
  exposure: CatPerilExposure;
  active: boolean;
  onClick: () => void;
}) {
  const Icon = PERIL_ICONS[exposure.peril_slug] ?? ShieldAlert;
  const severityTone =
    exposure.relative_severity >= 0.6 ? "text-generate-text-bad"
    : exposure.relative_severity >= 0.4 ? "text-generate-text-maybe"
    : "text-generate-text-good";

  return (
    <button
      onClick={onClick}
      className={`
        text-left
        border rounded-lg p-3
        transition-colors
        ${active
          ? "border-generate-text-input bg-generate-light-input"
          : "border-generate-text-outline hover:border-generate-text-input"}
      `}
    >
      <div className="flex items-center gap-2 mb-2">
        <Icon className="generate-app-icon" />
        <span className="text-sm font-bold">{exposure.peril_name}</span>
      </div>
      <div className="text-xs text-generate-text-placeholder mb-1">
        Book-relative severity
      </div>
      <div className={`text-2xl font-bold ${severityTone}`}>
        {(exposure.relative_severity * 100).toFixed(0)}%
      </div>
      <ScoreBar
        value={exposure.relative_severity * 100}
        min={0}
        max={100}
        decimals={0}
        hideValue
        thresholds={[
          { at: 30, color: "var(--color-generate-text-good)" },
          { at: 50, color: "var(--color-generate-text-maybe)" },
          { at: Infinity, color: "var(--color-generate-text-bad)" },
        ]}
      />
      <div className="text-xs text-generate-text-placeholder mt-2">
        {exposure.exposed_policy_count} polic{exposure.exposed_policy_count === 1 ? "y" : "ies"} exposed
      </div>
    </button>
  );
}


function PerilNarrative({
  exposure, totalPremium,
}: {
  exposure: CatPerilExposure;
  totalPremium: number;
}) {
  const sharePct = totalPremium ? (exposure.exposed_premium_usd / totalPremium) * 100 : 0;
  return (
    <div className="space-y-2">
      <h3 className="text-sm font-bold flex items-center gap-2">
        <ShieldAlert className="generate-app-icon" /> {exposure.peril_name} — impact narrative
      </h3>
      <p className="text-sm">
        A {exposure.peril_name.toLowerCase()} event would touch
        {" "}<strong>{exposure.exposed_policy_count}</strong> polic{exposure.exposed_policy_count === 1 ? "y" : "ies"} in your book,
        with exposure-weighted premium of
        {" "}<strong>{formatCurrency(exposure.exposed_premium_usd, 0)}</strong>
        {" "}({sharePct.toFixed(0)}% of book).
        {exposure.most_exposed_verticals.length > 0 && (
          <span>
            {" "}Concentration sits in
            {" "}<strong>{exposure.most_exposed_verticals.join(", ")}</strong>.
          </span>
        )}
      </p>
      <p className="text-xs text-generate-text-placeholder">
        Severity rating: {(exposure.relative_severity * 100).toFixed(0)}% of book at meaningful exposure.
      </p>
    </div>
  );
}


function LoadShell() {
  return (
    <ViewCanvas>
      <CardGrid cols="grid-cols-1">
        <StandardCard title="Loading" lucideIcon={Network}>
          <NoData message="Loading risk aggregation…" />
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
          <NoData message={msg} />
        </StandardCard>
      </CardGrid>
    </ViewCanvas>
  );
}

function BrokerOnly() {
  return (
    <ViewCanvas>
      <CardGrid cols="grid-cols-1">
        <StandardCard title="Broker-only" lucideIcon={AlertTriangle}>
          <NoData message="Risk Aggregation is for broker users only." />
        </StandardCard>
      </CardGrid>
    </ViewCanvas>
  );
}

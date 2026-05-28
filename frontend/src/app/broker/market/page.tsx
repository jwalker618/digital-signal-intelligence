"use client";

// v8.2 Market Pulse — /broker/market
//
// Rebuilt from the v8.1 placeholder into a real intelligence surface:
//   - Overall cycle position + climate pulse narrative
//   - By-line dashboards (7 lines) with cycle / capacity / rate /
//     loss-trend per line, expandable into per-line detail
//   - Recent loss-event ticker shaping market direction
//   - ESG overlay surfaced on every line

import { useEffect, useState } from "react";
import {
  ArrowRight,
  Leaf,
  ShieldAlert,
  Sparkles,
  TrendingUp,
} from "lucide-react";
import Modal from "@/components/base/modal";
import ViewCanvas from "@/components/ViewCanvas";
import VerticalFilter from "@/components/portal/VerticalFilter";
import {
  CardGrid,
  StandardCard,
  SubmissionHeaderCard,
} from "@/components/base/cards";
import {
  InfoPanel,
  KpiTile,
  LabelValueList,
  NoData,
  ScoreBar,
  StatsGrid,
} from "@/components/base/content/primatives";

import { useAuthStore } from "@/store/authStore";
import { useDsiStore } from "@/store/dsiStore";
import {
  fetchMarketLineDetail,
  fetchMarketPulse,
} from "@/lib/portalApi";
import { formatNumber } from "@/lib/format";
import type {
  CarrierSummary,
  LineDetailResponse,
  LossEventEntry,
  MarketLineSummary,
  MarketPulseResponse,
} from "@/types/portal";
import { PageLoading, PageError, RoleGate } from "@/components/base/pageStates";


export default function MarketPulsePage() {
  const accessToken = useAuthStore((s) => s.accessToken);
  const userRole = useAuthStore((s) => s.user?.role ?? null);
  const setActiveMenu = useDsiStore((s) => s.setActiveMenu);

  const [data, setData] = useState<MarketPulseResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [lineDetail, setLineDetail] = useState<LineDetailResponse | null>(null);

  useEffect(() => { setActiveMenu("Market Pulse"); }, [setActiveMenu]);

  useEffect(() => {
    let cancelled = false;
    async function load() {
      try {
        const resp = await fetchMarketPulse(accessToken);
        if (!cancelled) setData(resp);
      } catch (e) {
        if (!cancelled) setError(e instanceof Error ? e.message : String(e));
      }
    }
    if (accessToken && userRole === "BROKER") load();
    return () => { cancelled = true; };
  }, [accessToken, userRole]);

  if (userRole !== "BROKER") return <RoleGate expected="broker" message="Market Pulse is for broker users only." />;
  if (error) return <PageError message={error} />;
  if (!data) return <PageLoading icon={TrendingUp} message="Loading market pulse…" />;

  const hardening = data.lines.filter((l) => l.cycle_position === "Hardening").length;
  const softening = data.lines.filter((l) => l.cycle_position === "Softening").length;

  return (
    <ViewCanvas>
      <CardGrid cols="grid-cols-1" className="gap-4">

        <SubmissionHeaderCard
          decision="approve"
          title="Market Pulse"
          subtitle="By-line cycle position, capacity, loss trends, and the climate overlay shaping placement"
          lucideIcon={TrendingUp}
        >
          <StatsGrid
            columns={[
              { label: "Cycle overall",   value: shortCycle(data.cycle_overall), align: "center" },
              { label: "Lines hardening", value: hardening, align: "center" },
              { label: "Lines softening", value: softening, align: "center" },
              { label: "Lines watched",   value: data.lines.length, align: "center" },
              { label: "Recent events",   value: data.recent_loss_events.length, align: "center" },
            ]}
          />
        </SubmissionHeaderCard>

        <VerticalFilter />

        <StandardCard title="Climate Pulse — the active market force" lucideIcon={Leaf}>
          <p className="text-sm py-2">{data.climate_pulse_summary}</p>
        </StandardCard>

        <StandardCard
          title="By-line dashboards"
          lucideIcon={Sparkles}
          headerRight={
            <span className="text-xs text-generate-text-placeholder">
              Click a line for full carrier + loss-event detail
            </span>
          }
        >
          <CardGrid cols="grid-cols-1 md:grid-cols-2 xl:grid-cols-3" className="gap-3">
            {data.lines.map((line) => (
              <LineCard
                key={line.slug}
                line={line}
                onClick={async () => {
                  try {
                    const d = await fetchMarketLineDetail(accessToken, line.slug);
                    setLineDetail(d);
                  } catch (e) {
                    setError(e instanceof Error ? e.message : String(e));
                  }
                }}
              />
            ))}
          </CardGrid>
        </StandardCard>

        <StandardCard
          title="Recent loss events shaping market direction"
          lucideIcon={ShieldAlert}
          headerRight={
            <span className="text-xs text-generate-text-placeholder">
              Last 12 months
            </span>
          }
        >
          <LossEventList events={data.recent_loss_events} />
        </StandardCard>

        <InfoPanel label="Marsh Pulse — data freshness" aside="v8.2 demo">
          <p className="text-xs">
            Cycle / capacity / rate signals reflect synthesised
            quarter-end-2026 market intelligence. Production wires
            real-time Marsh Pulse Index data plus carrier conditional
            commitments. ESG overlays are derived from public carrier
            commitments and observable underwriting behaviour.
          </p>
        </InfoPanel>

      </CardGrid>

      <LineDetailModal detail={lineDetail} onClose={() => setLineDetail(null)} />
    </ViewCanvas>
  );
}


// ----------------------------------------------------------------------------
// Line dashboard card
// ----------------------------------------------------------------------------

function LineCard({
  line, onClick,
}: {
  line: MarketLineSummary;
  onClick: () => void;
}) {
  const cycleTone =
    line.cycle_position === "Hardening" ? "text-generate-text-bad"
    : line.cycle_position === "Softening" ? "text-generate-text-good"
    : "text-generate-text-comment";

  const rateTone =
    line.rate_change_yoy_pct > 5 ? "text-generate-text-bad"
    : line.rate_change_yoy_pct < -3 ? "text-generate-text-good"
    : "text-generate-text-placeholder";

  const lossTone =
    line.loss_trend.startsWith("Deteriorating") || line.loss_trend.startsWith("Worsening")
      ? "text-generate-text-bad"
    : line.loss_trend.startsWith("Improving") ? "text-generate-text-good"
    : "text-generate-text-placeholder";

  return (
    <button
      onClick={onClick}
      className="
        text-left
        border border-generate-text-outline rounded-lg p-4
        hover:border-generate-text-input
        group transition-colors
      "
    >
      <div className="flex items-baseline justify-between mb-3">
        <span className="text-sm font-bold group-hover:text-generate-text-input">
          {line.name}
        </span>
        <span className={`text-xs font-bold ${cycleTone}`}>
          {line.cycle_position}
        </span>
      </div>

      <div className="grid grid-cols-2 gap-2 text-xs mb-3">
        <div>
          <div className="text-generate-text-placeholder">Rate change YoY</div>
          <div className={`text-lg font-bold ${rateTone}`}>
            {line.rate_change_yoy_pct > 0 ? "+" : ""}
            {formatNumber(line.rate_change_yoy_pct, 1)}%
          </div>
        </div>
        <div>
          <div className="text-generate-text-placeholder">Capacity</div>
          <div className="text-lg font-bold">{line.capacity_state}</div>
          <div className="text-[10px] text-generate-text-placeholder">
            {line.capacity_trend}
          </div>
        </div>
      </div>

      <div className="text-xs mb-2">
        <span className="text-generate-text-placeholder">Loss trend: </span>
        <span className={`font-bold ${lossTone}`}>{line.loss_trend}</span>
      </div>

      <div className="border-t border-generate-text-outline pt-2 mt-2">
        <div className="text-xs text-generate-text-placeholder mb-1 flex items-center gap-1">
          <Leaf className="generate-app-icon" /> ESG overlay
        </div>
        <p className="text-xs">{line.esg_overlay}</p>
      </div>

      <div className="text-xs text-generate-text-placeholder mt-3 flex items-center justify-end gap-1 group-hover:text-generate-text-input">
        Full detail <ArrowRight className="generate-app-icon" />
      </div>
    </button>
  );
}


// ----------------------------------------------------------------------------
// Loss event list
// ----------------------------------------------------------------------------

function LossEventList({ events }: { events: LossEventEntry[] }) {
  if (events.length === 0) {
    return <NoData message="No material loss events in the watch window." />;
  }
  return (
    <div className="space-y-2 py-2">
      {events.map((e, i) => (
        <div
          key={i}
          className="border border-generate-text-outline rounded-md p-3 text-sm"
        >
          <div className="flex items-baseline justify-between mb-1">
            <span className="font-bold">{e.headline}</span>
            <span className="text-xs text-generate-text-placeholder">
              {e.date} · {e.line}
            </span>
          </div>
          <div className="text-xs text-generate-text-placeholder mb-1">
            Industry-level loss: <span className="font-bold text-generate-text-input">${formatNumber(e.estimated_industry_loss_usd_bn, 1)}B</span>
          </div>
          <p className="text-xs italic">{e.implication}</p>
        </div>
      ))}
    </div>
  );
}


// ----------------------------------------------------------------------------
// Per-line detail modal
// ----------------------------------------------------------------------------

function LineDetailModal({
  detail, onClose,
}: {
  detail: LineDetailResponse | null;
  onClose: () => void;
}) {
  return (
    <Modal
      isOpen={detail !== null}
      onClose={onClose}
      title={detail?.name ?? ""}
      icon={Sparkles}
    >
      {detail && (
        <div className="space-y-4">
          <div className="grid grid-cols-3 gap-3">
            <KpiTile label="Cycle" value={detail.cycle_position} />
            <KpiTile
              label="Rate YoY"
              value={`${detail.rate_change_yoy_pct > 0 ? "+" : ""}${detail.rate_change_yoy_pct.toFixed(1)}%`}
              variant="emphasis"
            />
            <KpiTile label="Capacity" value={detail.capacity_state} />
          </div>

          <InfoPanel label="Summary">
            <p className="text-sm">{detail.summary}</p>
          </InfoPanel>

          <InfoPanel label="Key drivers">
            <ul className="text-sm space-y-1 mt-1">
              {detail.key_drivers.map((d, i) => (
                <li key={i}>· {d}</li>
              ))}
            </ul>
          </InfoPanel>

          <InfoPanel label="ESG overlay" aside={
            <Leaf className="generate-app-icon" />
          }>
            <p className="text-sm">{detail.esg_overlay}</p>
          </InfoPanel>

          <InfoPanel label="Top carriers for this line" aside={`${detail.top_carriers.length}`}>
            <ul className="space-y-1 mt-1">
              {detail.top_carriers.map((c) => (
                <li key={c.slug} className="flex items-baseline justify-between text-sm">
                  <span className="font-bold">{c.name}</span>
                  <span className="text-xs text-generate-text-placeholder">
                    {(c.win_rate * 100).toFixed(0)}% win · {c.typical_commission_pct.toFixed(1)}% cmsn
                  </span>
                </li>
              ))}
            </ul>
          </InfoPanel>

          {detail.recent_loss_events.length > 0 && (
            <InfoPanel label="Loss events affecting this line">
              <ul className="space-y-2 mt-1">
                {detail.recent_loss_events.map((e, i) => (
                  <li key={i} className="text-xs">
                    <span className="font-bold">{e.headline}</span>
                    <span className="text-generate-text-placeholder ml-2">{e.date}</span>
                    <div className="italic mt-0.5">{e.implication}</div>
                  </li>
                ))}
              </ul>
            </InfoPanel>
          )}
        </div>
      )}
    </Modal>
  );
}


function shortCycle(cycle: string): string {
  // The cycle string includes commentary; for the KPI strip we want just
  // the headline movement.
  if (cycle.includes("hardening")) return "Hardening";
  if (cycle.includes("softening")) return "Softening";
  return "Balanced";
}
"use client";

// v8.2 Placement Strategy — /broker/placement
//
// Two modes:
//   - No submission selected: picker showing in-flight book; click a
//     row to drill in
//   - Submission selected: ranked carrier matches with predicted
//     pricing, commission, ESG fit, win rate, rationale

import { useEffect, useMemo, useState } from "react";
import {
  Briefcase,
  Building2,
  Leaf,
  Target as TargetIcon,
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
  NoData,
  ScoreBar,
  StatsGrid,
} from "@/components/base/content/primatives";
import VerticalFilter, { useVerticalFilter } from "@/components/portal/VerticalFilter";

import { useAuthStore } from "@/store/authStore";
import { useDsiStore } from "@/store/dsiStore";
import {
  fetchOverview,
  fetchPlacementStrategy,
} from "@/lib/portalApi";
import { formatCurrency } from "@/lib/format";
import type {
  BrokerOverviewResponse,
  CarrierMatch,
  ClientBookEntry,
  PlacementStrategyResponse,
} from "@/types/portal";
import { PageLoading, PageError, RoleGate } from "@/components/base/pageStates";


export default function PlacementPage() {
  const accessToken = useAuthStore((s) => s.accessToken);
  const userRole = useAuthStore((s) => s.user?.role ?? null);
  const setActiveMenu = useDsiStore((s) => s.setActiveMenu);
  const filter = useVerticalFilter();

  const [overview, setOverview] = useState<BrokerOverviewResponse | null>(null);
  const [selected, setSelected] = useState<string | null>(null);
  const [strategy, setStrategy] = useState<PlacementStrategyResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => { setActiveMenu("Placement Strategy"); }, [setActiveMenu]);

  useEffect(() => {
    let cancelled = false;
    async function load() {
      try {
        const resp = await fetchOverview(accessToken);
        if (cancelled) return;
        if (resp.role !== "BROKER") {
          setError("Placement Strategy is for broker users only.");
          return;
        }
        setOverview(resp as BrokerOverviewResponse);
      } catch (e) {
        if (!cancelled) setError(e instanceof Error ? e.message : String(e));
      }
    }
    if (accessToken && userRole === "BROKER") load();
    return () => { cancelled = true; };
  }, [accessToken, userRole]);

  useEffect(() => {
    let cancelled = false;
    async function loadStrategy() {
      if (!selected) { setStrategy(null); return; }
      try {
        const resp = await fetchPlacementStrategy(accessToken, selected);
        if (!cancelled) setStrategy(resp);
      } catch (e) {
        if (!cancelled) setError(e instanceof Error ? e.message : String(e));
      }
    }
    loadStrategy();
    return () => { cancelled = true; };
  }, [accessToken, selected]);

  if (userRole !== "BROKER") return <RoleGate expected="broker" message="Placement Strategy is for broker users only." />;
  if (error) return <PageError message={error} />;
  if (!overview) return <PageLoading icon={TargetIcon} message="Loading placement strategy…" />;

  const filteredClients = overview.clients.filter((c) => {
    // Map vertical via the back-end's vertical_slug; the broker overview
    // doesn't expose this directly today, so fall back to showing all
    // when no filter is set.
    return filter.slug == null || true; // simplification: filter applied client-side via Client Health
  });

  return (
    <ViewCanvas>
      <CardGrid cols="grid-cols-1" className="gap-4">

        <SubmissionHeaderCard
          decision="approve"
          title="Placement Strategy"
          subtitle="For any in-flight risk, see the carrier roster ranked by fit, pricing, commission, and ESG match"
          lucideIcon={TargetIcon}
        >
          <StatsGrid
            columns={[
              { label: "Policies in book", value: overview.clients.length, align: "center" },
              { label: "Selected", value: selected ? "1" : "—", align: "center" },
              { label: "Open queries", value: overview.open_queries_count, align: "center" },
              { label: "Method", value: "Rule + heuristic", align: "center" },
            ]}
          />
        </SubmissionHeaderCard>

        <VerticalFilter />

        <CardGrid cols="grid-cols-1 lg:grid-cols-3" className="gap-4">

          {/* Submission picker (left third) */}
          <StandardCard title="Pick a policy" lucideIcon={Briefcase}>
            {filteredClients.length === 0 ? (
              <NoData message="No policies in your book yet." />
            ) : (
              <div className="space-y-2 py-1 max-h-[600px] overflow-y-auto no-scrollbar">
                {filteredClients.map((c) => (
                  <PolicyPicker
                    key={c.submission_code}
                    client={c}
                    active={selected === c.submission_code}
                    onClick={() => setSelected(c.submission_code)}
                  />
                ))}
              </div>
            )}
          </StandardCard>

          {/* Strategy detail (right two-thirds) */}
          <div className="lg:col-span-2">
            {selected && !strategy && (
              <StandardCard title="Building strategy…" lucideIcon={TargetIcon}>
                <NoData message="Computing carrier matches…" />
              </StandardCard>
            )}

            {!selected && (
              <StandardCard title="Carrier matches" lucideIcon={TargetIcon}>
                <NoData message="Pick a policy from the left to see ranked carrier matches, predicted pricing, commission yield, ESG fit, and win-rate context." />
              </StandardCard>
            )}

            {strategy && (
              <StrategyDetail strategy={strategy} />
            )}
          </div>
        </CardGrid>

        <InfoPanel label="How matches are scored" aside="v8.2 — composite scoring">
          <p className="text-xs">
            Each carrier's suitability score blends appetite stance (50%
            weight), pricing position vs market median (10%), ESG fit with
            the insured's vertical (15%), and the carrier's win rate (25%).
            Predicted premium range is anchored on the current quote and
            adjusted by the carrier's pricing position. Production wires
            actual placement history; the demo uses synthesised hit-rate
            data and indicative pricing ranges.
          </p>
        </InfoPanel>

      </CardGrid>
    </ViewCanvas>
  );
}


function PolicyPicker({
  client, active, onClick,
}: {
  client: ClientBookEntry;
  active: boolean;
  onClick: () => void;
}) {
  return (
    <button
      onClick={onClick}
      className={`
        w-full text-left
        border rounded-md p-3
        transition-colors
        ${active
          ? "border-generate-text-input bg-generate-light-input"
          : "border-generate-text-outline hover:border-generate-text-input"}
      `}
    >
      <div className="text-sm font-bold">{client.entity_name}</div>
      <div className="text-xs text-generate-text-placeholder capitalize">
        {client.coverage}
        {client.recommended_premium != null && (
          <span> · {formatCurrency(client.recommended_premium, 0)}</span>
        )}
      </div>
      {client.referral_state === "awaiting_broker" && (
        <div className="text-xs text-generate-text-maybe font-bold mt-1">
          Awaiting reply
        </div>
      )}
    </button>
  );
}


function StrategyDetail({ strategy }: { strategy: PlacementStrategyResponse }) {
  const top = strategy.carrier_matches[0];

  return (
    <div className="space-y-4">
      <StandardCard
        title={`${strategy.entity_name} — ${strategy.coverage}`}
        lucideIcon={TargetIcon}
        headerRight={
          <span className="text-xs text-generate-text-placeholder">
            {strategy.carrier_matches.length} matches
          </span>
        }
      >
        <p className="text-sm py-2">{strategy.placement_note}</p>
      </StandardCard>

      {top && (
        <StandardCard
          title="Lead recommendation"
          lucideIcon={Building2}
        >
          <CarrierMatchCard match={top} highlight />
        </StandardCard>
      )}

      <StandardCard
        title="Ranked carrier matches"
        lucideIcon={Building2}
      >
        <div className="space-y-3">
          {strategy.carrier_matches.slice(1).map((m) => (
            <CarrierMatchCard key={m.slug} match={m} />
          ))}
        </div>
      </StandardCard>
    </div>
  );
}


function CarrierMatchCard({
  match, highlight = false,
}: {
  match: CarrierMatch;
  highlight?: boolean;
}) {
  return (
    <div
      className={`
        border rounded-lg p-4
        ${highlight ? "border-2 border-generate-text-comment/40 bg-generate-text-comment/5" : "border-generate-text-outline"}
      `}
    >
      <div className="grid gap-4" style={{ gridTemplateColumns: "2fr 100px 110px" }}>
        <div>
          <div className="flex items-baseline gap-2 mb-1">
            <span className="text-sm font-bold">{match.name}</span>
            <span className="text-xs text-generate-text-placeholder capitalize">
              · {match.appetite_stance.replace(/_/g, " ")}
            </span>
            {match.esg_stance === "leader" && (
              <span className="text-xs text-generate-text-good flex items-center gap-1 ml-2">
                <Leaf className="generate-app-icon" /> ESG leader
              </span>
            )}
          </div>
          <p className="text-xs text-generate-text-placeholder">{match.rationale}</p>
        </div>
        <div>
          <div className="text-xs text-generate-text-placeholder">Suitability</div>
          <div className="text-xl font-bold">{match.suitability_score}</div>
          <ScoreBar
            value={match.suitability_score}
            min={0}
            max={100}
            decimals={0}
            hideValue
            thresholds={[
              { at: 40, color: "var(--color-generate-text-bad)" },
              { at: 60, color: "var(--color-generate-text-maybe)" },
              { at: 80, color: "var(--color-generate-text-comment)" },
              { at: Infinity, color: "var(--color-generate-text-good)" },
            ]}
          />
        </div>
        <div className="text-right">
          <div className="text-xs text-generate-text-placeholder">Predicted premium</div>
          <div className="text-sm font-bold">
            {formatCurrency(match.predicted_premium_low, 0)} - {formatCurrency(match.predicted_premium_high, 0)}
          </div>
          <div className="text-xs text-generate-text-placeholder mt-1">
            Commission {match.typical_commission_pct.toFixed(1)}%
          </div>
          <div className="text-xs text-generate-text-placeholder">
            Win rate {match.win_rate_pct.toFixed(0)}%
          </div>
        </div>
      </div>
    </div>
  );
}
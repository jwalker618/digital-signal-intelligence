"use client";

// v8.1 Phase D — /client/scenarios
//
// Four scenario types in one page:
//   1. Signal what-ifs    -- close gap X -> score lifts to Y, premium -$Z
//   2. Limit what-ifs     -- raise cyber limit to $25M -> premium becomes $X (uses Phase C ROL data)
//   3. Add-coverage what-ifs -- add D&O at your profile -> premium ~$X (heuristic by NAICS/revenue)
//   4. Restructure what-ifs -- split property into primary + excess -> premium ~$X (heuristic for demo)

import { useEffect, useMemo } from "react";

import {
  ChartPie,
  FlaskConical,
  Layers,
  ListChecks,
  Plus,
} from "lucide-react";
import ViewCanvas from "@/components/ViewCanvas";
import {
  CardGrid,
  StandardCard,
  SubmissionHeaderCard,
} from "@/components/base/cards";
import {
  CompareRow,
  InfoPanel,
  KpiTile,
  NoData,
  StatsGrid,
} from "@/components/base/content/primatives";

import { useAuthStore } from "@/store/authStore";
import { useDsiStore } from "@/store/dsiStore";
import {
  fetchClientProfile,
  fetchOverview,
  fetchSubmissionScore,
} from "@/lib/portalApi";
import { formatCurrency, formatNumber } from "@/lib/format";
import type {
  ClientCoverageEntry,
  ClientOverviewResponse,
  ClientProfileResponse,
  ScoreResponse,
  SignalImpact,
} from "@/types/portal";
import { PageLoading, PageError, RoleGate } from "@/components/base/pageStates";
import { useRoleScopedFetch } from "@/lib/useRoleScopedFetch";


export default function ScenariosPage() {
  const accessToken = useAuthStore((s) => s.accessToken);
  const userRole = useAuthStore((s) => s.user?.role ?? null);
  const setActiveMenu = useDsiStore((s) => s.setActiveMenu);

  useEffect(() => { setActiveMenu("Scenarios"); }, [setActiveMenu]);

  const { data: bundle, error } = useRoleScopedFetch({
    fetcher: async () => {
      const [overviewResp, profileResp] = await Promise.all([
        fetchOverview(accessToken),
        fetchClientProfile(accessToken),
      ]);
      if (overviewResp.role !== "CLIENT") {
        throw new Error("The Scenarios view is for client users only.");
      }
      const clientOverview = overviewResp as ClientOverviewResponse;
      let score: ScoreResponse | null = null;
      const primary = clientOverview.active_coverages[0];
      if (primary) {
        try {
          score = await fetchSubmissionScore(accessToken, primary.submission_code);
        } catch {
          /* best-effort; scenarios still render without the score */
        }
      }
      return { overview: clientOverview, profile: profileResp, score };
    },
    enabled: !!accessToken && userRole === "CLIENT",
  });

  if (userRole !== "CLIENT") {
    return <RoleGate expected="client" message="The Scenarios view is for client users only." />;
  }
  if (error) return <PageError message={error} />;
  if (!bundle) return <PageLoading icon={FlaskConical} message="Building scenarios…" />;

  const { overview, profile, score } = bundle;

  const primary = overview.active_coverages[0] ?? null;
  const carriedCoverages = new Set(overview.active_coverages.map((c) => c.coverage));

  return (
    <ViewCanvas>
      <CardGrid cols="grid-cols-1" className="gap-4">

        <SubmissionHeaderCard
          decision="approve"
          title="Scenarios"
          subtitle="Explore what would happen if you changed signals, limits, or coverage shape"
          lucideIcon={FlaskConical}
        >
          <StatsGrid
            columns={[
              { label: "Primary policy", value: primary ? primary.coverage : "—", align: "center" },
              { label: "Current score", value: primary?.composite_score != null ? formatNumber(primary.composite_score, 0) : "—", align: "center" },
              { label: "Active policies", value: overview.active_coverages.length, align: "center" },
              { label: "Industry", value: profile.industry_label ?? "—", align: "center" },
              { label: "Revenue band", value: profile.revenue_band ?? "—", align: "center" },
            ]}
          />
        </SubmissionHeaderCard>

        {/* 1. Signal what-ifs ------------------------------------------ */}
        <StandardCard
          title="Improve a signal"
          lucideIcon={ListChecks}
          headerRight={
            <span className="text-xs text-generate-text-placeholder">
              Heuristic estimate, all-else-equal
            </span>
          }
        >
          <SignalWhatIfs score={score} subjectScore={primary?.composite_score ?? 0} />
        </StandardCard>

        {/* 2. Limit what-ifs ------------------------------------------- */}
        <StandardCard
          title="Adjust the limit on a current policy"
          lucideIcon={Layers}
          headerRight={
            <span className="text-xs text-generate-text-placeholder">
              Based on your carrier's ROL engine
            </span>
          }
        >
          <LimitWhatIfs score={score} coverage={primary?.coverage ?? ""} />
        </StandardCard>

        {/* 3. Add-coverage what-ifs ----------------------------------- */}
        <StandardCard
          title="Add a new coverage line"
          lucideIcon={Plus}
          headerRight={
            <span className="text-xs text-generate-text-placeholder">
              Indicative range — confirm placement with your broker
            </span>
          }
        >
          <AddCoverageWhatIfs
            profile={profile}
            carried={carriedCoverages}
          />
        </StandardCard>

        {/* 4. Restructure what-ifs ------------------------------------ */}
        <StandardCard
          title="Restructure your tower"
          lucideIcon={ChartPie}
          headerRight={
            <span className="text-xs text-generate-text-placeholder">
              Heuristic split — your broker would model the precise impact
            </span>
          }
        >
          <RestructureWhatIfs primary={primary} score={score} />
        </StandardCard>

        <InfoPanel label="How to read these">
          <p className="text-xs">
            All scenario figures are estimates intended to support
            conversations with your broker. Actual pricing is set by your
            carrier at placement and depends on full underwriting context.
          </p>
        </InfoPanel>

      </CardGrid>
    </ViewCanvas>
  );
}


// ----------------------------------------------------------------------------
// 1. Signal what-ifs
// ----------------------------------------------------------------------------

function SignalWhatIfs({
  score, subjectScore,
}: {
  score: ScoreResponse | null;
  subjectScore: number;
}) {
  if (!score || !score.impact_breakdown || score.impact_breakdown.drags.length === 0) {
    return <NoData message="No opportunities to model — your signal profile is clean across observed signals." />;
  }
  const top = score.impact_breakdown.drags.slice(0, 4);
  const allSaved = top.reduce((a, d) => a + Math.abs(d.premium_delta_usd), 0);
  const newScore = Math.min(1000, subjectScore + Math.round(allSaved / 1000 * 0.6));

  return (
    <div className="space-y-3 py-2">
      {top.map((d) => {
        const liftedScore = Math.min(1000, subjectScore + Math.round(Math.abs(d.premium_delta_usd) / 1000 * 0.6));
        return (
          <CompareRow
            key={d.signal_key}
            label={d.signal_label}
            sublabel="Close this gap"
            original={formatNumber(subjectScore, 0)}
            scenario={
              <span>
                {formatNumber(liftedScore, 0)}
                <span className="ml-2 text-generate-text-good">
                  -{formatCurrency(Math.abs(d.premium_delta_usd), 0)}
                </span>
              </span>
            }
            changed
          />
        );
      })}
      <div className="pt-2 border-t-2 border-generate-text-comment/30 mt-2">
        <CompareRow
          label={<strong>Close all opportunities above</strong>}
          original={formatNumber(subjectScore, 0)}
          scenario={
            <strong>
              {formatNumber(newScore, 0)}
              <span className="ml-2 text-generate-text-good">
                -{formatCurrency(allSaved, 0)}
              </span>
            </strong>
          }
          changed
        />
      </div>
    </div>
  );
}


// ----------------------------------------------------------------------------
// 2. Limit what-ifs (uses Phase C ROL recommendations from the backend)
// ----------------------------------------------------------------------------

function LimitWhatIfs({
  score, coverage,
}: {
  score: ScoreResponse | null;
  coverage: string;
}) {
  if (!score || score.final_premium == null) {
    return <NoData message="No current quote to compare against." />;
  }

  const currentPremium = score.final_premium;
  const lowerLimit = score.rol_lower_limit;
  const lowerPremium = score.rol_lower_premium;
  const upperLimit = score.rol_upper_limit;
  const upperPremium = score.rol_upper_premium;

  const haveAnyRol = lowerLimit != null || upperLimit != null;
  if (!haveAnyRol) {
    return (
      <p className="text-sm py-2">
        Your carrier's rate-on-line engine hasn't produced limit alternatives
        for this policy yet. Your broker can model bespoke options on request.
      </p>
    );
  }

  return (
    <div className="space-y-3 py-2">
      <p className="text-xs text-generate-text-placeholder">
        Two carrier-recommended alternatives for {coverage}: the minimum
        adequate limit (cheapest) and the best-value limit (best ROL).
      </p>
      {lowerLimit != null && lowerPremium != null && (
        <CompareRow
          label="Minimum adequate limit"
          sublabel={`Drop to ${formatCurrency(lowerLimit, 0)} limit`}
          original={formatCurrency(currentPremium, 0)}
          scenario={
            <span>
              {formatCurrency(lowerPremium, 0)}
              {lowerPremium < currentPremium && (
                <span className="ml-2 text-generate-text-good">
                  -{formatCurrency(currentPremium - lowerPremium, 0)}
                </span>
              )}
            </span>
          }
          changed
        />
      )}
      {upperLimit != null && upperPremium != null && (
        <CompareRow
          label="Best-value limit"
          sublabel={`Lift to ${formatCurrency(upperLimit, 0)} limit`}
          original={formatCurrency(currentPremium, 0)}
          scenario={
            <span>
              {formatCurrency(upperPremium, 0)}
              {upperPremium > currentPremium ? (
                <span className="ml-2 text-generate-text-bad">
                  +{formatCurrency(upperPremium - currentPremium, 0)}
                </span>
              ) : (
                <span className="ml-2 text-generate-text-good">
                  -{formatCurrency(currentPremium - upperPremium, 0)}
                </span>
              )}
            </span>
          }
          changed
        />
      )}
    </div>
  );
}


// ----------------------------------------------------------------------------
// 3. Add-coverage what-ifs (heuristic by industry + revenue band)
// ----------------------------------------------------------------------------

const ADDABLE_COVERAGES = [
  { id: "cyber", label: "Cyber" },
  { id: "pi", label: "Professional Indemnity" },
  { id: "do", label: "D&O Liability" },
  { id: "property", label: "Property" },
  { id: "casualty", label: "General Liability" },
  { id: "prodlib", label: "Product Liability" },
  { id: "medprof", label: "Medical Professional Liability" },
] as const;

// Same heuristic table the backend uses for broker recommendations
// (kept in sync; live in two places intentionally so the page works
// without an extra round trip).
const ADD_PREMIUM_RANGES: Record<string, Record<string, [number, number]>> = {
  cyber:    { "<10M": [8000, 18000],    "10-50M": [25000, 60000],    "50-250M": [75000, 220000],  "250M-1B": [180000, 480000],  ">1B": [350000, 1200000] },
  pi:       { "<10M": [6000, 14000],    "10-50M": [18000, 40000],    "50-250M": [45000, 110000],  "250M-1B": [95000, 280000],   ">1B": [220000, 700000] },
  do:       { "<10M": [12000, 28000],   "10-50M": [40000, 90000],    "50-250M": [100000, 250000], "250M-1B": [220000, 550000],  ">1B": [500000, 1400000] },
  property: { "<10M": [10000, 25000],   "10-50M": [35000, 85000],    "50-250M": [70000, 220000],  "250M-1B": [160000, 480000],  ">1B": [380000, 1100000] },
  casualty: { "<10M": [15000, 35000],   "10-50M": [50000, 120000],   "50-250M": [130000, 320000], "250M-1B": [280000, 720000],  ">1B": [650000, 1800000] },
  prodlib:  { "<10M": [10000, 30000],   "10-50M": [40000, 100000],   "50-250M": [95000, 250000],  "250M-1B": [220000, 580000],  ">1B": [500000, 1400000] },
  medprof:  { "<10M": [30000, 80000],   "10-50M": [60000, 160000],   "50-250M": [140000, 380000], "250M-1B": [320000, 820000],  ">1B": [700000, 2000000] },
};

function AddCoverageWhatIfs({
  profile, carried,
}: {
  profile: ClientProfileResponse;
  carried: Set<string>;
}) {
  const rb = profile.revenue_band;
  const candidates = ADDABLE_COVERAGES.filter((c) => !carried.has(c.id));

  if (candidates.length === 0) {
    return <NoData message="You already carry every line we'd recommend for your profile." />;
  }
  if (!rb) {
    return <p className="text-sm py-2">Revenue band not set — fill in your profile to see indicative premium ranges.</p>;
  }

  return (
    <div className="space-y-2 py-2">
      <p className="text-xs text-generate-text-placeholder mb-2">
        Indicative premium ranges for adding a new line, based on your
        industry ({profile.industry_label ?? profile.industry_code}) and
        revenue band ({rb}). Actual placement depends on carrier appetite
        and underwriting outcome.
      </p>
      <div
        className="grid"
        style={{ gridTemplateColumns: "2fr 1fr 1fr" }}
      >
        {["Coverage", "Estimated range", ""].map((h, i) => (
          <div key={i} className="text-xs text-generate-text-placeholder border-b border-generate-text-outline pb-1.5 pt-1.5">
            {h}
          </div>
        ))}
        {candidates.map((c) => {
          const range = ADD_PREMIUM_RANGES[c.id]?.[rb];
          return (
            <div key={c.id} className="contents">
              <div className="text-sm py-2">{c.label}</div>
              <div className="text-sm py-2 font-bold">
                {range
                  ? `${formatCurrency(range[0], 0)} – ${formatCurrency(range[1], 0)}`
                  : "Contact broker"}
              </div>
              <div className="text-xs py-2 text-generate-text-placeholder">
                {range ? "Mid-market estimate" : "Bespoke placement"}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}


// ----------------------------------------------------------------------------
// 4. Restructure what-ifs (heuristic split for demo)
// ----------------------------------------------------------------------------

function RestructureWhatIfs({
  primary, score,
}: {
  primary: ClientCoverageEntry | null;
  score: ScoreResponse | null;
}) {
  if (!primary || primary.recommended_premium == null) {
    return <NoData message="No primary policy to restructure." />;
  }
  const currentPremium = primary.recommended_premium;

  // Heuristic: splitting a single $X tower into Y + (X-Y) excess typically
  // yields ~5-10% savings due to differential ROL on excess layers. We
  // model two illustrative splits.
  const split6040 = currentPremium * 0.93;
  const split5050 = currentPremium * 0.91;
  const allInOne = currentPremium;

  return (
    <div className="space-y-3 py-2">
      <p className="text-xs text-generate-text-placeholder">
        Splitting a single-line tower into primary + excess can reduce
        total premium by 7-10% on average. Your broker can model the
        exact impact for your placement.
      </p>
      <CompareRow
        label="Current — single tower"
        original={formatCurrency(allInOne, 0)}
        scenario={formatCurrency(allInOne, 0)}
        showArrow={false}
      />
      <CompareRow
        label="60 / 40 split (primary + excess)"
        sublabel="Lead carrier on primary, secondary on excess"
        original={formatCurrency(allInOne, 0)}
        scenario={
          <span>
            {formatCurrency(split6040, 0)}
            <span className="ml-2 text-generate-text-good">
              -{formatCurrency(allInOne - split6040, 0)}
            </span>
          </span>
        }
        changed
      />
      <CompareRow
        label="50 / 50 split"
        sublabel="Two equal layers"
        original={formatCurrency(allInOne, 0)}
        scenario={
          <span>
            {formatCurrency(split5050, 0)}
            <span className="ml-2 text-generate-text-good">
              -{formatCurrency(allInOne - split5050, 0)}
            </span>
          </span>
        }
        changed
      />
    </div>
  );
}


"use client";

// v8 Phase 8 — /client/drivers (CLIENT-focused, BROKER can also view)
//
// Deep-dive on positive and negative signal drivers for the user's
// latest submission. Reuses the SignalDriversInline section pattern
// from the submission detail page, but expands the lists and adds
// premium math summaries.

import { useEffect, useState } from "react";

import {
  ChartPie,
  Globe,
  ListChecks,
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
  ExpandableGroupTable,
  KpiTile,
  LabelValueList,
  type ExpandableGroup,
} from "@/components/base/content/primatives";

import { useAuthStore } from "@/store/authStore";
import { useDsiStore } from "@/store/dsiStore";
import {
  fetchOverview,
  fetchSubmissionScore,
} from "@/lib/portalApi";
import { formatCurrency, formatNumber } from "@/lib/format";
import type {
  ClientOverviewResponse,
  ScoreResponse,
  SignalImpact,
} from "@/types/portal";
import { PageLoading, PageError } from "@/components/base/pageStates";


export default function DriversPage() {
  const accessToken = useAuthStore((s) => s.accessToken);
  const setActiveMenu = useDsiStore((s) => s.setActiveMenu);

  const [score, setScore] = useState<ScoreResponse | null>(null);
  const [entityName, setEntityName] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => { setActiveMenu("Risk Insights"); }, [setActiveMenu]);

  useEffect(() => {
    let cancelled = false;
    async function load() {
      try {
        const overview = await fetchOverview(accessToken);
        if (cancelled) return;
        if (overview.role !== "CLIENT") {
          setError("Driver detail is currently for client users.");
          return;
        }
        const primary = (overview as ClientOverviewResponse).active_coverages[0];
        if (!primary) {
          setError("No active coverage to analyse yet.");
          return;
        }
        setEntityName((overview as ClientOverviewResponse).entity_name);
        const s = await fetchSubmissionScore(accessToken, primary.submission_code);
        if (!cancelled) setScore(s);
      } catch (e) {
        if (!cancelled) setError(e instanceof Error ? e.message : String(e));
      }
    }
    if (accessToken) load();
    return () => { cancelled = true; };
  }, [accessToken]);

  if (error) return <PageError message={error} />;
  if (!score) return <PageLoading icon={ListChecks} message="Computing signal impact breakdown…" />;

  const drags = score.impact_breakdown?.drags ?? [];
  const strengths = score.impact_breakdown?.strengths ?? [];
  const neutral = score.impact_breakdown?.neutral ?? [];
  const totalDrag = drags.reduce((a, d) => a + Math.abs(d.premium_delta_usd), 0);
  const totalStrength = strengths.reduce((a, s) => a + Math.abs(s.premium_delta_usd), 0);
  const netImpact = totalDrag - totalStrength;

  const groups: ExpandableGroup<SignalImpact>[] = [
    {
      key: "drags",
      title: `Opportunities (${drags.length}) — improving these would lower your premium`,
      items: drags,
      summary: [
        `${drags.length} signal${drags.length === 1 ? "" : "s"}`,
        formatCurrency(totalDrag, 0),
      ],
      emptyMessage: "No opportunities identified yet — clean profile.",
    },
    {
      key: "strengths",
      title: `Strengths (${strengths.length}) — already lowering your premium`,
      items: strengths,
      summary: [
        `${strengths.length} signal${strengths.length === 1 ? "" : "s"}`,
        formatCurrency(totalStrength, 0),
      ],
      emptyMessage: "Strengths haven't been identified on this quote yet.",
    },
    {
      key: "neutral",
      title: `Neutral (${neutral.length}) — neither helping nor hurting today`,
      items: neutral,
      summary: [
        `${neutral.length} signal${neutral.length === 1 ? "" : "s"}`,
        "—",
      ],
      emptyMessage: "No neutral signals on this quote.",
    },
  ];

  return (
    <ViewCanvas>
      <CardGrid cols="grid-cols-1" className="gap-4">

        <SubmissionHeaderCard
          decision={netImpact > 0 ? "refer" : "approve"}
          title={`Risk Insights — ${entityName ?? "Your entity"}`}
          subtitle="Strengths & opportunities, plus your loss outlook and exposure profile"
          lucideIcon={ListChecks}
        >
          <div className="grid grid-cols-2 md:grid-cols-4 gap-6 py-2">
            <KpiTile
              label="Base premium"
              value={score.base_premium != null ? formatCurrency(score.base_premium, 0) : "—"}
              lucideIcon={ChartPie}
            />
            <KpiTile
              label="Total strengths"
              value={`-${formatCurrency(totalStrength, 0)}`}
              subtext={`${strengths.length} signal${strengths.length === 1 ? "" : "s"}`}
            />
            <KpiTile
              label="Total opportunity"
              value={`+${formatCurrency(totalDrag, 0)}`}
              subtext={`${drags.length} signal${drags.length === 1 ? "" : "s"}`}
            />
            <KpiTile
              label="Final premium"
              value={score.final_premium != null ? formatCurrency(score.final_premium, 0) : "—"}
              variant="emphasis"
            />
          </div>
        </SubmissionHeaderCard>

        <CardGrid cols="grid-cols-1 lg:grid-cols-2" className="gap-4">
          <StandardCard title="Loss outlook" lucideIcon={ShieldAlert}>
            <LossOutlook score={score} />
          </StandardCard>

          <StandardCard title="Exposure profile" lucideIcon={Globe}>
            <ExposureProfile score={score} />
          </StandardCard>
        </CardGrid>

        <StandardCard
          title="Strengths & opportunities"
          lucideIcon={TrendingUpDown}
          headerRight={
            <span className="text-xs text-generate-text-placeholder">
              Click a row group to expand
            </span>
          }
        >
          <ExpandableGroupTable
            title=""
            defaultExpanded={{ drags: true, strengths: true, neutral: false }}
            columns={[
              { label: "Signal", width: "50%", align: "left", headeralign: "left" },
              { label: "Modifier", width: "20%", align: "center", headeralign: "center" },
              { label: "Premium impact", width: "30%", align: "right", headeralign: "right" },
            ]}
            groups={groups}
            renderItemCells={(item) => [
              item.signal_label,
              `${formatNumber(item.combined_modifier, 3)}x`,
              <span
                key={item.signal_key}
                className={
                  item.classification === "drag"
                    ? "text-generate-text-bad font-bold"
                    : item.classification === "strength"
                    ? "text-generate-text-good font-bold"
                    : "text-generate-text-placeholder"
                }
              >
                {item.classification === "drag" ? "+" : item.classification === "strength" ? "−" : ""}
                {formatCurrency(Math.abs(item.premium_delta_usd), 0)}
              </span>,
            ]}
          />
        </StandardCard>

      </CardGrid>
    </ViewCanvas>
  );
}
// ----------------------------------------------------------------------------
// Loss + Exposure summary cards (v8.1 Phase C)
// ----------------------------------------------------------------------------

function LossOutlook({ score }: { score: ScoreResponse }) {
  const propensity = score.loss_propensity_score;
  const band = score.loss_propensity_band;
  const trend = score.loss_trend_direction;
  const severityScore = score.severity_propensity_score;

  const trendTone =
    trend === "improving" ? "text-generate-text-good" :
    trend === "deteriorating" ? "text-generate-text-bad" :
    "text-generate-text-placeholder";

  const bandLabel =
    band === "very_low" ? "Very low" :
    band === "low" ? "Low" :
    band === "moderate" ? "Moderate" :
    band === "elevated" ? "Elevated" :
    band === "high" ? "High" :
    band ?? "—";

  if (propensity == null && band == null && trend == null) {
    return (
      <p className="text-sm py-2">
        Loss data isn't available for this submission yet. As claims experience
        accumulates and is reported, this section will populate.
      </p>
    );
  }

  return (
    <div className="space-y-3 py-2">
      <LabelValueList
        variant="card"
        rows={[
          { label: "Loss propensity band", value: <span className="font-bold">{bandLabel}</span> },
          { label: "Frequency score", value: propensity != null ? formatNumber(propensity, 0) : "—" },
          { label: "Severity score", value: severityScore != null ? formatNumber(severityScore, 0) : "—" },
          {
            label: "Trend direction",
            value: <span className={`font-bold capitalize ${trendTone}`}>{trend ?? "—"}</span>,
          },
        ]}
      />
      <p className="text-xs text-generate-text-placeholder">
        The loss outlook combines observed claims experience with forward-looking
        signals from your industry and posture. It's reviewed at each renewal cycle.
      </p>
    </div>
  );
}

function ExposureProfile({ score }: { score: ScoreResponse }) {
  const value = score.exposure_value;
  const band = score.exposure_band_label;
  const size = score.exposure_size_score;
  const complexity = score.exposure_complexity_score;

  if (value == null && band == null && size == null && complexity == null) {
    return (
      <p className="text-sm py-2">
        Exposure data isn't yet captured for this submission. Your broker can
        help complete this once you confirm exposure inputs.
      </p>
    );
  }

  return (
    <div className="space-y-3 py-2">
      <LabelValueList
        variant="card"
        rows={[
          { label: "Exposure band", value: <span className="font-bold">{band ?? "—"}</span> },
          {
            label: "Exposure value",
            value: value != null ? formatCurrency(value, 0) : "—",
          },
          { label: "Size score", value: size != null ? formatNumber(size, 0) : "—" },
          { label: "Complexity score", value: complexity != null ? formatNumber(complexity, 0) : "—" },
        ]}
      />
      <p className="text-xs text-generate-text-placeholder">
        Exposure measures the scale and complexity of your operations.
        Higher values increase capacity needs; higher complexity affects
        carrier appetite.
      </p>
    </div>
  );
}

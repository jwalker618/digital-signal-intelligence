"use client";

// v8 Phase 8 — /portal/drivers (CLIENT-focused, BROKER can also view)
//
// Deep-dive on positive and negative signal drivers for the user's
// latest submission. Reuses the SignalDriversInline section pattern
// from the submission detail page, but expands the lists and adds
// premium math summaries.

import { useEffect, useState } from "react";

import {
  AlertTriangle,
  ChartPie,
  ListChecks,
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


export default function DriversPage() {
  const accessToken = useAuthStore((s) => s.accessToken);
  const setActiveMenu = useDsiStore((s) => s.setActiveMenu);

  const [score, setScore] = useState<ScoreResponse | null>(null);
  const [entityName, setEntityName] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => { setActiveMenu("Signal Drivers"); }, [setActiveMenu]);

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

  if (error) return <ErrShell msg={error} />;
  if (!score) return <LoadShell />;

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
          title={`Signal Drivers — ${entityName ?? "Your entity"}`}
          subtitle="Each signal-driven modifier's effect on your final premium"
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

        <StandardCard
          title="All signal drivers"
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


function LoadShell() {
  return (
    <ViewCanvas>
      <CardGrid cols="grid-cols-1">
        <StandardCard title="Loading" lucideIcon={ListChecks}>
          <p className="text-sm">Computing signal impact breakdown…</p>
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

"use client";

// v8 Phase 8 — /portal/actions
//
// Full action plan: leverage-sorted remediation actions for the
// user's latest submission. Each card shows headline, description,
// effort, duration, cost, expected premium reduction, and evidence
// requirement.

import { useEffect, useState } from "react";

import {
  AlertTriangle,
  ChartPie,
  Gauge,
  Lightbulb,
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
  StatsGrid,
} from "@/components/base/content/primatives";

import { useAuthStore } from "@/store/authStore";
import { useDsiStore } from "@/store/dsiStore";
import {
  fetchOverview,
  fetchSubmissionActions,
} from "@/lib/portalApi";
import { formatCurrency, formatNumber } from "@/lib/format";
import type {
  ActionsResponse,
  ClientOverviewResponse,
  RemediationAction,
} from "@/types/portal";


export default function ActionsPage() {
  const accessToken = useAuthStore((s) => s.accessToken);
  const setActiveMenu = useDsiStore((s) => s.setActiveMenu);

  const [actions, setActions] = useState<ActionsResponse | null>(null);
  const [entityName, setEntityName] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => { setActiveMenu("Action Plan"); }, [setActiveMenu]);

  useEffect(() => {
    let cancelled = false;
    async function load() {
      try {
        const overview = await fetchOverview(accessToken);
        if (cancelled) return;
        if (overview.role !== "CLIENT") {
          setError("Action plan view is currently for client users.");
          return;
        }
        const primary = (overview as ClientOverviewResponse).active_coverages[0];
        if (!primary) {
          setError("No active coverage to build actions for.");
          return;
        }
        setEntityName((overview as ClientOverviewResponse).entity_name);
        const a = await fetchSubmissionActions(accessToken, primary.submission_code);
        if (!cancelled) setActions(a);
      } catch (e) {
        if (!cancelled) setError(e instanceof Error ? e.message : String(e));
      }
    }
    if (accessToken) load();
    return () => { cancelled = true; };
  }, [accessToken]);

  if (error) return <ErrShell msg={error} />;
  if (!actions) return <LoadShell />;

  const plan = actions.remediation_plan.actions;
  const totalSavings = plan.reduce((a, action) => a + Math.abs(action.estimated_premium_delta_usd), 0);
  const lowEffort = plan.filter((a) => a.remediation.effort === "LOW").length;
  const mediumEffort = plan.filter((a) => a.remediation.effort === "MEDIUM").length;
  const highEffort = plan.filter((a) => a.remediation.effort === "HIGH").length;

  return (
    <ViewCanvas>
      <CardGrid cols="grid-cols-1" className="gap-4">

        <SubmissionHeaderCard
          decision="approve"
          title={`Action Plan — ${entityName ?? "Your entity"}`}
          subtitle="Prioritised by leverage (premium impact ÷ effort)"
          lucideIcon={Lightbulb}
        >
          <StatsGrid
            columns={[
              { label: "Actions",      value: plan.length, align: "center" },
              { label: "Low effort",   value: lowEffort, align: "center" },
              { label: "Medium",       value: mediumEffort, align: "center" },
              { label: "High effort",  value: highEffort, align: "center" },
              { label: "Total savings", value: formatCurrency(totalSavings, 0), align: "center" },
            ]}
          />
        </SubmissionHeaderCard>

        {plan.length === 0 ? (
          <StandardCard title="No actions required" lucideIcon={Gauge}>
            <p className="text-sm">
              Nothing material is dragging your score right now. Maintain
              current posture; we'll surface new recommendations as signals
              evolve.
            </p>
          </StandardCard>
        ) : (
          <CardGrid cols="grid-cols-1 lg:grid-cols-2" className="gap-4">
            {plan.map((action, idx) => (
              <ActionDetailCard key={action.signal_key} action={action} rank={idx + 1} />
            ))}
          </CardGrid>
        )}

        {actions.remediation_plan.placeholder_count > 0 && (
          <InfoPanel
            label="Authoring debt"
            aside={`${actions.remediation_plan.placeholder_count} placeholder${
              actions.remediation_plan.placeholder_count === 1 ? "" : "s"
            }`}
          >
            <p className="text-xs">
              Some drag signals don't yet have specific remediation guidance
              authored. Your broker may have additional context on the best
              path forward for these.
            </p>
          </InfoPanel>
        )}

      </CardGrid>
    </ViewCanvas>
  );
}


function ActionDetailCard({
  action, rank,
}: {
  action: RemediationAction;
  rank: number;
}) {
  const effortColor =
    action.remediation.effort === "LOW"
      ? "text-generate-text-good"
      : action.remediation.effort === "MEDIUM"
      ? "text-generate-text-maybe"
      : "text-generate-text-bad";

  return (
    <StandardCard
      title={`${rank}. ${action.remediation.headline}`}
      lucideIcon={Zap}
      headerRight={
        <span className={`text-xs font-bold ${effortColor}`}>
          {action.remediation.effort}
        </span>
      }
    >
      <div className={`space-y-3 py-2 ${action.is_placeholder ? "opacity-60" : ""}`}>
        <p className="text-sm">{action.remediation.description}</p>

        <LabelValueList
          variant="card"
          rows={[
            {
              label: "Estimated premium reduction",
              value: (
                <span className="text-generate-text-good font-bold">
                  -{formatCurrency(Math.abs(action.estimated_premium_delta_usd), 0)}
                  {" "}
                  <span className="text-xs">
                    ({formatNumber(Math.abs(action.estimated_premium_delta_pct) * 100, 1)}%)
                  </span>
                </span>
              ),
            },
            { label: "Typical duration", value: action.remediation.typical_duration },
            { label: "Approx. cost", value: formatCurrency(action.remediation.typical_cost_usd, 0) },
            { label: "Leverage score", value: formatNumber(action.leverage, 0) },
          ]}
        />

        <div className="pt-2 border-t border-generate-text-outline">
          <span className="text-xs text-generate-text-placeholder">Evidence required</span>
          <p className="text-xs mt-1">{action.remediation.evidence_required}</p>
        </div>

        {action.remediation.references.length > 0 && (
          <div className="pt-2 border-t border-generate-text-outline">
            <span className="text-xs text-generate-text-placeholder">References</span>
            <ul className="mt-1 space-y-0.5">
              {action.remediation.references.map((ref, i) => (
                <li key={i} className="text-xs">
                  <a
                    href={ref}
                    target="_blank"
                    rel="noreferrer"
                    className="underline hover:text-generate-text-input"
                  >
                    {ref}
                  </a>
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </StandardCard>
  );
}


function LoadShell() {
  return (
    <ViewCanvas>
      <CardGrid cols="grid-cols-1">
        <StandardCard title="Loading" lucideIcon={Lightbulb}>
          <p className="text-sm">Building your action plan…</p>
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

"use client";

// v8 Phase 8 polish — /client/actions
//
// Table-first action plan with a modal per row for the full detail
// (description, references, evidence, leverage math). Matches the
// carrier-side pattern of "summary table + click for richer modal".

import { useEffect, useMemo, useState } from "react";

import {
  ExternalLink,
  Gauge,
  Lightbulb,
  Zap,
} from "lucide-react";
import Modal from "@/components/base/modal";
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
  ClientOverviewResponse,
  RemediationAction,
} from "@/types/portal";
import { PageLoading, PageError } from "@/components/base/pageStates";
import { useRoleScopedFetch } from "@/lib/useRoleScopedFetch";


export default function ActionsPage() {
  const accessToken = useAuthStore((s) => s.accessToken);
  const setActiveMenu = useDsiStore((s) => s.setActiveMenu);

  const [selected, setSelected] = useState<RemediationAction | null>(null);

  useEffect(() => { setActiveMenu("Action Plan"); }, [setActiveMenu]);

  const { data: bundle, error } = useRoleScopedFetch({
    fetcher: async () => {
      const overview = await fetchOverview(accessToken);
      if (overview.role !== "CLIENT") {
        throw new Error("Action plan view is currently for client users.");
      }
      const clientData = overview as ClientOverviewResponse;
      const primary = clientData.active_coverages[0];
      if (!primary) {
        throw new Error("No active coverage to build actions for.");
      }
      const actions = await fetchSubmissionActions(accessToken, primary.submission_code);
      return { actions, entityName: clientData.entity_name };
    },
    enabled: !!accessToken,
  });

  if (error) return <PageError message={error} />;
  if (!bundle) return <PageLoading icon={Lightbulb} message="Building your action plan…" />;

  const { actions, entityName } = bundle;

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
              { label: "Actions",        value: plan.length, align: "center" },
              { label: "Low effort",     value: lowEffort, align: "center" },
              { label: "Medium",         value: mediumEffort, align: "center" },
              { label: "High effort",    value: highEffort, align: "center" },
              { label: "Total savings",  value: formatCurrency(totalSavings, 0), align: "center" },
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
          <StandardCard
            title={`Recommended actions (${plan.length})`}
            lucideIcon={Zap}
            headerRight={
              <span className="text-xs text-generate-text-placeholder">
                Click a row for detail
              </span>
            }
          >
            <ActionTable
              actions={plan}
              onSelect={(a) => setSelected(a)}
            />
          </StandardCard>
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
              authored. Your broker may have additional context.
            </p>
          </InfoPanel>
        )}

      </CardGrid>

      <ActionDetailModal
        action={selected}
        onClose={() => setSelected(null)}
      />
    </ViewCanvas>
  );
}


function ActionTable({
  actions, onSelect,
}: {
  actions: RemediationAction[];
  onSelect: (a: RemediationAction) => void;
}) {
  return (
    <div
      className="grid"
      style={{ gridTemplateColumns: "40px 3fr 90px 120px 1fr 90px" }}
    >
      {["#", "Action", "Effort", "Est. savings", "Leverage", ""].map((h, i) => (
        <div
          key={i}
          className="text-xs text-generate-text-placeholder border-b border-generate-text-outline pb-1.5 pt-1.5"
        >
          {h}
        </div>
      ))}
      {actions.map((a, idx) => (
        <ActionTableRow
          key={a.signal_key}
          rank={idx + 1}
          action={a}
          onClick={() => onSelect(a)}
        />
      ))}
    </div>
  );
}

function ActionTableRow({
  rank, action, onClick,
}: {
  rank: number;
  action: RemediationAction;
  onClick: () => void;
}) {
  const effortColor =
    action.remediation.effort === "LOW"
      ? "text-generate-text-good"
      : action.remediation.effort === "MEDIUM"
      ? "text-generate-text-maybe"
      : "text-generate-text-bad";
  const placeholderMute = action.is_placeholder ? "opacity-60" : "";
  return (
    <div
      onClick={onClick}
      className={`contents cursor-pointer group ${placeholderMute}`}
    >
      <div className="text-sm py-3 font-bold text-generate-text-placeholder group-hover:text-generate-text-input">
        {rank}
      </div>
      <div className="py-3 group-hover:text-generate-text-input">
        <div className="text-sm font-bold">{action.remediation.headline}</div>
        <div className="text-xs text-generate-text-placeholder mt-1">
          {action.signal_label}
          {action.is_placeholder && " · generic guidance"}
        </div>
      </div>
      <div className="text-sm py-3 flex items-center">
        <span className={`text-xs font-bold ${effortColor}`}>
          {action.remediation.effort}
        </span>
      </div>
      <div className="text-sm py-3 group-hover:text-generate-text-input">
        <span className="text-generate-text-good font-bold">
          -{formatCurrency(Math.abs(action.estimated_premium_delta_usd), 0)}
        </span>
        <div className="text-xs text-generate-text-placeholder">
          {formatNumber(Math.abs(action.estimated_premium_delta_pct) * 100, 1)}%
        </div>
      </div>
      <div className="text-sm py-3 group-hover:text-generate-text-input">
        {formatNumber(action.leverage, 0)}
      </div>
      <div className="text-sm py-3 flex items-center justify-end text-generate-text-placeholder group-hover:text-generate-text-input">
        <span className="text-xs underline">Detail →</span>
      </div>
    </div>
  );
}


function ActionDetailModal({
  action, onClose,
}: {
  action: RemediationAction | null;
  onClose: () => void;
}) {
  return (
    <Modal
      isOpen={action !== null}
      onClose={onClose}
      title={action?.remediation.headline ?? ""}
      icon={Zap}
    >
      {action && (
        <div className="space-y-4">
          <p className="text-sm">{action.remediation.description}</p>

          <LabelValueList
            variant="modal"
            rows={[
              { label: "Signal", value: action.signal_label },
              { label: "Effort", value: action.remediation.effort },
              { label: "Typical duration", value: action.remediation.typical_duration },
              { label: "Approx. cost", value: formatCurrency(action.remediation.typical_cost_usd, 0) },
              { label: "Estimated savings", value: (
                <span className="text-generate-text-good font-bold">
                  -{formatCurrency(Math.abs(action.estimated_premium_delta_usd), 0)}
                  {" "}
                  <span className="text-xs">
                    ({formatNumber(Math.abs(action.estimated_premium_delta_pct) * 100, 1)}%)
                  </span>
                </span>
              )},
              { label: "Leverage score", value: formatNumber(action.leverage, 0) },
            ]}
          />

          <div className="pt-3 border-t border-generate-text-outline">
            <div className="text-xs text-generate-text-placeholder mb-1 uppercase tracking-wide">
              Evidence required
            </div>
            <p className="text-sm">{action.remediation.evidence_required}</p>
          </div>

          {action.remediation.references.length > 0 && (
            <div className="pt-3 border-t border-generate-text-outline">
              <div className="text-xs text-generate-text-placeholder mb-1 uppercase tracking-wide">
                References
              </div>
              <ul className="space-y-1">
                {action.remediation.references.map((ref, i) => (
                  <li key={i}>
                    <a
                      href={ref}
                      target="_blank"
                      rel="noreferrer"
                      className="text-sm flex items-center gap-1 underline hover:text-generate-text-input"
                    >
                      {ref} <ExternalLink className="generate-app-icon" />
                    </a>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </Modal>
  );
}
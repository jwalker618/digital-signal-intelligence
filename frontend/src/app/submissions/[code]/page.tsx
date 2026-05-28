"use client";

// v8 Phase 8 — /submissions/[code]
//
// Drill-down view for one submission. Sections:
//   - SubmissionHeaderCard with score / tier / premium / percentile
//   - Signal drivers (strengths and drags) -- Phase 3 data
//   - Peer comparison -- Phase 2 data
//   - Action plan -- Phase 4 data
//   - Quote evolution timeline -- Act 7's "Marsh saved you $X" story
//   - Referral thread + broker reply form when AWAITING_BROKER

import { use, useEffect, useState } from "react";
import Link from "next/link";

import {
  ArrowRight,
  ChartPie,
  Gauge,
  Inbox,
  Layers,
  Lightbulb,
  ListChecks,
  Send,
  TrendingUpDown,
  UserStar,
} from "lucide-react";

import ViewCanvas from "@/components/ViewCanvas";
import {
  CardGrid,
  StandardCard,
  SubmissionHeaderCard,
} from "@/components/base/cards";
import {
  ExpandableGroupTable,
  InfoPanel,
  KpiTile,
  LabelValueList,
  ScoreBar,
  type ExpandableGroup,
} from "@/components/base/content/primatives";

import { useAuthStore } from "@/store/authStore";
import { homePathForRole } from "@/lib/portalPaths";
import { useDsiStore } from "@/store/dsiStore";
import {
  fetchSubmissionActions,
  fetchSubmissionDetail,
  fetchSubmissionPeers,
  fetchSubmissionScore,
  postBrokerReply,
} from "@/lib/portalApi";
import { formatCurrency, formatNumber } from "@/lib/format";
import { opportunityFromDrag, peerStandingPositive, tierStatus } from "@/lib/portalTone";
import type {
  ActionsResponse,
  PeersResponse,
  RemediationAction,
  ScoreResponse,
  SignalImpact,
  SubmissionDetailResponse,
} from "@/types/portal";


export default function SubmissionDetailPage({
  params,
}: {
  params: Promise<{ code: string }>;
}) {
  const { code } = use(params);
  const accessToken = useAuthStore((s) => s.accessToken);
  const userRole = useAuthStore((s) => s.user?.role ?? null);
  const setActiveMenu = useDsiStore((s) => s.setActiveMenu);

  const [detail, setDetail] = useState<SubmissionDetailResponse | null>(null);
  const [score, setScore] = useState<ScoreResponse | null>(null);
  const [peers, setPeers] = useState<PeersResponse | null>(null);
  const [actions, setActions] = useState<ActionsResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [reloadKey, setReloadKey] = useState(0);

  useEffect(() => {
    setActiveMenu("Submission Detail");
  }, [setActiveMenu]);

  useEffect(() => {
    let cancelled = false;
    async function load() {
      try {
        const [d, s, p, a] = await Promise.all([
          fetchSubmissionDetail(accessToken, code),
          fetchSubmissionScore(accessToken, code),
          fetchSubmissionPeers(accessToken, code),
          fetchSubmissionActions(accessToken, code),
        ]);
        if (cancelled) return;
        setDetail(d); setScore(s); setPeers(p); setActions(a);
      } catch (e) {
        if (!cancelled) setError(e instanceof Error ? e.message : String(e));
      }
    }
    if (accessToken) load();
    return () => { cancelled = true; };
  }, [accessToken, code, reloadKey]);

  if (error) return <PortalError message={error} />;
  if (!detail || !score) return <PortalLoading />;

  const decision = detail.referral?.status === "awaiting_broker"
    ? "refer"
    : detail.referral?.status === "approved"
    ? "approve"
    : detail.referral?.status === "declined"
    ? "decline"
    : "approve";

  return (
    <ViewCanvas>
      <CardGrid cols="grid-cols-1" className="gap-4">

        <SubmissionHeaderCard
          decision={decision}
          title={detail.entity_name}
          subtitle={`${detail.coverage} · ${detail.status}`}
          headerRight={
            <Link
              href={homePathForRole(userRole)}
              className="text-xs underline hover:text-generate-text-input"
            >
              ← Back
            </Link>
          }
          lucideIcon={Gauge}
        >
          <div className="grid grid-cols-2 md:grid-cols-4 gap-6 py-2">
            <KpiTile
              label="Signal score"
              value={formatNumber(score.composite_score ?? 0, 0)}
              variant="emphasis"
              lucideIcon={Gauge}
            />
            <KpiTile
              label="Status"
              value={tierStatus(score.tier).label}
              lucideIcon={Layers}
            />
            <KpiTile
              label="Premium"
              value={
                score.final_premium != null
                  ? formatCurrency(score.final_premium, 0)
                  : "—"
              }
              subtext={
                score.base_premium != null
                  ? `Base ${formatCurrency(score.base_premium, 0)}`
                  : undefined
              }
              lucideIcon={ChartPie}
            />
            <KpiTile
              label="Peer percentile"
              value={
                peers?.peer_percentile_rank != null
                  ? `${formatNumber(peers.peer_percentile_rank, 0)}th`
                  : "—"
              }
              subtext={
                peers?.cohort_size != null
                  ? `of ${peers.cohort_size} peers`
                  : undefined
              }
              lucideIcon={TrendingUpDown}
            />
          </div>
        </SubmissionHeaderCard>

        {/* Signal drivers ----------------------------------------- */}
        <StandardCard
          title="What's helping and hurting"
          lucideIcon={ListChecks}
          headerRight={
            <Link
              href="/client/drivers"
              className="text-xs underline hover:text-generate-text-input flex items-center gap-1"
            >
              Full driver detail <ArrowRight className="generate-app-icon" />
            </Link>
          }
        >
          <SignalDriversInline impact={score} />
        </StandardCard>

        {/* Peer comparison ---------------------------------------- */}
        <StandardCard
          title="Peer comparison"
          lucideIcon={TrendingUpDown}
          headerRight={
            <Link
              href="/client/peers"
              className="text-xs underline hover:text-generate-text-input flex items-center gap-1"
            >
              Full peer view <ArrowRight className="generate-app-icon" />
            </Link>
          }
        >
          <PeerCardInline peers={peers} score={score} />
        </StandardCard>

        {/* Actions ------------------------------------------------ */}
        <StandardCard
          title="Prioritised actions"
          lucideIcon={Lightbulb}
          headerRight={
            <Link
              href="/client/actions"
              className="text-xs underline hover:text-generate-text-input flex items-center gap-1"
            >
              Full plan <ArrowRight className="generate-app-icon" />
            </Link>
          }
        >
          <ActionsInline actions={actions} />
        </StandardCard>

        {/* Quote evolution timeline ------------------------------- */}
        <StandardCard
          title="Quote history"
          lucideIcon={ChartPie}
        >
          <QuoteHistoryInline detail={detail} />
        </StandardCard>

        {/* Referral thread ---------------------------------------- */}
        {detail.referral && (
          <StandardCard
            title="Referral thread"
            lucideIcon={UserStar}
            headerRight={
              <span
                className={
                  detail.referral.status === "awaiting_broker"
                    ? "text-xs text-generate-text-maybe font-bold"
                    : "text-xs text-generate-text-placeholder"
                }
              >
                {detail.referral.status}
              </span>
            }
          >
            <ReferralBlockInline
              detail={detail}
              userRole={userRole}
              accessToken={accessToken}
              onReplied={() => setReloadKey((k) => k + 1)}
            />
          </StandardCard>
        )}

      </CardGrid>
    </ViewCanvas>
  );
}


// ----------------------------------------------------------------------------
// Loading / error
// ----------------------------------------------------------------------------

function PortalLoading() {
  return (
    <ViewCanvas>
      <CardGrid cols="grid-cols-1">
        <StandardCard title="Loading" lucideIcon={Gauge}>
          <p className="text-sm">Fetching submission detail…</p>
        </StandardCard>
      </CardGrid>
    </ViewCanvas>
  );
}

function PortalError({ message }: { message: string }) {
  return (
    <ViewCanvas>
      <CardGrid cols="grid-cols-1">
        <StandardCard title="Unable to load" lucideIcon={Gauge}>
          <p className="text-sm text-generate-text-bad">{message}</p>
        </StandardCard>
      </CardGrid>
    </ViewCanvas>
  );
}


// ----------------------------------------------------------------------------
// Inline sections — used both here and on the dedicated /client/drivers,
// /client/peers, /client/actions pages.
// ----------------------------------------------------------------------------

export function SignalDriversInline({ impact }: { impact: ScoreResponse }) {
  const drags = impact.impact_breakdown?.drags ?? [];
  const strengths = impact.impact_breakdown?.strengths ?? [];

  const groups: ExpandableGroup<SignalImpact>[] = [
    {
      key: "drags",
      title: `Opportunities (${drags.length}) — improving these would lower your premium`,
      items: drags.slice(0, 8),
      summary: [
        `${drags.length} signal${drags.length === 1 ? "" : "s"}`,
        formatCurrency(
          drags.reduce((a, d) => a + Math.abs(d.premium_delta_usd), 0), 0,
        ),
      ],
      emptyMessage: "No opportunities identified yet — clean profile.",
    },
    {
      key: "strengths",
      title: `Strengths (${strengths.length}) — already lowering your premium`,
      items: strengths.slice(0, 8),
      summary: [
        `${strengths.length} signal${strengths.length === 1 ? "" : "s"}`,
        formatCurrency(
          strengths.reduce((a, s) => a + Math.abs(s.premium_delta_usd), 0), 0,
        ),
      ],
      emptyMessage: "No strengths identified yet.",
    },
  ];

  return (
    <ExpandableGroupTable
      title=""
      defaultExpanded={{ drags: true, strengths: false }}
      columns={[
        { label: "Signal", width: "60%", align: "left", headeralign: "left" },
        { label: "Count", width: "20%", align: "center", headeralign: "center" },
        { label: "Impact", width: "20%", align: "right", headeralign: "right" },
      ]}
      groups={groups}
      renderItemCells={(item) => [
        item.signal_label,
        "",
        <span
          key={item.signal_key}
          className={
            item.classification === "drag"
              ? "text-generate-text-bad font-bold"
              : "text-generate-text-good font-bold"
          }
        >
          {item.classification === "drag"
            ? opportunityFromDrag(item.premium_delta_usd).framing
            : `Saving ${formatCurrency(Math.abs(item.premium_delta_usd), 0)}`}
        </span>,
      ]}
    />
  );
}


export function PeerCardInline({
  peers, score,
}: {
  peers: PeersResponse | null;
  score: ScoreResponse;
}) {
  if (!peers || peers.peer_percentile_rank == null) {
    return (
      <InfoPanel label="Peer cohort">
        <p className="text-sm">
          {peers?.note ?? "Cohort not yet established for this entity."}
        </p>
      </InfoPanel>
    );
  }

  const subjectScore = score.composite_score ?? 0;
  const cohortMean = peers.cohort_mean_score ?? 0;
  const delta = subjectScore - cohortMean;

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <KpiTile
          label="Your score"
          value={formatNumber(subjectScore, 0)}
          variant="emphasis"
        />
        <KpiTile
          label={`Cohort average (${peers.cohort_size ?? 0} peers)`}
          value={formatNumber(cohortMean, 0)}
        />
        <KpiTile
          label="vs cohort"
          value={`${delta >= 0 ? "+" : ""}${formatNumber(delta, 0)}`}
          subtext={delta >= 0 ? "Above average" : "Below average"}
        />
      </div>
      <div>
        <span className="text-xs text-generate-text-placeholder">
          Your percentile rank
        </span>
        <ScoreBar
          value={peers.peer_percentile_rank}
          min={0}
          max={100}
          decimals={0}
          thresholds={[
            { at: 25, color: "var(--color-generate-text-bad)" },
            { at: 50, color: "var(--color-generate-text-maybe)" },
            { at: 75, color: "var(--color-generate-text-comment)" },
            { at: Infinity, color: "var(--color-generate-text-good)" },
          ]}
        />
      </div>
    </div>
  );
}


export function ActionsInline({ actions }: { actions: ActionsResponse | null }) {
  if (!actions || actions.remediation_plan.actions.length === 0) {
    return <p className="text-sm">No remediation actions needed.</p>;
  }
  const top = actions.remediation_plan.actions.slice(0, 4);
  return (
    <CardGrid cols="grid-cols-1 md:grid-cols-2" className="gap-3">
      {top.map((a) => (
        <ActionCard key={a.signal_key} action={a} />
      ))}
    </CardGrid>
  );
}

export function ActionCard({ action }: { action: RemediationAction }) {
  const effortColor =
    action.remediation.effort === "LOW"
      ? "text-generate-text-good"
      : action.remediation.effort === "MEDIUM"
      ? "text-generate-text-maybe"
      : "text-generate-text-bad";

  return (
    <InfoPanel
      label={
        <span className={`flex items-center gap-2 ${action.is_placeholder ? "opacity-60" : ""}`}>
          {action.remediation.headline}
        </span>
      }
      aside={
        <span className={`text-xs font-bold ${effortColor}`}>
          {action.remediation.effort}
        </span>
      }
    >
      <p className="text-xs mt-1 mb-2">{action.remediation.description}</p>
      <LabelValueList
        variant="card"
        rows={[
          { label: "Est. premium reduction", value: (
            <span className="text-generate-text-good font-bold">
              -{formatCurrency(Math.abs(action.estimated_premium_delta_usd), 0)}
            </span>
          )},
          { label: "Duration", value: action.remediation.typical_duration },
          { label: "Approx cost", value: formatCurrency(action.remediation.typical_cost_usd, 0) },
        ]}
      />
    </InfoPanel>
  );
}


export function QuoteHistoryInline({
  detail,
}: {
  detail: SubmissionDetailResponse;
}) {
  if (!detail.quotes.length) {
    return <p className="text-sm">No quote history yet.</p>;
  }
  const quotes = [...detail.quotes].reverse();  // newest first

  return (
    <div className="space-y-2">
      {quotes.map((q, idx) => {
        const next = idx < quotes.length - 1 ? quotes[idx + 1] : null;
        const premiumDelta = next && q.final_premium != null && next.final_premium != null
          ? q.final_premium - next.final_premium
          : null;
        const scoreDelta = next && q.composite_score != null && next.composite_score != null
          ? q.composite_score - next.composite_score
          : null;
        return (
          <div
            key={q.quote_code}
            className="flex justify-between items-center py-2 border-b border-generate-text-outline"
          >
            <div>
              <div className="text-sm font-bold">
                Quote v{q.version_number}
                {idx === 0 && <span className="ml-2 text-xs text-generate-text-good">latest</span>}
              </div>
              <div className="text-xs text-generate-text-placeholder">
                {new Date(q.created_at).toLocaleString()}
              </div>
            </div>
            <div className="text-right">
              <div className="text-sm">
                Score {q.composite_score != null ? formatNumber(q.composite_score, 0) : "—"}
                {scoreDelta != null && scoreDelta !== 0 && (
                  <span className={scoreDelta > 0 ? "ml-2 text-generate-text-good" : "ml-2 text-generate-text-bad"}>
                    ({scoreDelta > 0 ? "+" : ""}{formatNumber(scoreDelta, 0)})
                  </span>
                )}
                {" · Tier "}{q.tier ?? "—"}
              </div>
              <div className="text-sm font-bold">
                {q.final_premium != null ? formatCurrency(q.final_premium, 0) : "—"}
                {premiumDelta != null && premiumDelta !== 0 && (
                  <span className={premiumDelta < 0 ? "ml-2 text-generate-text-good" : "ml-2 text-generate-text-bad"}>
                    ({premiumDelta < 0 ? "−" : "+"}{formatCurrency(Math.abs(premiumDelta), 0)})
                  </span>
                )}
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
}


function ReferralBlockInline({
  detail, userRole, accessToken, onReplied,
}: {
  detail: SubmissionDetailResponse;
  userRole: string | null;
  accessToken: string | null;
  onReplied: () => void;
}) {
  const ref = detail.referral!;
  const isAwaitingBroker = ref.status === "awaiting_broker";
  const isBroker = userRole === "BROKER";

  if (isAwaitingBroker && isBroker) {
    return (
      <BrokerReplyForm
        referralCode={ref.referral_code}
        accessToken={accessToken}
        onSubmitted={onReplied}
      />
    );
  }
  if (isAwaitingBroker && !isBroker) {
    return (
      <InfoPanel label="Status">
        <p className="text-sm">
          Awaiting broker response to underwriter query. Once your broker
          confirms, the quote will be re-assessed.
        </p>
      </InfoPanel>
    );
  }
  return (
    <p className="text-sm">
      Referral status: <span className="font-bold">{ref.status}</span>
    </p>
  );
}


function BrokerReplyForm({
  referralCode, accessToken, onSubmitted,
}: {
  referralCode: string;
  accessToken: string | null;
  onSubmitted: () => void;
}) {
  const [body, setBody] = useState(
    "MFA was deployed across all admin accounts in Q1 2026. " +
    "Attached attestation confirms enforcement."
  );
  const [signalId, setSignalId] = useState("mfa_enabled");
  const [newValue, setNewValue] = useState<"true" | "false">("true");
  const [submitting, setSubmitting] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setSubmitting(true); setErr(null);
    try {
      await postBrokerReply(accessToken, referralCode, {
        body,
        signal_value_update: {
          signal_id: signalId,
          new_value: newValue === "true",
        },
      });
      onSubmitted();
    } catch (e) {
      setErr(e instanceof Error ? e.message : String(e));
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <form onSubmit={onSubmit} className="space-y-3">
      <div>
        <label className="block text-xs text-generate-text-placeholder mb-1">
          Response to underwriter
        </label>
        <textarea
          value={body}
          onChange={(e) => setBody(e.target.value)}
          rows={3}
          className="
            w-full text-sm
            bg-generate-light-input
            border border-generate-text-outline
            rounded-md p-2
            focus:outline-none focus:border-generate-text-input"
          required
        />
      </div>
      <div className="grid grid-cols-3 gap-3">
        <div className="col-span-2">
          <label className="block text-xs text-generate-text-placeholder mb-1">
            Signal to update
          </label>
          <input
            value={signalId}
            onChange={(e) => setSignalId(e.target.value)}
            className="
              w-full text-sm
              bg-generate-light-input
              border border-generate-text-outline
              rounded-md p-2"
          />
        </div>
        <div>
          <label className="block text-xs text-generate-text-placeholder mb-1">
            Value
          </label>
          <select
            value={newValue}
            onChange={(e) => setNewValue(e.target.value as "true" | "false")}
            className="
              w-full text-sm
              bg-generate-light-input
              border border-generate-text-outline
              rounded-md p-2"
          >
            <option value="true">true (deployed)</option>
            <option value="false">false (not in place)</option>
          </select>
        </div>
      </div>
      {err && (
        <p className="text-xs text-generate-text-bad">{err}</p>
      )}
      <button
        type="submit"
        disabled={submitting}
        className="
          flex items-center gap-2
          bg-generate-dark-background text-generate-text-input
          rounded-md px-4 py-2 text-sm font-bold
          hover:opacity-90 disabled:opacity-50"
      >
        <Send className="generate-app-icon" />
        {submitting ? "Submitting…" : "Submit reply & trigger re-assessment"}
      </button>
    </form>
  );
}

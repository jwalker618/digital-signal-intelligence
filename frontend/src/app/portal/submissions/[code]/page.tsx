"use client";

// v8 Phase 8 — /portal/submissions/[code]
//
// Detail view for a single submission. Shows:
//   - Headline numbers (score, tier, premium)
//   - Impact breakdown: strengths and drags by $-impact
//   - Peer comparison: cohort size, mean, your percentile
//   - Remediation plan: leverage-sorted actions
//   - Quote evolution timeline (Act 7's "Marsh saved you $X" story)
//   - Referral thread (if open) -- broker reply form when AWAITING_BROKER

import { use, useEffect, useState } from "react";
import Link from "next/link";

import { useAuthStore } from "@/store/authStore";
import {
  fetchSubmissionActions,
  fetchSubmissionDetail,
  fetchSubmissionPeers,
  fetchSubmissionScore,
  postBrokerReply,
} from "@/lib/portalApi";
import type {
  ActionsResponse,
  PeersResponse,
  RemediationAction,
  ScoreResponse,
  SignalImpact,
  SubmissionDetailResponse,
} from "@/types/portal";

export default function SubmissionDetailPage(
  { params }: { params: Promise<{ code: string }> },
) {
  const { code } = use(params);
  const accessToken = useAuthStore((s) => s.accessToken);
  const userRole = useAuthStore((s) => s.user?.role ?? null);

  const [detail, setDetail] = useState<SubmissionDetailResponse | null>(null);
  const [score, setScore] = useState<ScoreResponse | null>(null);
  const [peers, setPeers] = useState<PeersResponse | null>(null);
  const [actions, setActions] = useState<ActionsResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [reloadKey, setReloadKey] = useState(0);

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

  if (error) return <Shell><p className="text-red-600">{error}</p></Shell>;
  if (!detail || !score) return <Shell><p>Loading…</p></Shell>;

  return (
    <Shell>
      <div className="mb-6">
        <Link href="/portal" className="text-sm underline opacity-70">
          ← Overview
        </Link>
      </div>
      <h1 className="text-2xl font-semibold mb-1">{detail.entity_name}</h1>
      <div className="text-sm opacity-70 mb-6 capitalize">
        {detail.coverage} · {detail.status}
      </div>

      <Headline score={score} peers={peers} />

      <Section title="What's helping and hurting your score">
        <ImpactList drags={score.impact_breakdown?.drags ?? []}
                    strengths={score.impact_breakdown?.strengths ?? []} />
      </Section>

      <Section title="Peer comparison">
        <PeerCard peers={peers} />
      </Section>

      <Section title="Prioritised actions">
        <ActionList actions={actions?.remediation_plan.actions ?? []} />
      </Section>

      <Section title="Quote history">
        <QuoteHistory detail={detail} />
      </Section>

      {detail.referral && (
        <Section title="Referral">
          <ReferralBlock
            detail={detail}
            userRole={userRole}
            accessToken={accessToken}
            onReplied={() => setReloadKey((k) => k + 1)}
          />
        </Section>
      )}
    </Shell>
  );
}

function Shell({ children }: { children: React.ReactNode }) {
  return <div className="p-8 max-w-5xl mx-auto">{children}</div>;
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section className="mt-8">
      <h2 className="text-lg font-semibold mb-3">{title}</h2>
      {children}
    </section>
  );
}

// ---------------------------------------------------------------------------
// Headline numbers
// ---------------------------------------------------------------------------

function Headline({ score, peers }: { score: ScoreResponse; peers: PeersResponse | null }) {
  const pct = peers?.peer_percentile_rank;
  return (
    <div className="grid grid-cols-1 sm:grid-cols-4 gap-4 mb-6 border rounded-lg p-4">
      <Stat label="Signal score" value={score.composite_score?.toFixed(0) ?? "—"} />
      <Stat label="Tier" value={score.tier?.toString() ?? "—"} />
      <Stat
        label="Premium"
        value={
          score.final_premium != null
            ? `$${score.final_premium.toLocaleString()}`
            : "—"
        }
      />
      <Stat
        label="Peer percentile"
        value={pct != null ? `${pct.toFixed(0)}th` : "—"}
      />
    </div>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <div className="text-xs opacity-70 uppercase tracking-wide">{label}</div>
      <div className="text-2xl font-semibold mt-1">{value}</div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Impact list
// ---------------------------------------------------------------------------

function ImpactList(
  { drags, strengths }: { drags: SignalImpact[]; strengths: SignalImpact[] },
) {
  if (drags.length === 0 && strengths.length === 0) {
    return <p className="opacity-70">No signal-driven modifiers on this quote.</p>;
  }
  return (
    <div className="grid gap-4 sm:grid-cols-2">
      <div>
        <div className="text-sm font-medium mb-2 text-green-700">Strengths</div>
        {strengths.length === 0 ? (
          <p className="text-sm opacity-60">None</p>
        ) : strengths.slice(0, 6).map((s) => (
          <ImpactRow key={s.signal_key} impact={s} positive />
        ))}
      </div>
      <div>
        <div className="text-sm font-medium mb-2 text-red-700">Drags</div>
        {drags.length === 0 ? (
          <p className="text-sm opacity-60">None</p>
        ) : drags.slice(0, 6).map((d) => (
          <ImpactRow key={d.signal_key} impact={d} positive={false} />
        ))}
      </div>
    </div>
  );
}

function ImpactRow({ impact, positive }: { impact: SignalImpact; positive: boolean }) {
  return (
    <div className="flex justify-between border-b py-2 text-sm">
      <span>{impact.signal_label}</span>
      <span className={positive ? "text-green-700" : "text-red-700"}>
        {positive ? "−" : "+"}${Math.abs(impact.premium_delta_usd).toLocaleString(undefined, { maximumFractionDigits: 0 })}
      </span>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Peer card
// ---------------------------------------------------------------------------

function PeerCard({ peers }: { peers: PeersResponse | null }) {
  if (!peers) return <p className="opacity-70">—</p>;
  if (peers.note && peers.peer_percentile_rank == null) {
    return <p className="opacity-70 text-sm">{peers.note}</p>;
  }
  return (
    <div className="border rounded-lg p-4 text-sm">
      <p>
        You rank <strong>{peers.peer_percentile_rank?.toFixed(0)}th</strong> of{" "}
        {peers.cohort_size} peers in your cohort
        {peers.cohort_id && (
          <span className="opacity-60"> ({peers.cohort_id})</span>
        )}
        .
      </p>
      {peers.cohort_mean_score != null && (
        <p className="mt-1">
          Peers average <strong>{peers.cohort_mean_score.toFixed(0)}</strong>; your score is{" "}
          <strong>{peers.entity_score?.toFixed(0)}</strong>.
        </p>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Action list
// ---------------------------------------------------------------------------

function ActionList({ actions }: { actions: RemediationAction[] }) {
  if (actions.length === 0) {
    return <p className="opacity-70">No actions needed -- nothing material is dragging your score.</p>;
  }
  return (
    <div className="space-y-3">
      {actions.slice(0, 6).map((a) => (
        <div
          key={a.signal_key}
          className={`border rounded-lg p-4 ${a.is_placeholder ? "opacity-60" : ""}`}
        >
          <div className="flex justify-between items-baseline">
            <h3 className="font-medium">{a.remediation.headline}</h3>
            <EffortBadge effort={a.remediation.effort} />
          </div>
          <p className="text-sm mt-1">{a.remediation.description}</p>
          <div className="flex gap-4 text-xs mt-2 opacity-70">
            <span>{a.remediation.typical_duration}</span>
            <span>~${a.remediation.typical_cost_usd.toLocaleString()}</span>
            <span className="text-green-700">
              Est. save ${Math.abs(a.estimated_premium_delta_usd).toLocaleString(undefined, { maximumFractionDigits: 0 })}
            </span>
          </div>
          <p className="text-xs mt-2 opacity-70">
            Evidence: {a.remediation.evidence_required}
          </p>
        </div>
      ))}
    </div>
  );
}

function EffortBadge({ effort }: { effort: "LOW" | "MEDIUM" | "HIGH" }) {
  const colour = effort === "LOW"
    ? "bg-green-100 text-green-800"
    : effort === "MEDIUM"
    ? "bg-amber-100 text-amber-800"
    : "bg-red-100 text-red-800";
  return (
    <span className={`text-xs px-2 py-0.5 rounded-full ${colour}`}>
      {effort}
    </span>
  );
}

// ---------------------------------------------------------------------------
// Quote history
// ---------------------------------------------------------------------------

function QuoteHistory({ detail }: { detail: SubmissionDetailResponse }) {
  if (!detail.quotes.length) {
    return <p className="opacity-70">No quote history yet.</p>;
  }
  return (
    <div className="space-y-2">
      {detail.quotes.map((q, idx) => {
        const prev = idx > 0 ? detail.quotes[idx - 1] : null;
        const delta =
          prev && q.final_premium != null && prev.final_premium != null
            ? q.final_premium - prev.final_premium
            : null;
        return (
          <div key={q.quote_code} className="border rounded p-3 text-sm flex justify-between">
            <div>
              <div className="font-medium">Quote v{q.version_number}</div>
              <div className="opacity-60 text-xs">
                {new Date(q.created_at).toLocaleString()}
              </div>
            </div>
            <div className="text-right">
              <div>
                Score {q.composite_score?.toFixed(0) ?? "—"} · Tier {q.tier ?? "—"}
              </div>
              <div>
                {q.final_premium != null ? `$${q.final_premium.toLocaleString()}` : "—"}
                {delta != null && (
                  <span className={delta < 0 ? "ml-2 text-green-700" : "ml-2 text-red-700"}>
                    {delta < 0 ? "−" : "+"}${Math.abs(delta).toLocaleString(undefined, { maximumFractionDigits: 0 })}
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

// ---------------------------------------------------------------------------
// Referral block + broker reply form
// ---------------------------------------------------------------------------

function ReferralBlock(
  { detail, userRole, accessToken, onReplied }: {
    detail: SubmissionDetailResponse;
    userRole: string | null;
    accessToken: string | null;
    onReplied: () => void;
  },
) {
  const ref = detail.referral!;
  const isAwaitingBroker = ref.status === "awaiting_broker";
  const isBroker = userRole === "BROKER";

  return (
    <div className="border rounded-lg p-4 text-sm">
      <div className="flex items-baseline justify-between mb-2">
        <span className="font-medium">{ref.referral_code}</span>
        <span className={isAwaitingBroker ? "text-amber-700" : "opacity-70"}>
          {ref.status}
        </span>
      </div>
      {isAwaitingBroker && isBroker && (
        <BrokerReplyForm
          referralCode={ref.referral_code}
          accessToken={accessToken}
          onSubmitted={onReplied}
        />
      )}
      {isAwaitingBroker && !isBroker && (
        <p className="opacity-70">
          Awaiting broker response to underwriter query.
        </p>
      )}
    </div>
  );
}

function BrokerReplyForm(
  { referralCode, accessToken, onSubmitted }: {
    referralCode: string;
    accessToken: string | null;
    onSubmitted: () => void;
  },
) {
  const [body, setBody] = useState(
    "MFA was deployed across all admin accounts in Q1 2026. " +
    "See attached attestation."
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
        <label className="block text-xs opacity-70 mb-1">Response</label>
        <textarea
          value={body}
          onChange={(e) => setBody(e.target.value)}
          rows={3}
          className="w-full border rounded p-2 text-sm"
          required
        />
      </div>
      <div className="flex gap-3">
        <div className="flex-1">
          <label className="block text-xs opacity-70 mb-1">Signal</label>
          <input
            value={signalId}
            onChange={(e) => setSignalId(e.target.value)}
            className="w-full border rounded p-2 text-sm"
          />
        </div>
        <div>
          <label className="block text-xs opacity-70 mb-1">Value</label>
          <select
            value={newValue}
            onChange={(e) => setNewValue(e.target.value as "true" | "false")}
            className="border rounded p-2 text-sm"
          >
            <option value="true">true (yes)</option>
            <option value="false">false (no)</option>
          </select>
        </div>
      </div>
      {err && <p className="text-red-600 text-xs">{err}</p>}
      <button
        type="submit"
        disabled={submitting}
        className="bg-black text-white text-sm rounded px-4 py-2 disabled:opacity-50"
      >
        {submitting ? "Submitting…" : "Submit reply + trigger re-assessment"}
      </button>
    </form>
  );
}

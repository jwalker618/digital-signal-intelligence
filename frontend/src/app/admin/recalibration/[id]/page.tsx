// FE: Recalibration proposal detail + governance actions (C-3).
//
// Shows the statistical evidence, weight/tier diffs, and impact
// assessment. Approve / reject require a rationale. Deploy is gated
// to APPROVED status only.

"use client";

import { use, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import {
  AlertTriangle,
  ArrowLeft,
  CheckCircle2,
  PlayCircle,
  RefreshCw,
  Rocket,
  XCircle,
} from "lucide-react";

import { api, fmtDate } from "@/lib/api";
import { formatNumber } from "@/lib/format";
import { SubmissionStatusPill } from "@/components/base/content/primatives";
import { useAuthStore } from "@/store/authStore";
import type { ProposalDetail } from "@/types/recalibration";

export default function ProposalDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = use(params);
  const router = useRouter();
  const hasPermission = useAuthStore((s) => s.hasPermission);
  const canApprove = hasPermission("recalibration:approve");

  const [detail, setDetail] = useState<ProposalDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState<string | null>(null);
  const [rationale, setRationale] = useState("");
  const [simulation, setSimulation] = useState<unknown>(null);

  async function load() {
    setLoading(true);
    setError(null);
    try {
      const data = await api.get<ProposalDetail>(
        `/api/v1/recalibration/proposals/${id}`,
      );
      setDetail(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Load failed");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id]);

  async function act(
    endpoint: "approve" | "reject" | "deploy",
    withRationale: boolean,
  ) {
    if (withRationale && rationale.trim().length === 0) {
      setError("Rationale is required");
      return;
    }
    setBusy(endpoint);
    setError(null);
    try {
      await api.post(
        `/api/v1/recalibration/proposals/${id}/${endpoint}`,
        withRationale ? { rationale } : undefined,
      );
      setRationale("");
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : `${endpoint} failed`);
    } finally {
      setBusy(null);
    }
  }

  async function simulate() {
    setBusy("simulate");
    setError(null);
    try {
      const result = await api.post(
        `/api/v1/recalibration/proposals/${id}/simulate`,
      );
      setSimulation(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Simulation failed");
    } finally {
      setBusy(null);
    }
  }

  if (loading) return <main className="p-6 opacity-70">Loading…</main>;
  if (!detail) return <main className="p-6">Proposal not found.</main>;

  const canEdit =
    canApprove && ["DRAFT", "PENDING_REVIEW"].includes(detail.status);
  const canReject = canApprove && detail.status !== "DEPLOYED";
  const canDeploy = canApprove && detail.status === "APPROVED";

  return (
    <main className="p-6 flex flex-col gap-4">
      <header className="flex items-center gap-3">
        <button
          onClick={() => router.back()}
          className="flex items-center gap-1 text-sm hover:underline"
        >
          <ArrowLeft className="w-4 h-4" /> Back
        </button>
        <h1 className="font-inter text-2xl tracking-wide">
          Proposal
          <span className="font-mono text-sm opacity-60 ml-2">
            {detail.id.slice(0, 8)}…
          </span>
        </h1>
        <SubmissionStatusPill decision={detail.status} />
        <button
          onClick={() => void load()}
          className="ml-auto border-2 border-generate-text-outline py-1 px-3 rounded text-sm flex items-center gap-1"
        >
          <RefreshCw className="w-4 h-4" /> Refresh
        </button>
      </header>

      {error && (
        <div className="border-2 border-generate-text-bad rounded p-3 text-sm flex items-center gap-2">
          <AlertTriangle className="w-4 h-4 text-generate-text-bad" /> {error}
        </div>
      )}

      <section className="grid md:grid-cols-2 gap-4">
        <Card title="Scope">
          <dl className="grid grid-cols-[8rem_1fr] text-sm gap-y-1">
            <dt className="opacity-60">Coverage</dt>
            <dd className="font-mono">{detail.coverage}</dd>
            <dt className="opacity-60">Config</dt>
            <dd className="font-mono">{detail.config_name}</dd>
            <dt className="opacity-60">Trigger</dt>
            <dd>{detail.trigger}</dd>
            <dt className="opacity-60">Proposed by</dt>
            <dd className="font-mono text-xs">{detail.proposed_by}</dd>
            <dt className="opacity-60">Proposed at</dt>
            <dd>{fmtDate(detail.proposed_at)}</dd>
            <dt className="opacity-60">Sample size</dt>
            <dd className="tabular-nums">{detail.sample_size}</dd>
          </dl>
        </Card>
        <Card title="Review">
          <dl className="grid grid-cols-[8rem_1fr] text-sm gap-y-1">
            <dt className="opacity-60">Reviewer</dt>
            <dd className="font-mono text-xs">
              {detail.reviewer_id ?? "—"}
            </dd>
            <dt className="opacity-60">Decision</dt>
            <dd>{detail.review_decision ?? "—"}</dd>
            <dt className="opacity-60">Rationale</dt>
            <dd className="whitespace-pre-wrap">
              {detail.review_rationale ?? "—"}
            </dd>
            <dt className="opacity-60">Deployed version</dt>
            <dd className="font-mono text-xs">
              {detail.deployed_config_version_id ?? "—"}
            </dd>
          </dl>
        </Card>
      </section>

      {canApprove && (
        <section className="border-2 border-generate-text-outline rounded p-4 flex flex-col gap-2">
          <h2 className="font-semibold tracking-wider">Governance actions</h2>
          <textarea
            value={rationale}
            onChange={(e) => setRationale(e.target.value)}
            placeholder="Rationale (required for approve / reject)"
            rows={2}
            className="border-2 border-generate-text-outline bg-generate-light-background px-2 py-1 rounded text-sm"
          />
          <div className="flex items-center gap-2 flex-wrap">
            <button
              onClick={() => void simulate()}
              disabled={busy !== null}
              className="flex items-center gap-1 border-2 border-generate-text-outline py-1 px-3 rounded text-sm"
            >
              <PlayCircle className="w-4 h-4" /> Simulate
            </button>
            <button
              onClick={() => void act("approve", true)}
              disabled={!canEdit || busy !== null}
              className="flex items-center gap-1 bg-generate-text-good/20 border border-generate-text-good py-1 px-3 rounded text-sm disabled:opacity-50"
            >
              <CheckCircle2 className="w-4 h-4" /> Approve
            </button>
            <button
              onClick={() => void act("reject", true)}
              disabled={!canReject || busy !== null}
              className="flex items-center gap-1 bg-generate-text-bad/20 border border-generate-text-bad py-1 px-3 rounded text-sm disabled:opacity-50"
            >
              <XCircle className="w-4 h-4" /> Reject
            </button>
            <button
              onClick={() => void act("deploy", false)}
              disabled={!canDeploy || busy !== null}
              className="flex items-center gap-1 bg-generate-text-input/20 border border-generate-text-input py-1 px-3 rounded text-sm disabled:opacity-50"
            >
              <Rocket className="w-4 h-4" /> Deploy
            </button>
          </div>
        </section>
      )}

      <section className="grid md:grid-cols-2 gap-4">
        <Card title={`Weight changes (${detail.weight_changes.length})`}>
          <table className="w-full text-xs">
            <thead className="opacity-60 text-left">
              <tr>
                <th className="py-1">Signal</th>
                <th className="py-1 text-right">From</th>
                <th className="py-1 text-right">To</th>
                <th className="py-1">Why</th>
              </tr>
            </thead>
            <tbody>
              {detail.weight_changes.map((w) => (
                <tr
                  key={w.signal_id}
                  className="border-t border-generate-text-outline/20 align-top"
                >
                  <td className="py-1 pr-2 font-mono">{w.signal_id}</td>
                  <td className="py-1 pr-2 text-right tabular-nums">
                    {formatNumber(w.current_weight, 3)}
                  </td>
                  <td className="py-1 pr-2 text-right tabular-nums text-generate-text-input">
                    {formatNumber(w.proposed_weight, 3)}
                  </td>
                  <td className="py-1 opacity-80">{w.rationale}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </Card>
        <Card title={`Tier changes (${detail.tier_threshold_changes.length})`}>
          <table className="w-full text-xs">
            <thead className="opacity-60 text-left">
              <tr>
                <th className="py-1">Band</th>
                <th className="py-1">Boundary</th>
                <th className="py-1 text-right">From</th>
                <th className="py-1 text-right">To</th>
              </tr>
            </thead>
            <tbody>
              {detail.tier_threshold_changes.map((t, i) => (
                <tr
                  key={`${t.band_id}-${t.boundary}-${i}`}
                  className="border-t border-generate-text-outline/20"
                >
                  <td className="py-1 pr-2 font-mono">{t.band_id}</td>
                  <td className="py-1 pr-2">{t.boundary}</td>
                  <td className="py-1 pr-2 text-right tabular-nums">
                    {t.current_value}
                  </td>
                  <td className="py-1 text-right tabular-nums text-generate-text-input">
                    {t.proposed_value}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </Card>
      </section>

      {simulation !== null && (
        <Card title="Simulation">
          <pre className="text-xs whitespace-pre-wrap break-all overflow-auto max-h-64">
            {JSON.stringify(simulation, null, 2)}
          </pre>
        </Card>
      )}

      <details className="border-2 border-generate-text-outline rounded p-3 text-xs">
        <summary className="cursor-pointer font-semibold tracking-wider">
          Raw proposal payload
        </summary>
        <pre className="mt-2 whitespace-pre-wrap break-all overflow-auto max-h-96">
          {JSON.stringify(detail, null, 2)}
        </pre>
      </details>

      <div className="text-xs opacity-50">
        <Link href="/admin/recalibration" className="hover:underline">
          ← All proposals
        </Link>
      </div>
    </main>
  );
}

function Card({
  title,
  children,
}: {
  title: string;
  children: React.ReactNode;
}) {
  return (
    <div className="border-2 border-generate-text-outline rounded p-4">
      <h2 className="font-semibold tracking-wider mb-2">{title}</h2>
      {children}
    </div>
  );
}

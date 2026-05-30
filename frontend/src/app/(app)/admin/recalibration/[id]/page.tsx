// No direct design counterpart; adapted from reim_admin_c.jsx
"use client";

import Link from "next/link";
import { use, useEffect, useState } from "react";
import {
  ArrowDown,
  ArrowLeft,
  ArrowUp,
  CheckCircle2,
  Layers,
  Loader2,
  PlayCircle,
  Rocket,
  SlidersHorizontal,
  XCircle,
} from "lucide-react";
import { Topbar } from "@/components/chrome/topbar";
import {
  AdminTable,
  Body,
  Button,
  Card,
  Chip,
  Eyebrow,
  Micro,
  MiniKpi,
} from "@/components/ui";
import type { AdminTableCol, AdminTableRow } from "@/components/ui";
import { PageError, PageLoading } from "@/components/base/pageStates";
import { PermissionGate } from "@/components/shared/PermissionGate";
import { api } from "@/lib/api";
import { formatText } from "@/lib/format";
import { cn, fmtRelative } from "@/lib/utils";
import type {
  ProposalDetail,
  ProposalStatus,
  TierThresholdChange,
} from "@/types/recalibration";

const STATUS_TONE: Record<
  ProposalStatus,
  "mute" | "info" | "warn" | "pos" | "neg" | "spot"
> = {
  DRAFT: "mute",
  PENDING_REVIEW: "spot",
  APPROVED: "info",
  REJECTED: "neg",
  DEPLOYED: "pos",
};

export default function RecalDetailPage(props: {
  params: Promise<{ id: string }>;
}) {
  return (
    <PermissionGate
      permission="recalibration:view"
      fallback={
        <PageError message="You don't have recalibration:view permission." />
      }
    >
      <Inner params={props.params} />
    </PermissionGate>
  );
}

function Inner({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const [data, setData] = useState<ProposalDetail | null>(null);
  const [state, setState] = useState<"loading" | "ok" | "error">("loading");
  const [err, setErr] = useState<string | null>(null);
  const [acting, setActing] = useState<string | null>(null);
  const [rationale, setRationale] = useState("");

  async function load() {
    setState("loading");
    try {
      const r = await api.get<ProposalDetail>(
        `/api/v1/recalibration/proposals/${id}`,
      );
      setData(r);
      setRationale(r.review_rationale ?? "");
      setState("ok");
    } catch (e) {
      setErr(e instanceof Error ? e.message : String(e));
      setState("error");
    }
  }

  useEffect(() => {
    void load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id]);

  async function transition(endpoint: string) {
    setActing(endpoint);
    try {
      const body = rationale ? { rationale } : undefined;
      await api.post(
        `/api/v1/recalibration/proposals/${id}/${endpoint}`,
        body,
      );
      await load();
    } finally {
      setActing(null);
    }
  }

  if (state === "loading") return <PageLoading message="Loading proposal…" />;
  if (state === "error") return <PageError message={err ?? "Unknown error"} />;
  if (!data) return <PageLoading />;

  return (
    <DetailBody
      data={data}
      onTransition={transition}
      acting={acting}
      rationale={rationale}
      setRationale={setRationale}
    />
  );
}

function DetailBody({
  data,
  onTransition,
  acting,
  rationale,
  setRationale,
}: {
  data: ProposalDetail;
  onTransition: (endpoint: string) => void;
  acting: string | null;
  rationale: string;
  setRationale: (v: string) => void;
}) {
  const canReview = data.status === "PENDING_REVIEW";
  const canDeploy = data.status === "APPROVED";

  const scopeRows: [string, React.ReactNode][] = [
    ["Coverage", <code key="coverage" className="font-mono">{data.coverage}</code>],
    ["Config", <code key="config" className="font-mono">{data.config_name}</code>],
    ["Trigger", data.trigger],
    ["Proposer", <code key="proposer" className="font-mono">{data.proposed_by}</code>],
    [
      "Sample",
      `${data.sample_size.toLocaleString()} assessments`,
    ],
    ["Proposed", fmtRelative(data.proposed_at)],
  ];

  const weightCols: AdminTableCol[] = [
    { key: "signal", label: "Signal", width: "1.4fr" },
    { key: "from", label: "From", align: "right", width: "100px" },
    { key: "to", label: "To", align: "right", width: "100px" },
    { key: "delta", label: "Δ", align: "right", width: "110px" },
    { key: "why", label: "Rationale", width: "2.4fr" },
  ];

  const weightRows: AdminTableRow[] = data.weight_changes.map((w) => {
    const d = w.proposed_weight - w.current_weight;
    const up = d > 0;
    return {
      signal: <code className="text-[12px] text-ink">{w.signal_id}</code>,
      from: (
        <span className="tabular-nums text-ink-soft">
          {w.current_weight.toFixed(3)}
        </span>
      ),
      to: (
        <span className="tabular-nums font-bold text-info">
          {w.proposed_weight.toFixed(3)}
        </span>
      ),
      delta: (
        <span
          className={cn(
            "inline-flex items-center justify-end gap-1 tabular-nums font-semibold",
            up ? "text-pos" : "text-warn",
          )}
        >
          {up ? <ArrowUp size={11} /> : <ArrowDown size={11} />}
          {up ? "+" : ""}
          {d.toFixed(3)}
        </span>
      ),
      why: (
        <span className="text-[12.5px] leading-snug text-ink-soft">
          {w.rationale}
        </span>
      ),
    };
  });

  const tierCols: AdminTableCol[] = [
    { key: "band", label: "Band", width: "1fr" },
    { key: "boundary", label: "Boundary", width: "1fr" },
    { key: "from", label: "From", align: "right", width: "1fr" },
    { key: "to", label: "To", align: "right", width: "1fr" },
    { key: "delta", label: "Δ", align: "right", width: "1fr" },
  ];

  const tierRows: AdminTableRow[] = data.tier_threshold_changes.map(
    (t: TierThresholdChange, i) => {
      const d = t.proposed_value - t.current_value;
      const up = d > 0;
      return {
        _key: `${t.band_id}-${t.boundary}-${i}`,
        band: (
          <code className="text-[12px] font-bold text-ink">
            TIER_{t.band_id}
          </code>
        ),
        boundary: <span className="capitalize">{t.boundary}</span>,
        from: (
          <span className="tabular-nums text-ink-soft">
            {t.current_value.toFixed(2)}
          </span>
        ),
        to: (
          <span className="tabular-nums font-bold text-info">
            {t.proposed_value.toFixed(2)}
          </span>
        ),
        delta: (
          <span
            className={cn(
              "tabular-nums font-semibold",
              up ? "text-pos" : "text-warn",
            )}
          >
            {up ? "+" : ""}
            {d.toFixed(2)}
          </span>
        ),
      };
    },
  );

  return (
    <>
      <Topbar
        crumbs={["Admin", "Recalibration", `${data.coverage} · ${data.config_name}`]}
      />
      <div className="flex-1 overflow-y-auto px-9 py-7">
        <div className="grid gap-4">
          <Link
            href="/admin/recalibration"
            className="inline-flex items-center gap-1.5 text-[12.5px] font-medium text-ink-soft hover:text-ink"
          >
            <ArrowLeft size={12} />
            All proposals
          </Link>

          <Card pad="lg">
            <div className="flex items-end justify-between gap-4">
              <div>
                <Eyebrow>Recalibration</Eyebrow>
                <h1 className="mt-1.5 font-display text-[28px] font-semibold leading-tight text-ink">
                  Recalibration proposal · {data.coverage}
                </h1>
                <div className="mt-2 flex flex-wrap gap-2">
                  <Chip variant={STATUS_TONE[data.status]} size="md">
                    {data.status.replace("_", " ")}
                  </Chip>
                  <Chip variant="outline" size="md">
                    <span className="font-mono">
                      {data.coverage} / {data.config_name}
                    </span>
                  </Chip>
                  <Chip variant="mute" size="md">
                    {data.trigger}
                  </Chip>
                </div>
              </div>
              {(canReview || canDeploy) && (
                <div className="flex gap-2">
                  {canReview && (
                    <>
                      <Button variant="ghost" disabled>
                        <PlayCircle size={13} />
                        Simulate
                      </Button>
                      <Button
                        variant="ghost"
                        disabled={!!acting}
                        onClick={() => onTransition("reject")}
                      >
                        {acting === "reject" ? (
                          <Loader2 size={13} className="animate-spin" />
                        ) : (
                          <XCircle size={13} />
                        )}
                        Reject
                      </Button>
                      <Button
                        variant="primary"
                        disabled={!!acting}
                        onClick={() => onTransition("approve")}
                      >
                        {acting === "approve" ? (
                          <Loader2 size={13} className="animate-spin" />
                        ) : (
                          <CheckCircle2 size={13} />
                        )}
                        Approve
                      </Button>
                    </>
                  )}
                  {canDeploy && (
                    <Button
                      variant="spot"
                      disabled={!!acting}
                      onClick={() => onTransition("deploy")}
                    >
                      {acting === "deploy" ? (
                        <Loader2 size={13} className="animate-spin" />
                      ) : (
                        <Rocket size={13} />
                      )}
                      Deploy
                    </Button>
                  )}
                </div>
              )}
            </div>
          </Card>

          <div className="grid gap-4 md:grid-cols-3">
            <MiniKpi
              label="Sample size"
              value={data.sample_size.toLocaleString()}
            />
            <MiniKpi
              label="Weight changes"
              value={data.weight_changes.length}
            />
            <MiniKpi
              label="Tier threshold changes"
              value={data.tier_threshold_changes.length}
            />
          </div>

          <div className="grid gap-4 md:grid-cols-2">
            <Card pad="lg">
              <Eyebrow>Scope</Eyebrow>
              <div className="mt-3 flex flex-col">
                {scopeRows.map(([k, v], i) => (
                  <div
                    key={k}
                    className={cn(
                      "grid grid-cols-[120px_1fr] gap-3 py-2",
                      i < scopeRows.length - 1 && "border-b border-rule",
                    )}
                  >
                    <Micro>{k}</Micro>
                    <span className="text-[13px] font-medium text-ink">
                      {v}
                    </span>
                  </div>
                ))}
              </div>
            </Card>

            <Card pad="lg" variant="spot">
              <Eyebrow className="text-spot-deep dark:text-spot">
                Reviewer rationale
              </Eyebrow>
              <h2 className="mt-1.5 mb-3 text-[17px] font-semibold text-ink">
                Required for approval or rejection
              </h2>
              <textarea
                value={rationale}
                onChange={(e) => setRationale(e.target.value)}
                placeholder="Document why this proposal should (or shouldn't) deploy — drift evidence, sample adequacy, downstream impact…"
                rows={4}
                className="block w-full rounded-card border border-rule-strong bg-surface p-3 text-[13.5px] leading-snug text-ink placeholder:text-ink-mute focus:border-info focus:outline-none focus:ring-2 focus:ring-info/30"
              />
              {canReview && (
                <div className="mt-3">
                  <Button
                    variant="spot"
                    disabled={!!acting || !rationale.trim()}
                    onClick={() => onTransition("approve")}
                  >
                    {acting === "approve" ? (
                      <Loader2 size={13} className="animate-spin" />
                    ) : (
                      <CheckCircle2 size={13} />
                    )}
                    Approve with rationale
                  </Button>
                </div>
              )}
            </Card>
          </div>

          {(data.review_decision || data.deployed_at) && (
            <Card pad="md">
              <Eyebrow>Review trail</Eyebrow>
              <div className="mt-3 grid gap-2 text-[13px] text-ink">
                {data.review_decision && (
                  <TrailRow
                    label="Decision"
                    value={formatText(data.review_decision, "capitalize")}
                  />
                )}
                {data.reviewed_at && (
                  <TrailRow
                    label="Reviewed"
                    value={`${fmtRelative(data.reviewed_at)} by ${data.reviewer_id ?? "—"}`}
                  />
                )}
                {data.deployed_at && (
                  <TrailRow
                    label="Deployed"
                    value={fmtRelative(data.deployed_at)}
                  />
                )}
                {data.deployed_config_version_id && (
                  <TrailRow
                    label="Deployed version"
                    value={
                      <span className="font-mono">
                        {data.deployed_config_version_id}
                      </span>
                    }
                  />
                )}
              </div>
            </Card>
          )}

          {data.weight_changes.length > 0 && (
            <Card
              pad="none"
              icon={SlidersHorizontal}
              header="Weight changes"
              headerRight={
                <Chip size="sm" variant="mute">
                  {data.weight_changes.length}
                </Chip>
              }
            >
              <AdminTable cols={weightCols} rows={weightRows} />
            </Card>
          )}

          {data.tier_threshold_changes.length > 0 && (
            <Card
              pad="none"
              icon={Layers}
              header="Tier threshold changes"
              headerRight={
                <Chip size="sm" variant="mute">
                  {data.tier_threshold_changes.length}
                </Chip>
              }
            >
              <AdminTable
                cols={tierCols}
                rows={tierRows}
                getRowKey={(row, i) =>
                  typeof row._key === "string" ? row._key : String(i)
                }
              />
            </Card>
          )}

          {data.weight_changes.length === 0 &&
            data.tier_threshold_changes.length === 0 && (
              <Card pad="lg">
                <Body className="italic">
                  This proposal has no weight or tier-threshold changes.
                </Body>
              </Card>
            )}
        </div>
      </div>
    </>
  );
}

function TrailRow({
  label,
  value,
}: {
  label: string;
  value: React.ReactNode;
}) {
  return (
    <div className="grid grid-cols-[140px_1fr] gap-3 border-b border-rule py-2 last:border-0">
      <Micro>{label}</Micro>
      <span className="text-[13px] text-ink">{value}</span>
    </div>
  );
}


"use client";

import Link from "next/link";
import { use, useEffect, useState } from "react";
import {
  ArrowLeft,
  ArrowRight,
  CheckCircle2,
  Loader2,
  Rocket,
  XCircle,
} from "lucide-react";
import { Topbar } from "@/components/chrome/topbar";
import { Card } from "@/components/ui/card";
import { Chip } from "@/components/ui/chip";
import { Button } from "@/components/ui/button";
import { Eyebrow, NumDisplay, Body, Micro } from "@/components/ui/typography";
import { LabelRow } from "@/components/ui/label-row";
import { PageError, PageLoading } from "@/components/base/pageStates";
import { PermissionGate } from "@/components/shared/PermissionGate";
import { api } from "@/lib/api";
import { formatText } from "@/lib/format";
import { fmtRelative } from "@/lib/utils";
import { cn } from "@/lib/utils";
import type {
  ProposalDetail,
  ProposalStatus,
  TierThresholdChange,
  WeightChange,
} from "@/types/recalibration";

const STATUS_TONE: Record<ProposalStatus, "mute" | "info" | "warn" | "pos" | "neg"> = {
  DRAFT: "mute",
  PENDING_REVIEW: "warn",
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

  async function load() {
    setState("loading");
    try {
      const r = await api.get<ProposalDetail>(
        `/api/v1/recalibration/proposals/${id}`,
      );
      setData(r);
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
      await api.post(`/api/v1/recalibration/proposals/${id}/${endpoint}`);
      await load();
    } finally {
      setActing(null);
    }
  }

  if (state === "loading") return <PageLoading message="Loading proposal…" />;
  if (state === "error") return <PageError message={err ?? "Unknown error"} />;
  if (!data) return <PageLoading />;

  return <DetailBody data={data} onTransition={transition} acting={acting} />;
}

function DetailBody({
  data,
  onTransition,
  acting,
}: {
  data: ProposalDetail;
  onTransition: (endpoint: string) => void;
  acting: string | null;
}) {
  const canReview = data.status === "PENDING_REVIEW";
  const canDeploy = data.status === "APPROVED";

  return (
    <>
      <Topbar
        crumbs={["Admin", "Recalibration", `${data.coverage} · ${data.config_name}`]}
      />
      <div className="flex-1 overflow-y-auto px-9 py-7">
        <div className="mx-auto grid max-w-[1280px] gap-6">
          <Link
            href="/admin/recalibration"
            className="inline-flex items-center gap-1.5 text-[13px] font-medium text-info hover:underline"
          >
            <ArrowLeft size={14} /> All proposals
          </Link>

          {/* Header */}
          <Card pad="lg" className="space-y-4">
            <div className="flex items-start justify-between gap-4">
              <div>
                <Eyebrow>Proposal</Eyebrow>
                <h1 className="mt-1 font-display text-[28px] font-semibold leading-tight text-ink">
                  {data.coverage} · {data.config_name}
                </h1>
                <Micro className="mt-1 block">
                  proposed by{" "}
                  <span className="font-medium text-ink">
                    {data.proposed_by}
                  </span>{" "}
                  · {fmtRelative(data.proposed_at)}
                </Micro>
              </div>
              <Chip variant={STATUS_TONE[data.status]}>
                {formatText(data.status, "capitalize")}
              </Chip>
            </div>
            <Card pad="md" variant="info" className="space-y-1">
              <Micro className="text-info-deep dark:text-info">Trigger</Micro>
              <Body className="text-ink">{data.trigger}</Body>
            </Card>
          </Card>

          {/* Summary stats */}
          <div className="grid gap-4 md:grid-cols-3">
            <Stat label="Sample size">{data.sample_size.toLocaleString()}</Stat>
            <Stat label="Weight changes">{data.weight_change_count}</Stat>
            <Stat label="Tier threshold changes">{data.tier_change_count}</Stat>
          </div>

          {/* Action row */}
          {(canReview || canDeploy) && (
            <Card pad="md" className="flex flex-wrap items-center gap-2">
              <Eyebrow className="mr-auto">Decide</Eyebrow>
              {canReview && (
                <>
                  <Button
                    type="button"
                    variant="ghost"
                    onClick={() => onTransition("reject")}
                    disabled={!!acting}
                  >
                    {acting === "reject" ? (
                      <Loader2 size={14} className="animate-spin" />
                    ) : (
                      <XCircle size={14} />
                    )}
                    Reject
                  </Button>
                  <Button
                    type="button"
                    variant="primary"
                    onClick={() => onTransition("approve")}
                    disabled={!!acting}
                  >
                    {acting === "approve" ? (
                      <Loader2 size={14} className="animate-spin" />
                    ) : (
                      <CheckCircle2 size={14} />
                    )}
                    Approve
                  </Button>
                </>
              )}
              {canDeploy && (
                <Button
                  type="button"
                  variant="spot"
                  onClick={() => onTransition("deploy")}
                  disabled={!!acting}
                >
                  {acting === "deploy" ? (
                    <Loader2 size={14} className="animate-spin" />
                  ) : (
                    <Rocket size={14} />
                  )}
                  Deploy
                </Button>
              )}
            </Card>
          )}

          {/* Review trail */}
          {(data.review_decision || data.review_rationale) && (
            <Card pad="md" className="space-y-2">
              <Eyebrow>Review trail</Eyebrow>
              {data.review_decision && (
                <LabelRow
                  label="Decision"
                  value={formatText(data.review_decision, "capitalize")}
                />
              )}
              {data.reviewed_at && (
                <LabelRow
                  label="Reviewed"
                  value={`${fmtRelative(data.reviewed_at)} by ${data.reviewer_id ?? "—"}`}
                />
              )}
              {data.review_rationale && (
                <div className="pt-2">
                  <Micro className="block">Rationale</Micro>
                  <Body className="mt-1 text-ink">{data.review_rationale}</Body>
                </div>
              )}
              {data.deployed_at && (
                <LabelRow
                  label="Deployed"
                  value={fmtRelative(data.deployed_at)}
                />
              )}
              {data.deployed_config_version_id && (
                <LabelRow
                  label="Deployed version"
                  value={
                    <span className="font-mono">
                      {data.deployed_config_version_id}
                    </span>
                  }
                />
              )}
            </Card>
          )}

          {/* Weight changes */}
          {data.weight_changes.length > 0 && (
            <section>
              <Eyebrow className="mb-3">
                Weight changes ({data.weight_changes.length})
              </Eyebrow>
              <Card pad="md" className="overflow-hidden p-0">
                <table className="w-full table-fixed text-[13px]">
                  <thead>
                    <tr className="border-b border-rule bg-surface-sunken text-left">
                      <ColHead width="w-[28%]">Signal</ColHead>
                      <ColHead width="w-[15%]">Current</ColHead>
                      <ColHead width="w-[6%]">→</ColHead>
                      <ColHead width="w-[15%]">Proposed</ColHead>
                      <ColHead width="w-[10%]">Δ</ColHead>
                      <ColHead width="w-[26%]">Rationale</ColHead>
                    </tr>
                  </thead>
                  <tbody>
                    {data.weight_changes.map((c) => (
                      <WeightRow key={c.signal_id} change={c} />
                    ))}
                  </tbody>
                </table>
              </Card>
            </section>
          )}

          {/* Tier threshold changes */}
          {data.tier_threshold_changes.length > 0 && (
            <section>
              <Eyebrow className="mb-3">
                Tier threshold changes ({data.tier_threshold_changes.length})
              </Eyebrow>
              <Card pad="md" className="overflow-hidden p-0">
                <table className="w-full table-fixed text-[13px]">
                  <thead>
                    <tr className="border-b border-rule bg-surface-sunken text-left">
                      <ColHead width="w-[12%]">Band</ColHead>
                      <ColHead width="w-[12%]">Boundary</ColHead>
                      <ColHead width="w-[15%]">Current</ColHead>
                      <ColHead width="w-[6%]">→</ColHead>
                      <ColHead width="w-[15%]">Proposed</ColHead>
                      <ColHead width="w-[10%]">Δ</ColHead>
                      <ColHead width="w-[30%]">Rationale</ColHead>
                    </tr>
                  </thead>
                  <tbody>
                    {data.tier_threshold_changes.map((c, i) => (
                      <TierRow key={`${c.band_id}-${c.boundary}-${i}`} change={c} />
                    ))}
                  </tbody>
                </table>
              </Card>
            </section>
          )}
        </div>
      </div>
    </>
  );
}

function WeightRow({ change }: { change: WeightChange }) {
  const delta = change.proposed_weight - change.current_weight;
  return (
    <tr className="border-b border-rule last:border-0 hover:bg-surface-sunken/40">
      <td className="px-5 py-2.5 font-mono text-[12.5px] text-ink">
        {change.signal_id}
      </td>
      <td className="px-5 py-2.5 tabular-nums text-ink-soft">
        {change.current_weight.toFixed(3)}
      </td>
      <td className="px-5 py-2.5 text-center text-ink-mute">
        <ArrowRight size={12} className="inline" />
      </td>
      <td className="px-5 py-2.5 font-semibold tabular-nums text-ink">
        {change.proposed_weight.toFixed(3)}
      </td>
      <td
        className={cn(
          "px-5 py-2.5 font-semibold tabular-nums",
          delta > 0 ? "text-pos" : delta < 0 ? "text-neg" : "text-ink-mute",
        )}
      >
        {delta > 0 ? "+" : ""}
        {delta.toFixed(3)}
      </td>
      <td className="px-5 py-2.5 text-[12.5px] text-ink-soft">
        {change.rationale}
      </td>
    </tr>
  );
}

function TierRow({ change }: { change: TierThresholdChange }) {
  const delta = change.proposed_value - change.current_value;
  return (
    <tr className="border-b border-rule last:border-0 hover:bg-surface-sunken/40">
      <td className="px-5 py-2.5 font-semibold text-ink">{change.band_id}</td>
      <td className="px-5 py-2.5 text-ink-soft">{change.boundary}</td>
      <td className="px-5 py-2.5 tabular-nums text-ink-soft">
        {change.current_value.toFixed(2)}
      </td>
      <td className="px-5 py-2.5 text-center text-ink-mute">
        <ArrowRight size={12} className="inline" />
      </td>
      <td className="px-5 py-2.5 font-semibold tabular-nums text-ink">
        {change.proposed_value.toFixed(2)}
      </td>
      <td
        className={cn(
          "px-5 py-2.5 font-semibold tabular-nums",
          delta > 0 ? "text-pos" : delta < 0 ? "text-neg" : "text-ink-mute",
        )}
      >
        {delta > 0 ? "+" : ""}
        {delta.toFixed(2)}
      </td>
      <td className="px-5 py-2.5 text-[12.5px] text-ink-soft">
        {change.rationale}
      </td>
    </tr>
  );
}

function Stat({
  label,
  children,
}: {
  label: string;
  children: React.ReactNode;
}) {
  return (
    <Card pad="md">
      <Micro>{label}</Micro>
      <div className="mt-2">
        <NumDisplay size="lg">{children}</NumDisplay>
      </div>
    </Card>
  );
}

function ColHead({
  width,
  children,
}: {
  width: string;
  children: React.ReactNode;
}) {
  return (
    <th
      className={`px-5 py-2.5 text-[11px] font-semibold uppercase tracking-[0.08em] text-ink-mute ${width}`}
    >
      {children}
    </th>
  );
}

"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { AlertCircle, ChevronRight, Search, UserCheck } from "lucide-react";
import { Topbar } from "@/components/chrome/topbar";
import { CarrierShell } from "@/components/chrome/carrier-shell";
import { isCarrierRole } from "@/lib/portalPaths";
import { Card } from "@/components/ui/card";
import { Chip } from "@/components/ui/chip";
import { MiniKpi } from "@/components/ui/mini-kpi";
import { Eyebrow, NumDisplay, Body, Micro, Caption } from "@/components/ui/typography";
import { ScoreBar } from "@/components/ui/score-bar";
import { PageLoading, PageError, RoleGate } from "@/components/base/pageStates";
import { useAuthStore } from "@/store/authStore";
import { useDsiStore, type ApiRecord } from "@/store/dsiStore";
import { formatCurrency, formatText } from "@/lib/format";
import { fmtRelative } from "@/lib/utils";
import { cn } from "@/lib/utils";

type DecisionFilter = "all" | "refer" | "approve" | "decline";

export default function CarrierPipelinePage() {
  const user = useAuthStore((s) => s.user);
  const submissions = useDsiStore((s) => s.submissions);
  const fetchSubmissions = useDsiStore((s) => s.fetchSubmissions);
  const [loadState, setLoadState] = useState<"idle" | "loading" | "error" | "ok">(
    submissions.length > 0 ? "ok" : "idle",
  );
  const [errMsg, setErrMsg] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    setLoadState("loading");
    fetchSubmissions()
      .then(() => !cancelled && setLoadState("ok"))
      .catch((e) => {
        if (cancelled) return;
        setErrMsg(e instanceof Error ? e.message : String(e));
        setLoadState("error");
      });
    return () => {
      cancelled = true;
    };
  }, [fetchSubmissions]);

  const inner =
    !user ? (
      <PageLoading message="Signing in…" />
    ) : user.role && !isCarrierRole(user.role) ? (
      <RoleGate expected="carrier" />
    ) : loadState === "loading" ? (
      <PageLoading message="Loading pipeline…" />
    ) : loadState === "error" ? (
      <PageError message={errMsg ?? "Unknown error"} />
    ) : (
      <PipelineBody submissions={submissions} mode="referral" />
    );

  return <CarrierShell>{inner}</CarrierShell>;
}

interface PipelineBodyProps {
  submissions: ApiRecord[];
  mode: "referral" | "full";
}

interface PipelineCounts {
  referrals: number;
  approvals: number;
  declines: number;
  awaiting: number;
  premium: number;
}

/** Decision bucket for a submission row, lower-cased and normalised. */
function decisionOf(sub: ApiRecord): string {
  return (sub.decision ?? "").toLowerCase();
}

function premiumOf(sub: ApiRecord): number {
  return sub.final_premium ?? sub.recommended_premium ?? 0;
}

export function PipelineBody({ submissions, mode }: PipelineBodyProps) {
  const [query, setQuery] = useState("");
  const [decision, setDecision] = useState<DecisionFilter>("all");

  const filtered = useMemo(() => {
    return submissions.filter((s) => {
      if (mode === "referral") {
        const dec = decisionOf(s);
        const refState = (s.referral_state ?? "").toLowerCase();
        const isReferral = dec === "refer" || refState.includes("await");
        if (!isReferral) return false;
      }
      if (decision !== "all") {
        if (decisionOf(s) !== decision) return false;
      }
      if (!query) return true;
      const q = query.toLowerCase();
      return (
        (s.entity_name ?? "").toLowerCase().includes(q) ||
        (s.coverage_configuration ?? "").toLowerCase().includes(q) ||
        (s.coverage ?? "").toLowerCase().includes(q) ||
        (s.submission_code ?? "").toLowerCase().includes(q)
      );
    });
  }, [submissions, query, decision, mode]);

  const counts: PipelineCounts = useMemo(() => {
    let referrals = 0;
    let approvals = 0;
    let declines = 0;
    let awaiting = 0;
    let premium = 0;
    for (const s of filtered) {
      const dec = decisionOf(s);
      if (dec === "refer") referrals++;
      else if (dec === "approve") approvals++;
      else if (dec === "decline") declines++;
      if ((s.referral_state ?? "").toLowerCase().includes("await")) awaiting++;
      premium += premiumOf(s);
    }
    return { referrals, approvals, declines, awaiting, premium };
  }, [filtered]);

  const heroLabel = mode === "referral" ? "Referral pipeline" : "Full pipeline";
  const heroCaption =
    mode === "referral"
      ? "submissions awaiting decision"
      : "submissions in the pipeline";

  return (
    <>
      <Topbar
        crumbs={[
          "Carrier Portal",
          mode === "referral" ? "Referral Pipeline" : "Full Pipeline",
        ]}
      />
      <div className="flex-1 overflow-y-auto px-9 py-7">
        <div className="mx-auto grid max-w-[1400px] gap-4">
          {/* Hero row — pipeline count + decision-mix KPI strip. Full mode
              renders 5 cards; referral mode renders only the hero +
              Pipeline$ so the grid template collapses accordingly to
              avoid stranded empty columns. */}
          <div
            className={
              mode === "full"
                ? "grid gap-4 lg:grid-cols-[1.6fr_1fr_1fr_1fr_1fr]"
                : "grid gap-4 lg:grid-cols-[1.6fr_1fr]"
            }
          >
            <Card variant="info" pad="md" className="flex items-center gap-4">
              <div className="flex size-14 shrink-0 items-center justify-center rounded-card bg-info-soft text-info-deep dark:text-info">
                <UserCheck size={28} />
              </div>
              <div className="min-w-0 flex-1">
                <Eyebrow className="text-info-deep dark:text-info">
                  {heroLabel}
                </Eyebrow>
                <NumDisplay size="lg" className="mt-1.5 block text-info">
                  {filtered.length}
                </NumDisplay>
                <Caption className="mt-1.5 block">{heroCaption}</Caption>
              </div>
            </Card>
            {/* To-refer/approve/declined are only meaningful in full mode;
                in referral mode the hero count already covers "to refer". */}
            {mode === "full" && (
              <>
                <Card pad="md">
                  <MiniKpi label="To refer" value={counts.referrals} />
                </Card>
                <Card pad="md">
                  <MiniKpi label="To approve" value={counts.approvals} />
                </Card>
                <Card pad="md">
                  <MiniKpi label="Declined" value={counts.declines} />
                </Card>
              </>
            )}
            <Card pad="md">
              <MiniKpi label="Pipeline $" value={formatCurrency(counts.premium)} />
            </Card>
          </div>

          {/* Filters */}
          <div className="flex flex-wrap items-center gap-2">
            <Micro className="mr-1">Decision:</Micro>
            {(
              [
                ["all", `All (${filtered.length})`],
                ["refer", `Refer (${counts.referrals})`],
                ["approve", `Approve (${counts.approvals})`],
                ["decline", `Decline (${counts.declines})`],
              ] as [DecisionFilter, string][]
            ).map(([key, label]) => (
              <button
                key={key}
                type="button"
                onClick={() => setDecision(key)}
                className="focus:outline-none"
              >
                <Chip
                  variant={decision === key ? "info" : "outline"}
                  className="cursor-pointer"
                >
                  {label}
                </Chip>
              </button>
            ))}
            <span className="flex-1" />
            <div className="flex items-center gap-2 rounded-btn border border-rule-strong bg-surface px-3">
              <Search size={15} className="text-ink-mute" />
              <input
                type="search"
                placeholder="Entity, line, or code…"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                className="h-9 w-56 border-0 bg-transparent text-[13.5px] text-ink placeholder:text-ink-mute focus:outline-none"
              />
            </div>
          </div>

          {/* Table */}
          <Card pad="md" className="overflow-hidden p-0">
            <table className="w-full table-fixed text-[13px]">
              <thead>
                <tr className="border-b border-rule bg-surface-sunken text-left">
                  <ColHead width="w-[22%]">Entity</ColHead>
                  <ColHead width="w-[13%]">Broker</ColHead>
                  <ColHead width="w-[15%]">Line</ColHead>
                  <ColHead width="w-[13%]">Score</ColHead>
                  <ColHead width="w-[11%]">Decision</ColHead>
                  <ColHead width="w-[12%]">Premium</ColHead>
                  <ColHead width="w-[12%]">Status</ColHead>
                  <ColHead width="w-[8%]">Age</ColHead>
                  <ColHead width="w-[4%]">{null}</ColHead>
                </tr>
              </thead>
              <tbody>
                {filtered.map((s) => (
                  <Row key={s.submission_code} sub={s} />
                ))}
              </tbody>
            </table>
            {filtered.length === 0 && (
              <div className="px-5 py-8 text-center">
                <Body className="italic">No submissions match the filters.</Body>
              </div>
            )}
          </Card>
        </div>
      </div>
    </>
  );
}

function Row({ sub }: { sub: ApiRecord }) {
  const decision = decisionOf(sub);
  const decisionTone =
    decision === "approve"
      ? "pos"
      : decision === "decline"
        ? "neg"
        : decision === "refer"
          ? "warn"
          : "mute";
  const awaiting = (sub.referral_state ?? "").toLowerCase().includes("await");
  const received = sub.received_at ?? sub.created_at ?? sub.submitted_at;

  return (
    <tr className="border-b border-rule last:border-0 hover:bg-surface-sunken/40">
      <td className="px-5 py-3">
        <p className="truncate font-medium text-ink">{sub.entity_name ?? "—"}</p>
        <Micro className="mt-0.5 block font-mono">{sub.submission_code}</Micro>
      </td>
      <td className="px-5 py-3">
        <Caption className="truncate">{sub.broker_name ?? "Marsh"}</Caption>
      </td>
      <td className="px-5 py-3 truncate text-ink">
        {sub.coverage_configuration ?? "—"}
      </td>
      <td className="px-5 py-3">
        {sub.final_composite_score != null ? (
          <div className="space-y-1">
            <span className="font-semibold tabular-nums text-ink">
              {Number(sub.final_composite_score).toFixed(0)}
            </span>
            <ScoreBar
              value={Number(sub.final_composite_score)}
              max={1000}
              showValue={false}
              thresholds={[
                { at: 400, tone: "neg" },
                { at: 650, tone: "warn" },
                { at: 800, tone: "info" },
                { at: 1000, tone: "pos" },
              ]}
            />
          </div>
        ) : (
          <span className="text-ink-mute">—</span>
        )}
      </td>
      <td className="px-5 py-3">
        {decision ? (
          <Chip variant={decisionTone} size="sm">
            {formatText(decision, "capitalize")}
          </Chip>
        ) : (
          <span className="text-ink-mute">—</span>
        )}
      </td>
      <td className="px-5 py-3">
        <span className="font-semibold tabular-nums text-ink">
          {sub.final_premium != null || sub.recommended_premium != null
            ? formatCurrency(sub.final_premium ?? sub.recommended_premium)
            : "—"}
        </span>
      </td>
      <td className="px-5 py-3">
        {awaiting ? (
          <Chip variant="spot" size="sm">
            <AlertCircle size={10} />
            {formatText(sub.referral_state, "capitalize")}
          </Chip>
        ) : sub.submission_status ? (
          <Chip variant="mute" size="sm">
            {formatText(sub.submission_status, "capitalize")}
          </Chip>
        ) : sub.status ? (
          <Chip variant="mute" size="sm">
            {formatText(sub.status, "capitalize")}
          </Chip>
        ) : (
          <span className="text-ink-mute">—</span>
        )}
      </td>
      <td className="px-5 py-3">
        <Micro>{received ? fmtRelative(String(received)) : "—"}</Micro>
      </td>
      <td className="px-5 py-3 text-right">
        <Link
          href={`/carrier/submissions/${sub.submission_code}`}
          className="inline-flex items-center text-ink-mute hover:text-ink"
        >
          <ChevronRight size={16} />
        </Link>
      </td>
    </tr>
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
      className={cn(
        "px-5 py-2.5 text-[11px] font-semibold uppercase tracking-[0.08em] text-ink-mute",
        width,
      )}
    >
      {children}
    </th>
  );
}

"use client";

import Link from "next/link";
import { memo, useEffect, useMemo, useState } from "react";
import { AlertCircle, Check, ChevronRight, Search, UserCheck, X } from "lucide-react";
import { Topbar } from "@/components/chrome/topbar";
import { CarrierShell } from "@/components/chrome/carrier-shell";
import { isCarrierRole } from "@/lib/portalPaths";
import { Card } from "@/components/ui/card";
import { Chip } from "@/components/ui/chip";
import { MiniKpi } from "@/components/ui/mini-kpi";
import { WorkArea } from "@/components/ui/work-area";
import { Eyebrow, NumDisplay, Body, Micro, Caption } from "@/components/ui/typography";
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

  // Referral-mode triage metrics (replace the decision-breakdown KPIs that
  // only make sense on the full pipeline). Same count + sizing as full mode.
  const triage = useMemo(() => {
    if (filtered.length === 0) {
      return { avgScore: 0, loPrem: 0, medPrem: 0, hiPrem: 0, oldest: "—" };
    }
    const scores = filtered.map((s) =>
      Number(s.final_composite_score ?? 0),
    );
    const avgScore = Math.round(
      scores.reduce((a, b) => a + b, 0) / scores.length,
    );
    const premiums = filtered.map((s) => premiumOf(s)).sort((a, b) => a - b);
    const n = premiums.length;
    const medPrem =
      n % 2 ? premiums[(n - 1) / 2]! : (premiums[n / 2 - 1]! + premiums[n / 2]!) / 2;
    const oldestRow = filtered.reduce((a, b) => {
      const at = new Date(String(a.received_at ?? a.created_at ?? 0)).getTime();
      const bt = new Date(String(b.received_at ?? b.created_at ?? 0)).getTime();
      return bt < at ? b : a;
    });
    const oldestTs = oldestRow.received_at ?? oldestRow.created_at;
    return {
      avgScore,
      loPrem: premiums[0]!,
      medPrem,
      hiPrem: premiums[n - 1]!,
      oldest: oldestTs ? fmtRelative(String(oldestTs)) : "—",
    };
  }, [filtered]);

  const heroLabel = mode === "referral" ? "Referral pipeline" : "Full pipeline";
  const heroCaption =
    mode === "referral"
      ? "submissions awaiting decision"
      : "submissions in the pipeline";
  const fmtK = (v: number) => `$${Math.round(v / 1000)}k`;

  return (
    <>
      <Topbar
        crumbs={[
          "Carrier Portal",
          mode === "referral" ? "Referral Pipeline" : "Full Pipeline",
        ]}
      />
      <WorkArea maxWidth={1400} className="gap-4">
          {/* Hero row — count + KPI strip. Both modes fill 5 columns: full
              mode shows the decision breakdown; referral mode swaps in
              triage metrics (those decision counts are meaningless when
              every row is already a referral). */}
          <div className="grid gap-4 lg:grid-cols-[1.6fr_1fr_1fr_1fr_1fr]">
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
            {mode === "referral" ? (
              <>
                <Card pad="md">
                  <MiniKpi label="Avg score" value={triage.avgScore} tone="info" />
                </Card>
                <Card pad="md">
                  <Micro>Premium range</Micro>
                  <div className="mt-2 flex justify-between gap-2">
                    {[
                      ["Low", triage.loPrem, "text-ink-soft"],
                      ["Median", triage.medPrem, "text-ink"],
                      ["High", triage.hiPrem, "text-ink-soft"],
                    ].map(([k, v, c]) => (
                      <div key={k as string} className="min-w-0">
                        <div className="text-[10px] text-ink-mute">{k}</div>
                        <div
                          className={`mt-0.5 whitespace-nowrap font-mono text-[16px] tabular-nums ${c}`}
                        >
                          {fmtK(v as number)}
                        </div>
                      </div>
                    ))}
                  </div>
                </Card>
                <Card pad="md">
                  <MiniKpi label="Oldest waiting" value={triage.oldest} tone="spot" />
                </Card>
              </>
            ) : (
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

          {/* Filters — search on both modes; decision filter is only
              meaningful on the full pipeline (every referral-mode row is
              already a referral). */}
          <div className="flex flex-wrap items-center gap-2">
            <div className="flex items-center gap-2 rounded-btn border border-rule-strong bg-surface px-3">
              <Search size={15} className="text-ink-mute" />
              <input
                type="search"
                placeholder="Search entity, broker…"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                className="h-9 w-56 border-0 bg-transparent text-[13.5px] text-ink placeholder:text-ink-mute focus:outline-none"
              />
            </div>
            {mode === "full" && (
              <>
                <Micro className="ml-2 mr-1">Decision:</Micro>
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
              </>
            )}
          </div>

          {/* Table */}
          <Card pad="none" className="overflow-hidden">
            <table className="w-full table-fixed text-[13px]">
              <thead>
                <tr className="border-b border-rule bg-surface-elev text-left">
                  <ColHead width="w-[20%]">Entity</ColHead>
                  <ColHead width="w-[12%]">Broker</ColHead>
                  <ColHead width="w-[14%]">Line</ColHead>
                  <ColHead width="w-[8%]">Score</ColHead>
                  <ColHead width="w-[7%]">Tier</ColHead>
                  <ColHead width="w-[11%]">Decision</ColHead>
                  <ColHead width="w-[11%]">Premium</ColHead>
                  <ColHead width="w-[11%]">Status</ColHead>
                  <ColHead width="w-[6%]">Age</ColHead>
                  <ColHead width={mode === "referral" ? "w-[10%]" : "w-[4%]"}>
                    {mode === "referral" ? "Quick" : null}
                  </ColHead>
                </tr>
              </thead>
              <tbody>
                {filtered.map((s) => (
                  <Row
                    key={s.submission_code}
                    sub={s}
                    quick={mode === "referral"}
                  />
                ))}
              </tbody>
            </table>
            {filtered.length === 0 && (
              <div className="px-5 py-8 text-center">
                <Body className="italic">
                  {query
                    ? `No submissions match “${query}”.`
                    : "No submissions match the filters."}
                </Body>
              </div>
            )}
          </Card>
      </WorkArea>
    </>
  );
}

const Row = memo(function Row({ sub, quick }: { sub: ApiRecord; quick?: boolean }) {
  const decision = decisionOf(sub);
  const decisionTone =
    decision === "approve"
      ? "pos"
      : decision === "decline"
        ? "neg"
        : decision === "refer"
          ? "spot"
          : "mute";
  const awaiting = (sub.referral_state ?? "").toLowerCase().includes("await");
  const received = sub.received_at ?? sub.created_at ?? sub.submitted_at;
  const tier = sub.final_tier as number | null | undefined;
  const tierTone =
    tier == null
      ? "mute"
      : tier <= 2
        ? "pos"
        : tier === 3
          ? "info"
          : tier === 4
            ? "warn"
            : "neg";
  const industry =
    (sub.submission_data as ApiRecord | undefined)?.industry_label ??
    (sub.submission_data as ApiRecord | undefined)?.naics_label;

  return (
    <tr className="border-b border-rule last:border-0 hover:bg-surface-sunken/40">
      <td className="px-5 py-3">
        <p className="truncate font-medium text-ink">{sub.entity_name ?? "—"}</p>
        <Micro className="mt-0.5 block">
          {industry ? String(industry) : sub.submission_code}
        </Micro>
      </td>
      <td className="px-5 py-3">
        <Caption className="truncate">{sub.broker_name ?? "Marsh"}</Caption>
      </td>
      <td className="px-5 py-3 truncate text-ink">
        {sub.coverage ?? sub.coverage_configuration ?? "—"}
      </td>
      <td className="px-5 py-3">
        {sub.final_composite_score != null ? (
          <span className="font-bold tabular-nums text-info">
            {Number(sub.final_composite_score).toFixed(0)}
          </span>
        ) : (
          <span className="text-ink-mute">—</span>
        )}
      </td>
      <td className="px-5 py-3">
        {tier != null ? (
          <span
            className={`inline-flex h-6 w-6 items-center justify-center rounded-md text-[12px] font-bold ${
              tierTone === "pos"
                ? "bg-pos-soft text-pos"
                : tierTone === "info"
                  ? "bg-info-soft text-info"
                  : tierTone === "warn"
                    ? "bg-warn-soft text-warn"
                    : tierTone === "neg"
                      ? "bg-neg-soft text-neg"
                      : "bg-surface-elev text-ink-mute"
            }`}
          >
            {tier}
          </span>
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
      <td className="px-5 py-3">
        {quick ? (
          <div className="flex items-center justify-end gap-1.5">
            <button
              type="button"
              aria-label="Approve"
              title="Approve"
              className="flex h-7 w-7 items-center justify-center rounded-md border border-pos/40 text-pos hover:bg-pos-soft"
            >
              <Check size={14} />
            </button>
            <button
              type="button"
              aria-label="Decline"
              title="Decline"
              className="flex h-7 w-7 items-center justify-center rounded-md border border-neg/40 text-neg hover:bg-neg-soft"
            >
              <X size={14} />
            </button>
            <Link
              href={`/carrier/submissions/${sub.submission_code}`}
              className="ml-0.5 inline-flex items-center text-ink-mute hover:text-ink"
            >
              <ChevronRight size={16} />
            </Link>
          </div>
        ) : (
          <Link
            href={`/carrier/submissions/${sub.submission_code}`}
            className="flex items-center justify-end text-ink-mute hover:text-ink"
          >
            <ChevronRight size={16} />
          </Link>
        )}
      </td>
    </tr>
  );
});

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

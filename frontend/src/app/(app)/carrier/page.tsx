"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { AlertCircle, ChevronRight, Search } from "lucide-react";
import { Topbar } from "@/components/chrome/topbar";
import { CarrierShell } from "@/components/chrome/carrier-shell";
import { isCarrierRole } from "@/lib/portalPaths";
import { Card } from "@/components/ui/card";
import { Chip } from "@/components/ui/chip";
import { Eyebrow, NumDisplay, Body, Micro } from "@/components/ui/typography";
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

export function PipelineBody({ submissions, mode }: PipelineBodyProps) {
  const [query, setQuery] = useState("");
  const [decision, setDecision] = useState<DecisionFilter>("all");

  const filtered = useMemo(() => {
    return submissions.filter((s) => {
      if (mode === "referral") {
        const dec = (s.decision ?? "").toLowerCase();
        const refState = (s.referral_state ?? "").toLowerCase();
        const isReferral = dec === "refer" || refState.includes("await");
        if (!isReferral) return false;
      }
      if (decision !== "all") {
        const dec = (s.decision ?? "").toLowerCase();
        if (dec !== decision) return false;
      }
      if (!query) return true;
      const q = query.toLowerCase();
      return (
        (s.entity_name ?? "").toLowerCase().includes(q) ||
        (s.coverage ?? "").toLowerCase().includes(q) ||
        (s.submission_code ?? "").toLowerCase().includes(q)
      );
    });
  }, [submissions, query, decision, mode]);

  const totalPremium = filtered.reduce(
    (sum, s) => sum + (s.final_premium ?? s.recommended_premium ?? 0),
    0,
  );
  const awaiting = filtered.filter((s) =>
    (s.referral_state ?? "").toLowerCase().includes("await"),
  ).length;

  return (
    <>
      <Topbar
        crumbs={[
          "Carrier Portal",
          mode === "referral" ? "Referral Pipeline" : "Full Pipeline",
        ]}
      />
      <div className="flex-1 overflow-y-auto px-9 py-7">
        <div className="mx-auto grid max-w-[1400px] gap-6">
          <header className="flex items-end justify-between gap-6">
            <div>
              <Eyebrow>Underwriting</Eyebrow>
              <h1 className="mt-1 font-display text-[32px] font-semibold leading-none tracking-tight text-ink">
                {mode === "referral" ? "Referral Pipeline" : "Full Pipeline"}
              </h1>
              <Body className="mt-2">
                {mode === "referral"
                  ? "Submissions flagged for human review by the scoring engine."
                  : "Every submission in the pipeline, regardless of decision."}
              </Body>
            </div>
            <div className="flex items-center gap-2">
              <div className="flex items-center gap-2 rounded-btn border border-rule-strong bg-surface px-3">
                <Search size={15} className="text-ink-mute" />
                <input
                  type="search"
                  placeholder="Entity, coverage, or code…"
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  className="h-10 w-64 border-0 bg-transparent text-[13.5px] text-ink placeholder:text-ink-mute focus:outline-none"
                />
              </div>
              {mode === "full" && (
                <select
                  value={decision}
                  onChange={(e) =>
                    setDecision(e.target.value as DecisionFilter)
                  }
                  className="h-10 rounded-btn border border-rule-strong bg-surface px-3 text-[13px] font-medium text-ink focus:border-info focus:outline-none"
                >
                  <option value="all">All decisions</option>
                  <option value="refer">Refer</option>
                  <option value="approve">Approve</option>
                  <option value="decline">Decline</option>
                </select>
              )}
            </div>
          </header>

          <div className="grid gap-4 sm:grid-cols-3">
            <Stat label={mode === "referral" ? "Referrals" : "Submissions"}>
              {filtered.length}
            </Stat>
            <Stat label="Awaiting" tone={awaiting > 0 ? "spot" : undefined}>
              {awaiting}
            </Stat>
            <Stat label="Premium under review" emphasis>
              {formatCurrency(totalPremium)}
            </Stat>
          </div>

          <Card pad="md" className="overflow-hidden p-0">
            <table className="w-full table-fixed text-[13px]">
              <thead>
                <tr className="border-b border-rule bg-surface-sunken text-left">
                  <ColHead width="w-[24%]">Entity</ColHead>
                  <ColHead width="w-[15%]">Coverage</ColHead>
                  <ColHead width="w-[14%]">Score</ColHead>
                  <ColHead width="w-[12%]">Decision</ColHead>
                  <ColHead width="w-[14%]">Premium</ColHead>
                  <ColHead width="w-[15%]">Status</ColHead>
                  <ColHead width="w-[6%]">{null}</ColHead>
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
  const decision = (sub.decision ?? "").toLowerCase();
  const decisionTone =
    decision === "approve"
      ? "pos"
      : decision === "decline"
        ? "neg"
        : decision === "refer"
          ? "warn"
          : "mute";
  const awaiting = (sub.referral_state ?? "").toLowerCase().includes("await");

  return (
    <tr className="border-b border-rule last:border-0 hover:bg-surface-sunken/40">
      <td className="px-5 py-3">
        <p className="font-medium text-ink">{sub.entity_name ?? "—"}</p>
        <Micro className="mt-0.5 block font-mono">
          {sub.submission_code}
        </Micro>
        {sub.broker_name && (
          <Micro className="mt-0.5 block">via {sub.broker_name}</Micro>
        )}
      </td>
      <td className="px-5 py-3 text-ink">{sub.coverage_configuration ?? "—"}</td>
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
      className={`px-5 py-2.5 text-[11px] font-semibold uppercase tracking-[0.08em] text-ink-mute ${width}`}
    >
      {children}
    </th>
  );
}

function Stat({
  label,
  tone,
  emphasis,
  children,
}: {
  label: string;
  tone?: "spot";
  emphasis?: boolean;
  children: React.ReactNode;
}) {
  return (
    <Card pad="md" variant={tone === "spot" ? "spot" : emphasis ? "info" : "default"}>
      <Micro
        className={cn(
          tone === "spot" && "text-spot-deep dark:text-spot",
          emphasis && "text-info-deep dark:text-info",
        )}
      >
        {label}
      </Micro>
      <div className="mt-2">
        <NumDisplay size={emphasis ? "lg" : "md"}>{children}</NumDisplay>
      </div>
    </Card>
  );
}

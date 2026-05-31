// No direct design counterpart; adapted from reim_carrier_pipeline.jsx
"use client";

import { useEffect, useMemo, useState } from "react";
import { Topbar } from "@/components/chrome/topbar";
import { Card } from "@/components/ui/card";
import { Chip } from "@/components/ui/chip";
import { KpiSnug } from "@/components/ui/kpi-snug";
import { AdminTable, type AdminTableCol } from "@/components/ui/admin-table";
import { Eyebrow, Body, Micro } from "@/components/ui/typography";
import { PageError, PageLoading, RoleGate } from "@/components/base/pageStates";
import { CarrierShell } from "@/components/chrome/carrier-shell";
import { isCarrierRole } from "@/lib/portalPaths";
import { useAuthStore } from "@/store/authStore";
import { useDsiStore, type ApiRecord } from "@/store/dsiStore";
import { formatCurrency, formatPercent } from "@/lib/format";

type DecisionKey = "approve" | "refer" | "decline" | "pending";

const DECISION_META: Record<
  DecisionKey,
  { label: string; tone: "pos" | "warn" | "neg" | "mute"; bar: string }
> = {
  approve: { label: "Approve", tone: "pos", bar: "bg-pos" },
  refer: { label: "Refer", tone: "warn", bar: "bg-warn" },
  decline: { label: "Decline", tone: "neg", bar: "bg-neg" },
  pending: { label: "Pending", tone: "mute", bar: "bg-ink-mute" },
};

function lineOf(s: ApiRecord): string {
  return String(s.coverage_configuration ?? s.coverage ?? "Unknown");
}

function premiumOf(s: ApiRecord): number {
  return s.final_premium ?? s.recommended_premium ?? 0;
}

function decisionKey(s: ApiRecord): DecisionKey {
  const dec = String(s.decision ?? "").toLowerCase();
  if (dec === "approve") return "approve";
  if (dec === "refer") return "refer";
  if (dec === "decline") return "decline";
  return "pending";
}

export default function CarrierMetricsPage() {
  const user = useAuthStore((s) => s.user);
  const submissions = useDsiStore((s) => s.submissions);
  const fetchSubmissions = useDsiStore((s) => s.fetchSubmissions);
  const [state, setState] = useState<"loading" | "ok" | "error">(
    submissions.length > 0 ? "ok" : "loading",
  );
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    fetchSubmissions()
      .then(() => !cancelled && setState("ok"))
      .catch((e) => {
        if (cancelled) return;
        setErr(e instanceof Error ? e.message : String(e));
        setState("error");
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
    ) : state === "loading" ? (
      <PageLoading />
    ) : state === "error" ? (
      <PageError message={err ?? "Unknown error"} />
    ) : (
      <MetricsBody submissions={submissions} />
    );

  return <CarrierShell>{inner}</CarrierShell>;
}

function MetricsBody({ submissions }: { submissions: ApiRecord[] }) {
  const [line, setLine] = useState<string>("all");

  const lines = useMemo(() => {
    const set = new Set<string>();
    for (const s of submissions) set.add(lineOf(s));
    return [...set].sort();
  }, [submissions]);

  const scoped = useMemo(
    () =>
      line === "all"
        ? submissions
        : submissions.filter((s) => lineOf(s) === line),
    [submissions, line],
  );

  const stats = useMemo(() => {
    const total = scoped.length;
    const decisionCounts: Record<DecisionKey, number> = {
      approve: 0,
      refer: 0,
      decline: 0,
      pending: 0,
    };
    let premiumWritten = 0;
    const byLine = new Map<string, number>();
    for (const s of scoped) {
      const key = decisionKey(s);
      decisionCounts[key]++;
      if (key === "approve") premiumWritten += premiumOf(s);
      const l = lineOf(s);
      byLine.set(l, (byLine.get(l) ?? 0) + 1);
    }
    const decided =
      decisionCounts.approve + decisionCounts.refer + decisionCounts.decline;
    const hitRate = decided > 0 ? decisionCounts.approve / decided : 0;
    // Decision quality = share of submissions the engine resolved without
    // leaving them pending. Cycle time has no backend field yet.
    const decisionQuality = total > 0 ? decided / total : 0;
    return {
      total,
      decisionCounts,
      premiumWritten,
      hitRate,
      decisionQuality,
      byLine: [...byLine.entries()].sort((a, b) => b[1] - a[1]),
    };
  }, [scoped]);

  const maxLine = Math.max(...stats.byLine.map(([, n]) => n), 1);

  const cohortCols: AdminTableCol[] = [
    { key: "line", label: "Line", width: "1.6fr" },
    { key: "volume", label: "Volume", align: "right", width: "90px" },
    { key: "approve", label: "Approve", align: "right", width: "90px" },
    { key: "refer", label: "Refer", align: "right", width: "90px" },
    { key: "decline", label: "Decline", align: "right", width: "90px" },
    { key: "hit", label: "Hit rate", align: "right", width: "100px" },
    { key: "premium", label: "Premium written", align: "right", width: "140px" },
  ];

  const cohortRows = useMemo(() => {
    const acc = new Map<
      string,
      { volume: number; approve: number; refer: number; decline: number; premium: number }
    >();
    for (const s of scoped) {
      const l = lineOf(s);
      const row =
        acc.get(l) ?? { volume: 0, approve: 0, refer: 0, decline: 0, premium: 0 };
      row.volume++;
      const key = decisionKey(s);
      if (key === "approve") {
        row.approve++;
        row.premium += premiumOf(s);
      } else if (key === "refer") row.refer++;
      else if (key === "decline") row.decline++;
      acc.set(l, row);
    }
    return [...acc.entries()]
      .sort((a, b) => b[1].volume - a[1].volume)
      .map(([l, r]) => {
        const decided = r.approve + r.refer + r.decline;
        return {
          line: l,
          volume: r.volume,
          approve: r.approve,
          refer: r.refer,
          decline: r.decline,
          hit: decided > 0 ? formatPercent(r.approve / decided, 0) : "—",
          premium: r.premium > 0 ? formatCurrency(r.premium) : "—",
        };
      });
  }, [scoped]);

  return (
    <>
      <Topbar crumbs={["Carrier Portal", "Performance Metrics"]} />
      <div className="flex-1 overflow-y-auto px-9 py-7">
        <div className="grid gap-4">
          <header>
            <Eyebrow>Underwriting</Eyebrow>
            <Body className="mt-2 max-w-2xl text-[15px] leading-relaxed">
              Engine throughput, decision mix, and premium under management.
            </Body>
          </header>

          {/* KPI strip */}
          <Card pad="lg">
            <div className="grid gap-6 sm:grid-cols-3 lg:grid-cols-5">
              <KpiSnug label="Volume" value={stats.total} />
              <KpiSnug
                label="Hit rate"
                value={stats.total > 0 ? formatPercent(stats.hitRate, 0) : "—"}
                tone="pos"
              />
              <KpiSnug label="Cycle time" value="—" />
              <KpiSnug
                label="Decision quality"
                value={
                  stats.total > 0 ? formatPercent(stats.decisionQuality, 0) : "—"
                }
                tone="info"
              />
              <KpiSnug
                label="Premium written"
                value={
                  stats.premiumWritten > 0
                    ? formatCurrency(stats.premiumWritten)
                    : "—"
                }
              />
            </div>
          </Card>

          {/* Line filter pills */}
          <div className="flex flex-wrap items-center gap-2">
            <Micro className="mr-1">Line:</Micro>
            <button
              type="button"
              onClick={() => setLine("all")}
              className="focus:outline-none"
            >
              <Chip
                variant={line === "all" ? "info" : "outline"}
                className="cursor-pointer"
              >
                All ({submissions.length})
              </Chip>
            </button>
            {lines.map((l) => (
              <button
                key={l}
                type="button"
                onClick={() => setLine(l)}
                className="focus:outline-none"
              >
                <Chip
                  variant={line === l ? "info" : "outline"}
                  className="cursor-pointer"
                >
                  {l}
                </Chip>
              </button>
            ))}
          </div>

          {/* 2-up: volume by line + decision mix */}
          <div className="grid gap-4 lg:grid-cols-2">
            <Card pad="lg">
              <Eyebrow className="mb-4">Volume by line</Eyebrow>
              {stats.byLine.length === 0 ? (
                <Body className="italic">No submissions in scope.</Body>
              ) : (
                <ul className="space-y-2.5">
                  {stats.byLine.slice(0, 8).map(([name, count]) => (
                    <li key={name}>
                      <div className="flex items-baseline justify-between text-[13px]">
                        <span className="truncate font-medium text-ink">
                          {name}
                        </span>
                        <span className="font-semibold tabular-nums text-ink">
                          {count}
                        </span>
                      </div>
                      <div className="mt-1 h-1.5 overflow-hidden rounded-full bg-surface-sunken">
                        <div
                          className="h-full bg-info"
                          style={{ width: `${(count / maxLine) * 100}%` }}
                        />
                      </div>
                    </li>
                  ))}
                </ul>
              )}
            </Card>

            <Card pad="lg">
              <Eyebrow className="mb-4">Decision mix</Eyebrow>
              <ul className="space-y-2.5">
                {(Object.keys(DECISION_META) as DecisionKey[]).map((key) => {
                  const count = stats.decisionCounts[key];
                  const meta = DECISION_META[key];
                  const pct = stats.total > 0 ? count / stats.total : 0;
                  return (
                    <li key={key}>
                      <div className="flex items-baseline justify-between text-[13px]">
                        <Chip variant={meta.tone} size="sm">
                          {meta.label}
                        </Chip>
                        <span className="font-semibold tabular-nums text-ink">
                          {count}{" "}
                          <span className="font-normal text-ink-mute">
                            {formatPercent(pct, 0)}
                          </span>
                        </span>
                      </div>
                      <div className="mt-1 h-1.5 overflow-hidden rounded-full bg-surface-sunken">
                        <div
                          className={`h-full ${meta.bar}`}
                          style={{ width: `${pct * 100}%` }}
                        />
                      </div>
                    </li>
                  );
                })}
              </ul>
            </Card>
          </div>

          {/* Cohort metrics by line */}
          <Card pad="none" className="overflow-hidden" header="Cohort metrics by line">
            {cohortRows.length === 0 ? (
              <div className="px-5 py-8 text-center">
                <Body className="italic">No submissions in scope.</Body>
              </div>
            ) : (
              <AdminTable
                cols={cohortCols}
                rows={cohortRows}
                getRowKey={(r) => String(r.line)}
              />
            )}
          </Card>
        </div>
      </div>
    </>
  );
}

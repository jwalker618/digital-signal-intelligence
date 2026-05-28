"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { Topbar } from "@/components/chrome/topbar";
import {
  AdminTable,
  Body,
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
import { fmtRelative } from "@/lib/utils";
import { cn } from "@/lib/utils";
import type { ProposalStatus, ProposalSummary } from "@/types/recalibration";

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

type StatusFilter = ProposalStatus | "ALL";

const STATUS_FILTERS: { value: StatusFilter; label: string }[] = [
  { value: "ALL", label: "All" },
  { value: "PENDING_REVIEW", label: "Pending" },
  { value: "APPROVED", label: "Approved" },
  { value: "DEPLOYED", label: "Deployed" },
  { value: "REJECTED", label: "Rejected" },
];

export default function AdminRecalibrationPage() {
  return (
    <PermissionGate
      permission="recalibration:view"
      fallback={
        <PageError message="You don't have recalibration:view permission." />
      }
    >
      <RecalInner />
    </PermissionGate>
  );
}

function RecalInner() {
  const [data, setData] = useState<ProposalSummary[] | null>(null);
  const [state, setState] = useState<"loading" | "ok" | "error">("loading");
  const [err, setErr] = useState<string | null>(null);
  const [statusFilter, setStatusFilter] = useState<StatusFilter>("ALL");
  const [coverageFilter, setCoverageFilter] = useState<string>("ALL");

  useEffect(() => {
    let cancelled = false;
    setState("loading");
    const params = new URLSearchParams();
    if (statusFilter !== "ALL") params.set("status", statusFilter);
    api
      .get<{ proposals: ProposalSummary[] }>(
        `/api/v1/recalibration/proposals?${params.toString()}`,
      )
      .then((r) => {
        if (cancelled) return;
        setData(r.proposals ?? []);
        setState("ok");
      })
      .catch((e) => {
        if (cancelled) return;
        setErr(e instanceof Error ? e.message : String(e));
        setState("error");
      });
    return () => {
      cancelled = true;
    };
  }, [statusFilter]);

  const proposals = data ?? [];
  const coverages = useMemo(() => {
    const set = new Set<string>();
    for (const p of proposals) set.add(p.coverage);
    return [...set].sort();
  }, [proposals]);

  const filtered = useMemo(
    () =>
      coverageFilter === "ALL"
        ? proposals
        : proposals.filter((p) => p.coverage === coverageFilter),
    [proposals, coverageFilter],
  );

  const counts = {
    pending: proposals.filter((p) => p.status === "PENDING_REVIEW").length,
    approved: proposals.filter((p) => p.status === "APPROVED").length,
    deployed: proposals.filter((p) => p.status === "DEPLOYED").length,
    rejected: proposals.filter((p) => p.status === "REJECTED").length,
  };

  const cols: AdminTableCol[] = [
    { key: "id", label: "ID", width: "110px" },
    { key: "coverage", label: "Coverage", width: "1fr" },
    { key: "config", label: "Config", width: "1.4fr" },
    { key: "trigger", label: "Trigger", width: "1.6fr" },
    { key: "sample", label: "Sample", align: "right", width: "90px" },
    { key: "weights", label: "Weights", align: "right", width: "90px" },
    { key: "tiers", label: "Tiers", align: "right", width: "80px" },
    { key: "proposed", label: "Proposed", width: "130px" },
    { key: "status", label: "Status", width: "140px" },
    { key: "open", label: "", align: "right", width: "90px" },
  ];

  const rows: AdminTableRow[] = filtered.map((p) => ({
    id: <code className="text-[12px] font-bold text-ink">{shortId(p.id)}</code>,
    coverage: (
      <span className="font-mono text-[12px] font-semibold uppercase text-ink">
        {p.coverage}
      </span>
    ),
    config: <code className="text-[12px] text-ink-soft">{p.config_name}</code>,
    trigger: (
      <span className="text-[12.5px] text-ink-soft">{p.trigger}</span>
    ),
    sample: (
      <span className="tabular-nums text-ink-soft">
        {p.sample_size.toLocaleString()}
      </span>
    ),
    weights: (
      <span
        className={cn(
          "tabular-nums",
          p.weight_change_count > 0
            ? "font-semibold text-ink"
            : "text-ink-mute",
        )}
      >
        {p.weight_change_count}
      </span>
    ),
    tiers: (
      <span
        className={cn(
          "tabular-nums",
          p.tier_change_count > 0
            ? "font-semibold text-ink"
            : "text-ink-mute",
        )}
      >
        {p.tier_change_count}
      </span>
    ),
    proposed: <Micro>{fmtRelative(p.proposed_at)}</Micro>,
    status: (
      <Chip size="sm" variant={STATUS_TONE[p.status]}>
        {p.status.replace("_", " ")}
      </Chip>
    ),
    open: (
      <Link
        href={`/admin/recalibration/${p.id}`}
        className="text-[12px] font-semibold text-info hover:underline"
      >
        Review →
      </Link>
    ),
  }));

  return (
    <>
      <Topbar crumbs={["Admin", "Recalibration"]} />
      <div className="flex-1 overflow-y-auto px-9 py-7">
        <div className="mx-auto grid max-w-[1400px] gap-4">
          <header className="flex items-end justify-between gap-6">
            <div>
              <Eyebrow>Recalibration</Eyebrow>
              <h1 className="mt-1.5 font-display text-[32px] font-semibold leading-none tracking-tight text-ink">
                Proposals awaiting governance
              </h1>
              <Body className="mt-1.5">
                Model-suggested weight + tier changes. Approve → Deploy through
                the detail page. Drift-triggered proposals are prioritised.
              </Body>
            </div>
            <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
              <MiniKpi label="Pending" value={counts.pending} />
              <MiniKpi label="Approved" value={counts.approved} />
              <MiniKpi label="Deployed" value={counts.deployed} />
              <MiniKpi label="Rejected" value={counts.rejected} />
            </div>
          </header>

          <div className="flex flex-wrap items-center gap-2">
            <Micro className="mr-1">Status:</Micro>
            {STATUS_FILTERS.map((f) => (
              <FilterChip
                key={f.value}
                active={statusFilter === f.value}
                onClick={() => setStatusFilter(f.value)}
              >
                {f.label}
              </FilterChip>
            ))}
            {coverages.length > 0 && (
              <>
                <Micro className="ml-3 mr-1">Coverage:</Micro>
                <FilterChip
                  active={coverageFilter === "ALL"}
                  onClick={() => setCoverageFilter("ALL")}
                >
                  All
                </FilterChip>
                {coverages.map((c) => (
                  <FilterChip
                    key={c}
                    active={coverageFilter === c}
                    onClick={() => setCoverageFilter(c)}
                  >
                    {c}
                  </FilterChip>
                ))}
              </>
            )}
            <span className="ml-auto text-[12px] text-ink-mute">
              Sort: newest first
            </span>
          </div>

          {state === "loading" && <PageLoading message="Loading proposals…" />}
          {state === "error" && <PageError message={err ?? "Unknown error"} />}
          {state === "ok" && (
            <Card pad="none">
              <AdminTable cols={cols} rows={rows} />
              {filtered.length === 0 && (
                <div className="px-5 py-8 text-center">
                  <Body className="italic">No proposals.</Body>
                </div>
              )}
            </Card>
          )}
        </div>
      </div>
    </>
  );
}

function FilterChip({
  active,
  onClick,
  children,
}: {
  active: boolean;
  onClick: () => void;
  children: React.ReactNode;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={cn(
        "inline-flex items-center gap-1.5 rounded-chip px-2.5 py-1 text-[11.5px] font-medium transition-colors",
        active
          ? "bg-ink text-canvas"
          : "bg-surface-sunken text-ink-soft hover:bg-surface-elev",
      )}
    >
      {children}
    </button>
  );
}

function shortId(id: string): string {
  if (id.length <= 12) return id;
  return id.slice(0, 8);
}

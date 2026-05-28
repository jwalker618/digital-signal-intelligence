"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { ChevronRight, TrendingUpDown } from "lucide-react";
import { Topbar } from "@/components/chrome/topbar";
import { Card } from "@/components/ui/card";
import { Chip } from "@/components/ui/chip";
import { Eyebrow, NumDisplay, Body, Micro } from "@/components/ui/typography";
import { PageError, PageLoading } from "@/components/base/pageStates";
import { PermissionGate } from "@/components/shared/PermissionGate";
import { api } from "@/lib/api";
import { formatText } from "@/lib/format";
import { fmtRelative } from "@/lib/utils";
import type { ProposalStatus, ProposalSummary } from "@/types/recalibration";

const STATUS_TONE: Record<ProposalStatus, "mute" | "info" | "warn" | "pos" | "neg"> = {
  DRAFT: "mute",
  PENDING_REVIEW: "warn",
  APPROVED: "info",
  REJECTED: "neg",
  DEPLOYED: "pos",
};

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
  const [statusFilter, setStatusFilter] = useState<ProposalStatus | "">("");

  useEffect(() => {
    let cancelled = false;
    setState("loading");
    const params = new URLSearchParams();
    if (statusFilter) params.set("status", statusFilter);
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

  if (state === "error") return <PageError message={err ?? "Unknown error"} />;

  const proposals = data ?? [];
  const pending = proposals.filter((p) => p.status === "PENDING_REVIEW").length;
  const deployed = proposals.filter((p) => p.status === "DEPLOYED").length;

  return (
    <>
      <Topbar crumbs={["Admin", "Recalibration"]} />
      <div className="flex-1 overflow-y-auto px-9 py-7">
        <div className="mx-auto grid max-w-[1400px] gap-6">
          <header className="flex items-end justify-between gap-6">
            <div>
              <Eyebrow>Loop</Eyebrow>
              <h1 className="mt-1 font-display text-[32px] font-semibold leading-none tracking-tight text-ink">
                Recalibration
              </h1>
              <Body className="mt-2">
                Proposed weight and tier-threshold changes from the
                continuous-learning loop. Review, approve, deploy.
              </Body>
            </div>
            <select
              value={statusFilter}
              onChange={(e) =>
                setStatusFilter(e.target.value as ProposalStatus | "")
              }
              className="h-10 rounded-btn border border-rule-strong bg-surface px-3 text-[13px] font-medium text-ink focus:border-info focus:outline-none"
            >
              <option value="">All statuses</option>
              <option value="DRAFT">Draft</option>
              <option value="PENDING_REVIEW">Pending review</option>
              <option value="APPROVED">Approved</option>
              <option value="REJECTED">Rejected</option>
              <option value="DEPLOYED">Deployed</option>
            </select>
          </header>

          <div className="grid gap-4 sm:grid-cols-3">
            <Stat label="Proposals">{proposals.length}</Stat>
            <Stat label="Pending review" tone={pending > 0 ? "spot" : undefined}>
              {pending}
            </Stat>
            <Stat label="Deployed" tone="pos">
              {deployed}
            </Stat>
          </div>

          {state === "loading" && <PageLoading message="Loading proposals…" />}
          {state === "ok" && (
            <Card pad="md" className="overflow-hidden p-0">
              <table className="w-full table-fixed text-[13px]">
                <thead>
                  <tr className="border-b border-rule bg-surface-sunken text-left">
                    <ColHead width="w-[22%]">Coverage / config</ColHead>
                    <ColHead width="w-[14%]">Status</ColHead>
                    <ColHead width="w-[18%]">Trigger</ColHead>
                    <ColHead width="w-[10%]">Changes</ColHead>
                    <ColHead width="w-[12%]">Sample</ColHead>
                    <ColHead width="w-[14%]">Proposed</ColHead>
                    <ColHead width="w-[6%]">{null}</ColHead>
                    <ColHead width="w-[4%]">{null}</ColHead>
                  </tr>
                </thead>
                <tbody>
                  {proposals.map((p) => (
                    <tr
                      key={p.id}
                      className="border-b border-rule last:border-0 hover:bg-surface-sunken/40"
                    >
                      <td className="px-5 py-3">
                        <div className="flex items-center gap-2">
                          <TrendingUpDown
                            size={13}
                            className="text-ink-mute"
                          />
                          <span className="font-medium text-ink">
                            {p.coverage}
                          </span>
                        </div>
                        <Micro className="mt-0.5 block">
                          {p.config_name}
                        </Micro>
                      </td>
                      <td className="px-5 py-3">
                        <Chip variant={STATUS_TONE[p.status]} size="sm">
                          {formatText(p.status, "capitalize")}
                        </Chip>
                      </td>
                      <td className="px-5 py-3 text-ink-soft">{p.trigger}</td>
                      <td className="px-5 py-3 text-ink-soft">
                        <Micro className="block">
                          {p.weight_change_count} weight
                          {p.weight_change_count === 1 ? "" : "s"}
                        </Micro>
                        <Micro className="block">
                          {p.tier_change_count} tier
                          {p.tier_change_count === 1 ? "" : "s"}
                        </Micro>
                      </td>
                      <td className="px-5 py-3 tabular-nums text-ink-soft">
                        n = {p.sample_size.toLocaleString()}
                      </td>
                      <td className="px-5 py-3 text-ink-soft">
                        <span>{fmtRelative(p.proposed_at)}</span>
                        <Micro className="mt-0.5 block">
                          by {p.proposed_by}
                        </Micro>
                      </td>
                      <td className="px-5 py-3 text-right">
                        <Link
                          href={`/admin/recalibration/${p.id}`}
                          className="text-[13px] font-semibold text-info hover:underline"
                        >
                          Open
                        </Link>
                      </td>
                      <td className="px-5 py-3 text-right">
                        <Link
                          href={`/admin/recalibration/${p.id}`}
                          className="inline-flex items-center text-ink-mute hover:text-ink"
                        >
                          <ChevronRight size={16} />
                        </Link>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
              {proposals.length === 0 && (
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

function Stat({
  label,
  tone,
  children,
}: {
  label: string;
  tone?: "pos" | "spot";
  children: React.ReactNode;
}) {
  return (
    <Card pad="md" variant={tone === "spot" ? "spot" : "default"}>
      <Micro
        className={
          tone === "pos"
            ? "text-pos"
            : tone === "spot"
              ? "text-spot-deep dark:text-spot"
              : ""
        }
      >
        {label}
      </Micro>
      <div className="mt-2">
        <NumDisplay size="md">{children}</NumDisplay>
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

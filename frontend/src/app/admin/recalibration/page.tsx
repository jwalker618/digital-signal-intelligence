// FE: Recalibration governance dashboard (C-3).
//
// Lists proposals with a compact status/coverage filter bar. Each row
// links to the detail page which holds the approve / reject / deploy /
// simulate actions.

"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { AlertTriangle, RefreshCw } from "lucide-react";

import ViewCanvas from "@/components/ViewCanvas";
import { api, fmtRelative } from "@/lib/api";
import { StatusBadge } from "@/components/shared/StatusBadge";
import { useDsiStore } from "@/store/dsiStore";
import type { ProposalSummary } from "@/types/recalibration";

const STATUSES = ["", "DRAFT", "PENDING_REVIEW", "APPROVED", "REJECTED", "DEPLOYED"];

export default function RecalibrationPage() {
  const router = useRouter();
  const setPageQuickAction = useDsiStore((s) => s.setPageQuickAction);

  const [items, setItems] = useState<ProposalSummary[]>([]);
  const [status, setStatus] = useState("");
  const [coverage, setCoverage] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function load() {
    setLoading(true);
    setError(null);
    try {
      const params = new URLSearchParams();
      if (status) params.set("status", status);
      if (coverage) params.set("coverage", coverage);
      params.set("limit", "100");
      const data = await api.get<ProposalSummary[]>(
        `/api/v1/recalibration/proposals?${params.toString()}`,
      );
      setItems(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Load failed");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    setPageQuickAction(
      <button
        onClick={() => void load()}
        disabled={loading}
        className="generate-actiontext disabled:opacity-50"
      >
        <RefreshCw className={`icon ${loading ? "animate-spin" : ""}`} />
        Refresh
      </button>,
    );
    return () => setPageQuickAction(null);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [loading]);

  return (
    <ViewCanvas unstyledMain={true}>
      <div className="flex flex-col h-full bg-generate-background text-generate-contrast-analysis p-generate-pad animate-in fade-in duration-500">

        {/* FIXED TOP */}
        <div className="shrink-0 text-generate-contrast-background pb-4 text-sm flex items-center gap-3">
          <h1>Showing {items.length} proposals.</h1>
          <div className="flex items-center gap-2 ml-auto">
            <select
              value={status}
              onChange={(e) => setStatus(e.target.value)}
              className="generate-inputbox"
            >
              {STATUSES.map((s) => (
                <option key={s} value={s}>{s || "All statuses"}</option>
              ))}
            </select>
            <input
              value={coverage}
              onChange={(e) => setCoverage(e.target.value)}
              placeholder="Coverage"
              className="generate-inputbox w-32"
            />
            <button onClick={() => void load()} className="generate-actionbutton">
              Apply
            </button>
          </div>
        </div>

        {error && (
          <div className="generate-notificationpill shrink-0 mb-generate-pad flex items-center gap-2">
            <AlertTriangle className="icon" /> {error}
          </div>
        )}

        {/* SCROLLABLE TABLE */}
        <div className="flex-1 overflow-y-auto no-scrollbar pb-12">
          <table className="w-full text-left whitespace-nowrap border-collapse">
            <thead className="sticky top-0 z-20 bg-generate-background">
              <tr className="generate-grid-table-header text-generate-contrast-background">
                <th className="p-1.5">Coverage</th>
                <th className="p-1.5">Config</th>
                <th className="p-1.5">Trigger</th>
                <th className="p-1.5 text-right">Sample</th>
                <th className="p-1.5 text-right">Weights</th>
                <th className="p-1.5 text-right">Tiers</th>
                <th className="p-1.5">Proposed</th>
                <th className="p-1.5">Status</th>
                <th className="p-1.5"></th>
              </tr>
            </thead>
            <tbody>
              {items.map((p) => (
                <tr
                  key={p.id}
                  onClick={() => router.push(`/admin/recalibration/${p.id}`)}
                  className="cursor-pointer even:bg-generate-contrast-analysis text-generate-contrast-background hover:text-generate-selected"
                >
                  <td className="p-1.5 font-mono text-xs">{p.coverage}</td>
                  <td className="p-1.5 font-mono text-xs">{p.config_name}</td>
                  <td className="p-1.5 text-xs opacity-80">{p.trigger}</td>
                  <td className="p-1.5 text-right tabular-nums">{p.sample_size}</td>
                  <td className="p-1.5 text-right tabular-nums">{p.weight_change_count}</td>
                  <td className="p-1.5 text-right tabular-nums">{p.tier_change_count}</td>
                  <td className="p-1.5 text-xs opacity-80">{fmtRelative(p.proposed_at)}</td>
                  <td className="p-1.5"><StatusBadge status={p.status} /></td>
                  <td className="p-1.5 text-xs text-generate-selected">Review →</td>
                </tr>
              ))}
            </tbody>
          </table>

          {items.length === 0 && !loading && (
            <div className="generate-user-message">No proposals.</div>
          )}
        </div>
      </div>
    </ViewCanvas>
  );
}

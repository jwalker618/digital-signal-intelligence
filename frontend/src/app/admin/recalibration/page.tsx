// FE: Recalibration governance dashboard (C-3).
//
// Lists proposals with status filter. Each row links to the detail
// page which holds the approve / reject / deploy / simulate actions.

"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { AlertTriangle, RefreshCw } from "lucide-react";

import { api, fmtRelative } from "@/lib/api";
import { StatusBadge } from "@/components/shared/StatusBadge";
import type { ProposalSummary } from "@/types/recalibration";

const STATUSES = [
  "",
  "DRAFT",
  "PENDING_REVIEW",
  "APPROVED",
  "REJECTED",
  "DEPLOYED",
];

export default function RecalibrationPage() {
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

  return (
    <main className="p-6 flex flex-col gap-4">
      <header className="flex items-center gap-3">
        <h1 className="font-inter text-2xl tracking-wide">Recalibration</h1>
        <button
          onClick={() => void load()}
          disabled={loading}
          className="ml-auto flex items-center gap-1 border-2 border-dsi-outline py-1 px-3 rounded text-sm"
        >
          <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin" : ""}`} />
          Refresh
        </button>
      </header>

      {error && (
        <div className="border-2 border-dsi-negative rounded p-3 text-sm flex items-center gap-2">
          <AlertTriangle className="w-4 h-4 text-dsi-negative" /> {error}
        </div>
      )}

      <section className="flex items-end gap-2 border-2 border-dsi-outline rounded p-3">
        <label className="flex flex-col gap-0.5">
          <span className="text-xs opacity-60">Status</span>
          <select
            value={status}
            onChange={(e) => setStatus(e.target.value)}
            className="border-2 border-dsi-outline bg-dsi-background px-2 py-1 rounded text-sm"
          >
            {STATUSES.map((s) => (
              <option key={s} value={s}>
                {s || "All"}
              </option>
            ))}
          </select>
        </label>
        <label className="flex flex-col gap-0.5">
          <span className="text-xs opacity-60">Coverage</span>
          <input
            value={coverage}
            onChange={(e) => setCoverage(e.target.value)}
            className="border-2 border-dsi-outline bg-dsi-background px-2 py-1 rounded text-sm font-mono w-24"
          />
        </label>
        <button
          onClick={() => void load()}
          className="bg-dsi-contrast-background text-dsi-background py-1 px-3 rounded text-sm font-semibold"
        >
          Apply
        </button>
      </section>

      <section className="border-2 border-dsi-outline rounded">
        <table className="w-full text-sm">
          <thead>
            <tr className="text-xs uppercase opacity-60 text-left">
              <th className="py-1 px-3">Coverage</th>
              <th className="py-1 px-3">Config</th>
              <th className="py-1 px-3">Trigger</th>
              <th className="py-1 px-3 text-right">Sample</th>
              <th className="py-1 px-3 text-right">Weights</th>
              <th className="py-1 px-3 text-right">Tiers</th>
              <th className="py-1 px-3">Proposed</th>
              <th className="py-1 px-3">Status</th>
              <th className="py-1 px-3"></th>
            </tr>
          </thead>
          <tbody>
            {items.map((p) => (
              <tr key={p.id} className="border-t border-dsi-outline/20">
                <td className="py-1 px-3 font-mono text-xs">{p.coverage}</td>
                <td className="py-1 px-3 font-mono text-xs">{p.config_name}</td>
                <td className="py-1 px-3 text-xs opacity-80">{p.trigger}</td>
                <td className="py-1 px-3 text-right tabular-nums">
                  {p.sample_size}
                </td>
                <td className="py-1 px-3 text-right tabular-nums">
                  {p.weight_change_count}
                </td>
                <td className="py-1 px-3 text-right tabular-nums">
                  {p.tier_change_count}
                </td>
                <td className="py-1 px-3 text-xs opacity-80">
                  {fmtRelative(p.proposed_at)}
                </td>
                <td className="py-1 px-3">
                  <StatusBadge status={p.status} />
                </td>
                <td className="py-1 px-3">
                  <Link
                    href={`/admin/recalibration/${p.id}`}
                    className="text-dsi-selected hover:underline text-xs"
                  >
                    Review →
                  </Link>
                </td>
              </tr>
            ))}
            {items.length === 0 && !loading && (
              <tr>
                <td colSpan={9} className="p-4 opacity-60 text-center">
                  No proposals.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </section>
    </main>
  );
}

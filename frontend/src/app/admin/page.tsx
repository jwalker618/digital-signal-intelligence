// FE: Admin landing -- System Health + Pipeline (B-1).

"use client";

import { useEffect, useState } from "react";
import { AlertTriangle, CheckCircle2, RefreshCw } from "lucide-react";

import { api, fmtDate } from "@/lib/api";
import { formatNumber, formatPercent } from "@/lib/format";

import type {
  ExtractorHealth,
  PipelineMetrics,
  SystemHealth,
} from "@/types/admin";

import { StatusBadge } from "@/components/shared/StatusBadge";

export default function AdminSystemHealthPage() {
  const [health, setHealth] = useState<SystemHealth | null>(null);
  const [extractors, setExtractors] = useState<ExtractorHealth[]>([]);
  const [pipeline, setPipeline] = useState<PipelineMetrics | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  async function load() {
    setLoading(true);
    setError(null);
    try {
      const [h, e, p] = await Promise.all([
        api.get<SystemHealth>("/api/v1/admin/health"),
        api.get<{ extractors: ExtractorHealth[] }>(
          "/api/v1/admin/health/extractors",
        ),
        api.get<PipelineMetrics>("/api/v1/admin/health/pipeline"),
      ]);
      setHealth(h);
      setExtractors(e.extractors ?? []);
      setPipeline(p);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void load();
    const t = setInterval(() => void load(), 30_000);
    return () => clearInterval(t);
  }, []);

  return (
    <main className="p-6 flex flex-col gap-4">
      <header className="flex items-center gap-3">
        <h1 className="font-inter text-2xl tracking-wide">System Health</h1>
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

      {health && (
        <section className="border-2 border-dsi-outline rounded p-4">
          <div className="flex items-center justify-between mb-2">
            <h2 className="font-semibold tracking-wider">Overall</h2>
            <div className="flex items-center gap-2">
              <StatusBadge status={health.status} />
              <span className="text-xs opacity-60">
                as of {fmtDate(health.checked_at)}
              </span>
            </div>
          </div>
          <ul className="divide-y divide-dsi-outline/20">
            {Object.entries(health.components ?? {}).map(([name, c]) => (
              <li key={name} className="flex items-center gap-3 py-1 text-sm">
                <StatusBadge status={c.status} />
                <span className="font-mono">{name}</span>
                {c.detail && <span className="opacity-70">{c.detail}</span>}
              </li>
            ))}
          </ul>
        </section>
      )}

      {pipeline && (
        <section className="border-2 border-dsi-outline rounded p-4">
          <h2 className="font-semibold tracking-wider mb-2">
            Pipeline ({pipeline.window_hours}h window)
          </h2>
          <div className="grid grid-cols-2 md:grid-cols-5 gap-3 text-sm">
            <Stat label="Assessments" value={formatNumber(pipeline.total_assessments)} />
            <Stat label="p50" value={`${formatNumber(pipeline.p50_ms)} ms`} />
            <Stat label="p95" value={`${formatNumber(pipeline.p95_ms)} ms`} />
            <Stat label="p99" value={`${formatNumber(pipeline.p99_ms)} ms`} />
            <Stat label="Failure rate" value={formatPercent(pipeline.failure_rate, 2)} />
          </div>
        </section>
      )}

      <section className="border-2 border-dsi-outline rounded p-4">
        <h2 className="font-semibold tracking-wider mb-2">Extractors</h2>
        <table className="w-full text-sm">
          <thead>
            <tr className="text-xs uppercase opacity-60 text-left">
              <th className="py-1">Extractor</th>
              <th className="py-1">Mode</th>
              <th className="py-1 text-right">Success</th>
              <th className="py-1 text-right">Errors</th>
              <th className="py-1">Status</th>
              <th className="py-1">Last error</th>
            </tr>
          </thead>
          <tbody>
            {extractors.map((e) => (
              <tr key={e.name} className="border-t border-dsi-outline/20">
                <td className="py-1 pr-2 font-mono text-xs">{e.name}</td>
                <td className="py-1 pr-2 opacity-80">{e.mode}</td>
                <td className="py-1 pr-2 text-right tabular-nums">
                  {e.success_count}
                </td>
                <td className="py-1 pr-2 text-right tabular-nums">
                  {e.error_count}
                </td>
                <td className="py-1 pr-2">
                  <StatusBadge status={e.status} />
                </td>
                <td className="py-1 opacity-70 text-xs truncate max-w-xs">
                  {e.last_error ?? "—"}
                </td>
              </tr>
            ))}
            {extractors.length === 0 && (
              <tr>
                <td className="py-4 opacity-60" colSpan={6}>
                  No extractor activity yet.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </section>

      {!loading && health?.status === "green" && (
        <p className="text-xs opacity-50 flex items-center gap-2">
          <CheckCircle2 className="w-4 h-4 text-dsi-positive" />
          All systems nominal. Auto-refresh every 30s.
        </p>
      )}
    </main>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="border border-dsi-outline/30 rounded p-2">
      <div className="text-xs opacity-60 uppercase tracking-wider">{label}</div>
      <div className="font-inter text-lg tabular-nums">{value}</div>
    </div>
  );
}

// FE: Admin landing -- System Health + Pipeline (B-1).

"use client";

import { useEffect, useState } from "react";

import {
  Gauge,
  Activity,
  AlertTriangle,
  CheckCircle2,
  RefreshCw,
  Workflow,
} from "lucide-react";

import ViewCanvas from "@/components/ViewCanvas";
import { CardGrid, StandardCard } from "@/components/base/cards";
import { api, fmtDate } from "@/lib/api";
import { formatNumber, formatPercent } from "@/lib/format";
import { StatusBadge } from "@/components/shared/StatusBadge";
import { useDsiStore } from "@/store/dsiStore";

import type {
  ExtractorHealth,
  PipelineMetrics,
  SystemHealth,
} from "@/types/admin";

export default function AdminSystemHealthPage() {
  const setPageQuickAction = useDsiStore((s) => s.setPageQuickAction);

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
  }, [loading, setPageQuickAction]);

  return (
    
    <ViewCanvas unstyledMain={true}>
      <div className="w-full no-scrollbar animate-in fade-in duration-500 pb-12 pt-generate-pad">

        {error && (
          <div className="generate-notificationpill mb-generate-pad flex items-center gap-2">
            <AlertTriangle className="icon" /> {error}
          </div>
        )}

        <CardGrid cols="grid-cols-1">

          <StandardCard title="Overall" lucideIcon={Activity}>
            {health ? (
              <>
                <div className="flex items-center gap-2 mb-generate-pad">
                  <StatusBadge status={health.status} />
                  <span className="text-xs">
                    as of {fmtDate(health.checked_at)}
                  </span>
                </div>

                <ul className="divide-y divide-generate-outline/20">
                  {Object.entries(health.components ?? {}).map(([name, c]) => (
                    
                    <li key={name} className="flex items-center gap-3 py-1 text-sm">
                      <StatusBadge status={c.status} />
                      <span>{name}</span>
                      {c.detail && <span>{c.detail}</span>}
                    </li>

                  ))}
                </ul>

              </>
            ) : (
              <div className="generate-user-message">No health data.</div>
            )}
          </StandardCard>

          <StandardCard
            title={`Pipeline${pipeline ? ` (${pipeline.window_hours}h window)` : ""}`}
            lucideIcon={Gauge}
          >
            {pipeline ? (
              <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
                <Kpi label="Assessments" value={formatNumber(pipeline.total_assessments)} />
                <Kpi label="p50" value={`${formatNumber(pipeline.p50_ms)} ms`} />
                <Kpi label="p95" value={`${formatNumber(pipeline.p95_ms)} ms`} />
                <Kpi label="p99" value={`${formatNumber(pipeline.p99_ms)} ms`} />
                <Kpi label="Failure rate" value={formatPercent(pipeline.failure_rate, 2)} />
              </div>
            ) : (
              <div className="generate-user-message">No pipeline data.</div>
            )}
          </StandardCard>

          <StandardCard title="Extractors" lucideIcon={Workflow}>
            <table className="w-full text-left whitespace-nowrap border-collapse">
              
              <thead>
                <tr className="generate-grid-table-header text-generate-contrast-background">
                  <th className="p-1.5">Extractor</th>
                  <th className="p-1.5">Mode</th>
                  <th className="p-1.5 text-right">Success</th>
                  <th className="p-1.5 text-right">Errors</th>
                  <th className="p-1.5">Status</th>
                  <th className="p-1.5 border-none">Last error</th>
                </tr>
              </thead>
              
              <tbody>
                {extractors.map((e) => (
                  <tr key={e.name} className="even:bg-generate-contrast-analysis text-generate-contrast-background">
                    <td className="p-1.5 text-xs">{e.name}</td>
                    <td className="p-1.5">{e.mode}</td>
                    <td className="p-1.5 text-right tabular-nums">{e.success_count}</td>
                    <td className="p-1.5 text-right tabular-nums">{e.error_count}</td>
                    <td className="p-1.5"><StatusBadge status={e.status} /></td>
                    <td className="p-1.5 text-xs truncate max-w-xs">
                      {e.last_error ?? "—"}
                    </td>
                  </tr>
                ))}
              </tbody>

            </table>
            
            {extractors.length === 0 && (
              <div className="generate-user-message">No extractor activity yet.</div>
            )}

          </StandardCard>

        </CardGrid>

        {!loading && health?.status === "green" && (
          <p className="text-xs flex items-center gap-2 mt-generate-pad">
            <CheckCircle2 className="icon" />
            All systems nominal. Auto-refresh every 30s.
          </p>
        )}

      </div>
    </ViewCanvas>
  );
}

function Kpi({ label, value }: { label: string; value: string }) {
  return (
    <div className="border border-generate-outline/20 rounded-lg p-3">
      <span className="text-xs block mb-1">{label}</span>
      <span className="text-xl font-black text-generate-selected">{value}</span>
    </div>
  );
}

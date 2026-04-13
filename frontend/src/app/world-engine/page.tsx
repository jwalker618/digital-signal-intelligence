// FE: World Engine dashboard landing (WE-1+).
//
// Three sections:
//   - Maturity + stats (WE-1)
//   - Drift alerts open list with acknowledge action (WE-3)
//   - Active relationships table (WE-2)

"use client";

import { useEffect, useState } from "react";
import {
  AlertTriangle,
  CheckCircle2,
  RefreshCw,
  Sparkles,
  TrendingDown,
} from "lucide-react";

import { api, fmtDate, fmtRelative } from "@/lib/api";
import { StatusBadge } from "@/components/shared/StatusBadge";
import type {
  DriftAlert,
  MaturityState,
  RelationshipRow,
  WorldEngineStats,
} from "@/types/worldEngine";

export default function WorldEnginePage() {
  const [maturity, setMaturity] = useState<MaturityState | null>(null);
  const [stats, setStats] = useState<WorldEngineStats | null>(null);
  const [alerts, setAlerts] = useState<DriftAlert[]>([]);
  const [rels, setRels] = useState<RelationshipRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function load() {
    setLoading(true);
    setError(null);
    try {
      const [m, s, a, r] = await Promise.all([
        api
          .get<MaturityState>("/api/v1/world-engine/maturity")
          .catch(() => null),
        api
          .get<WorldEngineStats>("/api/v1/world-engine/stats")
          .catch(() => null),
        api
          .get<{ alerts: DriftAlert[] }>(
            "/api/v1/world-engine/drift-alerts?status=open",
          )
          .catch(() => ({ alerts: [] as DriftAlert[] })),
        api
          .get<{ relationships: RelationshipRow[] }>(
            "/api/v1/world-engine/relationships?limit=50",
          )
          .catch(() => ({ relationships: [] as RelationshipRow[] })),
      ]);
      setMaturity(m);
      setStats(s);
      setAlerts(a.alerts ?? []);
      setRels(r.relationships ?? []);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Load failed");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void load();
  }, []);

  async function acknowledge(alertId: string) {
    setBusy(`ack:${alertId}`);
    setError(null);
    try {
      await api.post(
        `/api/v1/world-engine/drift-alerts/${alertId}/acknowledge`,
      );
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Acknowledge failed");
    } finally {
      setBusy(null);
    }
  }

  return (
    <main className="p-6 flex flex-col gap-4 overflow-y-auto h-full">
      <header className="flex items-center gap-3">
        <h1 className="font-inter text-2xl tracking-wide">World Engine</h1>
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
        <div className="border-2 border-red-500 rounded p-3 text-sm flex items-center gap-2">
          <AlertTriangle className="w-4 h-4 text-red-400" /> {error}
        </div>
      )}

      <section className="grid md:grid-cols-3 gap-4">
        <Card title="Maturity" icon={Sparkles}>
          {maturity ? (
            <>
              <div className="text-2xl font-inter tracking-wide">
                {maturity.stage}
              </div>
              <div className="text-xs opacity-70 mt-1">
                {maturity.assessed_entity_count} entities,{" "}
                {maturity.active_relationships} relationships
              </div>
              <div className="text-xs opacity-60 mt-2">
                coverage {(maturity.coverage_ratio * 100).toFixed(1)}%
              </div>
            </>
          ) : (
            <span className="opacity-60">No data</span>
          )}
        </Card>
        <Card title="Relationships" icon={CheckCircle2}>
          {stats ? (
            <dl className="grid grid-cols-2 text-sm gap-y-1">
              <dt className="opacity-60">Total</dt>
              <dd className="tabular-nums">{stats.total_relationships}</dd>
              <dt className="opacity-60">Active</dt>
              <dd className="tabular-nums">{stats.active_relationships}</dd>
              <dt className="opacity-60">Inactive</dt>
              <dd className="tabular-nums">{stats.inactive_relationships}</dd>
            </dl>
          ) : (
            <span className="opacity-60">No data</span>
          )}
        </Card>
        <Card title="Drift alerts" icon={TrendingDown}>
          {stats ? (
            <div className="text-2xl font-inter tracking-wide">
              {stats.drift_alerts_open}
              <span className="text-sm opacity-60 ml-2">open</span>
            </div>
          ) : (
            <span className="opacity-60">No data</span>
          )}
        </Card>
      </section>

      <section className="border-2 border-dsi-outline rounded">
        <h2 className="font-semibold tracking-wider p-3">Open drift alerts</h2>
        <table className="w-full text-sm">
          <thead>
            <tr className="text-xs uppercase opacity-60 text-left">
              <th className="py-1 px-3">Signal</th>
              <th className="py-1 px-3">Severity</th>
              <th className="py-1 px-3">Type</th>
              <th className="py-1 px-3">Detected</th>
              <th className="py-1 px-3">Summary</th>
              <th className="py-1 px-3"></th>
            </tr>
          </thead>
          <tbody>
            {alerts.map((a) => (
              <tr key={a.id} className="border-t border-dsi-outline/20">
                <td className="py-1 px-3 font-mono text-xs">{a.signal_id}</td>
                <td className="py-1 px-3">
                  <StatusBadge status={a.severity} />
                </td>
                <td className="py-1 px-3 text-xs">{a.drift_type}</td>
                <td className="py-1 px-3 text-xs">
                  {fmtRelative(a.detected_at)}
                </td>
                <td className="py-1 px-3 opacity-80">{a.summary}</td>
                <td className="py-1 px-3">
                  <button
                    onClick={() => void acknowledge(a.id)}
                    disabled={busy === `ack:${a.id}`}
                    className="text-xs text-dsi-selected hover:underline"
                  >
                    Acknowledge
                  </button>
                </td>
              </tr>
            ))}
            {alerts.length === 0 && (
              <tr>
                <td colSpan={6} className="p-4 opacity-60 text-center">
                  No open alerts.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </section>

      <section className="border-2 border-dsi-outline rounded">
        <h2 className="font-semibold tracking-wider p-3">
          Recent relationships
        </h2>
        <table className="w-full text-sm">
          <thead>
            <tr className="text-xs uppercase opacity-60 text-left">
              <th className="py-1 px-3">Source</th>
              <th className="py-1 px-3">→ Target</th>
              <th className="py-1 px-3">Type</th>
              <th className="py-1 px-3 text-right">Strength</th>
              <th className="py-1 px-3 text-right">Conf.</th>
              <th className="py-1 px-3 text-right">Evid.</th>
              <th className="py-1 px-3">Status</th>
              <th className="py-1 px-3">Discovered</th>
            </tr>
          </thead>
          <tbody>
            {rels.map((r) => (
              <tr key={r.id} className="border-t border-dsi-outline/20">
                <td className="py-1 px-3 font-mono text-xs">
                  {r.source_entity}
                </td>
                <td className="py-1 px-3 font-mono text-xs">
                  {r.target_entity}
                </td>
                <td className="py-1 px-3 text-xs">{r.relationship_type}</td>
                <td className="py-1 px-3 text-right tabular-nums">
                  {r.strength.toFixed(2)}
                </td>
                <td className="py-1 px-3 text-right tabular-nums">
                  {(r.confidence * 100).toFixed(0)}%
                </td>
                <td className="py-1 px-3 text-right tabular-nums">
                  {r.evidence_count}
                </td>
                <td className="py-1 px-3">
                  <StatusBadge status={r.status} />
                </td>
                <td className="py-1 px-3 text-xs opacity-70">
                  {fmtDate(r.created_at)}
                </td>
              </tr>
            ))}
            {rels.length === 0 && (
              <tr>
                <td colSpan={8} className="p-4 opacity-60 text-center">
                  No relationships discovered yet.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </section>
    </main>
  );
}

function Card({
  title,
  icon: Icon,
  children,
}: {
  title: string;
  icon: React.ComponentType<{ className?: string }>;
  children: React.ReactNode;
}) {
  return (
    <div className="border-2 border-dsi-outline rounded p-4">
      <h2 className="font-semibold tracking-wider flex items-center gap-2 mb-2">
        <Icon className="w-4 h-4" /> {title}
      </h2>
      {children}
    </div>
  );
}

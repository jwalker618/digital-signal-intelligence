// FE: Config management dashboard (B-2).
//
// Lists available (coverage, config_name) pairs with their active
// deployment + draft count. Each row expands to show version history
// with deploy / validate / calibrate actions.

"use client";

import { useEffect, useState } from "react";
import { AlertTriangle, RefreshCw, ShieldCheck } from "lucide-react";

import { api, fmtDate } from "@/lib/api";
import { StatusBadge } from "@/components/shared/StatusBadge";
import { useAuthStore } from "@/store/authStore";
import type { ConfigVersionRow } from "@/types/admin";

interface ConfigSummary {
  coverage: string;
  config_name: string;
  active_version: number | null;
  draft_count: number;
}

export default function ConfigsPage() {
  const hasPermission = useAuthStore((s) => s.hasPermission);
  const canDeploy = hasPermission("config:deploy");

  const [summaries, setSummaries] = useState<ConfigSummary[]>([]);
  const [selected, setSelected] = useState<
    { coverage: string; config_name: string } | null
  >(null);
  const [history, setHistory] = useState<ConfigVersionRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function loadSummaries() {
    setLoading(true);
    setError(null);
    try {
      const data = await api.get<{ configs: ConfigSummary[] }>(
        "/api/v1/admin/configs",
      );
      setSummaries(data.configs ?? []);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Load failed");
    } finally {
      setLoading(false);
    }
  }

  async function loadHistory(coverage: string, config_name: string) {
    setBusy(`history:${coverage}/${config_name}`);
    try {
      const data = await api.get<{ versions: ConfigVersionRow[] }>(
        `/api/v1/admin/configs/${encodeURIComponent(coverage)}/${encodeURIComponent(config_name)}/history`,
      );
      setHistory(data.versions ?? []);
      setSelected({ coverage, config_name });
    } catch (err) {
      setError(err instanceof Error ? err.message : "History load failed");
    } finally {
      setBusy(null);
    }
  }

  async function action(versionId: string, endpoint: string) {
    setBusy(`${endpoint}:${versionId}`);
    setError(null);
    try {
      await api.post(`/api/v1/admin/configs/versions/${versionId}/${endpoint}`);
      if (selected) await loadHistory(selected.coverage, selected.config_name);
    } catch (err) {
      setError(err instanceof Error ? err.message : `${endpoint} failed`);
    } finally {
      setBusy(null);
    }
  }

  useEffect(() => {
    void loadSummaries();
  }, []);

  return (
    <main className="p-6 flex flex-col gap-4">
      <header className="flex items-center gap-3">
        <h1 className="font-inter text-2xl tracking-wide">Config Management</h1>
        <button
          onClick={() => void loadSummaries()}
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

      <section className="border-2 border-dsi-outline rounded">
        <table className="w-full text-sm">
          <thead>
            <tr className="text-xs uppercase opacity-60 text-left">
              <th className="py-2 px-3">Coverage</th>
              <th className="py-2 px-3">Config</th>
              <th className="py-2 px-3">Active</th>
              <th className="py-2 px-3">Drafts</th>
              <th className="py-2 px-3"></th>
            </tr>
          </thead>
          <tbody>
            {summaries.map((s) => (
              <tr
                key={`${s.coverage}/${s.config_name}`}
                className="border-t border-dsi-outline/20"
              >
                <td className="py-2 px-3 font-mono">{s.coverage}</td>
                <td className="py-2 px-3 font-mono">{s.config_name}</td>
                <td className="py-2 px-3 tabular-nums">
                  {s.active_version ?? "—"}
                </td>
                <td className="py-2 px-3 tabular-nums">{s.draft_count}</td>
                <td className="py-2 px-3">
                  <button
                    onClick={() => void loadHistory(s.coverage, s.config_name)}
                    className="text-dsi-selected hover:underline"
                  >
                    History
                  </button>
                </td>
              </tr>
            ))}
            {summaries.length === 0 && !loading && (
              <tr>
                <td colSpan={5} className="p-4 opacity-60 text-center">
                  No configs yet.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </section>

      {selected && (
        <section className="border-2 border-dsi-outline rounded p-4">
          <h2 className="font-semibold tracking-wider mb-2">
            {selected.coverage} / {selected.config_name} -- version history
          </h2>
          <table className="w-full text-xs">
            <thead>
              <tr className="text-xs uppercase opacity-60 text-left">
                <th className="py-1 pr-2">v</th>
                <th className="py-1 pr-2">Status</th>
                <th className="py-1 pr-2">Author</th>
                <th className="py-1 pr-2">Updated</th>
                <th className="py-1 pr-2">Notes</th>
                <th className="py-1">Actions</th>
              </tr>
            </thead>
            <tbody>
              {history.map((v) => (
                <tr key={v.id} className="border-t border-dsi-outline/20">
                  <td className="py-1 pr-2 font-mono tabular-nums">
                    {v.version}
                  </td>
                  <td className="py-1 pr-2">
                    <StatusBadge status={v.status} />
                  </td>
                  <td className="py-1 pr-2 font-mono text-[10px] opacity-70">
                    {v.author_id ? v.author_id.slice(0, 8) : "—"}
                  </td>
                  <td className="py-1 pr-2">{fmtDate(v.updated_at)}</td>
                  <td className="py-1 pr-2 max-w-xs truncate">
                    {v.notes ?? "—"}
                  </td>
                  <td className="py-1 flex gap-1">
                    <button
                      onClick={() => void action(v.id, "validate")}
                      disabled={busy !== null}
                      className="text-xs border border-dsi-outline/40 rounded px-2 py-0.5 hover:bg-dsi-outline/10"
                    >
                      Validate
                    </button>
                    <button
                      onClick={() => void action(v.id, "calibrate")}
                      disabled={busy !== null}
                      className="text-xs border border-dsi-outline/40 rounded px-2 py-0.5 hover:bg-dsi-outline/10"
                    >
                      Calibrate
                    </button>
                    {canDeploy && v.status === "READY" && (
                      <button
                        onClick={() => void action(v.id, "deploy")}
                        disabled={busy !== null}
                        className="text-xs bg-dsi-selected/20 border border-dsi-selected/40 rounded px-2 py-0.5"
                      >
                        <ShieldCheck className="inline w-3 h-3 mr-1" />
                        Deploy
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>
      )}
    </main>
  );
}

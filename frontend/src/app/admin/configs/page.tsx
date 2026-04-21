// FE: Config management dashboard (B-2).
//
// Lists (coverage, config_name) pairs with their active deployment +
// draft count. Selecting a row loads version history below with
// validate / calibrate / deploy actions.

"use client";

import { useEffect, useState } from "react";
import { AlertTriangle, RefreshCw, ShieldCheck } from "lucide-react";

import ViewCanvas from "@/components/ViewCanvas";
import { api, fmtDate } from "@/lib/api";
import { StatusBadge } from "@/components/shared/StatusBadge";
import { useAuthStore } from "@/store/authStore";
import { useDsiStore } from "@/store/dsiStore";
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
  const setPageQuickAction = useDsiStore((s) => s.setPageQuickAction);

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

  useEffect(() => {
    setPageQuickAction(
      <button
        onClick={() => void loadSummaries()}
        disabled={loading}
        className="dsi-actiontext disabled:opacity-50"
      >
        <RefreshCw className={`icon ${loading ? "animate-spin" : ""}`} />
        Refresh
      </button>,
    );
    return () => setPageQuickAction(null);
  }, [loading, setPageQuickAction]);

  return (
    <ViewCanvas unstyledMain={true}>
      <div className="flex flex-col h-full bg-dsi-background text-dsi-contrast-analysis p-dsi-pad animate-in fade-in duration-500">

        {/* FIXED TOP */}
        <div className="shrink-0 text-dsi-contrast-background pb-4 text-sm flex items-center gap-3">
          <h1>Showing {summaries.length} configs.</h1>
        </div>

        {error && (
          <div className="dsi-notificationpill shrink-0 mb-dsi-pad flex items-center gap-2">
            <AlertTriangle className="icon" /> {error}
          </div>
        )}

        {/* SCROLLABLE TABLE AREA */}
        <div className="flex-1 overflow-y-auto no-scrollbar pb-12">

          <table className="w-full text-left whitespace-nowrap border-collapse">
            <thead className="sticky top-0 z-20 bg-dsi-background">
              <tr className="dsi-grid-table-header text-dsi-contrast-background">
                <th className="p-1.5">Coverage</th>
                <th className="p-1.5">Config</th>
                <th className="p-1.5 text-right">Active</th>
                <th className="p-1.5 text-right">Drafts</th>
                <th className="p-1.5"></th>
              </tr>
            </thead>
            <tbody>
              {summaries.map((s) => (
                <tr
                  key={`${s.coverage}/${s.config_name}`}
                  onClick={() => void loadHistory(s.coverage, s.config_name)}
                  className="cursor-pointer even:bg-dsi-contrast-analysis text-dsi-contrast-background hover:text-dsi-selected"
                >
                  <td className="p-1.5 font-mono">{s.coverage}</td>
                  <td className="p-1.5 font-mono">{s.config_name}</td>
                  <td className="p-1.5 text-right tabular-nums">{s.active_version ?? "—"}</td>
                  <td className="p-1.5 text-right tabular-nums">{s.draft_count}</td>
                  <td className="p-1.5 text-xs text-dsi-selected">History →</td>
                </tr>
              ))}
            </tbody>
          </table>

          {summaries.length === 0 && !loading && (
            <div className="dsi-user-message">No configs yet.</div>
          )}

          {selected && (
            <>
              <div className="mt-dsi-gap text-dsi-contrast-background text-sm pb-2">
                <span className="font-bold">{selected.coverage}</span>
                <span className="opacity-50"> / </span>
                <span className="font-bold">{selected.config_name}</span>
                <span className="opacity-60"> — version history ({history.length})</span>
              </div>

              <table className="w-full text-left whitespace-nowrap border-collapse">
                <thead>
                  <tr className="dsi-grid-table-header text-dsi-contrast-background">
                    <th className="p-1.5">v</th>
                    <th className="p-1.5">Status</th>
                    <th className="p-1.5">Author</th>
                    <th className="p-1.5">Updated</th>
                    <th className="p-1.5">Notes</th>
                    <th className="p-1.5">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {history.map((v) => (
                    <tr key={v.id} className="even:bg-dsi-contrast-analysis text-dsi-contrast-background">
                      <td className="p-1.5 font-mono tabular-nums">{v.version}</td>
                      <td className="p-1.5"><StatusBadge status={v.status} /></td>
                      <td className="p-1.5 font-mono text-[10px] opacity-70">
                        {v.author_id ? v.author_id.slice(0, 8) : "—"}
                      </td>
                      <td className="p-1.5 text-xs">{fmtDate(v.updated_at)}</td>
                      <td className="p-1.5 max-w-xs truncate">{v.notes ?? "—"}</td>
                      <td className="p-1.5 flex gap-1">
                        <button
                          onClick={() => void action(v.id, "validate")}
                          disabled={busy !== null}
                          className="text-xs border border-dsi-outline/40 rounded px-2 py-0.5 hover:bg-dsi-outline/10 disabled:opacity-50"
                        >
                          Validate
                        </button>
                        <button
                          onClick={() => void action(v.id, "calibrate")}
                          disabled={busy !== null}
                          className="text-xs border border-dsi-outline/40 rounded px-2 py-0.5 hover:bg-dsi-outline/10 disabled:opacity-50"
                        >
                          Calibrate
                        </button>
                        {canDeploy && v.status === "READY" && (
                          <button
                            onClick={() => void action(v.id, "deploy")}
                            disabled={busy !== null}
                            className="text-xs bg-dsi-selected/20 border border-dsi-selected/40 rounded px-2 py-0.5 disabled:opacity-50"
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

              {history.length === 0 && (
                <div className="dsi-user-message">No versions.</div>
              )}
            </>
          )}
        </div>
      </div>
    </ViewCanvas>
  );
}

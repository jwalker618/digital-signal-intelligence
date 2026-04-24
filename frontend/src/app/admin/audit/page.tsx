// FE: Audit log viewer (B-4).
//
// Filter by action_type / resource_type / date range. Cursor paginated.
// Clicking a row expands a before/after state diff via StateDiffViewer.

"use client";

import { Fragment, useEffect, useState } from "react";
import { AlertTriangle, Download } from "lucide-react";

import ViewCanvas from "@/components/ViewCanvas";
import { api, fmtDate } from "@/lib/api";
import { formatNumber } from "@/lib/format";
import { StateDiffViewer } from "@/components/shared/StateDiffViewer";
import { useDsiStore } from "@/store/dsiStore";
import type { AuditEventRow } from "@/types/admin";

interface QueryState {
  action_type: string;
  resource_type: string;
  date_from: string;
  date_to: string;
}

const EMPTY: QueryState = {
  action_type: "",
  resource_type: "",
  date_from: "",
  date_to: "",
};

export default function AuditPage() {
  const setPageQuickAction = useDsiStore((s) => s.setPageQuickAction);

  const [query, setQuery] = useState<QueryState>(EMPTY);
  const [events, setEvents] = useState<AuditEventRow[]>([]);
  const [cursor, setCursor] = useState<string | null>(null);
  const [nextCursor, setNextCursor] = useState<string | null>(null);
  const [expanded, setExpanded] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function load(reset = true) {
    setLoading(true);
    setError(null);
    try {
      const params = new URLSearchParams();
      if (query.action_type) params.set("action_type", query.action_type);
      if (query.resource_type) params.set("resource_type", query.resource_type);
      if (query.date_from) params.set("date_from", query.date_from);
      if (query.date_to) params.set("date_to", query.date_to);
      if (!reset && cursor) params.set("cursor", cursor);
      params.set("limit", "50");
      const data = await api.get<{
        events: AuditEventRow[];
        next_cursor: string | null;
      }>(`/api/v1/admin/audit?${params.toString()}`);
      setEvents(reset ? data.events : [...events, ...data.events]);
      setNextCursor(data.next_cursor ?? null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Load failed");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void load(true);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  function applyFilters() {
    setCursor(null);
    void load(true);
  }

  function loadMore() {
    if (!nextCursor) return;
    setCursor(nextCursor);
    void load(false);
  }

  function exportCsv() {
    const params = new URLSearchParams();
    if (query.action_type) params.set("action_type", query.action_type);
    if (query.resource_type) params.set("resource_type", query.resource_type);
    if (query.date_from) params.set("date_from", query.date_from);
    if (query.date_to) params.set("date_to", query.date_to);
    params.set("format", "csv");
    window.open(`/api/v1/admin/audit/export?${params.toString()}`, "_blank");
  }

  useEffect(() => {
    setPageQuickAction(
      <button onClick={exportCsv} className="generate-actiontext">
        <Download className="icon" /> Export CSV
      </button>,
    );
    return () => setPageQuickAction(null);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [query]);

  return (
    <ViewCanvas unstyledMain={true}>
      <div className="flex flex-col h-full bg-generate-background text-generate-contrast-analysis p-generate-pad animate-in fade-in duration-500">

        {/* FIXED TOP */}
        <div className="shrink-0 text-generate-contrast-background pb-4 text-sm">
          <div className="flex items-center gap-3 pb-2">
            <h1>Showing {events.length} events.</h1>
          </div>

          <div className="flex flex-wrap items-end gap-2">
            <label className="flex flex-col gap-0.5">
              <span className="text-xs opacity-60">Action</span>
              <input
                value={query.action_type}
                onChange={(e) => setQuery({ ...query, action_type: e.target.value })}
                placeholder="CONFIG_DEPLOY"
                className="generate-inputbox w-40 font-mono"
              />
            </label>
            <label className="flex flex-col gap-0.5">
              <span className="text-xs opacity-60">Resource</span>
              <input
                value={query.resource_type}
                onChange={(e) => setQuery({ ...query, resource_type: e.target.value })}
                placeholder="config_version"
                className="generate-inputbox w-40 font-mono"
              />
            </label>
            <label className="flex flex-col gap-0.5">
              <span className="text-xs opacity-60">From</span>
              <input
                type="date"
                value={query.date_from}
                onChange={(e) => setQuery({ ...query, date_from: e.target.value })}
                className="generate-inputbox"
              />
            </label>
            <label className="flex flex-col gap-0.5">
              <span className="text-xs opacity-60">To</span>
              <input
                type="date"
                value={query.date_to}
                onChange={(e) => setQuery({ ...query, date_to: e.target.value })}
                className="generate-inputbox"
              />
            </label>
            <button
              onClick={applyFilters}
              disabled={loading}
              className="generate-actionbutton"
            >
              Apply
            </button>
            <button
              onClick={() => { setQuery(EMPTY); setCursor(null); }}
              className="generate-actiontext"
            >
              Reset
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
                <th className="p-1.5">When</th>
                <th className="p-1.5">Action</th>
                <th className="p-1.5">Resource</th>
                <th className="p-1.5">User</th>
                <th className="p-1.5 text-right">Latency</th>
              </tr>
            </thead>
            <tbody>
              {events.map((e) => {
                const open = expanded === e.id;
                return (
                  <Fragment key={e.id}>
                    <tr
                      onClick={() => setExpanded(open ? null : e.id)}
                      className="cursor-pointer even:bg-generate-contrast-analysis text-generate-contrast-background hover:text-generate-selected"
                    >
                      <td className="p-1.5 text-xs whitespace-nowrap">
                        {fmtDate(e.created_at)}
                      </td>
                      <td className="p-1.5 font-mono text-xs">{e.action_type}</td>
                      <td className="p-1.5 text-xs">
                        {e.resource_type}
                        {e.resource_id && (
                          <span className="opacity-60"> · {e.resource_id}</span>
                        )}
                      </td>
                      <td className="p-1.5 font-mono text-[10px] opacity-70">
                        {e.user_id ? e.user_id.slice(0, 8) : "—"}
                      </td>
                      <td className="p-1.5 text-right tabular-nums text-xs">
                        {e.duration_ms ? `${formatNumber(e.duration_ms)} ms` : "—"}
                      </td>
                    </tr>
                    {open && (
                      <tr className="bg-generate-analysis/40">
                        <td colSpan={5} className="p-3">
                          <StateDiffViewer
                            before={e.before_state}
                            after={e.after_state}
                          />
                        </td>
                      </tr>
                    )}
                  </Fragment>
                );
              })}
            </tbody>
          </table>

          {events.length === 0 && !loading && (
            <div className="generate-user-message">No events match these filters.</div>
          )}

          {nextCursor && (
            <div className="pt-generate-pad text-center">
              <button
                onClick={loadMore}
                disabled={loading}
                className="generate-actionbutton inline-block disabled:opacity-50"
              >
                Load more
              </button>
            </div>
          )}
        </div>
      </div>
    </ViewCanvas>
  );
}

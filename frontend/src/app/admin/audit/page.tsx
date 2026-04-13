// FE: Audit log viewer (B-4).
//
// Filter by action_type / resource_type / date range. Cursor paginated.
// Clicking a row expands a before/after state diff via StateDiffViewer.

"use client";

import { useEffect, useState } from "react";
import { AlertTriangle, Download, Filter } from "lucide-react";

import { api, fmtDate } from "@/lib/api";
import { StateDiffViewer } from "@/components/shared/StateDiffViewer";
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
    const url = `/api/v1/admin/audit/export?${params.toString()}`;
    window.open(url, "_blank");
  }

  return (
    <main className="p-6 flex flex-col gap-4">
      <header className="flex items-center gap-3">
        <h1 className="font-inter text-2xl tracking-wide">Audit Log</h1>
        <button
          onClick={exportCsv}
          className="ml-auto flex items-center gap-1 border-2 border-dsi-outline py-1 px-3 rounded text-sm"
        >
          <Download className="w-4 h-4" />
          Export CSV
        </button>
      </header>

      <section className="border-2 border-dsi-outline rounded p-3 flex flex-wrap items-end gap-2">
        <Filter className="w-4 h-4 opacity-60" />
        <Field label="Action">
          <input
            value={query.action_type}
            onChange={(e) => setQuery({ ...query, action_type: e.target.value })}
            placeholder="CONFIG_DEPLOY"
            className="border-2 border-dsi-outline bg-dsi-background px-2 py-1 rounded text-sm font-mono w-40"
          />
        </Field>
        <Field label="Resource">
          <input
            value={query.resource_type}
            onChange={(e) =>
              setQuery({ ...query, resource_type: e.target.value })
            }
            placeholder="config_version"
            className="border-2 border-dsi-outline bg-dsi-background px-2 py-1 rounded text-sm font-mono w-40"
          />
        </Field>
        <Field label="From">
          <input
            type="date"
            value={query.date_from}
            onChange={(e) => setQuery({ ...query, date_from: e.target.value })}
            className="border-2 border-dsi-outline bg-dsi-background px-2 py-1 rounded text-sm"
          />
        </Field>
        <Field label="To">
          <input
            type="date"
            value={query.date_to}
            onChange={(e) => setQuery({ ...query, date_to: e.target.value })}
            className="border-2 border-dsi-outline bg-dsi-background px-2 py-1 rounded text-sm"
          />
        </Field>
        <button
          onClick={applyFilters}
          disabled={loading}
          className="bg-dsi-contrast-background text-dsi-background py-1 px-3 rounded text-sm font-semibold"
        >
          Apply
        </button>
        <button
          onClick={() => {
            setQuery(EMPTY);
            setCursor(null);
          }}
          className="border-2 border-dsi-outline py-1 px-3 rounded text-sm"
        >
          Reset
        </button>
      </section>

      {error && (
        <div className="border-2 border-red-500 rounded p-3 text-sm flex items-center gap-2">
          <AlertTriangle className="w-4 h-4 text-red-400" /> {error}
        </div>
      )}

      <section className="border-2 border-dsi-outline rounded">
        <table className="w-full text-sm">
          <thead>
            <tr className="text-xs uppercase opacity-60 text-left">
              <th className="py-1 px-3">When</th>
              <th className="py-1 px-3">Action</th>
              <th className="py-1 px-3">Resource</th>
              <th className="py-1 px-3">User</th>
              <th className="py-1 px-3">Latency</th>
            </tr>
          </thead>
          <tbody>
            {events.map((e) => {
              const open = expanded === e.id;
              return (
                <>
                  <tr
                    key={e.id}
                    className="border-t border-dsi-outline/20 hover:bg-dsi-outline/5 cursor-pointer"
                    onClick={() => setExpanded(open ? null : e.id)}
                  >
                    <td className="py-1 px-3 text-xs whitespace-nowrap">
                      {fmtDate(e.created_at)}
                    </td>
                    <td className="py-1 px-3 font-mono text-xs">
                      {e.action_type}
                    </td>
                    <td className="py-1 px-3 text-xs">
                      {e.resource_type}
                      {e.resource_id && (
                        <span className="opacity-60"> · {e.resource_id}</span>
                      )}
                    </td>
                    <td className="py-1 px-3 font-mono text-[10px] opacity-70">
                      {e.user_id ? e.user_id.slice(0, 8) : "—"}
                    </td>
                    <td className="py-1 px-3 tabular-nums text-xs">
                      {e.duration_ms ? `${e.duration_ms.toFixed(0)} ms` : "—"}
                    </td>
                  </tr>
                  {open && (
                    <tr className="border-t border-dsi-outline/20 bg-dsi-outline/5">
                      <td colSpan={5} className="p-3">
                        <StateDiffViewer
                          before={e.before_state}
                          after={e.after_state}
                        />
                      </td>
                    </tr>
                  )}
                </>
              );
            })}
            {events.length === 0 && !loading && (
              <tr>
                <td colSpan={5} className="p-4 opacity-60 text-center">
                  No events match these filters.
                </td>
              </tr>
            )}
          </tbody>
        </table>
        {nextCursor && (
          <div className="p-2 text-center">
            <button
              onClick={loadMore}
              disabled={loading}
              className="border-2 border-dsi-outline py-1 px-4 rounded text-sm"
            >
              Load more
            </button>
          </div>
        )}
      </section>
    </main>
  );
}

function Field({
  label,
  children,
}: {
  label: string;
  children: React.ReactNode;
}) {
  return (
    <label className="flex flex-col gap-0.5">
      <span className="text-xs opacity-60">{label}</span>
      {children}
    </label>
  );
}

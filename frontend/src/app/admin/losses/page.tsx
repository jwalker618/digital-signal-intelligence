// FE: Loss Register (C-1).
//
// Lists loss events with inline filters, CSV bulk import, and a
// "link all" action that re-runs retrospective attachment against
// submissions.

"use client";

import { FormEvent, useEffect, useState } from "react";
import { AlertTriangle, Link2, Upload } from "lucide-react";

import ViewCanvas from "@/components/ViewCanvas";
import { api, fmtDate } from "@/lib/api";
import { formatCurrency } from "@/lib/format";
import { StatusBadge } from "@/components/shared/StatusBadge";
import { useAuthStore } from "@/store/authStore";
import { useDsiStore } from "@/store/dsiStore";
import type { LossEvent } from "@/types/recalibration";

interface Filters {
  coverage: string;
  status: string;
  linked: "" | "true" | "false";
}

const EMPTY: Filters = { coverage: "", status: "", linked: "" };

export default function LossesPage() {
  const setPageQuickAction = useDsiStore((s) => s.setPageQuickAction);

  const [items, setItems] = useState<LossEvent[]>([]);
  const [filters, setFilters] = useState<Filters>(EMPTY);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState<string | null>(null);
  const [importResult, setImportResult] = useState<string | null>(null);

  async function load() {
    setLoading(true);
    setError(null);
    try {
      const params = new URLSearchParams();
      if (filters.coverage) params.set("coverage", filters.coverage);
      if (filters.status) params.set("status", filters.status);
      if (filters.linked) params.set("linked", filters.linked);
      params.set("limit", "100");
      const data = await api.get<{ losses: LossEvent[] }>(
        `/api/v1/losses?${params.toString()}`,
      );
      setItems(data.losses ?? []);
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

  async function uploadCsv(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const form = new FormData(e.currentTarget);
    const file = form.get("file") as File | null;
    if (!file) return;
    setBusy("import");
    setImportResult(null);
    setError(null);
    try {
      const fd = new FormData();
      fd.append("file", file);
      const res = await fetch("/api/v1/losses/import", {
        method: "POST",
        body: fd,
        headers: { Authorization: `Bearer ${getAccessToken()}` },
      });
      const text = await res.text();
      const parsed = text ? JSON.parse(text) : null;
      if (!res.ok) {
        throw new Error(
          (parsed && (parsed.error || parsed.detail)) || `HTTP ${res.status}`,
        );
      }
      setImportResult(
        `Imported ${parsed.imported ?? 0}, skipped ${parsed.skipped ?? 0}, errors ${parsed.errors?.length ?? 0}`,
      );
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Import failed");
    } finally {
      setBusy(null);
    }
  }

  async function linkAll() {
    setBusy("link");
    setError(null);
    try {
      const resp = await api.post<{
        newly_linked: number;
        already_linked: number;
      }>("/api/v1/losses/link-all");
      setImportResult(
        `Linked ${resp.newly_linked} new, ${resp.already_linked} already linked`,
      );
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Link failed");
    } finally {
      setBusy(null);
    }
  }

  useEffect(() => {
    setPageQuickAction(
      <button
        onClick={() => void linkAll()}
        disabled={busy !== null}
        className="generate-actiontext disabled:opacity-50"
      >
        <Link2 className="icon" /> Link all
      </button>,
    );
    return () => setPageQuickAction(null);
  }, [busy, setPageQuickAction]);

  return (
    <ViewCanvas unstyledMain={true}>
      <div className="flex flex-col h-full bg-generate-background text-generate-contrast-analysis p-generate-pad animate-in fade-in duration-500">

        {/* FIXED TOP */}
        <div className="shrink-0 text-generate-contrast-background pb-4 text-sm">
          <div className="flex items-center gap-3 pb-2">
            <h1>Showing {items.length} loss events.</h1>
            {importResult && (
              <span className="text-xs opacity-80 ml-auto">{importResult}</span>
            )}
          </div>

          <form
            onSubmit={uploadCsv}
            encType="multipart/form-data"
            className="flex items-center gap-2 pb-2"
          >
            <Upload className="icon opacity-60" />
            <input
              type="file"
              name="file"
              accept=".csv,text/csv"
              required
              className="text-xs"
            />
            <button
              type="submit"
              disabled={busy === "import"}
              className="generate-actionbutton disabled:opacity-50"
            >
              {busy === "import" ? "Importing…" : "Import CSV"}
            </button>
          </form>

          <div className="flex flex-wrap items-end gap-2">
            <label className="flex flex-col gap-0.5">
              <span className="text-xs opacity-60">Coverage</span>
              <input
                value={filters.coverage}
                onChange={(e) => setFilters({ ...filters, coverage: e.target.value })}
                className="generate-inputbox w-24 font-mono"
              />
            </label>
            <label className="flex flex-col gap-0.5">
              <span className="text-xs opacity-60">Status</span>
              <input
                value={filters.status}
                onChange={(e) => setFilters({ ...filters, status: e.target.value })}
                className="generate-inputbox w-32"
              />
            </label>
            <label className="flex flex-col gap-0.5">
              <span className="text-xs opacity-60">Linked</span>
              <select
                value={filters.linked}
                onChange={(e) =>
                  setFilters({ ...filters, linked: e.target.value as Filters["linked"] })
                }
                className="generate-inputbox"
              >
                <option value="">Any</option>
                <option value="true">Linked</option>
                <option value="false">Unlinked</option>
              </select>
            </label>
            <button
              onClick={() => void load()}
              disabled={loading}
              className="generate-actionbutton"
            >
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
                <th className="p-1.5">Entity</th>
                <th className="p-1.5">Coverage</th>
                <th className="p-1.5">Event date</th>
                <th className="p-1.5 text-right">Gross</th>
                <th className="p-1.5 text-right">Net</th>
                <th className="p-1.5">Status</th>
                <th className="p-1.5">Linked</th>
              </tr>
            </thead>
            <tbody>
              {items.map((l) => (
                <tr key={l.id} className="even:bg-generate-contrast-analysis text-generate-contrast-background">
                  <td className="p-1.5">{l.entity_name}</td>
                  <td className="p-1.5 font-mono text-xs">{l.coverage}</td>
                  <td className="p-1.5 text-xs">{fmtDate(l.event_date)}</td>
                  <td className="p-1.5 text-right tabular-nums">{formatCurrency(l.gross_amount)}</td>
                  <td className="p-1.5 text-right tabular-nums opacity-80">
                    {l.net_amount != null ? formatCurrency(l.net_amount) : "—"}
                  </td>
                  <td className="p-1.5"><StatusBadge status={l.status} /></td>
                  <td className="p-1.5 text-xs">{l.quote_id ? "yes" : "no"}</td>
                </tr>
              ))}
            </tbody>
          </table>

          {items.length === 0 && !loading && (
            <div className="generate-user-message">No loss events.</div>
          )}
        </div>
      </div>
    </ViewCanvas>
  );
}

// Multipart uploads can't use api.ts (which JSON-serialises the body),
// so we reach for the live access token directly.
function getAccessToken(): string {
  if (typeof window === "undefined") return "";
  return useAuthStore.getState().accessToken ?? "";
}

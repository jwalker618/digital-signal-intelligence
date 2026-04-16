// FE: Loss Register (C-1).
//
// Lists loss events with inline filters, plus a CSV import form
// (file-drag-enabled) and a "link all" action to re-run retrospective
// attachment against submissions.

"use client";

import { FormEvent, useEffect, useState } from "react";
import { AlertTriangle, Link2, Upload } from "lucide-react";

import { api, fmtDate } from "@/lib/api";
import { formatCurrency } from "@/lib/format";
import { StatusBadge } from "@/components/shared/StatusBadge";
import { useAuthStore } from "@/store/authStore";
import type { LossEvent } from "@/types/recalibration";

interface Filters {
  coverage: string;
  status: string;
  linked: "" | "true" | "false";
}

const EMPTY: Filters = { coverage: "", status: "", linked: "" };

export default function LossesPage() {
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
        headers: {
          Authorization: `Bearer ${getAccessToken()}`,
        },
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

  return (
    <main className="p-6 flex flex-col gap-4">
      <header className="flex items-center gap-3">
        <h1 className="font-inter text-2xl tracking-wide">Loss Register</h1>
        <button
          onClick={() => void linkAll()}
          disabled={busy !== null}
          className="ml-auto flex items-center gap-1 border-2 border-dsi-outline py-1 px-3 rounded text-sm"
        >
          <Link2 className="w-4 h-4" /> Link all
        </button>
      </header>

      {error && (
        <div className="border-2 border-dsi-negative rounded p-3 text-sm flex items-center gap-2">
          <AlertTriangle className="w-4 h-4 text-dsi-negative" /> {error}
        </div>
      )}

      <section className="border-2 border-dsi-outline rounded p-3">
        <h2 className="font-semibold tracking-wider mb-2 flex items-center gap-2">
          <Upload className="w-4 h-4" /> Bulk import CSV
        </h2>
        <form
          onSubmit={uploadCsv}
          className="flex items-center gap-2 text-sm"
          encType="multipart/form-data"
        >
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
            className="bg-dsi-contrast-background text-dsi-background py-1 px-3 rounded text-sm font-semibold disabled:opacity-50"
          >
            {busy === "import" ? "Importing…" : "Import"}
          </button>
          {importResult && (
            <span className="text-xs opacity-80">{importResult}</span>
          )}
        </form>
      </section>

      <section className="border-2 border-dsi-outline rounded p-3 flex flex-wrap items-end gap-2">
        <Field label="Coverage">
          <input
            value={filters.coverage}
            onChange={(e) => setFilters({ ...filters, coverage: e.target.value })}
            className="border-2 border-dsi-outline bg-dsi-background px-2 py-1 rounded text-sm font-mono w-24"
          />
        </Field>
        <Field label="Status">
          <input
            value={filters.status}
            onChange={(e) => setFilters({ ...filters, status: e.target.value })}
            className="border-2 border-dsi-outline bg-dsi-background px-2 py-1 rounded text-sm w-32"
          />
        </Field>
        <Field label="Linked">
          <select
            value={filters.linked}
            onChange={(e) =>
              setFilters({ ...filters, linked: e.target.value as Filters["linked"] })
            }
            className="border-2 border-dsi-outline bg-dsi-background px-2 py-1 rounded text-sm"
          >
            <option value="">Any</option>
            <option value="true">Linked</option>
            <option value="false">Unlinked</option>
          </select>
        </Field>
        <button
          onClick={() => void load()}
          disabled={loading}
          className="bg-dsi-contrast-background text-dsi-background py-1 px-3 rounded text-sm font-semibold"
        >
          Apply
        </button>
      </section>

      <section className="border-2 border-dsi-outline rounded">
        <table className="w-full text-sm">
          <thead>
            <tr className="text-xs uppercase opacity-60 text-left">
              <th className="py-1 px-3">Entity</th>
              <th className="py-1 px-3">Coverage</th>
              <th className="py-1 px-3">Event date</th>
              <th className="py-1 px-3 text-right">Gross</th>
              <th className="py-1 px-3 text-right">Net</th>
              <th className="py-1 px-3">Status</th>
              <th className="py-1 px-3">Linked</th>
            </tr>
          </thead>
          <tbody>
            {items.map((l) => (
              <tr key={l.id} className="border-t border-dsi-outline/20">
                <td className="py-1 px-3">{l.entity_name}</td>
                <td className="py-1 px-3 font-mono text-xs">{l.coverage}</td>
                <td className="py-1 px-3 text-xs">{fmtDate(l.event_date)}</td>
                <td className="py-1 px-3 text-right tabular-nums">
                  {formatCurrency(l.gross_amount)}
                </td>
                <td className="py-1 px-3 text-right tabular-nums opacity-80">
                  {l.net_amount != null ? formatCurrency(l.net_amount) : "—"}
                </td>
                <td className="py-1 px-3">
                  <StatusBadge status={l.status} />
                </td>
                <td className="py-1 px-3 text-xs">
                  {l.quote_id ? "yes" : "no"}
                </td>
              </tr>
            ))}
            {items.length === 0 && !loading && (
              <tr>
                <td colSpan={7} className="p-4 opacity-60 text-center">
                  No loss events.
                </td>
              </tr>
            )}
          </tbody>
        </table>
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

// Multipart uploads can't use api.ts (which JSON-serialises the body),
// so we reach for the live access token directly.
function getAccessToken(): string {
  if (typeof window === "undefined") return "";
  return useAuthStore.getState().accessToken ?? "";
}

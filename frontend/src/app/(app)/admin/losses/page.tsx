"use client";

import { ChangeEvent, useEffect, useMemo, useState } from "react";
import {
  FileX,
  Link2,
  Loader2,
  Search,
  Upload,
} from "lucide-react";
import { Topbar } from "@/components/chrome/topbar";
import { Card } from "@/components/ui/card";
import { Chip } from "@/components/ui/chip";
import { Button } from "@/components/ui/button";
import { Eyebrow, NumDisplay, Body, Micro } from "@/components/ui/typography";
import { PageError, PageLoading } from "@/components/base/pageStates";
import { PermissionGate } from "@/components/shared/PermissionGate";
import { authorizedFetch } from "@/lib/authApi";
import { api } from "@/lib/api";
import { useAuthStore } from "@/store/authStore";
import { formatCurrency, formatDate, formatText } from "@/lib/format";
import type { LossEvent } from "@/types/recalibration";

export default function AdminLossesPage() {
  return (
    <PermissionGate
      permission="assessment:write"
      fallback={
        <PageError message="You don't have assessment:write permission." />
      }
    >
      <LossesInner />
    </PermissionGate>
  );
}

function LossesInner() {
  const accessToken = useAuthStore((s) => s.accessToken);
  const [data, setData] = useState<LossEvent[] | null>(null);
  const [state, setState] = useState<"loading" | "ok" | "error">("loading");
  const [err, setErr] = useState<string | null>(null);
  const [query, setQuery] = useState("");
  const [importing, setImporting] = useState(false);
  const [linking, setLinking] = useState(false);
  const [toast, setToast] = useState<string | null>(null);

  async function load() {
    setState("loading");
    try {
      const params = new URLSearchParams();
      params.set("limit", "200");
      const r = await api.get<{ events: LossEvent[] }>(
        `/api/v1/losses?${params.toString()}`,
      );
      setData(r.events ?? []);
      setState("ok");
    } catch (e) {
      setErr(e instanceof Error ? e.message : String(e));
      setState("error");
    }
  }

  useEffect(() => {
    void load();
  }, []);

  async function onImport(e: ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    setImporting(true);
    setToast(null);
    try {
      const formData = new FormData();
      formData.append("file", file);
      const res = await authorizedFetch(accessToken, "/api/v1/losses/import", {
        method: "POST",
        body: formData,
      });
      if (!res.ok) throw new Error(`Import failed (${res.status})`);
      const body = (await res.json()) as { imported?: number };
      setToast(`Imported ${body.imported ?? 0} losses.`);
      await load();
    } catch (err) {
      setToast(err instanceof Error ? err.message : String(err));
    } finally {
      setImporting(false);
      e.target.value = "";
    }
  }

  async function onLinkAll() {
    setLinking(true);
    setToast(null);
    try {
      const r = await api.post<{ linked?: number }>("/api/v1/losses/link-all");
      setToast(`Linked ${r.linked ?? 0} losses to submissions.`);
      await load();
    } catch (err) {
      setToast(err instanceof Error ? err.message : String(err));
    } finally {
      setLinking(false);
    }
  }

  const filtered = useMemo(() => {
    if (!data) return [] as LossEvent[];
    if (!query) return data;
    const q = query.toLowerCase();
    return data.filter(
      (l) =>
        l.entity_name.toLowerCase().includes(q) ||
        l.coverage.toLowerCase().includes(q) ||
        (l.cause_code ?? "").toLowerCase().includes(q) ||
        l.id.toLowerCase().includes(q),
    );
  }, [data, query]);

  const linked = data?.filter((l) => l.quote_id || l.assessment_id).length ?? 0;
  const total = data?.length ?? 0;
  const grossSum = data?.reduce((s, l) => s + l.gross_amount, 0) ?? 0;

  return (
    <>
      <Topbar crumbs={["Admin", "Loss Register"]} />
      <div className="flex-1 overflow-y-auto px-9 py-7">
        <div className="mx-auto grid max-w-[1400px] gap-6">
          <header className="flex items-end justify-between gap-6">
            <div>
              <Eyebrow>Records</Eyebrow>
              <h1 className="mt-1 font-display text-[32px] font-semibold leading-none tracking-tight text-ink">
                Loss Register
              </h1>
              <Body className="mt-2">
                Reported losses across the book. Import from a CSV file or
                trigger linking to existing assessments.
              </Body>
            </div>
            <div className="flex items-center gap-2">
              <label className="cursor-pointer">
                <input
                  type="file"
                  accept=".csv,.tsv,.json"
                  onChange={onImport}
                  className="hidden"
                  disabled={importing}
                />
                <span
                  className={`inline-flex h-10 items-center gap-2 rounded-btn border border-rule-strong bg-surface px-4 text-[13px] font-semibold text-ink transition hover:bg-surface-sunken ${
                    importing ? "opacity-60" : ""
                  }`}
                >
                  {importing ? (
                    <Loader2 size={14} className="animate-spin" />
                  ) : (
                    <Upload size={14} />
                  )}
                  Import CSV
                </span>
              </label>
              <Button
                variant="primary"
                onClick={onLinkAll}
                disabled={linking}
              >
                {linking ? (
                  <Loader2 size={14} className="animate-spin" />
                ) : (
                  <Link2 size={14} />
                )}
                Link to assessments
              </Button>
            </div>
          </header>

          {toast && (
            <Card pad="md" variant="info">
              <Body className="text-[13.5px] text-ink">{toast}</Body>
            </Card>
          )}

          <div className="grid gap-4 sm:grid-cols-3">
            <Stat label="Total events">{total}</Stat>
            <Stat label="Linked to assessments" tone="pos">
              {linked} / {total}
            </Stat>
            <Stat label="Gross losses" emphasis>
              {formatCurrency(grossSum)}
            </Stat>
          </div>

          <Card pad="md" className="flex items-center gap-3">
            <Search size={15} className="text-ink-mute" />
            <input
              type="search"
              placeholder="Entity, coverage, cause code, or id…"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              className="h-9 flex-1 border-0 bg-transparent text-[13.5px] text-ink placeholder:text-ink-mute focus:outline-none"
            />
            <Micro>{filtered.length} shown</Micro>
          </Card>

          {state === "loading" && <PageLoading message="Loading losses…" />}
          {state === "error" && <PageError message={err ?? "Unknown error"} />}
          {state === "ok" && (
            <Card pad="md" className="overflow-hidden p-0">
              <table className="w-full table-fixed text-[13px]">
                <thead>
                  <tr className="border-b border-rule bg-surface-sunken text-left">
                    <ColHead width="w-[22%]">Entity</ColHead>
                    <ColHead width="w-[14%]">Coverage</ColHead>
                    <ColHead width="w-[12%]">Date</ColHead>
                    <ColHead width="w-[14%]">Gross</ColHead>
                    <ColHead width="w-[12%]">Net</ColHead>
                    <ColHead width="w-[12%]">Cause</ColHead>
                    <ColHead width="w-[14%]">Status</ColHead>
                  </tr>
                </thead>
                <tbody>
                  {filtered.map((l) => (
                    <tr
                      key={l.id}
                      className="border-b border-rule last:border-0 hover:bg-surface-sunken/40"
                    >
                      <td className="px-5 py-2.5">
                        <div className="flex items-center gap-2">
                          <FileX size={13} className="text-ink-mute" />
                          <span className="font-medium text-ink">
                            {l.entity_name}
                          </span>
                        </div>
                        <Micro className="mt-0.5 block font-mono">{l.id}</Micro>
                      </td>
                      <td className="px-5 py-2.5 text-ink">{l.coverage}</td>
                      <td className="px-5 py-2.5 text-ink-soft">
                        {formatDate(l.event_date)}
                      </td>
                      <td className="px-5 py-2.5 font-semibold tabular-nums text-ink">
                        {formatCurrency(l.gross_amount)}
                      </td>
                      <td className="px-5 py-2.5 tabular-nums text-ink-soft">
                        {l.net_amount != null
                          ? formatCurrency(l.net_amount)
                          : "—"}
                      </td>
                      <td className="px-5 py-2.5 text-ink-soft">
                        {l.cause_code ? (
                          <span className="font-mono text-[12.5px]">
                            {l.cause_code}
                          </span>
                        ) : (
                          "—"
                        )}
                      </td>
                      <td className="px-5 py-2.5">
                        <Chip
                          variant={
                            /closed|paid/i.test(l.status)
                              ? "pos"
                              : /open|reserve/i.test(l.status)
                                ? "warn"
                                : "mute"
                          }
                          size="sm"
                        >
                          {formatText(l.status, "capitalize")}
                        </Chip>
                        {(l.quote_id || l.assessment_id) && (
                          <Chip variant="info" size="sm" className="ml-1">
                            Linked
                          </Chip>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
              {filtered.length === 0 && (
                <div className="px-5 py-8 text-center">
                  <Body className="italic">No losses match "{query}".</Body>
                </div>
              )}
            </Card>
          )}
        </div>
      </div>
    </>
  );
}

function Stat({
  label,
  tone,
  emphasis,
  children,
}: {
  label: string;
  tone?: "pos" | "info";
  emphasis?: boolean;
  children: React.ReactNode;
}) {
  return (
    <Card pad="md" variant={emphasis ? "info" : "default"}>
      <Micro
        className={
          tone === "pos"
            ? "text-pos"
            : emphasis
              ? "text-info-deep dark:text-info"
              : ""
        }
      >
        {label}
      </Micro>
      <div className="mt-2">
        <NumDisplay size={emphasis ? "lg" : "md"}>{children}</NumDisplay>
      </div>
    </Card>
  );
}

function ColHead({
  width,
  children,
}: {
  width: string;
  children: React.ReactNode;
}) {
  return (
    <th
      className={`px-5 py-2.5 text-[11px] font-semibold uppercase tracking-[0.08em] text-ink-mute ${width}`}
    >
      {children}
    </th>
  );
}

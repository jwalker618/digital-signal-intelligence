// No direct design counterpart; adapted from reim_admin_b.jsx
"use client";

import { ChangeEvent, useEffect, useMemo, useState } from "react";
import {
  Check,
  Link2,
  Loader2,
  Search,
  UploadCloud,
} from "lucide-react";
import { Topbar } from "@/components/chrome/topbar";
import {
  AdminTable,
  Body,
  Button,
  Card,
  Chip,
  Eyebrow,
  Micro,
  MiniKpi,
} from "@/components/ui";
import type { AdminTableCol, AdminTableRow } from "@/components/ui";
import { PageError, PageLoading } from "@/components/base/pageStates";
import { PermissionGate } from "@/components/shared/PermissionGate";
import { authorizedFetch } from "@/lib/authApi";
import { api } from "@/lib/api";
import { useAuthStore } from "@/store/authStore";
import { formatCurrency, formatDate, formatText } from "@/lib/format";
import { cn } from "@/lib/utils";
import type { LossEvent } from "@/types/recalibration";

type LossFilter = "all" | "unlinked" | "open";

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
  const [filter, setFilter] = useState<LossFilter>("all");
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

  const all = data ?? [];
  const linkedFlag = (l: LossEvent): boolean =>
    Boolean(l.quote_id || l.assessment_id);
  const isOpen = (l: LossEvent): boolean => /open|reserve/i.test(l.status);
  const unlinkedCount = all.filter((l) => !linkedFlag(l)).length;
  const openCount = all.filter(isOpen).length;
  const grossSum = all.reduce((s, l) => s + l.gross_amount, 0);

  const filtered = useMemo(() => {
    let rows = all;
    if (filter === "unlinked") rows = rows.filter((l) => !linkedFlag(l));
    if (filter === "open") rows = rows.filter(isOpen);
    if (query) {
      const q = query.toLowerCase();
      rows = rows.filter(
        (l) =>
          l.entity_name.toLowerCase().includes(q) ||
          l.coverage.toLowerCase().includes(q) ||
          (l.cause_code ?? "").toLowerCase().includes(q) ||
          l.id.toLowerCase().includes(q),
      );
    }
    return rows;
  }, [all, filter, query]);

  const cols: AdminTableCol[] = [
    { key: "entity", label: "Entity", width: "2fr" },
    { key: "coverage", label: "Coverage", width: "1fr" },
    { key: "date", label: "Event date", width: "130px" },
    { key: "gross", label: "Gross", align: "right", width: "120px" },
    { key: "net", label: "Net", align: "right", width: "120px" },
    { key: "status", label: "Status", width: "120px" },
    { key: "linked", label: "Linked", width: "90px" },
  ];

  const rows: AdminTableRow[] = filtered.map((l) => ({
    entity: (
      <div>
        <span className="font-semibold text-ink">{l.entity_name}</span>
        <Micro className="mt-0.5 block font-mono">{l.id}</Micro>
      </div>
    ),
    coverage: <code className="text-[12px] text-ink">{l.coverage}</code>,
    date: (
      <span className="font-mono text-[12px] text-ink-soft">
        {formatDate(l.event_date)}
      </span>
    ),
    gross: (
      <span className="tabular-nums font-semibold text-ink">
        {formatCurrency(l.gross_amount)}
      </span>
    ),
    net: (
      <span className="tabular-nums text-ink-soft">
        {l.net_amount != null ? formatCurrency(l.net_amount) : "—"}
      </span>
    ),
    status: (
      <Chip
        size="sm"
        variant={
          isOpen(l) ? "spot" : /pending/i.test(l.status) ? "warn" : "pos"
        }
      >
        {formatText(l.status, "capitalize")}
      </Chip>
    ),
    linked: linkedFlag(l) ? (
      <Chip size="sm" variant="pos">
        <Check size={10} /> yes
      </Chip>
    ) : (
      <Chip size="sm" variant="spot">
        no
      </Chip>
    ),
  }));

  return (
    <>
      <Topbar crumbs={["Admin", "Loss Register"]} />
      <div className="flex-1 overflow-y-auto px-9 py-7">
        <div className="mx-auto grid max-w-[1400px] gap-4">
          <header className="flex items-end justify-between gap-6">
            <div>
              <Eyebrow>Loss register</Eyebrow>
              <h1 className="mt-1.5 font-display text-[32px] font-semibold leading-none tracking-tight text-ink">
                Loss events feeding recalibration
              </h1>
              <Body className="mt-1.5">
                Import claims via CSV; we'll attempt to attach them back to the
                submissions that priced them.
              </Body>
            </div>
            <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
              <MiniKpi label="Events" value={all.length} />
              <MiniKpi label="Gross" value={formatCurrency(grossSum)} />
              <MiniKpi label="Unlinked" value={unlinkedCount} />
              <MiniKpi label="Open" value={openCount} />
            </div>
          </header>

          {toast && (
            <Card pad="md" variant="info">
              <Body className="text-[13.5px] text-ink">{toast}</Body>
            </Card>
          )}

          <Card pad="md">
            <div className="flex flex-wrap items-center gap-4">
              <label className="flex cursor-pointer items-center gap-2.5">
                <input
                  type="file"
                  accept=".csv,.tsv,.json"
                  onChange={onImport}
                  className="hidden"
                  disabled={importing}
                />
                <UploadCloud size={18} className="text-ink-soft" />
                <span className="text-[13px] font-semibold text-ink">
                  Drop a CSV here
                </span>
                <span className="text-[12px] text-ink-mute">or</span>
                <span
                  className={cn(
                    "inline-flex h-8 items-center gap-1.5 rounded-btn border border-rule-strong bg-surface px-3 text-[12px] font-semibold text-ink",
                    importing && "opacity-60",
                  )}
                >
                  {importing ? (
                    <Loader2 size={11} className="animate-spin" />
                  ) : null}
                  Browse
                </span>
              </label>

              <div className="h-8 w-px self-stretch bg-rule" />

              <div className="flex flex-1 flex-wrap items-center gap-2">
                <Micro>Filter:</Micro>
                <FilterChip
                  active={filter === "all"}
                  onClick={() => setFilter("all")}
                >
                  All
                </FilterChip>
                <FilterChip
                  active={filter === "unlinked"}
                  onClick={() => setFilter("unlinked")}
                >
                  Unlinked ({unlinkedCount})
                </FilterChip>
                <FilterChip
                  active={filter === "open"}
                  onClick={() => setFilter("open")}
                >
                  Open ({openCount})
                </FilterChip>
                <div className="ml-auto flex items-center gap-2">
                  <div className="flex h-9 items-center gap-2 rounded-btn border border-rule-strong bg-surface px-3">
                    <Search size={14} className="text-ink-mute" />
                    <input
                      type="search"
                      placeholder="Entity, coverage, cause code…"
                      value={query}
                      onChange={(e) => setQuery(e.target.value)}
                      className="w-52 border-0 bg-transparent text-[13px] text-ink placeholder:text-ink-mute focus:outline-none"
                    />
                  </div>
                  <Button
                    variant="primary"
                    onClick={onLinkAll}
                    disabled={linking}
                  >
                    {linking ? (
                      <Loader2 size={13} className="animate-spin" />
                    ) : (
                      <Link2 size={13} />
                    )}
                    Link all
                  </Button>
                </div>
              </div>
            </div>
          </Card>

          {state === "loading" && <PageLoading message="Loading losses…" />}
          {state === "error" && <PageError message={err ?? "Unknown error"} />}
          {state === "ok" && (
            <Card pad="none">
              <AdminTable cols={cols} rows={rows} />
              {filtered.length === 0 && (
                <div className="px-5 py-8 text-center">
                  <Body className="italic">
                    No losses match the current filters.
                  </Body>
                </div>
              )}
            </Card>
          )}
        </div>
      </div>
    </>
  );
}

function FilterChip({
  active,
  onClick,
  children,
}: {
  active: boolean;
  onClick: () => void;
  children: React.ReactNode;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={cn(
        "inline-flex items-center gap-1.5 rounded-chip px-2.5 py-1 text-[11.5px] font-medium transition-colors",
        active
          ? "bg-ink text-canvas"
          : "bg-surface-sunken text-ink-soft hover:bg-surface-elev",
      )}
    >
      {children}
    </button>
  );
}

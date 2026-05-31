"use client";

import { useEffect, useState } from "react";
import { ChevronDown, ChevronRight, Download, Search } from "lucide-react";
import { Topbar } from "@/components/chrome/topbar";
import {
  Body,
  Button,
  Card,
  Chip,
  Eyebrow,
  Micro,
} from "@/components/ui";
import { PageError, PageLoading } from "@/components/base/pageStates";
import { PermissionGate } from "@/components/shared/PermissionGate";
import { api } from "@/lib/api";
import { fmtRelative } from "@/lib/utils";
import type { AuditEventRow } from "@/types/admin";

export default function AdminAuditPage() {
  return (
    <PermissionGate
      permission="admin:audit"
      fallback={<PageError message="You don't have admin:audit permission." />}
    >
      <AuditInner />
    </PermissionGate>
  );
}

function AuditInner() {
  const [data, setData] = useState<AuditEventRow[] | null>(null);
  const [state, setState] = useState<"loading" | "ok" | "error">("loading");
  const [err, setErr] = useState<string | null>(null);

  const [actionType, setActionType] = useState("");
  const [resourceType, setResourceType] = useState("");
  const [fromDate, setFromDate] = useState("");
  const [toDate, setToDate] = useState("");
  const [query, setQuery] = useState("");

  async function load() {
    setState("loading");
    try {
      const params = new URLSearchParams();
      if (actionType) params.set("action_type", actionType);
      if (resourceType) params.set("resource_type", resourceType);
      if (fromDate) params.set("from", fromDate);
      if (toDate) params.set("to", toDate);
      params.set("limit", "200");
      const r = await api.get<{ events: AuditEventRow[] }>(
        `/api/v1/admin/audit?${params.toString()}`,
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
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  function reset() {
    setActionType("");
    setResourceType("");
    setFromDate("");
    setToDate("");
    setQuery("");
    void load();
  }

  function exportCsv() {
    const params = new URLSearchParams();
    if (actionType) params.set("action_type", actionType);
    if (resourceType) params.set("resource_type", resourceType);
    if (fromDate) params.set("from", fromDate);
    if (toDate) params.set("to", toDate);
    window.open(`/api/v1/admin/audit/export?${params.toString()}`, "_blank");
  }

  const filtered = (data ?? []).filter((e) => {
    if (!query) return true;
    const q = query.toLowerCase();
    return (
      e.action_type.toLowerCase().includes(q) ||
      (e.resource_type ?? "").toLowerCase().includes(q) ||
      (e.resource_id ?? "").toLowerCase().includes(q) ||
      (e.user_id ?? "").toLowerCase().includes(q) ||
      (e.request_id ?? "").toLowerCase().includes(q)
    );
  });

  return (
    <>
      <Topbar crumbs={["Admin", "Audit Log"]} />
      <div className="flex-1 overflow-y-auto px-9 py-7">
        <div className="grid gap-4">
          <header className="flex items-end justify-between gap-6">
            <div>
              <h1 className="mt-1.5 font-display text-[32px] font-semibold leading-none tracking-tight text-ink">
                Everything that changed
              </h1>
              <Body className="mt-1.5">
                Every config deploy, decision, user action, recalibration
                approval — who, what, when, from where.
              </Body>
            </div>
            <Button variant="ghost" onClick={exportCsv}>
              <Download size={13} />
              Export CSV
            </Button>
          </header>

          <Card pad="md">
            <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-[1fr_1fr_1fr_1fr_auto_auto]">
              <FilterField label="Action">
                <input
                  type="text"
                  value={actionType}
                  onChange={(ev) => setActionType(ev.target.value)}
                  placeholder="CONFIG_DEPLOY"
                  className={filterInput}
                />
              </FilterField>
              <FilterField label="Resource">
                <input
                  type="text"
                  value={resourceType}
                  onChange={(ev) => setResourceType(ev.target.value)}
                  placeholder="config_version"
                  className={filterInput}
                />
              </FilterField>
              <FilterField label="From">
                <input
                  type="date"
                  value={fromDate}
                  onChange={(ev) => setFromDate(ev.target.value)}
                  className={filterInput}
                />
              </FilterField>
              <FilterField label="To">
                <input
                  type="date"
                  value={toDate}
                  onChange={(ev) => setToDate(ev.target.value)}
                  className={filterInput}
                />
              </FilterField>
              <div className="flex items-end gap-2">
                <Button variant="primary" onClick={() => void load()}>
                  Apply
                </Button>
                <Button variant="ghost" onClick={reset}>
                  Reset
                </Button>
              </div>
              <div className="flex items-end">
                <div className="flex h-10 items-center gap-2 rounded-btn border border-rule-strong bg-surface px-3">
                  <Search size={14} className="text-ink-mute" />
                  <input
                    type="search"
                    placeholder="Find an event…"
                    value={query}
                    onChange={(ev) => setQuery(ev.target.value)}
                    className="w-44 border-0 bg-transparent text-[13px] text-ink placeholder:text-ink-mute focus:outline-none"
                  />
                </div>
              </div>
            </div>
          </Card>

          {state === "loading" && <PageLoading message="Loading events…" />}
          {state === "error" && <PageError message={err ?? "Unknown error"} />}
          {state === "ok" && (
            <Card
              pad="none"
              header="Events"
              headerRight={
                <Chip size="sm" variant="mute">
                  {filtered.length}
                </Chip>
              }
            >
              {/* Column header strip mirrors the AdminTable layout but rows
                  expand to reveal the before/after state diff. */}
              <div className="grid grid-cols-[180px_1.4fr_2.2fr_1fr_110px_28px] gap-3 border-b border-rule bg-surface-elev px-5 py-2.5 text-[11px] uppercase tracking-wider text-ink-mute">
                <span>When</span>
                <span>Action</span>
                <span>Resource</span>
                <span>User</span>
                <span className="text-right">Latency</span>
                <span />
              </div>
              {filtered.map((e) => (
                <AuditRow key={e.id} event={e} />
              ))}
              {filtered.length === 0 && (
                <div className="px-5 py-8 text-center">
                  <Body className="italic">No events match the filters.</Body>
                </div>
              )}
            </Card>
          )}
        </div>
      </div>
    </>
  );
}

function FilterField({
  label,
  children,
}: {
  label: string;
  children: React.ReactNode;
}) {
  return (
    <div>
      <Micro className="mb-1 block">{label}</Micro>
      {children}
    </div>
  );
}

const filterInput =
  "block h-10 w-full rounded-btn border border-rule-strong bg-surface px-3 font-mono text-[12.5px] text-ink placeholder:text-ink-mute focus:border-info focus:outline-none focus:ring-2 focus:ring-info/30";

function AuditRow({ event: e }: { event: AuditEventRow }) {
  const [open, setOpen] = useState(false);
  const hasDiff =
    (e.before_state != null && e.before_state !== "") ||
    (e.after_state != null && e.after_state !== "");

  return (
    <div className="border-b border-rule last:border-0">
      <button
        type="button"
        onClick={() => hasDiff && setOpen((v) => !v)}
        className={`grid w-full grid-cols-[180px_1.4fr_2.2fr_1fr_110px_28px] items-center gap-3 px-5 py-3 text-left ${
          hasDiff ? "hover:bg-surface-sunken/40" : "cursor-default"
        }`}
      >
        <span className="font-mono text-[12px] tabular-nums text-ink-soft">
          {fmtRelative(e.created_at)}
        </span>
        <code className="text-[12px] font-bold text-ink">{e.action_type}</code>
        <span className="text-[12.5px] text-ink-soft">
          {e.resource_type ? (
            <>
              <span className="text-ink">{e.resource_type}</span>
              {e.resource_id && (
                <span className="ml-1 font-mono text-[11.5px] text-ink-mute">
                  · {e.resource_id}
                </span>
              )}
            </>
          ) : (
            "—"
          )}
        </span>
        <code className="text-[11.5px] text-ink-mute">{e.user_id ?? "—"}</code>
        <span className="text-right text-[12.5px] tabular-nums text-ink-soft">
          {e.duration_ms != null ? `${e.duration_ms} ms` : "—"}
        </span>
        <span className="flex justify-end text-ink-mute">
          {hasDiff ? (
            open ? <ChevronDown size={16} /> : <ChevronRight size={16} />
          ) : null}
        </span>
      </button>
      {open && hasDiff && (
        <div className="grid gap-3 px-5 pb-4 md:grid-cols-2">
          <DiffPanel label="Before" state={e.before_state} tone="neg" />
          <DiffPanel label="After" state={e.after_state} tone="pos" />
        </div>
      )}
    </div>
  );
}

function DiffPanel({
  label,
  state,
  tone,
}: {
  label: string;
  state: unknown;
  tone: "neg" | "pos";
}) {
  const border = tone === "neg" ? "border-neg/40" : "border-pos/40";
  const text = tone === "neg" ? "text-neg" : "text-pos";
  const body =
    state == null
      ? "—"
      : typeof state === "string"
        ? state
        : JSON.stringify(state, null, 2);
  return (
    <div className={`rounded-card border ${border} bg-surface-elev p-3`}>
      <div className={`mb-1.5 text-[10.5px] font-bold uppercase tracking-wider ${text}`}>
        {label}
      </div>
      <pre className="overflow-x-auto whitespace-pre-wrap break-words font-mono text-[11.5px] leading-relaxed text-ink-soft">
        {body}
      </pre>
    </div>
  );
}

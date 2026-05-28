"use client";

import { useEffect, useState } from "react";
import { Download, History, Search } from "lucide-react";
import { Topbar } from "@/components/chrome/topbar";
import { Card } from "@/components/ui/card";
import { Chip } from "@/components/ui/chip";
import { Button } from "@/components/ui/button";
import { Eyebrow, Body, Micro } from "@/components/ui/typography";
import { PageError, PageLoading } from "@/components/base/pageStates";
import { PermissionGate } from "@/components/shared/PermissionGate";
import { api } from "@/lib/api";
import { formatText } from "@/lib/format";
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
  const [query, setQuery] = useState("");

  async function load() {
    setState("loading");
    try {
      const params = new URLSearchParams();
      if (actionType) params.set("action_type", actionType);
      if (resourceType) params.set("resource_type", resourceType);
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
  }, [actionType, resourceType]);

  function exportCsv() {
    const params = new URLSearchParams();
    if (actionType) params.set("action_type", actionType);
    if (resourceType) params.set("resource_type", resourceType);
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
        <div className="mx-auto grid max-w-[1400px] gap-6">
          <header className="flex items-end justify-between gap-6">
            <div>
              <Eyebrow>Compliance</Eyebrow>
              <h1 className="mt-1 font-display text-[32px] font-semibold leading-none tracking-tight text-ink">
                Audit Log
              </h1>
              <Body className="mt-2">
                Every state-changing action across the platform — who, what,
                when, from where.
              </Body>
            </div>
            <Button variant="ghost" onClick={exportCsv}>
              <Download size={14} />
              Export CSV
            </Button>
          </header>

          <Card pad="md" className="flex flex-wrap items-center gap-3">
            <FilterField label="Action">
              <input
                type="text"
                value={actionType}
                onChange={(e) => setActionType(e.target.value)}
                placeholder="login, config.deploy, …"
                className={filterInput}
              />
            </FilterField>
            <FilterField label="Resource">
              <input
                type="text"
                value={resourceType}
                onChange={(e) => setResourceType(e.target.value)}
                placeholder="user, config, submission, …"
                className={filterInput}
              />
            </FilterField>
            <div className="ml-auto flex items-center gap-2 rounded-btn border border-rule-strong bg-surface px-3">
              <Search size={15} className="text-ink-mute" />
              <input
                type="search"
                placeholder="Find an event…"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                className="h-9 w-64 border-0 bg-transparent text-[13px] text-ink placeholder:text-ink-mute focus:outline-none"
              />
            </div>
          </Card>

          {state === "loading" && <PageLoading message="Loading events…" />}
          {state === "error" && <PageError message={err ?? "Unknown error"} />}
          {state === "ok" && (
            <Card pad="md" className="overflow-hidden p-0">
              <table className="w-full table-fixed text-[13px]">
                <thead>
                  <tr className="border-b border-rule bg-surface-sunken text-left">
                    <ColHead width="w-[18%]">When</ColHead>
                    <ColHead width="w-[18%]">Action</ColHead>
                    <ColHead width="w-[20%]">Resource</ColHead>
                    <ColHead width="w-[18%]">User</ColHead>
                    <ColHead width="w-[14%]">IP</ColHead>
                    <ColHead width="w-[12%]">Duration</ColHead>
                  </tr>
                </thead>
                <tbody>
                  {filtered.map((e) => (
                    <tr
                      key={e.id}
                      className="border-b border-rule last:border-0 hover:bg-surface-sunken/40"
                    >
                      <td className="px-5 py-2.5 text-ink-soft">
                        {fmtRelative(e.created_at)}
                      </td>
                      <td className="px-5 py-2.5">
                        <Chip variant={actionTone(e.action_type)} size="sm">
                          {e.action_type}
                        </Chip>
                      </td>
                      <td className="px-5 py-2.5 text-ink-soft">
                        {e.resource_type ? (
                          <>
                            <span className="font-medium text-ink">
                              {e.resource_type}
                            </span>
                            {e.resource_id && (
                              <span className="ml-1 font-mono text-[11.5px] text-ink-mute">
                                · {e.resource_id}
                              </span>
                            )}
                          </>
                        ) : (
                          <Micro>—</Micro>
                        )}
                      </td>
                      <td className="px-5 py-2.5 font-mono text-[12.5px] text-ink-soft">
                        {e.user_id ?? "—"}
                      </td>
                      <td className="px-5 py-2.5 font-mono text-[12.5px] text-ink-soft">
                        {e.ip_address ?? "—"}
                      </td>
                      <td className="px-5 py-2.5 tabular-nums text-ink-soft">
                        {e.duration_ms != null ? `${e.duration_ms}ms` : "—"}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
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

function actionTone(
  action: string,
): "pos" | "neg" | "warn" | "info" | "mute" {
  const a = action.toLowerCase();
  if (/delete|deactivate|revoke|reject/.test(a)) return "neg";
  if (/login|auth|create|invite|deploy/.test(a)) return "pos";
  if (/fail|error/.test(a)) return "warn";
  if (/read|list|view|export/.test(a)) return "mute";
  return "info";
}

function FilterField({
  label,
  children,
}: {
  label: string;
  children: React.ReactNode;
}) {
  return (
    <label className="flex items-center gap-2 text-[12.5px]">
      <span className="text-ink-mute">{label}:</span>
      {children}
    </label>
  );
}

const filterInput =
  "h-9 w-44 rounded-btn border border-rule-strong bg-surface px-2.5 text-[13px] text-ink placeholder:text-ink-mute focus:border-info focus:outline-none focus:ring-2 focus:ring-info/30";

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

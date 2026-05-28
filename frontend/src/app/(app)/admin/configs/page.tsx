"use client";

import { useEffect, useMemo, useState } from "react";
import { CheckCircle2, FileStack, GitBranch, Loader2, Rocket } from "lucide-react";
import { Topbar } from "@/components/chrome/topbar";
import { Card } from "@/components/ui/card";
import { Chip } from "@/components/ui/chip";
import { Button } from "@/components/ui/button";
import { Eyebrow, Body, Micro } from "@/components/ui/typography";
import { PageError, PageLoading } from "@/components/base/pageStates";
import { PermissionGate } from "@/components/shared/PermissionGate";
import { api } from "@/lib/api";
import { formatText, formatDate } from "@/lib/format";
import { cn } from "@/lib/utils";
import type { ConfigVersionRow } from "@/types/admin";

const STATUS_TONE: Record<ConfigVersionRow["status"], "mute" | "info" | "warn" | "pos" | "neg"> = {
  DRAFT: "mute",
  VALIDATING: "info",
  CALIBRATING: "info",
  READY: "warn",
  DEPLOYED: "pos",
  SUPERSEDED: "mute",
  ARCHIVED: "mute",
};

export default function AdminConfigsPage() {
  return (
    <PermissionGate
      permission="config:read"
      fallback={<PageError message="You don't have config:read permission." />}
    >
      <ConfigsInner />
    </PermissionGate>
  );
}

function ConfigsInner() {
  const [data, setData] = useState<ConfigVersionRow[] | null>(null);
  const [state, setState] = useState<"loading" | "ok" | "error">("loading");
  const [err, setErr] = useState<string | null>(null);
  const [acting, setActing] = useState<string | null>(null);

  async function load() {
    setState("loading");
    try {
      const r = await api.get<{ versions: ConfigVersionRow[] }>(
        "/api/v1/admin/configs",
      );
      setData(r.versions ?? []);
      setState("ok");
    } catch (e) {
      setErr(e instanceof Error ? e.message : String(e));
      setState("error");
    }
  }

  useEffect(() => {
    void load();
  }, []);

  async function transition(versionId: string, endpoint: string) {
    setActing(versionId);
    try {
      await api.post(`/api/v1/admin/configs/versions/${versionId}/${endpoint}`);
      await load();
    } finally {
      setActing(null);
    }
  }

  if (state === "loading") return <PageLoading message="Loading configs…" />;
  if (state === "error") return <PageError message={err ?? "Unknown error"} />;
  if (!data) return <PageLoading />;

  const grouped = new Map<string, ConfigVersionRow[]>();
  for (const v of data) {
    const key = `${v.coverage} · ${v.config_name}`;
    const list = grouped.get(key) ?? [];
    list.push(v);
    grouped.set(key, list);
  }

  return (
    <>
      <Topbar crumbs={["Admin", "Configs"]} />
      <div className="flex-1 overflow-y-auto px-9 py-7">
        <div className="mx-auto grid max-w-[1400px] gap-6">
          <header>
            <Eyebrow>Governance</Eyebrow>
            <h1 className="mt-1 font-display text-[32px] font-semibold leading-none tracking-tight text-ink">
              Configs
            </h1>
            <Body className="mt-2">
              Per-coverage configuration versions. Promote drafts through
              validate → calibrate → deploy.
            </Body>
          </header>

          {grouped.size === 0 ? (
            <Card pad="lg">
              <Body className="italic">No config versions found.</Body>
            </Card>
          ) : (
            <div className="space-y-5">
              {[...grouped.entries()]
                .sort((a, b) => a[0].localeCompare(b[0]))
                .map(([title, versions]) => {
                  const sorted = [...versions].sort((a, b) => b.version - a.version);
                  return (
                    <Card key={title} pad="md" className="overflow-hidden p-0">
                      <header className="flex items-center gap-3 border-b border-rule px-5 py-3.5">
                        <FileStack size={15} className="text-ink-mute" />
                        <h2 className="text-[15px] font-semibold text-ink">
                          {title}
                        </h2>
                        <Micro className="ml-auto">
                          {versions.length} version{versions.length === 1 ? "" : "s"}
                        </Micro>
                      </header>
                      <table className="w-full table-fixed text-[13px]">
                        <thead>
                          <tr className="border-b border-rule bg-surface-sunken/60 text-left">
                            <ColHead width="w-[8%]">V</ColHead>
                            <ColHead width="w-[14%]">Status</ColHead>
                            <ColHead width="w-[18%]">Author</ColHead>
                            <ColHead width="w-[28%]">Notes</ColHead>
                            <ColHead width="w-[14%]">Updated</ColHead>
                            <ColHead width="w-[18%]">Actions</ColHead>
                          </tr>
                        </thead>
                        <tbody>
                          {sorted.map((v) => (
                            <VersionRow
                              key={v.id}
                              v={v}
                              isActing={acting === v.id}
                              onTransition={(ep) => transition(v.id, ep)}
                            />
                          ))}
                        </tbody>
                      </table>
                    </Card>
                  );
                })}
            </div>
          )}
        </div>
      </div>
    </>
  );
}

function VersionRow({
  v,
  isActing,
  onTransition,
}: {
  v: ConfigVersionRow;
  isActing: boolean;
  onTransition: (endpoint: string) => void;
}) {
  const next = nextTransition(v.status);
  return (
    <tr className="border-b border-rule last:border-0 hover:bg-surface-sunken/40">
      <td className="px-5 py-3">
        <span className="font-semibold tabular-nums text-ink">v{v.version}</span>
      </td>
      <td className="px-5 py-3">
        <Chip variant={STATUS_TONE[v.status]} size="sm">
          {formatText(v.status, "capitalize")}
        </Chip>
      </td>
      <td className="px-5 py-3 font-mono text-[12.5px] text-ink-soft">
        {v.author_id ?? "—"}
      </td>
      <td
        className={cn(
          "px-5 py-3 text-[12.5px]",
          v.notes ? "text-ink-soft" : "text-ink-mute italic",
        )}
      >
        {v.notes ?? "no notes"}
      </td>
      <td className="px-5 py-3 text-ink-soft">{formatDate(v.updated_at)}</td>
      <td className="px-5 py-3">
        {next ? (
          <Button
            type="button"
            variant={next.endpoint === "deploy" ? "spot" : "ghost"}
            size="sm"
            disabled={isActing}
            onClick={() => onTransition(next.endpoint)}
          >
            {isActing ? (
              <Loader2 size={12} className="animate-spin" />
            ) : next.endpoint === "deploy" ? (
              <Rocket size={12} />
            ) : (
              <GitBranch size={12} />
            )}
            {next.label}
          </Button>
        ) : v.status === "DEPLOYED" ? (
          <span className="inline-flex items-center gap-1 text-[12.5px] text-pos">
            <CheckCircle2 size={12} />
            Active
          </span>
        ) : (
          <Micro>—</Micro>
        )}
      </td>
    </tr>
  );
}

function nextTransition(
  status: ConfigVersionRow["status"],
): { endpoint: string; label: string } | null {
  switch (status) {
    case "DRAFT":
      return { endpoint: "validate", label: "Validate" };
    case "VALIDATING":
      return { endpoint: "calibrate", label: "Calibrate" };
    case "CALIBRATING":
      return { endpoint: "ready", label: "Mark ready" };
    case "READY":
      return { endpoint: "deploy", label: "Deploy" };
    default:
      return null;
  }
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

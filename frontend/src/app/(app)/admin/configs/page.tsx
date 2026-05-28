"use client";

import { useEffect, useMemo, useState } from "react";
import {
  CheckCircle2,
  FileStack,
  History,
  Loader2,
  RefreshCw,
  Rocket,
  ShieldCheck,
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
} from "@/components/ui";
import type { AdminTableCol, AdminTableRow } from "@/components/ui";
import { PageError, PageLoading } from "@/components/base/pageStates";
import { PermissionGate } from "@/components/shared/PermissionGate";
import { api } from "@/lib/api";
import { formatDate, formatText } from "@/lib/format";
import { fmtRelative } from "@/lib/utils";
import type { ConfigVersionRow } from "@/types/admin";

type VersionStatus = ConfigVersionRow["status"];

const STATUS_TONE: Record<
  VersionStatus,
  "mute" | "info" | "warn" | "pos" | "neg"
> = {
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

interface ConfigGroup {
  key: string;
  coverage: string;
  configName: string;
  versions: ConfigVersionRow[];
  activeVersion: number | null;
  draftCount: number;
  lastUpdated: string | null;
}

function ConfigsInner() {
  const [data, setData] = useState<ConfigVersionRow[] | null>(null);
  const [state, setState] = useState<"loading" | "ok" | "error">("loading");
  const [err, setErr] = useState<string | null>(null);
  const [acting, setActing] = useState<string | null>(null);
  const [focusKey, setFocusKey] = useState<string | null>(null);

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

  const groups = useMemo<ConfigGroup[]>(() => {
    if (!data) return [];
    const map = new Map<string, ConfigGroup>();
    for (const v of data) {
      const key = `${v.coverage}/${v.config_name}`;
      const g = map.get(key) ?? {
        key,
        coverage: v.coverage,
        configName: v.config_name,
        versions: [],
        activeVersion: null,
        draftCount: 0,
        lastUpdated: null,
      };
      g.versions.push(v);
      if (v.status === "DEPLOYED") {
        g.activeVersion = Math.max(g.activeVersion ?? 0, v.version);
      }
      if (v.status === "DRAFT") g.draftCount += 1;
      if (!g.lastUpdated || v.updated_at > g.lastUpdated) {
        g.lastUpdated = v.updated_at;
      }
      map.set(key, g);
    }
    return [...map.values()].sort((a, b) => a.key.localeCompare(b.key));
  }, [data]);

  const focusGroup = useMemo<ConfigGroup | null>(() => {
    if (groups.length === 0) return null;
    const match = focusKey ? groups.find((g) => g.key === focusKey) : null;
    return match ?? groups[0];
  }, [groups, focusKey]);

  if (state === "loading") return <PageLoading message="Loading configs…" />;
  if (state === "error") return <PageError message={err ?? "Unknown error"} />;

  const configCols: AdminTableCol[] = [
    { key: "coverage", label: "Coverage", width: "1.4fr" },
    { key: "config", label: "Config", width: "2fr" },
    { key: "active", label: "Active v", align: "right", width: "100px" },
    { key: "drafts", label: "Drafts", align: "right", width: "100px" },
    { key: "updated", label: "Last updated", width: "150px" },
  ];

  const configRows: AdminTableRow[] = groups.map((g) => ({
    coverage: (
      <button
        type="button"
        onClick={() => setFocusKey(g.key)}
        className="text-left font-mono text-[12px] font-bold uppercase text-ink hover:underline"
      >
        {g.coverage}
      </button>
    ),
    config: (
      <code className="text-[12px] text-ink">{g.configName}</code>
    ),
    active: (
      <span className="tabular-nums font-semibold text-ink">
        {g.activeVersion != null ? `v${g.activeVersion}` : "—"}
      </span>
    ),
    drafts:
      g.draftCount > 0 ? (
        <Chip size="sm" variant="spot">
          {g.draftCount}
        </Chip>
      ) : (
        <Micro>—</Micro>
      ),
    updated: <Micro>{g.lastUpdated ? fmtRelative(g.lastUpdated) : "—"}</Micro>,
  }));

  const historyCols: AdminTableCol[] = [
    { key: "v", label: "v", width: "70px" },
    { key: "status", label: "Status", width: "120px" },
    { key: "author", label: "Author", width: "1fr" },
    { key: "updated", label: "Updated", width: "140px" },
    { key: "notes", label: "Notes", width: "2fr" },
    { key: "actions", label: "Actions", align: "right", width: "220px" },
  ];

  const historyRows: AdminTableRow[] = focusGroup
    ? [...focusGroup.versions]
        .sort((a, b) => b.version - a.version)
        .map((v) => ({
          v: (
            <span className="font-mono font-bold tabular-nums text-ink">
              v{v.version}
            </span>
          ),
          status: (
            <Chip size="sm" variant={STATUS_TONE[v.status]}>
              {formatText(v.status, "capitalize")}
            </Chip>
          ),
          author: (
            <code className="text-[11.5px] text-ink-mute">
              {v.author_id ?? "—"}
            </code>
          ),
          updated: <Micro>{formatDate(v.updated_at)}</Micro>,
          notes: (
            <span className="text-[12.5px] text-ink-soft">
              {v.notes ?? "no notes"}
            </span>
          ),
          actions: (
            <ActionButtons
              version={v}
              isActing={acting === v.id}
              onTransition={(ep) => transition(v.id, ep)}
            />
          ),
        }))
    : [];

  return (
    <>
      <Topbar crumbs={["Admin", "Configs"]} />
      <div className="flex-1 overflow-y-auto px-9 py-7">
        <div className="mx-auto grid max-w-[1400px] gap-4">
          <header className="flex items-end justify-between gap-6">
            <div>
              <Eyebrow>Scoring configs</Eyebrow>
              <h1 className="mt-1.5 font-display text-[32px] font-semibold leading-none tracking-tight text-ink">
                Signal weights + tier thresholds
              </h1>
              <Body className="mt-1.5">
                Versioned configs per coverage line. Promote from DRAFT →
                READY → DEPLOYED through governance.
              </Body>
            </div>
            <Button variant="ghost" onClick={() => void load()}>
              <RefreshCw size={13} />
              Refresh
            </Button>
          </header>

          {groups.length === 0 ? (
            <Card pad="lg">
              <Body className="italic">No config versions found.</Body>
            </Card>
          ) : (
            <>
              <Card
                pad="none"
                icon={FileStack}
                header={`Configs · ${groups.length}`}
              >
                <AdminTable cols={configCols} rows={configRows} />
              </Card>

              {focusGroup && (
                <Card pad="none" icon={History} header="Version history">
                  <div className="border-b border-rule bg-surface-sunken px-5 py-2">
                    <code className="text-[12px] text-ink-soft">
                      {focusGroup.coverage} / {focusGroup.configName} ·{" "}
                      {focusGroup.versions.length} version
                      {focusGroup.versions.length === 1 ? "" : "s"}
                    </code>
                  </div>
                  <AdminTable cols={historyCols} rows={historyRows} />
                </Card>
              )}
            </>
          )}
        </div>
      </div>
    </>
  );
}

function ActionButtons({
  version,
  isActing,
  onTransition,
}: {
  version: ConfigVersionRow;
  isActing: boolean;
  onTransition: (endpoint: string) => void;
}) {
  const next = nextTransition(version.status);
  if (!next && version.status === "DEPLOYED") {
    return (
      <span className="inline-flex items-center gap-1 text-[12px] text-pos">
        <CheckCircle2 size={11} />
        Active
      </span>
    );
  }
  if (!next) return <Micro>—</Micro>;
  return (
    <div className="flex items-center justify-end gap-1.5">
      <Button
        type="button"
        variant={next.endpoint === "deploy" ? "primary" : "ghost"}
        size="sm"
        disabled={isActing}
        onClick={() => onTransition(next.endpoint)}
      >
        {isActing ? (
          <Loader2 size={11} className="animate-spin" />
        ) : next.endpoint === "deploy" ? (
          <Rocket size={11} />
        ) : next.endpoint === "ready" ? (
          <ShieldCheck size={11} />
        ) : null}
        {next.label}
      </Button>
    </div>
  );
}

function nextTransition(
  status: VersionStatus,
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

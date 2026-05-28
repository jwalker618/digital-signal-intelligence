"use client";

import { useEffect, useState } from "react";
import { CheckCircle2, RefreshCw } from "lucide-react";
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
  NumDisplay,
} from "@/components/ui";
import type { AdminTableCol, AdminTableRow } from "@/components/ui";
import { PageError, PageLoading } from "@/components/base/pageStates";
import { PermissionGate } from "@/components/shared/PermissionGate";
import { api } from "@/lib/api";
import { useAuthStore } from "@/store/authStore";
import { formatPercent, formatText } from "@/lib/format";
import { cn, fmtRelative } from "@/lib/utils";
import type {
  ExtractorHealth,
  HealthStatus,
  PipelineMetrics,
  SystemHealth,
} from "@/types/admin";

interface HealthBundle {
  health: SystemHealth | null;
  pipeline: PipelineMetrics | null;
  extractors: ExtractorHealth[];
}

export default function SystemHealthPage() {
  const accessToken = useAuthStore((s) => s.accessToken);
  const [data, setData] = useState<HealthBundle | null>(null);
  const [state, setState] = useState<"loading" | "ok" | "error">("loading");
  const [err, setErr] = useState<string | null>(null);

  async function load() {
    setState("loading");
    try {
      const [health, pipeline, extractors] = await Promise.all([
        api.get<SystemHealth>("/api/v1/admin/health").catch(() => null),
        api
          .get<PipelineMetrics>("/api/v1/admin/health/pipeline")
          .catch(() => null),
        api
          .get<{ extractors: ExtractorHealth[] }>(
            "/api/v1/admin/health/extractors",
          )
          .then((r) => r.extractors ?? [])
          .catch(() => [] as ExtractorHealth[]),
      ]);
      setData({ health, pipeline, extractors });
      setState("ok");
    } catch (e) {
      setErr(e instanceof Error ? e.message : String(e));
      setState("error");
    }
  }

  useEffect(() => {
    void load();
  }, [accessToken]);

  return (
    <PermissionGate
      permission="admin:system"
      fallback={<PageError message="You don't have admin:system permission." />}
    >
      {state === "loading" && <PageLoading message="Reading system health…" />}
      {state === "error" && <PageError message={err ?? "Unknown error"} />}
      {state === "ok" && data && <HealthBody data={data} onReload={load} />}
    </PermissionGate>
  );
}

function HealthBody({
  data,
  onReload,
}: {
  data: HealthBundle;
  onReload: () => void;
}) {
  const components = Object.entries(data.health?.components ?? {});
  const greens = components.filter(([, c]) => c.status === "green").length;
  const overallStatus = data.health?.status ?? "green";
  const overallLabel =
    overallStatus === "green"
      ? "All systems operational"
      : overallStatus === "amber"
        ? "Degraded performance"
        : "Critical incident";

  const extractorCols: AdminTableCol[] = [
    { key: "name", label: "Extractor", width: "2fr" },
    { key: "mode", label: "Mode", width: "90px" },
    { key: "success", label: "Success", align: "right", width: "100px" },
    { key: "errors", label: "Errors", align: "right", width: "90px" },
    { key: "status", label: "Status", width: "110px" },
    { key: "lastError", label: "Last error", width: "1.6fr" },
  ];

  const extractorRows: AdminTableRow[] = data.extractors.map((x) => ({
    name: (
      <code className="font-mono text-[12px] text-ink">{x.name}</code>
    ),
    mode: <Caption>{x.mode}</Caption>,
    success: (
      <span className="tabular-nums text-ink-soft">
        {x.success_count.toLocaleString()}
      </span>
    ),
    errors: (
      <span
        className={cn(
          "tabular-nums",
          x.error_count > 10
            ? "text-warn"
            : x.error_count > 0
              ? "text-ink-soft"
              : "text-ink-mute",
        )}
      >
        {x.error_count.toLocaleString()}
      </span>
    ),
    status: <StatusDot status={x.status} />,
    lastError: (
      <span className="text-[12px] text-ink-soft">
        {x.last_error ?? (x.last_error_at ? fmtRelative(x.last_error_at) : "—")}
      </span>
    ),
  }));

  return (
    <>
      <Topbar crumbs={["Admin", "System Health"]} />
      <div className="flex-1 overflow-y-auto px-9 py-7">
        <div className="mx-auto grid max-w-[1400px] gap-4">
          <header className="flex items-end justify-between gap-6">
            <div>
              <Eyebrow>System health</Eyebrow>
              <h1 className="mt-1.5 font-display text-[32px] font-semibold leading-none tracking-tight text-ink">
                {overallLabel}
              </h1>
              {data.health?.checked_at && (
                <Body className="mt-1.5">
                  Auto-refresh every 30s · last check {fmtRelative(data.health.checked_at)}
                </Body>
              )}
            </div>
            <div className="flex items-center gap-2.5">
              <Chip variant={toneFromHealth(overallStatus)} size="md">
                <CheckCircle2 size={13} />
                {greens} of {components.length || 0} green
              </Chip>
              <Button variant="ghost" onClick={onReload}>
                <RefreshCw size={13} />
                Refresh
              </Button>
            </div>
          </header>

          {data.pipeline && (
            <Card
              pad="lg"
              header={`Pipeline · last ${data.pipeline.window_hours}h`}
              headerRight={
                <Chip
                  variant={
                    data.pipeline.failure_rate <= 0.005
                      ? "pos"
                      : data.pipeline.failure_rate <= 0.02
                        ? "warn"
                        : "neg"
                  }
                  size="sm"
                >
                  Failure {formatPercent(data.pipeline.failure_rate, 2)}
                </Chip>
              }
            >
              <div className="grid grid-cols-2 gap-3 md:grid-cols-5">
                <MiniKpi
                  label="Assessments"
                  value={data.pipeline.total_assessments.toLocaleString()}
                />
                <MiniKpi
                  label="p50"
                  value={`${data.pipeline.p50_ms.toFixed(0)}ms`}
                  caption="median latency"
                />
                <MiniKpi
                  label="p95"
                  value={`${data.pipeline.p95_ms.toFixed(0)}ms`}
                />
                <MiniKpi
                  label="p99"
                  value={`${data.pipeline.p99_ms.toFixed(0)}ms`}
                />
                <MiniKpi
                  label="Failure rate"
                  value={formatPercent(data.pipeline.failure_rate, 2)}
                />
              </div>
            </Card>
          )}

          <div className="grid gap-4 lg:grid-cols-[1fr_1.6fr]">
            {components.length > 0 && (
              <Card pad="lg">
                <Eyebrow>Components</Eyebrow>
                <h2 className="mt-1.5 mb-3 text-[17px] font-semibold text-ink">
                  Subsystems
                </h2>
                <div className="flex flex-col">
                  {components.map(([name, c], i) => (
                    <div
                      key={name}
                      className={cn(
                        "grid grid-cols-[12px_1fr] items-start gap-3 py-2.5",
                        i < components.length - 1 && "border-b border-rule",
                      )}
                    >
                      <span
                        className={cn(
                          "mt-1.5 h-2.5 w-2.5 rounded-full",
                          c.status === "green"
                            ? "bg-pos"
                            : c.status === "amber"
                              ? "bg-warn"
                              : "bg-neg",
                        )}
                        aria-label={`Status ${c.status}`}
                      />
                      <div>
                        <p className="text-[13px] font-semibold text-ink">
                          {formatText(name, "capitalize")}
                        </p>
                        {c.detail && (
                          <Micro className="mt-0.5 block">{c.detail}</Micro>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </Card>
            )}

            {data.extractors.length > 0 && (
              <Card
                pad="none"
                header="Extractors"
                headerRight={
                  <Chip size="sm" variant="mute">
                    {data.extractors.length} active
                  </Chip>
                }
              >
                <AdminTable cols={extractorCols} rows={extractorRows} dense />
              </Card>
            )}
          </div>

          {!data.health && !data.pipeline && data.extractors.length === 0 && (
            <Card pad="lg">
              <Body className="italic">
                No health data returned by the admin endpoints.
              </Body>
            </Card>
          )}
        </div>
      </div>
    </>
  );
}

function StatusDot({ status }: { status: HealthStatus }) {
  return (
    <span className="inline-flex items-center gap-1.5">
      <span
        className={cn(
          "h-2 w-2 rounded-full",
          status === "green"
            ? "bg-pos"
            : status === "amber"
              ? "bg-warn"
              : "bg-neg",
        )}
      />
      <span className="text-[12px] font-semibold capitalize text-ink">
        {status}
      </span>
    </span>
  );
}

function toneFromHealth(s: HealthStatus): "pos" | "warn" | "neg" {
  return s === "green" ? "pos" : s === "amber" ? "warn" : "neg";
}

function Caption({ children }: { children: React.ReactNode }) {
  return <span className="text-[12px] text-ink-soft">{children}</span>;
}

void NumDisplay;

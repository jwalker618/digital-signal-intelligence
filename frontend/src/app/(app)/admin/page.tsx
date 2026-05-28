"use client";

import { useEffect, useState } from "react";
import {
  Activity,
  AlertCircle,
  AlertTriangle,
  CheckCircle2,
  RefreshCw,
  Server,
} from "lucide-react";
import { Topbar } from "@/components/chrome/topbar";
import { Card } from "@/components/ui/card";
import { Chip } from "@/components/ui/chip";
import { Button } from "@/components/ui/button";
import { Eyebrow, NumDisplay, Body, Micro } from "@/components/ui/typography";
import { LabelRow } from "@/components/ui/label-row";
import { PageError, PageLoading } from "@/components/base/pageStates";
import { PermissionGate } from "@/components/shared/PermissionGate";
import { api } from "@/lib/api";
import { useAuthStore } from "@/store/authStore";
import { formatPercent, formatText } from "@/lib/format";
import { fmtRelative } from "@/lib/utils";
import { cn } from "@/lib/utils";
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
  const components = data.health?.components ?? {};
  return (
    <>
      <Topbar crumbs={["Admin", "System Health"]} />
      <div className="flex-1 overflow-y-auto px-9 py-7">
        <div className="mx-auto grid max-w-[1400px] gap-6">
          <header className="flex items-end justify-between gap-6">
            <div>
              <Eyebrow>Operations</Eyebrow>
              <h1 className="mt-1 font-display text-[32px] font-semibold leading-none tracking-tight text-ink">
                System Health
              </h1>
              {data.health?.checked_at && (
                <Body className="mt-2">
                  Last checked {fmtRelative(data.health.checked_at)}
                </Body>
              )}
            </div>
            <Button variant="ghost" onClick={onReload}>
              <RefreshCw size={14} />
              Refresh
            </Button>
          </header>

          {/* Overall status */}
          {data.health?.status && (
            <Card
              variant={toneFromHealth(data.health.status)}
              pad="lg"
              className="flex items-center gap-4"
            >
              <StatusBadge status={data.health.status} large />
              <div>
                <Eyebrow>System status</Eyebrow>
                <p className="font-display text-[24px] font-semibold leading-tight text-ink">
                  {data.health.status === "green"
                    ? "All systems operational"
                    : data.health.status === "amber"
                      ? "Degraded performance"
                      : "Critical incident"}
                </p>
              </div>
            </Card>
          )}

          {/* Pipeline metrics */}
          {data.pipeline && (
            <Card pad="lg" className="space-y-4">
              <header className="flex items-center justify-between">
                <Eyebrow>Pipeline ({data.pipeline.window_hours}h window)</Eyebrow>
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
              </header>
              <div className="grid gap-6 md:grid-cols-4">
                <Metric label="Assessments">
                  {data.pipeline.total_assessments.toLocaleString()}
                </Metric>
                <Metric label="p50 latency">
                  {data.pipeline.p50_ms.toFixed(0)}ms
                </Metric>
                <Metric label="p95 latency">
                  {data.pipeline.p95_ms.toFixed(0)}ms
                </Metric>
                <Metric label="p99 latency">
                  {data.pipeline.p99_ms.toFixed(0)}ms
                </Metric>
              </div>
            </Card>
          )}

          {/* Components */}
          {Object.keys(components).length > 0 && (
            <section>
              <Eyebrow className="mb-3">Components</Eyebrow>
              <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
                {Object.entries(components).map(([name, c]) => (
                  <Card key={name} pad="md" className="flex items-start gap-3">
                    <StatusBadge status={c.status} />
                    <div className="min-w-0 flex-1">
                      <p className="text-[14px] font-semibold text-ink">
                        {formatText(name, "capitalize")}
                      </p>
                      {c.detail && (
                        <Micro className="block">{c.detail}</Micro>
                      )}
                    </div>
                  </Card>
                ))}
              </div>
            </section>
          )}

          {/* Extractors */}
          {data.extractors.length > 0 && (
            <section>
              <Eyebrow className="mb-3">
                Extractors ({data.extractors.length})
              </Eyebrow>
              <Card pad="md" className="overflow-hidden p-0">
                <table className="w-full table-fixed text-[13px]">
                  <thead>
                    <tr className="border-b border-rule bg-surface-sunken text-left">
                      <ColHead width="w-[26%]">Name</ColHead>
                      <ColHead width="w-[10%]">Mode</ColHead>
                      <ColHead width="w-[10%]">Status</ColHead>
                      <ColHead width="w-[12%]">Success</ColHead>
                      <ColHead width="w-[12%]">Errors</ColHead>
                      <ColHead width="w-[15%]">Last success</ColHead>
                      <ColHead width="w-[15%]">Last error</ColHead>
                    </tr>
                  </thead>
                  <tbody>
                    {data.extractors.map((x) => (
                      <tr
                        key={x.name}
                        className="border-b border-rule last:border-0 hover:bg-surface-sunken/40"
                      >
                        <td className="px-5 py-2.5">
                          <div className="flex items-center gap-2">
                            <Server size={13} className="text-ink-mute" />
                            <span className="font-medium text-ink">{x.name}</span>
                          </div>
                        </td>
                        <td className="px-5 py-2.5 font-mono text-[12.5px] text-ink-soft">
                          {x.mode}
                        </td>
                        <td className="px-5 py-2.5">
                          <StatusBadge status={x.status} />
                        </td>
                        <td className="px-5 py-2.5 tabular-nums text-pos">
                          {x.success_count.toLocaleString()}
                        </td>
                        <td
                          className={cn(
                            "px-5 py-2.5 tabular-nums",
                            x.error_count > 0 ? "text-neg" : "text-ink-mute",
                          )}
                        >
                          {x.error_count.toLocaleString()}
                        </td>
                        <td className="px-5 py-2.5 text-ink-soft">
                          {fmtRelative(x.last_success_at)}
                        </td>
                        <td className="px-5 py-2.5 text-ink-soft">
                          {fmtRelative(x.last_error_at)}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </Card>
            </section>
          )}

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

function StatusBadge({
  status,
  large,
}: {
  status: HealthStatus;
  large?: boolean;
}) {
  const cls =
    status === "green"
      ? "bg-pos text-white"
      : status === "amber"
        ? "bg-warn text-white"
        : "bg-neg text-white";
  const Icon =
    status === "green"
      ? CheckCircle2
      : status === "amber"
        ? AlertTriangle
        : AlertCircle;
  return (
    <span
      className={cn(
        "flex items-center justify-center rounded-full",
        cls,
        large ? "h-10 w-10" : "h-6 w-6",
      )}
      aria-label={`Status ${status}`}
    >
      <Icon size={large ? 18 : 12} />
    </span>
  );
}

function toneFromHealth(s: HealthStatus): "pos" | "warn" | "neg" {
  return s === "green" ? "pos" : s === "amber" ? "warn" : "neg";
}

function Metric({
  label,
  children,
}: {
  label: string;
  children: React.ReactNode;
}) {
  return (
    <div>
      <Micro className="block">{label}</Micro>
      <p className="mt-1 font-display text-[28px] font-semibold tabular-nums text-ink">
        {children}
      </p>
    </div>
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

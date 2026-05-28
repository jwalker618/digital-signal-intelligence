"use client";

import { useEffect, useState } from "react";
import {
  AlertCircle,
  AlertTriangle,
  Check,
  Link as LinkIcon,
  Orbit,
  Sparkles,
} from "lucide-react";
import { Topbar } from "@/components/chrome/topbar";
import { Card } from "@/components/ui/card";
import { Chip } from "@/components/ui/chip";
import { Button } from "@/components/ui/button";
import { Eyebrow, NumDisplay, Body, Micro } from "@/components/ui/typography";
import { PageError, PageLoading, RoleGate } from "@/components/base/pageStates";
import { CarrierShell } from "@/components/chrome/carrier-shell";
import { isCarrierRole } from "@/lib/portalPaths";
import { useAuthStore } from "@/store/authStore";
import { api } from "@/lib/api";
import { formatText } from "@/lib/format";
import { fmtRelative } from "@/lib/utils";
import { cn } from "@/lib/utils";
import type {
  DiscoveredRelationship,
  DriftAlert,
  MaturityStage,
  WorldEngineStats,
} from "@/types/worldEngine";

const STAGES: { stage: MaturityStage; label: string; description: string }[] = [
  { stage: "seed", label: "Seed", description: "Bootstrapping signal apparatus" },
  { stage: "learn", label: "Learn", description: "Capturing temporal data" },
  { stage: "emerge", label: "Emerge", description: "Causal patterns surfacing" },
  { stage: "simulate", label: "Simulate", description: "Full scenario modelling" },
];

interface WorldEngineState {
  stats: WorldEngineStats | null;
  alerts: DriftAlert[];
  relationships: DiscoveredRelationship[];
}

export default function CarrierWorldEnginePage() {
  const user = useAuthStore((s) => s.user);
  const [data, setData] = useState<WorldEngineState | null>(null);
  const [state, setState] = useState<"loading" | "ok" | "error">("loading");
  const [err, setErr] = useState<string | null>(null);

  async function load() {
    setState("loading");
    try {
      const [stats, alertsResp, relsResp] = await Promise.all([
        api
          .get<WorldEngineStats>("/api/v1/world-engine/stats")
          .catch(() => null),
        api
          .get<{ alerts: DriftAlert[] }>(
            "/api/v1/world-engine/drift-alerts?unacknowledged_only=true",
          )
          .catch(() => ({ alerts: [] as DriftAlert[] })),
        api
          .get<{ relationships: DiscoveredRelationship[] }>(
            "/api/v1/world-engine/relationships?limit=50",
          )
          .catch(() => ({ relationships: [] as DiscoveredRelationship[] })),
      ]);
      setData({
        stats,
        alerts: alertsResp.alerts ?? [],
        relationships: relsResp.relationships ?? [],
      });
      setState("ok");
    } catch (e) {
      setErr(e instanceof Error ? e.message : String(e));
      setState("error");
    }
  }

  useEffect(() => {
    void load();
  }, []);

  async function ackAlert(id: string) {
    try {
      await api.post(`/api/v1/world-engine/drift-alerts/${id}/acknowledge`);
      await load();
    } catch {
      /* keep state */
    }
  }

  const inner =
    !user ? (
      <PageLoading message="Signing in…" />
    ) : user.role && !isCarrierRole(user.role) ? (
      <RoleGate expected="carrier" />
    ) : state === "loading" ? (
      <PageLoading message="Reading the engine…" />
    ) : state === "error" ? (
      <PageError message={err ?? "Unknown error"} />
    ) : !data ? (
      <PageLoading />
    ) : (
      <Body0 data={data} onAck={ackAlert} />
    );

  return <CarrierShell>{inner}</CarrierShell>;
}

function Body0({
  data,
  onAck,
}: {
  data: WorldEngineState;
  onAck: (id: string) => void;
}) {
  return (
    <>
      <Topbar crumbs={["Carrier Portal", "World Engine"]} />
      <div className="flex-1 overflow-y-auto px-9 py-7">
        <div className="mx-auto grid max-w-[1400px] gap-6">
          <header>
            <Eyebrow>Causal model</Eyebrow>
            <h1 className="mt-1 flex items-center gap-3 font-display text-[32px] font-semibold leading-none tracking-tight text-ink">
              <Orbit size={28} className="text-info" />
              World Engine
            </h1>
            <Body className="mt-2">
              The continuous-learning model that watches signals, infers
              causal relationships, and flags drift before it touches your
              pricing.
            </Body>
          </header>

          {/* Maturity */}
          {data.stats?.maturity && <MaturityCard stats={data.stats} />}

          {/* Stats */}
          {data.stats && (
            <div className="grid gap-4 md:grid-cols-4">
              <KPI label="Scan runs (7d)">
                {data.stats.scan_runs_last_7_days}
              </KPI>
              <KPI label="Scan runs total">{data.stats.scan_runs_total}</KPI>
              <KPI label="Drift alerts" tone={data.stats.drift_alerts_unacknowledged > 0 ? "spot" : undefined}>
                {data.stats.drift_alerts_unacknowledged}
              </KPI>
              <KPI label="CAF computations">
                {data.stats.caf_computations_total}
              </KPI>
            </div>
          )}

          {/* Drift alerts */}
          {data.alerts.length > 0 && (
            <section>
              <Eyebrow className="mb-3 text-spot">
                Drift alerts ({data.alerts.length})
              </Eyebrow>
              <div className="space-y-3">
                {data.alerts.slice(0, 8).map((a) => (
                  <AlertCard key={a.id} alert={a} onAck={onAck} />
                ))}
              </div>
            </section>
          )}

          {/* Relationships */}
          {data.relationships.length > 0 && (
            <section>
              <Eyebrow className="mb-3">
                Discovered relationships ({data.relationships.length})
              </Eyebrow>
              <Card pad="md" className="overflow-hidden p-0">
                <table className="w-full table-fixed text-[13px]">
                  <thead>
                    <tr className="border-b border-rule bg-surface-sunken text-left">
                      <ColHead width="w-[22%]">Source</ColHead>
                      <ColHead width="w-[6%]">→</ColHead>
                      <ColHead width="w-[22%]">Target</ColHead>
                      <ColHead width="w-[12%]">Lag</ColHead>
                      <ColHead width="w-[12%]">ρ</ColHead>
                      <ColHead width="w-[12%]">Weight</ColHead>
                      <ColHead width="w-[14%]">Lifecycle</ColHead>
                    </tr>
                  </thead>
                  <tbody>
                    {data.relationships.slice(0, 30).map((r) => (
                      <RelRow key={r.id} rel={r} />
                    ))}
                  </tbody>
                </table>
              </Card>
            </section>
          )}
        </div>
      </div>
    </>
  );
}

function MaturityCard({ stats }: { stats: WorldEngineStats }) {
  const currentIdx = STAGES.findIndex((s) => s.stage === stats.maturity.stage);
  return (
    <Card variant="info" pad="lg" className="space-y-4">
      <header>
        <Eyebrow className="text-info-deep dark:text-info">Maturity</Eyebrow>
        <h2 className="mt-1 font-display text-[22px] font-semibold leading-tight text-ink">
          {STAGES[currentIdx]?.label ?? formatText(stats.maturity.stage, "capitalize")}{" "}
          stage —{" "}
          <span className="text-ink-soft">
            {STAGES[currentIdx]?.description ?? ""}
          </span>
        </h2>
      </header>
      <div className="grid grid-cols-4 gap-2">
        {STAGES.map((s, i) => (
          <div
            key={s.stage}
            className={cn(
              "rounded-card border px-3 py-2.5",
              i <= currentIdx
                ? "border-info bg-info text-white"
                : "border-rule bg-surface text-ink-mute",
            )}
          >
            <p className="text-[11.5px] font-semibold uppercase tracking-[0.08em]">
              {s.label}
            </p>
            <p className="mt-0.5 text-[11px] opacity-80">{s.description}</p>
          </div>
        ))}
      </div>
      <div className="grid grid-cols-2 gap-6 border-t border-info/30 pt-4 md:grid-cols-4">
        <SubStat label="Assessed entities">
          {stats.maturity.assessed_entity_count}
        </SubStat>
        <SubStat label="With temporal data">
          {stats.maturity.entities_with_temporal_data}
        </SubStat>
        <SubStat label="Time depth">
          {stats.maturity.time_depth_months}mo
        </SubStat>
        <SubStat label="Active relationships">
          {stats.maturity.active_relationships}
        </SubStat>
      </div>
    </Card>
  );
}

function AlertCard({
  alert,
  onAck,
}: {
  alert: DriftAlert;
  onAck: (id: string) => void;
}) {
  const tone =
    alert.severity === "critical"
      ? "neg"
      : alert.severity === "warning"
        ? "warn"
        : "info";
  return (
    <Card pad="md" variant={tone} className="flex items-start gap-3">
      {alert.severity === "critical" ? (
        <AlertCircle size={18} className="mt-0.5 shrink-0 text-neg" />
      ) : alert.severity === "warning" ? (
        <AlertTriangle size={18} className="mt-0.5 shrink-0 text-warn" />
      ) : (
        <Sparkles size={18} className="mt-0.5 shrink-0 text-info" />
      )}
      <div className="min-w-0 flex-1">
        <div className="flex flex-wrap items-baseline gap-2">
          <Chip variant={tone} size="sm">
            {formatText(alert.alert_type, "capitalize")}
          </Chip>
          {(alert.source_signal || alert.target_signal) && (
            <Micro className="font-mono">
              {alert.source_signal}
              {alert.target_signal && ` → ${alert.target_signal}`}
            </Micro>
          )}
          <Micro className="ml-auto">{fmtRelative(alert.detected_at)}</Micro>
        </div>
        <Body className="mt-1.5 text-[13.5px]">{alert.description}</Body>
      </div>
      <Button
        type="button"
        variant="ghost"
        size="sm"
        onClick={() => onAck(alert.id)}
      >
        <Check size={13} /> Ack
      </Button>
    </Card>
  );
}

function RelRow({ rel }: { rel: DiscoveredRelationship }) {
  const lifecycleTone =
    rel.lifecycle_state === "active"
      ? "pos"
      : rel.lifecycle_state === "provisional"
        ? "info"
        : rel.lifecycle_state === "deprecated"
          ? "mute"
          : "warn";
  const arrow =
    rel.direction === "bidirectional"
      ? "↔"
      : rel.direction === "b_causes_a"
        ? "←"
        : rel.direction === "contemporaneous"
          ? "≈"
          : "→";
  return (
    <tr className="border-b border-rule last:border-0 hover:bg-surface-sunken/40">
      <td className="px-5 py-2.5 font-mono text-[12.5px] text-ink">
        {rel.source_signal}
      </td>
      <td className="px-5 py-2.5 text-center text-ink-mute">{arrow}</td>
      <td className="px-5 py-2.5 font-mono text-[12.5px] text-ink">
        {rel.target_signal}
      </td>
      <td className="px-5 py-2.5 tabular-nums text-ink-soft">
        {rel.lag_months != null ? `${rel.lag_months}mo` : "—"}
      </td>
      <td className="px-5 py-2.5 tabular-nums text-ink-soft">
        {rel.correlation_rho.toFixed(2)}
      </td>
      <td className="px-5 py-2.5 tabular-nums text-ink">
        {rel.influence_weight.toFixed(2)}
      </td>
      <td className="px-5 py-2.5">
        <Chip variant={lifecycleTone} size="sm">
          {formatText(rel.lifecycle_state, "capitalize")}
        </Chip>
      </td>
    </tr>
  );
}

function KPI({
  label,
  tone,
  children,
}: {
  label: string;
  tone?: "spot";
  children: React.ReactNode;
}) {
  return (
    <Card pad="md" variant={tone === "spot" ? "spot" : "default"}>
      <Micro className={tone === "spot" ? "text-spot-deep dark:text-spot" : ""}>
        {label}
      </Micro>
      <NumDisplay size="lg" className="mt-2 block">
        {children}
      </NumDisplay>
    </Card>
  );
}

function SubStat({
  label,
  children,
}: {
  label: string;
  children: React.ReactNode;
}) {
  return (
    <div>
      <Micro className="block">{label}</Micro>
      <p className="mt-1 text-[18px] font-semibold tabular-nums text-ink">
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

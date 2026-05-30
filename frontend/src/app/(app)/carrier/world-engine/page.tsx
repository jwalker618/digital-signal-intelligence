"use client";

import { useEffect, useMemo, useState } from "react";
import {
  AlertCircle,
  AlertTriangle,
  Check,
  Eye,
  Link as LinkIcon,
  Orbit,
  Sparkles,
  X,
  Zap,
} from "lucide-react";
import { Topbar } from "@/components/chrome/topbar";
import { WorkArea } from "@/components/ui/work-area";
import { Card } from "@/components/ui/card";
import { Chip } from "@/components/ui/chip";
import { Button } from "@/components/ui/button";
import { Eyebrow, Body, Micro, Caption } from "@/components/ui/typography";
import { PageError, PageLoading, RoleGate } from "@/components/base/pageStates";
import { CarrierShell } from "@/components/chrome/carrier-shell";
import { isCarrierRole } from "@/lib/portalPaths";
import { useAuthStore } from "@/store/authStore";
import { useDsiStore, type ApiRecord } from "@/store/dsiStore";
import { api } from "@/lib/api";
import { formatCurrency, formatText, formatPercent } from "@/lib/format";
import { fmtRelative } from "@/lib/utils";
import { cn } from "@/lib/utils";
import { tierToneOf, TIER_BAR, TIER_TEXT } from "@/lib/tier";
import type {
  DiscoveredRelationship,
  DriftAlert,
  WorldEngineStats,
} from "@/types/worldEngine";

const STAGE_LABELS: Record<string, string> = {
  seed: "Seed",
  learn: "Learn",
  emerge: "Emerge",
  simulate: "Simulate",
};

interface WorldEngineState {
  stats: WorldEngineStats | null;
  alerts: DriftAlert[];
  relationships: DiscoveredRelationship[];
  submissions: ApiRecord[];
}

export default function CarrierWorldEnginePage() {
  const user = useAuthStore((s) => s.user);
  const fetchSubmissions = useDsiStore((s) => s.fetchSubmissions);
  const submissions = useDsiStore((s) => s.submissions);
  const [data, setData] = useState<WorldEngineState | null>(null);
  const [state, setState] = useState<"loading" | "ok" | "error">("loading");
  const [err, setErr] = useState<string | null>(null);

  async function load() {
    setState("loading");
    try {
      const [stats, alertsResp, relsResp] = await Promise.all([
        api.get<WorldEngineStats>("/api/v1/world-engine/stats").catch(() => null),
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
        fetchSubmissions().catch(() => undefined),
      ]);
      setData({
        stats,
        alerts: alertsResp.alerts ?? [],
        relationships: relsResp.relationships ?? [],
        submissions: useDsiStore.getState().submissions,
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

  const resolved: WorldEngineState | null = data
    ? { ...data, submissions: submissions.length ? submissions : data.submissions }
    : null;

  const inner =
    !user ? (
      <PageLoading message="Signing in…" />
    ) : user.role && !isCarrierRole(user.role) ? (
      <RoleGate expected="carrier" />
    ) : state === "loading" ? (
      <PageLoading message="Reading the engine…" />
    ) : state === "error" ? (
      <PageError message={err ?? "Unknown error"} />
    ) : !resolved ? (
      <PageLoading />
    ) : (
      <Body0 data={resolved} onAck={ackAlert} />
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
  const { stats, alerts, relationships, submissions } = data;
  return (
    <>
      <Topbar crumbs={["Carrier Portal", "World Engine"]} />
      <WorkArea className="gap-4">
          {/* 1 — World Engine status */}
          {stats && <StatusCard stats={stats} alertCount={alerts.length} />}

          {/* 2 — Open drift alerts */}
          <Card
            pad="none"
            className="overflow-hidden"
            icon={Eye}
            header="Open drift alerts"
            headerRight={
              <Chip variant="spot" size="sm">
                {alerts.length} open
              </Chip>
            }
          >
            {alerts.length === 0 ? (
              <div className="px-5 py-8 text-center">
                <Body className="italic">No unacknowledged drift alerts.</Body>
              </div>
            ) : (
              <table className="w-full table-fixed text-[13px]">
                <thead>
                  <tr className="border-b border-rule bg-surface-sunken text-left">
                    <ColHead width="w-[18%]">Signal</ColHead>
                    <ColHead width="w-[11%]">Severity</ColHead>
                    <ColHead width="w-[15%]">Type</ColHead>
                    <ColHead width="w-[10%]">Detected</ColHead>
                    <ColHead width="w-[34%]">Summary</ColHead>
                    <ColHead width="w-[12%]">{null}</ColHead>
                  </tr>
                </thead>
                <tbody>
                  {alerts.map((a) => (
                    <AlertRow key={a.id} alert={a} onAck={onAck} />
                  ))}
                </tbody>
              </table>
            )}
          </Card>

          {/* 3 — Discovered relationships */}
          <Card
            pad="none"
            className="overflow-hidden"
            icon={LinkIcon}
            header="Discovered relationships"
            headerRight={
              <Chip variant="mute" size="sm">
                {relationships.length} recent
              </Chip>
            }
          >
            {relationships.length === 0 ? (
              <div className="px-5 py-8 text-center">
                <Body className="italic">No relationships discovered yet.</Body>
              </div>
            ) : (
              <table className="w-full table-fixed text-[12.5px]">
                <thead>
                  <tr className="border-b border-rule bg-surface-elev text-left">
                    <ColHead width="w-[19%]">Source</ColHead>
                    <ColHead width="w-[19%]">Target</ColHead>
                    <ColHead width="w-[11%]">Direction</ColHead>
                    <ColHead width="w-[8%]">Rho</ColHead>
                    <ColHead width="w-[9%]">Influence</ColHead>
                    <ColHead width="w-[10%]">Population</ColHead>
                    <ColHead width="w-[14%]">Lifecycle</ColHead>
                    <ColHead width="w-[10%]">Discovered</ColHead>
                  </tr>
                </thead>
                <tbody>
                  {relationships.slice(0, 30).map((r) => (
                    <RelRow key={r.id} rel={r} />
                  ))}
                </tbody>
              </table>
            )}
          </Card>

          {/* 4 — Portfolio overview */}
          <PortfolioCard submissions={submissions} />

          {/* 5 — Emerging scenarios + Shock simulator */}
          <div className="grid gap-4 lg:grid-cols-[1.4fr_1fr]">
            <EmergingScenariosCard />
            <ShockSimulatorCard />
          </div>
      </WorkArea>
    </>
  );
}

function StatusCard({
  stats,
  alertCount,
}: {
  stats: WorldEngineStats;
  alertCount: number;
}) {
  const m = stats.maturity;
  const stageLabel =
    STAGE_LABELS[m.stage] ?? formatText(m.stage, "capitalize");
  return (
    <Card variant="info" pad="lg" className="space-y-4">
      <div className="flex items-baseline justify-between gap-4">
        <div>
          <Eyebrow className="text-info-deep dark:text-info">World Engine</Eyebrow>
          <h2 className="mt-1.5 flex items-center gap-2 font-display text-[22px] font-semibold leading-tight text-ink">
            <Orbit size={20} className="text-info" />
            Status of the assessing model
          </h2>
        </div>
        <Chip variant="info" size="sm">
          {m.assessed_entity_count.toLocaleString()} entities
        </Chip>
      </div>
      <div className="grid gap-3 sm:grid-cols-2 md:grid-cols-4">
        <StatCell
          label="Maturity stage"
          value={stageLabel}
          sub={`${m.time_depth_months.toFixed(1)} months of data`}
          tone="info"
        />
        <StatCell
          label="Active relationships"
          value={m.active_relationships}
          sub={`${m.provisional_relationships} provisional · ${m.candidate_relationships} candidate`}
        />
        <StatCell
          label="Open drift alerts"
          value={alertCount}
          sub="Unacknowledged"
          tone={alertCount > 0 ? "neg" : "pos"}
        />
        <StatCell
          label="Assessed entities"
          value={m.assessed_entity_count.toLocaleString()}
          sub={`${m.entities_with_temporal_data.toLocaleString()} with temporal data`}
        />
      </div>
    </Card>
  );
}

function PortfolioCard({ submissions }: { submissions: ApiRecord[] }) {
  const p = useMemo(() => {
    const total = submissions.length;
    let premium = 0;
    let scoreSum = 0;
    let scoreCount = 0;
    let approve = 0;
    let refer = 0;
    const bySector = new Map<string, number>();
    for (const s of submissions) {
      premium += s.final_premium ?? s.recommended_premium ?? 0;
      const sc = s.final_composite_score ?? s.composite_score;
      if (typeof sc === "number") {
        scoreSum += sc;
        scoreCount++;
      }
      const dec = (s.decision ?? "").toLowerCase();
      if (dec === "approve") approve++;
      else if (dec === "refer") refer++;
      const sector = s.industry ?? s.sector;
      if (sector) {
        const name = String(sector);
        bySector.set(name, (bySector.get(name) ?? 0) + 1);
      }
    }
    const sectors = [...bySector.entries()]
      .map(([name, n]) => ({ name, n, pct: total > 0 ? (n / total) * 100 : 0 }))
      .sort((a, b) => b.n - a.n)
      .slice(0, 6);
    const tierCounts = [1, 2, 3, 4, 5].map((t) => ({
      t,
      n: submissions.filter((s) => (s.final_tier ?? s.tier) === t).length,
    }));
    return {
      total,
      premium,
      avgScore: scoreCount > 0 ? Math.round(scoreSum / scoreCount) : null,
      approvalRate: total > 0 ? approve / total : 0,
      referralRate: total > 0 ? refer / total : 0,
      sectors,
      tierCounts,
      maxTier: Math.max(...tierCounts.map((x) => x.n), 1),
    };
  }, [submissions]);

  return (
    <Card pad="lg" className="space-y-5">
      <div>
        <Eyebrow>Portfolio overview</Eyebrow>
        <h3 className="mt-1.5 font-display text-[17px] font-semibold leading-tight text-ink">
          {p.total} submissions in flight
        </h3>
      </div>
      <div className="grid gap-4 sm:grid-cols-3 md:grid-cols-5">
        <StatCell label="Submissions" value={p.total} />
        <StatCell label="Aggregate premium" value={formatCurrency(p.premium)} />
        <StatCell
          label="Avg score"
          value={p.avgScore ?? "—"}
          tone={p.avgScore != null ? "info" : undefined}
        />
        <StatCell
          label="Approval rate"
          value={formatPercent(p.approvalRate, 0)}
          tone="pos"
        />
        <StatCell
          label="Referral rate"
          value={formatPercent(p.referralRate, 0)}
          tone="spot"
        />
      </div>
      <div className="grid gap-6 md:grid-cols-2">
        {/* Tier distribution */}
        <div>
          <Micro className="mb-2 block">Tier distribution</Micro>
          <div className="flex h-[110px] items-end gap-2.5">
            {p.tierCounts.map(({ t, n }) => {
              const tone = tierToneOf(t);
              return (
                <div key={t} className="flex flex-1 flex-col items-center gap-1">
                  <span className={cn("text-[14px] font-semibold tabular-nums", TIER_TEXT[tone])}>
                    {n}
                  </span>
                  <div
                    className={cn("w-full rounded-t", TIER_BAR[tone])}
                    style={{ height: `${Math.max(4, (n / p.maxTier) * 78)}px` }}
                  />
                  <Micro className="text-[10px]">T{t}</Micro>
                </div>
              );
            })}
          </div>
        </div>
        {/* Sector concentration */}
        <div>
          <Micro className="mb-2 block">Sector concentration</Micro>
          {p.sectors.length === 0 ? (
            <Caption className="italic">Sector data not available.</Caption>
          ) : (
            <ul className="flex flex-col gap-1.5">
              {p.sectors.map((s) => (
                <li key={s.name}>
                  <div className="flex items-baseline justify-between text-[12px]">
                    <span className="truncate text-ink">{s.name}</span>
                    <span className="tabular-nums text-ink-soft">
                      {s.n} ({Math.round(s.pct)}%)
                    </span>
                  </div>
                  <div className="mt-0.5 h-1.5 overflow-hidden rounded-full bg-surface-sunken">
                    <div className="h-full bg-info" style={{ width: `${s.pct}%` }} />
                  </div>
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>
    </Card>
  );
}

/* Emerging scenarios — World Engine surfaces continuously-monitored
 * portfolio scenarios generated from signals. Forward-looking product
 * surface (no dedicated endpoint yet); representative scenarios shown. */
const EMERGING_SCENARIOS = [
  {
    id: "sc-1",
    name: "Cyber ransomware wave — manufacturing",
    likelihood: 0.62,
    likelihoodLabel: "Elevated",
    scope: "14 policies",
    magnitude: -38,
    horizon: "3–6 mo",
    source: "claims.history + cyber.posture drift",
  },
  {
    id: "sc-2",
    name: "NE windstorm season — property aggregation",
    likelihood: 0.41,
    likelihoodLabel: "Watch",
    scope: "9 policies",
    magnitude: -26,
    horizon: "Q3",
    source: "exposure geo-concentration",
  },
  {
    id: "sc-3",
    name: "D&O securities-claim uptick — tech",
    likelihood: 0.78,
    likelihoodLabel: "High",
    scope: "6 policies",
    magnitude: -19,
    horizon: "6–12 mo",
    source: "market signals + financial drift",
  },
];

function likelihoodTone(label: string): "neg" | "warn" | "info" {
  return label === "High" ? "neg" : label === "Elevated" ? "warn" : "info";
}

function EmergingScenariosCard() {
  return (
    <Card pad="lg">
      <div className="mb-3 flex items-baseline justify-between">
        <div>
          <Eyebrow>Emerging scenarios</Eyebrow>
          <h3 className="mt-1.5 font-display text-[17px] font-semibold leading-tight text-ink">
            Continuously monitored
          </h3>
        </div>
        <Caption>Generated from portfolio + signals</Caption>
      </div>
      <div className="flex flex-col gap-2.5">
        {EMERGING_SCENARIOS.map((sc) => {
          const tone = likelihoodTone(sc.likelihoodLabel);
          return (
            <div
              key={sc.id}
              className="grid grid-cols-[1fr_auto] items-center gap-4 rounded-card border border-rule bg-surface-elev px-3.5 py-3"
            >
              <div>
                <div className="mb-1 flex items-center gap-2">
                  <span className="text-[13px] font-bold">{sc.name}</span>
                  <Chip variant={tone} size="sm">
                    {Math.round(sc.likelihood * 100)}% · {sc.likelihoodLabel}
                  </Chip>
                </div>
                <Caption className="text-[12px]">
                  Scope: <strong>{sc.scope}</strong> · Magnitude:{" "}
                  <strong>{sc.magnitude} pts</strong> · Horizon: {sc.horizon} ·
                  Source: {sc.source}
                </Caption>
              </div>
              <button
                type="button"
                className="inline-flex items-center gap-1.5 rounded-md bg-spot px-3 py-2 text-[12px] font-semibold text-white hover:opacity-90"
              >
                <Zap size={13} /> Simulate
              </button>
            </div>
          );
        })}
      </div>
    </Card>
  );
}

function ShockSimulatorCard() {
  return (
    <Card variant="spot" pad="lg">
      <div className="flex items-baseline justify-between">
        <div>
          <Eyebrow className="text-spot-deep dark:text-spot">Shock simulator</Eyebrow>
          <h3 className="mt-1.5 font-display text-[17px] font-semibold leading-tight text-ink">
            Stress-test the portfolio
          </h3>
        </div>
        <Chip variant="spot" size="sm">
          1 active
        </Chip>
      </div>
      <div className="mt-3.5 flex flex-col gap-3">
        <div>
          <Micro className="mb-1 block">Active shocks</Micro>
          <div className="flex items-center gap-2 rounded-md bg-surface-elev px-2.5 py-2 text-[12px]">
            <Zap size={12} className="text-spot" />
            <span className="font-semibold">Hurricane Wendell</span>
            <Caption>property · −32 pts</Caption>
            <X size={12} className="ml-auto text-ink-mute" />
          </div>
        </div>
        <div className="border-t border-rule pt-3">
          <Micro className="mb-2 block">Impact preview</Micro>
          <div className="grid grid-cols-2 gap-3">
            <ShockStat label="Affected" value="3" tone="text-spot" />
            <ShockStat label="Tier migrations" value="2" tone="text-warn" />
            <ShockStat label="Decision changes" value="1" tone="text-ink" />
            <ShockStat label="Premium impact" value="+$84k" tone="text-neg" />
          </div>
        </div>
        <button
          type="button"
          className="mt-1 inline-flex items-center justify-center gap-1.5 rounded-md bg-spot px-3 py-2.5 text-[13px] font-semibold text-white hover:opacity-90"
        >
          <Zap size={13} /> Open full analysis →
        </button>
      </div>
    </Card>
  );
}

function ShockStat({ label, value, tone }: { label: string; value: string; tone: string }) {
  return (
    <div>
      <Micro>{label}</Micro>
      <div className={cn("font-mono text-[22px] font-semibold tabular-nums", tone)}>
        {value}
      </div>
    </div>
  );
}

function AlertRow({
  alert,
  onAck,
}: {
  alert: DriftAlert;
  onAck: (id: string) => void;
}) {
  const sevTone =
    alert.severity === "critical"
      ? "neg"
      : alert.severity === "warning"
        ? "warn"
        : "info";
  const SevIcon =
    alert.severity === "critical"
      ? AlertCircle
      : alert.severity === "warning"
        ? AlertTriangle
        : Sparkles;
  return (
    <tr className="border-b border-rule last:border-0 align-top hover:bg-surface-sunken/40">
      <td className="px-5 py-3 font-mono text-[12px] text-ink">
        {alert.source_signal ?? "—"}
        {alert.target_signal && (
          <span className="text-ink-mute"> → {alert.target_signal}</span>
        )}
      </td>
      <td className="px-5 py-3">
        <span
          className={cn(
            "inline-flex items-center gap-1 font-semibold capitalize",
            sevTone === "neg"
              ? "text-neg"
              : sevTone === "warn"
                ? "text-warn"
                : "text-info",
          )}
        >
          <SevIcon size={13} />
          {alert.severity}
        </span>
      </td>
      <td className="px-5 py-3 capitalize text-ink-soft">
        {formatText(alert.alert_type, "capitalize")}
      </td>
      <td className="px-5 py-3">
        <Micro>{fmtRelative(alert.detected_at)}</Micro>
      </td>
      <td className="px-5 py-3 text-ink">{alert.description}</td>
      <td className="px-5 py-3 text-right">
        <Button
          type="button"
          variant="ghost"
          size="sm"
          onClick={() => onAck(alert.id)}
        >
          <Check size={13} /> Acknowledge
        </Button>
      </td>
    </tr>
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
          : "spot";
  const direction =
    rel.direction === "bidirectional"
      ? "Bidirectional"
      : rel.direction === "b_causes_a"
        ? "Target → Source"
        : rel.direction === "contemporaneous"
          ? "Contemporaneous"
          : "Source → Target";
  return (
    <tr className="border-b border-rule last:border-0 hover:bg-surface-sunken/40">
      <td className="px-5 py-2.5 truncate font-mono text-ink">
        {rel.source_signal}
      </td>
      <td className="px-5 py-2.5 truncate font-mono text-ink">
        {rel.target_signal}
      </td>
      <td className="px-5 py-2.5">
        <Caption>{direction}</Caption>
      </td>
      <td className="px-5 py-2.5 font-semibold tabular-nums text-ink">
        {rel.correlation_rho.toFixed(2)}
      </td>
      <td className="px-5 py-2.5 tabular-nums text-ink-soft">
        {Math.round(rel.influence_weight * 100)}%
      </td>
      <td className="px-5 py-2.5 tabular-nums text-ink-soft">
        {rel.population_size}
      </td>
      <td className="px-5 py-2.5">
        <Chip variant={lifecycleTone} size="sm">
          {formatText(rel.lifecycle_state, "capitalize")}
        </Chip>
      </td>
      <td className="px-5 py-2.5">
        <Micro>{rel.created_at ? fmtRelative(rel.created_at) : "—"}</Micro>
      </td>
    </tr>
  );
}

function StatCell({
  label,
  value,
  sub,
  tone,
}: {
  label: string;
  value: React.ReactNode;
  sub?: string;
  tone?: "info" | "pos" | "spot" | "neg";
}) {
  const valueTone =
    tone === "pos"
      ? "text-pos"
      : tone === "spot"
        ? "text-spot"
        : tone === "neg"
          ? "text-neg"
          : tone === "info"
            ? "text-info"
            : "text-ink";
  return (
    <div className="rounded-card border border-rule bg-surface px-3.5 py-3">
      <Micro className="block">{label}</Micro>
      <p className={cn("mt-1 text-[22px] font-semibold tabular-nums", valueTone)}>
        {value}
      </p>
      {sub && <Caption className="mt-0.5 block">{sub}</Caption>}
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
      className={cn(
        "px-5 py-2.5 text-[11px] font-semibold uppercase tracking-[0.08em] text-ink-mute",
        width,
      )}
    >
      {children}
    </th>
  );
}

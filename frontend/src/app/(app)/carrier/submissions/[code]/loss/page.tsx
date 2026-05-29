"use client";

import {
  Layers,
  ShieldAlert,
  Target,
  TrendingUp,
} from "lucide-react";
import { Card } from "@/components/ui/card";
import { WorkArea } from "@/components/ui/work-area";
import { Body, Micro } from "@/components/ui/typography";
import { KpiSnug } from "@/components/ui/kpi-snug";
import { PageLoading } from "@/components/base/pageStates";
import { useDsiStore, type ApiRecord } from "@/store/dsiStore";
import { useEnsureFetched } from "@/store/useEnsureFetched";
import { SubjectMarker } from "@/components/charts/subject-marker";

/* ============================================================
 * Loss Assessment — mirrors reim_wb_b.jsx WbLoss (section 04).
 *
 * Three stacked rows:
 *   1. Active Submission · Loss Profile — 8 KPIs
 *   2. Two-col: Freq vs Severity matrix (scatter) + Loss Trajectory
 *   3. Loss Group Scores — 2-col grid of group cards (freq + sev bars)
 * ============================================================ */

type ScatterPoint = {
  loss_propensity_score?: number;
  severity_propensity_score?: number;
  decision?: string;
  entity_name?: string;
};

export default function LossAssessmentPage() {
  const sub = useDsiStore((s) => s.activeSubmission) as ApiRecord | null;
  const ver = useDsiStore((s) => s.activeVersion) as ApiRecord | null;
  const fetchLoss = useDsiStore((s) => s.fetchLossAnalytics);
  const trendDistribution = useDsiStore((s) => s.lossTrendDistribution);
  const scatter = useDsiStore((s) => s.lossScatterData);

  const coverage = sub?.coverage as string | undefined;
  useEnsureFetched(coverage, fetchLoss);

  if (!ver) {
    return (
      <>
        <PageLoading />
      </>
    );
  }

  const propensityBand = strOrNull(ver.loss_propensity_band);
  const severityBand = strOrNull(ver.severity_propensity_band);
  const combinedMod = numOrNull(ver.loss_combined_modifier);
  const freqMult = numOrNull(ver.loss_frequency_multiplier);
  const sevMult = numOrNull(ver.loss_severity_multiplier);
  const confidence = numOrNull(ver.loss_confidence);
  const cohortName = strOrNull(ver.loss_cohort_name);
  const freqVelocity = numOrNull(ver.loss_frequency_velocity);
  const sevVelocity = numOrNull(ver.loss_severity_velocity);
  const trendDirection = strOrNull(ver.loss_trend_direction);
  const propensityScore = numOrNull(ver.loss_propensity_score);
  const severityScore = numOrNull(ver.severity_propensity_score);

  // Combined score velocity = average of freq + sev velocities when available.
  const combinedVelocity =
    freqVelocity != null && sevVelocity != null
      ? (freqVelocity + sevVelocity) / 2
      : freqVelocity ?? sevVelocity;

  // Loss-related group scores. The MV row keeps these on `group_scores`
  // JSONB; we surface every group that has any loss-relevant signal data
  // (freq or sev scores). Falls back to all groups when not differentiated.
  const groupScores = (ver.group_scores as ApiRecord | undefined) ?? {};
  const lossGroups = Object.entries(groupScores).map(([id, raw]) => {
    const v = (raw as ApiRecord) ?? {};
    return {
      id,
      freq: numOrNull(v.frequency_score ?? v.score),
      sev: numOrNull(v.severity_score ?? v.score),
      conf: numOrNull(v.confidence),
    };
  });

  const cohortPoints: ScatterPoint[] = Array.isArray(scatter)
    ? (scatter as ScatterPoint[])
    : [];

  return (
    <>
      <WorkArea>
        {/* ─── 1. Loss Profile KPIs (8 across) ─────────────── */}
        <Card header="Active Submission · Loss Profile" icon={Target} pad="md">
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-4 lg:grid-cols-8">
            <KpiSnug
              label="Propensity band"
              value={propensityBand ? propensityBand.toUpperCase() : "—"}
              tone={
                propensityBand && /low|very_low/i.test(propensityBand) ? "pos" : "default"
              }
            />
            <KpiSnug
              label="Severity band"
              value={severityBand ? severityBand.toUpperCase() : "—"}
            />
            <KpiSnug
              label="Combined modifier"
              value={combinedMod != null ? `${combinedMod.toFixed(2)}x` : "—"}
              tone={combinedMod != null && combinedMod < 1 ? "pos" : "default"}
            />
            <KpiSnug
              label="Freq multiplier"
              value={freqMult != null ? `${freqMult.toFixed(2)}x` : "—"}
            />
            <KpiSnug
              label="Sev multiplier"
              value={sevMult != null ? `${sevMult.toFixed(2)}x` : "—"}
            />
            <KpiSnug
              label="Model confidence"
              value={confidence != null ? `${(confidence * 100).toFixed(0)}%` : "—"}
            />
            <KpiSnug label="Cohort" value={cohortName ?? "—"} />
            <KpiSnug
              label="Score velocity"
              value={
                combinedVelocity != null
                  ? `${combinedVelocity > 0 ? "+" : ""}${combinedVelocity.toFixed(1)}`
                  : "—"
              }
              tone={combinedVelocity != null && combinedVelocity < 0 ? "pos" : "default"}
            />
          </div>
        </Card>

        {/* ─── 2. Matrix + Trajectory ──────────────────────── */}
        <div className="grid gap-3.5 lg:grid-cols-[1.6fr_1fr]">
          <Card
            header="Frequency vs Severity Matrix"
            icon={ShieldAlert}
            pad="md"
          >
            <FreqSevScatter
              points={cohortPoints}
              subject={
                propensityScore != null && severityScore != null
                  ? { x: propensityScore, y: severityScore }
                  : null
              }
            />
            <div className="mt-2 flex gap-3 text-[11px]">
              <LegendDot tone="pos" label="Approved" />
              <LegendDot tone="warn" label="Referred" />
              <LegendDot tone="neg" label="Declined" />
            </div>
          </Card>

          <Card header="Loss Trajectory" icon={TrendingUp} pad="md">
            <TrajectoryRow
              label="Overall"
              trend={trendDirection ?? "—"}
              delta={combinedVelocity}
            />
            <TrajectoryRow
              label="Frequency"
              trend={velocityTrend(freqVelocity)}
              delta={freqVelocity}
            />
            <TrajectoryRow
              label="Severity"
              trend={velocityTrend(sevVelocity)}
              delta={sevVelocity}
            />
            <TrendDistribution rows={trendDistribution} />
          </Card>
        </div>

        {/* ─── 3. Loss Group Scores ────────────────────────── */}
        <Card header="Loss Group Scores" icon={Layers} pad="md">
          {lossGroups.length === 0 ? (
            <Body className="italic">No loss group scores on this version.</Body>
          ) : (
            <div className="grid gap-4 md:grid-cols-2">
              {lossGroups.map((g) => (
                <div
                  key={g.id}
                  className="rounded-card border border-rule bg-surface-elev px-3.5 py-2.5"
                >
                  <div className="mb-1.5 flex justify-between">
                    <span className="font-mono text-[12px] font-semibold">{g.id}</span>
                    {g.conf != null && (
                      <Micro>{Math.round(g.conf * 100)}% conf</Micro>
                    )}
                  </div>
                  <div className="mb-1">
                    <Micro>Freq</Micro>
                    <div className="mt-0.5 h-1 overflow-hidden rounded-sm bg-rule">
                      <div
                        className="h-full bg-pos"
                        style={{ width: `${pctBar(g.freq)}%` }}
                      />
                    </div>
                  </div>
                  <div>
                    <Micro>Sev</Micro>
                    <div className="mt-0.5 h-1 overflow-hidden rounded-sm bg-rule">
                      <div
                        className="h-full bg-info"
                        style={{ width: `${pctBar(g.sev)}%` }}
                      />
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </Card>
      </WorkArea>
    </>
  );
}

/* ──────────────────── sub-components ──────────────────── */

function FreqSevScatter({
  points,
  subject,
}: {
  points: ScatterPoint[];
  subject: { x: number; y: number } | null;
}) {
  const W = 560;
  const H = 280;
  const xToPx = (x: number) => 40 + (x / 100) * (W - 60);
  const yToPx = (y: number) => H - 32 - (y / 100) * (H - 64);
  const color = (d?: string) =>
    d === "approve" ? "var(--color-pos)" : d === "refer" ? "var(--color-warn)" : "var(--color-neg)";

  return (
    <svg viewBox={`0 0 ${W} ${H}`} width="100%" className="block">
      <line x1={40} y1={H - 32} x2={W - 20} y2={H - 32} stroke="var(--color-rule)" />
      <line x1={40} y1={20} x2={40} y2={H - 32} stroke="var(--color-rule)" />
      {[0, 25, 50, 75, 100].map((v) => (
        <g key={`x-${v}`}>
          <line
            x1={xToPx(v)}
            y1={H - 32}
            x2={xToPx(v)}
            y2={H - 28}
            stroke="var(--color-ink-mute)"
          />
          <text
            x={xToPx(v)}
            y={H - 14}
            textAnchor="middle"
            style={{ font: "10px IBM Plex Sans", fill: "var(--color-ink-mute)" }}
          >
            {v}
          </text>
        </g>
      ))}
      {[0, 25, 50, 75, 100].map((v) => (
        <g key={`y-${v}`}>
          <line x1={36} y1={yToPx(v)} x2={40} y2={yToPx(v)} stroke="var(--color-ink-mute)" />
          <text
            x={32}
            y={yToPx(v) + 3}
            textAnchor="end"
            style={{ font: "10px IBM Plex Sans", fill: "var(--color-ink-mute)" }}
          >
            {v}
          </text>
        </g>
      ))}
      <text
        x={W / 2}
        y={H - 2}
        textAnchor="middle"
        style={{ font: "10.5px IBM Plex Sans", fill: "var(--color-ink-soft)" }}
      >
        Loss propensity score →
      </text>
      <text
        x={14}
        y={H / 2}
        textAnchor="middle"
        transform={`rotate(-90, 14, ${H / 2})`}
        style={{ font: "10.5px IBM Plex Sans", fill: "var(--color-ink-soft)" }}
      >
        ← Severity score
      </text>

      {points.map((p, i) => {
        const x = p.loss_propensity_score;
        const y = p.severity_propensity_score;
        if (x == null || y == null) return null;
        return (
          <circle
            key={i}
            cx={xToPx(x)}
            cy={yToPx(y)}
            r={4}
            fill={color(p.decision)}
            opacity={0.7}
          />
        );
      })}

      {subject && (
        <SubjectMarker
          cx={xToPx(subject.x)}
          cy={yToPx(subject.y)}
          label={`YOU · ${Math.round(subject.x)}/${Math.round(subject.y)}`}
        />
      )}
    </svg>
  );
}

function LegendDot({ tone, label }: { tone: "pos" | "warn" | "neg"; label: string }) {
  const bg = tone === "pos" ? "bg-pos" : tone === "warn" ? "bg-warn" : "bg-neg";
  return (
    <span className="flex items-center gap-1.5">
      <span className={`h-2 w-2 rounded-full ${bg}`} />
      {label}
    </span>
  );
}

function TrajectoryRow({
  label,
  trend,
  delta,
}: {
  label: string;
  trend: string;
  delta: number | null;
}) {
  const tone = delta == null ? "text-ink" : delta < 0 ? "text-pos" : delta > 0 ? "text-warn" : "text-ink";
  return (
    <div className="mb-2 rounded-card border border-rule bg-surface-elev px-3.5 py-3">
      <Micro className="mb-1 block">{label}</Micro>
      <div className="flex items-baseline justify-between">
        <span className="text-[14px] font-bold capitalize">{trend}</span>
        <span className={`text-[14px] font-bold tabular-nums ${tone}`}>
          {delta != null ? `${delta > 0 ? "+" : ""}${delta.toFixed(1)}` : "—"}
        </span>
      </div>
    </div>
  );
}

type TrendCount = {
  improving?: number;
  stable?: number;
  deteriorating?: number;
  cohort_size?: number;
};

function TrendDistribution({ rows }: { rows: unknown }) {
  // The backend returns either a single row (totals) or per-cohort rows.
  // Aggregate when there are multiple.
  const list: TrendCount[] = Array.isArray(rows) ? (rows as TrendCount[]) : [];
  if (list.length === 0) return null;
  let improving = 0;
  let stable = 0;
  let deteriorating = 0;
  let total = 0;
  for (const r of list) {
    improving += r.improving ?? 0;
    stable += r.stable ?? 0;
    deteriorating += r.deteriorating ?? 0;
    total += r.cohort_size ?? (r.improving ?? 0) + (r.stable ?? 0) + (r.deteriorating ?? 0);
  }
  return (
    <Micro className="mt-2.5 block text-[11.5px]">
      Book-wide trend ({total} peers):{" "}
      <strong className="text-pos">{improving} improving</strong> ·{" "}
      <strong>{stable} stable</strong> ·{" "}
      <strong className="text-neg">{deteriorating} deteriorating</strong>.
    </Micro>
  );
}

/* ──────────────────── helpers ──────────────────── */

function velocityTrend(v: number | null): string {
  if (v == null) return "—";
  if (v < -0.5) return "Improving";
  if (v > 0.5) return "Deteriorating";
  return "Stable";
}

function pctBar(v: number | null): number {
  if (v == null) return 0;
  return Math.max(0, Math.min(100, v));
}

function numOrNull(v: unknown): number | null {
  if (v == null) return null;
  const n = Number(v);
  return Number.isFinite(n) ? n : null;
}

function strOrNull(v: unknown): string | null {
  if (v == null) return null;
  const s = String(v).trim();
  return s.length > 0 ? s : null;
}

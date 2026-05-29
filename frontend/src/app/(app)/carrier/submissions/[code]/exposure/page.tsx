"use client";

import { Gauge, ScatterChart, Puzzle, Target } from "lucide-react";
import { WorkbenchTopbar } from "@/components/chrome/workbench-topbar";
import { Card } from "@/components/ui/card";
import { WorkArea } from "@/components/ui/work-area";
import { Body, Micro } from "@/components/ui/typography";
import { KpiSnug } from "@/components/ui/kpi-snug";
import { PageLoading } from "@/components/base/pageStates";
import { useDsiStore, type ApiRecord } from "@/store/dsiStore";
import { useEnsureFetched } from "@/store/useEnsureFetched";
import { formatCurrency, formatText } from "@/lib/format";

/* ============================================================
 * Exposure Assessment — mirrors reim_wb_c.jsx WbExposure.
 *
 * Three stacked rows:
 *   1. Exposure profile — 7 KPIs
 *   2. Two-col: Band position + Components
 *   3. Exposure vs overall score — scatter
 * ============================================================ */

type ScatterPoint = {
  exposure_size_score?: number;
  composite_score?: number;
  decision?: string;
};

export default function ExposureAssessmentPage() {
  const sub = useDsiStore((s) => s.activeSubmission) as ApiRecord | null;
  const ver = useDsiStore((s) => s.activeVersion) as ApiRecord | null;
  const fetch_ = useDsiStore((s) => s.fetchExposureAnalytics);
  const scatter = useDsiStore((s) => s.exposureScatterData);

  const coverage = sub?.coverage as string | undefined;
  useEnsureFetched(coverage, fetch_);
  const loading = !Array.isArray(scatter) || scatter.length === 0;

  if (!ver) {
    return (
      <>
        <WorkbenchTopbar activeTabLabel="Exposure Assessment" />
        <PageLoading />
      </>
    );
  }

  const value = numOrNull(ver.exposure_value);
  const band = strOrNull(ver.exposure_band_label);
  const sizeScore = numOrNull(ver.exposure_size_score);
  const complexity = numOrNull(ver.exposure_complexity_score);
  const modifier = numOrNull(ver.exposure_modifier);
  const method = strOrNull(ver.exposure_assessment_method);
  const finalTier = numOrNull(ver.final_tier);
  const tierLabel = strOrNull(ver.tier_label);

  const boundaries = (ver.exposure_band_boundaries as ApiRecord | undefined) ?? {};
  const floor = numOrNull(boundaries.min_value);
  const ceiling = numOrNull(boundaries.max_value);
  const bandPct =
    value != null && floor != null && ceiling != null && ceiling > floor
      ? Math.max(0, Math.min(1, (value - floor) / (ceiling - floor)))
      : null;

  const cohortPoints: ScatterPoint[] = Array.isArray(scatter)
    ? (scatter as ScatterPoint[])
    : [];

  return (
    <>
      <WorkbenchTopbar activeTabLabel="Exposure Assessment" />
      <WorkArea>
        {/* ─── 1. Exposure profile (7 KPIs) ─────────────────── */}
        <Card header="Exposure profile" icon={Target} pad="md">
          <div className="grid grid-cols-2 gap-3.5 sm:grid-cols-4 lg:grid-cols-7">
            <KpiSnug
              label="Exposure value"
              value={value != null ? formatCurrencyShort(value) : "—"}
              tone="info"
            />
            <KpiSnug
              label="Band"
              value={band ? formatText(band, "capitalize") : "—"}
              delta={
                floor != null && ceiling != null ? (
                  <Micro>
                    {formatCurrencyShort(floor)} – {formatCurrencyShort(ceiling)}
                  </Micro>
                ) : undefined
              }
            />
            <KpiSnug
              label="Size score"
              value={sizeScore != null ? sizeScore.toFixed(0) : "—"}
            />
            <KpiSnug
              label="Complexity"
              value={complexity != null ? complexity.toFixed(0) : "—"}
            />
            <KpiSnug
              label="Modifier"
              value={modifier != null ? `${modifier.toFixed(2)}x` : "—"}
            />
            <KpiSnug
              label="Method"
              value={
                method ? formatText(method.replace(/_/g, " "), "capitalize") : "—"
              }
            />
            <KpiSnug
              label="Final tier"
              value={
                finalTier != null
                  ? `T${finalTier}${tierLabel ? ` · ${tierLabel}` : ""}`
                  : "—"
              }
            />
          </div>
        </Card>

        {/* ─── 2. Band position + Components ────────────────── */}
        <div className="grid gap-3.5 md:grid-cols-2">
          <Card header="Band position" icon={Gauge} pad="md">
            <Micro className="mb-3.5 block">
              Where you sit within the {band ? formatText(band, "capitalize").toLowerCase() : "band"}.
            </Micro>
            <div className="relative h-9">
              <div className="absolute inset-x-0 top-3.5 h-2 rounded-sm border border-rule bg-surface-sunken" />
              {bandPct != null && (
                <>
                  <div
                    className="absolute top-0 bottom-0 w-0.5 -translate-x-1/2 bg-info"
                    style={{ left: `${bandPct * 100}%` }}
                  />
                  <div
                    className="absolute -top-5 -translate-x-1/2 whitespace-nowrap text-[11px] font-bold text-info"
                    style={{ left: `${bandPct * 100}%` }}
                  >
                    {value != null ? formatCurrencyShort(value) : ""}
                  </div>
                </>
              )}
            </div>
            <div className="mt-2 flex justify-between text-[11px] text-ink-mute">
              <span>{floor != null ? `${formatCurrencyShort(floor)} floor` : "—"}</span>
              <span>{ceiling != null ? `${formatCurrencyShort(ceiling)} ceiling` : "—"}</span>
            </div>
            <div className="mt-4 grid grid-cols-3 gap-3 border-t border-rule pt-3.5">
              <KpiSnug
                label="Band percentile"
                value={bandPct != null ? `${(bandPct * 100).toFixed(0)}%` : "—"}
              />
              <KpiSnug
                label="Below ceiling"
                value={
                  value != null && ceiling != null
                    ? formatCurrencyShort(ceiling - value)
                    : "—"
                }
              />
              <KpiSnug
                label="Above floor"
                value={
                  value != null && floor != null
                    ? formatCurrencyShort(value - floor)
                    : "—"
                }
              />
            </div>
          </Card>

          <Card header="Components" icon={Puzzle} pad="md">
            <ComponentRow
              name="Size"
              weight={0.7}
              score={sizeScore}
              band={sizeScore != null ? scoreBand(sizeScore) : "—"}
              mod={null}
            />
            <ComponentRow
              name="Complexity"
              weight={0.3}
              score={complexity}
              band={complexity != null ? scoreBand(complexity) : "—"}
              mod={null}
            />
            <div className="mt-2 flex justify-between border-t border-ink-soft pt-3">
              <span className="text-[13.5px] font-bold">Combined modifier</span>
              <span className="font-mono text-[17px] font-bold text-info-deep dark:text-info tabular-nums">
                {modifier != null ? `${modifier.toFixed(2)}x` : "—"}
              </span>
            </div>
          </Card>
        </div>

        {/* ─── 3. Exposure vs overall score scatter ────────── */}
        <Card header="Exposure vs overall score" icon={ScatterChart} pad="md">
          {loading && cohortPoints.length === 0 ? (
            <Body className="italic">Loading cohort…</Body>
          ) : (
            <ExposureScatter
              points={cohortPoints}
              subject={
                sizeScore != null && numOrNull(ver.final_composite_score) != null
                  ? { x: sizeScore, y: Number(ver.final_composite_score) }
                  : null
              }
            />
          )}
        </Card>
      </WorkArea>
    </>
  );
}

function ComponentRow({
  name,
  weight,
  score,
  band,
  mod,
}: {
  name: string;
  weight: number;
  score: number | null;
  band: string;
  mod: number | null;
}) {
  return (
    <div className="border-b border-rule py-3">
      <div className="mb-2 flex justify-between">
        <span className="text-[13px] font-semibold">{name}</span>
        <Micro>Weight {weight.toFixed(2)}</Micro>
      </div>
      <div className="grid grid-cols-3 gap-2.5">
        <div>
          <Micro>Score</Micro>
          <div className="font-semibold tabular-nums">
            {score != null ? score.toFixed(0) : "—"}
          </div>
        </div>
        <div>
          <Micro>Band</Micro>
          <div className="font-semibold">{band}</div>
        </div>
        <div>
          <Micro>Modifier</Micro>
          <div className="font-semibold tabular-nums">
            {mod != null ? `${mod.toFixed(2)}x` : "—"}
          </div>
        </div>
      </div>
    </div>
  );
}

function ExposureScatter({
  points,
  subject,
}: {
  points: ScatterPoint[];
  subject: { x: number; y: number } | null;
}) {
  const W = 980;
  const H = 220;
  const xToPx = (x: number) => 50 + (x / 100) * (W - 70);
  const yToPx = (y: number) => H - 28 - ((y - 400) / 600) * (H - 56);
  const color = (d?: string) =>
    d === "approve"
      ? "var(--color-pos)"
      : d === "refer"
        ? "var(--color-warn)"
        : "var(--color-neg)";
  return (
    <svg viewBox={`0 0 ${W} ${H}`} width="100%" className="block">
      <line x1={50} y1={H - 28} x2={W - 20} y2={H - 28} stroke="var(--color-rule)" />
      <line x1={50} y1={20} x2={50} y2={H - 28} stroke="var(--color-rule)" />
      {[0, 25, 50, 75, 100].map((v) => (
        <text
          key={v}
          x={xToPx(v)}
          y={H - 12}
          textAnchor="middle"
          style={{ font: "10px IBM Plex Sans", fill: "var(--color-ink-mute)" }}
        >
          {v}
        </text>
      ))}
      {[400, 600, 800, 1000].map((v) => (
        <text
          key={v}
          x={42}
          y={yToPx(v) + 3}
          textAnchor="end"
          style={{ font: "10px IBM Plex Sans", fill: "var(--color-ink-mute)" }}
        >
          {v}
        </text>
      ))}
      <text
        x={W / 2}
        y={H}
        textAnchor="middle"
        style={{ font: "10.5px IBM Plex Sans", fill: "var(--color-ink-soft)" }}
      >
        Exposure magnitude score →
      </text>
      <text
        x={16}
        y={H / 2}
        transform={`rotate(-90, 16, ${H / 2})`}
        textAnchor="middle"
        style={{ font: "10.5px IBM Plex Sans", fill: "var(--color-ink-soft)" }}
      >
        Composite score →
      </text>
      {points.map((p, i) => {
        const x = p.exposure_size_score;
        const y = p.composite_score;
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
        <>
          <circle
            cx={xToPx(subject.x)}
            cy={yToPx(subject.y)}
            r={8}
            fill="var(--color-info)"
            stroke="var(--color-surface)"
            strokeWidth={2}
          />
          <text
            x={xToPx(subject.x)}
            y={yToPx(subject.y) - 14}
            textAnchor="middle"
            style={{ font: "600 11px IBM Plex Sans", fill: "var(--color-info)" }}
          >
            YOU · {Math.round(subject.x)} / {Math.round(subject.y)}
          </text>
        </>
      )}
    </svg>
  );
}

function scoreBand(s: number): string {
  if (s >= 70) return "High";
  if (s >= 40) return "Mid";
  return "Low";
}

function formatCurrencyShort(n: number): string {
  const abs = Math.abs(n);
  if (abs >= 1_000_000) return `${n < 0 ? "-" : ""}$${(abs / 1_000_000).toFixed(abs >= 10_000_000 ? 0 : 1)}M`;
  if (abs >= 1_000) return `${n < 0 ? "-" : ""}$${(abs / 1_000).toFixed(0)}k`;
  return formatCurrency(n);
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

"use client";

import { use } from "react";
import {
  AlertTriangle,
  ArrowUp,
  ChevronRight,
  Gauge,
  Glasses,
  Layers,
  ShieldAlert,
} from "lucide-react";
import { Card } from "@/components/ui/card";
import { Chip } from "@/components/ui/chip";
import { WorkArea } from "@/components/ui/work-area";
import { Eyebrow, Body, Micro } from "@/components/ui/typography";
import { KpiSnug } from "@/components/ui/kpi-snug";
import { PageLoading } from "@/components/base/pageStates";
import { useDsiStore, type ApiRecord } from "@/store/dsiStore";
import { useEnsureFetched } from "@/store/useEnsureFetched";
import { numOrNull, strOrNull } from "@/lib/coerce";

/* ============================================================
 * Risk Assessment — mirrors reim_wb_a.jsx WbRisk (section 03).
 *
 * Stacked layout:
 *   1. Results — 6 KPIs (pure vs final composite + tier + conf/coverage)
 *   2. Tier Position & Improvement Paths — 5-tier strip + paths-to-improve
 *   3. Group & Signal Breakdown — table of TLA groups
 *   4. Active conditions — list of evaluated signal conditions
 * ============================================================ */

const TIERS = [
  { id: 1, label: "Preferred", min: 800, max: 1000, action: "approve" },
  { id: 2, label: "Standard", min: 700, max: 799, action: "approve" },
  { id: 3, label: "Under review", min: 600, max: 699, action: "refer" },
  { id: 4, label: "Sub-standard", min: 500, max: 599, action: "refer" },
  { id: 5, label: "Decline", min: 0, max: 499, action: "decline" },
];

function tierFromScore(score: number | null): number | null {
  if (score == null) return null;
  const t = TIERS.find((x) => score >= x.min && score <= x.max);
  return t?.id ?? null;
}

export default function RiskAssessmentPage(props: {
  params: Promise<{ code: string }>;
}) {
  use(props.params);
  const ver = useDsiStore((s) => s.activeVersion) as ApiRecord | null;
  const fetchRiskSignals = useDsiStore((s) => s.fetchRiskSignals);

  const versionCode = ver?.version_code as string | undefined;
  const hasConditions = Array.isArray(ver?.signal_conditions) && ver!.signal_conditions.length > 0;
  useEnsureFetched(hasConditions ? undefined : versionCode, fetchRiskSignals);

  if (!ver) {
    return (
      <>
        <PageLoading />
      </>
    );
  }

  const pureScore = numOrNull(ver.pure_composite_score);
  const finalScore = numOrNull(ver.final_composite_score);
  const confidence = numOrNull(ver.confidence);
  const coverage = numOrNull(ver.signal_coverage);
  const finalTier = (ver.final_tier as number | null | undefined) ?? null;
  const tierLabel = strOrNull(ver.tier_label);
  const pureTier = tierFromScore(pureScore);

  const groupScores = (ver.group_scores as ApiRecord | undefined) ?? {};
  const groupRows = Object.entries(groupScores).map(([id, raw]) => {
    const v = (raw as ApiRecord) ?? {};
    return {
      id,
      score: numOrNull(v.score),
      weight: numOrNull(v.weight),
      contribution: numOrNull(v.contribution ?? v.weighted_score),
      signalsPresent: numOrNull(v.signals_present ?? v.signal_count),
      signalsExpected: numOrNull(v.signals_expected ?? v.expected_signals),
      status: strOrNull(v.status) ?? "active",
    };
  });

  const conditions: Array<{
    signal_id?: string;
    source_id?: string;
    source_name?: string;
    action?: string;
    note?: string;
    applied_modifier?: number;
    condition_class?: string;
  }> = Array.isArray(ver.signal_conditions) ? ver.signal_conditions : [];

  // Improvement target = the tier above current (or null if already T1).
  const improveTarget = finalTier != null && finalTier > 1
    ? TIERS.find((t) => t.id === finalTier - 1)
    : null;
  const pointsToImprove =
    improveTarget && finalScore != null ? Math.max(0, improveTarget.min - finalScore) : null;

  return (
    <>
      <WorkArea>
        {/* ─── 1. Results ────────────────────────────────────── */}
        <Card header="Results" icon={Glasses} pad="md">
          <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-6">
            <KpiSnug
              label="Pure composite"
              value={pureScore != null ? pureScore.toFixed(0) : "—"}
            />
            <KpiSnug
              label="Confidence"
              value={confidence != null ? `${(confidence * 100).toFixed(0)}%` : "—"}
              tone="pos"
            />
            <KpiSnug
              label="Signal coverage"
              value={coverage != null ? `${(coverage * 100).toFixed(0)}%` : "—"}
              tone="pos"
            />
            <KpiSnug
              label="Pure tier"
              value={pureTier != null ? `T${pureTier}` : "—"}
            />
            <KpiSnug
              label="Final composite"
              value={finalScore != null ? finalScore.toFixed(0) : "—"}
              tone="info"
            />
            <KpiSnug
              label="Final tier"
              value={
                finalTier != null
                  ? `T${finalTier}${tierLabel ? ` · ${tierLabel}` : ""}`
                  : "—"
              }
              tone="info"
            />
          </div>
        </Card>

        {/* ─── 2. Tier Position & Improvement Paths ──────────── */}
        <Card header="Tier Position & Improvement Paths" icon={Gauge} pad="md">
          <div className="grid grid-cols-5 gap-2">
            {TIERS.map((t) => {
              const isCurrent = t.id === finalTier;
              const markerPct =
                isCurrent && finalScore != null
                  ? Math.max(0, Math.min(100, ((finalScore - t.min) / Math.max(1, t.max - t.min)) * 100))
                  : null;
              return (
                <div key={t.id}>
                  <div
                    className={`relative h-7 rounded-md bg-surface-elev ${
                      isCurrent ? "border-2 border-info" : "border border-rule"
                    }`}
                  >
                    {markerPct != null && (
                      <>
                        <div
                          className="absolute top-0 bottom-0 w-0.5 bg-info"
                          style={{ left: `${markerPct}%` }}
                        />
                        <div
                          className="absolute -top-4 text-[10px] font-bold text-info"
                          style={{ left: `${markerPct}%`, transform: "translateX(-50%)" }}
                        >
                          {finalScore!.toFixed(0)}
                        </div>
                      </>
                    )}
                  </div>
                  <div className="mt-1 flex items-center justify-between text-[10px] text-ink-mute">
                    <span>{t.min}</span>
                    <span
                      className={`${
                        isCurrent ? "font-bold text-info" : "font-medium"
                      }`}
                    >
                      T{t.id} · {t.label}
                    </span>
                    <span>{t.max}</span>
                  </div>
                </div>
              );
            })}
          </div>
          {improveTarget && pointsToImprove != null && (
            <div className="mt-3.5 border-t border-rule pt-3.5">
              <Eyebrow className="mb-2.5 inline-flex items-center gap-1">
                <ArrowUp size={11} /> Paths to improve
              </Eyebrow>
              <div className="grid grid-cols-[1fr_auto_auto] items-center gap-3.5 rounded-card border border-rule bg-surface-elev px-3 py-2.5">
                <div>
                  <div className="text-[13px] font-semibold">
                    Tier {improveTarget.id} — {improveTarget.label}
                  </div>
                  <Micro>
                    Key levers: top-weighted groups with lowest score
                  </Micro>
                </div>
                <div className="text-[11px] text-ink-soft">
                  Target range {improveTarget.min}–{improveTarget.max}
                </div>
                <div className="text-[14px] font-bold text-pos tabular-nums">
                  +{pointsToImprove.toFixed(0)} pts
                </div>
              </div>
            </div>
          )}
        </Card>

        {/* ─── 3. Group & Signal Breakdown ──────────────────── */}
        <Card header="Group & Signal Breakdown" icon={Layers} pad="md">
          {groupRows.length === 0 ? (
            <Body className="italic">No group scores on this version.</Body>
          ) : (
            <>
              <div className="grid grid-cols-[1.6fr_70px_70px_90px_70px_90px] border-b border-rule py-2 text-[10.5px] uppercase tracking-wider text-ink-mute">
                {["Group", "Score", "Weight", "Contribution", "Coverage", "Status"].map(
                  (h) => (
                    <span key={h}>{h}</span>
                  ),
                )}
              </div>
              {groupRows.map((g) => (
                <div
                  key={g.id}
                  className="grid grid-cols-[1.6fr_70px_70px_90px_70px_90px] items-center border-b border-rule py-2.5"
                >
                  <span className="flex items-center gap-1.5 text-[13px]">
                    <ChevronRight size={11} className="text-ink-mute" />
                    <span className="font-mono font-semibold">{g.id}</span>
                    {g.signalsPresent != null && (
                      <Micro>({g.signalsPresent})</Micro>
                    )}
                  </span>
                  <span className="tabular-nums">
                    {g.score != null ? g.score.toFixed(1) : "—"}
                  </span>
                  <span className="tabular-nums text-ink-soft">
                    {g.weight != null ? g.weight.toFixed(2) : "—"}
                  </span>
                  <span className="font-bold tabular-nums">
                    {g.contribution != null ? g.contribution.toFixed(1) : "—"}
                  </span>
                  <span
                    className={`tabular-nums ${
                      g.signalsPresent != null &&
                      g.signalsExpected != null &&
                      g.signalsPresent === g.signalsExpected
                        ? "text-pos"
                        : "text-warn"
                    }`}
                  >
                    {g.signalsPresent != null && g.signalsExpected != null
                      ? `${g.signalsPresent}/${g.signalsExpected}`
                      : g.signalsPresent != null
                        ? String(g.signalsPresent)
                        : "—"}
                  </span>
                  <Chip variant="pos" size="sm">
                    {g.status}
                  </Chip>
                </div>
              ))}
            </>
          )}
        </Card>

        {/* ─── 4. Active conditions ─────────────────────────── */}
        <Card
          header="Active conditions"
          icon={AlertTriangle}
          pad="md"
          headerRight={<Micro>{conditions.length}</Micro>}
        >
          {conditions.length === 0 ? (
            <Body className="italic">
              No signal conditions are attached to this version yet.
            </Body>
          ) : (
            conditions.map((c, i) => {
              const action = String(c.action ?? "").toLowerCase();
              const tone =
                action === "approve"
                  ? "pos"
                  : action === "decline"
                    ? "neg"
                    : action === "refer"
                      ? "spot"
                      : "info";
              const actionLabel =
                action === "modifier" && c.applied_modifier != null
                  ? `modifier · ${Number(c.applied_modifier).toFixed(2)}x`
                  : c.action ?? "—";
              return (
                <div
                  key={`${c.source_id ?? c.signal_id}-${i}`}
                  className={`grid grid-cols-[1fr_auto] items-center gap-3 py-2.5 ${
                    i < conditions.length - 1 ? "border-b border-rule" : ""
                  }`}
                >
                  <div className="flex items-center gap-2.5">
                    <ShieldAlert size={14} className="text-ink-soft" />
                    <div>
                      <span className="text-[13px]">
                        {c.note ?? c.source_name ?? c.signal_id ?? c.source_id ?? "—"}
                      </span>
                      <Micro className="mt-0.5 block">
                        {c.condition_class ?? "signal_condition"}
                      </Micro>
                    </div>
                  </div>
                  <Chip variant={tone} size="sm">
                    {actionLabel}
                  </Chip>
                </div>
              );
            })
          )}
        </Card>
      </WorkArea>
    </>
  );
}



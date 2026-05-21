"use client";

import { useEffect, useMemo } from "react";
import {
  AlertTriangle, ArrowUp, Gauge, Glasses, Layers, ShieldAlert,
} from "lucide-react";

import { useDsiStore } from "@/store/dsiStore";

import { CardGrid, StandardCard } from "@/components/base/cards";
import {
  ExpandableGroupTable,
  KpiTile,
  SubmissionStatusPill,
} from "@/components/base/content/primatives";

import {
  formatNumber, formatPercent,
} from "@/lib/format";

import { getPalette, KEYTERM } from "@/lib/keytermPalette";

export default function RiskTab() {
  const {
    activeSubmission, activeVersion,
    riskSignals, fetchRiskSignals,
  } = useDsiStore();

  useEffect(() => {
    if (activeVersion?.version_code) {
      fetchRiskSignals(activeVersion.version_code);
    }
  }, [activeVersion?.version_code, fetchRiskSignals]);

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const av = activeVersion as any;

  // Conditions indexed by source + grouped by type for accordion
  const signalConditions = av?.signal_conditions || [];
  const queryConditions = av?.query_conditions || [];
  const allConditions = [...signalConditions, ...queryConditions];

  const conditionsByType = useMemo(() => {
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const groups: Record<string, any[]> = {};
    for (const c of allConditions) {
      const type = c.source_type || "other";
      if (!groups[type]) groups[type] = [];
      groups[type].push(c);
    }
    return groups;
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [allConditions]);

  const conditionsBySource = useMemo(() => {
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const map: Record<string, any[]> = {};
    for (const c of allConditions) {
      const key = c.source_id || c.signal_id || "";
      if (!map[key]) map[key] = [];
      map[key].push(c);
    }
    return map;
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [allConditions]);

  // Group scores + signals per group
  const groupScores = av?.group_scores || {};
  const groupEntries = Object.entries(groupScores).sort(
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    ([, a]: any, [, b]: any) => (b?.risk_contribution || 0) - (a?.risk_contribution || 0),
  );

  // Loss / exposure band lookup helpers
  const lossBands = av?.loss_band_interpretation?.bands || [];
  const lossPropensityScore = av?.loss_propensity_score || 0;
  const lookupLossBand = (score: number) => {
    for (const b of lossBands) {
      if (score >= (b.bands?.min ?? 0) && score <= (b.bands?.max ?? 100)) return b;
    }
    return null;
  };
  const currentLossBand = lookupLossBand(lossPropensityScore);

  const expBands = av?.exposure_band_interpretation?.size?.bands || [];
  const expSizeScore = av?.exposure_size_score || 0;
  const lookupExpBand = (score: number) => {
    for (const b of expBands) {
      if (score >= (b.bands?.min ?? 0) && score <= (b.bands?.max ?? 100)) return b;
    }
    return null;
  };
  const currentExpBand = lookupExpBand(expSizeScore);

  const signalsByGroup = useMemo(() => {
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const map: Record<string, any[]> = {};
    for (const sig of (riskSignals || [])) {
      const group = sig.group_code || "ungrouped";
      if (!map[group]) map[group] = [];
      map[group].push(sig);
    }
    for (const group of Object.keys(map)) {
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      map[group].sort((a: any, b: any) => (b.contribution || 0) - (a.contribution || 0));
    }
    return map;
  }, [riskSignals]);

  // Tier improvement paths
  const tierBands = av?.tier_band_interpretation?.tiers || [];
  const currentTier = av?.final_tier || av?.score_based_tier;
  const currentScore = av?.final_composite_score || 0;

  const improvementPaths = useMemo(() => {
    if (!currentTier || currentTier <= 1 || tierBands.length === 0) return [];
    return tierBands
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      .filter((t: any) => t.tier_id < currentTier)
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      .sort((a: any, b: any) => b.tier_id - a.tier_id)
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      .map((t: any) => {
        const targetMin = t.bands?.min ?? 0;
        const ptsNeeded = currentScore < targetMin ? targetMin - currentScore : 0;
        return {
          tier_id: t.tier_id,
          label: t.label,
          action: t.action,
          target_range: `${t.bands?.min ?? 0} – ${t.bands?.max ?? 0}`,
          pts_needed: Math.round(ptsNeeded),
        };
      });
  }, [currentTier, currentScore, tierBands]);

  const topLevers = useMemo(() => {
    return groupEntries
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      .filter(([, gs]: any) => (gs?.risk_contribution || 0) > 0)
      .slice(0, 3)
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      .map(([groupId, gs]: any) => ({
        group: groupId,
        contribution: gs.risk_contribution || 0,
      }));
  }, [groupEntries]);

  if (!activeSubmission || !activeVersion) return null;

  const marginPct = av.tier_margin_percentile;
  const tierMin = av.tier_margin_tier_min;
  const tierMax = av.tier_margin_tier_max;
  const hasTierMargin = marginPct != null && tierMin != null && tierMax != null;

  // ────────────────────────────────────────────────────────────────────
  // Group → Signal table: build groups for ExpandableGroupTable
  // ────────────────────────────────────────────────────────────────────
  const groupBreakdownGroups = groupEntries.map(([groupId, gsRaw]) => {
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const gs = gsRaw as any;
    const signals = signalsByGroup[groupId] || [];
    const groupConditions = conditionsBySource[groupId] || [];

    const lossGroupEntry = (av?.loss_group_scores || {})[groupId];
    const lossWeight = lossGroupEntry?.loss_weight || 0;
    const lossFreqScore = lossGroupEntry?.frequency_score;

    const expGroupWeights = (av?.exposure_components || {}).group_weights || {};
    const expWeight = expGroupWeights[groupId] || 0;

    const coverageRatio = gs?.coverage_ratio ?? 0;
    const coverageColor =
      coverageRatio >= 1 ? "text-generate-text-good"
      : coverageRatio >= 0.5 ? "text-generate-text-maybe"
      : "text-generate-text-bad";

    return {
      key: groupId,
      title: (
        <span className="inline-flex items-center gap-2">
          <span className="font-bold">{groupId}</span>
          {groupConditions.length > 0 && (
            <span className="text-[10px] bg-generate-text-maybe/15 text-generate-text-maybe px-1.5 py-0.5 rounded font-bold">
              {groupConditions.length} cond
            </span>
          )}
          <span className="text-[10px] opacity-40">({signals.length})</span>
        </span>
      ),
      items: signals,
      summary: [
        formatNumber(gs?.risk_score, 1),
        formatNumber(gs?.risk_weight, 2),
        formatNumber(gs?.risk_contribution, 1),
        <span key="cov" className={`text-xs ${coverageColor}`}>
          {gs?.signal_count || 0}/{gs?.expected_signal_count || 0}
        </span>,
        lossWeight > 0 ? (
          <span key="loss" className="text-xs leading-tight inline-block text-right">
            <span className="opacity-50">wgt {formatNumber(lossWeight, 2)}</span>
            {lossFreqScore != null && (
              <span className="block"><span className="font-bold">{formatNumber(lossFreqScore, 1)}</span><span className="opacity-40"> freq</span></span>
            )}
            {currentLossBand && (
              <span className="block text-[9px] font-bold uppercase text-generate-text-comment">
                → {currentLossBand.label} ({currentLossBand.frequency_modifier}x)
              </span>
            )}
          </span>
        ) : <span key="loss" className="opacity-20">–</span>,
        expWeight > 0 ? (
          <span key="exp" className="text-xs leading-tight inline-block text-right">
            <span className="opacity-50">wgt {formatNumber(expWeight, 2)}</span>
            {currentExpBand && (
              <span className="block text-[9px] font-bold uppercase text-generate-text-comment">
                → {currentExpBand.label} ({currentExpBand.modifier}x)
              </span>
            )}
          </span>
        ) : <span key="exp" className="opacity-20">–</span>,
      ],
    };
  });

  // ────────────────────────────────────────────────────────────────────
  // Conditions table: each "group" is a condition type
  // ────────────────────────────────────────────────────────────────────
  const conditionGroups = Object.entries(conditionsByType).map(([type, conds]) => {
    const modifiers = conds.filter((c) => {
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      const a = typeof c.action === "string" ? c.action.toLowerCase() : ((c as any).action?.value || "");
      return a === "modifier";
    });
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const modProduct = modifiers.reduce((acc: number, c: any) => acc * (c.action_value || 1), 1);

    return {
      key: `cond_${type}`,
      title: (
        <span className="inline-flex items-center gap-2">
          <span className="font-bold capitalize">{type.replace(/_/g, " ")}</span>
          <span className="text-[10px] opacity-40">({conds.length})</span>
        </span>
      ),
      items: conds,
      summary: [
        modifiers.length > 0 ? (
          <span key="mod" className="text-[10px] bg-generate-text-comment/15 text-generate-text-comment px-1.5 py-0.5 rounded font-bold">
            {modifiers.length} modifier{modifiers.length > 1 ? "s" : ""} ({formatPercent(modProduct, 0)})
          </span>
        ) : <span key="mod" className="opacity-20">–</span>,
      ],
    };
  });

  return (
    <div className="w-full pb-12 pt-generate-pad">

      <CardGrid cols="grid-cols-1" className="gap-4">

        {/* KPI Results */}
        <StandardCard title="Results" lucideIcon={Glasses}>
          <div className="grid grid-cols-2 md:grid-cols-6 gap-6 py-2">
            <KpiTile label="Pure Composite Score" value={formatNumber(av.pure_composite_score, 1)} />
            <KpiTile label="Confidence"            value={formatPercent(av.confidence || 0, 0)} />
            <KpiTile label="Signal Coverage"       value={formatPercent(av.signal_coverage || 0, 0)} />
            <KpiTile label="Pure Score-Based Tier" value={`T${av.score_based_tier}`} />
            <KpiTile label="Final Composite Score" value={formatNumber(av.final_composite_score, 1)} variant="emphasis" />
            <KpiTile label="Final Tier"            value={`T${av.final_tier} (${av.tier_label})`} variant="emphasis" />
          </div>
        </StandardCard>

        {/* Tier Position & Improvement Paths */}
        <StandardCard title="Tier Position & Improvement Paths" lucideIcon={Gauge}>
          {hasTierMargin ? (
            <div className="space-y-4 py-2">
              <div className="grid gap-2" style={{ gridTemplateColumns: `repeat(${tierBands.length || 5}, 1fr)` }}>
                {/* eslint-disable-next-line @typescript-eslint/no-explicit-any */}
                {tierBands.map((band: any) => {
                  const isCurrent = band.tier_id === (av.final_tier || av.score_based_tier);
                  return (
                    <div key={band.tier_id} className="text-wrap">
                      <div className={`relative h-8 rounded bg-generate-light-background border ${isCurrent ? "border-4 border-generate-text-outline" : "border-generate-text-outline/40"}`}>
                        {isCurrent && marginPct != null && (
                          <div
                            className="absolute top-0 h-8 w-1 bg-generate-text-input"
                            style={{ left: `${Math.max(2, Math.min(98, marginPct * 100))}%` }}
                          >
                            <div className="absolute -top-5 right-0 text-xs font-bold text-generate-text-input whitespace-nowrap">
                              {formatNumber(currentScore, 0)}
                            </div>
                          </div>
                        )}
                      </div>
                      <div className="flex justify-between mt-1 text-xs">
                        <span>{band.bands?.max ?? ""}</span>
                        <span className={isCurrent ? "font-bold text-generate-text-input" : ""}>
                          T{band.tier_id} ({band.label})
                        </span>
                        <span>{band.bands?.min ?? ""}</span>
                      </div>
                      <div className="text-center mt-0.5">
                        <SubmissionStatusPill decision={band.action} />
                      </div>
                    </div>
                  );
                })}
              </div>

              {improvementPaths.length > 0 && (
                <div className="border-t border-generate-text-outline/20 pt-3">
                  <span className="text-xs opacity-60 mb-2 flex items-center gap-1">
                    <ArrowUp className="w-3 h-3" /> Paths to Improve
                  </span>
                  <CardGrid cols="grid-cols-1 md:grid-cols-2 lg:grid-cols-3">
                    {improvementPaths.map((path) => {
                      const { color } = getPalette(KEYTERM, path.action);
                      return (
                        <div key={path.tier_id} className="border border-generate-text-outline/30 rounded-lg p-3 text-wrap">
                          <div className="flex items-center justify-between mb-2">
                            <span className="text-sm font-bold">Tier {path.tier_id} — {path.label}</span>
                            <span className={`text-xs font-bold px-2 py-0.5 rounded bg-[var(--${color})]/10 text-[var(--${color})]`}>
                              {path.action}
                            </span>
                          </div>
                          <div className="flex items-center justify-between mb-1">
                            <span className="text-xs opacity-50">Score range: {path.target_range}</span>
                            <span className="text-sm font-bold text-generate-text-good">+{path.pts_needed} pts</span>
                          </div>
                          {topLevers.length > 0 && (
                            <div className="text-[10px] opacity-50 border-t border-generate-text-outline/20 pt-1.5 mt-1.5">
                              <span className="font-semibold">Key levers: </span>
                              {topLevers.map((l, i) => (
                                <span key={l.group}>{i > 0 && ", "}{l.group} ({formatNumber(l.contribution, 0)}pts)</span>
                              ))}
                            </div>
                          )}
                        </div>
                      );
                    })}
                  </CardGrid>
                </div>
              )}
            </div>
          ) : (
            <div className="flex items-center justify-center h-24 opacity-50 text-sm italic">
              Tier margin data not available.
            </div>
          )}
        </StandardCard>

        {/* Group → Signal Breakdown — now via ExpandableGroupTable */}
        <StandardCard title="Group & Signal Breakdown" lucideIcon={Layers}>
          {groupBreakdownGroups.length === 0 ? (
            <div className="flex items-center justify-center h-24 opacity-50 text-sm italic">
              No group data available.
            </div>
          ) : (
            <ExpandableGroupTable
              title=""
              columns={[
                { label: "Group / Signal", width: "1fr",   align: "left",  headeralign: "left"   },
                { label: "Score",          width: "70px",  align: "right", headeralign: "center" },
                { label: "Weight",         width: "70px",  align: "right", headeralign: "center" },
                { label: "Contribution",   width: "90px",  align: "right", headeralign: "center", bold: true },
                { label: "Cov",            width: "60px",  align: "center", headeralign: "center" },
                { label: "Loss Deriv",     width: "120px", align: "right", headeralign: "center" },
                { label: "Exposure Deriv", width: "120px", align: "right", headeralign: "center" },
              ]}
              groups={groupBreakdownGroups}
              // eslint-disable-next-line @typescript-eslint/no-explicit-any
              renderItemCells={(sig: any) => [
                <span key="name" className="inline-flex items-center gap-2">
                  <span className="text-sm">{sig.code}</span>
                  {(conditionsBySource[sig.code] || conditionsBySource[sig.signal_id] || []).length > 0 && (
                    <AlertTriangle className="w-3 h-3 text-generate-text-maybe shrink-0" />
                  )}
                  {sig.was_absent && <span className="text-[10px] text-generate-text-bad font-bold">ABSENT</span>}
                </span>,
                formatNumber(sig.score, 1),
                formatNumber(sig.weight, 2),
                formatNumber(sig.contribution, 2),
                "",
                "",
                "",
              ]}
            />
          )}
        </StandardCard>

        {/* Active Conditions — via ExpandableGroupTable */}
        <StandardCard
          title="Active Conditions"
          lucideIcon={AlertTriangle}
          headerRight={<span className="text-[10px] opacity-40">({allConditions.length})</span>}
        >
          {conditionGroups.length === 0 ? (
            <div className="flex items-center justify-center h-24 opacity-50 text-sm italic">
              No conditions triggered.
            </div>
          ) : (
            <ExpandableGroupTable
              title=""
              columns={[
                { label: "Type",       width: "1fr",   align: "left",  headeralign: "left"   },
                { label: "Modifiers",  width: "240px", align: "right", headeralign: "right"  },
              ]}
              groups={conditionGroups}
              // eslint-disable-next-line @typescript-eslint/no-explicit-any
              renderItemCells={(cond: any) => {
                const actionKey =
                  typeof cond.action === "string"
                    ? cond.action.toLowerCase()
                    : cond.action?.value || "note";

                return [
                  <span key="note" className="inline-flex items-center gap-2 min-w-0">
                    <ShieldAlert className="w-3 h-3 shrink-0 text-generate-text-placeholder" />
                    <span className="text-sm truncate">{cond.note || cond.source_name || "Condition"}</span>
                    <span className="text-[10px] opacity-40">{cond.source_id}</span>
                  </span>,
                  <span key="pill" className="inline-flex items-center gap-2 justify-end">
                    <SubmissionStatusPill decision={actionKey} />
                    {cond.action_value != null && typeof cond.action_value === "number" && (
                      <span className="text-xs font-bold opacity-70">
                        {actionKey === "modifier" ? formatPercent(cond.action_value, 0)
                          : actionKey === "tier_override" ? `→ T${cond.action_value}`
                          : cond.action_value}
                      </span>
                    )}
                  </span>,
                ];
              }}
            />
          )}
        </StandardCard>

      </CardGrid>
    </div>
  );
}

"use client";

import { useEffect, useMemo, useState } from "react";
import { useDsiStore } from "@/store/dsiStore";
import {
  Target, Activity, AlertTriangle, ShieldAlert, Glasses,
  Gauge, Layers, ChevronDown, ChevronRight, MessageSquare, ArrowUp
} from "lucide-react";
import { formatNumber, formatPercent, formatDate, formatText, formatCurrency } from "@/lib/format";
import { KpiTile, StatusPill } from "@/components/base/content/primatives";
import { StandardCard } from "@/components/base/cards";
import KeyDetailsBar from "@/components/base/keyDetailsBar";
import { ACTION_PALETTE, getStatusStyle } from "@/lib/statusPalette";

export default function RiskTab() {
  const { activeSubmission, activeVersion, activeQuote, riskSignals, isFetchingRiskSignals, fetchRiskSignals } = useDsiStore();
  const [expandedGroups, setExpandedGroups] = useState<Record<string, boolean>>({});

  useEffect(() => {
    if (activeVersion?.version_code) {
      fetchRiskSignals(activeVersion.version_code);
    }
  }, [activeVersion?.version_code, fetchRiskSignals]);

  const toggleGroup = (group: string) => {
    setExpandedGroups(prev => ({ ...prev, [group]: !prev[group] }));
  };

  // Conditions indexed by source + grouped by type for accordion
  const signalConditions = activeVersion?.signal_conditions || [];
  const queryConditions = activeVersion?.query_conditions || [];
  const allConditions = [...signalConditions, ...queryConditions];

  const conditionsByType = useMemo(() => {
    const groups: Record<string, any[]> = {};
    for (const c of allConditions) {
      const type = c.source_type || 'other';
      if (!groups[type]) groups[type] = [];
      groups[type].push(c);
    }
    return groups;
  }, [allConditions]);

  // Aggregate modifier value per condition type
  const conditionTypeSummary = useMemo(() => {
    return Object.entries(conditionsByType).map(([type, conds]) => {
      const modifiers = conds.filter((c: any) => {
        const a = typeof c.action === 'string' ? c.action.toLowerCase() : (c.action?.value || '');
        return a === 'modifier';
      });
      const modProduct = modifiers.reduce((acc: number, c: any) => acc * (c.action_value || 1), 1);
      return { type, count: conds.length, modifierCount: modifiers.length, aggregateModifier: modProduct };
    });
  }, [conditionsByType]);

  const conditionsBySource = useMemo(() => {
    const map: Record<string, any[]> = {};
    for (const c of allConditions) {
      const key = c.source_id || c.signal_id || '';
      if (!map[key]) map[key] = [];
      map[key].push(c);
    }
    return map;
  }, [allConditions]);

  // Group scores + signals per group
  const groupScores = activeVersion?.group_scores || {};
  const groupEntries = Object.entries(groupScores).sort(([, a]: any, [, b]: any) => (b?.risk_contribution || 0) - (a?.risk_contribution || 0));

  // Loss/exposure band lookup helpers
  const lossBands = activeVersion?.loss_band_interpretation?.bands || [];
  const lossPropensityScore = activeVersion?.loss_propensity_score || 0;
  const lookupLossBand = (score: number) => {
    for (const b of lossBands) {
      if (score >= (b.bands?.min ?? 0) && score <= (b.bands?.max ?? 100)) return b;
    }
    return null;
  };
  const currentLossBand = lookupLossBand(lossPropensityScore);

  const expBands = activeVersion?.exposure_band_interpretation?.size?.bands || [];
  const expSizeScore = activeVersion?.exposure_size_score || 0;
  const lookupExpBand = (score: number) => {
    for (const b of expBands) {
      if (score >= (b.bands?.min ?? 0) && score <= (b.bands?.max ?? 100)) return b;
    }
    return null;
  };
  const currentExpBand = lookupExpBand(expSizeScore);

  const signalsByGroup = useMemo(() => {
    const map: Record<string, any[]> = {};
    for (const sig of (riskSignals || [])) {
      const group = sig.group_code || 'ungrouped';
      if (!map[group]) map[group] = [];
      map[group].push(sig);
    }
    // Sort each group's signals by contribution descending
    for (const group of Object.keys(map)) {
      map[group].sort((a: any, b: any) => (b.contribution || 0) - (a.contribution || 0));
    }
    return map;
  }, [riskSignals]);

  // Direct queries (separate from signal conditions)
  const directQueries = useMemo(() => {
    return (activeVersion?.query_conditions || []).filter((c: any) =>
      c.source_type === 'direct_query'
    );
  }, [activeVersion?.query_conditions]);

  // Tier improvement paths
  const tierBands = activeVersion?.tier_band_interpretation?.tiers || [];
  const currentTier = activeVersion?.final_tier || activeVersion?.score_based_tier;
  const currentScore = activeVersion?.final_composite_score || 0;

  const improvementPaths = useMemo(() => {
    if (!currentTier || currentTier <= 1 || tierBands.length === 0) return [];
    // Find tiers better than current (lower tier_id = better)
    const betterTiers = tierBands
      .filter((t: any) => t.tier_id < currentTier)
      .sort((a: any, b: any) => b.tier_id - a.tier_id); // closest first

    return betterTiers.map((t: any) => {
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

  // Top group levers (highest contribution = most room to improve)
  const topLevers = useMemo(() => {
    return groupEntries
      .filter(([, gs]: any) => (gs?.risk_contribution || 0) > 0)
      .slice(0, 3)
      .map(([groupId, gs]: any) => ({
        group: groupId,
        contribution: gs.risk_contribution || 0,
        score: gs.risk_score || 0,
        weight: gs.risk_weight || 0,
      }));
  }, [groupEntries]);

  if (!activeSubmission || !activeVersion) return null;

  const marginPct = activeVersion.tier_margin_percentile;
  const tierMin = activeVersion.tier_margin_tier_min;
  const tierMax = activeVersion.tier_margin_tier_max;
  const distBetter = activeVersion.tier_margin_distance_better;
  const distWorse = activeVersion.tier_margin_distance_worse;
  const hasTierMargin = marginPct != null && tierMin != null && tierMax != null;

  return (
    <div className="w-full no-scrollbar animate-in fade-in duration-500 pb-12">

      <KeyDetailsBar
        status={activeQuote?.status}
        validFrom={activeQuote?.valid_from}
        validUntil={activeQuote?.valid_until}
        boundAt={activeQuote?.bound_at}
        policyNumber={activeQuote?.policy_number}
        submissionCode={activeSubmission?.submission_code}
        quoteCode={activeQuote?.quote_code}
      />

      {/* KPIs */}
      <div className="pt-2 pb-2">
        <StandardCard title="Results" lucideIcon={Glasses}>
          <div className="grid grid-cols-2 md:grid-cols-6 gap-6 py-2">
            <KpiTile label="Pure Composite Score" value={formatNumber(activeVersion.pure_composite_score, 1)} />
            <KpiTile label="Confidence"           value={formatPercent(activeVersion.confidence || 0, 0)} />
            <KpiTile label="Signal Coverage"      value={formatPercent(activeVersion.signal_coverage || 0, 0)} />
            <KpiTile label="Pure Score-Based Tier" value={`T${activeVersion.score_based_tier}`} />
            <KpiTile label="Final Composite Score" value={formatNumber(activeVersion.final_composite_score, 1)} variant="emphasis" />
            <KpiTile label="Final Tier"            value={`T${activeVersion.final_tier} (${activeVersion.tier_label})`} variant="emphasis" />
          </div>
        </StandardCard>
      </div>

      {/* =======================================================================
          TIER POSITION — full width, enhanced visualisation
          ======================================================================= */}
      <div className="pt-2 pb-2">
        <StandardCard title="Tier Position & Improvement Paths" lucideIcon={Gauge}>
        <div className="
          overflow-x-hidden
          bg-dsi-analysis shadow-sm 
          pt-dsi-gap pb-4"
          >
          {hasTierMargin ? (
            <div className="pl-dsi-pad pr-dsi-pad space-y-4">
              {/* Full tier band visualisation — shows ALL tiers with current position */}
              <div>
                <div className="grid gap-2 mb-3" style={{ gridTemplateColumns: `repeat(${tierBands.length || 5}, 1fr)` }}>
                  {tierBands.map((band: any, idx: number) => {
                    const isCurrent = band.tier_id === (activeVersion.final_tier || activeVersion.score_based_tier);
                    return (
                      <div key={band.tier_id} className="relative text-wrap">
                        <div className={`h-dsi-gap rounded ${isCurrent ? 'bg-dsi-contrast-background/30 border-4 border-dsi-outline/50' : 'bg-dsi-contrast-background/30 border border-dsi-outline/50'}`}>
                          {/* Position marker within current tier */}
                          {isCurrent && marginPct != null && (
                            <div className="
                              absolute 
                              top-0
                              h-dsi-gap
                              w-1
                              bg-dsi-selected" 
                              style={
                                { left: `${Math.max(2, Math.min(98, marginPct * 100))}%` }
                                }
                              >
                              <div className="
                                absolute
                                text-right
                                bottom-dsi-padicon
                                text-xs
                                font-bold 
                                text-dsi-selected whitespace-nowrap">
                                {formatNumber(currentScore, 0)}
                              </div>
                            </div>
                          )}
                        </div>
                        
                        <div className="flex justify-between mt-1 text-xs">
                          <span>{band.bands?.max ?? ''}</span>
                          <span className={`${isCurrent ? 'font-bold text-dsi-selected' : 'text-xs'}`}>T{band.tier_id} ({band.label})</span>
                          <span>{band.bands?.min ?? ''}</span>
                        </div>
                        
                        <div className="text-center mt-0.5">
                          <span className={`text-xs ${band.action?.toLowerCase().includes('approve') ? 'text-dsi-positive' : band.action?.toLowerCase().includes('decline') ? 'text-dsi-negative' : 'text-dsi-warning'}`}>
                            {band.action}
                          </span>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
                
                {/* Distance metrics */}
                <div className="grid grid-cols-4">

                  {/* row 1 */}
                  <div className="flex flex-col">
                    <span>Position</span>
                    <span>{formatNumber(activeVersion.tier_margin_percentile, 3)}%</span>
                  </div>
                  <div className="flex flex-col">
                    <span>hey</span>
                  </div>
                  <div className="flex flex-col">
                    <span>yo</span>
                  </div>
                  <div className="flex flex-col">
                    <span>hi</span>
                  </div>                 

                  
                </div>

              {/* Paths to improve */}
              {improvementPaths.length > 0 && (
                <div className="border-t border-dsi-outline/20 pt-3">
                  <span className="text-xs opacity-60 block mb-2 flex items-center gap-1">
                    <ArrowUp className="w-3 h-3" /> Paths to Improve
                  </span>
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                    {improvementPaths.map((path: any) => (
                      <div key={path.tier_id} className="border border-dsi-outline/15 rounded-lg p-3 text-wrap hover:bg-dsi-background/10 transition-colors">
                        <div className="flex items-center justify-between mb-2">
                          <span className="text-sm font-bold">Tier {path.tier_id} — {path.label}</span>
                          <span className={`text-xs font-bold px-2 py-0.5 rounded ${path.action?.toLowerCase().includes('approve') ? 'bg-dsi-positive/10 text-dsi-positive' : 'bg-dsi-warning/10 text-dsi-warning'}`}>
                            {path.action}
                          </span>
                        </div>
                        <div className="flex items-center justify-between mb-1">
                          <span className="text-xs opacity-50">Score range: {path.target_range}</span>
                          <span className="text-sm font-black text-dsi-positive">+{path.pts_needed} pts</span>
                        </div>
                        {topLevers.length > 0 && (
                          <div className="text-[10px] opacity-50 border-t border-dsi-outline/10 pt-1.5 mt-1.5">
                            <span className="font-semibold">Key levers: </span>
                            {topLevers.map((l, i) => (
                              <span key={l.group}>{i > 0 && ', '}{l.group} ({formatNumber(l.contribution, 0)}pts)</span>
                            ))}
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          ) : (
            <div className="flex items-center justify-center h-24 opacity-50 text-sm italic">
              Tier margin data not available.
            </div>
          )}
        </div>
        </StandardCard>
      </div>

      {/* =======================================================================
          GROUP → SIGNAL BREAKDOWN with contribution totals and pillar derivation
          ======================================================================= */}
      <div className="flex flex-col pt-2 pb-2">
        <div className="dsi-section-header items-center overflow-x-hidden whitespace-nowrap border-collapse">
          <Layers className="icon"/><span className="text-sm">Group & Signal Breakdown</span>
        </div>
        <div className="dsi-section-analysis overflow-x-auto whitespace-nowrap border-collapse">

          {isFetchingRiskSignals ? (
            <div className="flex flex-col items-center justify-center py-10 opacity-50 space-y-4">
              <Activity className="w-6 h-6 animate-spin" />
            </div>
          ) : groupEntries.length === 0 ? (
            <div className="flex items-center justify-center h-24 opacity-50 text-sm italic">No group data available.</div>
          ) : (
            <div className="w-full">
              {/* Column headers */}
              <div className="grid grid-cols-[1fr_70px_70px_90px_60px_120px_120px] gap-0 text-[11px] underline opacity-70 px-dsi-pad py-2">
                <span>Group / Signal</span>
                <span className="text-right">Score</span>
                <span className="text-right">Weight</span>
                <span className="text-right">Contribution</span>
                <span className="text-center">Cov</span>
                <span className="text-right">Loss Derivation</span>
                <span className="text-right">Exposure Derivation</span>
              </div>

              {groupEntries.map(([groupId, gs]: [string, any]) => {
                const isExpanded = expandedGroups[groupId] ?? false;
                const signals = signalsByGroup[groupId] || [];
                const groupConditions = conditionsBySource[groupId] || [];
                const hasConditions = groupConditions.length > 0 || signals.some((s: any) => (conditionsBySource[s.code] || []).length > 0);

                // Loss derivation for this group (loss_weight now lives in loss_group_scores)
                const lossGroupEntry = (activeVersion?.loss_group_scores || {})[groupId];
                const lossWeight = lossGroupEntry?.loss_weight || 0;
                const lossFreqScore = lossGroupEntry?.frequency_score;
                const lossSevScore = lossGroupEntry?.severity_score;

                // Exposure derivation (exposure_weight now lives in exposure_components.group_weights)
                const expGroupWeights = (activeVersion?.exposure_components || {}).group_weights || {};
                const expWeight = expGroupWeights[groupId] || 0;

                return (
                  <div key={groupId}>
                    {/* GROUP ROW */}
                    <div
                      onClick={() => toggleGroup(groupId)}
                      className={`grid grid-cols-[1fr_70px_70px_90px_60px_120px_120px] gap-0 px-dsi-pad py-2.5 border-t border-dsi-outline/20 cursor-pointer hover:bg-dsi-background/20 transition-colors ${hasConditions ? 'border-l-2 border-l-dsi-warning' : ''}`}
                    >
                      <div className="flex items-center gap-2">
                        {isExpanded ? <ChevronDown className="w-3.5 h-3.5 shrink-0" /> : <ChevronRight className="w-3.5 h-3.5 shrink-0" />}
                        <span className="font-bold text-sm">{groupId}</span>
                        {groupConditions.length > 0 && (
                          <span className="text-[10px] bg-dsi-warning/10 text-dsi-warning px-1.5 py-0.5 rounded font-bold">
                            {groupConditions.length} cond
                          </span>
                        )}
                        <span className="text-[10px] opacity-40 ml-1">({signals.length})</span>
                      </div>
                      <span className="text-right text-sm">{formatNumber(gs.risk_score, 1)}</span>
                      <span className="text-right text-sm opacity-60">{formatNumber(gs.risk_weight, 2)}</span>
                      <span className="text-right text-sm font-bold">{formatNumber(gs.risk_contribution, 1)}</span>
                      <span className="text-center">
                        <span className={`text-xs ${(gs.coverage_ratio ?? 0) >= 1 ? 'text-dsi-positive' : (gs.coverage_ratio ?? 0) >= 0.5 ? 'text-dsi-warning' : 'text-dsi-negative'}`}>
                          {gs.signal_count || 0}/{gs.expected_signal_count || 0}
                        </span>
                      </span>
                      {/* Loss derivation: weight × score → band */}
                      <span className="text-right text-xs text-wrap">
                        {lossWeight > 0 ? (
                          <span>
                            <span className="opacity-50">wgt {formatNumber(lossWeight, 2)}</span>
                            {lossFreqScore != null && (
                              <span className="block"><span className="font-bold">{formatNumber(lossFreqScore, 1)}</span><span className="opacity-40"> freq</span></span>
                            )}
                            {currentLossBand && (
                              <span className="block text-[9px] font-bold uppercase text-dsi-info">→ {currentLossBand.label} ({currentLossBand.frequency_modifier}x)</span>
                            )}
                          </span>
                        ) : <span className="opacity-20">–</span>}
                      </span>
                      {/* Exposure derivation: weight → band */}
                      <span className="text-right text-xs text-wrap">
                        {expWeight > 0 ? (
                          <span>
                            <span className="opacity-50">wgt {formatNumber(expWeight, 2)}</span>
                            {currentExpBand && (
                              <span className="block text-[9px] font-bold uppercase text-dsi-info">→ {currentExpBand.label} ({currentExpBand.modifier}x)</span>
                            )}
                          </span>
                        ) : <span className="opacity-20">–</span>}
                      </span>
                    </div>

                    {/* Group-level conditions */}
                    {isExpanded && groupConditions.length > 0 && (
                      <div className="ml-8 mr-dsi-pad mb-1">
                        {groupConditions.map((cond: any, cidx: number) => {
                          const actionKey = typeof cond.action === 'string' ? cond.action.toLowerCase() : (cond.action?.value || 'note');
                          return (
                            <div key={`gc-${cidx}`} className="flex items-center gap-2 py-1 text-xs">
                              <ShieldAlert className={`w-3 h-3 shrink-0 ${getStatusStyle(ACTION_PALETTE, actionKey).text}`} />
                              <span className="opacity-70 truncate">{cond.note || cond.source_name || 'Condition'}</span>
                              <StatusPill palette={ACTION_PALETTE} status={actionKey}>
                                {actionKey.replace('_', ' ')}
                              </StatusPill>
                            </div>
                          );
                        })}
                      </div>
                    )}

                    {/* Signal rows */}
                    {isExpanded && signals.map((sig: any, sidx: number) => {
                      const sigConditions = conditionsBySource[sig.code] || conditionsBySource[sig.signal_id] || [];
                      return (
                        <div
                          key={`${sig.code}-${sidx}`}
                          className={`grid grid-cols-[1fr_70px_70px_90px_60px_120px_120px] gap-0 px-dsi-pad py-1.5 bg-dsi-background/10 hover:bg-dsi-background/20 transition-colors ${sigConditions.length > 0 ? 'border-l-2 border-l-dsi-warning' : ''}`}
                        >
                          <div className="flex items-center gap-2 pl-6">
                            <span className="text-sm">{sig.code}</span>
                            {sigConditions.length > 0 && <AlertTriangle className="w-3 h-3 text-dsi-warning shrink-0" />}
                            {sig.was_absent && <span className="text-[10px] text-dsi-negative font-bold">ABSENT</span>}
                            {sig.proxy_tier && <span className="text-[10px] opacity-30">T{sig.proxy_tier}</span>}
                          </div>
                          <span className="text-right text-sm">{formatNumber(sig.score, 1)}</span>
                          <span className="text-right text-sm opacity-50">{formatNumber(sig.weight, 2)}</span>
                          <span className="text-right text-sm">{formatNumber(sig.contribution, 2)}</span>
                          <span></span><span></span><span></span>
                        </div>
                      );
                    })}
                    {isExpanded && signals.length === 0 && (
                      <div className="pl-12 py-2 text-xs opacity-40 italic">No signals in this group.</div>
                    )}
                  </div>
                );
              })}

              {/* CONTRIBUTION TOTAL + TIER SUMMARY */}
              {(() => {
                const totalContribution = groupEntries.reduce((sum, [, gs]: any) => sum + (gs?.risk_contribution || 0), 0);
                return (
                  <div className="grid grid-cols-[1fr_70px_70px_90px_60px_120px_120px] gap-0 px-dsi-pad py-3 border-t-2 border-dsi-outline/30 bg-dsi-background/20">
                    <span className="font-black text-sm">Total → Composite Score</span>
                    <span></span>
                    <span></span>
                    <span className="text-right font-black text-sm">{formatNumber(totalContribution, 1)}</span>
                    <span></span>
                    <span className="text-right text-xs text-wrap">
                      {currentLossBand ? (
                        <span className="font-bold text-dsi-info uppercase">{activeVersion?.loss_propensity_band?.replace(/_/g, ' ')} → {formatNumber(activeVersion?.loss_combined_modifier, 3)}x</span>
                      ) : <span className="opacity-30">–</span>}
                    </span>
                    <span className="text-right text-xs text-wrap">
                      {currentExpBand ? (
                        <span className="font-bold text-dsi-info uppercase">{activeVersion?.exposure_band_label} → {formatNumber(activeVersion?.exposure_modifier, 3)}x</span>
                      ) : <span className="opacity-30">–</span>}
                    </span>
                  </div>
                );
              })()}

              {/* Tier result summary */}
              <div className="px-dsi-pad py-2 text-xs opacity-60 text-wrap">
                Composite {formatNumber(currentScore, 1)} → <span className="font-bold text-dsi-selected">Tier {activeVersion?.final_tier} ({activeVersion?.tier_label})</span>
                {activeVersion?.score_based_tier !== activeVersion?.final_tier && (
                  <span className="ml-2 opacity-50">(score-based: Tier {activeVersion?.score_based_tier}, overridden to {activeVersion?.final_tier})</span>
                )}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* =======================================================================
          ACTIVE CONDITIONS — full width, bottom section
          ======================================================================= */}
      <div className="flex flex-col pt-2 pb-2">
        <div className="dsi-section-header overflow-x-hidden whitespace-nowrap border-collapse">
          <AlertTriangle className="icon"/>
          <span className="text-sm">Active Conditions ({allConditions.length})</span>
        </div>
        <div className="dsi-section-analysis border-collapse">
          {conditionTypeSummary.length === 0 ? (
            <div className="flex items-center justify-center h-24 opacity-50 text-sm italic">No conditions triggered.</div>
          ) : (
            <div>
              {conditionTypeSummary.map(({ type, count, modifierCount, aggregateModifier }) => {
                const isExpanded = expandedGroups[`cond_${type}`] ?? false;
                const conds = conditionsByType[type] || [];
                const typeLabel = type.replace(/_/g, ' ');
                return (
                  <div key={type}>
                    <div onClick={() => toggleGroup(`cond_${type}`)} className="flex items-center justify-between px-dsi-pad py-2.5 border-b border-dsi-outline/20 cursor-pointer hover:bg-dsi-background/20 transition-colors">
                      <div className="flex items-center gap-2">
                        {isExpanded ? <ChevronDown className="w-3.5 h-3.5 shrink-0" /> : <ChevronRight className="w-3.5 h-3.5 shrink-0" />}
                        <span className="text-sm font-bold capitalize">{typeLabel}</span>
                        <span className="text-[10px] opacity-40">({count})</span>
                      </div>
                      <div className="flex items-center gap-2">
                        {modifierCount > 0 && (
                          <span className="text-[10px] bg-dsi-info/15 text-dsi-info px-1.5 py-0.5 rounded font-bold">
                            {modifierCount} modifier{modifierCount > 1 ? 's' : ''} ({formatPercent(aggregateModifier, 0)})
                          </span>
                        )}
                      </div>
                    </div>
                    {isExpanded && conds.map((cond: any, cidx: number) => {
                      const actionKey = typeof cond.action === 'string' ? cond.action.toLowerCase() : (cond.action?.value || 'note');
                      const actionStyle = getStatusStyle(ACTION_PALETTE, actionKey);
                      return (
                        <div key={cidx} className="flex items-center justify-between px-dsi-pad py-2 pl-8 bg-dsi-background/10 border-b border-dsi-outline/5 hover:bg-dsi-background/20 transition-colors">
                          <div className="flex items-center gap-3 min-w-0">
                            <ShieldAlert className={`w-3 h-3 shrink-0 ${actionStyle.text}`} />
                            <div className="min-w-0">
                              <span className="text-sm block truncate">{cond.note || cond.source_name || 'Condition'}</span>
                              <span className="text-[10px] opacity-40 block">{cond.source_id}</span>
                              {type === 'direct_query' && (
                                <span className={`text-xs font-bold ${cond.response === true || cond.response === 'yes' ? 'text-dsi-positive' : cond.response === false || cond.response === 'no' ? 'text-dsi-negative' : 'opacity-70'}`}>
                                  Response: {typeof cond.response === 'boolean' ? (cond.response ? 'Yes' : 'No') : String(cond.response ?? 'N/A')}
                                </span>
                              )}
                            </div>
                          </div>
                          <div className="flex items-center gap-2 shrink-0 ml-2">
                            <StatusPill palette={ACTION_PALETTE} status={actionKey} size="md">
                              {actionKey.replace('_', ' ')}
                            </StatusPill>
                            {cond.action_value != null && typeof cond.action_value === 'number' && (
                              <span className="text-xs font-bold opacity-70 w-16 text-right">
                                {actionKey === 'modifier' ? formatPercent(cond.action_value, 0) :
                                 actionKey === 'tier_override' ? `→ T${cond.action_value}` :
                                 cond.action_value}
                              </span>
                            )}
                          </div>
                        </div>
                      );
                    })}
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>

    </div>
  );
}

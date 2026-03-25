"use client";

import { useEffect, useState, useMemo, useCallback } from "react";
import { useDsiStore } from "@/store/dsiStore";
import {
  Target, Activity, Calculator, RotateCcw, Paperclip,
  AlertTriangle, ShieldAlert, ChevronUp, ChevronDown, Gauge, ListFilter
} from "lucide-react";

// ─── Helpers ─────────────────────────────────────────────────────────────────

const formatNum = (num: number | null | undefined, decimals = 1) =>
  num !== null && num !== undefined ? Number(num).toFixed(decimals) : "-";

const ACTION_COLORS: Record<string, { bg: string; text: string }> = {
  modifier:      { bg: 'bg-blue-500/15', text: 'text-blue-400' },
  referral:      { bg: 'bg-amber-500/15', text: 'text-amber-400' },
  refer:         { bg: 'bg-amber-500/15', text: 'text-amber-400' },
  tier_override: { bg: 'bg-rose-500/15', text: 'text-rose-400' },
  flag:          { bg: 'bg-slate-500/15', text: 'text-slate-400' },
  note:          { bg: 'bg-slate-500/15', text: 'text-slate-400' },
};

// ─── Component ───────────────────────────────────────────────────────────────

export default function RiskTab() {
  const { activeSubmission, activeVersion, activeQuote, riskSignals, isFetchingRiskSignals, fetchRiskSignals } = useDsiStore();

  const [scenarioOverrides, setScenarioOverrides] = useState<Record<string, number>>({});
  const [filterMode, setFilterMode] = useState<'all' | 'impact' | 'conditions'>('all');

  useEffect(() => {
    if (activeVersion?.version_code) {
      fetchRiskSignals(activeVersion.version_code);
    }
  }, [activeVersion?.version_code, fetchRiskSignals]);

  // ─── Score stepper: click starts at actual score, then increments ────────
  const handleStep = useCallback((sigCode: string, origScore: number, direction: 1 | -1) => {
    setScenarioOverrides(prev => {
      const current = prev[sigCode] !== undefined ? prev[sigCode] : origScore;
      const next = Math.round((current + direction) * 10) / 10;
      // If stepping back to original, remove override
      if (Math.abs(next - origScore) < 0.05) {
        const { [sigCode]: _, ...rest } = prev;
        return rest;
      }
      return { ...prev, [sigCode]: Math.max(0, Math.min(100, next)) };
    });
  }, []);

  // ─── Scenario recalculation ──────────────────────────────────────────────
  const { enrichedSignals, scenarioCompositeScore } = useMemo(() => {
    if (!riskSignals || riskSignals.length === 0) return { enrichedSignals: [], scenarioCompositeScore: 0 };

    const groupStats: Record<string, { totalWeight: number, groupWeight: number }> = {};
    riskSignals.forEach((sig: any) => {
      const group = sig.group_code || 'ungrouped';
      if (!groupStats[group]) {
        groupStats[group] = { totalWeight: 0, groupWeight: sig.group_weight || 0 };
      }
      groupStats[group].totalWeight += (sig.weight || 0);
    });

    let newComposite = 0;
    const groupScores: Record<string, number> = {};

    const processedSignals = riskSignals.map((sig: any) => {
      const group = sig.group_code || 'ungrouped';
      const activeScore = scenarioOverrides[sig.code] !== undefined ? scenarioOverrides[sig.code] : (sig.score || 0);

      const weight = sig.weight || 0;
      const groupWeight = sig.group_weight || 0;
      const totalGroupWeight = groupStats[group].totalWeight || 1;

      const scenarioContribution = ((activeScore * weight) / totalGroupWeight) * groupWeight * 10;

      if (!groupScores[group]) groupScores[group] = 0;
      groupScores[group] += (activeScore * weight) / totalGroupWeight;

      return {
        ...sig,
        scenario_score: activeScore,
        scenario_contribution: scenarioContribution,
        is_overridden: scenarioOverrides[sig.code] !== undefined
      };
    });

    Object.keys(groupScores).forEach(group => {
      newComposite += (groupScores[group] * groupStats[group].groupWeight * 10);
    });

    processedSignals.sort((a: any, b: any) => {
      if (a.group_code < b.group_code) return -1;
      if (a.group_code > b.group_code) return 1;
      return (b.contribution || 0) - (a.contribution || 0);
    });

    return {
      enrichedSignals: processedSignals,
      scenarioCompositeScore: newComposite
    };
  }, [riskSignals, scenarioOverrides]);

  // ─── Scenario tier estimation from tier margin data ──────────────────────
  const scenarioTier = useMemo(() => {
    if (!activeVersion) return null;
    const origScore = activeVersion.pure_composite_score || 0;
    const tierMin = activeVersion.tier_margin_tier_min;
    const tierMax = activeVersion.tier_margin_tier_max;
    const currentTier = activeVersion.score_based_tier || activeVersion.final_tier;
    const betterTier = activeVersion.tier_margin_adjacent_better;
    const worseTier = activeVersion.tier_margin_adjacent_worse;

    if (tierMin == null || tierMax == null) return currentTier;

    if (scenarioCompositeScore < tierMin && betterTier != null) return betterTier;
    if (scenarioCompositeScore > tierMax && worseTier != null) return worseTier;
    return currentTier;
  }, [activeVersion, scenarioCompositeScore]);

  // ─── Conditions: map source_id → signal code for matching ────────────────
  const signalConditions = activeVersion?.signal_conditions || [];
  const queryConditions = activeVersion?.query_conditions || [];
  const allConditions = [...signalConditions, ...queryConditions];

  // Build lookup: which signal codes have conditions attached
  const conditionsBySignal = useMemo(() => {
    const map: Record<string, any[]> = {};
    for (const c of allConditions) {
      const key = c.source_id || c.signal_id || '';
      if (!map[key]) map[key] = [];
      map[key].push(c);
    }
    return map;
  }, [allConditions]);

  // ─── Apply UI Filters to Enriched Signals ────────────────────────────────
  const displayedSignals = useMemo(() => {
    if (filterMode === 'all') return enrichedSignals;
    
    if (filterMode === 'conditions') {
      return enrichedSignals.filter((sig: any) => conditionsBySignal[sig.code] || conditionsBySignal[sig.signal_id]);
    }
    
    if (filterMode === 'impact') {
      const sorted = [...enrichedSignals].sort((a: any, b: any) => Math.abs(b.contribution || 0) - Math.abs(a.contribution || 0));
      // Return anything moving the score by > 2.0, or at least the top 5 movers so the list isn't empty
      return sorted.filter((sig: any, idx: number) => Math.abs(sig.contribution || 0) >= 2.0 || idx < 5);
    }
    
    return enrichedSignals;
  }, [enrichedSignals, filterMode, conditionsBySignal]);

  if (!activeSubmission || !activeVersion) return null;

  const scoreDiff = scenarioCompositeScore - (activeVersion.pure_composite_score || 0);
  const tierChanged = scenarioTier !== null && scenarioTier !== (activeVersion.score_based_tier || activeVersion.final_tier);

  // Tier margin data
  const marginPct = activeVersion.tier_margin_percentile;
  const tierMin = activeVersion.tier_margin_tier_min;
  const tierMax = activeVersion.tier_margin_tier_max;
  const distBetter = activeVersion.tier_margin_distance_better;
  const distWorse = activeVersion.tier_margin_distance_worse;
  const hasTierMargin = marginPct != null && tierMin != null && tierMax != null;

  return (
    <div className="
      w-full no-scrollbar
      animate-in fade-in duration-500 pb-12"
      >
      {/* STICKY WRAPPER */}
      <div className="
        sticky top-0 z-20
        bg-dsi-background
        pt-3 pb-2"
        >

        {/* SECTION HEADER */}
        <div className="
          flex gap-dsi-pad
          rounded-t-xl
          border-b-1 border-dsi-outline/50
          overflow-x-hidden whitespace-nowrap border-collapse
          bg-dsi-analysis/60
          pl-dsi-pad
          pt-2 pb-2
        "
        >
          <Paperclip className="icon"/><span className="text-sm">Key Details</span>
        </div>

        {/* KEY INFORMATION CARD */}
        <div className="
          grid grid-cols-[10%_35%_55%] grid-rows-1
          border-b-3 border-dsi-contrast-background
          overflow-x-hidden whitespace-nowrap border-collapse
          rounded-b-xl
          bg-dsi-analysis shadow-sm
          pt-2 pb-2"
        >
          <div className="text-left pl-dsi-pad pr-dsi-pad border-r-1 border-dsi-outline/50 overflow-x-hidden">
            <span className="text-sm">Status:</span><span className="pl-2 uppercase font-bold">{activeQuote.status}</span>
          </div>

          <div className="text-center pl-dsi-pad pr-dsi-pad border-r-1 border-dsi-outline/50 overflow-x-hidden">
            {(activeQuote.status === 'draft' || activeQuote.status === 'ready') && (
              <span className="">
                <span className="text-sm">Quote Valid From:</span><span className="pl-2 uppercase font-bold">{new Date(activeQuote.valid_from).toLocaleDateString()};</span>
                <span className="pl-2 pr-2"> </span>
                <span className="text-sm">Until:</span><span className="pl-2 uppercase font-bold">{new Date(activeQuote.valid_until).toLocaleDateString()}</span>
              </span>
            )}
            {activeQuote.status === 'bound' && (
              <span className="">
                  <span className="text-sm">Bound Date:</span><span className="pl-2 uppercase font-bold">{activeQuote.bound_at ? new Date(activeQuote.bound_at).toLocaleDateString() : 'N/A'}</span>
                  <span className="text-sm">Policy Reference:</span><span className="pl-2 uppercase font-bold">{activeQuote.policy_number || 'Pending'}</span>
              </span>
            )}
          </div>

          <div className="text-center pl-dsi-pad pr-dsi-pad overflow-x-hidden">
            <span className="text-sm">Submission Code: </span><span className="pl-2 uppercase font-bold">{activeSubmission.submission_code}</span>
            <span className="pl-6 pr-6">||</span>
            <span className="text-sm">Quote Code: </span><span className="pl-2 uppercase font-bold">{activeQuote.quote_code}</span>
          </div>

        </div>
      </div>

      {/* =======================================================================
          SUMMARY KPIs
          ======================================================================= */}
      <div className="flex flex-col pt-2 pb-2">
        <div className="
          flex justify-between items-center gap-dsi-pad
          rounded-t-xl
          border-b-1 border-dsi-outline/50
          overflow-x-hidden whitespace-nowrap border-collapse
          bg-dsi-analysis/60
          pl-dsi-pad pr-dsi-pad
          pt-2 pb-2
        ">
          <div className="flex items-center gap-dsi-pad">
            <Target className="icon"/><span className="text-sm">Risk Assessment Summary</span>
          </div>
          {Object.keys(scenarioOverrides).length > 0 && (
            <button
              onClick={() => setScenarioOverrides({})}
              className="flex items-center gap-2 text-xs hover:bg-dsi-outline/10 px-2 py-1 rounded transition-colors text-dsi-selected"
            >
              <RotateCcw className="w-3 h-3" /> Reset Scenarios
            </button>
          )}
        </div>
        <div className="
          flex flex-col flex-1
          border-b-3 border-dsi-contrast-background
          overflow-x-hidden whitespace-nowrap border-collapse
          rounded-b-xl
          bg-dsi-analysis shadow-sm
          pt-4 pb-4
        ">
          <div className="grid grid-cols-2 md:grid-cols-5 gap-6 pl-dsi-pad pr-dsi-pad">
            <div>
              <span className="opacity-70 block text-xs mb-1">Score-Based Tier</span>
              <span className="font-bold text-lg text-dsi-selected">
                Tier {activeVersion.score_based_tier || activeVersion.final_tier}
              </span>
            </div>
            <div>
              <span className="opacity-70 block text-xs mb-1">Confidence</span>
              <span className="font-bold text-lg">
                {((activeVersion.confidence || 0) * 100).toFixed(0)}%
              </span>
            </div>
            <div>
              <span className="opacity-70 block text-xs mb-1">Signal Coverage</span>
              <span className="font-bold text-lg">
                {((activeVersion.signal_coverage || 0) * 100).toFixed(0)}%
              </span>
            </div>
            <div className="border-l border-dsi-outline/20 pl-6">
              <span className="opacity-70 block text-xs mb-1">Original Composite</span>
              <span className="font-bold text-xl">
                {formatNum(activeVersion.pure_composite_score, 1)}
              </span>
            </div>
            <div className="border-l border-dsi-outline/20 pl-6">
              <span className="text-dsi-selected block text-xs mb-1 font-bold">Scenario Composite</span>
              <div className="flex items-baseline gap-2">
                <span className="font-bold text-2xl text-dsi-selected">
                  {formatNum(scenarioCompositeScore, 1)}
                </span>
                {Math.abs(scoreDiff) > 0.1 && (
                  <span className={`text-xs font-bold ${scoreDiff > 0 ? 'text-rose-400' : 'text-emerald-400'}`}>
                    ({scoreDiff > 0 ? '+' : ''}{formatNum(scoreDiff, 1)})
                  </span>
                )}
                {tierChanged && (
                  <span className={`text-xs font-bold ml-1 ${(scenarioTier || 0) > (activeVersion.score_based_tier || activeVersion.final_tier) ? 'text-rose-400' : 'text-emerald-400'}`}>
                    → Tier {scenarioTier}
                  </span>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* =======================================================================
          TIER MARGIN & SIGNAL CONDITIONS ROW
          ======================================================================= */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-2 pt-2 pb-2">

        {/* TIER MARGIN GAUGE */}
        <div className="flex flex-col">
          <div className="
            flex gap-dsi-pad
            rounded-t-xl
            border-b-1 border-dsi-outline/50
            overflow-x-hidden whitespace-nowrap border-collapse
            bg-dsi-analysis/60
            pl-dsi-pad
            pt-2 pb-2
          ">
            <Gauge className="icon"/><span className="text-sm">Tier Position</span>
          </div>
          <div className="
            flex flex-col flex-1
            border-b-3 border-dsi-contrast-background
            overflow-x-hidden border-collapse
            rounded-b-xl
            bg-dsi-analysis shadow-sm
            pt-4 pb-4
          ">
            {hasTierMargin ? (
              <div className="pl-dsi-pad pr-dsi-pad space-y-4">
                {/* Tier band visual */}
                <div>
                  <div className="flex justify-between text-xs opacity-60 mb-1">
                    <span>Tier {activeVersion.tier_margin_adjacent_better ?? '–'} boundary</span>
                    <span>Tier {activeVersion.score_based_tier || activeVersion.final_tier}</span>
                    <span>Tier {activeVersion.tier_margin_adjacent_worse ?? '–'} boundary</span>
                  </div>
                  <div className="relative h-6 bg-dsi-background rounded-full overflow-hidden border border-dsi-outline/20">
                    {/* Fill showing position in tier */}
                    <div
                      className="absolute inset-y-0 left-0 bg-gradient-to-r from-emerald-600/40 via-slate-500/40 to-rose-600/40 rounded-full"
                      style={{ width: '100%' }}
                    />
                    {/* Current position marker */}
                    <div
                      className="absolute top-0 bottom-0 w-0.5 bg-dsi-selected z-10"
                      style={{ left: `${Math.max(2, Math.min(98, (marginPct || 0) * 100))}%` }}
                    >
                      <div className="absolute -top-5 left-1/2 -translate-x-1/2 text-[10px] font-bold text-dsi-selected whitespace-nowrap">
                        {formatNum(activeVersion.pure_composite_score, 0)}
                      </div>
                    </div>
                    {/* Scenario position if different */}
                    {Math.abs(scoreDiff) > 0.1 && tierMin != null && tierMax != null && (
                      <div
                        className="absolute top-0 bottom-0 w-0.5 bg-amber-400 z-10"
                        style={{
                          left: `${Math.max(2, Math.min(98, ((scenarioCompositeScore - tierMin) / (tierMax - tierMin)) * 100))}%`
                        }}
                      >
                        <div className="absolute -bottom-5 left-1/2 -translate-x-1/2 text-[10px] font-bold text-amber-400 whitespace-nowrap">
                          {formatNum(scenarioCompositeScore, 0)}
                        </div>
                      </div>
                    )}
                  </div>
                  <div className="flex justify-between text-xs mt-1 opacity-50">
                    <span>{formatNum(tierMin, 0)}</span>
                    <span>{formatNum(tierMax, 0)}</span>
                  </div>
                </div>

                {/* Distance metrics */}
                <div className="grid grid-cols-3 gap-4 text-wrap">
                  <div className="border border-dsi-outline/20 rounded-lg p-3">
                    <span className="text-xs opacity-60 block mb-1">Position in Tier</span>
                    <span className="font-bold text-lg">{((marginPct || 0) * 100).toFixed(0)}%</span>
                    <span className="text-xs opacity-50 block">from tier floor</span>
                  </div>
                  <div className="border border-dsi-outline/20 rounded-lg p-3">
                    <span className="text-xs opacity-60 block mb-1">To Better Tier</span>
                    <span className={`font-bold text-lg ${distBetter != null && distBetter < 20 ? 'text-emerald-400' : ''}`}>
                      {distBetter != null ? `${formatNum(distBetter, 0)} pts` : 'N/A'}
                    </span>
                    {activeVersion.tier_margin_adjacent_better != null && (
                      <span className="text-xs opacity-50 block">→ Tier {activeVersion.tier_margin_adjacent_better}</span>
                    )}
                  </div>
                  <div className="border border-dsi-outline/20 rounded-lg p-3">
                    <span className="text-xs opacity-60 block mb-1">To Worse Tier</span>
                    <span className={`font-bold text-lg ${distWorse != null && distWorse < 20 ? 'text-rose-400' : ''}`}>
                      {distWorse != null ? `${formatNum(distWorse, 0)} pts` : 'N/A'}
                    </span>
                    {activeVersion.tier_margin_adjacent_worse != null && (
                      <span className="text-xs opacity-50 block">→ Tier {activeVersion.tier_margin_adjacent_worse}</span>
                    )}
                  </div>
                </div>
              </div>
            ) : (
              <div className="flex items-center justify-center h-24 opacity-50 text-sm italic">
                Tier margin data not available.
              </div>
            )}
          </div>
        </div>

        {/* SIGNAL CONDITIONS */}
        <div className="flex flex-col">
          <div className="
            flex gap-dsi-pad
            rounded-t-xl
            border-b-1 border-dsi-outline/50
            overflow-x-hidden whitespace-nowrap border-collapse
            bg-dsi-analysis/60
            pl-dsi-pad
            pt-2 pb-2
          ">
            <AlertTriangle className="icon"/>
            <span className="text-sm">Active Conditions ({allConditions.length})</span>
          </div>
          <div className="
            flex flex-col flex-1
            border-b-3 border-dsi-contrast-background
            border-collapse
            rounded-b-xl
            bg-dsi-analysis shadow-sm
            pt-2 pb-2
          ">
            {allConditions.length === 0 ? (
              <div className="flex items-center justify-center h-24 opacity-50 text-sm italic">
                No conditions triggered.
              </div>
            ) : (
              <div className="space-y-0">
                {allConditions.map((cond: any, idx: number) => {
                  const actionKey = typeof cond.action === 'string' ? cond.action.toLowerCase() : (cond.action?.value || 'note');
                  const colors = ACTION_COLORS[actionKey] || ACTION_COLORS.note;
                  return (
                    <div key={idx} className="flex items-center justify-between px-dsi-pad py-2 border-b border-dsi-outline/10 hover:bg-dsi-background/20 transition-colors">
                      <div className="flex items-center gap-3 min-w-0">
                        <ShieldAlert className={`w-3.5 h-3.5 shrink-0 ${colors.text}`} />
                        <div className="min-w-0">
                          <span className="text-sm block truncate">{cond.note || cond.source_name || 'Condition'}</span>
                          <span className="text-[10px] opacity-40 block">{cond.source_type}: {cond.source_id}</span>
                        </div>
                      </div>
                      <div className="flex items-center gap-2 shrink-0 ml-2">
                        <span className={`text-[10px] font-bold uppercase px-2 py-0.5 rounded ${colors.bg} ${colors.text}`}>
                          {actionKey.replace('_', ' ')}
                        </span>
                        {cond.action_value != null && typeof cond.action_value === 'number' && (
                          <span className="text-xs font-bold opacity-70 w-16 text-right">
                            {actionKey === 'modifier' ? `${(cond.action_value * 100).toFixed(0)}%` :
                             actionKey === 'tier_override' ? `→ T${cond.action_value}` :
                             cond.action_value}
                          </span>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        </div>

      </div>

      {/* =======================================================================
          SIGNAL TABLE WITH SCENARIO INPUTS
          ======================================================================= */}
      <div className="flex flex-col pt-2 pb-2">
        <div className="
          flex justify-between items-center gap-dsi-pad
          rounded-t-xl
          border-b-1 border-dsi-outline/50
          overflow-x-hidden whitespace-nowrap border-collapse
          bg-dsi-analysis/60
          pl-dsi-pad pr-dsi-pad
          pt-2 pb-2
        ">
          <div className="flex items-center gap-dsi-pad">
            <Calculator className="icon"/><span className="text-sm">Signal Breakdown & Scenario Sandbox</span>
          </div>

          <div className="flex items-center gap-3 text-xs">
            <ListFilter className="w-3 h-3 opacity-50" />
            <div className="flex items-center gap-1 border border-dsi-outline/20 rounded p-0.5">
              <button 
                onClick={() => setFilterMode('all')} 
                className={`px-2 py-1 rounded transition-colors ${filterMode === 'all' ? 'bg-dsi-selected/20 text-dsi-selected font-semibold' : 'opacity-50 hover:opacity-100'}`}
              >
                All
              </button>
              <button 
                onClick={() => setFilterMode('impact')} 
                className={`px-2 py-1 rounded transition-colors ${filterMode === 'impact' ? 'bg-dsi-selected/20 text-dsi-selected font-semibold' : 'opacity-50 hover:opacity-100'}`}
              >
                High Impact
              </button>
              <button 
                onClick={() => setFilterMode('conditions')} 
                className={`px-2 py-1 rounded transition-colors ${filterMode === 'conditions' ? 'bg-dsi-selected/20 text-dsi-selected font-semibold' : 'opacity-50 hover:opacity-100'}`}
              >
                Active Conditions
              </button>
            </div>
          </div>
        </div>

        <div className="
          flex flex-col flex-1
          border-b-3 border-dsi-contrast-background
          overflow-x-auto whitespace-nowrap border-collapse
          rounded-b-xl
          bg-dsi-analysis shadow-sm
          pt-2 pb-4
        ">
          {isFetchingRiskSignals ? (
            <div className="flex flex-col items-center justify-center py-10 opacity-50 space-y-4">
              <Activity className="w-6 h-6 animate-spin" />
            </div>
          ) : (
            <div className="w-full">
              <table className="w-full text-sm text-left whitespace-nowrap">
                <thead>
                  <tr className="text-center text-sm underline opacity-70">
                    <th className="py-2 pl-dsi-pad pr-dsi-pad font-normal text-left">Group</th>
                    <th className="py-2 px-2 font-normal text-right">Grp Wgt</th>
                    <th className="py-2 px-2 font-normal text-left">Signal Code</th>
                    <th className="py-2 px-2 font-normal">Proxy Tier</th>
                    <th className="py-2 px-2 font-normal text-center">Absent?</th>
                    <th className="py-2 px-2 font-normal text-right">Orig Score</th>
                    <th className="py-2 px-2 font-normal text-right">Sig Wgt</th>
                    <th className="py-2 px-2 font-normal text-right">Orig Contrib</th>
                    <th className="py-2 px-2 font-normal text-center text-dsi-selected border-l border-dsi-outline/20">Scenario Score</th>
                    <th className="py-2 pr-dsi-pad font-normal text-right text-dsi-selected">New Contrib</th>
                  </tr>
                </thead>
                <tbody>
                  {displayedSignals.length === 0 ? (
                    <tr>
                      <td colSpan={10} className="py-8 text-center text-dsi-selected opacity-50 italic">
                        No signals match the current filter.
                      </td>
                    </tr>
                  ) : (
                    displayedSignals.map((sig: any, idx: number) => {
                      const isNewGroup = idx === 0 || displayedSignals[idx - 1].group_code !== sig.group_code;
                      const hasCondition = conditionsBySignal[sig.code] || conditionsBySignal[sig.signal_id];
                      const currentScenarioScore = scenarioOverrides[sig.code] !== undefined ? scenarioOverrides[sig.code] : (sig.score || 0);

                      return (
                        <tr
                          key={`${sig.code}-${idx}`}
                          className={`
                            border-b border-dsi-outline/5 hover:bg-dsi-background/20 transition-colors
                            ${isNewGroup && idx !== 0 ? 'border-t-1 border-t-dsi-outline/50' : ''}
                            ${hasCondition ? 'bg-amber-500/5' : ''}
                          `}
                        >
                          <td className="py-2 pl-dsi-pad pr-dsi-pad opacity-70 truncate max-w-[120px]" title={sig.group_code}>
                            {isNewGroup ? sig.group_code : ''}
                          </td>
                          <td className="py-2 px-2 text-right opacity-50">
                            {isNewGroup ? formatNum(sig.group_weight, 2) : ''}
                          </td>
                          <td className="py-2 px-2 font-semibold">
                            <div className="flex items-center gap-1.5">
                              {sig.code}
                              {hasCondition && (
                                <AlertTriangle className="w-3 h-3 text-amber-400 shrink-0" title="Has active condition" />
                              )}
                            </div>
                          </td>
                          <td className="py-2 px-2 opacity-80 text-center">
                            {sig.proxy_tier || "-"}
                          </td>
                          <td className="py-2 px-2 text-center">
                            {sig.was_absent ? <span className="text-rose-400">Yes</span> : <span className="opacity-30">No</span>}
                          </td>
                          <td className="py-2 px-2 text-right">
                            {formatNum(sig.score, 1)}
                          </td>
                          <td className="py-2 px-2 text-right opacity-50">
                            {formatNum(sig.weight, 2)}
                          </td>
                          <td className="py-2 px-2 text-right">
                            {formatNum(sig.contribution, 2)}
                          </td>

                          {/* Scenario Input: stepper + text field */}
                          <td className="py-1 px-2 border-l border-dsi-outline/20">
                            <div className="flex items-center justify-center gap-0.5">
                              <button
                                onClick={() => handleStep(sig.code, sig.score || 0, -1)}
                                className="p-0.5 rounded hover:bg-dsi-outline/20 transition-colors text-dsi-selected/60 hover:text-dsi-selected"
                                title="Decrease score"
                              >
                                <ChevronDown className="w-3.5 h-3.5" />
                              </button>
                              <input
                                type="number"
                                className={`
                                  w-16 bg-dsi-background border rounded px-1.5 py-1 text-center text-sm outline-none transition-all
                                  [appearance:textfield] [&::-webkit-outer-spin-button]:appearance-none [&::-webkit-inner-spin-button]:appearance-none
                                  ${sig.is_overridden ? 'border-dsi-selected text-dsi-selected' : 'border-dsi-outline/20 focus:border-dsi-selected/50'}
                                `}
                                value={sig.is_overridden ? currentScenarioScore : ''}
                                placeholder={formatNum(sig.score, 1)}
                                onChange={(e) => {
                                  const val = e.target.value;
                                  setScenarioOverrides(prev => {
                                    const next = { ...prev };
                                    if (val === "") {
                                      delete next[sig.code];
                                    } else {
                                      next[sig.code] = parseFloat(val);
                                    }
                                    return next;
                                  });
                                }}
                              />
                              <button
                                onClick={() => handleStep(sig.code, sig.score || 0, 1)}
                                className="p-0.5 rounded hover:bg-dsi-outline/20 transition-colors text-dsi-selected/60 hover:text-dsi-selected"
                                title="Increase score"
                              >
                                <ChevronUp className="w-3.5 h-3.5" />
                              </button>
                            </div>
                          </td>
                          <td className={`py-2 pr-dsi-pad text-right font-bold ${sig.is_overridden ? 'text-dsi-selected' : ''}`}>
                            {formatNum(sig.scenario_contribution, 2)}
                          </td>
                        </tr>
                      );
                    })
                  )}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>

    </div>
  );
}
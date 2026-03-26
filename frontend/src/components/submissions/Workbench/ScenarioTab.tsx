"use client";

import { useEffect, useState, useMemo, useCallback } from "react";
import { useDsiStore } from "@/store/dsiStore";
import {
  Paperclip, RotateCcw, Activity, ChevronUp, ChevronDown,
  ChevronRight, ShieldAlert, FlaskConical, ArrowRightToLine, PenLine, Shield
} from "lucide-react";
import { runFullCascade, distributeGroupOverride, ScenarioOverrides, ScenarioResult } from "@/lib/scenarioEngine";
import { formatNum } from "@/lib/format";

const fmtDollar = (num: number | null | undefined) =>
  num != null ? `$${Number(num).toLocaleString(undefined, { maximumFractionDigits: 0 })}` : "-";

const deltaColor = (s: number, o: number) =>
  Math.abs(s - o) < 0.01 ? '' : s > o ? 'text-dsi-negative' : 'text-dsi-positive';

export default function ScenarioTab() {
  const {
    activeSubmission, activeVersion, activeQuote,
    riskSignals, isFetchingRiskSignals, fetchRiskSignals
  } = useDsiStore();

  const [signalOverrides, setSignalOverrides] = useState<Record<string, number>>({});
  const [lossModifierOverride, setLossModifierOverride] = useState<number | null>(null);
  const [exposureModifierOverride, setExposureModifierOverride] = useState<number | null>(null);
  const [limitOverride, setLimitOverride] = useState<number | null>(null);
  const [deductibleOverride, setDeductibleOverride] = useState<number | null>(null);
  const [expandedGroups, setExpandedGroups] = useState<Record<string, boolean>>({});

  useEffect(() => {
    if (activeVersion?.version_code) fetchRiskSignals(activeVersion.version_code);
  }, [activeVersion?.version_code, fetchRiskSignals]);

  const toggleGroup = (g: string) => setExpandedGroups(p => ({ ...p, [g]: !p[g] }));

  const handleStep = useCallback((sigCode: string, origScore: number, dir: 1 | -1) => {
    setSignalOverrides(prev => {
      const cur = prev[sigCode] !== undefined ? prev[sigCode] : origScore;
      const next = Math.round((cur + dir) * 10) / 10;
      if (Math.abs(next - origScore) < 0.05) { const { [sigCode]: _, ...rest } = prev; return rest; }
      return { ...prev, [sigCode]: Math.max(0, Math.min(100, next)) };
    });
  }, []);

  // F2: Group-level override — distributes proportionally
  const handleGroupOverride = useCallback((groupCode: string, targetScore: number) => {
    if (!riskSignals) return;
    setSignalOverrides(prev => distributeGroupOverride(riskSignals, groupCode, targetScore, prev));
  }, [riskSignals]);

  const resetAll = () => {
    setSignalOverrides({});
    setLossModifierOverride(null);
    setExposureModifierOverride(null);
    setLimitOverride(null);
    setDeductibleOverride(null);
  };

  const hasAnyOverride = Object.keys(signalOverrides).length > 0
    || lossModifierOverride !== null || exposureModifierOverride !== null
    || limitOverride !== null || deductibleOverride !== null;

  const scenario: ScenarioResult | null = useMemo(() => {
    if (!activeVersion || !riskSignals) return null;
    return runFullCascade(riskSignals, activeVersion, {
      signalOverrides, lossModifierOverride, exposureModifierOverride, limitOverride, deductibleOverride,
    });
  }, [activeVersion, riskSignals, signalOverrides, lossModifierOverride, exposureModifierOverride, limitOverride, deductibleOverride]);

  // Group signals for accordion
  const groupScores = activeVersion?.group_scores || {};
  const groupEntries = Object.entries(groupScores).sort(([, a]: any, [, b]: any) => (b?.risk_contribution || 0) - (a?.risk_contribution || 0));

  const signalsByGroup = useMemo(() => {
    const map: Record<string, any[]> = {};
    for (const sig of (riskSignals || [])) {
      const g = sig.group_code || 'ungrouped';
      if (!map[g]) map[g] = [];
      map[g].push(sig);
    }
    for (const g of Object.keys(map)) map[g].sort((a: any, b: any) => (b.contribution || 0) - (a.contribution || 0));
    return map;
  }, [riskSignals]);

  // Calculate scenario group scores for display
  const scenarioGroupScores = useMemo(() => {
    const result: Record<string, number> = {};
    for (const [groupId] of groupEntries) {
      const sigs = signalsByGroup[groupId] || [];
      const totalW = sigs.reduce((s: number, sig: any) => s + (sig.weight || 0), 0);
      if (totalW === 0) { result[groupId] = 0; continue; }
      let score = 0;
      for (const sig of sigs) {
        const sc = signalOverrides[sig.code] !== undefined ? signalOverrides[sig.code] : (sig.score || 0);
        score += (sc * (sig.weight || 0)) / totalW;
      }
      result[groupId] = score;
    }
    return result;
  }, [groupEntries, signalsByGroup, signalOverrides]);

  if (!activeSubmission || !activeVersion) return null;

  // Loss correlation detail
  const lossConfig = activeVersion.loss_correlation_config;
  const lossBandInterp = activeVersion.loss_band_interpretation;

  // Exposure band detail
  const expBandInterp = activeVersion.exposure_band_interpretation;

  return (
    <div className="w-full no-scrollbar animate-in fade-in duration-500 pb-12">

      {/* STICKY HEADER */}
      <div className="sticky top-0 z-20 bg-dsi-background pt-3 pb-2">
        <div className="flex gap-dsi-pad rounded-t-xl border-b-1 border-dsi-outline/50 overflow-x-hidden whitespace-nowrap border-collapse bg-dsi-analysis/60 pl-dsi-pad pt-2 pb-2">
          <Paperclip className="icon"/><span className="text-sm">Key Details</span>
        </div>
        <div className="grid grid-cols-[10%_35%_55%] grid-rows-1 border-b-3 border-dsi-contrast-background overflow-x-hidden whitespace-nowrap border-collapse rounded-b-xl bg-dsi-analysis shadow-sm pt-2 pb-2">
          <div className="text-left pl-dsi-pad pr-dsi-pad border-r-1 border-dsi-outline/50 overflow-x-hidden">
            <span className="text-sm">Status:</span><span className="pl-2 uppercase font-bold">{activeQuote?.status}</span>
          </div>
          <div className="text-center pl-dsi-pad pr-dsi-pad border-r-1 border-dsi-outline/50 overflow-x-hidden">
            {(activeQuote?.status === 'draft' || activeQuote?.status === 'ready') && (
              <span>
                <span className="text-sm">Quote Valid From:</span><span className="pl-2 uppercase font-bold">{activeQuote?.valid_from ? new Date(activeQuote.valid_from).toLocaleDateString() : 'N/A'};</span>
                <span className="pl-2 pr-2"> </span>
                <span className="text-sm">Until:</span><span className="pl-2 uppercase font-bold">{activeQuote?.valid_until ? new Date(activeQuote.valid_until).toLocaleDateString() : 'N/A'}</span>
              </span>
            )}
          </div>
          <div className="text-center pl-dsi-pad pr-dsi-pad overflow-x-hidden">
            <span className="text-sm">Submission Code: </span><span className="pl-2 uppercase font-bold">{activeSubmission?.submission_code}</span>
            <span className="pl-6 pr-6">||</span>
            <span className="text-sm">Quote Code: </span><span className="pl-2 uppercase font-bold">{activeQuote?.quote_code}</span>
          </div>
        </div>
      </div>

      {isFetchingRiskSignals || !scenario ? (
        <div className="flex flex-col items-center justify-center py-20 opacity-50 space-y-4">
          <Activity className="w-8 h-8 animate-spin" />
          <p className="text-sm tracking-widest uppercase">Loading Scenario Engine...</p>
        </div>
      ) : (
        <>
          {/* ══════════════════════════════════════════════════════════════
              F1/F2: GROUP → SIGNAL ACCORDION WITH OVERRIDES
              ══════════════════════════════════════════════════════════════ */}
          <div className="flex flex-col pt-2 pb-2">
            <div className="flex justify-between items-center gap-dsi-pad rounded-t-xl border-b-1 border-dsi-outline/50 overflow-x-hidden whitespace-nowrap border-collapse bg-dsi-analysis/60 pl-dsi-pad pr-dsi-pad pt-2 pb-2">
              <div className="flex items-center gap-dsi-pad">
                <FlaskConical className="icon"/><span className="text-sm">Signal Overrides</span>
                {Object.keys(signalOverrides).length > 0 && (
                  <span className="text-[10px] bg-dsi-selected/20 text-dsi-selected px-2 py-0.5 rounded font-bold">
                    {Object.keys(signalOverrides).length} modified
                  </span>
                )}
              </div>
              {hasAnyOverride && (
                <button onClick={resetAll} className="flex items-center gap-2 text-xs hover:bg-dsi-outline/10 px-2 py-1 rounded transition-colors text-dsi-selected">
                  <RotateCcw className="w-3 h-3" /> Reset All
                </button>
              )}
            </div>

            {/* Composite comparison header */}
            <div className="grid grid-cols-2 gap-4 bg-dsi-analysis border-x border-dsi-outline/10 px-dsi-pad py-3">
              <div>
                <span className="opacity-50 block text-xs mb-1">Original Composite</span>
                <span className="font-bold text-xl">{formatNum(scenario.original_composite, 1)}</span>
                <span className="text-xs opacity-40 ml-2">Tier {scenario.original_tier}</span>
              </div>
              <div>
                <span className="text-dsi-selected block text-xs mb-1 font-bold">Scenario Composite</span>
                <div className="flex items-baseline gap-2">
                  <span className="font-bold text-2xl text-dsi-selected">{formatNum(scenario.composite_score, 1)}</span>
                  {Math.abs(scenario.composite_score - scenario.original_composite) > 0.1 && (
                    <span className={`text-xs font-bold ${deltaColor(scenario.composite_score, scenario.original_composite)}`}>
                      ({scenario.composite_score > scenario.original_composite ? '+' : ''}{formatNum(scenario.composite_score - scenario.original_composite, 1)})
                    </span>
                  )}
                  {scenario.tier && scenario.tier.tier_id !== scenario.original_tier && (
                    <span className={`text-xs font-bold ml-1 ${scenario.tier.tier_id > scenario.original_tier ? 'text-dsi-negative' : 'text-dsi-positive'}`}>
                      → Tier {scenario.tier.tier_id}
                    </span>
                  )}
                </div>
              </div>
            </div>

            {/* Group accordion */}
            <div className="flex flex-col flex-1 border-b-3 border-dsi-contrast-background overflow-x-auto whitespace-nowrap border-collapse rounded-b-xl bg-dsi-analysis shadow-sm pt-0 pb-2">
              {/* Column headers */}
              <div className="grid grid-cols-[1fr_80px_80px_80px_120px_80px] gap-0 text-[11px] underline opacity-70 px-dsi-pad py-2">
                <span>Group / Signal</span>
                <span className="text-right">Orig Score</span>
                <span className="text-right">Weight</span>
                <span className="text-right">Contribution</span>
                <span className="text-center text-dsi-selected">Scenario</span>
                <span className="text-right text-dsi-selected">New Score</span>
              </div>

              {groupEntries.map(([groupId, gs]: [string, any]) => {
                const isExpanded = expandedGroups[groupId] ?? false;
                const signals = signalsByGroup[groupId] || [];
                const origGroupScore = gs?.risk_score || 0;
                const scenGroupScore = scenarioGroupScores[groupId] || origGroupScore;
                const groupChanged = Math.abs(scenGroupScore - origGroupScore) > 0.1;

                return (
                  <div key={groupId}>
                    {/* GROUP HEADER */}
                    <div className="grid grid-cols-[1fr_80px_80px_80px_120px_80px] gap-0 px-dsi-pad py-2.5 border-t border-dsi-outline/20 cursor-pointer hover:bg-dsi-background/20 transition-colors">
                      <div className="flex items-center gap-2" onClick={() => toggleGroup(groupId)}>
                        {isExpanded ? <ChevronDown className="w-3.5 h-3.5 shrink-0" /> : <ChevronRight className="w-3.5 h-3.5 shrink-0" />}
                        <span className="font-bold text-sm">{groupId}</span>
                        <span className="text-[10px] opacity-40">({signals.length})</span>
                      </div>
                      <span className="text-right text-sm" onClick={() => toggleGroup(groupId)}>{formatNum(origGroupScore, 1)}</span>
                      <span className="text-right text-sm opacity-60" onClick={() => toggleGroup(groupId)}>{formatNum(gs?.risk_weight, 2)}</span>
                      <span className="text-right text-sm font-bold" onClick={() => toggleGroup(groupId)}>{formatNum(gs?.risk_contribution, 1)}</span>
                      {/* F2: Group-level override input */}
                      <div className="flex items-center justify-center gap-0.5">
                        <button onClick={() => handleGroupOverride(groupId, scenGroupScore - 1)} className="p-0.5 rounded hover:bg-dsi-outline/20 text-dsi-selected/60 hover:text-dsi-selected">
                          <ChevronDown className="w-3.5 h-3.5" />
                        </button>
                        <input
                          type="number"
                          className={`w-16 bg-dsi-background border rounded px-1.5 py-1 text-center text-sm outline-none [appearance:textfield] [&::-webkit-outer-spin-button]:appearance-none [&::-webkit-inner-spin-button]:appearance-none ${groupChanged ? 'border-dsi-selected text-dsi-selected' : 'border-dsi-outline/20'}`}
                          value={groupChanged ? Math.round(scenGroupScore * 10) / 10 : ''}
                          placeholder={formatNum(origGroupScore, 1)}
                          onChange={(e) => {
                            if (e.target.value === '') {
                              // Reset group signals to originals
                              setSignalOverrides(prev => {
                                const next = { ...prev };
                                signals.forEach((s: any) => delete next[s.code]);
                                return next;
                              });
                            } else {
                              handleGroupOverride(groupId, parseFloat(e.target.value));
                            }
                          }}
                        />
                        <button onClick={() => handleGroupOverride(groupId, scenGroupScore + 1)} className="p-0.5 rounded hover:bg-dsi-outline/20 text-dsi-selected/60 hover:text-dsi-selected">
                          <ChevronUp className="w-3.5 h-3.5" />
                        </button>
                      </div>
                      <span className={`text-right text-sm font-bold ${groupChanged ? 'text-dsi-selected' : ''}`}>
                        {formatNum(scenGroupScore, 1)}
                      </span>
                    </div>

                    {/* SIGNAL ROWS */}
                    {isExpanded && signals.map((sig: any, sidx: number) => {
                      const isOverridden = signalOverrides[sig.code] !== undefined;
                      const currentScore = isOverridden ? signalOverrides[sig.code] : (sig.score || 0);
                      return (
                        <div key={`${sig.code}-${sidx}`} className="grid grid-cols-[1fr_80px_80px_80px_120px_80px] gap-0 px-dsi-pad py-1.5 bg-dsi-background/10 hover:bg-dsi-background/20 transition-colors">
                          <div className="flex items-center gap-2 pl-6">
                            <span className="text-sm">{sig.code}</span>
                            {sig.was_absent && <span className="text-[10px] text-dsi-negative font-bold">ABSENT</span>}
                          </div>
                          <span className="text-right text-sm">{formatNum(sig.score, 1)}</span>
                          <span className="text-right text-sm opacity-50">{formatNum(sig.weight, 2)}</span>
                          <span className="text-right text-sm">{formatNum(sig.contribution, 2)}</span>
                          <div className="flex items-center justify-center gap-0.5">
                            <button onClick={() => handleStep(sig.code, sig.score || 0, -1)} className="p-0.5 rounded hover:bg-dsi-outline/20 text-dsi-selected/60 hover:text-dsi-selected">
                              <ChevronDown className="w-3 h-3" />
                            </button>
                            <input
                              type="number"
                              className={`w-14 bg-dsi-background border rounded px-1 py-0.5 text-center text-xs outline-none [appearance:textfield] [&::-webkit-outer-spin-button]:appearance-none [&::-webkit-inner-spin-button]:appearance-none ${isOverridden ? 'border-dsi-selected text-dsi-selected' : 'border-dsi-outline/20 focus:border-dsi-selected/50'}`}
                              value={isOverridden ? currentScore : ''}
                              placeholder={formatNum(sig.score, 1)}
                              onChange={(e) => {
                                const val = e.target.value;
                                setSignalOverrides(prev => {
                                  const next = { ...prev };
                                  if (val === '') delete next[sig.code];
                                  else next[sig.code] = parseFloat(val);
                                  return next;
                                });
                              }}
                            />
                            <button onClick={() => handleStep(sig.code, sig.score || 0, 1)} className="p-0.5 rounded hover:bg-dsi-outline/20 text-dsi-selected/60 hover:text-dsi-selected">
                              <ChevronUp className="w-3 h-3" />
                            </button>
                          </div>
                          <span className={`text-right text-sm ${isOverridden ? 'font-bold text-dsi-selected' : ''}`}>
                            {formatNum(currentScore, 1)}
                          </span>
                        </div>
                      );
                    })}
                  </div>
                );
              })}
            </div>
          </div>

          {/* ══════════════════════════════════════════════════════════════
              F3/F4: LOSS & EXPOSURE MODIFIER DETAIL
              ══════════════════════════════════════════════════════════════ */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-2 pt-2 pb-2">
            {/* Loss modifier detail */}
            <div className="flex flex-col">
              <div className="flex gap-dsi-pad rounded-t-xl border-b-1 border-dsi-outline/50 overflow-x-hidden whitespace-nowrap border-collapse bg-dsi-analysis/60 pl-dsi-pad pt-2 pb-2">
                <Shield className="icon"/><span className="text-sm">Loss Modifier</span>
              </div>
              <div className="flex flex-col flex-1 border-b-3 border-dsi-contrast-background rounded-b-xl bg-dsi-analysis shadow-sm pt-4 pb-4 px-dsi-pad space-y-3">
                {/* Calculated path */}
                {scenario.loss_modifier ? (
                  <div className="border border-dsi-outline/20 rounded-lg p-3 space-y-2 text-wrap">
                    <span className="text-xs opacity-60 block">Calculated from signal overrides</span>
                    <div className="grid grid-cols-3 gap-2 text-sm">
                      <div><span className="text-[10px] opacity-50 block">Propensity</span><span className="font-bold">{formatNum(scenario.loss_modifier.propensity_score, 1)}</span> <span className="text-[10px] opacity-40 uppercase">{scenario.loss_modifier.propensity_band}</span></div>
                      <div><span className="text-[10px] opacity-50 block">Freq Mult</span><span className="font-bold">{formatNum(scenario.loss_modifier.frequency_multiplier, 3)}x</span></div>
                      <div><span className="text-[10px] opacity-50 block">Sev Mult</span><span className="font-bold">{formatNum(scenario.loss_modifier.severity_multiplier, 3)}x</span></div>
                    </div>
                    <div className="flex items-center justify-between pt-2 border-t border-dsi-outline/10">
                      <span className="text-xs opacity-60">Combined</span>
                      <span className={`font-bold text-lg ${deltaColor(scenario.scenario_loss_combined, scenario.original_loss_combined)}`}>
                        {formatNum(scenario.scenario_loss_combined, 3)}x
                      </span>
                    </div>
                  </div>
                ) : (
                  <div className="border border-dsi-outline/20 rounded-lg p-3 text-wrap">
                    <span className="text-xs opacity-60 block mb-1">Original: {formatNum(scenario.original_loss_combined, 3)}x</span>
                    <span className="text-[10px] opacity-40">{lossConfig ? 'Adjust signals above to recalculate' : 'Loss correlation config not available — override directly'}</span>
                  </div>
                )}
                {/* Direct override */}
                <div className="flex items-center gap-2">
                  <span className="text-xs opacity-60 shrink-0">Override:</span>
                  <input
                    type="number" step="0.01"
                    className={`w-20 bg-dsi-background border rounded px-2 py-1 text-sm outline-none [appearance:textfield] [&::-webkit-outer-spin-button]:appearance-none [&::-webkit-inner-spin-button]:appearance-none ${lossModifierOverride !== null ? 'border-dsi-selected text-dsi-selected' : 'border-dsi-outline/20'}`}
                    value={lossModifierOverride ?? ''}
                    placeholder={formatNum(scenario.scenario_loss_combined, 3)}
                    onChange={(e) => setLossModifierOverride(e.target.value === '' ? null : parseFloat(e.target.value))}
                  />
                  <span className="text-xs opacity-40">x</span>
                </div>
              </div>
            </div>

            {/* Exposure modifier detail */}
            <div className="flex flex-col">
              <div className="flex gap-dsi-pad rounded-t-xl border-b-1 border-dsi-outline/50 overflow-x-hidden whitespace-nowrap border-collapse bg-dsi-analysis/60 pl-dsi-pad pt-2 pb-2">
                <Shield className="icon"/><span className="text-sm">Exposure Modifier</span>
              </div>
              <div className="flex flex-col flex-1 border-b-3 border-dsi-contrast-background rounded-b-xl bg-dsi-analysis shadow-sm pt-4 pb-4 px-dsi-pad space-y-3">
                <div className="border border-dsi-outline/20 rounded-lg p-3 text-wrap">
                  <span className="text-xs opacity-60 block mb-2">Band lookup from exposure value</span>
                  <div className="grid grid-cols-3 gap-2 text-sm">
                    <div><span className="text-[10px] opacity-50 block">Value</span><span className="font-bold">{fmtDollar(activeVersion?.exposure_value)}</span></div>
                    <div><span className="text-[10px] opacity-50 block">Band</span><span className="font-bold uppercase">{activeVersion?.exposure_band_label || 'N/A'}</span></div>
                    <div><span className="text-[10px] opacity-50 block">Modifier</span><span className="font-bold">{formatNum(scenario.original_exposure_modifier, 3)}x</span></div>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-xs opacity-60 shrink-0">Override:</span>
                  <input
                    type="number" step="0.01"
                    className={`w-20 bg-dsi-background border rounded px-2 py-1 text-sm outline-none [appearance:textfield] [&::-webkit-outer-spin-button]:appearance-none [&::-webkit-inner-spin-button]:appearance-none ${exposureModifierOverride !== null ? 'border-dsi-selected text-dsi-selected' : 'border-dsi-outline/20'}`}
                    value={exposureModifierOverride ?? ''}
                    placeholder={formatNum(scenario.original_exposure_modifier, 3)}
                    onChange={(e) => setExposureModifierOverride(e.target.value === '' ? null : parseFloat(e.target.value))}
                  />
                  <span className="text-xs opacity-40">x</span>
                </div>
                {/* Limit + Deductible side by side */}
                <div className="grid grid-cols-2 gap-3 border-t border-dsi-outline/10 pt-3">
                  <div>
                    <span className="text-xs opacity-60 block mb-1">Policy Limit</span>
                    <div className="flex items-center gap-1">
                      <span className="text-xs opacity-40">$</span>
                      <input type="number" step="1000000"
                        className={`w-full bg-dsi-background border rounded px-2 py-1 text-sm outline-none [appearance:textfield] [&::-webkit-outer-spin-button]:appearance-none [&::-webkit-inner-spin-button]:appearance-none ${limitOverride !== null ? 'border-dsi-selected text-dsi-selected' : 'border-dsi-outline/20'}`}
                        value={limitOverride ?? ''}
                        placeholder={String(activeVersion?.final_premium_detail?.limit || '')}
                        onChange={(e) => setLimitOverride(e.target.value === '' ? null : parseFloat(e.target.value))}
                      />
                    </div>
                    <span className="text-[10px] opacity-30 block mt-1">ILF: {formatNum(activeVersion?.ilf_factor, 3)}x</span>
                  </div>
                  <div>
                    <span className="text-xs opacity-60 block mb-1">Deductible</span>
                    <div className="flex items-center gap-1">
                      <span className="text-xs opacity-40">$</span>
                      <input type="number" step="25000"
                        className={`w-full bg-dsi-background border rounded px-2 py-1 text-sm outline-none [appearance:textfield] [&::-webkit-outer-spin-button]:appearance-none [&::-webkit-inner-spin-button]:appearance-none ${deductibleOverride !== null ? 'border-dsi-selected text-dsi-selected' : 'border-dsi-outline/20'}`}
                        value={deductibleOverride ?? ''}
                        placeholder={String(activeVersion?.final_premium_detail?.deductible || '')}
                        onChange={(e) => setDeductibleOverride(e.target.value === '' ? null : parseFloat(e.target.value))}
                      />
                    </div>
                    <span className="text-[10px] opacity-30 block mt-1">Factor: {formatNum(activeVersion?.final_premium_detail?.deductible_factor, 3)}x</span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* ══════════════════════════════════════════════════════════════
              F5: PRICING CASCADE (PricingTab style)
              ══════════════════════════════════════════════════════════════ */}
          <div className="flex flex-col pt-2 pb-2">
            <div className="flex gap-dsi-pad rounded-t-xl border-b-1 border-dsi-outline/50 overflow-x-hidden whitespace-nowrap border-collapse bg-dsi-analysis/60 pl-dsi-pad pt-2 pb-2">
              <PenLine className="icon"/><span className="text-sm">Pricing Cascade — Original vs Scenario</span>
            </div>
            <div className="flex flex-col flex-1 border-b-3 border-dsi-contrast-background rounded-b-xl bg-dsi-analysis shadow-sm pt-4 pb-4">

              {/* Grid: matching PricingTab cols */}
              <div className="grid grid-cols-[50%_10%_20%_20%] px-dsi-pad">

                {/* TIER */}
                <div className="flex gap-dsi-pad text-sm pb-2">
                  <ArrowRightToLine className="icon"/> Tier Assignment
                </div>
                <div className="text-xs text-right pr-dsi-pad border-r border-dsi-outline/50 content-center">Original</div>
                <div className="text-sm text-right bg-dsi-selected/5 content-center">Tier {scenario.original_tier}</div>
                <div className={`pl-dsi-pad pr-dsi-pad text-right text-sm font-bold bg-dsi-selected/10 content-center ${scenario.tier && scenario.tier.tier_id !== scenario.original_tier ? 'text-dsi-selected' : ''}`}>
                  {scenario.tier ? `Tier ${scenario.tier.tier_id}` : `Tier ${scenario.original_tier}`}
                  {scenario.tier && scenario.tier.tier_id !== scenario.original_tier && (
                    <span className="text-[10px] ml-1 opacity-60">({scenario.tier.label})</span>
                  )}
                </div>

                {/* BASE PREMIUM */}
                <div className="flex gap-dsi-pad text-sm pt-3 pb-2 border-t border-dsi-outline/10">
                  <ArrowRightToLine className="icon"/> Base Premium
                </div>
                <div className="text-xs text-right pr-dsi-pad border-r border-dsi-outline/50 border-t border-dsi-outline/10 content-center pt-3">
                  {activeVersion?.base_premium_method || ''}
                </div>
                <div className="text-sm text-right bg-dsi-selected/5 border-t border-dsi-outline/10 content-center pt-3">
                  {fmtDollar(scenario.original_base_premium)}
                </div>
                <div className={`pl-dsi-pad pr-dsi-pad text-right text-sm font-bold bg-dsi-selected/10 border-t border-dsi-outline/10 content-center pt-3 ${Math.abs(scenario.base_premium - scenario.original_base_premium) > 1 ? 'text-dsi-selected' : ''}`}>
                  {fmtDollar(scenario.base_premium)}
                </div>

                {/* MODIFIERS */}
                <div className="flex gap-dsi-pad text-sm pt-3 pb-2 border-t border-dsi-outline/10">
                  <PenLine className="icon"/> Adjustments
                </div>
                <div className="text-xs text-center border-t border-dsi-outline/10 content-center pt-3">Factor</div>
                <div className="text-xs text-right border-t border-dsi-outline/10 content-center pt-3">Original</div>
                <div className="text-xs text-right pr-dsi-pad border-t border-dsi-outline/10 content-center pt-3 text-dsi-selected font-bold">Scenario</div>
              </div>

              {/* Modifier rows */}
              {scenario.waterfall.map((step, idx) => {
                const changed = Math.abs(step.scenario_factor - step.original_factor) > 0.001;
                return (
                  <div key={idx} className="contents">
                    <div className={`grid grid-cols-[50%_10%_20%_20%] px-dsi-pad ${changed ? 'bg-dsi-selected/5' : ''}`}>
                      <div className="text-xs pl-dsi-padicon py-1.5 truncate" title={step.name}>{step.name}</div>
                      <div className="text-center text-xs content-center">{step.scenario_factor.toFixed(3)}x</div>
                      <div className="text-right text-xs content-center">{step.original_factor.toFixed(3)}x</div>
                      <div className={`pr-dsi-pad text-right text-xs content-center font-bold ${changed ? 'text-dsi-selected' : ''}`}>
                        {step.scenario_factor.toFixed(3)}x
                      </div>
                    </div>
                  </div>
                );
              })}

              <div className="grid grid-cols-[50%_10%_20%_20%] px-dsi-pad border-t border-dsi-outline/20 pt-2 mt-1">
                <div className="text-sm font-bold py-1">Premium After Modifiers</div>
                <div></div>
                <div className="text-right text-sm">{fmtDollar(activeVersion?.premium_after_modifiers)}</div>
                <div className={`pr-dsi-pad text-right text-sm font-bold ${deltaColor(scenario.premium_after_modifiers, activeVersion?.premium_after_modifiers || 0)}`}>
                  {fmtDollar(scenario.premium_after_modifiers)}
                </div>
              </div>

              {/* ILF + DEDUCTIBLE + GUARDRAILS */}
              <div className="grid grid-cols-[50%_10%_20%_20%] px-dsi-pad border-t border-dsi-outline/10 pt-2 mt-1">
                <div className="text-xs py-1 pl-dsi-padicon">ILF Factor ({activeVersion?.ilf_method || 'N/A'})</div>
                <div className="text-center text-xs content-center">{formatNum(scenario.ilf_factor, 3)}x</div>
                <div className="text-right text-xs content-center">{formatNum(scenario.original_ilf_factor, 3)}x</div>
                <div className={`pr-dsi-pad text-right text-xs content-center font-bold ${Math.abs(scenario.ilf_factor - scenario.original_ilf_factor) > 0.001 ? 'text-dsi-selected' : ''}`}>
                  {formatNum(scenario.ilf_factor, 3)}x
                </div>
              </div>

              <div className="grid grid-cols-[50%_10%_20%_20%] px-dsi-pad">
                <div className="text-xs py-1 pl-dsi-padicon">Deductible Factor</div>
                <div className="text-center text-xs content-center">{formatNum(scenario.deductible_factor, 3)}x</div>
                <div className="text-right text-xs content-center">{formatNum(scenario.original_deductible_factor, 3)}x</div>
                <div className={`pr-dsi-pad text-right text-xs content-center font-bold ${Math.abs(scenario.deductible_factor - scenario.original_deductible_factor) > 0.001 ? 'text-dsi-selected' : ''}`}>
                  {formatNum(scenario.deductible_factor, 3)}x
                </div>
              </div>

              {/* Guardrails */}
              {scenario.guardrails.warnings.length > 0 && (
                <div className="mx-dsi-pad mt-2 p-2 border border-dsi-warning/20 bg-dsi-warning/5 rounded-lg">
                  <div className="flex items-center gap-2 mb-1">
                    <ShieldAlert className="w-3.5 h-3.5 text-dsi-warning" />
                    <span className="text-xs font-bold text-dsi-warning">Guardrails Active</span>
                  </div>
                  {scenario.guardrails.warnings.map((w, i) => (
                    <p key={i} className="text-xs opacity-70 text-wrap ml-5">{w}</p>
                  ))}
                </div>
              )}

              {/* FINAL PREMIUM */}
              <div className="grid grid-cols-[50%_10%_20%_20%] px-dsi-pad border-t-2 border-dsi-outline/30 pt-3 mt-3">
                <div className="text-lg font-black py-1">Final Premium</div>
                <div></div>
                <div className="text-right text-lg font-bold content-center">{fmtDollar(scenario.original_final_premium)}</div>
                <div className={`pr-dsi-pad text-right text-lg font-black content-center ${deltaColor(scenario.final_premium, scenario.original_final_premium)}`}>
                  {fmtDollar(scenario.final_premium)}
                </div>
              </div>

              {Math.abs(scenario.final_premium - scenario.original_final_premium) > 1 && (
                <div className="px-dsi-pad pt-1 text-right">
                  <span className={`text-sm font-bold ${deltaColor(scenario.final_premium, scenario.original_final_premium)}`}>
                    {scenario.final_premium > scenario.original_final_premium ? '+' : ''}{fmtDollar(scenario.final_premium - scenario.original_final_premium)}
                    {scenario.original_final_premium > 0 && (
                      <span className="ml-1">({scenario.final_premium > scenario.original_final_premium ? '+' : ''}{((scenario.final_premium - scenario.original_final_premium) / scenario.original_final_premium * 100).toFixed(1)}%)</span>
                    )}
                  </span>
                </div>
              )}

            </div>
          </div>
        </>
      )}
    </div>
  );
}

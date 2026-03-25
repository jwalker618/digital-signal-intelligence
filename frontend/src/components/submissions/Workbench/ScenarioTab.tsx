"use client";

import { useEffect, useState, useMemo, useCallback } from "react";
import { useDsiStore } from "@/store/dsiStore";
import {
  Paperclip, RotateCcw, Activity, ChevronUp, ChevronDown,
  AlertTriangle, ArrowDown, ShieldAlert, FlaskConical, Calculator
} from "lucide-react";
import { runFullCascade, ScenarioOverrides, ScenarioResult } from "@/lib/scenarioEngine";

// ─── Helpers ─────────────────────────────────────────────────────────────────

const fmt = (num: number | null | undefined, d = 1) =>
  num != null ? Number(num).toFixed(d) : "-";

const fmtDollar = (num: number | null | undefined) =>
  num != null ? `$${Number(num).toLocaleString(undefined, { maximumFractionDigits: 0 })}` : "-";

const deltaClass = (scenario: number, original: number) => {
  if (Math.abs(scenario - original) < 0.01) return '';
  return scenario > original ? 'text-rose-400' : 'text-emerald-400';
};

const deltaPrefix = (scenario: number, original: number) => {
  const diff = scenario - original;
  if (Math.abs(diff) < 0.01) return '';
  return diff > 0 ? '+' : '';
};

// ─── Component ───────────────────────────────────────────────────────────────

export default function ScenarioTab() {
  const {
    activeSubmission, activeVersion, activeQuote,
    riskSignals, isFetchingRiskSignals, fetchRiskSignals
  } = useDsiStore();

  // ── Override state ──
  const [signalOverrides, setSignalOverrides] = useState<Record<string, number>>({});
  const [lossModifierOverride, setLossModifierOverride] = useState<number | null>(null);
  const [exposureModifierOverride, setExposureModifierOverride] = useState<number | null>(null);
  const [limitOverride, setLimitOverride] = useState<number | null>(null);
  const [deductibleOverride, setDeductibleOverride] = useState<number | null>(null);

  useEffect(() => {
    if (activeVersion?.version_code) {
      fetchRiskSignals(activeVersion.version_code);
    }
  }, [activeVersion?.version_code, fetchRiskSignals]);

  // ── Signal stepper ──
  const handleStep = useCallback((sigCode: string, origScore: number, direction: 1 | -1) => {
    setSignalOverrides(prev => {
      const current = prev[sigCode] !== undefined ? prev[sigCode] : origScore;
      const next = Math.round((current + direction) * 10) / 10;
      if (Math.abs(next - origScore) < 0.05) {
        const { [sigCode]: _, ...rest } = prev;
        return rest;
      }
      return { ...prev, [sigCode]: Math.max(0, Math.min(100, next)) };
    });
  }, []);

  // ── Reset ──
  const resetAll = () => {
    setSignalOverrides({});
    setLossModifierOverride(null);
    setExposureModifierOverride(null);
    setLimitOverride(null);
    setDeductibleOverride(null);
  };

  const hasAnyOverride = Object.keys(signalOverrides).length > 0
    || lossModifierOverride !== null
    || exposureModifierOverride !== null
    || limitOverride !== null
    || deductibleOverride !== null;

  // ── Full cascade recalculation ──
  const scenario: ScenarioResult | null = useMemo(() => {
    if (!activeVersion || !riskSignals) return null;
    const overrides: ScenarioOverrides = {
      signalOverrides,
      lossModifierOverride,
      exposureModifierOverride,
      limitOverride,
      deductibleOverride,
    };
    return runFullCascade(riskSignals, activeVersion, overrides);
  }, [activeVersion, riskSignals, signalOverrides, lossModifierOverride, exposureModifierOverride, limitOverride, deductibleOverride]);

  // ── Sorted signals for table ──
  const sortedSignals = useMemo(() => {
    if (!riskSignals || riskSignals.length === 0) return [];
    return [...riskSignals].sort((a: any, b: any) => {
      if (a.group_code < b.group_code) return -1;
      if (a.group_code > b.group_code) return 1;
      return (b.contribution || 0) - (a.contribution || 0);
    });
  }, [riskSignals]);

  if (!activeSubmission || !activeVersion) return null;

  return (
    <div className="w-full no-scrollbar animate-in fade-in duration-500 pb-12">

      {/* ════════════════════════════════════════════════════════════════════
          STICKY HEADER
          ════════════════════════════════════════════════════════════════════ */}
      <div className="sticky top-0 z-20 bg-dsi-background pt-3 pb-2">
        <div className="flex gap-dsi-pad rounded-t-xl border-b-1 border-dsi-outline/50 overflow-x-hidden whitespace-nowrap border-collapse bg-dsi-analysis/60 pl-dsi-pad pt-2 pb-2">
          <Paperclip className="icon"/><span className="text-sm">Key Details</span>
        </div>
        <div className="grid grid-cols-[10%_35%_55%] grid-rows-1 border-b-3 border-dsi-contrast-background overflow-x-hidden whitespace-nowrap border-collapse rounded-b-xl bg-dsi-analysis shadow-sm pt-2 pb-2">
          <div className="text-left pl-dsi-pad pr-dsi-pad border-r-1 border-dsi-outline/50 overflow-x-hidden">
            <span className="text-sm">Status:</span><span className="pl-2 uppercase font-bold">{activeQuote.status}</span>
          </div>
          <div className="text-center pl-dsi-pad pr-dsi-pad border-r-1 border-dsi-outline/50 overflow-x-hidden">
            {(activeQuote.status === 'draft' || activeQuote.status === 'ready') && (
              <span>
                <span className="text-sm">Quote Valid From:</span><span className="pl-2 uppercase font-bold">{new Date(activeQuote.valid_from).toLocaleDateString()};</span>
                <span className="pl-2 pr-2"> </span>
                <span className="text-sm">Until:</span><span className="pl-2 uppercase font-bold">{new Date(activeQuote.valid_until).toLocaleDateString()}</span>
              </span>
            )}
            {activeQuote.status === 'bound' && (
              <span>
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

      {isFetchingRiskSignals || !scenario ? (
        <div className="flex flex-col items-center justify-center py-20 opacity-50 space-y-4">
          <Activity className="w-8 h-8 animate-spin" />
          <p className="text-sm tracking-widest uppercase">Loading Scenario Engine...</p>
        </div>
      ) : (
        <>
          {/* ════════════════════════════════════════════════════════════════
              COHORT C: SIGNAL OVERRIDE TABLE
              ════════════════════════════════════════════════════════════════ */}
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

            {/* Composite score comparison header */}
            <div className="grid grid-cols-2 gap-4 bg-dsi-analysis border-x border-dsi-outline/10 px-dsi-pad py-3">
              <div>
                <span className="opacity-50 block text-xs mb-1">Original Composite</span>
                <span className="font-bold text-xl">{fmt(scenario.original_composite, 1)}</span>
                <span className="text-xs opacity-40 ml-2">Tier {scenario.original_tier}</span>
              </div>
              <div>
                <span className="text-dsi-selected block text-xs mb-1 font-bold">Scenario Composite</span>
                <div className="flex items-baseline gap-2">
                  <span className="font-bold text-2xl text-dsi-selected">{fmt(scenario.composite_score, 1)}</span>
                  {Math.abs(scenario.composite_score - scenario.original_composite) > 0.1 && (
                    <span className={`text-xs font-bold ${deltaClass(scenario.composite_score, scenario.original_composite)}`}>
                      ({deltaPrefix(scenario.composite_score, scenario.original_composite)}{fmt(scenario.composite_score - scenario.original_composite, 1)})
                    </span>
                  )}
                  {scenario.tier && scenario.tier.tier_id !== scenario.original_tier && (
                    <span className={`text-xs font-bold ml-1 ${scenario.tier.tier_id > scenario.original_tier ? 'text-rose-400' : 'text-emerald-400'}`}>
                      → Tier {scenario.tier.tier_id}
                    </span>
                  )}
                </div>
              </div>
            </div>

            {/* Signal table */}
            <div className="flex flex-col flex-1 border-b-3 border-dsi-contrast-background overflow-x-auto whitespace-nowrap border-collapse rounded-b-xl bg-dsi-analysis shadow-sm pt-0 pb-4">
              <table className="w-full text-sm text-left whitespace-nowrap">
                <thead>
                  <tr className="text-center text-sm underline opacity-70">
                    <th className="py-2 pl-dsi-pad pr-dsi-pad font-normal text-left">Group</th>
                    <th className="py-2 px-2 font-normal text-right">Grp Wgt</th>
                    <th className="py-2 px-2 font-normal text-left">Signal Code</th>
                    <th className="py-2 px-2 font-normal text-right">Score</th>
                    <th className="py-2 px-2 font-normal text-right">Weight</th>
                    <th className="py-2 px-2 font-normal text-right">Contrib</th>
                    <th className="py-2 px-2 font-normal text-center text-dsi-selected border-l border-dsi-outline/20">Scenario</th>
                    <th className="py-2 pr-dsi-pad font-normal text-right text-dsi-selected">New Contrib</th>
                  </tr>
                </thead>
                <tbody>
                  {sortedSignals.map((sig: any, idx: number) => {
                    const isNewGroup = idx === 0 || sortedSignals[idx - 1].group_code !== sig.group_code;
                    const currentScore = signalOverrides[sig.code] !== undefined ? signalOverrides[sig.code] : (sig.score || 0);
                    const isOverridden = signalOverrides[sig.code] !== undefined;

                    // Recalc contribution for this signal
                    const groupStats: Record<string, number> = {};
                    sortedSignals.filter((s: any) => s.group_code === sig.group_code).forEach((s: any) => {
                      groupStats[s.group_code] = (groupStats[s.group_code] || 0) + (s.weight || 0);
                    });
                    const totalGW = groupStats[sig.group_code] || 1;
                    const scenarioContrib = ((currentScore * (sig.weight || 0)) / totalGW) * (sig.group_weight || 0) * 10;

                    return (
                      <tr key={`${sig.code}-${idx}`} className={`border-b border-dsi-outline/5 hover:bg-dsi-background/20 transition-colors ${isNewGroup && idx !== 0 ? 'border-t-1 border-t-dsi-outline/50' : ''}`}>
                        <td className="py-2 pl-dsi-pad pr-dsi-pad opacity-70 truncate max-w-[120px]">{isNewGroup ? sig.group_code : ''}</td>
                        <td className="py-2 px-2 text-right opacity-50">{isNewGroup ? fmt(sig.group_weight, 2) : ''}</td>
                        <td className="py-2 px-2 font-semibold">{sig.code}</td>
                        <td className="py-2 px-2 text-right">{fmt(sig.score, 1)}</td>
                        <td className="py-2 px-2 text-right opacity-50">{fmt(sig.weight, 2)}</td>
                        <td className="py-2 px-2 text-right">{fmt(sig.contribution, 2)}</td>
                        <td className="py-1 px-2 border-l border-dsi-outline/20">
                          <div className="flex items-center justify-center gap-0.5">
                            <button onClick={() => handleStep(sig.code, sig.score || 0, -1)} className="p-0.5 rounded hover:bg-dsi-outline/20 transition-colors text-dsi-selected/60 hover:text-dsi-selected">
                              <ChevronDown className="w-3.5 h-3.5" />
                            </button>
                            <input
                              type="number"
                              className={`w-16 bg-dsi-background border rounded px-1.5 py-1 text-center text-sm outline-none transition-all [appearance:textfield] [&::-webkit-outer-spin-button]:appearance-none [&::-webkit-inner-spin-button]:appearance-none ${isOverridden ? 'border-dsi-selected text-dsi-selected' : 'border-dsi-outline/20 focus:border-dsi-selected/50'}`}
                              value={isOverridden ? currentScore : ''}
                              placeholder={fmt(sig.score, 1)}
                              onChange={(e) => {
                                const val = e.target.value;
                                setSignalOverrides(prev => {
                                  const next = { ...prev };
                                  if (val === "") { delete next[sig.code]; }
                                  else { next[sig.code] = parseFloat(val); }
                                  return next;
                                });
                              }}
                            />
                            <button onClick={() => handleStep(sig.code, sig.score || 0, 1)} className="p-0.5 rounded hover:bg-dsi-outline/20 transition-colors text-dsi-selected/60 hover:text-dsi-selected">
                              <ChevronUp className="w-3.5 h-3.5" />
                            </button>
                          </div>
                        </td>
                        <td className={`py-2 pr-dsi-pad text-right font-bold ${isOverridden ? 'text-dsi-selected' : ''}`}>
                          {fmt(scenarioContrib, 2)}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>

          {/* ════════════════════════════════════════════════════════════════
              COHORT E: DIRECT OVERRIDE CONTROLS
              ════════════════════════════════════════════════════════════════ */}
          <div className="flex flex-col pt-2 pb-2">
            <div className="flex gap-dsi-pad rounded-t-xl border-b-1 border-dsi-outline/50 overflow-x-hidden whitespace-nowrap border-collapse bg-dsi-analysis/60 pl-dsi-pad pt-2 pb-2">
              <Calculator className="icon"/><span className="text-sm">Direct Overrides</span>
            </div>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 border-b-3 border-dsi-contrast-background rounded-b-xl bg-dsi-analysis shadow-sm px-dsi-pad py-4">

              {/* Loss modifier */}
              <div className="border border-dsi-outline/20 rounded-lg p-3">
                <span className="text-xs opacity-60 block mb-1">Loss Modifier</span>
                <div className="flex items-center gap-1">
                  <input
                    type="number" step="0.01"
                    className={`w-20 bg-dsi-background border rounded px-2 py-1 text-sm outline-none [appearance:textfield] [&::-webkit-outer-spin-button]:appearance-none [&::-webkit-inner-spin-button]:appearance-none ${lossModifierOverride !== null ? 'border-dsi-selected text-dsi-selected' : 'border-dsi-outline/20'}`}
                    value={lossModifierOverride ?? ''}
                    placeholder={fmt(activeVersion.loss_combined_modifier, 3)}
                    onChange={(e) => setLossModifierOverride(e.target.value === '' ? null : parseFloat(e.target.value))}
                  />
                  <span className="text-xs opacity-40">x</span>
                </div>
                <span className="text-[10px] opacity-30 block mt-1">Original: {fmt(activeVersion.loss_combined_modifier, 3)}x</span>
              </div>

              {/* Exposure modifier */}
              <div className="border border-dsi-outline/20 rounded-lg p-3">
                <span className="text-xs opacity-60 block mb-1">Exposure Modifier</span>
                <div className="flex items-center gap-1">
                  <input
                    type="number" step="0.01"
                    className={`w-20 bg-dsi-background border rounded px-2 py-1 text-sm outline-none [appearance:textfield] [&::-webkit-outer-spin-button]:appearance-none [&::-webkit-inner-spin-button]:appearance-none ${exposureModifierOverride !== null ? 'border-dsi-selected text-dsi-selected' : 'border-dsi-outline/20'}`}
                    value={exposureModifierOverride ?? ''}
                    placeholder={fmt(activeVersion.exposure_modifier, 3)}
                    onChange={(e) => setExposureModifierOverride(e.target.value === '' ? null : parseFloat(e.target.value))}
                  />
                  <span className="text-xs opacity-40">x</span>
                </div>
                <span className="text-[10px] opacity-30 block mt-1">Original: {fmt(activeVersion.exposure_modifier, 3)}x</span>
              </div>

              {/* Limit */}
              <div className="border border-dsi-outline/20 rounded-lg p-3">
                <span className="text-xs opacity-60 block mb-1">Policy Limit</span>
                <div className="flex items-center gap-1">
                  <span className="text-xs opacity-40">$</span>
                  <input
                    type="number" step="1000000"
                    className={`w-28 bg-dsi-background border rounded px-2 py-1 text-sm outline-none [appearance:textfield] [&::-webkit-outer-spin-button]:appearance-none [&::-webkit-inner-spin-button]:appearance-none ${limitOverride !== null ? 'border-dsi-selected text-dsi-selected' : 'border-dsi-outline/20'}`}
                    value={limitOverride ?? ''}
                    placeholder={String(activeVersion.final_premium_detail?.limit || activeVersion.ilf_anchor_limit || '')}
                    onChange={(e) => setLimitOverride(e.target.value === '' ? null : parseFloat(e.target.value))}
                  />
                </div>
                <span className="text-[10px] opacity-30 block mt-1">ILF: {fmt(activeVersion.ilf_factor, 3)}x @ anchor {fmtDollar(activeVersion.ilf_anchor_limit)}</span>
              </div>

              {/* Deductible */}
              <div className="border border-dsi-outline/20 rounded-lg p-3">
                <span className="text-xs opacity-60 block mb-1">Deductible</span>
                <div className="flex items-center gap-1">
                  <span className="text-xs opacity-40">$</span>
                  <input
                    type="number" step="25000"
                    className={`w-28 bg-dsi-background border rounded px-2 py-1 text-sm outline-none [appearance:textfield] [&::-webkit-outer-spin-button]:appearance-none [&::-webkit-inner-spin-button]:appearance-none ${deductibleOverride !== null ? 'border-dsi-selected text-dsi-selected' : 'border-dsi-outline/20'}`}
                    value={deductibleOverride ?? ''}
                    placeholder={String(activeVersion.final_premium_detail?.deductible || '')}
                    onChange={(e) => setDeductibleOverride(e.target.value === '' ? null : parseFloat(e.target.value))}
                  />
                </div>
                <span className="text-[10px] opacity-30 block mt-1">Factor: {fmt(activeVersion.final_premium_detail?.deductible_factor, 3)}x</span>
              </div>

            </div>
          </div>

          {/* ════════════════════════════════════════════════════════════════
              COHORT D: CASCADE WATERFALL
              ════════════════════════════════════════════════════════════════ */}
          <div className="flex flex-col pt-2 pb-2">
            <div className="flex gap-dsi-pad rounded-t-xl border-b-1 border-dsi-outline/50 overflow-x-hidden whitespace-nowrap border-collapse bg-dsi-analysis/60 pl-dsi-pad pt-2 pb-2">
              <ArrowDown className="icon"/><span className="text-sm">Pricing Cascade</span>
            </div>
            <div className="flex flex-col flex-1 border-b-3 border-dsi-contrast-background rounded-b-xl bg-dsi-analysis shadow-sm pt-4 pb-4">

              {/* Header row */}
              <div className="grid grid-cols-[1fr_140px_30px_140px] gap-2 px-dsi-pad pb-2 mb-2 border-b border-dsi-outline/20 text-xs uppercase tracking-wider opacity-50">
                <span>Stage</span>
                <span className="text-right">Original</span>
                <span></span>
                <span className="text-right font-bold text-dsi-selected opacity-100">Scenario</span>
              </div>

              {/* D1: Tier */}
              <CascadeRow
                label="Tier Assignment"
                sublabel={scenario.tier ? `${scenario.tier.action} — ${scenario.tier.label}` : ''}
                original={`Tier ${scenario.original_tier}`}
                scenarioVal={scenario.tier ? `Tier ${scenario.tier.tier_id}` : `Tier ${scenario.original_tier}`}
                changed={scenario.tier !== null && scenario.tier.tier_id !== scenario.original_tier}
              />

              {/* D2: Base Premium */}
              <CascadeRow
                label="Base Premium"
                sublabel={activeVersion.base_premium_method || ''}
                original={fmtDollar(scenario.original_base_premium)}
                scenarioVal={fmtDollar(scenario.base_premium)}
                changed={Math.abs(scenario.base_premium - scenario.original_base_premium) > 1}
              />

              {/* D3: Modifier Waterfall */}
              {scenario.waterfall.map((step, idx) => (
                <CascadeRow
                  key={idx}
                  label={step.name}
                  sublabel={step.source}
                  original={`${step.original_factor.toFixed(3)}x`}
                  scenarioVal={`${step.scenario_factor.toFixed(3)}x`}
                  changed={Math.abs(step.scenario_factor - step.original_factor) > 0.001}
                  indent
                />
              ))}

              {/* Premium after modifiers subtotal */}
              <div className="grid grid-cols-[1fr_140px_30px_140px] gap-2 px-dsi-pad py-2 border-t border-dsi-outline/20 bg-dsi-background/20">
                <span className="text-sm font-bold">Premium After Modifiers</span>
                <span className="text-right text-sm font-bold">{fmtDollar(activeVersion.premium_after_modifiers)}</span>
                <span className="text-center opacity-30">→</span>
                <span className={`text-right text-sm font-bold ${deltaClass(scenario.premium_after_modifiers, activeVersion.premium_after_modifiers || 0)}`}>
                  {fmtDollar(scenario.premium_after_modifiers)}
                </span>
              </div>

              {/* D4: ILF */}
              <CascadeRow
                label="ILF Factor"
                sublabel={activeVersion.ilf_method || ''}
                original={`${fmt(scenario.original_ilf_factor, 3)}x`}
                scenarioVal={`${fmt(scenario.ilf_factor, 3)}x`}
                changed={Math.abs(scenario.ilf_factor - scenario.original_ilf_factor) > 0.001}
              />

              {/* D5: Deductible */}
              <CascadeRow
                label="Deductible Factor"
                sublabel=""
                original={`${fmt(scenario.original_deductible_factor, 3)}x`}
                scenarioVal={`${fmt(scenario.deductible_factor, 3)}x`}
                changed={Math.abs(scenario.deductible_factor - scenario.original_deductible_factor) > 0.001}
              />

              {/* D6: Guardrails */}
              {scenario.guardrails.warnings.length > 0 && (
                <div className="px-dsi-pad py-2 border-t border-amber-500/20 bg-amber-500/5">
                  <div className="flex items-center gap-2 mb-1">
                    <ShieldAlert className="w-3.5 h-3.5 text-amber-400" />
                    <span className="text-xs font-bold text-amber-400">Guardrails Active</span>
                  </div>
                  {scenario.guardrails.warnings.map((w, i) => (
                    <p key={i} className="text-xs opacity-70 text-wrap ml-5">{w}</p>
                  ))}
                </div>
              )}

              {/* D7: Final Premium */}
              <div className="grid grid-cols-[1fr_140px_30px_140px] gap-2 px-dsi-pad py-4 border-t-2 border-dsi-outline/30 bg-dsi-background/30">
                <span className="text-lg font-black">Final Premium</span>
                <span className="text-right text-lg font-bold">{fmtDollar(scenario.original_final_premium)}</span>
                <span className="text-center opacity-30 text-lg">→</span>
                <span className={`text-right text-lg font-black ${deltaClass(scenario.final_premium, scenario.original_final_premium)}`}>
                  {fmtDollar(scenario.final_premium)}
                </span>
              </div>

              {/* Delta summary */}
              {Math.abs(scenario.final_premium - scenario.original_final_premium) > 1 && (
                <div className="px-dsi-pad pt-2 text-right">
                  <span className={`text-sm font-bold ${deltaClass(scenario.final_premium, scenario.original_final_premium)}`}>
                    {deltaPrefix(scenario.final_premium, scenario.original_final_premium)}
                    {fmtDollar(scenario.final_premium - scenario.original_final_premium)}
                    {' '}({deltaPrefix(scenario.final_premium, scenario.original_final_premium)}
                    {scenario.original_final_premium > 0 ? ((scenario.final_premium - scenario.original_final_premium) / scenario.original_final_premium * 100).toFixed(1) : '0'}%)
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

// ─── Cascade Row Sub-component ───────────────────────────────────────────────

function CascadeRow({ label, sublabel, original, scenarioVal, changed, indent }: {
  label: string; sublabel: string; original: string; scenarioVal: string; changed: boolean; indent?: boolean;
}) {
  return (
    <div className={`grid grid-cols-[1fr_140px_30px_140px] gap-2 px-dsi-pad py-2 border-b border-dsi-outline/5 hover:bg-dsi-background/10 transition-colors ${changed ? 'bg-dsi-selected/5' : ''}`}>
      <div className={indent ? 'pl-4' : ''}>
        <span className="text-sm">{label}</span>
        {sublabel && <span className="text-[10px] opacity-30 block">{sublabel}</span>}
      </div>
      <span className="text-right text-sm opacity-70">{original}</span>
      <span className="text-center opacity-30">→</span>
      <span className={`text-right text-sm font-bold ${changed ? 'text-dsi-selected' : ''}`}>{scenarioVal}</span>
    </div>
  );
}

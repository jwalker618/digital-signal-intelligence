"use client";

import { useEffect, useState, useMemo } from "react";
import { useDsiStore } from "@/store/dsiStore";
import { Target, Activity, Calculator, RotateCcw } from "lucide-react";

export default function RiskTab() {
  const { activeSubmission, activeVersion, riskSignals, isFetchingRiskSignals, fetchRiskSignals } = useDsiStore();
  
  // State to hold user's "sandbox" overrides: { "signal_code": newScore }
  const [scenarioOverrides, setScenarioOverrides] = useState<Record<string, number>>({});

  useEffect(() => {
    if (activeVersion?.version_code) {
      fetchRiskSignals(activeVersion.version_code);
    }
  }, [activeVersion?.version_code, fetchRiskSignals]);

  // =======================================================================
  // SCENARIO MATH ENGINE (Recalculates instantly on keystroke)
  // =======================================================================
  const { enrichedSignals, scenarioCompositeScore } = useMemo(() => {
    if (!riskSignals || riskSignals.length === 0) return { enrichedSignals: [], scenarioCompositeScore: 0 };

    // 1. Calculate the total signal weight per group 
    // Needed for: group_score = Σ(signal.score × signal.weight) / Σ(signal.weight)
    const groupStats: Record<string, { totalWeight: number, groupWeight: number }> = {};
    riskSignals.forEach((sig: any) => {
      const group = sig.group_code || 'ungrouped';
      if (!groupStats[group]) {
        groupStats[group] = { totalWeight: 0, groupWeight: sig.group_weight || 0 };
      }
      groupStats[group].totalWeight += (sig.weight || 0);
    });

    // 2. Map signals, apply scenario scores, and calculate individual contributions
    let newComposite = 0;
    const groupScores: Record<string, number> = {};

    const processedSignals = riskSignals.map((sig: any) => {
      const group = sig.group_code || 'ungrouped';
      // Use user override if it exists, otherwise use original score
      const activeScore = scenarioOverrides[sig.code] !== undefined ? scenarioOverrides[sig.code] : (sig.score || 0);
      
      const weight = sig.weight || 0;
      const groupWeight = sig.group_weight || 0;
      const totalGroupWeight = groupStats[group].totalWeight || 1;

      // Calculate Scenario Contribution
      const scenarioContribution = ((activeScore * weight) / totalGroupWeight) * groupWeight * 10;

      // Accumulate the weighted score for the Group Score calculation
      if (!groupScores[group]) groupScores[group] = 0;
      groupScores[group] += (activeScore * weight) / totalGroupWeight;

      return {
        ...sig,
        scenario_score: activeScore,
        scenario_contribution: scenarioContribution,
        is_overridden: scenarioOverrides[sig.code] !== undefined
      };
    });

    // 3. Finalize the Scenario Composite Score
    // pure_composite_score = Σ(group_score × group.risk.weight × 10)
    Object.keys(groupScores).forEach(group => {
      newComposite += (groupScores[group] * groupStats[group].groupWeight * 10);
    });

    // 4. Sort: By Group Code, then by Highest Original Contribution
    processedSignals.sort((a, b) => {
      if (a.group_code < b.group_code) return -1;
      if (a.group_code > b.group_code) return 1;
      return (b.contribution || 0) - (a.contribution || 0);
    });

    return { 
      enrichedSignals: processedSignals, 
      scenarioCompositeScore: newComposite 
    };
  }, [riskSignals, scenarioOverrides]);

  if (!activeSubmission || !activeVersion) return null;

  // Formatting helper
  const formatNum = (num: number | null | undefined, decimals = 1) => 
    num !== null && num !== undefined ? Number(num).toFixed(decimals) : "-";

  const scoreDiff = scenarioCompositeScore - (activeVersion.pure_composite_score || 0);

  return (
    <div className="w-full max-w-[1400px] mx-auto space-y-6 animate-in fade-in duration-500 pb-12 pt-4">
      
      {/* =======================================================================
          SUMMARY KPIs
          ======================================================================= */}
      <div className="border border-dsi-outline/20 rounded-xl p-5 bg-dsi-analysis shadow-sm">
        <div className="flex justify-between items-center mb-4 border-b border-dsi-outline/10 pb-2">
          <h3 className="text-sm font-bold tracking-wide flex items-center gap-2">
            <Target className="w-4 h-4 text-dsi-selected" /> Risk Assessment Summary
          </h3>
          {Object.keys(scenarioOverrides).length > 0 && (
            <button 
              onClick={() => setScenarioOverrides({})}
              className="flex items-center gap-2 text-xs font-mono bg-dsi-outline/10 hover:bg-dsi-outline/20 px-3 py-1.5 rounded transition-colors text-dsi-selected"
            >
              <RotateCcw className="w-3 h-3" /> Reset Scenarios
            </button>
          )}
        </div>

        <div className="grid grid-cols-2 md:grid-cols-5 gap-6">
          <div>
            <span className="opacity-50 block text-xs mb-1">Score-Based Tier</span>
            <span className="font-mono font-bold text-lg text-dsi-selected">
              Tier {activeVersion.score_based_tier || activeVersion.final_tier}
            </span>
          </div>
          <div>
            <span className="opacity-50 block text-xs mb-1">Confidence</span>
            <span className="font-mono font-bold text-lg">
              {((activeVersion.confidence || 0) * 100).toFixed(0)}%
            </span>
          </div>
          <div>
            <span className="opacity-50 block text-xs mb-1">Signal Coverage</span>
            <span className="font-mono font-bold text-lg">
              {((activeVersion.signal_coverage || 0) * 100).toFixed(0)}%
            </span>
          </div>
          <div className="border-l border-dsi-outline/20 pl-6">
            <span className="opacity-50 block text-xs mb-1">Original Composite</span>
            <span className="font-mono font-bold text-xl">
              {formatNum(activeVersion.pure_composite_score, 1)}
            </span>
          </div>
          <div className="bg-dsi-selected/10 -m-2 p-2 rounded border border-dsi-selected/30">
            <span className="text-dsi-selected block text-xs mb-1 font-bold">Scenario Composite</span>
            <div className="flex items-baseline gap-2">
              <span className="font-mono font-bold text-2xl text-dsi-selected">
                {formatNum(scenarioCompositeScore, 1)}
              </span>
              {Math.abs(scoreDiff) > 0.1 && (
                <span className={`text-xs font-bold ${scoreDiff > 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
                  ({scoreDiff > 0 ? '+' : ''}{formatNum(scoreDiff, 1)})
                </span>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* =======================================================================
          SIGNAL TABLE WITH SCENARIO INPUTS
          ======================================================================= */}
      <div className="border border-dsi-outline/20 rounded-xl p-5 bg-dsi-analysis shadow-sm">
        <h3 className="text-sm font-bold tracking-wide flex items-center gap-2 mb-6">
          <Calculator className="w-4 h-4 text-dsi-selected" /> Signal Breakdown & Scenario Sandbox
        </h3>

        {isFetchingRiskSignals ? (
          <div className="flex flex-col items-center justify-center py-10 opacity-50 space-y-4">
            <Activity className="w-6 h-6 animate-spin" />
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm font-mono text-left whitespace-nowrap">
              <thead>
                <tr className="border-b border-dsi-outline/20 text-[10px] uppercase tracking-wider opacity-50 bg-dsi-background/30">
                  <th className="py-3 px-2">Group</th>
                  <th className="py-3 px-2 text-right">Grp Wgt</th>
                  <th className="py-3 px-2">Signal Code</th>
                  <th className="py-3 px-2">Proxy Tier</th>
                  <th className="py-3 px-2 text-center">Absent?</th>
                  <th className="py-3 px-2 text-right">Orig Score</th>
                  <th className="py-3 px-2 text-right">Sig Wgt</th>
                  <th className="py-3 px-2 text-right">Orig Contrib</th>
                  <th className="py-3 px-2 text-center text-dsi-selected border-l border-dsi-outline/20">Scenario Score</th>
                  <th className="py-3 px-2 text-right text-dsi-selected">New Contrib</th>
                </tr>
              </thead>
              <tbody>
                {enrichedSignals.map((sig: any, idx: number) => {
                  // Check if this row is the start of a new group for visual separation
                  const isNewGroup = idx === 0 || enrichedSignals[idx - 1].group_code !== sig.group_code;
                  
                  return (
                    <tr 
                      key={`${sig.code}-${idx}`} 
                      className={`
                        border-b border-dsi-outline/5 hover:bg-dsi-outline/5 transition-colors
                        ${isNewGroup ? 'border-t-2 border-t-dsi-outline/20' : ''}
                        ${sig.is_overridden ? 'bg-dsi-selected/5' : ''}
                      `}
                    >
                      <td className="py-2 px-2 opacity-70 truncate max-w-[120px]" title={sig.group_code}>
                        {isNewGroup ? sig.group_code : ''}
                      </td>
                      <td className="py-2 px-2 text-right opacity-50">
                        {isNewGroup ? formatNum(sig.group_weight, 2) : ''}
                      </td>
                      <td className="py-2 px-2 font-semibold">
                        {sig.code}
                      </td>
                      <td className="py-2 px-2 opacity-80">
                        {sig.proxy_tier || "-"}
                      </td>
                      <td className="py-2 px-2 text-center">
                        {sig.was_absent ? <span className="text-rose-400">Yes</span> : <span className="text-emerald-400 opacity-50">No</span>}
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
                      
                      {/* Scenario Inputs */}
                      <td className="py-1 px-2 border-l border-dsi-outline/20 flex justify-center">
                        <input 
                          type="number"
                          className={`
                            w-20 bg-dsi-background border rounded px-2 py-1 text-right outline-none transition-all
                            ${sig.is_overridden ? 'border-dsi-selected text-dsi-selected' : 'border-dsi-outline/20 focus:border-dsi-selected/50'}
                          `}
                          placeholder={formatNum(sig.score, 1)}
                          value={scenarioOverrides[sig.code] !== undefined ? scenarioOverrides[sig.code] : ""}
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
                      </td>
                      <td className={`py-2 px-2 text-right font-bold ${sig.is_overridden ? 'text-dsi-selected' : ''}`}>
                        {formatNum(sig.scenario_contribution, 2)}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

    </div>
  );
}
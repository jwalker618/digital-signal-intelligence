"use client";

import { useEffect, useState, useMemo } from "react";
import { useDsiStore } from "@/store/dsiStore";
import { Target, Activity, Calculator, RotateCcw, Paperclip } from "lucide-react";

export default function RiskTab() {
  const { activeSubmission, activeVersion, activeQuote, riskSignals, isFetchingRiskSignals, fetchRiskSignals } = useDsiStore();
  
  const [scenarioOverrides, setScenarioOverrides] = useState<Record<string, number>>({});

  useEffect(() => {
    if (activeVersion?.version_code) {
      fetchRiskSignals(activeVersion.version_code);
    }
  }, [activeVersion?.version_code, fetchRiskSignals]);

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

  const formatNum = (num: number | null | undefined, decimals = 1) => 
    num !== null && num !== undefined ? Number(num).toFixed(decimals) : "-";

  const scoreDiff = scenarioCompositeScore - (activeVersion.pure_composite_score || 0);

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
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* =======================================================================
          SIGNAL TABLE WITH SCENARIO INPUTS
          ======================================================================= */}
      <div className="flex flex-col pt-2 pb-2">
        <div className="
          flex gap-dsi-pad
          rounded-t-xl
          border-b-1 border-dsi-outline/50
          overflow-x-hidden whitespace-nowrap border-collapse
          bg-dsi-analysis/60
          pl-dsi-pad
          pt-2 pb-2    
        ">
          <Calculator className="icon"/><span className="text-sm">Signal Breakdown & Scenario Sandbox</span>
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
                  {enrichedSignals.map((sig: any, idx: number) => {
                    const isNewGroup = idx === 0 || enrichedSignals[idx - 1].group_code !== sig.group_code;
                    
                    return (
                      <tr 
                        key={`${sig.code}-${idx}`} 
                        className={`
                          border-b border-dsi-outline/5 hover:bg-dsi-background/20 transition-colors
                          ${isNewGroup && idx !== 0 ? 'border-t-1 border-t-dsi-outline/50' : ''}
                        `}
                      >
                        <td className="py-2 pl-dsi-pad pr-dsi-pad opacity-70 truncate max-w-[120px]" title={sig.group_code}>
                          {isNewGroup ? sig.group_code : ''}
                        </td>
                        <td className="py-2 px-2 text-right opacity-50">
                          {isNewGroup ? formatNum(sig.group_weight, 2) : ''}
                        </td>
                        <td className="py-2 px-2 font-semibold">
                          {sig.code}
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
                        <td className={`py-2 pr-dsi-pad text-right font-bold ${sig.is_overridden ? 'text-dsi-selected' : ''}`}>
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

    </div>
  );
}
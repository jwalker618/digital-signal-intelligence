"use client";

import { useDsiStore } from "@/store/dsiStore";
import { Activity, Shield, Calculator, BarChart3, TrendingUp, AlertTriangle } from "lucide-react";

export default function SummaryTab() {
  const { activeSubmission, activeQuote, activeVersion, activeReferral } = useDsiStore();

  if (!activeSubmission) return null;

  if (!activeVersion) {
    return (
      <div className="flex items-center justify-center h-full text-dsi-selected/50 animate-pulse">
        Loading version details...
      </div>
    );
  }

  return (
    <div className="w-full max-w-6xl mx-auto space-y-6 animate-in fade-in duration-500 pb-12 pt-4">
      
      {/* SECTION 1: TRUST & MODEL CONTEXT */}
      <div className="grid grid-cols-3 gap-4">
        <div className="col-span-1 border border-dsi-outline/20 rounded-xl p-4 bg-dsi-background/30 flex items-center justify-between">
          <div>
            <div className="text-xs font-semibold uppercase tracking-wider opacity-50 mb-1">Model Confidence</div>
            <div className="text-2xl font-mono font-bold text-dsi-selected">
              {((activeVersion.confidence || 0) * 100).toFixed(0)}%
            </div>
          </div>
          <Shield className={`w-8 h-8 ${activeVersion.confidence > 0.8 ? 'text-green-500' : 'text-yellow-500'} opacity-80`} />
        </div>
        
        <div className="col-span-1 border border-dsi-outline/20 rounded-xl p-4 bg-dsi-background/30 flex items-center justify-between">
          <div>
            <div className="text-xs font-semibold uppercase tracking-wider opacity-50 mb-1">Signal Coverage</div>
            <div className="text-2xl font-mono font-bold text-dsi-selected">
              {((activeVersion.signal_coverage || 0) * 100).toFixed(0)}%
            </div>
          </div>
          <Activity className="w-8 h-8 text-dsi-selected opacity-80" />
        </div>

        <div className="col-span-1 border border-dsi-outline/20 rounded-xl p-4 bg-dsi-background/30 flex items-center justify-between">
          <div>
            <div className="text-xs font-semibold uppercase tracking-wider opacity-50 mb-1">Composite Score</div>
            <div className="text-2xl font-mono font-bold text-dsi-selected">
              {activeVersion.pure_composite_score || "N/A"}
            </div>
          </div>
          <div className="text-right">
            <span className="bg-dsi-selected/10 text-dsi-selected px-2 py-1 rounded text-xs font-bold font-mono">
              Tier {activeVersion.final_tier}
            </span>
          </div>
        </div>
      </div>

      {/* SECTION 2: 3-PILLAR BREAKDOWN (Loss, Exposure, Signals) */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        
        {/* Loss & Exposure */}
        <div className="space-y-6">
          <div className="border border-dsi-outline/20 rounded-xl p-5 bg-dsi-background/30">
            <h3 className="text-sm font-bold tracking-wide flex items-center gap-2 mb-4 border-b border-dsi-outline/10 pb-2">
              <TrendingUp className="w-4 h-4 text-dsi-selected" /> Loss Propensity
            </h3>
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <span className="opacity-50 block text-xs">Cohort ID</span>
                <span className="font-mono font-semibold">{activeVersion.loss_cohort_name || "Unknown"}</span>
              </div>
              <div>
                <span className="opacity-50 block text-xs">Propensity Band</span>
                <span className="font-mono font-semibold text-dsi-selected">{activeVersion.loss_propensity_band || "N/A"}</span>
              </div>
              <div>
                <span className="opacity-50 block text-xs">Cohort Confidence</span>
                <span className="font-mono font-semibold">
                  {((activeVersion.loss_confidence || 0) * 100).toFixed(0)}%
                </span>
              </div>
              <div>
                <span className="opacity-50 block text-xs">Score Velocity</span>
                <span className={`font-mono font-bold ${activeVersion.loss_score_velocity > 0 ? 'text-red-400' : 'text-green-400'}`}>
                  {activeVersion.loss_score_velocity > 0 ? '+' : ''}{activeVersion.loss_score_velocity || 0}
                </span>
              </div>
            </div>
          </div>

          <div className="border border-dsi-outline/20 rounded-xl p-5 bg-dsi-background/30">
            <h3 className="text-sm font-bold tracking-wide flex items-center gap-2 mb-4 border-b border-dsi-outline/10 pb-2">
              <BarChart3 className="w-4 h-4 text-dsi-selected" /> Exposure Assessment
            </h3>
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <span className="opacity-50 block text-xs">Exposure Value (TIV/Rev)</span>
                <span className="font-mono font-semibold">${(activeVersion.exposure_value || 0).toLocaleString()}</span>
              </div>
              <div>
                <span className="opacity-50 block text-xs">Band Label</span>
                <span className="font-mono font-semibold text-dsi-selected">{activeVersion.exposure_band_label || "N/A"}</span>
              </div>
              <div className="col-span-2">
                <span className="opacity-50 block text-xs">Calculated Modifier</span>
                <span className="font-mono font-semibold">{activeVersion.exposure_modifier?.toFixed(3) || "1.000"}x</span>
              </div>
            </div>
          </div>
        </div>

        {/* Group Scores (Signal Summaries) */}
        <div className="border border-dsi-outline/20 rounded-xl p-5 bg-dsi-background/30 h-full flex flex-col">
          <h3 className="text-sm font-bold tracking-wide flex items-center gap-2 mb-4 border-b border-dsi-outline/10 pb-2">
            <Activity className="w-4 h-4 text-dsi-selected" /> Signal Group Breakdown
          </h3>
          
          <div className="flex-1 space-y-4">
            {Object.entries(activeVersion.group_scores || {}).length === 0 ? (
              <div className="text-xs opacity-50 italic">No group score data available.</div>
            ) : (
              Object.entries(activeVersion.group_scores).map(([group, groupData]: any) => {
                
                // Extract the specific score to display (falling back to 0 if missing)
                const displayScore = groupData?.risk_score || groupData?.loss_score || 0;

                return (
                  <div key={group}>
                    <div className="flex justify-between text-xs font-semibold mb-1">
                      <span className="uppercase tracking-wider">{group.replace(/_/g, ' ')}</span>
                      <span className="font-mono">{displayScore.toFixed(1)}</span>
                    </div>
                    <div className="w-full bg-dsi-outline/10 rounded-full h-1.5 overflow-hidden">
                      <div 
                        className="bg-dsi-selected h-1.5 rounded-full" 
                        // Since the data is out of 100 (e.g. 92.0), we can just use the score directly as the width percentage
                        style={{ width: `${Math.min(100, displayScore)}%` }}
                      ></div>
                    </div>
                  </div>
                );
              })
            )}
          </div>

        </div>
      </div>

      {/* SECTION 3: PRICING ANATOMY */}
      <div className="border border-dsi-outline/20 rounded-xl p-5 bg-dsi-background/30">
        <h3 className="text-sm font-bold tracking-wide flex items-center gap-2 mb-4 border-b border-dsi-outline/10 pb-2">
          <Calculator className="w-4 h-4 text-dsi-selected" /> Pricing Anatomy
        </h3>
        
        <div className="flex flex-col md:flex-row gap-8">

          {/* Modifiers Table */}
          <div className="flex-1">
            <h4 className="text-xs uppercase tracking-wider opacity-50 mb-2">Applied Modifiers</h4>
            {activeVersion.modifiers_applied?.length > 0 ? (
              <table className="w-full text-sm font-mono text-left">
                <tbody>
                  {activeVersion.modifiers_applied.map((mod: any, idx: number) => (
                    <tr key={idx} className="border-b border-dsi-outline/5">
                      {/* FIX: Use mod.note, fallback to mod.source */}
                      <td className="py-2 opacity-80">{mod.note || mod.source}</td>
                      <td className="py-2 text-right">
                        {/* FIX: Use mod.applied */}
                        {Number(mod.applied ?? 1.0).toFixed(3)}x
                      </td>
                    </tr>
                  ))}
                  <tr className="bg-dsi-selected/5 font-bold">
                    <td className="py-2 px-2">Base Premium</td>
                    <td className="py-2 px-2 text-right">${activeVersion.base_premium?.toLocaleString()}</td>
                  </tr>
                  <tr className="bg-dsi-selected/10 font-bold text-dsi-selected">
                    <td className="py-2 px-2">Final Premium</td>
                    <td className="py-2 px-2 text-right">${activeVersion.premium_after_modifiers?.toLocaleString()}</td>
                  </tr>
                </tbody>
              </table>
            ) : (
              <div className="text-xs opacity-50 italic">No modifiers applied.</div>
            )}
          </div>

          {/* Premium Options */}
          <div className="flex-1 border-t md:border-t-0 md:border-l border-dsi-outline/10 pt-4 md:pt-0 md:pl-8">
            <h4 className="text-xs uppercase tracking-wider opacity-50 mb-2">Limit Options</h4>
            {Object.keys(activeVersion.limit_premiums || {}).length > 0 ? (
              <div className="space-y-2 font-mono text-sm">
                {Object.entries(activeVersion.limit_premiums).map(([limit, premium]: any) => (
                  <div key={limit} className="flex justify-between p-2 rounded hover:bg-dsi-selected/5">
                    <span>${parseInt(limit).toLocaleString()} Limit</span>
                    <span className="font-bold text-dsi-selected">${premium.toLocaleString()}</span>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-xs opacity-50 italic">No alternative limit options generated.</div>
            )}
          </div>
        </div>
      </div>

    </div>
  );
}
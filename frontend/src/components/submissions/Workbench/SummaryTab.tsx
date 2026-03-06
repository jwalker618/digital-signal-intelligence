"use client";

import { useState } from "react";
import { useDsiStore } from "@/store/dsiStore";
import { 
  DollarSign, Target, Activity, ShieldCheck, ShieldAlert, 
  Globe, Users, Building, TrendingUp, AlertTriangle, BarChart, Scale, Network,
  Calculator, X, CheckCircle2, XCircle, MinusCircle, Info
} from "lucide-react";

export default function SummaryTab() {
  const { activeSubmission } = useDsiStore();
  const [showPremiumCalc, setShowPremiumCalc] = useState(false);

  if (!activeSubmission) return null;

  // Helpers for formatting
  const formatCurrency = (val?: number) => {
    if (val === undefined || val === null) return "N/A";
    return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 }).format(val);
  };

  const formatNumber = (val?: number) => {
    if (val === undefined || val === null) return "N/A";
    return new Intl.NumberFormat('en-US').format(val);
  };

  // Determine decision styling
  const isApproved = activeSubmission.decision === "approve";
  const isReferred = activeSubmission.decision === "refer";
  const decisionColor = isApproved ? "text-green-500" : isReferred ? "text-yellow-500" : "text-red-500";
  const DecisionIcon = isApproved ? ShieldCheck : ShieldAlert;

  // Extract sections
  const { discovery, exposure, loss_propensity, signal_summary, modifiers_applied, base_premium } = activeSubmission;

  return (
    <div className="w-full max-w-7xl mx-auto space-y-8 animate-in fade-in duration-500 pb-12">
      
      {/* 1. TOP LINE KPI GRID */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
        
        {/* RECOMMENDED PREMIUM (Now Clickable!) */}
        <div 
          onClick={() => setShowPremiumCalc(true)}
          className="p-4 border border-dsi-outline/20 rounded-xl bg-dsi-background/30 flex flex-col gap-2 relative overflow-hidden cursor-pointer hover:bg-dsi-selected/5 hover:border-dsi-selected/30 transition-all group"
        >
          <div className="text-xs font-semibold tracking-wider text-dsi-selected opacity-70 uppercase flex items-center justify-between z-10">
            Recommended Premium
            <Calculator className="w-3.5 h-3.5 opacity-0 group-hover:opacity-100 transition-opacity" />
          </div>
          <div className="text-2xl font-bold font-inter tracking-tight z-10">
            {formatCurrency(activeSubmission.recommended_premium)}
          </div>
          <DollarSign className="absolute right-[-10px] bottom-[-10px] w-16 h-16 text-dsi-outline/10 group-hover:scale-110 transition-transform" />
        </div>

        {/* ... (Other KPI Cards remain exactly the same) ... */}
        <div className="p-4 border border-dsi-outline/20 rounded-xl bg-dsi-background/30 flex flex-col gap-2 relative overflow-hidden">
          <div className="text-xs font-semibold tracking-wider text-dsi-selected opacity-70 uppercase">Limit</div>
          <div className="text-2xl font-bold font-inter tracking-tight">{formatCurrency(activeSubmission.recommended_limit)}</div>
          <Target className="absolute right-[-10px] bottom-[-10px] w-16 h-16 text-dsi-outline/10" />
        </div>

        <div className="p-4 border border-dsi-outline/20 rounded-xl bg-dsi-background/30 flex flex-col gap-2 relative overflow-hidden">
          <div className="text-xs font-semibold tracking-wider text-dsi-selected opacity-70 uppercase">Composite Score</div>
          <div className="flex items-baseline gap-2">
            <span className="text-2xl font-bold font-inter tracking-tight">{activeSubmission.composite_score || activeSubmission.pure_composite_score || "N/A"}</span>
            <span className="text-xs opacity-50">/ 1000</span>
          </div>
          <Activity className="absolute right-[-10px] bottom-[-10px] w-16 h-16 text-dsi-outline/10" />
        </div>

        <div className="p-4 border border-dsi-outline/20 rounded-xl bg-dsi-background/30 flex flex-col gap-2 relative overflow-hidden">
          <div className="text-xs font-semibold tracking-wider text-dsi-selected opacity-70 uppercase">Risk Tier</div>
          <div className="flex items-baseline gap-2">
            <span className="text-2xl font-bold font-inter tracking-tight">{activeSubmission.tier || activeSubmission.final_tier || "N/A"}</span>
            <span className="text-xs font-mono opacity-60">{activeSubmission.tier_label?.replace('_', ' ')}</span>
          </div>
        </div>

        <div className={`p-4 border rounded-xl bg-dsi-background/30 flex flex-col gap-2 relative overflow-hidden transition-colors ${
          isApproved ? 'border-green-500/30' : isReferred ? 'border-yellow-500/30' : 'border-red-500/30'
        }`}>
          <div className="text-xs font-semibold tracking-wider text-dsi-selected opacity-70 uppercase">System Decision</div>
          <div className={`text-2xl font-bold font-inter tracking-tight capitalize ${decisionColor}`}>{activeSubmission.decision}</div>
          <DecisionIcon className={`absolute right-[-10px] bottom-[-10px] w-16 h-16 opacity-10 ${decisionColor}`} />
        </div>
      </div>

      {/* 2. THREE PILLAR ASSESSMENT (Remains exactly the same) */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        <div className="border border-dsi-outline/20 rounded-xl bg-dsi-background/10 overflow-hidden flex flex-col">
          <div className="px-4 py-3 border-b border-dsi-outline/20 bg-dsi-selected/5 flex items-center gap-2">
            <Network className="w-4 h-4 text-dsi-selected opacity-70" />
            <h3 className="font-semibold tracking-wide text-sm uppercase">1. Discovery & Firmographics</h3>
          </div>
          <div className="p-4 flex-1 flex flex-col gap-4">
            <div className="flex items-center justify-between">
              <span className="text-sm opacity-70 flex items-center gap-2"><Globe className="w-4 h-4" /> Domain</span>
              <span className="font-mono text-sm">{discovery?.domain || "N/A"}</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm opacity-70 flex items-center gap-2"><Building className="w-4 h-4" /> Industry</span>
              <span className="font-medium text-sm text-right max-w-[150px] truncate">{discovery?.industry || "N/A"}</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm opacity-70 flex items-center gap-2"><Users className="w-4 h-4" /> Employees</span>
              <span className="font-mono text-sm">{formatNumber(discovery?.employee_count)}</span>
            </div>
            <div className="mt-auto pt-4 border-t border-dsi-outline/10 flex items-center justify-between">
              <span className="text-xs opacity-50 uppercase tracking-wider">Discovery Confidence</span>
              <span className="text-xs font-bold text-dsi-selected uppercase bg-dsi-selected/10 px-2 py-1 rounded">
                {discovery?.confidence || "N/A"}
              </span>
            </div>
          </div>
        </div>

        <div className="border border-dsi-outline/20 rounded-xl bg-dsi-background/10 overflow-hidden flex flex-col">
          <div className="px-4 py-3 border-b border-dsi-outline/20 bg-dsi-selected/5 flex items-center gap-2">
            <Scale className="w-4 h-4 text-dsi-selected opacity-70" />
            <h3 className="font-semibold tracking-wide text-sm uppercase">2. Exposure Base</h3>
          </div>
          <div className="p-4 flex-1 flex flex-col gap-4">
            <div className="flex flex-col gap-1">
              <span className="text-sm opacity-70">Primary Exposure Value</span>
              <span className="text-xl font-bold font-mono text-dsi-selected">{formatCurrency(exposure?.exposure_value)}</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm opacity-70">Exposure Band</span>
              <span className="font-medium text-sm bg-dsi-contrast-background/5 px-2 py-0.5 rounded border border-dsi-outline/10">
                {exposure?.exposure_band_label || "N/A"}
              </span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm opacity-70">Magnitude Score</span>
              <span className="font-mono text-sm">{exposure?.exposure_magnitude_score?.toFixed(1) || "N/A"}</span>
            </div>
            <div className="mt-auto pt-4 border-t border-dsi-outline/10 flex items-center justify-between">
              <span className="text-xs opacity-50 uppercase tracking-wider">Exposure Modifier</span>
              <span className={`text-sm font-bold font-mono ${exposure?.exposure_modifier && exposure.exposure_modifier > 1 ? 'text-red-400' : 'text-green-400'}`}>
                {exposure?.exposure_modifier ? `${exposure.exposure_modifier.toFixed(2)}x` : "1.00x"}
              </span>
            </div>
          </div>
        </div>

        <div className="border border-dsi-outline/20 rounded-xl bg-dsi-background/10 overflow-hidden flex flex-col">
          <div className="px-4 py-3 border-b border-dsi-outline/20 bg-dsi-selected/5 flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 text-dsi-selected opacity-70" />
            <h3 className="font-semibold tracking-wide text-sm uppercase">3. Loss Propensity</h3>
          </div>
          <div className="p-4 flex-1 flex flex-col gap-4">
            <div className="flex items-center justify-between">
              <span className="text-sm opacity-70 flex items-center gap-2"><BarChart className="w-4 h-4" /> Freq / Sev Score</span>
              <div className="flex items-center gap-1 font-mono text-sm">
                <span className="text-blue-400">{loss_propensity?.loss_propensity_score?.toFixed(1) || "N/A"}</span>
                <span className="opacity-50">/</span>
                <span className="text-orange-400">{loss_propensity?.severity_propensity_score?.toFixed(1) || "N/A"}</span>
              </div>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm opacity-70">Risk Cohort</span>
              <span className="font-medium text-sm truncate max-w-[160px] text-right">{loss_propensity?.loss_cohort_name || "N/A"}</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm opacity-70 flex items-center gap-2"><TrendingUp className="w-4 h-4" /> Trend</span>
              <span className={`text-xs font-bold uppercase px-2 py-1 rounded ${
                loss_propensity?.loss_trend_direction === 'improving' ? 'bg-green-500/10 text-green-500' :
                loss_propensity?.loss_trend_direction === 'deteriorating' ? 'bg-red-500/10 text-red-500' :
                'bg-yellow-500/10 text-yellow-500'
              }`}>
                {loss_propensity?.loss_trend_direction || "Stable"}
              </span>
            </div>
            <div className="mt-auto pt-4 border-t border-dsi-outline/10 flex items-center justify-between">
              <span className="text-xs opacity-50 uppercase tracking-wider">Combined Modifier</span>
              <span className={`text-sm font-bold font-mono ${loss_propensity?.loss_combined_modifier && loss_propensity.loss_combined_modifier > 1 ? 'text-red-400' : 'text-green-400'}`}>
                {loss_propensity?.loss_combined_modifier ? `${loss_propensity.loss_combined_modifier.toFixed(2)}x` : "1.00x"}
              </span>
            </div>
          </div>
        </div>

      </div>

      {/* 3. TOP SIGNAL FACTORS */}
      {signal_summary && signal_summary.top_factors && signal_summary.top_factors.length > 0 && (
        <div className="pt-4 space-y-4">
          <div className="flex items-center gap-2">
            <Info className="w-4 h-4 text-dsi-selected opacity-70" />
            <h3 className="font-semibold tracking-wide text-sm uppercase text-dsi-selected">Key Influencing Signals</h3>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {signal_summary.top_factors.map((factor: any, i: number) => {
              const isPositive = factor.impact === "positive";
              const isNegative = factor.impact === "negative";
              const FactorIcon = isPositive ? CheckCircle2 : isNegative ? XCircle : MinusCircle;
              const colorClass = isPositive ? "text-green-500 border-green-500/30 bg-green-500/5" : 
                                 isNegative ? "text-red-500 border-red-500/30 bg-red-500/5" : 
                                 "text-yellow-500 border-yellow-500/30 bg-yellow-500/5";

              return (
                <div key={i} className={`p-4 border rounded-xl flex flex-col gap-2 ${colorClass}`}>
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-mono uppercase tracking-wider opacity-70 truncate pr-2">
                      {factor.signal?.replace(/_/g, ' ')}
                    </span>
                    <FactorIcon className="w-5 h-5 opacity-80 shrink-0" />
                  </div>
                  <div className="flex items-end justify-between mt-2">
                    <span className="text-2xl font-bold font-inter tracking-tight">{factor.score}</span>
                    <span className="text-xs uppercase tracking-wider opacity-70 font-semibold">{factor.impact} impact</span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* 4. PREMIUM CALCULATION MODAL */}
      {showPremiumCalc && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-dsi-contrast-background/80 backdrop-blur-sm animate-in fade-in duration-200">
          <div className="w-full max-w-md bg-dsi-background border border-dsi-outline rounded-2xl shadow-2xl flex flex-col overflow-hidden">
            
            {/* Modal Header */}
            <div className="px-6 py-4 border-b border-dsi-outline/20 flex items-center justify-between bg-dsi-selected/5">
              <h2 className="text-lg font-bold flex items-center gap-2">
                <Calculator className="w-5 h-5 text-dsi-selected" /> Premium Calculation
              </h2>
              <button 
                onClick={() => setShowPremiumCalc(false)}
                className="p-1 hover:bg-dsi-selected/10 rounded-full transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Receipt Content */}
            <div className="p-6 font-mono text-sm space-y-4">
              
              {/* Base Premium */}
              <div className="flex justify-between items-center pb-4 border-b border-dsi-outline/10 text-dsi-selected opacity-80">
                <span>Base Premium (Tier {activeSubmission.tier})</span>
                <span>{formatCurrency(base_premium)}</span>
              </div>

              {/* Modifiers List */}
              <div className="space-y-3 py-2">
                <div className="text-xs uppercase tracking-wider opacity-50 font-sans font-semibold">Applied Modifiers</div>
                
                {modifiers_applied?.map((mod: any, i: number) => (
                  <div key={i} className="flex justify-between items-center">
                    <span className="truncate pr-4">{mod.name}</span>
                    <span className={mod.factor > 1 ? 'text-red-400' : 'text-green-400'}>
                      x {mod.factor?.toFixed(2)}
                    </span>
                  </div>
                ))}

                {/* Always show 3-pillar modifiers if they exist and aren't in the list already */}
                {exposure?.exposure_modifier && (
                  <div className="flex justify-between items-center">
                    <span className="truncate pr-4">Exposure Base: {exposure.exposure_band_label}</span>
                    <span className={exposure.exposure_modifier > 1 ? 'text-red-400' : 'text-green-400'}>
                      x {exposure.exposure_modifier.toFixed(2)}
                    </span>
                  </div>
                )}
                
                {loss_propensity?.loss_combined_modifier && (
                  <div className="flex justify-between items-center">
                    <span className="truncate pr-4">Loss Propensity: {loss_propensity.loss_cohort_name}</span>
                    <span className={loss_propensity.loss_combined_modifier > 1 ? 'text-red-400' : 'text-green-400'}>
                      x {loss_propensity.loss_combined_modifier.toFixed(2)}
                    </span>
                  </div>
                )}
              </div>

              {/* Final Math */}
              <div className="pt-4 border-t-2 border-dashed border-dsi-outline/20 flex justify-between items-center text-lg">
                <span className="font-bold font-sans tracking-wide">Final Premium</span>
                <span className="font-bold text-dsi-selected">{formatCurrency(activeSubmission.recommended_premium)}</span>
              </div>

            </div>
          </div>
        </div>
      )}

    </div>
  );
}
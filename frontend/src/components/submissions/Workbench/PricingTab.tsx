"use client";

import { useDsiStore } from "@/store/dsiStore";
import { Calculator, DollarSign, ShieldCheck, ArrowRightIcon } from "lucide-react";

export default function PricingTab() {
  const { activeSubmission, activeQuote, activeVersion } = useDsiStore();

  if (!activeSubmission || !activeVersion) {
    return (
      <div className="flex items-center justify-center h-full text-dsi-selected/50 animate-pulse">
        Loading pricing details...
      </div>
    );
  }

  // Calculate the total impact of all modifiers for the KPI
  const basePremium = activeVersion.base_premium || 0;
  const finalPremium = activeVersion.premium_after_modifiers || 0;
  const modifierImpact = finalPremium - basePremium;
  const modifierImpactPercent = basePremium > 0 ? (modifierImpact / basePremium) * 100 : 0;

  return (
    <div className="w-full max-w-[1400px] mx-auto space-y-6 animate-in fade-in duration-500 pb-12 pt-4">
      
      {/* =======================================================================
          COMPONENT A: PRICING KPIs
          ======================================================================= */}
      <div className="border border-dsi-outline/20 rounded-xl p-5 bg-dsi-analysis shadow-sm">
        <h3 className="text-sm font-bold tracking-wide flex items-center gap-2 mb-4 border-b border-dsi-outline/10 pb-2">
          <DollarSign className="w-4 h-4 text-dsi-selected" /> Recommended Quote Details
        </h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
          <div>
            <span className="opacity-50 block text-xs mb-1">Recommended Premium</span>
            <span className="font-mono font-bold text-2xl text-dsi-selected">
              {activeQuote?.recommended_premium ? `$${activeQuote.recommended_premium.toLocaleString()}` : "Pending"}
            </span>
          </div>
          <div>
            <span className="opacity-50 block text-xs mb-1">Recommended Limit</span>
            <span className="font-mono font-bold text-2xl">
              {activeQuote?.recommended_limit ? `$${activeQuote.recommended_limit.toLocaleString()}` : "Pending"}
            </span>
          </div>
          <div>
            <span className="opacity-50 block text-xs mb-1">Base Premium (Tier {activeVersion.final_tier})</span>
            <span className="font-mono font-bold text-xl opacity-80">
              ${basePremium.toLocaleString()}
            </span>
          </div>
          <div>
            <span className="opacity-50 block text-xs mb-1">Net Modifier Impact</span>
            <span className={`font-mono font-bold text-xl ${modifierImpact > 0 ? 'text-rose-400' : 'text-emerald-400'}`}>
              {modifierImpact > 0 ? '+' : ''}{modifierImpactPercent.toFixed(1)}% (${Math.abs(modifierImpact).toLocaleString()})
            </span>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* =======================================================================
            COMPONENT B: PRICING ANATOMY (WATERFALL)
            ======================================================================= */}
        <div className="lg:col-span-2 border border-dsi-outline/20 rounded-xl p-5 bg-dsi-analysis shadow-sm flex flex-col">
          <h3 className="text-sm font-bold tracking-wide flex items-center gap-2 mb-6">
            <Calculator className="w-4 h-4 text-dsi-selected" /> Pricing Anatomy
          </h3>
          
          <div className="flex-1 overflow-x-auto">
            <table className="w-full text-sm font-mono text-left whitespace-nowrap">
              <thead>
                <tr className="border-b border-dsi-outline/20 text-xs uppercase tracking-wider opacity-50">
                  <th className="py-3 px-2 font-semibold">Calculation Step</th>
                  <th className="py-3 px-2 font-semibold text-right">Modifier</th>
                  <th className="py-3 px-2 font-semibold text-right">Premium Impact</th>
                  <th className="py-3 px-2 font-semibold text-right">Running Total</th>
                </tr>
              </thead>
              <tbody>
                {/* 1. Base Premium Row */}
                <tr className="border-b border-dsi-outline/10 bg-dsi-selected/5">
                  <td className="py-4 px-2 font-bold flex items-center gap-2">
                    <ArrowRightIcon className="w-3 h-3 opacity-50" /> Base Premium (Tier {activeVersion.final_tier})
                  </td>
                  <td className="py-4 px-2 text-right opacity-50">-</td>
                  <td className="py-4 px-2 text-right opacity-50">-</td>
                  <td className="py-4 px-2 text-right font-bold">${basePremium.toLocaleString()}</td>
                </tr>

                {/* 2. Modifiers Rows */}
                {activeVersion.modifiers_applied?.length > 0 ? (
                  activeVersion.modifiers_applied.map((mod: any, idx: number) => {
                    // Calculate the dollar impact of this specific step
                    const impact = (mod.premium_after || 0) - (mod.premium_before || 0);
                    const isCredit = impact < 0;

                    return (
                      <tr key={idx} className="border-b border-dsi-outline/5 hover:bg-dsi-outline/5 transition-colors">
                        <td className="py-3 px-2 opacity-90 pl-6 border-l-2 border-transparent hover:border-dsi-selected">
                          {mod.note || mod.source}
                        </td>
                        <td className="py-3 px-2 text-right font-semibold">
                          {Number(mod.applied ?? 1.0).toFixed(3)}x
                        </td>
                        <td className={`py-3 px-2 text-right ${isCredit ? 'text-emerald-400' : 'text-rose-400'}`}>
                          {impact > 0 ? '+' : ''}${Math.abs(impact).toLocaleString()}
                        </td>
                        <td className="py-3 px-2 text-right opacity-80">
                          ${(mod.premium_after || 0).toLocaleString()}
                        </td>
                      </tr>
                    );
                  })
                ) : (
                  <tr>
                    <td colSpan={4} className="py-6 text-center text-xs opacity-50 italic">
                      No modifiers applied to this quote.
                    </td>
                  </tr>
                )}

                {/* 3. Final Premium Row */}
                <tr className="border-t-2 border-dsi-outline/20 bg-dsi-selected/10 text-dsi-selected">
                  <td className="py-4 px-2 font-bold uppercase tracking-wider text-xs">
                    Final Technical Premium
                  </td>
                  <td className="py-4 px-2 text-right opacity-50">-</td>
                  <td className="py-4 px-2 text-right font-bold">
                    {modifierImpact > 0 ? '+' : ''}${Math.abs(modifierImpact).toLocaleString()}
                  </td>
                  <td className="py-4 px-2 text-right font-bold text-lg">
                    ${finalPremium.toLocaleString()}
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        {/* =======================================================================
            COMPONENT C: LIMIT OPTIONS
            ======================================================================= */}
        <div className="border border-dsi-outline/20 rounded-xl p-5 bg-dsi-analysis shadow-sm flex flex-col">
          <h3 className="text-sm font-bold tracking-wide flex items-center gap-2 mb-6">
            <ShieldCheck className="w-4 h-4 text-dsi-selected" /> Alternative Limit Options
          </h3>
          <p className="text-xs opacity-50 mb-4">
            Pre-calculated technical premiums for alternative limit requests based on the current model version.
          </p>
          
          <div className="flex-1 w-full space-y-2">
            {Object.keys(activeVersion.limit_premiums || {}).length > 0 ? (
              Object.entries(activeVersion.limit_premiums)
                // Sort by limit amount ascending
                .sort(([limitA], [limitB]) => parseInt(limitA) - parseInt(limitB))
                .map(([limit, premium]: any) => {
                  const isRecommended = activeQuote?.recommended_limit === parseInt(limit);
                  
                  return (
                    <div 
                      key={limit} 
                      className={`flex justify-between items-center p-3 rounded-lg border ${
                        isRecommended 
                          ? 'bg-dsi-selected/10 border-dsi-selected text-dsi-selected' 
                          : 'bg-dsi-background/30 border-dsi-outline/10 hover:border-dsi-outline/30'
                      } transition-all`}
                    >
                      <div className="flex items-center gap-2">
                        <span className="font-mono text-sm">${parseInt(limit).toLocaleString()} Limit</span>
                        {isRecommended && (
                          <span className="text-[10px] uppercase font-bold tracking-wider bg-dsi-selected text-dsi-background px-1.5 py-0.5 rounded">
                            Recommended
                          </span>
                        )}
                      </div>
                      <span className="font-mono font-bold text-lg">
                        ${premium.toLocaleString()}
                      </span>
                    </div>
                  );
                })
            ) : (
              <div className="flex h-40 items-center justify-center opacity-50 italic text-sm border border-dashed border-dsi-outline/20 rounded-lg">
                No alternative limit options generated.
              </div>
            )}
          </div>
        </div>

      </div>
    </div>
  );
}
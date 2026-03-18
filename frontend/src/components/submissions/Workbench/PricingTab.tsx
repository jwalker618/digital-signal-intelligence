"use client";

import { useState } from "react";
import { useDsiStore } from "@/store/dsiStore";
import { Calculator, DollarSign, ShieldCheck, ChevronDown, ChevronRight, ArrowRightToLine } from "lucide-react";

export default function PricingTab() {
  const { activeSubmission, activeQuote, activeVersion } = useDsiStore();

  // Accordion state for the grouped modifiers
  const [expandedGroups, setExpandedGroups] = useState<Record<string, boolean>>({
    signal: true,
    query: true,
    modifiers: true
  });

  const toggleGroup = (group: string) => {
    setExpandedGroups(prev => ({ ...prev, [group]: !prev[group] }));
  };

  if (!activeSubmission || !activeVersion) {
    return (
      <div className="flex items-center justify-center h-full text-dsi-selected/50 animate-pulse">
        Loading pricing details...
      </div>
    );
  }

  // =======================================================================
  // KPI CALCULATIONS
  // =======================================================================
  const recommendedPremium = activeQuote?.recommended_premium || 0;
  const recommendedLimit = activeQuote?.recommended_limit || 0;
  const basePremium = activeVersion.base_premium || 0;
  const anchorPremium = activeVersion.premium_after_modifiers || 0;

  // 1. Base to Anchor (Technical Modifiers Impact)
  const baseToAnchorDiff = anchorPremium - basePremium;
  const baseToAnchorPct = basePremium > 0 ? (baseToAnchorDiff / basePremium) * 100 : 0;

  // 2. Anchor to Final (ILF / Limit Impact)
  const anchorToFinalDiff = recommendedPremium - anchorPremium;
  const anchorToFinalPct = anchorPremium > 0 ? (anchorToFinalDiff / anchorPremium) * 100 : 0;

  // =======================================================================
  // DATA EXTRACTION & GROUPING
  // =======================================================================
  
  // Helper to extract and sort valid modifiers from arrays
  const extractModifiers = (arr: any[], isModifierAppliedArray = false) => {
    if (!arr) return [];
    return arr
      .filter(item => isModifierAppliedArray ? item.premium_before !== undefined : item.action === 'modifier')
      .map(item => ({
        name: item.note || item.source_name || item.source_id || item.source,
        multiplier: isModifierAppliedArray ? item.applied : item.action_value,
        before: item.premium_before || 0,
        after: item.premium_after || 0,
        impact: (item.premium_after || 0) - (item.premium_before || 0)
      }))
      .sort((a, b) => a.before - b.before);
  };

  const signalItems = extractModifiers(activeVersion.signal_conditions, false);
  const queryItems = extractModifiers(activeVersion.query_conditions, false);
  
  // For Modifiers Applied, we filter out direct_query and signal_feature types 
  // so they don't double-render if the backend aggregates them here.
  const modifierItems = extractModifiers(activeVersion.modifiers_applied, true)
    .filter((item: any) => {
      const orig = activeVersion.modifiers_applied.find((m: any) => m.note === item.name || m.source === item.name);
      return orig && orig.type !== 'direct_query' && orig.type !== 'signal_feature';
    });

  // Calculate Group Totals
  const signalTotal = signalItems.reduce((acc, item) => acc + item.impact, 0);
  const queryTotal = queryItems.reduce((acc, item) => acc + item.impact, 0);
  const modifiersTotal = modifierItems.reduce((acc, item) => acc + item.impact, 0);

  // Formatting helper
  const formatImpact = (val: number) => {
    const isCredit = val < 0;
    return (
      <span className={val === 0 ? "opacity-50" : isCredit ? "text-emerald-400" : "text-rose-400"}>
        {val > 0 ? '+' : ''}${Math.abs(val).toLocaleString()}
      </span>
    );
  };

  return (
    <div className="w-full max-w-[1400px] mx-auto space-y-6 animate-in fade-in duration-500 pb-12 pt-4">
      
      {/* =======================================================================
          COMPONENT A: PRICING SUMMARY KPIs
          ======================================================================= */}
      <div className="border border-dsi-outline/20 rounded-xl p-5 bg-dsi-analysis shadow-sm">
        <h3 className="text-sm font-bold tracking-wide flex items-center gap-2 mb-4 border-b border-dsi-outline/10 pb-2">
          <DollarSign className="w-4 h-4 text-dsi-selected" /> Recommended Quote Details
        </h3>
        <div className="grid grid-cols-2 md:grid-cols-6 gap-6">
          
          <div className="col-span-2 md:col-span-1">
            <span className="opacity-50 block text-xs mb-1">Recommended Limit</span>
            <span className="font-mono font-bold text-xl">
              {recommendedLimit ? `$${recommendedLimit.toLocaleString()}` : "Pending"}
            </span>
          </div>

          <div className="col-span-2 md:col-span-1 border-l border-dsi-outline/20 pl-6">
            <span className="opacity-50 block text-xs mb-1">Base Premium</span>
            <span className="font-mono font-bold text-lg opacity-80">
              ${basePremium.toLocaleString()}
            </span>
          </div>

          <div className="col-span-2 md:col-span-1">
            <span className="opacity-50 block text-xs mb-1">Tech Impact</span>
            <span className="font-mono font-bold text-sm block mb-0.5">
              {formatImpact(baseToAnchorDiff)}
            </span>
            <span className="text-xs opacity-70">
              {baseToAnchorDiff > 0 ? '+' : ''}{baseToAnchorPct.toFixed(1)}%
            </span>
          </div>

          <div className="col-span-2 md:col-span-1 border-l border-dsi-outline/20 pl-6">
            <span className="text-dsi-selected block text-xs mb-1 font-bold">Anchor Base Modified</span>
            <span className="font-mono font-bold text-xl text-dsi-selected">
              ${anchorPremium.toLocaleString()}
            </span>
          </div>

          <div className="col-span-2 md:col-span-1">
            <span className="opacity-50 block text-xs mb-1">ILF / Limit Impact</span>
            <span className="font-mono font-bold text-sm block mb-0.5">
              {formatImpact(anchorToFinalDiff)}
            </span>
            <span className="text-xs opacity-70">
              {anchorToFinalDiff > 0 ? '+' : ''}{anchorToFinalPct.toFixed(1)}%
            </span>
          </div>

          <div className="col-span-2 md:col-span-1 bg-dsi-selected/10 -m-2 p-3 rounded-lg border border-dsi-selected/30">
            <span className="text-dsi-selected block text-xs mb-1 font-bold uppercase tracking-wider">Final Premium</span>
            <span className="font-mono font-bold text-2xl text-dsi-selected">
              {recommendedPremium ? `$${recommendedPremium.toLocaleString()}` : "Pending"}
            </span>
          </div>

        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* =======================================================================
            COMPONENT B: PRICING ANATOMY (WATERFALL GROUPS)
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
                <tr className="border-b border-dsi-outline/20 bg-dsi-selected/5">
                  <td className="py-4 px-2 font-bold flex items-center gap-2">
                    <ArrowRightToLine className="w-3 h-3 opacity-50" /> Base Premium (Tier {activeVersion.final_tier})
                  </td>
                  <td className="py-4 px-2 text-right opacity-50">-</td>
                  <td className="py-4 px-2 text-right opacity-50">-</td>
                  <td className="py-4 px-2 text-right font-bold">${basePremium.toLocaleString()}</td>
                </tr>

                {/* --- GROUP 1: SIGNAL ADJUSTMENTS --- */}
                <tr 
                  className="bg-dsi-background/30 border-b border-dsi-outline/10 cursor-pointer hover:bg-dsi-background/50 transition-colors"
                  onClick={() => toggleGroup('signal')}
                >
                  <td className="py-3 px-2 font-semibold flex items-center gap-2">
                    {expandedGroups.signal ? <ChevronDown className="w-4 h-4 text-dsi-selected" /> : <ChevronRight className="w-4 h-4 text-dsi-selected" />}
                    Signal Adjustments
                  </td>
                  <td className="py-3 px-2 text-right opacity-50 text-xs">{signalItems.length} items</td>
                  <td className="py-3 px-2 text-right font-bold">{formatImpact(signalTotal)}</td>
                  <td className="py-3 px-2 text-right opacity-50">-</td>
                </tr>
                {expandedGroups.signal && signalItems.map((mod, idx) => (
                  <tr key={`sig-${idx}`} className="border-b border-dsi-outline/5 hover:bg-dsi-outline/5 transition-colors bg-dsi-background/10">
                    <td className="py-2.5 px-2 opacity-80 pl-8 border-l-2 border-transparent hover:border-dsi-selected truncate max-w-xs" title={mod.name}>
                      {mod.name}
                    </td>
                    <td className="py-2.5 px-2 text-right">{Number(mod.multiplier).toFixed(3)}x</td>
                    <td className="py-2.5 px-2 text-right">{formatImpact(mod.impact)}</td>
                    <td className="py-2.5 px-2 text-right opacity-70">${mod.after.toLocaleString()}</td>
                  </tr>
                ))}
                {expandedGroups.signal && signalItems.length === 0 && (
                  <tr className="bg-dsi-background/10"><td colSpan={4} className="py-3 px-8 text-xs opacity-50 italic">No signal modifiers applied.</td></tr>
                )}

                {/* --- GROUP 2: DIRECT QUERY ADJUSTMENTS --- */}
                <tr 
                  className="bg-dsi-background/30 border-b border-dsi-outline/10 cursor-pointer hover:bg-dsi-background/50 transition-colors"
                  onClick={() => toggleGroup('query')}
                >
                  <td className="py-3 px-2 font-semibold flex items-center gap-2">
                    {expandedGroups.query ? <ChevronDown className="w-4 h-4 text-dsi-selected" /> : <ChevronRight className="w-4 h-4 text-dsi-selected" />}
                    Direct Query Adjustments
                  </td>
                  <td className="py-3 px-2 text-right opacity-50 text-xs">{queryItems.length} items</td>
                  <td className="py-3 px-2 text-right font-bold">{formatImpact(queryTotal)}</td>
                  <td className="py-3 px-2 text-right opacity-50">-</td>
                </tr>
                {expandedGroups.query && queryItems.map((mod, idx) => (
                  <tr key={`query-${idx}`} className="border-b border-dsi-outline/5 hover:bg-dsi-outline/5 transition-colors bg-dsi-background/10">
                    <td className="py-2.5 px-2 opacity-80 pl-8 border-l-2 border-transparent hover:border-dsi-selected truncate max-w-xs" title={mod.name}>
                      {mod.name}
                    </td>
                    <td className="py-2.5 px-2 text-right">{Number(mod.multiplier).toFixed(3)}x</td>
                    <td className="py-2.5 px-2 text-right">{formatImpact(mod.impact)}</td>
                    <td className="py-2.5 px-2 text-right opacity-70">${mod.after.toLocaleString()}</td>
                  </tr>
                ))}
                {expandedGroups.query && queryItems.length === 0 && (
                  <tr className="bg-dsi-background/10"><td colSpan={4} className="py-3 px-8 text-xs opacity-50 italic">No direct query modifiers applied.</td></tr>
                )}

                {/* --- GROUP 3: MODIFIERS APPLIED --- */}
                <tr 
                  className="bg-dsi-background/30 border-b border-dsi-outline/10 cursor-pointer hover:bg-dsi-background/50 transition-colors"
                  onClick={() => toggleGroup('modifiers')}
                >
                  <td className="py-3 px-2 font-semibold flex items-center gap-2">
                    {expandedGroups.modifiers ? <ChevronDown className="w-4 h-4 text-dsi-selected" /> : <ChevronRight className="w-4 h-4 text-dsi-selected" />}
                    Modifiers Applied
                  </td>
                  <td className="py-3 px-2 text-right opacity-50 text-xs">{modifierItems.length} items</td>
                  <td className="py-3 px-2 text-right font-bold">{formatImpact(modifiersTotal)}</td>
                  <td className="py-3 px-2 text-right opacity-50">-</td>
                </tr>
                {expandedGroups.modifiers && modifierItems.map((mod, idx) => (
                  <tr key={`mod-${idx}`} className="border-b border-dsi-outline/5 hover:bg-dsi-outline/5 transition-colors bg-dsi-background/10">
                    <td className="py-2.5 px-2 opacity-80 pl-8 border-l-2 border-transparent hover:border-dsi-selected truncate max-w-xs" title={mod.name}>
                      {mod.name}
                    </td>
                    <td className="py-2.5 px-2 text-right">{Number(mod.multiplier).toFixed(3)}x</td>
                    <td className="py-2.5 px-2 text-right">{formatImpact(mod.impact)}</td>
                    <td className="py-2.5 px-2 text-right opacity-70">${mod.after.toLocaleString()}</td>
                  </tr>
                ))}
                {expandedGroups.modifiers && modifierItems.length === 0 && (
                  <tr className="bg-dsi-background/10"><td colSpan={4} className="py-3 px-8 text-xs opacity-50 italic">No general modifiers applied.</td></tr>
                )}

                {/* --- ANCHOR PREMIUM --- */}
                <tr className="border-t-2 border-dsi-outline/20 bg-dsi-selected/10 text-dsi-selected">
                  <td className="py-4 px-2 font-bold uppercase tracking-wider text-xs">
                    Anchor Base Modified Premium
                  </td>
                  <td className="py-4 px-2 text-right opacity-50">-</td>
                  <td className="py-4 px-2 text-right font-bold">
                    {formatImpact(baseToAnchorDiff)}
                  </td>
                  <td className="py-4 px-2 text-right font-bold text-lg">
                    ${anchorPremium.toLocaleString()}
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
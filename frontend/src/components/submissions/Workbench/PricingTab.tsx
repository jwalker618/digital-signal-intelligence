"use client";

import { useState } from "react";
import { useDsiStore } from "@/store/dsiStore";
import { Calculator, HandCoins, ShieldCheck, ChevronDown, ChevronRight, ArrowRightToLine, Paperclip, SquareMenu} from "lucide-react";

export default function PricingTab() {
  const { activeSubmission, activeQuote, activeVersion } = useDsiStore();

  // Accordion state for the grouped modifiers
  const [expandedGroups, setExpandedGroups] = useState<Record<string, boolean>>({
    categorcial: true,
    signal: true,
    query: true,
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
  // DATA EXTRACTION & GROUPING
  // =======================================================================
  
  // Helper to extract and sort valid modifiers from arrays
  const extractModifiers = (arr: any[], sourceType: string) => {
    if (!arr) return [];
    return arr
      .filter(item => item.source === sourceType)
      .map(item => ({
        name: item.name,
        multiplier: item.applied,
        before: item.premium_before || 0,
        after: item.premium_after || 0,
        impact: (item.premium_after || 0) - (item.premium_before || 0)
      }))
      .sort((a, b) => a.before - b.before);
  };

  // extract categorical changes
  const categoricalItems = extractModifiers(activeVersion.modifiers_applied, 'categorical');

  // extract signal changes
  const signalItems = extractModifiers(activeVersion.modifiers_applied, 'signal_condition');

  // extract direct changes
  const directItems = extractModifiers(activeVersion.modifiers_applied,'direct_query');

  // Calculate Group Totals
  const categoricalTotal = categoricalItems.reduce((acc, item) => acc + item.impact, 0);
  const signalTotal = signalItems.reduce((acc, item) => acc + item.impact, 0);
  const directTotal = directItems.reduce((acc, item) => acc + item.impact, 0);

  
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

  const premiumAfterCategorical = basePremium + categoricalTotal;
  const premiumAfterSignal = premiumAfterCategorical + signalTotal;
  const premiumAfterDirect = premiumAfterSignal + directTotal;

  return (
    <div className="
      w-full no-scrollbar 
      animate-in fade-in duration-500 pb-12"
      >
      {/* STICKY WRAPPER: Acts as a solid curtain to hide scrolling content */}
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
        <HandCoins className="icon"/><span className="text-sm">Recommended Quote Details</span>
      </div>
      {/* =======================================================================
          COMPONENT A: PRICING SUMMARY KPIs
          ======================================================================= */}
      <div className=" 
        border-b-3 border-dsi-contrast-background
        overflow-x-hidden whitespace-nowrap border-collapse
        rounded-b-xl
        bg-dsi-analysis shadow-sm
        pt-2 pb-2"        
        >
        <div className="
          grid grid-cols-6 grid-rows-1
          pl-dsi-pad
          pt-1 pb-1"
          >
          <div className="border-r-1 border-dsi-outline/50 overflow-x-hidden whitespace-nowrap border-collapse">
            <div className="mt-1 text-sm text-center underline pb-2"> 
              Base Premium
            </div>
            <div className="pl-dsi-pad pr-dsi-pad font-bold text-right">
              {basePremium.toLocaleString(undefined, { maximumFractionDigits: 0 })}
            </div>
            <div className="pl-dsi-pad pr-dsi-pad text-xs text-left">
              Calc. Methodology: {activeVersion.base_premium_method}
            </div>
          </div>
          <div className="border-r-1 border-dsi-outline/50 overflow-x-hidden whitespace-nowrap border-collapse">
            <div className="mt-1 pl-dsi-pad pr-dsi-pad text-sm text-center underline pb-2"> 
              Loaded Premium
            </div>
            <div className="pl-dsi-pad pr-dsi-pad font-bold text-right">
              {anchorPremium.toLocaleString(undefined, { maximumFractionDigits: 0 })}
            </div>
          </div>
          <div className="border-r-1 border-dsi-outline/50 overflow-x-hidden whitespace-nowrap border-collapse">
            <div className="pl-dsi-pad pr-dsi-pad text-sm text-center underline pb-2"> 
              Overall Loading
            </div>
            <div className="pl-dsi-pad pr-dsi-pad font-bold text-center">
              {baseToAnchorPct.toFixed(1)}%
            </div>
          </div>
          <div className="border-r-1 border-dsi-outline/50 overflow-x-hidden whitespace-nowrap border-collapse">
            <div className="mt-1 pl-dsi-pad pr-dsi-pad text-sm text-center underline pb-2"> 
              ILF
            </div>
            <div className="pl-dsi-pad pr-dsi-pad font-bold text-center">
              {activeVersion.ilf_factor.toFixed(1)}
            </div>
            <div className="pl-dsi-pad pr-dsi-pad text-xs text-left">
              Method: {activeVersion.ilf_method}
            </div>
            <div className="pl-dsi-pad pr-dsi-pad text-xs text-left">
              Anchor: {activeVersion.ilf_anchor_limit.toLocaleString()}
            </div>
          </div>
          <div className="
            bg-dsi-selected/10 border-r-1 border-dsi-outline/50 
            overflow-x-hidden whitespace-nowrap border-collapse
            text-dsi-selected"
            >
            <div className="mt-1 pl-dsi-pad pr-dsi-pad text-sm text-center underline pb-2"> 
              Final Premium
            </div>
            <div className="pl-dsi-pad pr-dsi-pad font-bold text-xl text-right">
              {recommendedPremium.toLocaleString(undefined, { maximumFractionDigits: 0 })}
            </div>
          </div>
          <div className="
            bg-dsi-selected/10 
            overflow-x-hidden whitespace-nowrap border-collapse
            text-dsi-selected
            mr-3"
            >
            <div className="mt-1 pl-dsi-pad pr-dsi-pad text-sm text-center underline pb-2"> 
              Final Limit
            </div>
            <div className="pl-dsi-pad pr-dsi-pad font-bold text-xl text-right">
              {recommendedLimit.toLocaleString(undefined, { maximumFractionDigits: 0 })}
            </div>
          </div>
        </div>
      </div>

      <div className="
        grid grid-cols-1 lg:grid-cols-3
        gap-2
        pt-2 pb-2
        ">

        <div className="lg:col-span-2 flex flex-col">
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
            <Calculator className="icon"/><span className="text-sm">Pricing Anatomy</span>
          </div>

          {/* =======================================================================
              COMPONENT B: PRICING ANATOMY (WATERFALL GROUPS)
              ======================================================================= */}
          <div className="
            flex flex-col flex-1
            border-b-3 border-dsi-contrast-background
            overflow-x-hidden whitespace-nowrap border-collapse
            rounded-b-xl
            bg-dsi-analysis shadow-sm
            pt-2 pb-2
            "
            >        
            <div className="
              flex-1 
              overflow-x-auto
              pl-dsi-pad pr-dsi-pad
              pt-2 pb-2
              "
              >
              <table className="w-full whitespace-nowrap border-collapse">
                <thead>
                  <tr className="text-center text-sm underline">
                    <th className="text-left font-normal">Calculation Step</th>
                    <th className="font-normal">Modifier</th>
                    <th className="font-normal">Premium Impact</th>
                    <th className="font-normal">Running Total</th>
                  </tr>
                </thead>
                <tbody>
                  
                  {/* 1. Base Premium Row */}
                  <tr className="border-b-1 border-dsi-outline/50"
                    >
                    <td className="
                      flex gap-dsi-pad 
                      text-sm
                      pt-dsi-pad pb-dsi-pad">
                      <ArrowRightToLine className="icon"/> Base Premium (Tier {activeVersion.final_tier})
                    </td>
                    <td className="pl-dsi-pad pr-dsi-pad text-center text-xs">-</td>
                    <td className="pl-dsi-pad pr-dsi-pad text-center text-xs">-</td>
                    <td className="pl-dsi-pad pr-dsi-pad text-right font-bold">{basePremium.toLocaleString(undefined, { maximumFractionDigits: 0 })}</td>
                  </tr>

                  {/* --- GROUP 1: CATEGORCIAL ADJUSTMENTS --- */}
                  <tr 
                    className="
                      cursor-pointer 
                      border-b border-dsi-outline/10 
                      hover:bg-dsi-background/20 
                      transition-colors
                      "
                    onClick={() => toggleGroup('categorical')}
                  >
                    <td className="
                      hover:text-dsi-selected
                      flex gap-dsi-pad 
                      text-sm
                      pt-dsi-pad pb-dsi-pad">
                      {expandedGroups.categorical ? <ChevronDown className="icon" /> : <ChevronRight className="icon" />}
                      Categorical Adjustments
                    </td>
                    <td className="pl-dsi-pad pr-dsi-pad text-center text-xs">{categoricalItems.length} items</td>
                    <td className="pl-dsi-pad pr-dsi-pad text-right font-bold">{categoricalTotal.toLocaleString(undefined, { maximumFractionDigits: 0 })}</td>
                    <td className="pl-dsi-pad pr-dsi-pad text-right">{premiumAfterCategorical.toLocaleString(undefined, { maximumFractionDigits: 0 })}</td>
                  </tr>
                  {expandedGroups.categorical && categoricalItems.map((mod, idx) => (
                    <tr key={`sig-${idx}`} className="bg-dsi-background/30"
                      >
                      <td className="pl-dsi-indent pr-dsi-pad text-sm" title={mod.name}>
                        {mod.name}
                      </td>
                      <td className="pl-dsi-pad pr-dsi-pad text-center text-xs">{Number(mod.multiplier).toFixed(3)}x</td>
                      <td className="pl-dsi-pad pr-dsi-pad text-right">{mod.impact.toLocaleString(undefined, { maximumFractionDigits: 0 })}</td>
                      <td className="pl-dsi-pad pr-dsi-pad text-right text-xs">-</td>
                    </tr>
                  ))}
                  {expandedGroups.categorical && categoricalItems.length === 0 && (
                    <tr className="bg-dsi-background/30"><td colSpan={4} className="pl-dsi-indent pr-dsi-pad text-xs opacity-50 italic">No modifiers applied.</td></tr>
                  )}

                  {/* --- GROUP 2: SIGNAL ADJUSTMENTS --- */}
                  <tr 
                    className="
                      cursor-pointer 
                      border-b border-dsi-outline/10 
                      hover:bg-dsi-background/20 
                      transition-colors
                      "
                    onClick={() => toggleGroup('signal')}
                  >
                    <td className="
                      hover:text-dsi-selected
                      flex gap-dsi-pad 
                      text-sm
                      pt-dsi-pad pb-dsi-pad">
                      {expandedGroups.signal ? <ChevronDown className="icon" /> : <ChevronRight className="icon" />}
                      Signal Adjustments
                    </td>
                    <td className="pl-dsi-pad pr-dsi-pad text-center text-xs">{signalItems.length} items</td>
                    <td className="pl-dsi-pad pr-dsi-pad text-right font-bold">{signalTotal.toLocaleString(undefined, { maximumFractionDigits: 0 })}</td>
                    <td className="pl-dsi-pad pr-dsi-pad text-right">{premiumAfterSignal.toLocaleString(undefined, { maximumFractionDigits: 0 })}</td>
                  </tr>
                  {expandedGroups.signal && signalItems.map((mod, idx) => (
                    <tr key={`sig-${idx}`} className="bg-dsi-background/30"
                      >
                      <td className="pl-dsi-indent pr-dsi-pad text-sm" title={mod.name}>
                        {mod.name}
                      </td>
                      <td className="pl-dsi-pad pr-dsi-pad text-center text-xs">{Number(mod.multiplier).toFixed(3)}x</td>
                      <td className="pl-dsi-pad pr-dsi-pad text-right">{mod.impact.toLocaleString(undefined, { maximumFractionDigits: 0 })}</td>
                      <td className="pl-dsi-pad pr-dsi-pad text-right text-xs">-</td>
                    </tr>
                  ))}
                  {expandedGroups.signal && signalItems.length === 0 && (
                    <tr className="bg-dsi-background/30"><td colSpan={4} className="pl-dsi-indent pr-dsi-pad text-xs opacity-50 italic">No modifiers applied.</td></tr>
                  )}

                  {/* --- GROUP 3: DIRECT ADJUSTMENTS --- */}
                  <tr 
                    className="
                      cursor-pointer 
                      hover:bg-dsi-background/20 
                      transition-colors
                      "
                    onClick={() => toggleGroup('direct')}
                  >
                    <td className="
                      hover:text-dsi-selected
                      flex gap-dsi-pad 
                      text-sm
                      pt-dsi-pad pb-dsi-pad">
                      {expandedGroups.direct ? <ChevronDown className="icon" /> : <ChevronRight className="icon" />}
                      Direct Query Adjustments
                    </td>
                    <td className="pl-dsi-pad pr-dsi-pad text-center text-xs">{directItems.length} items</td>
                    <td className="pl-dsi-pad pr-dsi-pad text-right font-bold">{directTotal.toLocaleString(undefined, { maximumFractionDigits: 0 })}</td>
                    <td className="pl-dsi-pad pr-dsi-pad text-right">{premiumAfterDirect.toLocaleString(undefined, { maximumFractionDigits: 0 })}</td>
                  </tr>
                  {expandedGroups.direct && directItems.map((mod, idx) => (
                    <tr key={`sig-${idx}`} className="bg-dsi-background/30"
                      >
                      <td className="pl-dsi-indent pr-dsi-pad text-sm" title={mod.name}>
                        {mod.name}
                      </td>
                      <td className="pl-dsi-pad pr-dsi-pad text-center text-xs">{Number(mod.multiplier).toFixed(3)}x</td>
                      <td className="pl-dsi-pad pr-dsi-pad text-right">{mod.impact.toLocaleString(undefined, { maximumFractionDigits: 0 })}</td>
                      <td className="pl-dsi-pad pr-dsi-pad text-right text-xs">-</td>
                    </tr>
                  ))}
                  {expandedGroups.direct && directItems.length === 0 && (
                    <tr className="bg-dsi-background/30"><td colSpan={4} className="pl-dsi-indent pr-dsi-pad text-xs opacity-50 italic">No modifiers applied.</td></tr>
                  )}

                  {/* LOADED PREMIUM */}
                  <tr className="border-t-1 border-dsi-outline/50"
                    >
                    <td className="
                      flex gap-dsi-pad 
                      text-sm
                      pt-dsi-pad pb-dsi-pad">
                      <ArrowRightToLine className="icon"/> Loaded Premium
                    </td>
                    <td className="pl-dsi-pad pr-dsi-pad text-center text-xs">-</td>
                    <td className="pl-dsi-pad pr-dsi-pad text-right font-bold">{baseToAnchorDiff.toLocaleString(undefined, { maximumFractionDigits: 0 })}</td>
                    <td className="pl-dsi-pad pr-dsi-pad text-right font-bold">{anchorPremium.toLocaleString(undefined, { maximumFractionDigits: 0 })}</td>
                  </tr>

                </tbody>
              </table>
            </div>
          </div>
        </div>

        <div className="flex flex-col">
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
            <SquareMenu className="icon"/><span className="text-sm">Alternative Limit Options</span>
          </div>

          {/* =======================================================================
              COMPONENT C: LIMIT OPTIONS
              ======================================================================= */}
          <div className="
            flex flex-col flex-1
            border-b-3 border-dsi-contrast-background
            overflow-x-hidden whitespace-nowrap border-collapse
            rounded-b-xl
            bg-dsi-analysis shadow-sm
            pt-2 pb-2">
            <p className="pl-dsi-pad pr-dsi-pad text-sm  mb-4 text-wrap">
              Pre-calculated technical premiums for alternative limit requests based on the current model version.
            </p>
            
            <div className="pl-dsi-pad pr-dsi-pad flex-1 w-full space-y-2">
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
                          <span className="text-sm">{parseInt(limit).toLocaleString(undefined, { maximumFractionDigits: 0 })} Limit</span>
                          {isRecommended && (
                            <span className="text-[10px] uppercase font-bold tracking-wider bg-dsi-selected text-dsi-background px-1.5 py-0.5 rounded">
                              Recommended
                            </span>
                          )}
                        </div>
                        <span className="font-bold">
                          {premium.toLocaleString(undefined, { maximumFractionDigits: 0 })}
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
    </div>
  );
}
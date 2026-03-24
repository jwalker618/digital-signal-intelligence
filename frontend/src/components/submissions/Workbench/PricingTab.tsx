"use client";

import { useState } from "react";
import { useDsiStore } from "@/store/dsiStore";
import {
  Calculator, HandCoins, ChevronDown,
  ChevronRight, ArrowRightToLine, Paperclip,
  SquareMenu, PenLine, WeightTilde, Check
} from "lucide-react";

export default function PricingTab() {
  const { activeSubmission, activeQuote, activeVersion, isSelectingLimit, selectLimitOption } = useDsiStore();

  // Accordion state for the grouped modifiers
  const [expandedGroups, setExpandedGroups] = useState<Record<string, boolean>>({
    categorcial: true,
    signal: true,
    query: true,
    loss: true,
    exposure: true,
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

  // extract modifiers
  const categoricalItems = extractModifiers(activeVersion.modifiers_applied, 'categorical');
  const signalItems = extractModifiers(activeVersion.modifiers_applied, 'signal_condition');
  const directItems = extractModifiers(activeVersion.modifiers_applied,'direct_query');
  const lossItems = extractModifiers(activeVersion.modifiers_applied,'loss_propensity');
  const exposureItems = extractModifiers(activeVersion.modifiers_applied,'exposure');

  // Calculate Group Totals
  const categoricalTotal = categoricalItems.reduce((acc, item) => acc + item.impact, 0);
  const signalTotal = signalItems.reduce((acc, item) => acc + item.impact, 0);
  const directTotal = directItems.reduce((acc, item) => acc + item.impact, 0);
  const lossTotal = lossItems.reduce((acc, item) => acc + item.impact, 0);
  const exposureTotal = exposureItems.reduce((acc, item) => acc + item.impact, 0);

  // =======================================================================
  // KPI CALCULATIONS
  // =======================================================================

  const recommendedPremium = activeQuote?.recommended_premium || 0;
  const recommendedLimit = activeQuote?.recommended_limit || 0;
  const basePremium = activeVersion.base_premium || 0;
  const anchorPremium = activeVersion.premium_after_modifiers || 0;

  const premiumAfterCategorical = basePremium + categoricalTotal;
  const premiumAfterSignal = premiumAfterCategorical + signalTotal;
  const premiumAfterDirect = premiumAfterSignal + directTotal;
  const premiumAfterLoss = premiumAfterDirect + lossTotal;
  const premiumAfterExposure = premiumAfterLoss + exposureTotal;

  // =======================================================================
  // LIMIT OPTIONS (from ROL columns + recommended)
  // =======================================================================

  const limitOptions: { limit: number; premium: number; rol: number; rationale: string; label: string }[] = [];

  if (activeVersion.rol_upper_limit && activeVersion.rol_upper_premium) {
    limitOptions.push({
      limit: activeVersion.rol_upper_limit,
      premium: activeVersion.rol_upper_premium,
      rol: activeVersion.rol_upper_rol || (activeVersion.rol_upper_premium / activeVersion.rol_upper_limit),
      rationale: activeVersion.rol_upper_rationale || '',
      label: 'Upper'
    });
  }

  if (activeVersion.rol_lower_limit && activeVersion.rol_lower_premium) {
    const isDuplicate = limitOptions.some(o => o.limit === activeVersion.rol_lower_limit);
    if (!isDuplicate) {
      limitOptions.push({
        limit: activeVersion.rol_lower_limit,
        premium: activeVersion.rol_lower_premium,
        rol: activeVersion.rol_lower_rol || (activeVersion.rol_lower_premium / activeVersion.rol_lower_limit),
        rationale: activeVersion.rol_lower_rationale || '',
        label: 'Lower'
      });
    }
  }

  if (recommendedLimit && recommendedPremium) {
    const isDuplicate = limitOptions.some(o => o.limit === recommendedLimit);
    if (!isDuplicate) {
      limitOptions.push({
        limit: recommendedLimit,
        premium: recommendedPremium,
        rol: recommendedPremium / recommendedLimit,
        rationale: 'Model recommended option',
        label: 'Recommended'
      });
    }
  }

  // Sort by limit ascending
  limitOptions.sort((a, b) => a.limit - b.limit);

  const handleSelectOption = async (limit: number) => {
    if (!activeQuote?.quote_code || isSelectingLimit) return;
    await selectLimitOption(activeQuote.quote_code, limit);
  };

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
              COMPONENT B: PRICING ANATOMY
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

              {/* BASE PREMIUM */}
              <div className="
                border-b-1 border-dsi-outline/50
                pb-dsi-pad
              "
              >
                <div className="grid grid-cols-[50%_10%_20%_20%] grid-rows-3">

                  {/* row 1 */}
                  <div className="
                    overflow-x-hidden whitespace-nowrap border-collapse
                    flex gap-dsi-pad text-sm"
                    >
                      <ArrowRightToLine className="icon"/> Tier {activeVersion.final_tier} Base Premium using {activeVersion.base_premium_derivation.method} methodology
                  </div>
                  <div className="
                    overflow-x-hidden whitespace-nowrap border-collapse
                    text-xs text-right pr-dsi-pad border-r-1 border-dsi-outline/50"
                    >Basis
                  </div>
                  <div className="
                    overflow-x-hidden whitespace-nowrap border-collapse
                    text-sm text-right uppercase bg-dsi-selected/10 text-dsi-selected"
                    >{activeVersion.base_premium_derivation.basis_field} @
                  </div>
                  <div className="
                    overflow-x-hidden whitespace-nowrap border-collapse
                    pl-dsi-pad pr-dsi-pad text-right text-sm bg-dsi-selected/10 text-dsi-selected"
                    >{activeVersion.base_premium_derivation.basis_value.toLocaleString(undefined, { maximumFractionDigits: 0 })}
                  </div>

                  {/* row 2 */}
                  <div></div>
                  <div className="
                    overflow-x-hidden whitespace-nowrap border-collapse
                    text-xs text-right pr-dsi-pad border-r-1 border-dsi-outline/50"
                    >Rate
                  </div>
                  <div className="
                    overflow-x-hidden whitespace-nowrap border-collapse
                    bg-dsi-selected/10 text-dsi-selected"
                    >
                  </div>
                  <div className="
                    overflow-x-hidden whitespace-nowrap border-collapse
                    pl-dsi-pad pr-dsi-pad text-right text-sm bg-dsi-selected/10 text-dsi-selected"
                    >{activeVersion.base_premium_derivation.rate}x
                  </div>

                  {/* row 3 */}
                  <div></div>
                  <div className="
                    overflow-x-hidden whitespace-nowrap border-collapse
                    text-xs text-right pr-dsi-pad border-r-1 border-dsi-outline/50"
                    >Result
                  </div>
                  <div className="
                    overflow-x-hidden whitespace-nowrap border-collapse
                    bg-dsi-selected/10 text-dsi-selected"
                    >
                  </div>
                  <div className="
                    overflow-x-hidden whitespace-nowrap border-collapse
                    pl-dsi-pad pr-dsi-pad text-right font-bold bg-dsi-selected/10 text-dsi-selected"
                    >{activeVersion.base_premium_derivation.result.toLocaleString(undefined, { maximumFractionDigits: 0 })}
                  </div>
                </div>

              </div>

            {/*ADJUSTMENTS*/}
            <div className="grid grid-cols-[50%_10%_20%_20%] pt-2 pb-2">

              {/* row 1: Table Headers */}
              <div className="
                overflow-x-hidden whitespace-nowrap border-collapse
                flex gap-dsi-pad text-sm pt-2 pb-2"
                >
                  <PenLine className="icon"/> Adjustments
              </div>
              <div className="
                overflow-x-hidden whitespace-nowrap border-collapse
                text-center text-xs pt-2 pb-2"
                >Modifier
              </div>
              <div className="
                overflow-x-hidden whitespace-nowrap border-collapse
                text-right text-xs pt-2 pb-2"
                >Impact
              </div>
              <div className="
                overflow-x-hidden whitespace-nowrap border-collapse
                pl-dsi-pad pr-dsi-pad text-right text-xs pt-2 pb-2"
                >Result
              </div>

              {/* ==============================================
                  CATEGORICAL HEADER
                  ============================================== */}
              <div className="
                overflow-x-hidden whitespace-nowrap border-collapse
                hover:text-dsi-selected cursor-pointer
                border-b border-dsi-outline/10
                flex gap-dsi-pad
                text-sm
                pt-dsi-pad pb-dsi-pad
                "
                onClick={() => toggleGroup('categorical')}
                >
                  {expandedGroups.categorical ? <ChevronDown className="icon" /> : <ChevronRight className="icon" />} Categorical
              </div>
              <div className="
                overflow-x-hidden whitespace-nowrap border-collapse cursor-pointer
                text-xs text-center content-center
                "
                onClick={() => toggleGroup('categorical')}
                >
                  {categoricalItems.length} items
              </div>
              <div className="
                overflow-x-hidden whitespace-nowrap border-collapse cursor-pointer
                border-b border-dsi-outline/10
                text-right font-bold content-center
                "
                onClick={() => toggleGroup('categorical')}
                >
                  {categoricalTotal.toLocaleString(undefined, { maximumFractionDigits: 0 })}
              </div>
              <div className="
                overflow-x-hidden whitespace-nowrap border-collapse cursor-pointer
                border-b border-dsi-outline/10
                pl-dsi-pad pr-dsi-pad text-right text-sm content-center
                "
                onClick={() => toggleGroup('categorical')}
                >
                  {premiumAfterCategorical.toLocaleString(undefined, { maximumFractionDigits: 0 })}
              </div>

              {/* ==============================================
                  GROUP BODY: Categorical Items
                  ============================================== */}
              {expandedGroups.categorical && categoricalItems.map((mod, idx) => (
                <div key={`cat-${idx}`} className="contents">
                  <div className="
                    overflow-x-hidden whitespace-nowrap border-collapse
                    text-xs pl-dsi-padicon pt-1 pb-1 bg-dsi-background/30"
                    title={mod.name}
                    >
                    {mod.name}
                  </div>
                  <div className="
                    overflow-x-hidden whitespace-nowrap border-collapse
                    text-center text-xs content-center bg-dsi-background/30"
                    >
                    {Number(mod.multiplier).toFixed(3)}x
                  </div>
                  <div className="
                    overflow-x-hidden whitespace-nowrap border-collapse
                    text-right text-xs content-center bg-dsi-background/30"
                    >
                    {mod.impact.toLocaleString(undefined, { maximumFractionDigits: 0 })}
                  </div>
                  <div className="
                    overflow-x-hidden whitespace-nowrap border-collapse
                    text-right text-xs content-center bg-dsi-background/30 pr-dsi-pad"
                    >
                    -
                  </div>
                </div>
              ))}

              {expandedGroups.categorical && categoricalItems.length === 0 && (
                <div className="
                  col-span-4 overflow-x-hidden whitespace-nowrap border-collapse
                  text-xs opacity-50 italic pl-dsi-padicon pt-1 pb-1 bg-dsi-background/30"
                  >
                  No modifiers applied.
                </div>
              )}


              {/* ==============================================
                  SIGNAL HEADER
                  ============================================== */}
              <div className="
                overflow-x-hidden whitespace-nowrap border-collapse
                hover:text-dsi-selected cursor-pointer
                border-b border-dsi-outline/10
                flex gap-dsi-pad
                text-sm
                pt-dsi-pad pb-dsi-pad
                "
                onClick={() => toggleGroup('signal')}
                >
                  {expandedGroups.signal ? <ChevronDown className="icon" /> : <ChevronRight className="icon" />} Signal
              </div>
              <div className="
                overflow-x-hidden whitespace-nowrap border-collapse cursor-pointer
                text-xs text-center content-center
                "
                onClick={() => toggleGroup('signal')}
                >
                  {signalItems.length} items
              </div>
              <div className="
                overflow-x-hidden whitespace-nowrap border-collapse cursor-pointer
                border-b border-dsi-outline/10
                text-right font-bold content-center
                "
                onClick={() => toggleGroup('signal')}
                >
                  {signalTotal.toLocaleString(undefined, { maximumFractionDigits: 0 })}
              </div>
              <div className="
                overflow-x-hidden whitespace-nowrap border-collapse cursor-pointer
                border-b border-dsi-outline/10
                pl-dsi-pad pr-dsi-pad text-right text-sm content-center
                "
                onClick={() => toggleGroup('signal')}
                >
                  {premiumAfterSignal.toLocaleString(undefined, { maximumFractionDigits: 0 })}
              </div>

              {/* ==============================================
                  GROUP BODY: Signal Items
                  ============================================== */}
              {expandedGroups.signal && signalItems.map((mod, idx) => (
                <div key={`sig-${idx}`} className="contents">
                  <div className="
                    overflow-x-hidden whitespace-nowrap border-collapse
                    text-xs pl-dsi-padicon pt-1 pb-1 bg-dsi-background/30"
                    title={mod.name}
                    >
                    {mod.name}
                  </div>
                  <div className="
                    overflow-x-hidden whitespace-nowrap border-collapse
                    text-center text-xs content-center bg-dsi-background/30"
                    >
                    {Number(mod.multiplier).toFixed(3)}x
                  </div>
                  <div className="
                    overflow-x-hidden whitespace-nowrap border-collapse
                    text-right text-xs content-center bg-dsi-background/30"
                    >
                    {mod.impact.toLocaleString(undefined, { maximumFractionDigits: 0 })}
                  </div>
                  <div className="
                    overflow-x-hidden whitespace-nowrap border-collapse
                    text-right text-xs content-center bg-dsi-background/30 pr-dsi-pad"
                    >
                    -
                  </div>
                </div>
              ))}

              {expandedGroups.signal && signalItems.length === 0 && (
                <div className="
                  col-span-4 overflow-x-hidden whitespace-nowrap border-collapse
                  text-xs opacity-50 italic pl-dsi-padicon pt-1 pb-1 bg-dsi-background/30"
                  >
                  No modifiers applied.
                </div>
              )}


              {/* ==============================================
                  DIRECT HEADER
                  ============================================== */}
              <div className="
                overflow-x-hidden whitespace-nowrap border-collapse
                hover:text-dsi-selected cursor-pointer
                border-b border-dsi-outline/10
                flex gap-dsi-pad
                text-sm
                pt-dsi-pad pb-dsi-pad
                "
                onClick={() => toggleGroup('direct')}
                >
                  {expandedGroups.direct ? <ChevronDown className="icon" /> : <ChevronRight className="icon" />} Direct Query
              </div>
              <div className="
                overflow-x-hidden whitespace-nowrap border-collapse cursor-pointer
                text-xs text-center content-center
                "
                onClick={() => toggleGroup('direct')}
                >
                  {directItems.length} items
              </div>
              <div className="
                overflow-x-hidden whitespace-nowrap border-collapse cursor-pointer
                border-b border-dsi-outline/10
                text-right font-bold content-center
                "
                onClick={() => toggleGroup('direct')}
                >
                  {directTotal.toLocaleString(undefined, { maximumFractionDigits: 0 })}
              </div>
              <div className="
                overflow-x-hidden whitespace-nowrap border-collapse cursor-pointer
                border-b border-dsi-outline/10
                pl-dsi-pad pr-dsi-pad text-right text-sm content-center
                "
                onClick={() => toggleGroup('direct')}
                >
                  {premiumAfterDirect.toLocaleString(undefined, { maximumFractionDigits: 0 })}
              </div>

              {/* ==============================================
                  GROUP BODY: Direct Items
                  ============================================== */}
              {expandedGroups.direct && directItems.map((mod, idx) => (
                <div key={`dir-${idx}`} className="contents">
                  <div className="
                    overflow-x-hidden whitespace-nowrap border-collapse
                    text-xs pl-dsi-padicon pt-1 pb-1 bg-dsi-background/30"
                    title={mod.name}
                    >
                    {mod.name}
                  </div>
                  <div className="
                    overflow-x-hidden whitespace-nowrap border-collapse
                    text-center text-xs content-center bg-dsi-background/30"
                    >
                    {Number(mod.multiplier).toFixed(3)}x
                  </div>
                  <div className="
                    overflow-x-hidden whitespace-nowrap border-collapse
                    text-right text-xs content-center bg-dsi-background/30"
                    >
                    {mod.impact.toLocaleString(undefined, { maximumFractionDigits: 0 })}
                  </div>
                  <div className="
                    overflow-x-hidden whitespace-nowrap border-collapse
                    text-right text-xs content-center bg-dsi-background/30 pr-dsi-pad"
                    >
                    -
                  </div>
                </div>
              ))}

              {expandedGroups.direct && directItems.length === 0 && (
                <div className="
                  col-span-4 overflow-x-hidden whitespace-nowrap border-collapse
                  text-xs opacity-50 italic pl-dsi-padicon pt-1 pb-1 bg-dsi-background/30"
                  >
                  No modifiers applied.
                </div>
              )}


              {/* ==============================================
                  LOSS HEADER
                  ============================================== */}
              <div className="
                overflow-x-hidden whitespace-nowrap border-collapse
                hover:text-dsi-selected cursor-pointer
                border-b border-dsi-outline/10
                flex gap-dsi-pad
                text-sm
                pt-dsi-pad pb-dsi-pad
                "
                onClick={() => toggleGroup('loss')}
                >
                  {expandedGroups.loss ? <ChevronDown className="icon" /> : <ChevronRight className="icon" />} Loss Analysis
              </div>
              <div className="
                overflow-x-hidden whitespace-nowrap border-collapse cursor-pointer
                text-xs text-center content-center
                "
                onClick={() => toggleGroup('loss')}
                >
                  {lossItems.length} items
              </div>
              <div className="
                overflow-x-hidden whitespace-nowrap border-collapse cursor-pointer
                border-b border-dsi-outline/10
                text-right font-bold content-center
                "
                onClick={() => toggleGroup('loss')}
                >
                  {lossTotal.toLocaleString(undefined, { maximumFractionDigits: 0 })}
              </div>
              <div className="
                overflow-x-hidden whitespace-nowrap border-collapse cursor-pointer
                border-b border-dsi-outline/10
                pl-dsi-pad pr-dsi-pad text-right text-sm content-center
                "
                onClick={() => toggleGroup('loss')}
                >
                  {premiumAfterLoss.toLocaleString(undefined, { maximumFractionDigits: 0 })}
              </div>

              {/* ==============================================
                  GROUP BODY: Loss Items
                  ============================================== */}
              {expandedGroups.loss && lossItems.map((mod, idx) => (
                <div key={`loss-${idx}`} className="contents">
                  <div className="
                    overflow-x-hidden whitespace-nowrap border-collapse
                    text-xs pl-dsi-padicon pt-1 pb-1 bg-dsi-background/30"
                    title={mod.name}
                    >
                    {mod.name}
                  </div>
                  <div className="
                    overflow-x-hidden whitespace-nowrap border-collapse
                    text-center text-xs content-center bg-dsi-background/30"
                    >
                    {Number(mod.multiplier).toFixed(3)}x
                  </div>
                  <div className="
                    overflow-x-hidden whitespace-nowrap border-collapse
                    text-right text-xs content-center bg-dsi-background/30"
                    >
                    {mod.impact.toLocaleString(undefined, { maximumFractionDigits: 0 })}
                  </div>
                  <div className="
                    overflow-x-hidden whitespace-nowrap border-collapse
                    text-right text-xs content-center bg-dsi-background/30 pr-dsi-pad"
                    >
                    -
                  </div>
                </div>
              ))}

              {expandedGroups.loss && lossItems.length === 0 && (
                <div className="
                  col-span-4 overflow-x-hidden whitespace-nowrap border-collapse
                  text-xs opacity-50 italic pl-dsi-padicon pt-1 pb-1 bg-dsi-background/30"
                  >
                  No modifiers applied.
                </div>
              )}

              {/* ==============================================
                  EXPOSURE HEADER
                  ============================================== */}
              <div className="
                overflow-x-hidden whitespace-nowrap border-collapse
                hover:text-dsi-selected cursor-pointer
                flex gap-dsi-pad
                text-sm
                pt-dsi-pad pb-dsi-pad
                "
                onClick={() => toggleGroup('exposure')}
                >
                  {expandedGroups.exposure ? <ChevronDown className="icon" /> : <ChevronRight className="icon" />} Exposure Analysis
              </div>
              <div className="
                overflow-x-hidden whitespace-nowrap border-collapse cursor-pointer
                text-xs text-center content-center
                "
                onClick={() => toggleGroup('exposure')}
                >
                  {exposureItems.length} items
              </div>
              <div className="
                overflow-x-hidden whitespace-nowrap border-collapse cursor-pointer
                text-right font-bold content-center
                "
                onClick={() => toggleGroup('exposure')}
                >
                  {exposureTotal.toLocaleString(undefined, { maximumFractionDigits: 0 })}
              </div>
              <div className="
                overflow-x-hidden whitespace-nowrap border-collapse cursor-pointer
                pl-dsi-pad pr-dsi-pad text-right text-sm content-center
                "
                onClick={() => toggleGroup('exposure')}
                >
                  {premiumAfterExposure.toLocaleString(undefined, { maximumFractionDigits: 0 })}
              </div>

              {/* ==============================================
                  GROUP BODY: Exposure Items
                  ============================================== */}
              {expandedGroups.exposure && exposureItems.map((mod, idx) => (
                <div key={`exp-${idx}`} className="contents">
                  <div className="
                    overflow-x-hidden whitespace-nowrap border-collapse
                    text-xs pl-dsi-padicon pt-1 pb-1 bg-dsi-background/30"
                    title={mod.name}
                    >
                    {mod.name}
                  </div>
                  <div className="
                    overflow-x-hidden whitespace-nowrap border-collapse
                    text-center text-xs content-center bg-dsi-background/30"
                    >
                    {Number(mod.multiplier).toFixed(3)}x
                  </div>
                  <div className="
                    overflow-x-hidden whitespace-nowrap border-collapse
                    text-right text-xs content-center bg-dsi-background/30"
                    >
                    {mod.impact.toLocaleString(undefined, { maximumFractionDigits: 0 })}
                  </div>
                  <div className="
                    overflow-x-hidden whitespace-nowrap border-collapse
                    text-right text-xs content-center bg-dsi-background/30 pr-dsi-pad"
                    >
                    -
                  </div>
                </div>
              ))}

              {expandedGroups.exposure && exposureItems.length === 0 && (
                <div className="
                  col-span-4 overflow-x-hidden whitespace-nowrap border-collapse
                  text-xs opacity-50 italic pl-dsi-padicon pt-1 pb-1 bg-dsi-background/30"
                  >
                  No modifiers applied.
                </div>
              )}

            </div>

              {/* LOADED PREMIUM */}
              <div className="
                border-t-1 border-dsi-outline/50
                pt-dsi-pad pb-dsi-pad
              "
              >
                <div className="grid grid-cols-[50%_10%_20%_20%] grid-rows-3">

                  {/* row 1 */}
                  <div className="
                    overflow-x-hidden whitespace-nowrap border-collapse
                    flex gap-dsi-pad text-sm"
                    >
                      <WeightTilde className="icon"/> Final Premium Calculation
                  </div>
                  <div></div>
                  <div className="
                    overflow-x-hidden whitespace-nowrap border-collapse
                    text-xs text-right pr-dsi-pad border-r-1 border-dsi-outline/50"
                    >Loaded Premium
                  </div>
                  <div className="
                    overflow-x-hidden whitespace-nowrap border-collapse
                    pl-dsi-pad pr-dsi-pad text-right text-sm bg-dsi-selected/10 text-dsi-selected"
                    >{activeVersion.final_premium_detail.premium_before_scaling.toLocaleString(undefined, { maximumFractionDigits: 0 })}
                  </div>

                  {/* row 2 */}
                  <div></div>
                  <div></div>
                  <div className="
                    overflow-x-hidden whitespace-nowrap border-collapse
                    text-xs text-right pr-dsi-pad border-r-1 border-dsi-outline/50"
                    >ILF Factor
                  </div>
                  <div className="
                    overflow-x-hidden whitespace-nowrap border-collapse
                    pl-dsi-pad pr-dsi-pad text-right text-sm bg-dsi-selected/10 text-dsi-selected"
                    >{activeVersion.final_premium_detail.ilf_factor.toFixed(3)}x
                  </div>

                  {/* row 3 */}
                  <div></div>
                  <div></div>
                  <div className="
                    overflow-x-hidden whitespace-nowrap border-collapse
                    text-xs text-right pr-dsi-pad border-r-1 border-dsi-outline/50"
                    >Deductible Factor
                  </div>
                  <div className="
                    overflow-x-hidden whitespace-nowrap border-collapse
                    pl-dsi-pad pr-dsi-pad text-right text-sm bg-dsi-selected/10 text-dsi-selected"
                    >{activeVersion.final_premium_detail.deductible_factor.toFixed(3)}x
                  </div>

                  {/* row 4 */}
                  <div></div>
                  <div></div>
                  <div className="
                    overflow-x-hidden whitespace-nowrap border-collapse
                    text-xs text-right pr-dsi-pad border-r-1 border-dsi-outline/50"
                    >Final Premium
                  </div>
                  <div className="
                    overflow-x-hidden whitespace-nowrap border-collapse
                    pl-dsi-pad pr-dsi-pad text-right font-bold bg-dsi-selected/10 text-dsi-selected"
                    >{activeVersion.final_premium_detail.premium_after_scaling.toLocaleString(undefined, { maximumFractionDigits: 0 })}
                  </div>
                </div>

              </div>



          </div>
        </div>
      </div>

        {/* RIGHT COLUMN: Recommended Quote Details + Limit Options */}
        <div className="flex flex-col gap-2">

          {/* SECTION HEADER: Recommended Quote Details */}
          <div>
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

            {/* RECOMMENDED QUOTE KPIs: Final Premium + Final Limit only */}
            <div className="
              border-b-3 border-dsi-contrast-background
              overflow-x-hidden whitespace-nowrap border-collapse
              rounded-b-xl
              bg-dsi-analysis shadow-sm
              pt-2 pb-2"
              >
              <div className="
                grid grid-cols-2 grid-rows-1
                pl-dsi-pad
                pt-1 pb-1"
                >
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
          </div>

          {/* SECTION HEADER: Limit Options */}
          <div>
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
              <SquareMenu className="icon"/><span className="text-sm">Limit Options</span>
            </div>

            {/* =======================================================================
                COMPONENT C: LIMIT OPTIONS
                ======================================================================= */}
            <div className="
              flex flex-col
              border-b-3 border-dsi-contrast-background
              overflow-x-hidden whitespace-nowrap border-collapse
              rounded-b-xl
              bg-dsi-analysis shadow-sm
              pt-2 pb-2">

              <div className="pl-dsi-pad pr-dsi-pad w-full space-y-2">
                {limitOptions.length > 0 ? (
                  limitOptions.map((option) => {
                    const isCurrentRecommended = recommendedLimit === option.limit;

                    return (
                      <div
                        key={option.limit}
                        className={`p-3 rounded-lg border ${
                          isCurrentRecommended
                            ? 'bg-dsi-selected/10 border-dsi-selected text-dsi-selected'
                            : 'bg-dsi-background/30 border-dsi-outline/10 hover:border-dsi-outline/30'
                        }`}
                      >
                        <div className="flex justify-between items-center">
                          <div className="flex items-center gap-2">
                            <span className="text-sm">{option.limit.toLocaleString(undefined, { maximumFractionDigits: 0 })} Limit</span>
                            {isCurrentRecommended && (
                              <span className="text-[10px] uppercase font-bold tracking-wider bg-dsi-selected text-dsi-background px-1.5 py-0.5 rounded">
                                Current
                              </span>
                            )}
                            {option.label === 'Upper' && !isCurrentRecommended && (
                              <span className="text-[10px] uppercase font-bold tracking-wider bg-dsi-outline/20 px-1.5 py-0.5 rounded">
                                Upper
                              </span>
                            )}
                            {option.label === 'Lower' && !isCurrentRecommended && (
                              <span className="text-[10px] uppercase font-bold tracking-wider bg-dsi-outline/20 px-1.5 py-0.5 rounded">
                                Lower
                              </span>
                            )}
                          </div>
                          <span className="font-bold">
                            {option.premium.toLocaleString(undefined, { maximumFractionDigits: 0 })}
                          </span>
                        </div>

                        <div className="flex justify-between items-center pt-1">
                          <span className="text-xs text-wrap">{option.rationale}</span>
                          <span className="text-xs pl-2">ROL {(option.rol * 100).toFixed(1)}%</span>
                        </div>

                        {!isCurrentRecommended && (
                          <div className="pt-2">
                            <button
                              disabled={isSelectingLimit}
                              onClick={() => handleSelectOption(option.limit)}
                              className="
                                flex items-center gap-1
                                text-xs uppercase font-bold tracking-wider
                                border border-dsi-outline/30 rounded
                                px-2 py-1
                                hover:bg-dsi-selected/10 hover:text-dsi-selected hover:border-dsi-selected
                                disabled:opacity-50 disabled:cursor-not-allowed
                              "
                            >
                              <Check className="w-3 h-3" />
                              {isSelectingLimit ? 'Selecting...' : 'Select Option'}
                            </button>
                          </div>
                        )}
                      </div>
                    );
                  })
                ) : (
                  <div className="flex h-24 items-center justify-center opacity-50 italic text-sm border border-dashed border-dsi-outline/20 rounded-lg">
                    No limit options available.
                  </div>
                )}
              </div>
            </div>
          </div>

        </div>

      </div>
    </div>
  );
}

"use client";

import { useDsiStore } from "@/store/dsiStore";
import {
  formatNumber,
  formatPercent,
  formatCurrency,
  formatText,
} from "@/lib/format";
import { ExpandableGroupTable } from "@/components/base/content/primatives";
import { StandardCard } from "@/components/base/cards";
import KeyDetailsBar from "@/components/base/keyDetailsBar";
import {
  Calculator, HandCoins, ArrowRightToLine,
  ShieldEllipsis, PenLine, WeightTilde, Check, CircleEllipsis,
} from "lucide-react";

export default function PricingTab() {
  const { activeSubmission, activeQuote, activeVersion, isSelectingLimit, selectLimitOption } = useDsiStore();

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
      <KeyDetailsBar
        status={activeQuote?.status}
        validFrom={activeQuote?.valid_from}
        validUntil={activeQuote?.valid_until}
        boundAt={activeQuote?.bound_at}
        policyNumber={activeQuote?.policy_number}
        submissionCode={activeSubmission?.submission_code}
        quoteCode={activeQuote?.quote_code}
      />

      <div className="
        grid grid-cols-1 lg:grid-cols-3
        gap-2
        pt-2 pb-2
        ">

        <StandardCard
          title="Pricing Anatomy"
          lucideIcon={Calculator}
          spanClass="lg:col-span-2"
        >
          <div className="flex-1 overflow-x-auto">

              {/* BASE PREMIUM */}
              <div className="
                border-b-1 border-dsi-outline/50
                pb-dsi-pad
              "
              >
                <div className="grid grid-cols-[50%_10%_20%_20%]">

                  {/* row 1 */}
                  <div className="
                    overflow-x-hidden whitespace-nowrap border-collapse
                    flex gap-dsi-pad text-sm"
                    >
                      <ArrowRightToLine className="icon"/> Tier {activeVersion.final_tier} Base Premium using {activeVersion?.base_premium_derivation?.method || 'N/A'} methodology
                  </div>
                  <div className="
                    overflow-x-hidden whitespace-nowrap border-collapse
                    text-xs text-right pr-dsi-pad border-r-1 border-dsi-outline/50"
                    >Basis
                  </div>
                  <div className="
                    overflow-x-hidden whitespace-nowrap border-collapse
                    text-sm text-right uppercase bg-dsi-selected/10 text-dsi-selected"
                    >{activeVersion?.base_premium_derivation?.basis_field || 'N/A'} @
                  </div>
                  <div className="
                    overflow-x-hidden whitespace-nowrap border-collapse
                    pl-dsi-pad pr-dsi-pad text-right text-sm bg-dsi-selected/10 text-dsi-selected"
                    >{formatCurrency(activeVersion?.base_premium_derivation?.basis_value || 0)}
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
                    >{activeVersion?.base_premium_derivation?.rate || 'N/A'}x
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
                    >{formatCurrency(activeVersion?.base_premium_derivation?.result || 0)}
                  </div>
                </div>

              </div>

            {/* ADJUSTMENTS — ExpandableGroupTable over the 5 modifier sources */}
            <ExpandableGroupTable
              columns={[
                {
                  label: (<><PenLine className="icon" /> Adjustments</>),
                  field: "name",       width: "50%", format: "text", textCase: "capitalize",
                  headeralign: "left",
                },
                { label: "Modifier", field: "multiplier", width: "10%", format: "number",   decimals: 3, align: "center", headeralign: "center" },
                { label: "Impact",   field: "impact",     width: "20%", format: "currency",                       headeralign: "right" },
                { label: "Result",   field: null,         width: "20%", align: "right", headeralign: "right" },
              ]}
              groups={[
                {
                  key: "categorical", title: "Categorical", items: categoricalItems,
                  summary: [
                    `${categoricalItems.length} items`,
                    formatCurrency(categoricalTotal),
                    formatCurrency(premiumAfterCategorical),
                  ],
                  emptyMessage: "No modifiers applied.",
                },
                {
                  key: "signal", title: "Signal", items: signalItems,
                  summary: [
                    `${signalItems.length} items`,
                    formatCurrency(signalTotal),
                    formatCurrency(premiumAfterSignal),
                  ],
                  emptyMessage: "No modifiers applied.",
                },
                {
                  key: "direct", title: "Direct Query", items: directItems,
                  summary: [
                    `${directItems.length} items`,
                    formatCurrency(directTotal),
                    formatCurrency(premiumAfterDirect),
                  ],
                  emptyMessage: "No modifiers applied.",
                },
                {
                  key: "loss", title: "Loss Analysis", items: lossItems,
                  summary: [
                    `${lossItems.length} items`,
                    formatCurrency(lossTotal),
                    formatCurrency(premiumAfterLoss),
                  ],
                  emptyMessage: "No modifiers applied.",
                },
                {
                  key: "exposure", title: "Exposure Analysis", items: exposureItems,
                  summary: [
                    `${exposureItems.length} items`,
                    formatCurrency(exposureTotal),
                    formatCurrency(premiumAfterExposure),
                  ],
                  emptyMessage: "No modifiers applied.",
                },
              ]}
              renderItemCells={(mod: typeof categoricalItems[number]) => [
                formatText(mod.name, "capitalize"),
                `${formatNumber(mod.multiplier, 3)}x`,
                formatCurrency(mod.impact),
                "-",
              ]}
            />

              {/* FINAL PREMIUM CALCULATION */}
              <div className="
                border-t-1 border-dsi-outline/50
                pt-dsi-pad pb-dsi-pad
              "
              >
                <div className="grid grid-cols-[50%_10%_20%_20%]">

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
                    >{formatCurrency(activeVersion?.final_premium_detail?.premium_before_scaling || 0)}
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
                    >{formatNumber(activeVersion?.final_premium_detail?.ilf_factor || 0, 3)}x
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
                    >{formatNumber(activeVersion?.final_premium_detail?.deductible_factor || 0, 3)}x
                  </div>

                  {/* GUARDRAILS */}
                  {activeVersion.guardrail_warnings && activeVersion.guardrail_warnings.length > 0 && (
                    <div className="contents">
                      <div className="pt-2"></div>
                      <div className="pt-2"></div>
                      <div className="pt-2"></div>
                      <div className="pt-2"></div>
                      
                      <div className="border-t-1 border-dsi-outline/50 pt-2"></div>
                      <div className="border-t-1 border-dsi-outline/50 pt-2"></div>
                      <div className="border-t-1 border-dsi-outline/50 pt-2"></div>
                      <div className="border-t-1 border-dsi-outline/50 pt-2"></div>

                      <div className="
                        flex gap-dsi-pad text-sm
                        overflow-x-hidden whitespace-nowrap border-collapse"
                        >
                          <ShieldEllipsis className="icon"/> Guardrails Applied
                      </div>
                      <div></div>
                      <div className="
                        overflow-x-hidden whitespace-nowrap border-collapse
                        text-xs text-right pr-dsi-pad border-r-1 border-dsi-outline/50
                        "
                        >Uncapped Premium *
                      </div>
                      <div className="
                        overflow-x-hidden whitespace-nowrap border-collapse
                        pl-dsi-pad pr-dsi-pad text-right text-sm bg-dsi-selected/10 text-dsi-selected line-through
                        "
                        >{formatCurrency(activeVersion.uncapped_premium)}
                      </div>
                      
                      {activeVersion.guardrail_warnings.map((warning: any, i: number) => (
                        <div key={i} className="col-span-4 text-xs pl-dsi-indent text-wrap italic text-dsi-selected pt-1">
                          * {warning.note}
                        </div>
                      ))}
                      <div className="col-span-4 pb-2"></div>
                    </div>
                  )}

                  {/* Final Premium */}
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
                    >{formatCurrency(activeVersion?.final_premium_detail?.premium_after_scaling || 0)}
                  </div>
                  
                </div>

              </div>

          </div>
        </StandardCard>


        {/* RIGHT COLUMN: Recommended Quote Details + Limit Options (Merged) */}
        <div className="flex flex-col">

          {/* SECTION HEADER: Recommended Quote Details */}
          <div className="dsi-section-header overflow-x-hidden whitespace-nowrap border-collapse"
          >
            <HandCoins className="icon"/><span className="text-sm">Recommended Quote Details</span>
          </div>

          {/* TOP BODY: KPIs (No rounding, no bottom shadow) */}
          <div className="
            flex flex-col
            overflow-x-hidden whitespace-nowrap border-collapse
            bg-dsi-analysis
            "
            >
            {/* RECOMMENDED QUOTE KPIs */}
            <div className="
              grid grid-cols-2 grid-rows-1
              pl-dsi-pad
              pt-2 pb-4"
              >
              <div className="
                bg-dsi-selected/10 border-r-1 border-dsi-outline/50
                overflow-x-hidden whitespace-nowrap border-collapse
                pb-2 pt-1
                text-dsi-selected"
                >
                <div className="mt-1 pl-dsi-pad pr-dsi-pad text-sm text-center underline pb-2">
                  Final Premium
                </div>
                <div className="pl-dsi-pad pr-dsi-pad font-bold text-xl text-right">
                  {formatCurrency(recommendedPremium)}
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
                  {formatCurrency(recommendedLimit)}
                </div>
              </div>
            </div>
          </div>

          {/* INNER SECTION HEADER: Calculated Quote Options (No top rounding) */}
          <div className="
            flex gap-dsi-pad
            border-t-1 border-b-1 border-dsi-outline/50
            overflow-x-hidden whitespace-nowrap border-collapse
            bg-dsi-analysis/60
            pl-dsi-pad
            pt-2 pb-2
          "
          >
            <CircleEllipsis className="icon"/><span className="text-sm">Calculated Quote Options</span>
          </div>

          {/* BOTTOM BODY: Limit Options (Has bottom rounding & flex-1 to stretch) */}
          <div className="
            flex flex-col flex-1
            border-b-3 border-dsi-contrast-background
            overflow-x-hidden whitespace-nowrap border-collapse
            rounded-b-xl
            bg-dsi-analysis shadow-sm
            pt-dsi-pad pb-dsi-pad
            ">

            {/* =======================================================================
                COMPONENT C: LIMIT OPTIONS
                ======================================================================= */}
            <div className="pl-dsi-pad pr-dsi-pad w-full space-y-2">
              {limitOptions.length > 0 ? (
                limitOptions.map((option) => {
                  const isCurrentRecommended = recommendedLimit === option.limit;

                  return (
                    <div
                      key={option.limit}
                      className={`p-dsi-pad rounded-lg border ${
                        isCurrentRecommended
                          ? 'border-dsi-selected text-dsi-selected'
                          : 'border-dsi-outline/10 hover:border-dsi-selected hover:text-dsi-selected'
                      }`}
                    >
                      <div className="flex justify-between items-center">
                        <div className="flex items-center gap-2">


                          {option.label === 'Upper' && !isCurrentRecommended && (
                            <span className="uppercase font-bold">
                              Upper
                            </span>
                          )}
                          {option.label === 'Lower' && !isCurrentRecommended && (
                            <span className="uppercase font-bold">
                              Lower
                            </span>
                          )}

                          <span className="text-sm">{formatCurrency(option.limit)} Limit</span>

                        </div>
                        <span className="font-bold">
                          {formatCurrency(option.premium)}
                        </span>
                      </div>

                      <div className="flex justify-between items-center pt-1">
                        <span className="text-xs text-wrap">{option.rationale}</span>
                        <span className="text-xs pl-2">ROL {formatPercent(option.rol, 1)}</span>
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
  );
}
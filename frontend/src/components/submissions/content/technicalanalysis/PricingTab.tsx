"use client";

import { useDsiStore } from "@/store/dsiStore";
import {
  formatNumber, formatPercent, formatCurrency, formatText,
} from "@/lib/format";
import { ExpandableGroupTable } from "@/components/base/content/primatives";
import { CardGrid, StandardCard } from "@/components/base/cards";
import {
  Calculator, HandCoins, ArrowRightToLine,
  ShieldEllipsis, PenLine, WeightTilde, Check, CircleEllipsis,
} from "lucide-react";

export default function PricingTab() {
  const { activeSubmission, activeQuote, activeVersion, isSelectingLimit, selectLimitOption } = useDsiStore();

  if (!activeSubmission || !activeVersion) {
    return (
      <div className="generate-light-loadingpage">Loading pricing details...</div>
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
    <div className="w-full pb-12 pt-generate-pad">
      <CardGrid cols="grid-cols-1 lg:grid-cols-3" className="gap-2">

        <StandardCard
          title="Pricing Anatomy"
          lucideIcon={Calculator}
          spanClass="lg:col-span-2"
        >
          
          <div className="flex-1">

            <div className="flex text-sm gap-1.5 items-center mb-4"
            >
              <ArrowRightToLine className="generate-app-icon hover:text-generate-text-placeholder"/> 
              Tier 
              <span className="font-bold text-generate-text-input">{activeVersion.final_tier}</span>
              base premium using 
              <span className="font-bold text-generate-text-input">{formatText(activeVersion?.base_premium_derivation?.method || 'N/A',"upper")}</span> 
              methodology
            </div>

              {/* BASE PREMIUM */}
                <div className="grid grid-cols-[60%_10%_15%_15%]">

                  {/* row 1 */}
                  <div className="text-sm pl-generate-pad">Basis</div>
                  <div></div>
                  <div className="font-bold text-right">{formatText(activeVersion?.base_premium_derivation?.basis_field + " @" || '-', "capitalize")}</div>
                  <div className="font-bold text-right">{formatCurrency(activeVersion?.base_premium_derivation?.basis_value || 0)}</div>

                  {/* row 2 */}
                  <div className="text-sm pl-generate-pad">Rate</div>
                  <div className="font-bold text-center">{activeVersion?.base_premium_derivation?.rate + "x" || '-'}</div>
                  <div></div>
                  <div></div>

                  {/* row 3 */}
                  <div className="text-sm pl-generate-pad">Result</div>
                  <div></div>
                  <div></div>
                  <div className="font-bold text-right">{formatCurrency(activeVersion?.base_premium_derivation?.result || 0)}</div>
                </div>

            {/* ADJUSTMENTS — ExpandableGroupTable over the 5 modifier sources */}
            
            <ExpandableGroupTable

              title="Detailed Premium Calculation"
              
              columns={[
                {
                  label: "Type",     field: "name",       width: "60%",  headeralign: "left", align: "left",  },
                { label: "Modifier", field: "multiplier", width: "10%",  headeralign: "center", align: "center",  bold: true  },
                { label: "Impact",   field: "impact",     width: "15%",  headeralign: "center", align: "right", bold: true  },
                { label: "Result",   field: null,         width: "15%",  headeralign: "center", align: "right", bold: true   },
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
                  key: "signal", title: "Signals", items: signalItems,
                  summary: [
                    `${signalItems.length} items`,
                    formatCurrency(signalTotal),
                    formatCurrency(premiumAfterSignal),
                  ],
                  emptyMessage: "No modifiers applied.",
                },
                {
                  key: "direct", title: "Direct Queries", items: directItems,
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
                formatNumber(mod.multiplier, 3) + "x",
                formatCurrency(mod.impact),
                "-",
              ]}
            />

            <div className="flex text-sm gap-1.5 items-center mt-4 mb-4 border-t-1 border-generate-text-outline pt-4">
              <WeightTilde className="generate-app-icon hover:text-generate-text-placeholder"/> 
              <span className="font-bold">Final Premium Calculation</span>
            </div>


              {/* FINAL PREMIUM CALCULATION */}
                <div className="grid grid-cols-[60%_10%_15%_15%]">

                  {/* row 1 */}
                  <div className="text-sm pl-generate-pad">Loaded Premium</div>
                  <div></div>
                  <div></div>
                  <div className="font-bold text-right">
                    {formatCurrency(activeVersion?.final_premium_detail?.premium_before_scaling || 0)}
                  </div>
                  
                  {/* row 2 */}
                  <div className="text-sm pl-generate-pad">ILF Factor</div>
                  
                  <div className="font-bold text-center">{formatNumber(activeVersion?.final_premium_detail?.ilf_factor || 0, 3)}x
                  </div>
                  <div></div>
                  <div></div>

                  {/* row 3 */}
                  <div className="text-sm pl-generate-pad">Deductible Factor</div>
                  <div className="font-bold text-center">{formatNumber(activeVersion?.final_premium_detail?.deductible_factor || 0, 3)}x
                  </div>
                  <div></div>
                  <div></div>

                  {/* Final Premium */}
                  <div className="text-sm pl-generate-pad">Final Premium</div>
                  <div></div>
                  <div></div>
                  <div className="font-bold text-right">
                    {formatCurrency(activeVersion?.final_premium_detail?.premium_after_scaling || 0)}
                  </div>
                  
                </div>

            {/* GUARDRAILS */}
            {activeVersion.guardrail_warnings && activeVersion.guardrail_warnings.length > 0 && (

            <div>

              <div className="flex text-sm gap-1.5 items-center mt-4 mb-4 border-t-1 border-generate-text-outline pt-4">
                <ShieldEllipsis className="generate-app-icon text-generate-text-maybe hover:text-generate-text-maybe"/> 
                <span className="font-bold text-generate-text-maybe">Guardrails</span>
              </div>
              
              <div className="flex justify-between"> 
                <span className="text-sm">Uncapped Premium</span>
                <span className="font-bold text-right">{formatCurrency(activeVersion.uncapped_premium)}</span>
              </div>

              <div className="text-xs mt-2">Rationale</div>

              {activeVersion.guardrail_warnings.map((warning: any, i: number) => (
                <div 
                  key={i} 
                  className="col-span-4"
                  >
                  {warning.note}
                </div>
              ))}
            
            </div>


          )}                

          </div>
        </StandardCard>

        {/* RIGHT COLUMN: Recommended Quote Details + Limit Options */}
        <div className="flex flex-col gap-2 pl-2">

          <StandardCard
            title="Recommended Quote and Calculated Options"
            lucideIcon={CircleEllipsis}
            spanClass="flex-1"
          >

            {/* =======================================================================
                COMPONENT B: LIMIT OPTIONS
                ======================================================================= */}
            <div className="w-full">
              {limitOptions.length > 0 ? (
                limitOptions.map((option) => {
                  const isCurrentRecommended = recommendedLimit === option.limit;

                  return (
                    <div
                      key={option.limit}
                      className={`pt-2 ${
                        isCurrentRecommended? '' : 'border-t-1 border-generate-text-outline'
                      }`}
                    >
                      <div className="justify between">
                        {option.label === 'Upper' && !isCurrentRecommended && (
                          <span className="font-bold mb-2">Upper</span>
                        )}
                        {option.label === 'Lower' && !isCurrentRecommended && (
                          <span className="font-bold mb-2">Lower</span>
                        )}
                      </div>
                      
                      <div className="flex justify-between gap-2">
                        <span className="text-sm">Techncial Limit</span>
                        <span className="font-bold">{formatCurrency(option.limit)}</span>
                      </div>
                      
                      <div className="flex justify-between gap-2">
                        <span className="text-sm">Techncial Premium</span>
                        <span className="font-bold">{formatCurrency(option.premium)}</span>
                      </div>

                      <div className="flex justify-between gap-2">
                        <span className="text-sm">RoL</span>
                        <span className="font-bold">{formatPercent(option.rol, 1)}</span>
                      </div>

                      <div className="flex flex-col mt-4 pt-2 pb-2 border-t-1 border-dashed border-generate-text-outline">
                        <span className="text-xs">Rationale</span>
                        <span className="text-sm text-wrap">{option.rationale}</span>
                      </div>

                      {!isCurrentRecommended && (
                        <div className="w-full right-0">
                          
                          <button
                            disabled={isSelectingLimit}
                            onClick={() => handleSelectOption(option.limit)}
                            className="generate-light-actionbutton w-full"
                          >
                            {isSelectingLimit ? 'Selecting...' : 'Select'}
                          </button>
                        </div>
                      )}

                    </div>
                  );
                })
              ) : (
                <div className="flex">
                  No limit options available.
                </div>
              )}
            </div>
          </StandardCard>

        </div>

      </CardGrid>
    </div>
  );
}
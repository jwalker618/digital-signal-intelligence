"use client";

import { useEffect } from "react";
import { useDsiStore } from "@/store/dsiStore";
import SectionCard from "@/components/shared/SectionCard";
import StickyHeader from "@/components/shared/StickyHeader";
import { Calculator, ArrowDown, Activity, AlertTriangle, DollarSign } from "lucide-react";
import { formatDollar, formatPct } from "@/lib/format";

export default function PremiumAssemblyTab() {
  const { activeSubmission, activeQuote, activeVersion, commercialTerms, isFetchingTerms, fetchCommercialTerms } = useDsiStore();

  useEffect(() => {
    if (activeVersion?.version_code) {
      fetchCommercialTerms(activeVersion.version_code);
    }
  }, [activeVersion?.version_code, fetchCommercialTerms]);

  if (!activeSubmission || !activeVersion) return null;

  if (isFetchingTerms) {
    return (
      <div className="flex flex-col items-center justify-center py-20 opacity-50 space-y-4">
        <Activity className="w-8 h-8 animate-spin" />
        <p className="text-sm tracking-widest uppercase">Loading Premium Assembly...</p>
      </div>
    );
  }

  if (!commercialTerms) {
    return (
      <div className="flex flex-col items-center justify-center py-20 opacity-50 space-y-4">
        <Calculator className="w-12 h-12 opacity-30" />
        <p className="text-sm tracking-widest uppercase">No commercial terms available</p>
      </div>
    );
  }

  const ct = commercialTerms;
  const deductions = ct.deductions || {};
  const taxes = ct.taxes_and_levies || {};

  // Build waterfall steps
  const waterfallSteps = [
    { label: "Technical Premium (USD)", value: ct.technical_premium_usd, type: "start" as const },
    { label: "FX Conversion", value: ct.technical_premium_local, note: `${ct.base_currency} @ ${ct.fx_rate_to_usd?.toFixed(4) || "1.0000"}`, type: "neutral" as const },
  ];

  // Deduction items
  const deductionItems: { label: string; rate: number | null; amount: number | null }[] = [];
  if (deductions.brokerage_rate || deductions.brokerage) {
    deductionItems.push({ label: "Brokerage", rate: deductions.brokerage_rate || deductions.brokerage, amount: deductions.brokerage_amount || null });
  }
  if (deductions.overrider_rate || deductions.overrider) {
    deductionItems.push({ label: "Overrider", rate: deductions.overrider_rate || deductions.overrider, amount: deductions.overrider_amount || null });
  }
  if (deductions.fronting_fee_rate || deductions.fronting_fee) {
    deductionItems.push({ label: "Fronting Fee", rate: deductions.fronting_fee_rate || deductions.fronting_fee, amount: deductions.fronting_fee_amount || null });
  }
  if (deductions.profit_commission_rate || deductions.profit_commission) {
    deductionItems.push({ label: "Profit Commission", rate: deductions.profit_commission_rate || deductions.profit_commission, amount: deductions.profit_commission_amount || null });
  }

  // Tax items
  const taxItems: { label: string; rate: number | null }[] = [];
  if (taxes.insurance_premium_tax_rate) taxItems.push({ label: "Insurance Premium Tax (IPT)", rate: taxes.insurance_premium_tax_rate });
  if (taxes.stamp_duty_rate) taxItems.push({ label: "Stamp Duty", rate: taxes.stamp_duty_rate });
  if (taxes.regulatory_levy_rate) taxItems.push({ label: "Regulatory Levy", rate: taxes.regulatory_levy_rate });
  if (taxes.fire_service_levy_rate) taxItems.push({ label: "Fire Service Levy", rate: taxes.fire_service_levy_rate });

  // Discretion analysis
  const discretionPct = ct.gross_premium && ct.offered_premium
    ? ((ct.offered_premium - ct.gross_premium) / ct.gross_premium)
    : null;

  return (
    <div className="w-full no-scrollbar border-collapse animate-in fade-in duration-500 pb-12 pt-3">
      <StickyHeader
        status={activeQuote?.status}
        validFrom={activeQuote?.valid_from}
        validUntil={activeQuote?.valid_until}
        boundAt={activeQuote?.bound_at}
        policyNumber={activeQuote?.policy_number}
        submissionCode={activeSubmission?.submission_code}
        quoteCode={activeQuote?.quote_code}
      />

      {/* Assembly Waterfall */}
      <SectionCard icon={Calculator} title="Premium Assembly Waterfall">
        <div className="px-dsi-pad py-4">
          <div className="flex flex-col gap-1">
            {/* Technical Premium */}
            <div className="flex justify-between items-center py-3 px-4 rounded-lg bg-dsi-background/30 border border-dsi-outline/10">
              <span className="text-sm font-semibold">Technical Premium (USD)</span>
              <span className="font-bold text-lg">{formatDollar(ct.technical_premium_usd)}</span>
            </div>

            <div className="flex justify-center py-1"><ArrowDown className="w-4 h-4 opacity-30" /></div>

            {/* FX */}
            {ct.base_currency !== "USD" && ct.technical_premium_local && (
              <>
                <div className="flex justify-between items-center py-3 px-4 rounded-lg bg-dsi-background/30 border border-dsi-outline/10">
                  <div>
                    <span className="text-sm font-semibold">Technical Premium ({ct.base_currency})</span>
                    <span className="text-xs opacity-50 block">FX Rate: {ct.fx_rate_to_usd?.toFixed(4)}</span>
                  </div>
                  <span className="font-bold text-lg">{ct.base_currency} {Number(ct.technical_premium_local).toLocaleString()}</span>
                </div>
                <div className="flex justify-center py-1"><ArrowDown className="w-4 h-4 opacity-30" /></div>
              </>
            )}

            {/* Deductions */}
            {deductionItems.length > 0 && (
              <div className="border border-dsi-negative/20 rounded-lg overflow-hidden">
                <div className="bg-dsi-negative/5 px-4 py-2 text-xs font-bold uppercase tracking-wider opacity-60 border-b border-dsi-negative/10">
                  Deductions
                </div>
                {deductionItems.map((item) => (
                  <div key={item.label} className="flex justify-between items-center py-2 px-4 text-sm border-b border-dsi-outline/5 last:border-0">
                    <span className="opacity-70">{item.label}</span>
                    <div className="text-right">
                      <span className="font-bold text-dsi-negative">{item.rate != null ? formatPct(item.rate) : "-"}</span>
                      {item.amount != null && <span className="text-xs opacity-50 block">{formatDollar(item.amount)}</span>}
                    </div>
                  </div>
                ))}
                <div className="flex justify-between items-center py-2 px-4 text-sm bg-dsi-negative/5 font-semibold">
                  <span>Total Commission</span>
                  <span className="font-bold">{formatDollar(ct.total_commission)}</span>
                </div>
              </div>
            )}

            <div className="flex justify-center py-1"><ArrowDown className="w-4 h-4 opacity-30" /></div>

            {/* Net Premium */}
            <div className="flex justify-between items-center py-3 px-4 rounded-lg bg-dsi-info/5 border border-dsi-info/20">
              <span className="text-sm font-bold">Net Premium</span>
              <span className="font-bold text-lg text-dsi-info">{formatDollar(ct.net_premium)}</span>
            </div>

            <div className="flex justify-center py-1"><ArrowDown className="w-4 h-4 opacity-30" /></div>

            {/* Taxes & Levies */}
            {taxItems.length > 0 && (
              <div className="border border-dsi-warning/20 rounded-lg overflow-hidden">
                <div className="bg-dsi-warning/5 px-4 py-2 text-xs font-bold uppercase tracking-wider opacity-60 border-b border-dsi-warning/10">
                  Taxes & Levies
                </div>
                {taxItems.map((item) => (
                  <div key={item.label} className="flex justify-between items-center py-2 px-4 text-sm border-b border-dsi-outline/5 last:border-0">
                    <span className="opacity-70">{item.label}</span>
                    <span className="font-bold">{item.rate != null ? formatPct(item.rate) : "-"}</span>
                  </div>
                ))}
                <div className="flex justify-between items-center py-2 px-4 text-sm bg-dsi-warning/5 font-semibold">
                  <span>Total Taxes</span>
                  <span className="font-bold">{formatDollar(ct.total_taxes)}</span>
                </div>
              </div>
            )}

            <div className="flex justify-center py-1"><ArrowDown className="w-4 h-4 opacity-30" /></div>

            {/* Gross Premium */}
            <div className="flex justify-between items-center py-3 px-4 rounded-lg bg-dsi-positive/5 border border-dsi-positive/20">
              <span className="text-sm font-bold">Gross Premium</span>
              <span className="font-bold text-lg text-dsi-positive">{formatDollar(ct.gross_premium)}</span>
            </div>

            <div className="flex justify-center py-1"><ArrowDown className="w-4 h-4 opacity-30" /></div>

            {/* Offered Premium */}
            <div className="flex justify-between items-center py-4 px-4 rounded-lg bg-dsi-selected/10 border-2 border-dsi-selected/30">
              <div>
                <span className="text-sm font-bold">Offered Premium</span>
                {discretionPct != null && (
                  <span className={`text-xs block ${discretionPct > 0 ? "text-dsi-positive" : discretionPct < 0 ? "text-dsi-negative" : "opacity-50"}`}>
                    {discretionPct > 0 ? "+" : ""}{(discretionPct * 100).toFixed(1)}% discretion from gross
                  </span>
                )}
              </div>
              <span className="font-black text-2xl text-dsi-selected">{formatDollar(ct.offered_premium)}</span>
            </div>
          </div>
        </div>
      </SectionCard>

      {/* Minimum Premium Check */}
      <SectionCard icon={AlertTriangle} title="Minimum Premium Check">
        <div className="px-dsi-pad py-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="border border-dsi-outline/20 rounded-lg p-4">
              <span className="opacity-50 block text-xs mb-1">Minimum Gross Premium</span>
              <span className="font-bold text-lg">{formatDollar(ct.minimum_gross_premium)}</span>
            </div>
            <div className="border border-dsi-outline/20 rounded-lg p-4">
              <span className="opacity-50 block text-xs mb-1">At Minimum Premium?</span>
              <span className={`font-bold text-lg ${ct.at_minimum_premium ? "text-dsi-warning" : "text-dsi-positive"}`}>
                {ct.at_minimum_premium ? "YES — Floor Applied" : "No"}
              </span>
            </div>
            <div className="border border-dsi-outline/20 rounded-lg p-4">
              <span className="opacity-50 block text-xs mb-1">Max Discretion Allowed</span>
              <span className="font-bold text-lg">{ct.offered_premium_discretion != null ? `±${(ct.offered_premium_discretion * 100).toFixed(0)}%` : "N/A"}</span>
            </div>
          </div>
        </div>
      </SectionCard>

      {/* Discretion Analysis */}
      <SectionCard icon={DollarSign} title="Discretion Analysis">
        <div className="px-dsi-pad py-4">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-x-6 gap-y-3 text-sm">
            <div>
              <span className="opacity-50 block text-xs mb-0.5">Gross Premium</span>
              <span className="font-bold">{formatDollar(ct.gross_premium)}</span>
            </div>
            <div>
              <span className="opacity-50 block text-xs mb-0.5">Offered Premium</span>
              <span className="font-bold text-dsi-selected">{formatDollar(ct.offered_premium)}</span>
            </div>
            <div>
              <span className="opacity-50 block text-xs mb-0.5">Discretion Applied</span>
              <span className={`font-bold ${discretionPct != null && discretionPct > 0 ? "text-dsi-positive" : discretionPct != null && discretionPct < 0 ? "text-dsi-negative" : ""}`}>
                {discretionPct != null ? `${discretionPct > 0 ? "+" : ""}${(discretionPct * 100).toFixed(1)}%` : "N/A"}
              </span>
            </div>
            <div>
              <span className="opacity-50 block text-xs mb-0.5">Rationale</span>
              <span className="font-semibold italic">{ct.offered_premium_rationale || "None provided"}</span>
            </div>
          </div>
        </div>
      </SectionCard>
    </div>
  );
}

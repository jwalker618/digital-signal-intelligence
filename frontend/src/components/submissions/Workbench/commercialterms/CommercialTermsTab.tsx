"use client";

import { useEffect } from "react";
import { useDsiStore } from "@/store/dsiStore";
import SectionCard from "@/components/shared/SectionCard";
import StickyHeader from "@/components/shared/StickyHeader";
import { FileText, Building2, DollarSign, ArrowRightLeft, Calendar, Activity } from "lucide-react";
import { formatCurrency, formatPercent, formatNumber, formatDate, formatText } from "@/lib/format";

export default function CommercialTermsTab() {
  const { activeSubmission, activeQuote, activeVersion, activeCommercial } = useDsiStore();

  if (!activeSubmission || !activeVersion) return null;


  const ct = activeCommercial;
  const deductions = ct.deductions || {};
  const taxesAndLevies = ct.taxes_and_levies || {};

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

      {/* Entity Identity */}
      <SectionCard icon={Building2} title="Entity Identity">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-x-6 gap-y-3 px-dsi-pad py-4 text-sm">
          <div>
            <span className="opacity-50 block text-xs mb-0.5">Entity Name</span>
            <span className="font-bold">{ct.entity_name || "N/A"}</span>
          </div>
          <div>
            <span className="opacity-50 block text-xs mb-0.5">Entity ID</span>
            <span className="font-bold">{ct.entity_id || "N/A"}</span>
          </div>
          <div>
            <span className="opacity-50 block text-xs mb-0.5">Market</span>
            <span className="font-bold uppercase">{ct.entity_market || "N/A"}</span>
          </div>
          <div>
            <span className="opacity-50 block text-xs mb-0.5">Base Currency</span>
            <span className="font-bold">{ct.base_currency || "USD"}</span>
          </div>
        </div>
      </SectionCard>

      {/* Premium Waterfall */}
      <SectionCard icon={DollarSign} title="Premium Waterfall">
        <div className="px-dsi-pad py-4">
          <div className="space-y-3">
            {[
              { label: "Technical Premium (USD)", value: formatCurrency(ct.technical_premium_usd) },
              { label: "Technical Premium (Local)", value: ct.technical_premium_local ? `${ct.base_currency || ""} ${formatNumber(ct.technical_premium_local)}` : "-" },
              { label: "Total Commission", value: ct.total_commission != null ? `- ${formatCurrency(ct.total_commission)}` : "-", sub: true },
              { label: "Net Premium", value: formatCurrency(ct.net_premium), highlight: true },
              { label: "Total Taxes & Levies", value: ct.total_taxes != null ? `+ ${formatCurrency(ct.total_taxes)}` : "-", sub: true },
              { label: "Gross Premium", value: formatCurrency(ct.gross_premium), highlight: true },
              { label: "Offered Premium", value: formatCurrency(ct.offered_premium), highlight: true, accent: true },
            ].map((row) => (
              <div
                key={row.label}
                className={`flex justify-between items-center py-2 px-3 rounded text-sm ${
                  row.accent ? "bg-dsi-selected/10 border border-dsi-selected/20" :
                  row.highlight ? "bg-dsi-background/30 font-semibold" :
                  row.sub ? "pl-6 opacity-70" : ""
                }`}
              >
                <span>{row.label}</span>
                <span className={`font-bold ${row.accent ? "text-dsi-selected text-lg" : ""}`}>{row.value}</span>
              </div>
            ))}
          </div>
        </div>
      </SectionCard>

      {/* Commission Structure */}
      <SectionCard icon={FileText} title="Commission Structure">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-x-6 gap-y-3 px-dsi-pad py-4 text-sm">
          <div>
            <span className="opacity-50 block text-xs mb-0.5">Brokerage</span>
            <span className="font-bold">{deductions.brokerage_rate != null ? formatPercent(deductions.brokerage_rate) : formatPercent(deductions.brokerage)}</span>
          </div>
          <div>
            <span className="opacity-50 block text-xs mb-0.5">Overrider</span>
            <span className="font-bold">{deductions.overrider_rate != null ? formatPercent(deductions.overrider_rate) : formatPercent(deductions.overrider)}</span>
          </div>
          <div>
            <span className="opacity-50 block text-xs mb-0.5">Profit Commission</span>
            <span className="font-bold">{deductions.profit_commission_rate != null ? formatPercent(deductions.profit_commission_rate) : formatPercent(deductions.profit_commission)}</span>
          </div>
          <div>
            <span className="opacity-50 block text-xs mb-0.5">Total Commission</span>
            <span className="font-bold">{formatCurrency(ct.total_commission)}</span>
          </div>
        </div>
      </SectionCard>

      {/* FX Context */}
      <SectionCard icon={ArrowRightLeft} title="FX Context">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-x-6 gap-y-3 px-dsi-pad py-4 text-sm">
          <div>
            <span className="opacity-50 block text-xs mb-0.5">Base Currency</span>
            <span className="font-bold">{ct.base_currency || "USD"}</span>
          </div>
          <div>
            <span className="opacity-50 block text-xs mb-0.5">FX Rate to USD</span>
            <span className="font-bold">{ct.fx_rate_to_usd != null ? formatNumber(ct.fx_rate_to_usd, 4) : "1.0000"}</span>
          </div>
          <div>
            <span className="opacity-50 block text-xs mb-0.5">Rate Source</span>
            <span className="font-bold">{ct.fx_rate_source || "N/A"}</span>
          </div>
          <div>
            <span className="opacity-50 block text-xs mb-0.5">Rate Date</span>
            <span className="font-bold">{ct.fx_rate_date ? formatDate(ct.fx_rate_date) : "N/A"}</span>
          </div>
        </div>
      </SectionCard>

      {/* Distribution */}
      <SectionCard icon={FileText} title="Distribution Structure">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-x-6 gap-y-3 px-dsi-pad py-4 text-sm">
          <div>
            <span className="opacity-50 block text-xs mb-0.5">Distribution Type</span>
            <span className="font-bold uppercase">{ct.distribution_type || "N/A"}</span>
          </div>
          <div>
            <span className="opacity-50 block text-xs mb-0.5">Signed Line</span>
            <span className="font-bold">{ct.signed_line != null ? formatPercent(ct.signed_line) : "N/A"}</span>
          </div>
          <div>
            <span className="opacity-50 block text-xs mb-0.5">Role</span>
            <span className="font-bold uppercase">{ct.role || "N/A"}</span>
          </div>
          <div>
            <span className="opacity-50 block text-xs mb-0.5">Lead Loading</span>
            <span className="font-bold">{ct.lead_loading_factor != null ? `${ct.lead_loading_factor}x` : "N/A"}</span>
          </div>
        </div>
      </SectionCard>

      {/* Offered Premium & Discretion */}
      <SectionCard icon={DollarSign} title="Offered Premium">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-x-6 gap-y-3 px-dsi-pad py-4 text-sm">
          <div>
            <span className="opacity-50 block text-xs mb-0.5">Offered Premium</span>
            <span className="font-bold text-dsi-selected text-lg">{formatCurrency(ct.offered_premium)}</span>
          </div>
          <div>
            <span className="opacity-50 block text-xs mb-0.5">Discretion</span>
            <span className="font-bold">{ct.offered_premium_discretion != null ? formatPercent(ct.offered_premium_discretion) : "N/A"}</span>
          </div>
          <div>
            <span className="opacity-50 block text-xs mb-0.5">Minimum Premium</span>
            <span className="font-bold">{formatCurrency(ct.minimum_gross_premium)}</span>
          </div>
          <div>
            <span className="opacity-50 block text-xs mb-0.5">At Minimum?</span>
            <span className={`font-bold ${ct.at_minimum_premium ? "text-dsi-warning" : ""}`}>
              {ct.at_minimum_premium ? "YES" : "No"}
            </span>
          </div>
          {ct.offered_premium_rationale && (
            <div className="col-span-full">
              <span className="opacity-50 block text-xs mb-0.5">Rationale</span>
              <span className="text-sm italic">{ct.offered_premium_rationale}</span>
            </div>
          )}
          {ct.offered_premium_set_at && (
            <div className="col-span-full">
              <span className="opacity-50 block text-xs mb-0.5">Set At</span>
              <span className="font-bold">{formatDate(ct.offered_premium_set_at)}</span>
            </div>
          )}
        </div>
      </SectionCard>

      {/* Written / Earned Period */}
      <SectionCard icon={Calendar} title="Written / Earned Period">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-x-6 gap-y-3 px-dsi-pad py-4 text-sm">
          <div>
            <span className="opacity-50 block text-xs mb-0.5">Written Date</span>
            <span className="font-bold">{ct.written_date ? formatDate(ct.written_date) : "N/A"}</span>
          </div>
          <div>
            <span className="opacity-50 block text-xs mb-0.5">Earned Start</span>
            <span className="font-bold">{ct.earned_start ? formatDate(ct.earned_start) : "N/A"}</span>
          </div>
          <div>
            <span className="opacity-50 block text-xs mb-0.5">Earned End</span>
            <span className="font-bold">{ct.earned_end ? formatDate(ct.earned_end) : "N/A"}</span>
          </div>
          <div>
            <span className="opacity-50 block text-xs mb-0.5">Earned Method</span>
            <span className="font-bold uppercase">{ct.earned_method || "N/A"}</span>
          </div>
        </div>
      </SectionCard>
    </div>
  );
}

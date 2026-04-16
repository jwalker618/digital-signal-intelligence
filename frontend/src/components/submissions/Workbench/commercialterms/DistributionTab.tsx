"use client";

import { useEffect } from "react";
import { useDsiStore } from "@/store/dsiStore";
import SectionCard from "@/components/shared/SectionCard";
import KeyDetailsBar from "@/components/base/keyDetailsBar";
import { Network, Building2, Activity, Users, Layers } from "lucide-react";
import { formatCurrency, formatPercent } from "@/lib/format";

export default function DistributionTab() {
  const { activeSubmission, activeQuote, activeVersion, activeCommercial } = useDsiStore();

  if (!activeSubmission || !activeVersion) return null;

  const ct = activeCommercial;
  const distType = (ct.distribution_type || "DIRECT").toUpperCase();

  const renderDirectContent = () => (
    <div className="px-dsi-pad py-6">
      <div className="flex items-center gap-4 p-6 rounded-xl border-2 border-dsi-positive/20 bg-dsi-positive/5">
        <Building2 className="w-10 h-10 text-dsi-positive" />
        <div>
          <span className="text-lg font-bold block">Direct Writer</span>
          <span className="text-sm opacity-60">100% written by {ct.entity_name || "entity"}</span>
        </div>
      </div>
      <div className="grid grid-cols-2 md:grid-cols-3 gap-x-6 gap-y-3 mt-4 text-sm">
        <div>
          <span className="opacity-50 block text-xs mb-0.5">Entity</span>
          <span className="font-bold">{ct.entity_name}</span>
        </div>
        <div>
          <span className="opacity-50 block text-xs mb-0.5">Market</span>
          <span className="font-bold uppercase">{ct.entity_market || "N/A"}</span>
        </div>
        <div>
          <span className="opacity-50 block text-xs mb-0.5">Gross Premium</span>
          <span className="font-bold">{formatCurrency(ct.gross_premium)}</span>
        </div>
      </div>
    </div>
  );

  const renderSubscriptionContent = () => (
    <div className="px-dsi-pad py-4">
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
        <div className="border border-dsi-outline/20 rounded-lg p-4">
          <span className="opacity-50 block text-xs mb-1">Signed Line</span>
          <span className="font-bold text-2xl text-dsi-selected">{ct.signed_line != null ? formatPercent(ct.signed_line) : "N/A"}</span>
        </div>
        <div className="border border-dsi-outline/20 rounded-lg p-4">
          <span className="opacity-50 block text-xs mb-1">Role</span>
          <span className={`font-bold text-lg uppercase ${ct.role === "LEAD" ? "text-dsi-selected" : ""}`}>{ct.role || "N/A"}</span>
        </div>
        <div className="border border-dsi-outline/20 rounded-lg p-4">
          <span className="opacity-50 block text-xs mb-1">Lead Loading Factor</span>
          <span className="font-bold text-lg">{ct.lead_loading_factor != null ? `${ct.lead_loading_factor}x` : "1.0x"}</span>
        </div>
        <div className="border border-dsi-outline/20 rounded-lg p-4">
          <span className="opacity-50 block text-xs mb-1">Gross Premium</span>
          <span className="font-bold text-lg">{formatCurrency(ct.gross_premium)}</span>
        </div>
      </div>

      {/* Line premium calculation */}
      {ct.signed_line != null && ct.gross_premium != null && (
        <div className="border border-dsi-outline/20 rounded-lg p-4">
          <div className="grid grid-cols-3 gap-4 text-sm">
            <div>
              <span className="opacity-50 block text-xs mb-0.5">Order Premium (100%)</span>
              <span className="font-bold">{formatCurrency(ct.gross_premium)}</span>
            </div>
            <div>
              <span className="opacity-50 block text-xs mb-0.5">Line Premium ({formatPercent(ct.signed_line)})</span>
              <span className="font-bold text-dsi-selected">{formatCurrency(ct.gross_premium * ct.signed_line)}</span>
            </div>
            {ct.role === "LEAD" && ct.lead_loading_factor && ct.lead_loading_factor > 1 && (
              <div>
                <span className="opacity-50 block text-xs mb-0.5">Lead-Loaded Premium</span>
                <span className="font-bold text-dsi-selected">{formatCurrency(ct.gross_premium * ct.signed_line * ct.lead_loading_factor)}</span>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );

  const renderTowerContent = () => (
    <div className="px-dsi-pad py-4">
      <div className="grid grid-cols-2 md:grid-cols-3 gap-4 mb-4">
        <div className="border border-dsi-outline/20 rounded-lg p-4">
          <span className="opacity-50 block text-xs mb-1">Distribution Type</span>
          <span className="font-bold text-lg">Tower (Layered)</span>
        </div>
        <div className="border border-dsi-outline/20 rounded-lg p-4">
          <span className="opacity-50 block text-xs mb-1">Signed Line</span>
          <span className="font-bold text-lg">{ct.signed_line != null ? formatPercent(ct.signed_line) : "N/A"}</span>
        </div>
        <div className="border border-dsi-outline/20 rounded-lg p-4">
          <span className="opacity-50 block text-xs mb-1">Total Gross Premium</span>
          <span className="font-bold text-lg">{formatCurrency(ct.gross_premium)}</span>
        </div>
      </div>
      <div className="border border-dsi-outline/20 rounded-lg p-4 text-sm opacity-60">
        <Layers className="w-5 h-5 inline mr-2" />
        Tower layer details are configured at the entity level. Contact underwriting management for layer structure.
      </div>
    </div>
  );

  const renderBundledContent = () => (
    <div className="px-dsi-pad py-4">
      <div className="grid grid-cols-2 gap-4 mb-4">
        <div className="border border-dsi-outline/20 rounded-lg p-4">
          <span className="opacity-50 block text-xs mb-1">Distribution Type</span>
          <span className="font-bold text-lg">Bundled (Package)</span>
        </div>
        <div className="border border-dsi-outline/20 rounded-lg p-4">
          <span className="opacity-50 block text-xs mb-1">Total Gross Premium</span>
          <span className="font-bold text-lg">{formatCurrency(ct.gross_premium)}</span>
        </div>
      </div>
      <div className="border border-dsi-outline/20 rounded-lg p-4 text-sm opacity-60">
        <Users className="w-5 h-5 inline mr-2" />
        Bundled package details are configured at the entity level. This submission is part of an SME menu package.
      </div>
    </div>
  );

  return (
    <div className="w-full no-scrollbar border-collapse animate-in fade-in duration-500 pb-12 pt-3">
      <KeyDetailsBar
        status={activeQuote?.status}
        validFrom={activeQuote?.valid_from}
        validUntil={activeQuote?.valid_until}
        boundAt={activeQuote?.bound_at}
        policyNumber={activeQuote?.policy_number}
        submissionCode={activeSubmission?.submission_code}
        quoteCode={activeQuote?.quote_code}
      />

      {/* Distribution Type Banner */}
      <SectionCard icon={Network} title={`Distribution — ${distType}`}>
        {distType === "DIRECT" && renderDirectContent()}
        {distType === "SUBSCRIPTION" && renderSubscriptionContent()}
        {distType === "TOWER" && renderTowerContent()}
        {distType === "BUNDLED" && renderBundledContent()}
        {distType === "DECOUPLED" && (
          <div className="px-dsi-pad py-4">
            <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
              <div className="border border-dsi-outline/20 rounded-lg p-4">
                <span className="opacity-50 block text-xs mb-1">Distribution Type</span>
                <span className="font-bold text-lg">Decoupled</span>
              </div>
              <div className="border border-dsi-outline/20 rounded-lg p-4">
                <span className="opacity-50 block text-xs mb-1">Gross Premium</span>
                <span className="font-bold text-lg">{formatCurrency(ct.gross_premium)}</span>
              </div>
              <div className="border border-dsi-outline/20 rounded-lg p-4">
                <span className="opacity-50 block text-xs mb-1">Offered Premium</span>
                <span className="font-bold text-lg text-dsi-selected">{formatCurrency(ct.offered_premium)}</span>
              </div>
            </div>
          </div>
        )}
      </SectionCard>

      {/* Entity Details */}
      <SectionCard icon={Building2} title="Entity Details">
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
    </div>
  );
}

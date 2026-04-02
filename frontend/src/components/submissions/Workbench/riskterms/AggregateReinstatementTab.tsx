"use client";

import { useEffect } from "react";
import { useDsiStore } from "@/store/dsiStore";
import SectionCard from "@/components/shared/SectionCard";
import StickyHeader from "@/components/shared/StickyHeader";
import { RefreshCw, Activity, Layers, DollarSign } from "lucide-react";
import { formatCurrency, formatPercent } from "@/lib/format";

export default function AggregateReinstatementTab() {
  const { activeSubmission, activeQuote, activeVersion, activeRisk } = useDsiStore();

  if (!activeSubmission || !activeVersion) return null;

  const rt = activeRisk;

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

      {/* Aggregate Limits */}
      <SectionCard icon={Layers} title="Aggregate Limits">
        <div className="px-dsi-pad py-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="border-2 border-dsi-selected/20 bg-dsi-selected/5 rounded-xl p-5">
              <span className="opacity-50 block text-xs mb-1 uppercase tracking-wider">Aggregate Limit</span>
              <span className="font-bold text-xl text-dsi-selected">
                {formatCurrency(rt.aggregate_limit)}
              </span>
            </div>
            <div className="border border-dsi-outline/20 rounded-xl p-5">
              <span className="opacity-50 block text-xs mb-1 uppercase tracking-wider">Aggregate Deductible</span>
              <span className="font-bold text-xl">
                {formatCurrency(rt.aggregate_deductible)}
              </span>
            </div>
            <div className="border border-dsi-outline/20 rounded-xl p-5">
              <span className="opacity-50 block text-xs mb-1 uppercase tracking-wider">Aggregate Basis</span>
              <span className="font-bold text-xl capitalize">
                {rt.aggregate_basis?.replace(/_/g, " ") || "N/A"}
              </span>
            </div>
          </div>
        </div>
      </SectionCard>

      {/* Reinstatement Provisions */}
      <SectionCard icon={RefreshCw} title="Reinstatement Provisions">
        <div className="px-dsi-pad py-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className={`border-2 rounded-xl p-5 ${rt.reinstatements ? "border-dsi-info/30 bg-dsi-info/5" : "border-dsi-outline/20"}`}>
              <span className="opacity-50 block text-xs mb-1 uppercase tracking-wider">Reinstatements</span>
              <span className="font-bold text-xl">
                {rt.reinstatements != null ? rt.reinstatements : "N/A"}
              </span>
              {rt.reinstatements != null && rt.reinstatements > 0 && (
                <span className="block text-xs opacity-50 mt-1">
                  {rt.reinstatements === 1 ? "1 reinstatement available" : `${rt.reinstatements} reinstatements available`}
                </span>
              )}
            </div>
            <div className="border border-dsi-outline/20 rounded-xl p-5">
              <span className="opacity-50 block text-xs mb-1 uppercase tracking-wider">Reinstatement Rate</span>
              <span className="font-bold text-xl">
                {rt.reinstatement_rate != null ? formatPercent(rt.reinstatement_rate) : "N/A"}
              </span>
              {rt.reinstatement_rate != null && (
                <span className="block text-xs opacity-50 mt-1">
                  of original premium per reinstatement
                </span>
              )}
            </div>
          </div>
        </div>
      </SectionCard>

      {/* Layer Details (if applicable) */}
      {(rt.attachment_point != null || rt.layer_limit != null) && (
        <SectionCard icon={DollarSign} title="Layer Details">
          <div className="grid grid-cols-2 gap-x-6 gap-y-3 px-dsi-pad py-4 text-sm">
            <div>
              <span className="opacity-50 block text-xs mb-0.5">Attachment Point</span>
              <span className="font-bold">{formatCurrency(rt.attachment_point)}</span>
            </div>
            <div>
              <span className="opacity-50 block text-xs mb-0.5">Layer Limit</span>
              <span className="font-bold">{formatCurrency(rt.layer_limit)}</span>
            </div>
          </div>
        </SectionCard>
      )}
    </div>
  );
}

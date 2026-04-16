"use client";

import { useEffect } from "react";
import { useDsiStore } from "@/store/dsiStore";
import SectionCard from "@/components/shared/SectionCard";
import KeyDetailsBar from "@/components/base/keyDetailsBar";
import { Layers, Activity, DollarSign, Shield } from "lucide-react";
import { formatCurrency } from "@/lib/format";

export default function DeductibleStructureTab() {
  const { activeSubmission, activeQuote, activeVersion, activeRisk } = useDsiStore();

  if (!activeSubmission || !activeVersion) return null;

  const rt = activeRisk;

  const deductibleTypeLabel: Record<string, string> = {
    per_occurrence: "Per Occurrence",
    aggregate: "Aggregate",
    each_and_every: "Each & Every",
  };

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

      {/* Deductible Overview */}
      <SectionCard icon={Layers} title="Deductible Overview">
        <div className="px-dsi-pad py-4">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="border-2 border-dsi-selected/20 bg-dsi-selected/5 rounded-xl p-5">
              <span className="opacity-50 block text-xs mb-1 uppercase tracking-wider">Deductible Type</span>
              <span className="font-bold text-xl text-dsi-selected">
                {deductibleTypeLabel[rt.deductible_type] || rt.deductible_type || "N/A"}
              </span>
            </div>
            <div className="border border-dsi-outline/20 rounded-xl p-5">
              <span className="opacity-50 block text-xs mb-1 uppercase tracking-wider">Deductible Amount</span>
              <span className="font-bold text-xl">{formatCurrency(rt.deductible_amount)}</span>
            </div>
            <div className="border border-dsi-outline/20 rounded-xl p-5">
              <span className="opacity-50 block text-xs mb-1 uppercase tracking-wider">Currency</span>
              <span className="font-bold text-xl">{rt.deductible_currency || "USD"}</span>
            </div>
            <div className="border border-dsi-outline/20 rounded-xl p-5">
              <span className="opacity-50 block text-xs mb-1 uppercase tracking-wider">Basis</span>
              <span className="font-bold text-xl capitalize">{rt.deductible_basis?.replace(/_/g, " ") || "N/A"}</span>
            </div>
          </div>
        </div>
      </SectionCard>

      {/* Attachment & Layer */}
      {(rt.attachment_point != null || rt.layer_limit != null) && (
        <SectionCard icon={Shield} title="Attachment & Layer">
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

      {/* Sub-Limits */}
      {rt.sub_limits && Object.keys(rt.sub_limits).length > 0 && (
        <SectionCard icon={DollarSign} title="Sub-Limits">
          <div className="px-dsi-pad py-4">
            <div className="space-y-2">
              {Object.entries(rt.sub_limits).map(([key, value]) => (
                <div key={key} className="flex justify-between items-center py-2 px-3 rounded bg-dsi-background/20 text-sm">
                  <span className="opacity-70 capitalize">{key.replace(/_/g, " ")}</span>
                  <span className="font-bold">{typeof value === "number" ? formatCurrency(value) : String(value)}</span>
                </div>
              ))}
            </div>
          </div>
        </SectionCard>
      )}
    </div>
  );
}

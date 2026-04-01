"use client";

import { useEffect } from "react";
import { useDsiStore } from "@/store/dsiStore";
import SectionCard from "@/components/shared/SectionCard";
import StickyHeader from "@/components/shared/StickyHeader";
import { Clock, Activity, Shield, DollarSign } from "lucide-react";
import { formatDollar } from "@/lib/format";

export default function SIRWaitingPeriodsTab() {
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

      {/* Self-Insured Retention */}
      <SectionCard icon={Shield} title="Self-Insured Retention (SIR)">
        <div className="px-dsi-pad py-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className={`border-2 rounded-xl p-5 ${rt.sir_applies ? "border-dsi-warning/30 bg-dsi-warning/5" : "border-dsi-outline/20"}`}>
              <span className="opacity-50 block text-xs mb-1 uppercase tracking-wider">SIR Applies</span>
              <span className={`font-bold text-xl ${rt.sir_applies ? "text-dsi-warning" : ""}`}>
                {rt.sir_applies ? "YES" : "No"}
              </span>
            </div>
            <div className="border border-dsi-outline/20 rounded-xl p-5">
              <span className="opacity-50 block text-xs mb-1 uppercase tracking-wider">SIR Amount</span>
              <span className="font-bold text-xl">
                {rt.sir_amount != null ? formatDollar(rt.sir_amount) : "N/A"}
              </span>
            </div>
            <div className="border border-dsi-outline/20 rounded-xl p-5">
              <span className="opacity-50 block text-xs mb-1 uppercase tracking-wider">Deductible Currency</span>
              <span className="font-bold text-xl">{rt.deductible_currency || "USD"}</span>
            </div>
          </div>
        </div>
      </SectionCard>

      {/* Waiting Periods */}
      <SectionCard icon={Clock} title="Waiting Periods">
        <div className="px-dsi-pad py-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className={`border-2 rounded-xl p-5 ${rt.waiting_period_hours ? "border-dsi-info/30 bg-dsi-info/5" : "border-dsi-outline/20"}`}>
              <span className="opacity-50 block text-xs mb-1 uppercase tracking-wider">Waiting Period</span>
              <span className="font-bold text-xl">
                {rt.waiting_period_hours != null ? `${rt.waiting_period_hours} hours` : "None"}
              </span>
              {rt.waiting_period_hours != null && rt.waiting_period_hours > 0 && (
                <span className="block text-xs opacity-50 mt-1">
                  ({(rt.waiting_period_hours / 24).toFixed(1)} days)
                </span>
              )}
            </div>
            <div className="border border-dsi-outline/20 rounded-xl p-5">
              <span className="opacity-50 block text-xs mb-1 uppercase tracking-wider">Waiting Period Type</span>
              <span className="font-bold text-xl capitalize">
                {rt.waiting_period_type?.replace(/_/g, " ") || "N/A"}
              </span>
            </div>
          </div>
        </div>
      </SectionCard>

      {/* Context — applicable coverage parts */}
      <SectionCard icon={DollarSign} title="Context">
        <div className="px-dsi-pad py-4 text-sm">
          <div className="grid grid-cols-2 md:grid-cols-3 gap-x-6 gap-y-3">
            <div>
              <span className="opacity-50 block text-xs mb-0.5">Deductible Type</span>
              <span className="font-bold capitalize">{rt.deductible_type?.replace(/_/g, " ") || "N/A"}</span>
            </div>
            <div>
              <span className="opacity-50 block text-xs mb-0.5">Deductible Amount</span>
              <span className="font-bold">{formatDollar(rt.deductible_amount)}</span>
            </div>
            <div>
              <span className="opacity-50 block text-xs mb-0.5">Deductible Basis</span>
              <span className="font-bold capitalize">{rt.deductible_basis?.replace(/_/g, " ") || "N/A"}</span>
            </div>
          </div>
        </div>
      </SectionCard>
    </div>
  );
}

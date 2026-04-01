"use client";

import { useEffect } from "react";
import { useDsiStore } from "@/store/dsiStore";
import SectionCard from "@/components/shared/SectionCard";
import StickyHeader from "@/components/shared/StickyHeader";
import { FileCheck, Activity, ShieldCheck, ShieldAlert } from "lucide-react";

export default function CoverageTermsTab() {
  const { activeSubmission, activeQuote, activeVersion, activeRisk } = useDsiStore();

  if (!activeSubmission || !activeVersion) return null;

  const rt = activeRisk;
  const coverageTerms = rt.coverage_terms || {};
  const extensions = coverageTerms.extensions || [];
  const exclusions = coverageTerms.exclusions || [];
  const territory = coverageTerms.coverage_territory || coverageTerms.territory;
  const trigger = coverageTerms.coverage_trigger || coverageTerms.trigger;

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

      {/* Coverage Overview */}
      <SectionCard icon={FileCheck} title="Coverage Overview">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-x-6 gap-y-3 px-dsi-pad py-4 text-sm">
          <div>
            <span className="opacity-50 block text-xs mb-0.5">Coverage Territory</span>
            <span className="font-bold capitalize">{territory || "N/A"}</span>
          </div>
          <div>
            <span className="opacity-50 block text-xs mb-0.5">Coverage Trigger</span>
            <span className="font-bold capitalize">{trigger?.replace(/_/g, " ") || "N/A"}</span>
          </div>
          <div>
            <span className="opacity-50 block text-xs mb-0.5">Extensions Count</span>
            <span className="font-bold">{Array.isArray(extensions) ? extensions.length : 0}</span>
          </div>
          <div>
            <span className="opacity-50 block text-xs mb-0.5">Exclusions Count</span>
            <span className="font-bold">{Array.isArray(exclusions) ? exclusions.length : 0}</span>
          </div>
        </div>
      </SectionCard>

      {/* Extensions */}
      <SectionCard icon={ShieldCheck} title={`Extensions (${Array.isArray(extensions) ? extensions.length : 0})`}>
        <div className="px-dsi-pad py-4">
          {Array.isArray(extensions) && extensions.length > 0 ? (
            <div className="space-y-2">
              {extensions.map((ext: any, i: number) => {
                const label = typeof ext === "string" ? ext : ext.name || ext.label || JSON.stringify(ext);
                const description = typeof ext === "object" ? (ext.description || ext.detail) : null;
                return (
                  <div key={i} className="flex items-start gap-3 py-2 px-3 rounded bg-dsi-positive/5 border border-dsi-positive/10 text-sm">
                    <ShieldCheck className="w-4 h-4 text-dsi-positive shrink-0 mt-0.5" />
                    <div>
                      <span className="font-semibold capitalize">{label}</span>
                      {description && <span className="block text-xs opacity-60 mt-0.5">{description}</span>}
                    </div>
                  </div>
                );
              })}
            </div>
          ) : (
            <p className="text-xs opacity-50 italic text-center py-4">No extensions defined</p>
          )}
        </div>
      </SectionCard>

      {/* Exclusions */}
      <SectionCard icon={ShieldAlert} title={`Exclusions (${Array.isArray(exclusions) ? exclusions.length : 0})`}>
        <div className="px-dsi-pad py-4">
          {Array.isArray(exclusions) && exclusions.length > 0 ? (
            <div className="space-y-2">
              {exclusions.map((exc: any, i: number) => {
                const label = typeof exc === "string" ? exc : exc.name || exc.label || JSON.stringify(exc);
                const description = typeof exc === "object" ? (exc.description || exc.detail) : null;
                return (
                  <div key={i} className="flex items-start gap-3 py-2 px-3 rounded bg-dsi-negative/5 border border-dsi-negative/10 text-sm">
                    <ShieldAlert className="w-4 h-4 text-dsi-negative shrink-0 mt-0.5" />
                    <div>
                      <span className="font-semibold capitalize">{label}</span>
                      {description && <span className="block text-xs opacity-60 mt-0.5">{description}</span>}
                    </div>
                  </div>
                );
              })}
            </div>
          ) : (
            <p className="text-xs opacity-50 italic text-center py-4">No exclusions defined</p>
          )}
        </div>
      </SectionCard>

      {/* Additional Coverage Terms */}
      {Object.keys(coverageTerms).filter(k => !["extensions", "exclusions", "coverage_territory", "territory", "coverage_trigger", "trigger"].includes(k)).length > 0 && (
        <SectionCard icon={FileCheck} title="Additional Terms">
          <div className="px-dsi-pad py-4">
            <div className="space-y-2">
              {Object.entries(coverageTerms)
                .filter(([k]) => !["extensions", "exclusions", "coverage_territory", "territory", "coverage_trigger", "trigger"].includes(k))
                .map(([key, value]) => (
                  <div key={key} className="flex justify-between items-center py-2 px-3 rounded bg-dsi-background/20 text-sm">
                    <span className="opacity-70 capitalize">{key.replace(/_/g, " ")}</span>
                    <span className="font-bold">{typeof value === "object" ? JSON.stringify(value) : String(value)}</span>
                  </div>
                ))}
            </div>
          </div>
        </SectionCard>
      )}
    </div>
  );
}

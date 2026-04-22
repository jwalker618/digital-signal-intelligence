"use client";

import { useDsiStore } from "@/store/dsiStore";
import SectionCard from "@/components/shared/SectionCard";
import KeyDetailsBar from "@/components/base/keyDetailsBar";
import { KpiTile, LabelValueList } from "@/components/base/content/primatives";
import { FileCheck, ShieldCheck, ShieldAlert, LucideIcon } from "lucide-react";
import { formatText } from "@/lib/format";

const OVERVIEW_KEYS = new Set([
  "extensions",
  "exclusions",
  "coverage_territory",
  "territory",
  "coverage_trigger",
  "trigger",
]);

interface CoverageItem {
  label: string;
  description?: string | null;
}

const normaliseItem = (raw: unknown): CoverageItem => {
  if (typeof raw === "string") return { label: raw };
  if (raw && typeof raw === "object") {
    const rec = raw as Record<string, unknown>;
    return {
      label: String(rec.name ?? rec.label ?? JSON.stringify(raw)),
      description: (rec.description ?? rec.detail) as string | null | undefined,
    };
  }
  return { label: String(raw) };
};

const CoverageItemList = ({
  items,
  emptyMessage,
  tone,
  icon: Icon,
}: {
  items: unknown[];
  emptyMessage: string;
  tone: "positive" | "negative";
  icon: LucideIcon;
}) => {
  if (items.length === 0) {
    return <p className="text-xs opacity-50 italic text-center py-4">{emptyMessage}</p>;
  }

  const bgClass = tone === "positive" ? "bg-dsi-approve/5 border-dsi-approve/10" : "bg-dsi-negative/5 border-dsi-negative/10";
  const iconClass = tone === "positive" ? "text-dsi-approve" : "text-dsi-negative";

  return (
    <div className="flex flex-col gap-2">
      {items.map((raw, i) => {
        const { label, description } = normaliseItem(raw);
        return (
          <div
            key={i}
            className={`flex items-start gap-3 py-2 px-3 rounded border text-sm ${bgClass}`}
          >
            <Icon className={`w-4 h-4 shrink-0 mt-0.5 ${iconClass}`} />
            <div>
              <span className="font-semibold capitalize">{label}</span>
              {description && <span className="block text-xs opacity-60 mt-0.5">{description}</span>}
            </div>
          </div>
        );
      })}
    </div>
  );
};

export default function CoverageTermsTab() {
  const { activeSubmission, activeQuote, activeVersion, activeRisk } = useDsiStore();

  if (!activeSubmission || !activeVersion) return null;

  const rt = activeRisk;
  const coverageTerms = (rt.coverage_terms ?? {}) as Record<string, unknown>;
  const extensions = Array.isArray(coverageTerms.extensions) ? coverageTerms.extensions : [];
  const exclusions = Array.isArray(coverageTerms.exclusions) ? coverageTerms.exclusions : [];
  const territory = (coverageTerms.coverage_territory ?? coverageTerms.territory) as string | undefined;
  const trigger = (coverageTerms.coverage_trigger ?? coverageTerms.trigger) as string | undefined;
  const additional = Object.entries(coverageTerms).filter(([k]) => !OVERVIEW_KEYS.has(k));

  return (
    <div className="w-full no-scrollbar animate-in fade-in duration-500 pb-12 pt-3">
      <KeyDetailsBar
        status={activeQuote?.status}
        validFrom={activeQuote?.valid_from}
        validUntil={activeQuote?.valid_until}
        boundAt={activeQuote?.bound_at}
        policyNumber={activeQuote?.policy_number}
        submissionCode={activeSubmission?.submission_code}
        quoteCode={activeQuote?.quote_code}
      />

      <SectionCard icon={FileCheck} title="Coverage Overview">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-x-6 gap-y-3 px-dsi-pad py-4">
          <KpiTile label="Coverage Territory" value={formatText(territory, "capitalize", "N/A")} />
          <KpiTile label="Coverage Trigger" value={formatText(trigger, "capitalize", "N/A")} />
          <KpiTile label="Extensions Count" value={extensions.length} />
          <KpiTile label="Exclusions Count" value={exclusions.length} />
        </div>
      </SectionCard>

      <SectionCard icon={ShieldCheck} title={`Extensions (${extensions.length})`}>
        <div className="px-dsi-pad py-4">
          <CoverageItemList
            items={extensions}
            emptyMessage="No extensions defined"
            tone="positive"
            icon={ShieldCheck}
          />
        </div>
      </SectionCard>

      <SectionCard icon={ShieldAlert} title={`Exclusions (${exclusions.length})`}>
        <div className="px-dsi-pad py-4">
          <CoverageItemList
            items={exclusions}
            emptyMessage="No exclusions defined"
            tone="negative"
            icon={ShieldAlert}
          />
        </div>
      </SectionCard>

      {additional.length > 0 && (
        <SectionCard icon={FileCheck} title="Additional Terms">
          <LabelValueList
            className="px-dsi-pad py-4"
            rows={additional.map(([key, value]) => ({
              key,
              label: formatText(key, "capitalize"),
              value: typeof value === "object" ? JSON.stringify(value) : String(value),
            }))}
          />
        </SectionCard>
      )}
    </div>
  );
}

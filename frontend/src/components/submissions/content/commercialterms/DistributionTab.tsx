"use client";

import { useDsiStore } from "@/store/dsiStore";
import SectionCard from "@/components/shared/SectionCard";
import KeyDetailsBar from "@/components/base/keyDetailsBar";
import { KpiTile, MetricCard } from "@/components/base/content/primatives";
import { Network, Building2, Users, Layers } from "lucide-react";
import { formatCurrency, formatPercent, formatText } from "@/lib/format";

export default function DistributionTab() {
  const { activeSubmission, activeQuote, activeVersion, activeCommercial } = useDsiStore();

  if (!activeSubmission || !activeVersion) return null;

  const ct = activeCommercial;
  const distType = (ct.distribution_type || "DIRECT").toUpperCase();

  const renderDirectContent = () => (
    <div className="flex flex-col gap-4 px-generate-pad py-6">
      <div className="flex items-center gap-4 p-6 rounded-xl border-2 border-generate-approve/20 bg-generate-approve/5">
        <Building2 className="w-10 h-10 text-generate-approve" />
        <div>
          <span className="text-lg font-bold block">Direct Writer</span>
          <span className="text-sm opacity-60">100% written by {ct.entity_name || "entity"}</span>
        </div>
      </div>
      <div className="grid grid-cols-2 md:grid-cols-3 gap-x-6 gap-y-3">
        <KpiTile label="Entity" value={ct.entity_name || "N/A"} />
        <KpiTile label="Market" value={formatText(ct.entity_market, "upper", "N/A")} />
        <KpiTile label="Gross Premium" value={formatCurrency(ct.gross_premium)} />
      </div>
    </div>
  );

  const renderSubscriptionContent = () => (
    <div className="flex flex-col gap-4 px-generate-pad py-4">
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <MetricCard
          tone="selected"
          label="Signed Line"
          value={ct.signed_line != null ? formatPercent(ct.signed_line) : "N/A"}
        />
        <MetricCard
          tone={ct.role === "LEAD" ? "selected" : undefined}
          label="Role"
          value={formatText(ct.role, "upper", "N/A")}
        />
        <MetricCard
          label="Lead Loading Factor"
          value={ct.lead_loading_factor != null ? `${ct.lead_loading_factor}x` : "1.0x"}
        />
        <MetricCard label="Gross Premium" value={formatCurrency(ct.gross_premium)} />
      </div>

      {ct.signed_line != null && ct.gross_premium != null && (
        <div className="border border-generate-outline/20 rounded-lg p-4 grid grid-cols-3 gap-4">
          <KpiTile label="Order Premium (100%)" value={formatCurrency(ct.gross_premium)} />
          <div>
            <span className="opacity-50 block text-xs mb-0.5">
              Line Premium ({formatPercent(ct.signed_line)})
            </span>
            <span className="font-bold text-generate-selected">
              {formatCurrency(ct.gross_premium * ct.signed_line)}
            </span>
          </div>
          {ct.role === "LEAD" && ct.lead_loading_factor && ct.lead_loading_factor > 1 && (
            <div>
              <span className="opacity-50 block text-xs mb-0.5">Lead-Loaded Premium</span>
              <span className="font-bold text-generate-selected">
                {formatCurrency(ct.gross_premium * ct.signed_line * ct.lead_loading_factor)}
              </span>
            </div>
          )}
        </div>
      )}
    </div>
  );

  const renderTowerContent = () => (
    <div className="flex flex-col gap-4 px-generate-pad py-4">
      <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
        <MetricCard label="Distribution Type" value="Tower (Layered)" />
        <MetricCard
          label="Signed Line"
          value={ct.signed_line != null ? formatPercent(ct.signed_line) : "N/A"}
        />
        <MetricCard label="Total Gross Premium" value={formatCurrency(ct.gross_premium)} />
      </div>
      <div className="border border-generate-outline/20 rounded-lg p-4 text-sm opacity-60">
        <Layers className="w-5 h-5 inline mr-2" />
        Tower layer details are configured at the entity level. Contact underwriting management for layer structure.
      </div>
    </div>
  );

  const renderBundledContent = () => (
    <div className="flex flex-col gap-4 px-generate-pad py-4">
      <div className="grid grid-cols-2 gap-4">
        <MetricCard label="Distribution Type" value="Bundled (Package)" />
        <MetricCard label="Total Gross Premium" value={formatCurrency(ct.gross_premium)} />
      </div>
      <div className="border border-generate-outline/20 rounded-lg p-4 text-sm opacity-60">
        <Users className="w-5 h-5 inline mr-2" />
        Bundled package details are configured at the entity level. This submission is part of an SME menu package.
      </div>
    </div>
  );

  const renderDecoupledContent = () => (
    <div className="grid grid-cols-2 md:grid-cols-3 gap-4 px-generate-pad py-4">
      <MetricCard label="Distribution Type" value="Decoupled" />
      <MetricCard label="Gross Premium" value={formatCurrency(ct.gross_premium)} />
      <MetricCard tone="selected" label="Offered Premium" value={formatCurrency(ct.offered_premium)} />
    </div>
  );

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

      <SectionCard icon={Network} title={`Distribution — ${distType}`}>
        {distType === "DIRECT" && renderDirectContent()}
        {distType === "SUBSCRIPTION" && renderSubscriptionContent()}
        {distType === "TOWER" && renderTowerContent()}
        {distType === "BUNDLED" && renderBundledContent()}
        {distType === "DECOUPLED" && renderDecoupledContent()}
      </SectionCard>

      <SectionCard icon={Building2} title="Entity Details">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-x-6 gap-y-3 px-generate-pad py-4">
          <KpiTile label="Entity Name" value={ct.entity_name || "N/A"} />
          <KpiTile label="Entity ID" value={ct.entity_id || "N/A"} />
          <KpiTile label="Market" value={formatText(ct.entity_market, "upper", "N/A")} />
          <KpiTile label="Base Currency" value={ct.base_currency || "USD"} />
        </div>
      </SectionCard>
    </div>
  );
}

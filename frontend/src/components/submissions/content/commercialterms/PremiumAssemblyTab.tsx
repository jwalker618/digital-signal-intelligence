"use client";

import { useDsiStore } from "@/store/dsiStore";
import { CardGrid, StandardCard } from "@/components/base/cards";
import { MetricCard, KpiTile } from "@/components/base/content/primatives";
import { Calculator, ArrowDown, AlertTriangle, DollarSign } from "lucide-react";
import { formatCurrency, formatPercent, formatNumber } from "@/lib/format";

interface DeductionItem {
  label: string;
  rate: number | null;
  amount: number | null;
}

interface TaxItem {
  label: string;
  rate: number | null;
}

const WaterfallStep = ({
  label,
  value,
  tone,
  sublabel,
}: {
  label: React.ReactNode;
  value: React.ReactNode;
  tone?: "info" | "positive" | "selected";
  sublabel?: React.ReactNode;
}) => {
  const toneBg =
    tone === "info"     ? "bg-generate-text-comment/5 border-generate-text-comment/20 text-generate-text-comment"
    : tone === "positive" ? "bg-generate-text-good/5 border-generate-text-good/20 text-generate-text-good"
    : tone === "selected" ? "bg-generate-text-input/10 border-2 border-generate-text-input/30 text-generate-text-input"
    : "bg-generate-light-background/30 border-generate-text-outline/10";
  const valueSize = tone === "selected" ? "text-2xl font-black" : "text-lg font-bold";

  return (
    <div className={`flex justify-between items-center py-3 px-4 rounded-lg border ${toneBg}`}>
      <div>
        <span className="text-sm font-semibold">{label}</span>
        {sublabel && <span className="text-xs opacity-50 block">{sublabel}</span>}
      </div>
      <span className={valueSize}>{value}</span>
    </div>
  );
};

const GroupedList = ({
  title,
  tone,
  items,
  totalLabel,
  total,
}: {
  title: string;
  tone: "negative" | "warning";
  items: Array<{ label: string; valueNode: React.ReactNode }>;
  totalLabel: string;
  total: React.ReactNode;
}) => {
  const border = tone === "negative" ? "border-generate-text-bad/20" : "border-generate-text-maybe/20";
  const headerBg = tone === "negative" ? "bg-generate-text-bad/5 border-generate-text-bad/10" : "bg-generate-text-maybe/5 border-generate-text-maybe/10";
  const footerBg = tone === "negative" ? "bg-generate-text-bad/5" : "bg-generate-text-maybe/5";

  return (
    <div className={`border ${border} rounded-lg overflow-hidden`}>
      <div className={`${headerBg} px-4 py-2 text-xs font-bold uppercase tracking-wider opacity-60 border-b`}>
        {title}
      </div>
      {items.map((item) => (
        <div
          key={item.label}
          className="flex justify-between items-center py-2 px-4 text-sm border-b border-generate-text-outline/5 last:border-0"
        >
          <span className="opacity-70">{item.label}</span>
          {item.valueNode}
        </div>
      ))}
      <div className={`flex justify-between items-center py-2 px-4 text-sm ${footerBg} font-semibold`}>
        <span>{totalLabel}</span>
        <span className="font-bold">{total}</span>
      </div>
    </div>
  );
};

const ArrowSpacer = () => (
  <div className="flex justify-center py-1">
    <ArrowDown className="w-4 h-4 opacity-30" />
  </div>
);

export default function PremiumAssemblyTab() {
  const { activeSubmission, activeVersion, activeCommercial } = useDsiStore();

  if (!activeSubmission || !activeVersion) return null;

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const ct = activeCommercial as any;
  const deductions = ct.deductions || {};
  const taxes = ct.taxes_and_levies || {};

  const deductionItems: DeductionItem[] = [];
  if (deductions.brokerage_rate || deductions.brokerage) {
    deductionItems.push({
      label: "Brokerage",
      rate: deductions.brokerage_rate || deductions.brokerage,
      amount: deductions.brokerage_amount || null,
    });
  }
  if (deductions.overrider_rate || deductions.overrider) {
    deductionItems.push({
      label: "Overrider",
      rate: deductions.overrider_rate || deductions.overrider,
      amount: deductions.overrider_amount || null,
    });
  }
  if (deductions.fronting_fee_rate || deductions.fronting_fee) {
    deductionItems.push({
      label: "Fronting Fee",
      rate: deductions.fronting_fee_rate || deductions.fronting_fee,
      amount: deductions.fronting_fee_amount || null,
    });
  }
  if (deductions.profit_commission_rate || deductions.profit_commission) {
    deductionItems.push({
      label: "Profit Commission",
      rate: deductions.profit_commission_rate || deductions.profit_commission,
      amount: deductions.profit_commission_amount || null,
    });
  }

  const taxItems: TaxItem[] = [];
  if (taxes.insurance_premium_tax_rate) taxItems.push({ label: "Insurance Premium Tax (IPT)", rate: taxes.insurance_premium_tax_rate });
  if (taxes.stamp_duty_rate) taxItems.push({ label: "Stamp Duty", rate: taxes.stamp_duty_rate });
  if (taxes.regulatory_levy_rate) taxItems.push({ label: "Regulatory Levy", rate: taxes.regulatory_levy_rate });
  if (taxes.fire_service_levy_rate) taxItems.push({ label: "Fire Service Levy", rate: taxes.fire_service_levy_rate });

  const discretionPct =
    ct.gross_premium && ct.offered_premium
      ? (ct.offered_premium - ct.gross_premium) / ct.gross_premium
      : null;

  const discretionTone =
    discretionPct != null && discretionPct > 0 ? "text-generate-text-good"
    : discretionPct != null && discretionPct < 0 ? "text-generate-text-bad"
    : "";

  return (
    <div className="w-full pb-12 pt-generate-pad">
      <CardGrid cols="grid-cols-1" className="gap-4">

      <StandardCard lucideIcon={Calculator} title="Premium Assembly Waterfall">
        <div className="flex flex-col gap-1 px-generate-pad py-4">
          <WaterfallStep
            label="Technical Premium (USD)"
            value={formatCurrency(ct.technical_premium_usd)}
          />
          <ArrowSpacer />

          {ct.base_currency !== "USD" && ct.technical_premium_local && (
            <>
              <WaterfallStep
                label={`Technical Premium (${ct.base_currency})`}
                sublabel={`FX Rate: ${formatNumber(ct.fx_rate_to_usd, 4)}`}
                value={`${ct.base_currency} ${formatNumber(Number(ct.technical_premium_local))}`}
              />
              <ArrowSpacer />
            </>
          )}

          {deductionItems.length > 0 && (
            <GroupedList
              title="Deductions"
              tone="negative"
              items={deductionItems.map((item) => ({
                label: item.label,
                valueNode: (
                  <div className="text-right">
                    <span className="font-bold text-generate-text-bad">
                      {item.rate != null ? formatPercent(item.rate) : "-"}
                    </span>
                    {item.amount != null && (
                      <span className="text-xs opacity-50 block">{formatCurrency(item.amount)}</span>
                    )}
                  </div>
                ),
              }))}
              totalLabel="Total Commission"
              total={formatCurrency(ct.total_commission)}
            />
          )}

          <ArrowSpacer />
          <WaterfallStep label="Net Premium" tone="info" value={formatCurrency(ct.net_premium)} />
          <ArrowSpacer />

          {taxItems.length > 0 && (
            <GroupedList
              title="Taxes & Levies"
              tone="warning"
              items={taxItems.map((item) => ({
                label: item.label,
                valueNode: (
                  <span className="font-bold">
                    {item.rate != null ? formatPercent(item.rate) : "-"}
                  </span>
                ),
              }))}
              totalLabel="Total Taxes"
              total={formatCurrency(ct.total_taxes)}
            />
          )}

          <ArrowSpacer />
          <WaterfallStep label="Gross Premium" tone="positive" value={formatCurrency(ct.gross_premium)} />
          <ArrowSpacer />
          <WaterfallStep
            label="Offered Premium"
            tone="selected"
            sublabel={
              discretionPct != null && (
                <span className={discretionPct === 0 ? "opacity-50" : discretionTone}>
                  {discretionPct > 0 ? "+" : ""}
                  {formatPercent(discretionPct, 1)} discretion from gross
                </span>
              )
            }
            value={formatCurrency(ct.offered_premium)}
          />
        </div>
      </StandardCard>

      <StandardCard lucideIcon={AlertTriangle} title="Minimum Premium Check">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 px-generate-pad py-4">
          <MetricCard label="Minimum Gross Premium" value={formatCurrency(ct.minimum_gross_premium)} />
          <MetricCard
            tone={ct.at_minimum_premium ? "warning" : "positive"}
            label="At Minimum Premium?"
            value={ct.at_minimum_premium ? "YES — Floor Applied" : "No"}
          />
          <MetricCard
            label="Max Discretion Allowed"
            value={
              ct.offered_premium_discretion != null
                ? `±${formatPercent(ct.offered_premium_discretion, 0)}`
                : "N/A"
            }
          />
        </div>
      </StandardCard>

      <StandardCard lucideIcon={DollarSign} title="Discretion Analysis">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-x-6 gap-y-3 px-generate-pad py-4">
          <KpiTile label="Gross Premium" value={formatCurrency(ct.gross_premium)} />
          <div>
            <span className="flex items-center gap-1 text-sm mb-1">Offered Premium</span>
            <span className="block font-bold text-lg text-generate-text-input">
              {formatCurrency(ct.offered_premium)}
            </span>
          </div>
          <div>
            <span className="flex items-center gap-1 text-sm mb-1">Discretion Applied</span>
            <span className={`block font-bold text-lg ${discretionTone}`}>
              {discretionPct != null
                ? `${discretionPct > 0 ? "+" : ""}${formatPercent(discretionPct, 1)}`
                : "N/A"}
            </span>
          </div>
          <KpiTile label="Rationale" value={ct.offered_premium_rationale || "None provided"} />
        </div>
      </StandardCard>

      </CardGrid>
    </div>
  );
}

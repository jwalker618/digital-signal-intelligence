"use client";

import { useDsiStore } from "@/store/dsiStore";
import { StandardCard } from "@/components/base/cards";
import { KpiTile } from "@/components/base/content/primatives";
import { FileText, Building2, DollarSign, ArrowRightLeft, Calendar } from "lucide-react";
import { formatCurrency, formatPercent, formatNumber, formatDate, formatText } from "@/lib/format";

interface WaterfallRow {
  label: string;
  value: React.ReactNode;
  highlight?: boolean;
  sub?: boolean;
  accent?: boolean;
}

const rowClass = (row: WaterfallRow) => {
  if (row.accent) return "bg-red-100";
  if (row.highlight) return "bg-yellow-100";
  if (row.sub) return "bg-green-100";
  return "";
};

export default function CommercialTermsTab() {
  const { activeSubmission, activeQuote, activeVersion, activeCommercial } = useDsiStore();

  if (!activeSubmission || !activeVersion) return null;

  const ct = activeCommercial;
  const deductions = ct.deductions || {};

  const pickRate = (rate: number | null | undefined, fallback: number | null | undefined) =>
    rate != null ? formatPercent(rate) : formatPercent(fallback);

  const waterfallRows: WaterfallRow[] = [
    { label: "Technical Premium (USD)", value: formatCurrency(ct.technical_premium_usd) },
    {
      label: "Technical Premium (Local)",
      value: ct.technical_premium_local ? `${ct.base_currency || ""} ${formatNumber(ct.technical_premium_local)}` : "-",
    },
    {
      label: "Total Commission",
      value: ct.total_commission != null ? `- ${formatCurrency(ct.total_commission)}` : "-",
      sub: true,
    },
    { label: "Net Premium", value: formatCurrency(ct.net_premium), highlight: true },
    {
      label: "Total Taxes & Levies",
      value: ct.total_taxes != null ? `+ ${formatCurrency(ct.total_taxes)}` : "-",
      sub: true,
    },
    { label: "Gross Premium", value: formatCurrency(ct.gross_premium), highlight: true },
    { label: "Offered Premium", value: formatCurrency(ct.offered_premium), highlight: true, accent: true },
  ];

  return (
    <div className="w-full no-scrollbar pb-12 pt-generate-pad ">

      <StandardCard 
          title="Entity Identity"
          lucideIcon={Building2}
          spanClass="lg:col-span-2 mb-2"
        >
        
        <div className="grid grid-cols-2 md:grid-cols-4">
          <KpiTile label="Entity Name" value={ct.entity_name || "N/A"} />
          <KpiTile label="Entity ID" value={ct.entity_id || "N/A"} />
          <KpiTile label="Market" value={formatText(ct.entity_market, "upper", "N/A")} />
          <KpiTile label="Base Currency" value={ct.base_currency || "USD"} />
        </div>

      </StandardCard>

      <StandardCard 
          title="Premium Waterfall"
          lucideIcon={DollarSign}
          spanClass="lg:col-span-2 mb-2"
        >
        <div className="flex flex-col">
          {waterfallRows.map((row) => (
            <div
              key={row.label}
              className={`flex justify-between items-center ${rowClass(row)}`}
            >
              <span>{row.label}</span>
              <span className={`font-bold ${row.accent ? "" : ""}`}>
                {row.value}
              </span>
            </div>
          ))}
        </div>
      </StandardCard>

      <StandardCard 
          title="Commission Structure"
          lucideIcon={FileText}
          spanClass="lg:col-span-2 mb-2"
        >
        <div className="grid grid-cols-2 md:grid-cols-4">
          <KpiTile label="Brokerage" value={pickRate(deductions.brokerage_rate, deductions.brokerage)} />
          <KpiTile label="Overrider" value={pickRate(deductions.overrider_rate, deductions.overrider)} />
          <KpiTile
            label="Profit Commission"
            value={pickRate(deductions.profit_commission_rate, deductions.profit_commission)}
          />
          <KpiTile label="Total Commission" value={formatCurrency(ct.total_commission)} />
        </div>
      </StandardCard>

      <StandardCard 
          title="FX Context"
          lucideIcon={ArrowRightLeft}
          spanClass="lg:col-span-2 mb-2"
        >
        <div className="grid grid-cols-2 md:grid-cols-4">
          <KpiTile label="Base Currency" value={ct.base_currency || "USD"} />
          <KpiTile
            label="FX Rate to USD"
            value={ct.fx_rate_to_usd != null ? formatNumber(ct.fx_rate_to_usd, 4) : "1.0000"}
          />
          <KpiTile label="Rate Source" value={ct.fx_rate_source || "N/A"} />
          <KpiTile label="Rate Date" value={formatDate(ct.fx_rate_date, "en-GB", "N/A")} />
        </div>
      </StandardCard>

      <StandardCard 
          title="Distribution Structure"
          lucideIcon={FileText}
          spanClass="lg:col-span-2 mb-2"
        >
        <div className="grid grid-cols-2 md:grid-cols-4">
          <KpiTile label="Distribution Type" value={formatText(ct.distribution_type, "upper", "N/A")} />
          <KpiTile
            label="Signed Line"
            value={ct.signed_line != null ? formatPercent(ct.signed_line) : "N/A"}
          />
          <KpiTile label="Role" value={formatText(ct.role, "upper", "N/A")} />
          <KpiTile
            label="Lead Loading"
            value={ct.lead_loading_factor != null ? `${ct.lead_loading_factor}x` : "N/A"}
          />
        </div>
      </StandardCard>

      <StandardCard 
          title="Offered Premium"
          lucideIcon={DollarSign}
          spanClass="lg:col-span-2 mb-2"
        >
        <div className="grid grid-cols-2 md:grid-cols-4">
          <div>
            <span className="block ">Offered Premium</span>
            <span className="font-bold">{formatCurrency(ct.offered_premium)}</span>
          </div>
          <KpiTile
            label="Discretion"
            value={ct.offered_premium_discretion != null ? formatPercent(ct.offered_premium_discretion) : "N/A"}
          />
          <KpiTile label="Minimum Premium" value={formatCurrency(ct.minimum_gross_premium)} />
          <div>
            <span className="">At Minimum?</span>
            <span className={`font-bold ${ct.at_minimum_premium ? "" : ""}`}>
              {ct.at_minimum_premium ? "YES" : "No"}
            </span>
          </div>
          {ct.offered_premium_rationale && (
            <div className="col-span-full">
              <span className="">Rationale</span>
              <span className="">{ct.offered_premium_rationale}</span>
            </div>
          )}
          {ct.offered_premium_set_at && (
            <div className="col-span-full">
              <KpiTile label="Set At" value={formatDate(ct.offered_premium_set_at, "en-GB", "N/A")} />
            </div>
          )}
        </div>
      </StandardCard>

      <StandardCard 
          title="Written / Earned Period"
          lucideIcon={Calendar}
          spanClass="lg:col-span-2 mb-2"
        >
        <div className="grid grid-cols-2 md:grid-cols-4">
          <KpiTile label="Written Date" value={formatDate(ct.written_date, "en-GB", "N/A")} />
          <KpiTile label="Earned Start" value={formatDate(ct.earned_start, "en-GB", "N/A")} />
          <KpiTile label="Earned End" value={formatDate(ct.earned_end, "en-GB", "N/A")} />
          <KpiTile label="Earned Method" value={formatText(ct.earned_method, "upper", "N/A")} />
        </div>
      </StandardCard>
    </div>
  );
}

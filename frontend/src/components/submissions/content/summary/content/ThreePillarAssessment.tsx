"use client";

/**
 * Three-pillar assessment block — Risk / Loss / Exposure, side-by-side.
 *
 * Each pillar is an icon + title, two top metrics, and a contribution
 * calculation table (top-3 + "Other"). The calculation table is
 * ContributionTable; the top metrics use a tiny local Pillar helper
 * specific to this block's layout.
 */

import { LucideIcon, ChartNoAxesGantt, TrendingUpDown, Globe } from "lucide-react";

import { useDsiStore } from "@/store/dsiStore";
import { formatPercent, formatText } from "@/lib/format";
import { getSortedItems, getOtherRow } from "@/lib/utils";

import {
  ContributionTable,
  StandardTableColumn,
  StandardTableRow,
} from "@/components/base/content/primatives";

/* ── Local helper ─────────────────────────────────────────────────────── */

interface PillarMetric {
  label: string;
  value: React.ReactNode;
  /** Value alignment. Default "right". */
  align?: "left" | "right";
}

interface PillarProps {
  title: string;
  icon: LucideIcon;
  titleUnderline?: boolean;
  metrics: PillarMetric[];
  calculationLabel: string;
  columns: StandardTableColumn[];
  rows: StandardTableRow[];
  otherRow?: StandardTableRow;
}

function Pillar({
  title,
  icon: Icon,
  metrics,
  calculationLabel,
  columns,
  rows,
  otherRow,
}: PillarProps) {
  return (
    <div>
      <div className="flex w-full pt-2 pb-2 gap-1.5 border-b-1 border-generate-text-outline font-bold">
        <Icon className="generate-app-icon" />
        <span className="text-sm">{title}</span>
      </div>

      {/* Top metrics — simple two-row list */}
      
      <div className="mt-4">
        {metrics.map((m, i) => (
          
          <div key={i} className="flex w-full justify-between items-center gap-1.5">
            
            <span className="text-sm">{m.label}</span>
            <span
              className={`font-bold ${
                m.align === "left" ? "text-left" : "text-right"
              }`}
            >
              {m.value}
            </span>
          </div>
        ))}
      </div>

      {/* Calculation section label */}
      <div className="text-xs mt-4 font-bold">
        {calculationLabel}
      </div>

      {/* Contribution table */}
      <ContributionTable
        columns={columns}
        rows={rows}
        otherRow={otherRow}
      />
    </div>
  );
}

/* ── Public component ─────────────────────────────────────────────────── */

export default function ThreePillarAssessment() {
  const { activeVersion } = useDsiStore() as any;
  if (!activeVersion) return null;

  const riskGroup = getSortedItems(activeVersion.group_scores, "risk_weight");
  const lossGroup = getSortedItems(
    activeVersion.loss_group_scores,
    "loss_weight",
    "_composite",
  );
  const exposureGroup = getSortedItems(
    activeVersion.exposure_components?.group_scores,
    "exposure_weight",
    "_composite",
  );

  const riskOther = getOtherRow(riskGroup, ["risk_contribution"])[0];
  const lossOther = getOtherRow(lossGroup, [
    "severity_contribution",
    "frequency_contribution",
  ])[0];
  const exposureOther = getOtherRow(exposureGroup, [
    "size_contribution",
    "complexity_contribution",
  ])[0];

  return (
    <div className="grid grid-cols-3 gap-generate-gap">
      <Pillar
        title="Risk Analysis"
        icon={ChartNoAxesGantt}
        calculationLabel="Composite Score Calculation"
        columns={[
          { label: "Group",        field: null,                width: "50%", format: "text",   textCase: "capitalize" },
          { label: "Contribution", field: "risk_contribution", width: "50%", format: "number", decimals: 2 },
        ]}
        rows={riskGroup}
        otherRow={riskOther}
        metrics={[
          { label: "Overall Confidence", value: formatPercent(activeVersion.confidence, 0) },
          {
            label: "Calculation Overridden",
            value: activeVersion.tier_overrides?.length > 0 ? "Yes" : "No",
            align: "left",
          },
        ]}
      />

      <Pillar
        title="Loss Propensity"
        icon={TrendingUpDown}
        calculationLabel="Loss Propensity Calculation"
        columns={[
          { label: "Group",     field: null,                         width: "50%", format: "text",   textCase: "capitalize" },
          { label: "Severity",  field: "severity_contribution",      width: "25%", format: "number", decimals: 2 },
          { label: "Frequency", field: "frequency_contribution",     width: "25%", format: "number", decimals: 2 },
        ]}
        rows={lossGroup}
        otherRow={lossOther}
        metrics={[
          { label: "Loss Confidence", value: formatPercent(activeVersion.loss_confidence, 0) },
          {
            label: "Combined Modifier",
            value: formatPercent(activeVersion.loss_combined_modifier, 0),
          },
        ]}
      />

      <Pillar
        title="Exposure"
        icon={Globe}
        calculationLabel="Exposure Calculation"
        columns={[
          { label: "Group",      field: null,                      width: "50%", format: "text",   textCase: "capitalize" },
          { label: "Size",       field: "size_contribution",       width: "25%", format: "number", decimals: 2 },
          { label: "Complexity", field: "complexity_contribution", width: "25%", format: "number", decimals: 2 },
        ]}
        rows={exposureGroup}
        otherRow={exposureOther}
        metrics={[
          {
            label: "Exposure Band",
            value: formatText(activeVersion.exposure_band_label, "upper"),
            align: "left",
          },
          {
            label: "Combined Modifier",
            value: formatPercent(activeVersion.exposure_modifier, 0),
          },
        ]}
      />
    </div>
  );
}

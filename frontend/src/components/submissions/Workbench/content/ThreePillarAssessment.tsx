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

import ContributionTable, {
  ContributionRow,
} from "@/components/base/contributionTable";

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
  columnHeaders: string[];
  rows: ContributionRow[];
  otherRow?: ContributionRow;
  fields: string[];
}

function Pillar({
  title,
  icon: Icon,
  titleUnderline = false,
  metrics,
  calculationLabel,
  columnHeaders,
  rows,
  otherRow,
  fields,
}: PillarProps) {
  return (
    <div>
      <div className="flex gap-2 ml-dsi-pad pt-1">
        <Icon className="icon" />
        <span className={`text-sm ${titleUnderline ? "underline" : ""}`}>{title}</span>
      </div>

      {/* Top metrics — simple two-row list */}
      <div className="pt-dsi-pad">
        {metrics.map((m, i) => (
          <div key={i} className="flex justify-between">
            <span className="dsi-analysis-description">{m.label}</span>
            <span
              className={`dsi-analysis-item ${
                m.align === "left" ? "text-left" : "text-right"
              }`}
            >
              {m.value}
            </span>
          </div>
        ))}
      </div>

      {/* Calculation section label */}
      <div className="dsi-analysis-description text-xs pt-dsi-pad">
        {calculationLabel}
      </div>

      {/* Contribution table */}
      <ContributionTable
        columnHeaders={columnHeaders}
        rows={rows}
        otherRow={otherRow}
        fields={fields}
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
    <div className="grid grid-cols-3 gap-dsi-gap">
      <Pillar
        title="Risk Analysis"
        icon={ChartNoAxesGantt}
        titleUnderline
        calculationLabel="Composite Score Calculation"
        columnHeaders={["Contribution"]}
        rows={riskGroup}
        otherRow={riskOther}
        fields={["risk_contribution"]}
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
        columnHeaders={["Severity", "Frequency"]}
        rows={lossGroup}
        otherRow={lossOther}
        fields={["severity_contribution", "frequency_contribution"]}
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
        columnHeaders={["Size", "Complexity"]}
        rows={exposureGroup}
        otherRow={exposureOther}
        fields={["size_contribution", "complexity_contribution"]}
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

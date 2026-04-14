"use client";

/**
 * Three-pillar assessment block — Risk / Loss / Exposure, side-by-side.
 *
 * The three pillars share a near-identical layout (top metrics, then a
 * contribution calculation table with a "top-3 + other" pattern), so the body
 * is factored into a local <Pillar /> helper that differs only in column
 * headers and value projection.
 */

import { Fragment } from "react";
import { LucideIcon, ChartNoAxesGantt, TrendingUpDown, Globe } from "lucide-react";

import { useDsiStore } from "@/store/dsiStore";
import { formatNumber, formatPercent, formatText } from "@/lib/format";
import { getSortedItems, getOtherRow } from "@/lib/utils";

/* ── Local helper ─────────────────────────────────────────────────────── */

interface PillarMetric {
  label: string;
  value: React.ReactNode;
  /** text-right on value column (default). Set false for left-align. */
  alignRight?: boolean;
}

interface PillarProps {
  title: string;
  icon: LucideIcon;
  titleUnderline?: boolean;
  metrics: PillarMetric[];
  /** Label above the calculation table (e.g. "Composite Score Calculation"). */
  calculationLabel: string;
  /** Column headers beyond the "Group" column. Length controls grid width. */
  columnHeaders: string[];
  /** Sorted group rows (top-N). */
  rows: Array<{ name?: string | null } & Record<string, unknown>>;
  /** "Other" aggregated row. */
  otherRow?: { name?: string | null } & Record<string, unknown>;
  /** Which numeric fields on each row map to which column. */
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
  // Build grid-template based on number of value columns.
  const valueCols = columnHeaders.length;
  const gridCols =
    valueCols === 1
      ? "grid-cols-[50%_20%]"
      : valueCols === 2
      ? "grid-cols-[50%_20%_20%]"
      : `grid-cols-[50%${"_20%".repeat(valueCols)}]`;

  const allRows = otherRow ? [...rows.slice(0, 3), otherRow] : rows.slice(0, 3);

  return (
    <div>
      <div className="flex gap-2 ml-dsi-pad pt-1">
        <Icon className="icon" />
        <span className={`text-sm ${titleUnderline ? "underline" : ""}`}>{title}</span>
      </div>

      <div className={`grid ${gridCols}`}>
        {/* Top metrics — two rows, each spans all value cols */}
        {metrics.map((m, i) => (
          <Fragment key={`m-${i}`}>
            <div className={`dsi-analysis-description ${i === 0 ? "pt-dsi-pad" : ""}`}>
              {m.label}
            </div>
            <div
              className={`dsi-analysis-item ${i === 0 ? "pt-dsi-pad" : ""} ${
                m.alignRight === false ? "text-left" : "text-right"
              }`}
            >
              {m.value}
            </div>
            {/* Filler cells for multi-column layouts */}
            {Array.from({ length: valueCols - 1 }).map((_, j) => (
              <div key={j} className={i === 0 ? "pt-dsi-pad" : ""} />
            ))}
          </Fragment>
        ))}

        {/* Section label above calculation table */}
        <div className="dsi-analysis-description text-xs pt-dsi-pad">{calculationLabel}</div>
        {Array.from({ length: valueCols }).map((_, j) => (
          <div key={`sec-f-${j}`} className="pt-dsi-pad" />
        ))}

        {/* Column headers */}
        <div className="dsi-analysis-description text-xs border-b-1 border-dsi-outline/50 ml-dsi-pad pl-0 pb-1">
          Group
        </div>
        {columnHeaders.map((h) => (
          <div
            key={`h-${h}`}
            className="dsi-analysis-description pl-0 pr-0 text-xs text-center border-b-1 border-dsi-outline/50 pb-1"
          >
            {h}
          </div>
        ))}

        {/* Rows */}
        {allRows.map((row, idx) => (
          <Fragment key={`r-${idx}`}>
            <div className="dsi-analysis-description text-xs border-r-1 border-dsi-outline/50">
              {formatText(row?.name, "capitalize", "n/a")}
            </div>
            {fields.map((field) => (
              <div key={field} className="dsi-analysis-item text-right">
                {formatNumber(row?.[field] as number | null | undefined, 2)}
              </div>
            ))}
          </Fragment>
        ))}
      </div>
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
          {
            label: "Overall Confidence",
            value: formatPercent(activeVersion.confidence, 0),
          },
          {
            label: "Calculation Overridden",
            value: activeVersion.tier_overrides?.length > 0 ? "Yes" : "No",
            alignRight: false,
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
          {
            label: "Loss Confidence",
            value: formatPercent(activeVersion.loss_confidence, 0),
          },
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
            alignRight: false,
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

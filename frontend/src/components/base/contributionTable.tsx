/**
 * ContributionTable — the "top-3 + other" calculation grid used across the
 * three-pillar assessment (Risk, Loss, Exposure). Layout:
 *
 *   Group     | Col1Header | Col2Header | ...
 *   -----------+------------+------------+----
 *   row1.name | row1[f1]   | row1[f2]   | ...
 *   row2.name | row2[f1]   | row2[f2]   | ...
 *   row3.name | row3[f1]   | row3[f2]   | ...
 *   other     | sum[f1]    | sum[f2]    | ...
 *
 * The "Group" column is fixed at 50% and each value column takes 20%.
 */

import "@/app/globals.css";
import { Fragment } from "react";
import { formatNumber, formatText } from "@/lib/format";

export interface ContributionRow extends Record<string, unknown> {
  name?: string | null;
}

interface ContributionTableProps {
  /** Column headers beyond the "Group" column. Length drives column count. */
  columnHeaders: string[];
  /** Pre-sorted rows; at most the first 3 are rendered. */
  rows: ContributionRow[];
  /** Optional pre-aggregated "Other" row rendered after the top 3. */
  otherRow?: ContributionRow;
  /** Numeric fields to read per row, one per column header. */
  fields: string[];
  /** Decimal places for value formatting. Default 2. */
  decimals?: number;
  className?: string;
}

export default function ContributionTable({
  columnHeaders,
  rows,
  otherRow,
  fields,
  decimals = 2,
  className = "",
}: ContributionTableProps) {
  const valueCols = columnHeaders.length;
  const template = `50% ${"20% ".repeat(valueCols).trim()}`;
  const allRows = otherRow ? [...rows.slice(0, 3), otherRow] : rows.slice(0, 3);

  return (
    <div className={`grid ${className}`} style={{ gridTemplateColumns: template }}>
      {/* Header row */}
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

      {/* Data rows */}
      {allRows.map((row, idx) => (
        <Fragment key={`r-${idx}`}>
          <div className="dsi-analysis-description text-xs border-r-1 border-dsi-outline/50">
            {formatText(row?.name, "capitalize", "n/a")}
          </div>
          {fields.map((field) => (
            <div key={field} className="dsi-analysis-item text-right">
              {formatNumber(row?.[field] as number | null | undefined, decimals)}
            </div>
          ))}
        </Fragment>
      ))}
    </div>
  );
}

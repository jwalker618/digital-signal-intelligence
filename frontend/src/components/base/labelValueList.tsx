/**
 * LabelValueList — the canonical data-presentation primitive.
 *
 * Renders an ordered list of `{ label, value }` rows. Two visual variants:
 *   • "card"  — in-card summary rows (flex justify-between, uses
 *               dsi-analysis-description / dsi-analysis-item utilities).
 *   • "modal" — divided key/value rows inside a modal body (font-mono,
 *               bottom border per row, opacity-60 label).
 *
 * Any content component that just needs to present "this label has this
 * value, repeated N times" should use this — e.g. CommercialSummary,
 * RiskTermsSummary, SubmissionDataList (via KeyValueList).
 */

import "@/app/globals.css";

export type LabelValueVariant = "card" | "modal";

export interface LabelValueRow {
  label: React.ReactNode;
  value: React.ReactNode;
  /** Override the React key. Defaults to the label stringified + index. */
  key?: string;
  /** Extra classes appended to the value `<span>` (e.g. `text-dsi-selected`). */
  valueClassName?: string;
}

interface LabelValueListProps {
  rows: LabelValueRow[];
  variant?: LabelValueVariant;
  emptyMessage?: string;
  /** Extra classes on the outer wrapper. */
  className?: string;
}

const ROW_STYLES: Record<
  LabelValueVariant,
  { wrapper: string; row: string; label: string; value: string }
> = {
  card: {
    wrapper: "",
    row: "flex justify-between",
    label: "dsi-analysis-description",
    value: "dsi-analysis-item",
  },
  modal: {
    wrapper: "space-y-3 font-mono text-sm",
    row: "flex justify-between items-center py-2 border-b border-dsi-outline/5 last:border-0",
    label: "opacity-60",
    value: "font-bold text-right",
  },
};

export default function LabelValueList({
  rows,
  variant = "card",
  emptyMessage = "No data available.",
  className = "",
}: LabelValueListProps) {
  if (rows.length === 0) {
    return <p className="dsi-user-message">{emptyMessage}</p>;
  }

  const s = ROW_STYLES[variant];

  return (
    <div className={`${s.wrapper} ${className}`}>
      {rows.map((r, i) => (
        <div key={r.key ?? `${String(r.label)}-${i}`} className={s.row}>
          <span className={s.label}>{r.label}</span>
          <span className={`${s.value} ${r.valueClassName ?? ""}`}>{r.value}</span>
        </div>
      ))}
    </div>
  );
}

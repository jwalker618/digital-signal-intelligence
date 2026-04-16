"use client";

import "@/app/globals.css";
import { Fragment, useState } from "react";
import { formatNumber, formatText } from "@/lib/format";

import {
  StatusPaletteEntry,
  TONE_PALETTE,
  getStatusStyle,
} from "@/lib/statusPalette";

import { 
    LucideIcon, ChevronDown, ChevronRight 
} from "lucide-react";

export type LabelValueVariant = "card" | "modal";
export type KpiVariant = "default" | "emphasis";
export type StatusTone = keyof typeof TONE_PALETTE;

export type Align = "left" | "center" | "right";

const TEXTALIGN_CLASS: Record<Align, string> = {
  left: "text-left", center: "text-center", right: "text-right",
};

const DEFAULT_THRESHOLDS: ScoreBarThreshold[] = [
  { at: 40, color: "var(--dsi-positive)" },
  { at: 70, color: "var(--dsi-warning)" },
  { at: Infinity, color: "var(--dsi-negative)" },
];

export type Padding = "sm" | "md" | "lg";

const PADDING_CLASS: Record<NonNullable<InfoPanelProps["padding"]>, string> = {
  sm: "p-2", md: "p-3", lg: "p-4",
};

/** Build a CSS grid-template-columns track list from column widths.
 *  Missing widths fall back to "1fr" so omitting width gives equal columns.
 *  Tolerates null/undefined for defensive rendering during loading states. */
const buildGridTemplate = (columns: StandardTableColumn[] | null | undefined): string =>
  (columns ?? []).map((c) => c.width ?? "1fr").join(" ");

/** COMMON INTERFACES ---------------------------------------------------------------------------------------------- */

/** GUIDANCE
 * width: CSS grid track value, e.g. `"50%"`, `"1fr"`, `"auto"`. Default `"1fr"`.
 * align: Horizontal alignment for this column's rows. Default `"right"`.
 * headeralign: Horizontal alignment for this column's header cell. Default to "center"`.
 */
export interface StandardTableColumn {
  label?: React.ReactNode;
  field?: string | null;
  width?: string;
  align: Align | "right";
  headeralign: Align | "center";
}

export interface StandardTableRow extends Record<string, unknown> {
  name?: string | null;
}

/** CONTRIBUTION TABLE ---------------------------------------------------------------------------------------------- */

/** GUIDANCE
 * columns: Column definitions. A column without `field` is treated as a
 *          NAME column and renders `row.name` (formatted text, left default,
 *          border-r). A column with `field` renders `row[field]` as a
 *          numeric cell (right default, no border).
 * rows: Pre-sorted rows; at most the first 3 are rendered.
 * otherRow: Optional pre-aggregated "Other" row rendered after the top 3.
 * decimals: Decimal places for value formatting. Default 2.
 */
interface ContributionTableProps {
  columns: StandardTableColumn[];
  rows: StandardTableRow[];
  otherRow?: StandardTableRow;
  decimals?: number;
  className?: string;
}

/**
 *   Col0Header | Col1Header | Col2Header | ...
 *   -----------+------------+------------+----
 *   row1.name  | row1[f1]   | row1[f2]   | ...
 *   other      | sum[f1]    | sum[f2]    | ...
 */
export const ContributionTable = ({
  columns = [],
  rows = [],
  otherRow,
  decimals = 2,
  className = "",
}: ContributionTableProps) => {

  const template = buildGridTemplate(columns);
  const allRows = otherRow ? [...rows.slice(0, 3), otherRow] : rows.slice(0, 3);

  return (

    <div className={`grid ${className}`} style={{ gridTemplateColumns: template }}>

      {/* Headers */}
      {columns.map((c, i) => (
        <div
          key={`h-${i}`}
          className={`
            dsi-analysis-description
            text-xs 
            ${TEXTALIGN_CLASS[c.headeralign]}  
            border-b-1 border-dsi-outline/50
            pb-1`}
        >
          {c.label}
        </div>
      ))}

      {/* Data rows */}
      {allRows.map((row, idx) => (
        <Fragment key={`r-${idx}`}>
          
          {columns.map((c, i) => {
            const isName = !c.field;
            return (
              <div
                key={`v-${idx}-${i}`}
                className={
                  isName
                    ? `dsi-analysis-description ${TEXTALIGN_CLASS[c.headeralign]} border-r-1 border-dsi-outline/50 pt-1 pb-1`
                    : `dsi-analysis-item ${TEXTALIGN_CLASS[c.align]} pt-1 pb-1`
                }
              >
                {isName
                  ? formatText(row?.name, "capitalize", "n/a")
                  : formatNumber(row?.[c.field!] as number | null | undefined, decimals)}
              </div>
            );
          })}
        </Fragment>
      ))}
    </div>
  );
}

/** EXPANDABLE GROUP TABLE ---------------------------------------------------------------------------------------------- */

/** GUIDANCE
 * emptyMessage: Shown when the group is expanded and `items` is empty.
 */
export interface ExpandableGroup<T> {
  key: string;
  title: React.ReactNode;
  items: T[];
  summary: React.ReactNode[];
  emptyMessage?: React.ReactNode;
}

/** GUIDANCE
 * expanded: Controlled expansion map — if provided, `onToggle` is required
 * defaultExpanded: Uncontrolled initial expansion map
 * showColumnHeaders: Render the column header row. Default true if any column has a label
 * defaultEmptyMessage: Default empty-state text.
 */
export interface ExpandableGroupTableProps<T> {
  columns: StandardTableColumn[];
  groups: ExpandableGroup<T>[];
  renderItemCells: (item: T, index: number, group: ExpandableGroup<T>) => React.ReactNode[];
  expanded?: Record<string, boolean>;
  onToggle?: (key: string) => void;
  defaultExpanded?: Record<string, boolean>;
  showColumnHeaders?: boolean;
  defaultEmptyMessage?: React.ReactNode;
  className?: string;
}

/**
 * Structure:
 *   ┌────────────────────────────────────────────────────────────┐
 *   │ <col1.label>   <col2.label>   <col3.label>   <col4.label>  │  (optional column headers)
 *   ├────────────────────────────────────────────────────────────┤
 *   │ ▸ Group A      <summary 1>    <summary 2>    <summary 3>   │  (clickable group header)
 *   │   item 1.a     item-cell      item-cell      item-cell     │  (rendered if expanded)
 *   │   item 1.b     item-cell      item-cell      item-cell     │
 *   │ ▸ Group B      <summary 1>    <summary 2>    <summary 3>   │
 *   │   (no items)                                               │
 *   └────────────────────────────────────────────────────────────┘
 *
 * The first column is always the group title / item name column. Column
 * widths and alignments are declared once; the component derives both
 * header-cell and item-cell styling from them.
 *
 * Example (PricingTab usage):
 *
 *   <ExpandableGroupTable
 *     columns={[
 *       { label: "Adjustments", width: "50%", align: "left", headeralign: "left" },
 *       { label: "Modifier",    width: "10%", align: "center", headeralign: "center" },
 *       { label: "Impact",      width: "20%", align: "right", headeralign: "center" },
 *       { label: "Result",      width: "20%", align: "right", headeralign: "center" },
 *     ]}
 *     groups={[
 *       { key: "categorical", title: "Categorical",
 *         items: categoricalItems,
 *         summary: [`${categoricalItems.length} items`,
 *                   formatCurrency(categoricalTotal),
 *                   formatCurrency(premiumAfterCategorical)] },
 *       // …
 *     ]}
 *     renderItemCells={(mod) => [
 *       mod.name,
 *       `${formatNumber(mod.multiplier, 3)}x`,
 *       formatCurrency(mod.impact),
 *       "-",
 *     ]}
 *   />
 */
export const ExpandableGroupTable = <T,>({
  columns,
  groups,
  renderItemCells,
  expanded: controlledExpanded,
  onToggle,
  defaultExpanded = {},
  showColumnHeaders,
  defaultEmptyMessage = "No items.",
  className = "",
}: ExpandableGroupTableProps<T>) => {
  const [internalExpanded, setInternalExpanded] =
    useState<Record<string, boolean>>(defaultExpanded);

  const isControlled = controlledExpanded !== undefined;
  const expanded = isControlled ? controlledExpanded! : internalExpanded;

  const toggle = (key: string) => {
    if (isControlled) {
      onToggle?.(key);
    } else {
      setInternalExpanded((p) => ({ ...p, [key]: !p[key] }));
    }
  };

  const renderHeaders = showColumnHeaders ?? columns.some((c) => c.label !== undefined);
  const template = buildGridTemplate(columns);
  const lastIdx = columns.length - 1;

  return (
    <div
      className={`grid ${className}`}
      style={{ gridTemplateColumns: template }}
    >
      {/* ── Column headers (optional) ───────────────────────────────── */}
      {renderHeaders &&
        columns.map((c, i) => (
          <div
            key={`ch-${i}`}
            className={`
              dsi-analysis-description
              flex gap-dsi-pad 
              text-xs 
              ${TEXTALIGN_CLASS[c.headeralign]} 
              border-b-1 border-dsi-outline/50
              pb-1`}
          >
            {c.label}
          </div>
        ))}

      {/* ── Groups ──────────────────────────────────────────────────── */}
      {groups.map((g) => {
        const isOpen = !!expanded[g.key];
        return (
          <Fragment key={g.key}>
            
            {/* Group header row */}
            <div
              onClick={() => toggle(g.key)}
              className="
                dsi-analysis-description  
                border-t border-dsi-outline/20 
                hover:text-dsi-selected 
                flex 
                gap-dsi-pad 
                pt-dsi-pad pb-dsi-pad"
            >
              {isOpen ? <ChevronDown className="icon" /> : <ChevronRight className="icon" />}
              {g.title}
            </div>
            {g.summary.map((cell, i) => {
              const colIdx = i + 1;
              const col = columns[colIdx];
              const isLast = colIdx === lastIdx;
              return (
                <div
                  key={`${g.key}-sum-${i}`}
                  onClick={() => toggle(g.key)}
                  className={`
                      border-t border-dsi-outline/10 
                      cursor-pointer 
                      content-center ${TEXTALIGN_CLASS[col.headeralign]}  
                      ${isLast ? "pl-dsi-pad pr-dsi-pad text-sm" : "text-xs"}`
                    }
                >
                  {cell}
                </div>
              );
            })}

            {/* Items, if expanded */}
            {isOpen &&
              g.items.length > 0 &&
              g.items.map((item, idx) => {
                const cells = renderItemCells(item, idx, g);
                return (
                  <Fragment key={`${g.key}-item-${idx}`}>
                    {cells.map((cell, colIdx) => {
                      const col = columns[colIdx];
                      return (
                        <div
                          key={colIdx}
                          className={`bg-dsi-background/30 text-xs content-center pt-1 pb-1 ${TEXTALIGN_CLASS[col.headeralign]} ${
                            colIdx === 0 ? "pl-dsi-padicon" : ""
                          } ${colIdx === lastIdx ? "pr-dsi-pad" : ""}`}
                        >
                          {cell}
                        </div>
                      );
                    })}
                  </Fragment>
                );
              })}

            {/* Empty state when expanded + no items */}
            {isOpen && g.items.length === 0 && (
              <div
                className={`text-xs opacity-50 italic pl-dsi-padicon pt-1 pb-1 bg-dsi-background/30`}
                style={{ gridColumn: "1 / -1" }}
              >
                {g.emptyMessage ?? defaultEmptyMessage}
              </div>
            )}
          </Fragment>
        );
      })}
    </div>
  );
}

/** INFO PANEL---------------------------------------------------------------------------------------------- */

/** GUIDANCE
 * label: Small header label shown above the body.
 * aside: Right-aligned aside in the header row (e.g. a weight, a pill)
 * children: Body content
 * className: Extra classes appended to the outer wrapper.
 * padding: Padding size. Default "md" (p-3).
 */
export interface InfoPanelProps {
  label?: React.ReactNode;
  aside?: React.ReactNode;
  children: React.ReactNode;
  className?: string;
  padding?: Padding;
}

export const InfoPanel = ({
  label,
  aside,
  children,
  className = "",
  padding = "md",
}: InfoPanelProps) => {
  const showHeader = label !== undefined || aside !== undefined;

  return (
    <div
      className={`border border-dsi-outline/20 rounded-lg ${PADDING_CLASS[padding]} ${className}`}
    >
      {showHeader && (
        <div className="flex items-center justify-between mb-2">
          {label !== undefined && (
            <span className="text-xs font-semibold uppercase opacity-70">{label}</span>
          )}
          {aside !== undefined && (
            <span className="text-[10px] opacity-40">{aside}</span>
          )}
        </div>
      )}
      {children}
    </div>
  );
}

/** LABEL-VALUE LIST---------------------------------------------------------------------------------------------- */

/** GUIDANCE
 * key: Override the React key. Defaults to the label stringified + index.
 * valueClassName: Extra classes on the value `<span>` (e.g. `text-dsi-selected`).
 */
export interface LabelValueRow {
  label: React.ReactNode;
  value: React.ReactNode;
  key?: string;
  valueClassName?: string;
}

/** GUIDANCE
 * className: Extra classes on the outer wrapper.
 */
interface LabelValueListProps {
  rows: LabelValueRow[];
  variant?: LabelValueVariant;
  emptyMessage?: string;
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

/**
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
export const LabelValueList = ({
  rows,
  variant = "card",
  emptyMessage = "No data available.",
  className = "",
}: LabelValueListProps) => {
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

/** KEY VALUE LIST---------------------------------------------------------------------------------------------- */

/** GUIDANCE
 * filter: Optional predicate to filter which keys are rendered.
 * renderLabel: Label cell renderer. Defaults to the raw key.
 * renderValue: Value cell renderer. Defaults to `String(value)
 * valueClassName: Tailwind classes appended to the value `<span>` in every row.
 * variant: Visual variant — defaults to "modal" (divided font-mono rows).
 */
export interface KeyValueListProps<V = unknown> {
  data: Record<string, V> | null | undefined;
  filter?: (key: string) => boolean;
  renderLabel?: (key: string) => React.ReactNode;
  renderValue?: (value: V, key: string) => React.ReactNode;
  valueClassName?: string;
  emptyMessage?: string;
  variant?: LabelValueVariant;
}

/**
 * Used when the source is a raw `Record<string, V>` rather than a
 * pre-structured rows array (modal bodies like Submission Data / Discovery
 * Output). Delegates all rendering to LabelValueList so styling stays in one
 * place.
 */
export const KeyValueList = <V,>({
  data,
  filter,
  renderLabel = (k) => k,
  renderValue = (v) => String(v),
  valueClassName,
  emptyMessage = "No data available.",
  variant = "modal",
}: KeyValueListProps<V>) => {
  const rows = Object.entries(data ?? {})
    .filter(([k]) => !filter || filter(k))
    .map(([k, v]) => ({
      key: k,
      label: renderLabel(k),
      value: renderValue(v as V, k),
      valueClassName,
    }));

  return <LabelValueList rows={rows} variant={variant} emptyMessage={emptyMessage} />;
}

/** KPI TILE---------------------------------------------------------------------------------------------- */

/** GUIDANCE
 * subText: Optional small caption under the value.
 * lucideIcon: Optional trailing icon on the label row..
 */
export interface KpiTileProps {
  label: React.ReactNode;
  value: React.ReactNode;
  subtext?: React.ReactNode;
  lucideIcon?: LucideIcon;
  variant?: KpiVariant;
}

/**
 * The "big number with a caption" pattern used ~20× across RiskTab /
 * LossTab / ExposureTab. Drop a row of tiles inside a card body for a
 * headline KPI strip.
 *
 * Variants:
 *   • "default"  — base colour, lg value.
 *   • "emphasis" — text-dsi-selected + xl value. For the "final" number in
 *                  a row.
 *
 * Compose a row manually (`<div className="grid grid-cols-N gap-4">`) — a
 * tile doesn't care about its siblings.
 */
export const KpiTile = ({
  label,
  value,
  subtext,
  lucideIcon: Icon,
  variant = "default",
}: KpiTileProps) => {
  const valueClass =
    variant === "emphasis"
      ? "font-bold text-xl text-dsi-selected"
      : "font-bold text-lg";

  return (
    <div>
      <span className="flex items-center gap-1 text-sm mb-1">
        {Icon && <Icon className="icon" />}
        {label}
      </span>
      <span className={`block ${valueClass}`}>{value}</span>
      {subtext && <span className="text-xs opacity-50 block">{subtext}</span>}
    </div>
  );
}

/** SCORE BAR---------------------------------------------------------------------------------------------- */


/** GUIDANCE
 * at: Inclusive upper bound. First matching entry wins.
 * colour: CSS value for `backgroundColor`, e.g. `"var(--dsi-negative)"`
 */
export interface ScoreBarThreshold {
  at: number;
  color: string;
}

/** GUIDANCE
 * value: Numeric score. Clamped to [min, max] for the bar width.
 * label: Label on the left. Optional
 * thresholds: Thresholds from lowest `at` to highest. The first whose `at >= value`
 * min: Domain min. Default 0 
 * max: Domain max. Default 100.
 * decimals: Decimal places for the numeric readout. Default 1.
 * hideValue: Don't show the numeric readout on the right. Default false.
 * labelWidth: Tailwind class for the label column width. Default "w-10".
 */
export interface ScoreBarProps {
  value: number;
  label?: React.ReactNode;
  thresholds?: ScoreBarThreshold[];
  min?: number;
  max?: number;
  decimals?: number;
  hideValue?: boolean;
  labelWidth?: string;
}

function pickColor(value: number, thresholds: ScoreBarThreshold[]): string {
  for (const t of thresholds) {
    if (value <= t.at) return t.color;
  }
  return thresholds[thresholds.length - 1]?.color ?? "var(--dsi-muted)";
}

/**
 * The "label | filled pill | number" row from LossTab's group frequency /
 * severity indicators. Configurable thresholds and colour stops so the
 * same primitive can render "higher is worse" (frequency) and "higher is
 * better" (any positive metric).
 */
export const ScoreBar = ({
  value,
  label,
  thresholds = DEFAULT_THRESHOLDS,
  min = 0,
  max = 100,
  decimals = 1,
  hideValue = false,
  labelWidth = "w-10",
}: ScoreBarProps) => {
  const span = max - min || 1;
  const pct = Math.min(100, Math.max(2, ((value - min) / span) * 100));
  const color = pickColor(value, thresholds);

  return (
    <div className="flex items-center gap-2">
      {label !== undefined && (
        <span className={`text-[10px] opacity-50 shrink-0 ${labelWidth}`}>{label}</span>
      )}
      <div className="flex-1 h-1.5 bg-dsi-background rounded-full overflow-hidden">
        <div
          className="h-full rounded-full transition-all"
          style={{ width: `${pct}%`, backgroundColor: color }}
        />
      </div>
      {!hideValue && (
        <span className="text-[10px] font-bold w-8 text-right">
          {formatNumber(value, decimals)}
        </span>
      )}
    </div>
  );
}

/** STATS GRID---------------------------------------------------------------------------------------------- */

/** GUIDANCE
 * Shares label / width / align with StandardTableColumn. Adds the per-column
 * `value` because StatsGrid embeds the value in the column def rather than
 * looking it up on a row by `field`.
 */
export interface StatsGridColumn extends StandardTableColumn {
  value: React.ReactNode;
}

interface StatsGridProps {
  columns: StatsGridColumn[];
  className?: string;
}

/**
 * Canonical primitive for the dashboard "hero metrics" style layout where
 * each column has a small header label on top and a large prominent value
 * underneath (uses `dsi-grid-table-header` / `dsi-grid-table-item`).
 *
 * Column widths are passed via inline grid-template-columns so arbitrary
 * percentages don't need to be known at build time. Per-column `align`
 * overrides the utilities' default centering.
 */
export const StatsGrid = ({ columns, className = "" }: StatsGridProps) => {
  const template = buildGridTemplate(columns);
  const lastIdx = columns.length - 1;

  return (
    <div className={`grid ${className}`} style={{ gridTemplateColumns: template }}>
      {columns.map((c, i) => (
        <div
          key={`h-${i}`}
          className={`dsi-grid-table-header ${TEXTALIGN_CLASS[c.align ?? "center"]} ${i === lastIdx ? "border-r-0" : ""}`}
        >
          {c.label}
        </div>
      ))}
      {columns.map((c, i) => (
        <div
          key={`v-${i}`}
          className={`dsi-grid-table-item ${TEXTALIGN_CLASS[c.align ?? "center"]} ${i === lastIdx ? "border-r-0" : ""}`}
        >
          {c.value}
        </div>
      ))}
    </div>
  );
}

/** STATUS PILL---------------------------------------------------------------------------------------------- */

/** GUIDANCE
 * children: Pill label — usually the status name, rendered uppercase
 * lucideIcon: Optional leading icon from lucide-react, e.g. `Circle`, `Check`, `AlertTriangle`.
 * palette + status: Either provide a palette + status key to look up, or pass `tone`
 * size: "sm"` (default) = 10px / `"md"` = xs..
 * label: Label on the left. Optional
 * thresholds: Thresholds from lowest `at` to highest. The first whose `at >= value`
 * min: Domain min. Default 0 
 * max: Domain max. Default 100.
 * decimals: Decimal places for the numeric readout. Default 1.
 * hideValue: Don't show the numeric readout on the right. Default false.
 * labelWidth: Tailwind class for the label column width. Default "w-10".
 */
export interface StatusPillProps {
  children: React.ReactNode;
  lucideIcon?: LucideIcon;
  palette?: Record<string, StatusPaletteEntry>;
  status?: string | null;
  tone?: StatusTone;
  size?: "sm" | "md";
}

/**
 * Wraps the `bg-dsi-<tone>/15 text-dsi-<tone>` pattern used 15+ times
 * across the workbench. Pass either a `palette` + `status` pair (to look
 * the entry up by key) or a raw `tone` for ad-hoc use.
 */
export const StatusPill = ({
  children,
  lucideIcon: Icon,
  palette,
  status,
  tone,
  size = "sm",
}: StatusPillProps) => {
  const entry: StatusPaletteEntry = tone
    ? TONE_PALETTE[tone]
    : palette
      ? getStatusStyle(palette, status)
      : TONE_PALETTE.muted;

  const sizeClass =
    size === "md"
      ? "text-xs px-2 py-1 gap-1.5"
      : "text-[10px] px-2 py-0.5 gap-1";

  return (
    <span
      className={`inline-flex items-center rounded font-bold uppercase tracking-wide whitespace-nowrap ${entry.bg} ${entry.text} ${sizeClass}`}
    >
      {Icon && <Icon className="w-3 h-3" />}
      {children}
    </span>
  );
}

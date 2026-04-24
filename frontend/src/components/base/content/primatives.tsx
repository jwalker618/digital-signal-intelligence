"use client";

import { Fragment, useState } from "react";
import {
  formatNumber,
  formatText,
  formatCurrency,
  formatPercent,
  formatDate,
} from "@/lib/format";

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
  { at: 40, color: "var(--generate-approve)" },
  { at: 70, color: "var(--generate-refer)" },
  { at: Infinity, color: "var(--generate-decline)" },
];

export type Padding = "sm" | "md" | "lg";

const PADDING_CLASS: Record<NonNullable<InfoPanelProps["padding"]>, string> = {
  sm: "p-2", md: "p-3", lg: "p-4",
};

/** COMMON INTERFACES ---------------------------------------------------------------------------------------------- */

/** Per-column formatter — maps 1:1 to the helpers in `@/lib/format`. */
export type ColumnFormat = "text" | "number" | "currency" | "percent" | "date";

/** Optional formatter configuration shared by every table-like primitive
 *  that renders data via columns. Defaults mirror each helper's defaults. */
export interface ColumnFormatOptions {
  format?: ColumnFormat;
  /** Numeric decimals for number / currency / percent. */
  decimals?: number;
  /** ISO currency code for `format: "currency"`. Default `"USD"`. */
  currency?: string;
  /** Casing for `format: "text"`. Default `"capitalize"`. */
  textCase?: "normal" | "upper" | "lower" | "capitalize";
  /** BCP-47 locale for `format: "date"`. Default `"en-GB"`. */
  locale?: string;
  /** Fallback string when the source value is nullish. */
  fallback?: string;
}

/** GUIDANCE
 * label:        Header cell content.
 * field:        Row field to read. Omit (or pass null) to treat this column
 *               as the "name" column — it will render `row.name` instead,
 *               with name-style chrome (border-r, lighter weight).
 * width:        CSS grid track value, e.g. `"50%"`, `"1fr"`, `"auto"`.
 *               Default `"1fr"`.
 * align:        Cell alignment. Defaults to "right" for value columns and
 *               "left" for name columns.
 * headeralign:  Header cell alignment. Defaults to "center" for value
 *               columns and "left" for name columns.
 * format + opts:Formatter to apply to raw values. Defaults: "text" for
 *               name columns, "number" for value columns.
 */
export interface StandardTableColumn extends ColumnFormatOptions {
  label?: React.ReactNode;
  field?: string | null;
  width?: string;
  align?: Align;
  headeralign?: Align;
}

export interface StandardTableRow extends Record<string, unknown> {
  name?: string | null;
}

/** Apply the column's configured formatter (or the smart default based on
 *  whether the column has a `field`) to a raw cell value. */
const applyColumnFormat = (
  value: unknown,
  column: StandardTableColumn,
): string => {
  const {
    format,
    decimals,
    currency = "USD",
    textCase = "capitalize",
    locale = "en-GB",
    fallback,
  } = column;
  const chosen: ColumnFormat = format ?? (column.field ? "number" : "text");

  switch (chosen) {
    case "text":
      return formatText(
        value as string | null | undefined,
        textCase,
        fallback ?? "n/a",
      );
    case "number":
      return formatNumber(
        value as number | null | undefined,
        decimals ?? 2,
        fallback ?? "0",
      );
    case "currency":
      return formatCurrency(
        value as number | null | undefined,
        decimals ?? 0,
        currency,
        fallback ?? "0",
      );
    case "percent":
      return formatPercent(
        value as number | null | undefined,
        decimals ?? 0,
        fallback ?? "0",
      );
    case "date":
      return formatDate(
        value as string | null | undefined,
        locale,
        fallback ?? "n/a",
      );
    default:
      return String(value ?? fallback ?? "");
  }
};

/** Build a CSS grid-template-columns track list from column widths.
 *  Missing widths fall back to "1fr" so omitting width gives equal columns.
 *  Tolerates null/undefined for defensive rendering during loading states. */
const buildGridTemplate = (columns: StandardTableColumn[] | null | undefined): string =>
  (columns ?? []).map((c) => c.width ?? "1fr").join(" ");

/** CONTRIBUTION TABLE ---------------------------------------------------------------------------------------------- */

/** GUIDANCE
 * columns: Column definitions. Fieldless columns render `row.name` in
 *          name-style (border-r, lighter weight). Fielded columns render
 *          `row[field]` through the column's formatter (default "number").
 * rows:    Pre-sorted rows; at most the first 3 are rendered.
 * otherRow: Optional pre-aggregated "Other" row rendered after the top 3.
 */
interface ContributionTableProps {
  columns: StandardTableColumn[];
  rows: StandardTableRow[];
  otherRow?: StandardTableRow;
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
  className = "",
}: ContributionTableProps) => {

  const template = buildGridTemplate(columns);
  const allRows = otherRow ? [...rows.slice(0, 3), otherRow] : rows.slice(0, 3);

  const cellAlign = (c: StandardTableColumn): Align =>
    c.align ?? (c.field ? "right" : "left");
  const headerAlign = (c: StandardTableColumn): Align =>
    c.headeralign ?? (c.field ? "center" : "left");

  return (

    <div className={`grid ${className}`} style={{ gridTemplateColumns: template }}>

      {/* Headers */}
      {columns.map((c, i) => (
        <div
          key={`h-${i}`}
          className={`generate-analysis-description text-xs ${TEXTALIGN_CLASS[headerAlign(c)]} border-b-1 border-generate-outline/50 pb-1`}
        >
          {c.label}
        </div>
      ))}

      {/* Data rows */}
      {allRows.map((row, idx) => (
        <Fragment key={`r-${idx}`}>
          {columns.map((c, i) => {
            const isName = !c.field;
            const rawValue = isName ? row?.name : row?.[c.field!];
            const content = applyColumnFormat(rawValue, c);
            return (
              <div
                key={`v-${idx}-${i}`}
                className={
                  isName
                    ? `generate-analysis-description ${TEXTALIGN_CLASS[cellAlign(c)]} border-r-1 border-generate-outline/50 pt-1 pb-1`
                    : `generate-analysis-item ${TEXTALIGN_CLASS[cellAlign(c)]} pt-1 pb-1`
                }
              >
                {content}
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
 * renderItemCells: Optional custom row renderer. If omitted, cells are
 *                  computed per column from `item[column.field]` through
 *                  `applyColumnFormat(...)`.
 * expanded: Controlled expansion map — if provided, `onToggle` is required.
 * defaultExpanded: Uncontrolled initial expansion map.
 * showColumnHeaders: Render the column header row. Default true if any
 *                    column has a label.
 * defaultEmptyMessage: Default empty-state text.
 */
export interface ExpandableGroupTableProps<T> {
  columns: StandardTableColumn[];
  groups: ExpandableGroup<T>[];
  renderItemCells?: (item: T, index: number, group: ExpandableGroup<T>) => React.ReactNode[];
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

  const cellAlign = (c: StandardTableColumn | undefined): Align =>
    c?.align ?? (c?.field ? "right" : "left");
  const headerAlign = (c: StandardTableColumn | undefined): Align =>
    c?.headeralign ?? (c?.field ? "center" : "left");

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
            className={`generate-analysis-description flex gap-generate-pad text-xs ${TEXTALIGN_CLASS[headerAlign(c)]} border-b-1 border-generate-outline/50 pb-1`}
          >
            {c.label}
          </div>
        ))}

      {/* ── Groups ──────────────────────────────────────────────────── */}
      {groups.map((g) => {
        const isOpen = !!expanded[g.key];
        return (
          <Fragment key={g.key}>

            {/* Group header row — chevron + title cell */}
            <div
              onClick={() => toggle(g.key)}
              className="generate-analysis-description border-t border-generate-outline/20 hover:text-generate-selected cursor-pointer flex gap-generate-pad pt-generate-pad pb-generate-pad"
            >
              {isOpen ? <ChevronDown className="icon" /> : <ChevronRight className="icon" />}
              {g.title}
            </div>
            {/* Group header row — summary value cells (align with value cells) */}
            {g.summary.map((cell, i) => {
              const colIdx = i + 1;
              const col = columns[colIdx];
              const isLast = colIdx === lastIdx;
              return (
                <div
                  key={`${g.key}-sum-${i}`}
                  onClick={() => toggle(g.key)}
                  className={`border-t border-generate-outline/10 cursor-pointer content-center ${TEXTALIGN_CLASS[cellAlign(col)]} ${
                    isLast ? "pl-generate-pad pr-generate-pad text-sm" : "text-xs"
                  }`}
                >
                  {cell}
                </div>
              );
            })}

            {/* Items, if expanded */}
            {isOpen &&
              g.items.length > 0 &&
              g.items.map((item, idx) => {
                // Auto-derive cells from `field + format` if caller didn't
                // provide a custom renderer.
                const cells = renderItemCells
                  ? renderItemCells(item, idx, g)
                  : columns.map((c) => {
                      const raw = c.field
                        ? (item as Record<string, unknown>)[c.field]
                        : (item as Record<string, unknown>).name;
                      return applyColumnFormat(raw, c);
                    });

                return (
                  <Fragment key={`${g.key}-item-${idx}`}>
                    {cells.map((cell, colIdx) => {
                      const col = columns[colIdx];
                      return (
                        <div
                          key={colIdx}
                          className={`bg-generate-background/30 text-xs content-center pt-1 pb-1 ${TEXTALIGN_CLASS[cellAlign(col)]} ${
                            colIdx === 0 ? "pl-generate-padicon" : ""
                          } ${colIdx === lastIdx ? "pr-generate-pad" : ""}`}
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
                className="text-xs opacity-50 italic pl-generate-padicon pt-1 pb-1 bg-generate-background/30"
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
      className={`border border-generate-outline/20 rounded-lg ${PADDING_CLASS[padding]} ${className}`}
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
 * valueClassName: Extra classes on the value `<span>` (e.g. `text-generate-selected`).
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
    label: "generate-analysis-description",
    value: "generate-analysis-item",
  },
  modal: {
    wrapper: "space-y-3 font-mono text-sm",
    row: "flex justify-between items-center py-2 border-b border-generate-outline/5 last:border-0",
    label: "opacity-60",
    value: "font-bold text-right",
  },
};

/**
 * Renders an ordered list of `{ label, value }` rows. Two visual variants:
 *   • "card"  — in-card summary rows (flex justify-between, uses
 *               generate-analysis-description / generate-analysis-item utilities).
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
    return <p className="generate-user-message">{emptyMessage}</p>;
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
 *   • "emphasis" — text-generate-selected + xl value. For the "final" number in
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
      ? "font-bold text-xl text-generate-selected"
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
 * colour: CSS value for `backgroundColor`, e.g. `"var(--generate-decline)"`
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
  return thresholds[thresholds.length - 1]?.color ?? "var(--generate-muted)";
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
      <div className="flex-1 h-1.5 bg-generate-background rounded-full overflow-hidden">
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
 * underneath (uses `generate-grid-table-header` / `generate-grid-table-item`).
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
          className={`generate-grid-table-header ${TEXTALIGN_CLASS[c.align ?? "center"]} ${i === lastIdx ? "border-r-0" : ""}`}
        >
          {c.label}
        </div>
      ))}
      {columns.map((c, i) => (
        <div
          key={`v-${i}`}
          className={`generate-grid-table-item ${TEXTALIGN_CLASS[c.align ?? "center"]} ${i === lastIdx ? "border-r-0" : ""}`}
        >
          {c.value}
        </div>
      ))}
    </div>
  );
}

/** COMPARE ROW---------------------------------------------------------------------------------------------- */

/** GUIDANCE
 * label:    Left cell content.
 * sublabel: Optional secondary line under the label.
 * original: Original-state value (left comparand).
 * scenario: Scenario-state value (right comparand).
 * changed:  When true, highlights the row with `bg-generate-selected/5` and
 *           renders the scenario value in `text-generate-selected font-bold`.
 * showArrow: Show the → between original and scenario. Default true.
 * gridTemplate: Override the grid-template-columns. Default
 *               `"1fr 80px 30px 80px"`.
 * className: Extra classes appended to the outer grid.
 */
export interface CompareRowProps {
  label: React.ReactNode;
  sublabel?: React.ReactNode;
  original: React.ReactNode;
  scenario: React.ReactNode;
  changed?: boolean;
  showArrow?: boolean;
  gridTemplate?: string;
  className?: string;
}

/**
 * The "label | original | → | scenario" row used repeatedly inside
 * ScenarioTab's loss / exposure / pricing cascades to visualise
 * before-vs-after comparisons. Kept column-template-driven so callers
 * can re-use the same primitive with different widths.
 */
export const CompareRow = ({
  label,
  sublabel,
  original,
  scenario,
  changed = false,
  showArrow = true,
  gridTemplate = "1fr 80px 30px 80px",
  className = "",
}: CompareRowProps) => {
  return (
    <div
      className={`grid gap-0 py-1.5 border-b border-generate-outline/5 ${
        changed ? "bg-generate-selected/5" : ""
      } ${className}`}
      style={{ gridTemplateColumns: gridTemplate }}
    >
      <div>
        <span className="text-xs">{label}</span>
        {sublabel && <span className="text-[10px] opacity-30 block">{sublabel}</span>}
      </div>
      <span className="text-right text-xs opacity-70">{original}</span>
      {showArrow ? (
        <span className="text-center opacity-30 text-xs">→</span>
      ) : (
        <span />
      )}
      <span className={`text-right text-xs font-bold ${changed ? "text-generate-selected" : ""}`}>
        {scenario}
      </span>
    </div>
  );
}

/** METRIC CARD---------------------------------------------------------------------------------------------- */

export type MetricCardTone =
  | "selected"
  | "positive"
  | "negative"
  | "warning"
  | "info"
  | "muted";

const METRIC_CARD_TONE: Record<
  MetricCardTone,
  { border: string; bg: string; text: string }
> = {
  selected: { border: "border-generate-selected/30", bg: "bg-generate-selected/5", text: "text-generate-selected" },
  positive: { border: "border-generate-approve/30", bg: "bg-generate-approve/5", text: "text-generate-approve" },
  negative: { border: "border-generate-decline/30", bg: "bg-generate-decline/5", text: "text-generate-decline" },
  warning:  { border: "border-generate-refer/30",  bg: "bg-generate-refer/5",  text: "text-generate-refer"  },
  info:     { border: "border-generate-info/30",     bg: "bg-generate-info/5",     text: "text-generate-info"     },
  muted:    { border: "border-generate-muted/30",    bg: "bg-generate-muted/5",    text: "text-generate-muted"    },
};

/** GUIDANCE
 * label:     Small uppercase caption above the hero value.
 * value:     Hero value — rendered xl + bold.
 * subtext:   Optional small caption beneath the value.
 * tone:      When provided, applies `border-2 border-generate-<tone>/30
 *            bg-generate-<tone>/5` and colours the value `text-generate-<tone>`.
 *            When omitted, renders a plain `border border-generate-outline/20` card.
 * lucideIcon: Optional leading icon rendered before the label.
 */
export interface MetricCardProps {
  label: React.ReactNode;
  value: React.ReactNode;
  subtext?: React.ReactNode;
  tone?: MetricCardTone;
  lucideIcon?: LucideIcon;
  className?: string;
}

/**
 * The "big label + hero value + caption" tile used across the risk-terms
 * tabs (Deductible / SIR / Aggregate / Reinstatement) inside a grid of
 * overview numbers. Pick `tone` to highlight the primary/selected cell or
 * to signal warning/info states.
 */
export const MetricCard = ({
  label,
  value,
  subtext,
  tone,
  lucideIcon: Icon,
  className = "",
}: MetricCardProps) => {
  const toneStyles = tone ? METRIC_CARD_TONE[tone] : null;
  const frame = toneStyles
    ? `border-2 ${toneStyles.border} ${toneStyles.bg}`
    : "border border-generate-outline/20";
  const valueColor = toneStyles?.text ?? "";

  return (
    <div className={`${frame} rounded-xl p-5 ${className}`}>
      <span className="flex items-center gap-1 opacity-50 text-xs mb-1 uppercase tracking-wider">
        {Icon && <Icon className="w-3 h-3" />}
        {label}
      </span>
      <span className={`block font-bold text-xl ${valueColor}`}>{value}</span>
      {subtext && <span className="block text-xs opacity-50 mt-1">{subtext}</span>}
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
 * Wraps the `bg-generate-<tone>/15 text-generate-<tone>` pattern used 15+ times
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

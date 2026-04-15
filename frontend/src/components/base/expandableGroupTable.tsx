"use client";

/**
 * ExpandableGroupTable — the "grouped accordion table" layout used by
 * PricingTab and similar detail views.
 *
 * Structure:
 *
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
 *       { label: "Adjustments", width: "50%", align: "left" },
 *       { label: "Modifier",   width: "10%", align: "center" },
 *       { label: "Impact",     width: "20%", align: "right" },
 *       { label: "Result",     width: "20%", align: "right" },
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

import "@/app/globals.css";
import { Fragment, useState } from "react";
import { ChevronDown, ChevronRight } from "lucide-react";

export type Align = "left" | "center" | "right";

export interface GroupTableColumn {
  label?: React.ReactNode;
  /** CSS grid track value, e.g. `"50%"`, `"1fr"`, `"auto"`. Default `"1fr"`. */
  width?: string;
  /** Horizontal alignment for this column's cells. Default `"left"`. */
  align?: Align;
}

export interface ExpandableGroup<T> {
  key: string;
  title: React.ReactNode;
  items: T[];
  /**
   * Cells 2..N of the group header row, left-to-right. Length should equal
   * `columns.length - 1` (the title occupies column 1).
   */
  summary: React.ReactNode[];
  /** Shown when the group is expanded and `items` is empty. */
  emptyMessage?: React.ReactNode;
}

export interface ExpandableGroupTableProps<T> {
  columns: GroupTableColumn[];
  groups: ExpandableGroup<T>[];
  /**
   * Returns one cell per column for a single item row — length must equal
   * `columns.length`.
   */
  renderItemCells: (item: T, index: number, group: ExpandableGroup<T>) => React.ReactNode[];
  /** Controlled expansion map — if provided, `onToggle` is required. */
  expanded?: Record<string, boolean>;
  onToggle?: (key: string) => void;
  /** Uncontrolled initial expansion map. */
  defaultExpanded?: Record<string, boolean>;
  /** Render the column header row. Default true if any column has a label. */
  showColumnHeaders?: boolean;
  /** Default empty-state text. */
  defaultEmptyMessage?: React.ReactNode;
  className?: string;
}

/* ── Styling helpers ─────────────────────────────────────────────────── */

const ALIGN_CLASS: Record<Align, string> = {
  left: "text-left",
  center: "text-center",
  right: "text-right",
};

const COMMON_CELL =
  "overflow-x-hidden whitespace-nowrap border-collapse";

/* ── Component ───────────────────────────────────────────────────────── */

export default function ExpandableGroupTable<T>({
  columns,
  groups,
  renderItemCells,
  expanded: controlledExpanded,
  onToggle,
  defaultExpanded = {},
  showColumnHeaders,
  defaultEmptyMessage = "No items.",
  className = "",
}: ExpandableGroupTableProps<T>) {
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
  const template = columns.map((c) => c.width ?? "1fr").join(" ");
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
            className={`${COMMON_CELL} text-xs pt-2 pb-2 ${ALIGN_CLASS[c.align ?? "left"]} ${
              i === lastIdx ? "pl-dsi-pad pr-dsi-pad" : ""
            } ${i === 0 ? "flex gap-dsi-pad text-sm" : ""}`}
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
              className={`${COMMON_CELL} border-t border-dsi-outline/10 hover:text-dsi-selected cursor-pointer flex gap-dsi-pad text-sm pt-dsi-pad pb-dsi-pad`}
            >
              {isOpen ? <ChevronDown className="icon" /> : <ChevronRight className="icon" />}
              {g.title}
            </div>
            {g.summary.map((cell, i) => {
              const colIdx = i + 1;
              const col = columns[colIdx];
              const align = col?.align ?? "right";
              const isLast = colIdx === lastIdx;
              return (
                <div
                  key={`${g.key}-sum-${i}`}
                  onClick={() => toggle(g.key)}
                  className={`${COMMON_CELL} border-t border-dsi-outline/10 cursor-pointer content-center ${ALIGN_CLASS[align]} ${
                    isLast ? "pl-dsi-pad pr-dsi-pad text-sm" : "text-xs"
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
                const cells = renderItemCells(item, idx, g);
                return (
                  <Fragment key={`${g.key}-item-${idx}`}>
                    {cells.map((cell, colIdx) => {
                      const col = columns[colIdx];
                      const align = col?.align ?? "left";
                      return (
                        <div
                          key={colIdx}
                          className={`${COMMON_CELL} bg-dsi-background/30 text-xs content-center pt-1 pb-1 ${ALIGN_CLASS[align]} ${
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
                className={`${COMMON_CELL} text-xs opacity-50 italic pl-dsi-padicon pt-1 pb-1 bg-dsi-background/30`}
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

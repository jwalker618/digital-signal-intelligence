/**
 * StatsGrid — header/value paired row layout.
 *
 * Canonical primitive for the dashboard "hero metrics" style layout where
 * each column has a small header label on top and a large prominent value
 * underneath (uses `dsi-grid-table-header` / `dsi-grid-table-item`).
 *
 * Column widths are passed via inline grid-template-columns so arbitrary
 * percentages don't need to be known at build time (Tailwind's JIT only sees
 * static class strings).
 */

import "@/app/globals.css";

export interface StatsGridColumn {
  label: React.ReactNode;
  value: React.ReactNode;
  /**
   * Any valid grid-template-columns track value — `"10%"`, `"1fr"`, `"auto"`,
   * etc. Defaults to `"1fr"` so omitting this gives equal-width columns.
   */
  width?: string;
}

interface StatsGridProps {
  columns: StatsGridColumn[];
  className?: string;
}

export default function StatsGrid({ columns, className = "" }: StatsGridProps) {
  const template = columns.map((c) => c.width ?? "1fr").join(" ");
  const lastIdx = columns.length - 1;

  return (
    <div className={`grid ${className}`} style={{ gridTemplateColumns: template }}>
      {columns.map((c, i) => (
        <div
          key={`h-${i}`}
          className={`dsi-grid-table-header ${i === lastIdx ? "border-r-0" : ""}`}
        >
          {c.label}
        </div>
      ))}
      {columns.map((c, i) => (
        <div
          key={`v-${i}`}
          className={`dsi-grid-table-item ${i === lastIdx ? "border-r-0" : ""}`}
        >
          {c.value}
        </div>
      ))}
    </div>
  );
}

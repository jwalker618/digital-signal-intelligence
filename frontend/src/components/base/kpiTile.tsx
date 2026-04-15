/**
 * KpiTile — a small labelled metric tile.
 *
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

import "@/app/globals.css";
import { LucideIcon } from "lucide-react";

export type KpiVariant = "default" | "emphasis";

export interface KpiTileProps {
  label: React.ReactNode;
  value: React.ReactNode;
  /** Optional small caption under the value. */
  subtext?: React.ReactNode;
  /** Optional trailing icon on the label row. */
  lucideIcon?: LucideIcon;
  variant?: KpiVariant;
}

export default function KpiTile({
  label,
  value,
  subtext,
  lucideIcon: Icon,
  variant = "default",
}: KpiTileProps) {
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

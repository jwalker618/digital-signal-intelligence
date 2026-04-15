/**
 * InfoPanel — the "bordered box with a small label" used across
 * ExposureTab and LossTab for sub-metric panels (band percentile, below
 * ceiling, component scores etc).
 *
 * Slightly more than a div — adds the border, rounded corners, padding,
 * and an optional header row (label + trailing aside).
 */

import "@/app/globals.css";

export interface InfoPanelProps {
  /** Small header label shown above the body. */
  label?: React.ReactNode;
  /** Right-aligned aside in the header row (e.g. a weight, a pill). */
  aside?: React.ReactNode;
  /** Body content. */
  children: React.ReactNode;
  /** Extra classes appended to the outer wrapper. */
  className?: string;
  /** Padding size. Default "md" (p-3). */
  padding?: "sm" | "md" | "lg";
}

const PADDING_CLASS: Record<NonNullable<InfoPanelProps["padding"]>, string> = {
  sm: "p-2",
  md: "p-3",
  lg: "p-4",
};

export default function InfoPanel({
  label,
  aside,
  children,
  className = "",
  padding = "md",
}: InfoPanelProps) {
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

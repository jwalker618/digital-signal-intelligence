import { cn } from "@/lib/utils";

type Tone = "default" | "spot" | "warn" | "neg" | "pos" | "info";

interface KpiPillProps {
  label: string;
  value: React.ReactNode;
  /** Color tone applied to the pill background + value text. */
  tone?: Tone;
  className?: string;
}

const toneClass: Record<Tone, string> = {
  default: "bg-surface-sunken text-ink",
  spot: "bg-spot-soft text-spot-deep dark:text-spot",
  warn: "bg-warn-soft text-warn",
  neg: "bg-neg-soft text-neg",
  pos: "bg-pos-soft text-pos",
  info: "bg-info-soft text-info-deep dark:text-info",
};

/**
 * Horizontal capsule KPI: a slim rounded pill carrying a label and a
 * tabular value. Used in the coverages summary rows where a Chip-shaped
 * KPI is wanted rather than a stacked block.
 */
export function KpiPill({
  label,
  value,
  tone = "default",
  className,
}: KpiPillProps) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-2 rounded-full px-3 py-1.5",
        toneClass[tone],
        className,
      )}
    >
      <span className="text-[11px] uppercase tracking-[0.08em] text-ink-mute">
        {label}
      </span>
      <span className="text-[15px] font-semibold tabular-nums">{value}</span>
    </span>
  );
}

import { cn } from "@/lib/utils";
import { Icon } from "./icon";
import { Caption, Micro } from "./typography";

interface KpiTileProps {
  label: string;
  value: React.ReactNode;
  sub?: React.ReactNode;
  icon?: string;
  emphasis?: boolean;
  className?: string;
}

/**
 * Small stat block. Label on top with optional icon, value (big), optional
 * sub-caption below. `emphasis` bumps the value size and pins it to ink.
 */
export function KpiTile({
  label,
  value,
  sub,
  icon,
  emphasis,
  className,
}: KpiTileProps) {
  return (
    <div className={className}>
      <div className="mb-1 flex items-center gap-1 text-[13px] text-ink-soft">
        {icon && <Icon name={icon} size={14} />}
        <span>{label}</span>
      </div>
      <div
        className={cn(
          "font-semibold tabular-nums",
          emphasis ? "text-[22px] text-ink" : "text-lg text-ink-soft",
        )}
      >
        {value}
      </div>
      {sub && (
        <div className="mt-0.5 text-[11px] text-ink-mute">{sub}</div>
      )}
    </div>
  );
}

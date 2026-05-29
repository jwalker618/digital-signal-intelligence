import { cn } from "@/lib/utils";
import { Micro, NumDisplay } from "./typography";

type Tone = "default" | "spot" | "warn" | "neg" | "pos" | "info";

interface KpiSnugProps {
  label: string;
  value: React.ReactNode;
  /** Optional delta indicator rendered below the value (e.g. a Chip). */
  delta?: React.ReactNode;
  /** Color tone applied to the value. */
  tone?: Tone;
  className?: string;
}

const toneClass: Record<Tone, string> = {
  default: "text-ink",
  spot: "text-spot",
  warn: "text-warn",
  neg: "text-neg",
  pos: "text-pos",
  info: "text-info",
};

/**
 * Compact KPI block used across broker pages. Tiny eyebrow label,
 * mid-sized tabular number, optional delta chip below. Renders as a plain
 * block — wrap in a Card/grid if a surface is needed.
 */
export function KpiSnug({
  label,
  value,
  delta,
  tone = "default",
  className,
}: KpiSnugProps) {
  return (
    <div className={className}>
      <Micro>{label}</Micro>
      <NumDisplay
        size="sm"
        className={cn("mt-0.5 block text-[22px]", toneClass[tone])}
      >
        {value}
      </NumDisplay>
      {delta && <div className="mt-1">{delta}</div>}
    </div>
  );
}

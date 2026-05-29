import { cn } from "@/lib/utils";
import { Micro, NumDisplay } from "./typography";

interface MiniKpiProps {
  label: string;
  value: React.ReactNode;
  /** Optional helper text rendered below the value. */
  caption?: string;
  className?: string;
}

/**
 * Even more compact KPI block — used inline, often in a row of stats.
 * Label on top, value below, optional caption underneath. No surface
 * wrapper of its own; compose inside a Card or grid as needed.
 */
export function MiniKpi({ label, value, caption, className }: MiniKpiProps) {
  return (
    <div className={cn("min-w-0", className)}>
      <Micro>{label}</Micro>
      <NumDisplay size="sm" className="mt-0.5 block">
        {value}
      </NumDisplay>
      {caption && <Micro className="mt-0.5 block">{caption}</Micro>}
    </div>
  );
}

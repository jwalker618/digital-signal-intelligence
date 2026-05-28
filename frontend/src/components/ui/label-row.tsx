import { cn } from "@/lib/utils";

interface LabelRowProps {
  label: React.ReactNode;
  value: React.ReactNode;
  className?: string;
}

/** Simple key/value row. Label left, value right (bold). */
export function LabelRow({ label, value, className }: LabelRowProps) {
  return (
    <div
      className={cn(
        "flex items-baseline justify-between gap-3 py-1 text-[13px]",
        className,
      )}
    >
      <span className="text-ink-soft">{label}</span>
      <span className="font-semibold text-ink tabular-nums">{value}</span>
    </div>
  );
}

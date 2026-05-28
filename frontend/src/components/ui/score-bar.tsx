import { cn } from "@/lib/utils";
import { TONE_BG, type Tone } from "@/lib/design-tokens";

interface Threshold {
  /** Inclusive upper bound on the value. */
  at: number;
  tone: Tone;
}

interface ScoreBarProps {
  value: number;
  max?: number;
  thresholds?: Threshold[];
  /** Show numeric value at the right edge. */
  showValue?: boolean;
  className?: string;
}

/**
 * Horizontal progress bar with threshold-driven color. The first threshold
 * whose `at >= value` wins; falls back to the last entry's tone.
 */
export function ScoreBar({
  value,
  max = 100,
  thresholds = [{ at: max, tone: "pos" }],
  showValue = true,
  className,
}: ScoreBarProps) {
  const pct = Math.min(100, Math.max(2, (value / max) * 100));
  let tone: Tone = thresholds[thresholds.length - 1]!.tone;
  for (const t of thresholds) {
    if (value <= t.at) {
      tone = t.tone;
      break;
    }
  }
  return (
    <div className={cn("flex items-center gap-2", className)}>
      <div className="h-1.5 flex-1 overflow-hidden rounded-full bg-surface-sunken">
        <div
          className={cn("h-full rounded-full", TONE_BG[tone])}
          style={{ width: `${pct}%` }}
        />
      </div>
      {showValue && (
        <span className="w-8 text-right text-[10px] font-bold tabular-nums text-ink">
          {value}
        </span>
      )}
    </div>
  );
}

import { memo } from "react";
import { Circle, TrendingDown, TrendingUp } from "lucide-react";
import { Card } from "@/components/ui/card";
import { Chip } from "@/components/ui/chip";
import { Eyebrow, Micro } from "@/components/ui/typography";
import { cn } from "@/lib/utils";
import type { ClientCoverageEntry } from "@/types/portal";

function lastTwelveQuarterLabels(now: Date = new Date()): string[] {
  const labels: string[] = [];
  let q = Math.floor(now.getUTCMonth() / 3);
  let yr = now.getUTCFullYear();
  for (let i = 0; i < 12; i++) {
    labels.unshift(`${String(yr).slice(2)} Q${q + 1}`);
    q -= 1;
    if (q < 0) {
      q = 3;
      yr -= 1;
    }
  }
  return labels;
}

function lossBandLabel(band: string): string {
  switch (band) {
    case "very_low":
      return "Very low";
    case "low":
      return "Low";
    case "moderate":
    case "medium":
      return "Moderate";
    case "elevated":
      return "Elevated";
    case "high":
      return "High";
    default:
      return band.charAt(0).toUpperCase() + band.slice(1).replace(/_/g, " ");
  }
}

function lossTrend(direction: string): {
  variant: "pos" | "neg" | "mute";
  icon: React.ReactNode;
  label: string;
} {
  switch (direction) {
    case "improving":
      return { variant: "pos", icon: <TrendingDown size={11} />, label: "Improving" };
    case "deteriorating":
    case "worsening":
      return { variant: "neg", icon: <TrendingUp size={11} />, label: "Worsening" };
    case "stable":
      return { variant: "mute", icon: <Circle size={11} />, label: "Stable" };
    default:
      return { variant: "mute", icon: <Circle size={11} />, label: direction };
  }
}

export const LossOutlookCard = memo(function LossOutlookCard({
  hero,
}: {
  hero?: ClientCoverageEntry;
}) {
  const bandLabel = hero?.loss_propensity_band
    ? lossBandLabel(hero.loss_propensity_band)
    : "Low";
  const trend = hero?.loss_trend_direction
    ? lossTrend(hero.loss_trend_direction)
    : { variant: "pos" as const, icon: <TrendingDown size={11} />, label: "Improving" };
  const freqValue =
    hero?.loss_frequency_velocity != null
      ? Math.round(hero.loss_frequency_velocity)
      : 32;
  const sevValue =
    hero?.loss_severity_velocity != null
      ? Math.round(hero.loss_severity_velocity)
      : 41;

  const quarters: number[] = hero?.loss_event_quarters?.length
    ? hero.loss_event_quarters
    : [0, 0, 0, 0, 0, 0.4, 0, 0, 0, 0, 0.7, 0];
  const quarterLabels = lastTwelveQuarterLabels();

  return (
    <Card variant="pos" pad="lg" className="flex h-full flex-col gap-3">
      <div className="flex items-baseline justify-between">
        <div>
          <Eyebrow className="text-pos">Loss outlook</Eyebrow>
          <p className="mt-1 text-xl font-semibold text-pos">{bandLabel}</p>
        </div>
        <Chip variant={trend.variant} size="sm">
          {trend.icon} {trend.label}
        </Chip>
      </div>
      <div>
        <Micro className="mb-1 block">Claims, last 12 quarters</Micro>
        <div className="grid grid-cols-12 gap-1">
          {quarters.map((v, i) => (
            <div
              key={i}
              className={cn(
                "h-3.5 rounded-sm border",
                v > 0 ? "border-neg bg-neg/40" : "border-rule bg-surface",
              )}
              style={
                v > 0
                  ? { background: `color-mix(in srgb, var(--color-neg) ${30 + v * 70}%, transparent)` }
                  : undefined
              }
              title={`${quarterLabels[i]} — ${v > 0 ? "claim" : "no claim"}`}
            />
          ))}
        </div>
        <div className="mt-1 flex justify-between">
          {[quarterLabels[0], quarterLabels[6], quarterLabels[11]].map((l) => (
            <Micro key={l}>{l}</Micro>
          ))}
        </div>
      </div>
      <div className="mt-auto grid grid-cols-2 gap-3">
        <CompareBar label="Frequency" value={freqValue} cohort={48} />
        <CompareBar label="Severity" value={sevValue} cohort={44} />
      </div>
    </Card>
  );
});

function CompareBar({
  label,
  value,
  cohort,
  max = 100,
}: {
  label: string;
  value: number;
  cohort: number;
  max?: number;
}) {
  const better = value < cohort;
  return (
    <div>
      <div className="flex justify-between">
        <Micro>{label}</Micro>
        <Micro>vs {cohort}</Micro>
      </div>
      <div className="relative mt-1 h-1 rounded-sm bg-rule">
        <div
          className={cn(
            "absolute left-0 top-0 h-full rounded-sm",
            better ? "bg-pos" : "bg-neg",
          )}
          style={{ width: `${(value / max) * 100}%` }}
        />
        <div
          className="absolute h-2.5 w-0.5 bg-ink-soft"
          style={{ left: `${(cohort / max) * 100}%`, top: -3 }}
        />
      </div>
      <p
        className={cn(
          "mt-1 text-[12px] font-semibold tabular-nums",
          better ? "text-pos" : "text-neg",
        )}
      >
        {value}
      </p>
    </div>
  );
}

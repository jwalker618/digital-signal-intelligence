import { memo } from "react";
import { TrendingDown, TrendingUp } from "lucide-react";
import { Card } from "@/components/ui/card";
import { Chip } from "@/components/ui/chip";
import { Eyebrow, Micro, Caption } from "@/components/ui/typography";
import type { ClientCoverageEntry } from "@/types/portal";

function formatExposure(value: number): string {
  const abs = Math.abs(value);
  if (abs >= 1_000_000_000) return `$${(value / 1_000_000_000).toFixed(1)}B`;
  if (abs >= 1_000_000) return `$${Math.round(value / 1_000_000)}M`;
  if (abs >= 1_000) return `$${Math.round(value / 1_000)}k`;
  return `$${Math.round(value)}`;
}

export const ExposureCard = memo(function ExposureCard({
  hero,
}: {
  hero?: ClientCoverageEntry;
}) {
  const exposureValue = hero?.exposure_value ?? null;
  const exposurePrior = hero?.exposure_value_prior ?? null;
  const pinPct = hero?.exposure_size_score ?? 55;
  const yoyPct =
    exposureValue != null && exposurePrior != null && exposurePrior !== 0
      ? Math.round(((exposureValue - exposurePrior) / exposurePrior) * 100)
      : null;
  const yoyLabel =
    yoyPct != null ? `${yoyPct >= 0 ? "+" : ""}${yoyPct}% YoY` : "+12% YoY";
  const yoyPositive = yoyPct == null ? true : yoyPct >= 0;
  const valueLabel = exposureValue != null ? formatExposure(exposureValue) : "$118M";
  const bandLabel = hero?.exposure_band_label ?? null;

  return (
    <Card variant="aux" pad="lg" className="flex h-full flex-col gap-3">
      <div className="flex items-baseline justify-between">
        <div>
          <Eyebrow className="text-aux">Exposure</Eyebrow>
          <p className="mt-1 text-xl font-semibold text-aux">{valueLabel}</p>
          {bandLabel && <Caption className="mt-0.5">{bandLabel}</Caption>}
        </div>
        <Chip variant={yoyPositive ? "pos" : "neg"} size="sm">
          {yoyPositive ? <TrendingUp size={11} /> : <TrendingDown size={11} />}{" "}
          {yoyLabel}
        </Chip>
      </div>
      <div className="mt-1">
        <Micro className="mb-1 block">Where you sit in market scale</Micro>
        <div className="relative h-7">
          <div
            className="absolute left-0 right-0 h-1.5 rounded-full border border-rule-strong"
            style={{
              top: 12,
              background:
                "linear-gradient(to right, var(--color-surface) 0%, var(--color-aux-soft) 50%, var(--color-aux) 100%)",
            }}
          />
          <Micro className="absolute left-0" style={{ top: 22, fontSize: 9.5 }}>
            Small
          </Micro>
          <Micro
            className="absolute left-1/2 -translate-x-1/2"
            style={{ top: 22, fontSize: 9.5 }}
          >
            Mid-market
          </Micro>
          <Micro className="absolute right-0" style={{ top: 22, fontSize: 9.5 }}>
            Large
          </Micro>
          <div
            className="absolute -translate-x-1/2 flex flex-col items-center"
            style={{ left: `${pinPct}%`, top: 0 }}
          >
            <span className="rounded bg-aux px-1.5 py-0.5 text-[10px] font-semibold text-white">
              YOU
            </span>
            <div className="h-3 w-0.5 bg-aux" />
          </div>
        </div>
      </div>
      <Caption className="mt-auto">2 states · diversified</Caption>
    </Card>
  );
});

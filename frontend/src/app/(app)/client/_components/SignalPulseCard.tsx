import { memo } from "react";
import { Lightbulb, TrendingDown } from "lucide-react";
import { Card } from "@/components/ui/card";
import { Chip } from "@/components/ui/chip";
import { Eyebrow, Body, Micro } from "@/components/ui/typography";
import { cn } from "@/lib/utils";
import type { ImpactBreakdown, SignalImpact } from "@/types/portal";

interface PulseRow {
  label: string;
  value: number;
  max: number;
}

const FALLBACK_HELPING: PulseRow[] = [
  { label: "MFA on admins", value: 12100, max: 12100 },
  { label: "No prior claims (5y)", value: 9300, max: 12100 },
  { label: "EDR coverage 95%+", value: 6700, max: 12100 },
];
const FALLBACK_OPPORTUNITY: PulseRow[] = [
  { label: "SOC 2 Type II", value: 18200, max: 18200 },
  { label: "Backup encryption", value: 11400, max: 18200 },
  { label: "Public RDP exposed", value: 6200, max: 18200 },
];
const FALLBACK_HELPING_DELTA = "−$28.1k";
const FALLBACK_OPPORTUNITY_DELTA = "+$40.7k";

const PULSE_MAX_ROWS = 3;

function deltaLabel(total: number, sign: "+" | "−"): string {
  return `${sign}$${(Math.abs(total) / 1000).toFixed(1)}k`;
}

function impactsToRows(impacts: SignalImpact[]): PulseRow[] {
  const rows = impacts.slice(0, PULSE_MAX_ROWS).map((s) => ({
    label: s.signal_label,
    value: Math.abs(s.premium_delta_usd),
    max: 1,
  }));
  const max = rows.reduce((m, r) => Math.max(m, r.value), 0) || 1;
  return rows.map((r) => ({ ...r, max }));
}

export const SignalPulseCard = memo(function SignalPulseCard({
  breakdown,
  loading,
}: {
  breakdown: ImpactBreakdown | null;
  loading: boolean;
}) {
  const hasReal =
    !!breakdown &&
    (breakdown.strengths.length > 0 || breakdown.drags.length > 0);

  const helping = hasReal ? impactsToRows(breakdown!.strengths) : FALLBACK_HELPING;
  const opportunity = hasReal ? impactsToRows(breakdown!.drags) : FALLBACK_OPPORTUNITY;

  const helpingDelta = hasReal
    ? deltaLabel(
        breakdown!.strengths.reduce((s, r) => s + r.premium_delta_usd, 0),
        "−",
      )
    : FALLBACK_HELPING_DELTA;
  const opportunityDelta = hasReal
    ? deltaLabel(
        breakdown!.drags.reduce((s, r) => s + r.premium_delta_usd, 0),
        "+",
      )
    : FALLBACK_OPPORTUNITY_DELTA;

  return (
    <Card pad="lg">
      <div className="mb-3 flex items-baseline justify-between">
        <div>
          <Eyebrow>Signal pulse</Eyebrow>
          <h3 className="mt-1 font-display text-[18px] font-semibold leading-none text-ink">
            What&apos;s moving your premium
          </h3>
        </div>
        <Micro>cyber · primary line</Micro>
      </div>
      {loading && !breakdown ? (
        <Body className="italic">Loading signal contributions…</Body>
      ) : (
        <div className="grid gap-6 sm:grid-cols-2">
          <PulseColumn
            heading="Helping"
            headingChip="pos"
            headingIcon={<TrendingDown size={12} />}
            deltaLabel={helpingDelta}
            accent="bg-pos"
            rows={helping}
            sign="−"
            deltaClass="text-pos"
          />
          <PulseColumn
            heading="Opportunity"
            headingChip="spot"
            headingIcon={<Lightbulb size={12} />}
            deltaLabel={opportunityDelta}
            accent="bg-spot"
            rows={opportunity}
            sign="+"
            deltaClass="text-spot-deep dark:text-spot"
          />
        </div>
      )}
    </Card>
  );
});

function PulseColumn({
  heading,
  headingChip,
  headingIcon,
  deltaLabel,
  accent,
  rows,
  sign,
  deltaClass,
}: {
  heading: string;
  headingChip: "pos" | "spot";
  headingIcon: React.ReactNode;
  deltaLabel: string;
  accent: string;
  rows: PulseRow[];
  sign: "+" | "−";
  deltaClass: string;
}) {
  return (
    <div>
      <div className="mb-2 flex items-center justify-between">
        <Chip variant={headingChip} size="sm">
          {headingIcon}
          {heading}
        </Chip>
        <span className={cn("text-[13px] font-semibold tabular-nums", deltaClass)}>
          {deltaLabel}
        </span>
      </div>
      {rows.map((r) => (
        <div key={r.label} className="mt-2.5">
          <div className="flex justify-between gap-2 text-[12.5px]">
            <span className="overflow-hidden text-ellipsis whitespace-nowrap text-ink-soft">
              {r.label}
            </span>
            <span className={cn("shrink-0 font-semibold tabular-nums", deltaClass)}>
              {sign}${(r.value / 1000).toFixed(1)}k
            </span>
          </div>
          <div className="mt-1 h-1 overflow-hidden rounded-full bg-surface-sunken">
            <div
              className={cn("h-full rounded-full", accent)}
              style={{ width: `${(r.value / r.max) * 100}%` }}
            />
          </div>
        </div>
      ))}
    </div>
  );
}

import { memo, useMemo } from "react";
import { ArrowDown, ArrowUp, Check, TrendingDown, TrendingUp } from "lucide-react";
import { Card } from "@/components/ui/card";
import { Chip } from "@/components/ui/chip";
import { Eyebrow, NumDisplay } from "@/components/ui/typography";
import { ScoreHistory, type ScorePoint } from "@/components/charts/score-history";
import type { ClientCoverageEntry } from "@/types/portal";

export const ScoreCard = memo(function ScoreCard({
  hero,
}: {
  hero?: ClientCoverageEntry;
}) {
  const score = hero?.composite_score ?? null;
  const median = hero?.peer_cohort_median_score ?? 714;
  const prev = hero?.previous_composite_score ?? 706;
  const history: ScorePoint[] = useMemo(() => {
    const real = hero?.score_history;
    if (real && real.length > 0) {
      const last = real.length - 1;
      return real.map((p, i): ScorePoint => ({
        label: `v${p.version_number}`,
        value: p.composite_score,
        marker: i === last ? "now" : i === last - 1 ? "prev" : undefined,
      }));
    }
    return [
      { label: "Q1", value: 692 },
      { label: "Q2", value: 705 },
      { label: "Q3", value: 712 },
      { label: "prev", value: prev, marker: "prev" },
      { label: "now", value: score ?? prev, marker: "now" },
    ];
  }, [hero?.score_history, prev, score]);
  const vsMedian = score != null ? Math.round(score - median) : null;
  const vsPrev = score != null ? Math.round(score - prev) : null;

  return (
    <Card variant="info" pad="lg" className="flex flex-col">
      <Eyebrow className="text-info-deep dark:text-info">
        Your signal score
      </Eyebrow>
      <div className="mt-2 flex items-start gap-5">
        <NumDisplay size="xl" className="text-info">
          {score != null ? score.toFixed(0) : "—"}
        </NumDisplay>
        <div className="flex flex-col gap-1.5 pt-1">
          {vsMedian != null && (
            <Chip variant={vsMedian >= 0 ? "pos" : "neg"} size="sm" className="self-start">
              {vsMedian >= 0 ? <ArrowUp size={11} /> : <ArrowDown size={11} />}
              {vsMedian >= 0 ? "+" : ""}
              {vsMedian} vs median
            </Chip>
          )}
          {vsPrev != null && (
            <Chip variant={vsPrev >= 0 ? "pos" : "neg"} size="sm" className="self-start">
              {vsPrev >= 0 ? <TrendingUp size={11} /> : <TrendingDown size={11} />}
              {vsPrev >= 0 ? "+" : ""}
              {vsPrev} since last quote
            </Chip>
          )}
        </div>
      </div>
      <div className="mt-4 min-h-[120px] flex-1">
        <ScoreHistory history={history} height={140} />
      </div>
      <div className="mt-3 flex flex-wrap gap-2 border-t border-info/30 pt-3">
        <Chip variant="mute" size="sm">
          <Check size={12} /> Standard tier
        </Chip>
        <Chip variant="info" size="sm">
          <TrendingUp size={12} /> 64th percentile
        </Chip>
      </div>
    </Card>
  );
});

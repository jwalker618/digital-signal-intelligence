import { memo } from "react";
import { Card } from "@/components/ui/card";
import { Eyebrow, Micro } from "@/components/ui/typography";
import { CohortBar } from "@/components/charts/cohort-bar";
import type { ClientCoverageEntry } from "@/types/portal";

export const CohortStandingCard = memo(function CohortStandingCard({
  hero,
}: {
  hero?: ClientCoverageEntry;
}) {
  const score = hero?.composite_score ?? 724;
  const median = hero?.peer_cohort_median_score ?? 714;
  const topDecile = hero?.peer_cohort_top_decile ?? 784;
  const range: [number, number] = [
    hero?.peer_cohort_min ?? 600,
    hero?.peer_cohort_max ?? 880,
  ];
  const peerCount = hero?.peer_cohort_size ?? 38;
  const vsMedian = Math.round(score - median);
  const toTopDecile = Math.max(0, Math.round(topDecile - score));

  return (
    <Card pad="lg" className="flex flex-col">
      <div className="flex items-baseline justify-between">
        <div>
          <Eyebrow>Cohort standing</Eyebrow>
          <h3 className="mt-1 font-display text-[18px] font-semibold leading-tight text-ink">
            You sit at the{" "}
            <span className="text-pos">
              {hero?.peer_percentile_rank
                ? `${Math.round(hero.peer_percentile_rank * 100)}th`
                : "64th"}{" "}
              percentile
            </span>
          </h3>
        </div>
        <Micro>{peerCount} peers</Micro>
      </div>
      <div className="my-5 flex flex-1 items-center">
        <CohortBar
          value={score}
          median={median}
          topDecile={topDecile}
          range={range}
          className="w-full"
        />
      </div>
      <div className="grid grid-cols-3 gap-2 border-t border-rule pt-3">
        <div>
          <Micro>vs median</Micro>
          <p className="mt-0.5 text-lg font-semibold tabular-nums text-pos">
            {vsMedian >= 0 ? "+" : ""}
            {vsMedian}
          </p>
        </div>
        <div>
          <Micro>your score</Micro>
          <p className="mt-0.5 text-lg font-semibold tabular-nums text-info">
            {score.toFixed(0)}
          </p>
        </div>
        <div>
          <Micro>to top decile</Micro>
          <p className="mt-0.5 text-lg font-semibold tabular-nums text-ink">
            {toTopDecile}
          </p>
        </div>
      </div>
    </Card>
  );
});

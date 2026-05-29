"use client";

import { TrendingUpDown } from "lucide-react";
import { Card } from "@/components/ui/card";
import { Chip } from "@/components/ui/chip";
import { WorkArea } from "@/components/ui/work-area";
import { Body } from "@/components/ui/typography";
import { KpiSnug } from "@/components/ui/kpi-snug";
import { ScoreHistory, type ScorePoint } from "@/components/charts/score-history";
import { useClientWorkbench } from "../_lib/context";

export default function ScoreCohortPage() {
  const cw = useClientWorkbench();
  if (!cw) return null;
  const c = cw.coverages[0];
  if (!c) {
    return (
      <WorkArea>
        <Card pad="lg">
          <Body className="italic">No coverage to score.</Body>
        </Card>
      </WorkArea>
    );
  }

  const history: ScorePoint[] = (c.score_history ?? []).map((p, i, arr): ScorePoint => ({
    label: `v${p.version_number}`,
    value: p.composite_score,
    marker: i === arr.length - 1 ? "now" : i === arr.length - 2 ? "prev" : undefined,
  }));
  const delta = c.prev_score != null && c.score != null ? Math.round(c.score - c.prev_score) : null;

  return (
    <WorkArea>
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-6">
        <Card pad="sm">
          <KpiSnug
            label="Composite"
            value={c.score != null ? c.score.toFixed(0) : "—"}
            tone="info"
          />
        </Card>
        <Card pad="sm">
          <KpiSnug label="Tier" value={c.tier != null ? `T${c.tier}` : "—"} />
        </Card>
        <Card pad="sm">
          <KpiSnug
            label="Percentile"
            value={c.percentile != null ? `${Math.round(c.percentile * 100)}th` : "—"}
          />
        </Card>
        <Card pad="sm">
          <KpiSnug label="Cohort median" value={c.cohort_median ?? "—"} />
        </Card>
        <Card pad="sm">
          <KpiSnug label="Pure score" value={c.pure != null ? c.pure.toFixed(0) : "—"} />
        </Card>
        <Card pad="sm">
          <KpiSnug
            label="vs last"
            value={delta != null ? `${delta >= 0 ? "+" : ""}${delta}` : "—"}
            tone={delta != null && delta >= 0 ? "pos" : "default"}
          />
        </Card>
      </div>

      <Card
        header={`Score history · ${c.line}`}
        icon={TrendingUpDown}
        pad="md"
        headerRight={
          delta != null ? (
            <Chip variant={delta >= 0 ? "pos" : "warn"} size="sm">
              {delta >= 0 ? "+" : ""}
              {delta} vs last
            </Chip>
          ) : undefined
        }
      >
        {history.length > 0 ? (
          <ScoreHistory history={history} height={180} />
        ) : (
          <Body className="italic">No score history on this coverage yet.</Body>
        )}
      </Card>
    </WorkArea>
  );
}

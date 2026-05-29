"use client";

import { ListChecks, TrendingUpDown } from "lucide-react";
import { Card } from "@/components/ui/card";
import { Chip } from "@/components/ui/chip";
import { WorkArea } from "@/components/ui/work-area";
import { Body, Micro } from "@/components/ui/typography";
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

      <div className="grid gap-3.5 lg:grid-cols-[1.3fr_1fr]">
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
          {c.cohort_median != null && (
            <Micro className="mt-2 block">
              Cohort median {c.cohort_median.toFixed(0)} · you{" "}
              {c.score != null
                ? `${c.score >= c.cohort_median ? "+" : ""}${Math.round(c.score - c.cohort_median)}`
                : "—"}
            </Micro>
          )}
        </Card>

        <Card header="Impact breakdown" icon={ListChecks} pad="md" headerRight={<Chip variant="default" size="sm">top drivers</Chip>}>
          {c.impact && c.impact.length > 0 ? (
            <div className="flex flex-col gap-2.5">
              {c.impact.map((it) => {
                const maxAbs = Math.max(...c.impact!.map((x) => Math.abs(x.delta)), 1);
                const pctW = (Math.abs(it.delta) / maxAbs) * 50;
                return (
                  <div
                    key={it.label}
                    className="grid grid-cols-[1fr_120px_56px] items-center gap-2"
                  >
                    <span className="truncate text-[12px] text-ink-soft">{it.label}</span>
                    <div className="relative h-2">
                      <div className="absolute left-1/2 top-0 bottom-0 w-px bg-rule" />
                      <div
                        className={`absolute top-[1px] h-1.5 rounded-sm ${it.direction === "up" ? "bg-pos" : "bg-neg"}`}
                        style={
                          it.direction === "up"
                            ? { left: "50%", width: `${pctW}%` }
                            : { right: "50%", width: `${pctW}%` }
                        }
                      />
                    </div>
                    <span
                      className={`text-right text-[12px] font-bold tabular-nums ${it.direction === "up" ? "text-pos" : "text-neg"}`}
                    >
                      {it.delta > 0 ? "+" : "−"}
                      {Math.abs(it.delta) >= 1000
                        ? `$${(Math.abs(it.delta) / 1000).toFixed(1)}k`
                        : Math.abs(it.delta)}
                    </span>
                  </div>
                );
              })}
            </div>
          ) : (
            <Body className="italic">No signal impact on this coverage yet.</Body>
          )}
        </Card>
      </div>
    </WorkArea>
  );
}

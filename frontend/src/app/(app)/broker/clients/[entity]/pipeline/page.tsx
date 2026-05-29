"use client";

import { Fragment } from "react";
import { Check, ChartPie, GitBranch } from "lucide-react";
import { Card } from "@/components/ui/card";
import { Chip } from "@/components/ui/chip";
import { WorkArea } from "@/components/ui/work-area";
import { Body } from "@/components/ui/typography";
import { useClientWorkbench } from "../_lib/context";
import { kFmt, DOT_BG, NUM_TEXT } from "../_lib/helpers";

const STAGES = ["Submitted", "Scored", "Referred", "Quoted", "Bound"];

// Derive the furthest-reached stage index from decision + status.
function stageFor(decision: string | null | undefined, tone: string): number {
  if (tone === "pos") return 4; // Bound
  if ((decision ?? "").toLowerCase() === "refer") return 2; // Referred
  if ((decision ?? "").toLowerCase() === "approve") return 3; // Quoted
  return 1; // Scored
}

export default function PipelineRenewalsPage() {
  const cw = useClientWorkbench();
  if (!cw) return null;

  const stateMix = [
    { label: "Bound", n: cw.coverages.filter((c) => c.status_tone === "pos").length, tone: "pos" },
    { label: "Referred", n: cw.coverages.filter((c) => c.decision === "refer").length, tone: "spot" },
    { label: "Declined", n: cw.coverages.filter((c) => c.decision === "decline").length, tone: "neg" },
  ];

  return (
    <WorkArea>
      <Card
        header="Placement pipeline"
        icon={GitBranch}
        pad="md"
        headerRight={<Chip variant="default" size="sm">{cw.coverages.length} coverages</Chip>}
      >
        <div className="flex flex-col gap-4">
          {cw.coverages.map((c) => {
            const stageIdx = stageFor(c.decision, c.status_tone);
            return (
              <div key={c.code}>
                <div className="mb-2 flex items-center gap-2">
                  <span className="text-[13px] font-bold">{c.line}</span>
                  <span className="text-[11px] text-ink-mute">{c.carrier ?? "—"}</span>
                  <span className="flex-1" />
                  <Chip variant={c.status_tone as "pos" | "spot" | "neg" | "mute"} size="sm">
                    {c.status}
                  </Chip>
                </div>
                <div className="flex items-center">
                  {STAGES.map((s, i) => {
                    const done = i <= stageIdx;
                    const isCur = i === stageIdx;
                    return (
                      <Fragment key={s}>
                        <div className="flex min-w-0 flex-col items-center gap-1.5">
                          <div
                            className={`flex h-4 w-4 shrink-0 items-center justify-center rounded-full border-2 ${
                              done
                                ? isCur
                                  ? "border-spot bg-spot"
                                  : "border-pos bg-pos"
                                : "border-rule-strong bg-surface-sunken"
                            }`}
                          >
                            {done && !isCur && <Check size={9} className="text-white" />}
                          </div>
                          <span
                            className={`text-[10px] ${
                              isCur
                                ? "font-bold text-spot"
                                : done
                                  ? "text-ink"
                                  : "text-ink-mute"
                            }`}
                          >
                            {s}
                          </span>
                        </div>
                        {i < STAGES.length - 1 && (
                          <div
                            className={`-mt-4 h-0.5 flex-1 ${i < stageIdx ? "bg-pos" : "bg-rule"}`}
                          />
                        )}
                      </Fragment>
                    );
                  })}
                </div>
              </div>
            );
          })}
        </div>
      </Card>

      <div className="grid gap-3.5 lg:grid-cols-[1.4fr_1fr]">
        <Card header="Coverage premiums" icon={GitBranch} pad="md">
          <div className="grid grid-cols-[1fr_1.3fr_110px] border-b border-rule pb-2 text-[10.5px] uppercase tracking-wider text-ink-mute">
            {["Line", "Carrier", "Premium"].map((h) => (
              <span key={h}>{h}</span>
            ))}
          </div>
          {cw.coverages.map((c, i) => (
            <div
              key={c.code}
              className={`grid grid-cols-[1fr_1.3fr_110px] items-center py-2.5 text-[13px] ${
                i < cw.coverages.length - 1 ? "border-b border-rule" : ""
              }`}
            >
              <span className="font-semibold">{c.line}</span>
              <span className="text-ink-soft">{c.carrier ?? "—"}</span>
              <span className="font-semibold tabular-nums">{kFmt(c.premium)}</span>
            </div>
          ))}
          {cw.coverages.length === 0 && <Body className="italic">No coverages.</Body>}
        </Card>

        <Card header="Pipeline state" icon={ChartPie} pad="md">
          <div className="mt-0.5 flex flex-col gap-2.5">
            {stateMix.map((s) => (
              <div key={s.label} className="flex items-center gap-2.5">
                <span className={`h-2 w-2 shrink-0 rounded-full ${DOT_BG[s.tone]}`} />
                <span className="flex-1 text-[13px]">{s.label}</span>
                <span className={`text-[15px] font-bold tabular-nums ${NUM_TEXT[s.tone]}`}>
                  {s.n}
                </span>
              </div>
            ))}
          </div>
        </Card>
      </div>
    </WorkArea>
  );
}

"use client";

import { CheckCircle2, Clock } from "lucide-react";
import { WorkArea } from "@/components/ui/work-area";
import { Chip } from "@/components/ui/chip";
import { Micro } from "@/components/ui/typography";
import { useClientWorkbench } from "../_lib/context";
import { kFmt, tierTone, TIER_BG, decisionTone, pct } from "../_lib/helpers";

const TIER_BORDER: Record<string, string> = {
  pos: "border-l-pos",
  info: "border-l-info",
  warn: "border-l-warn",
  neg: "border-l-neg",
  mute: "border-l-rule",
};

export default function CoverageListPage() {
  const cw = useClientWorkbench();
  if (!cw) return null;

  return (
    <WorkArea className="gap-3.5">
      {cw.coverages.map((c) => (
        <div
          key={c.code}
          className={`rounded-card border border-rule border-l-4 bg-surface p-[18px] ${TIER_BORDER[tierTone(c.tier)]}`}
        >
          <div className="grid grid-cols-1 items-center gap-5 lg:grid-cols-[1.4fr_1fr_1fr_1.3fr]">
            {/* identity */}
            <div>
              <div className="mb-1 flex items-center gap-2">
                <span className="text-[16px] font-bold">{c.line}</span>
                <Chip variant={decisionTone(c.decision)} size="sm">
                  {c.decision ?? "—"}
                </Chip>
              </div>
              <Micro>
                {c.carrier ?? "—"} · <span className="font-mono">{c.code}</span>
              </Micro>
              <div
                className={`mt-2 flex items-center gap-1.5 text-[12px] ${
                  c.status_tone === "pos" ? "text-pos" : "text-spot"
                }`}
              >
                {c.status_tone === "pos" ? <CheckCircle2 size={13} /> : <Clock size={13} />}
                {c.status}
              </div>
            </div>
            {/* score */}
            <div>
              <Micro>Signal score</Micro>
              <div className="mt-0.5 flex items-baseline gap-2">
                <span className="font-mono text-[26px] tabular-nums text-info">
                  {c.score != null ? c.score.toFixed(0) : "—"}
                </span>
                {c.tier != null && (
                  <span
                    className={`inline-flex h-[22px] min-w-[22px] items-center justify-center rounded-md px-1.5 text-[12px] font-bold ${TIER_BG[tierTone(c.tier)]}`}
                  >
                    T{c.tier}
                  </span>
                )}
              </div>
              <Micro className="mt-1 block">
                {[c.tier_label, c.percentile != null ? `${Math.round(c.percentile * 100)}th pct` : null, c.confidence != null ? `${pct(c.confidence)} conf.` : null]
                  .filter(Boolean)
                  .join(" · ")}
              </Micro>
            </div>
            {/* commercial */}
            <div>
              <Micro>Premium</Micro>
              <div className="mt-0.5 font-mono text-[22px] tabular-nums">{kFmt(c.premium)}</div>
              <Micro className="mt-1 block">
                limit {kFmt(c.limit)} · ded {kFmt(c.deductible)}
              </Micro>
            </div>
            {/* signal coverage */}
            <div>
              <Micro>Signal coverage</Micro>
              <div className="mt-1 flex items-baseline gap-2">
                <span className="font-mono text-[18px] tabular-nums">
                  {c.signal_coverage != null ? pct(c.signal_coverage) : "—"}
                </span>
                <Micro>of expected signals</Micro>
              </div>
              <div className="mt-2 h-[5px] overflow-hidden rounded-sm bg-rule">
                <div
                  className={`h-full ${(c.signal_coverage ?? 0) >= 0.85 ? "bg-pos" : "bg-warn"}`}
                  style={{ width: `${(c.signal_coverage ?? 0) * 100}%` }}
                />
              </div>
              {c.awaiting && (
                <Micro
                  className={`mt-2 block ${c.awaiting === "broker" ? "text-spot" : "text-info"}`}
                >
                  {c.awaiting === "broker" ? "Awaiting you" : "Awaiting client"}
                </Micro>
              )}
            </div>
          </div>
        </div>
      ))}
    </WorkArea>
  );
}

"use client";

import { Lightbulb, TriangleAlert } from "lucide-react";
import { Card } from "@/components/ui/card";
import { Chip } from "@/components/ui/chip";
import { WorkArea } from "@/components/ui/work-area";
import { Body, Micro } from "@/components/ui/typography";
import { useClientWorkbench } from "../_lib/context";

type RiskFlag = { flag: string; detail: string; sev: "high" | "med" };

const SEV_BORDER: Record<string, string> = {
  high: "border-l-neg",
  med: "border-l-warn",
};
const SEV_TEXT: Record<string, string> = {
  high: "text-neg",
  med: "text-warn",
};

export default function OpportunitiesRisksPage() {
  const cw = useClientWorkbench();
  if (!cw) return null;

  // Risk flags derived from real coverage data (no fabricated peer adds).
  const risks: RiskFlag[] = [];
  for (const c of cw.coverages) {
    if (c.tier != null && c.tier >= 4) {
      risks.push({
        flag: `${c.line} in Tier ${c.tier}`,
        detail: `${c.line} scores ${c.score?.toFixed(0) ?? "—"} (T${c.tier}). Renewal pricing pressure likely — pre-empt with the carrier.`,
        sev: "high",
      });
    }
    if (c.signal_coverage != null && c.signal_coverage < 0.85) {
      risks.push({
        flag: `${c.line} signal coverage ${Math.round(c.signal_coverage * 100)}%`,
        detail: `Below the 85% threshold — missing evidence is dragging the ${c.line} assessment.`,
        sev: "med",
      });
    }
    if (c.awaiting === "broker") {
      risks.push({
        flag: `${c.line} awaiting you`,
        detail: `An open referral on ${c.line} (${c.code}) is waiting on broker action.`,
        sev: "med",
      });
    }
  }

  const lines = new Set(cw.coverages.map((c) => c.line));

  return (
    <WorkArea className="lg:grid-cols-2">
      <Card
        header="Opportunities"
        icon={Lightbulb}
        pad="md"
        headerRight={<Chip variant="info" size="sm">coverage shape</Chip>}
      >
        <Micro className="mb-3 block">
          {cw.entity_name} currently carries {lines.size} coverage line
          {lines.size === 1 ? "" : "s"}: {[...lines].join(", ")}.
        </Micro>
        <Body className="text-[13px] text-ink-soft">
          Cross-sell opportunities are surfaced from cohort coverage-mix
          analysis — connect a peer-portfolio source to populate concrete
          gap recommendations here.
        </Body>
      </Card>

      <Card
        header="Risk flags"
        icon={TriangleAlert}
        pad="md"
        headerRight={
          <Chip variant="spot" size="sm">
            {risks.length} flagged
          </Chip>
        }
      >
        {risks.length === 0 ? (
          <Body className="italic">No risk flags on this client.</Body>
        ) : (
          <div className="flex flex-col gap-3">
            {risks.map((r, i) => (
              <div
                key={i}
                className={`rounded-card border border-rule border-l-4 p-3.5 ${SEV_BORDER[r.sev]}`}
              >
                <div className="mb-1.5 flex items-baseline justify-between">
                  <span className="text-[14px] font-bold">{r.flag}</span>
                  <span
                    className={`rounded-chip border px-2 py-0.5 text-[10px] uppercase ${SEV_TEXT[r.sev]}`}
                  >
                    {r.sev}
                  </span>
                </div>
                <Body className="text-[12.5px] leading-relaxed text-ink-soft">
                  {r.detail}
                </Body>
              </div>
            ))}
          </div>
        )}
      </Card>
    </WorkArea>
  );
}

import { memo, useMemo } from "react";
import { Check, Circle } from "lucide-react";
import { Card } from "@/components/ui/card";
import { Chip } from "@/components/ui/chip";
import { Eyebrow, Micro } from "@/components/ui/typography";
import type { ClientCoverageEntry } from "@/types/portal";

const TYPICAL_PEER_LINES = [
  { line: "Property", peerPct: 78 },
  { line: "GL", peerPct: 65 },
  { line: "Crime", peerPct: 42 },
];

export const CoverageShapeCard = memo(function CoverageShapeCard({
  coverages,
}: {
  coverages: ClientCoverageEntry[];
}) {
  const held = useMemo(() => {
    const seen = new Set<string>();
    return coverages
      .map((c) => c.coverage)
      .filter((c) => {
        if (seen.has(c)) return false;
        seen.add(c);
        return true;
      });
  }, [coverages]);
  const gaps = TYPICAL_PEER_LINES.filter((g) => !held.includes(g.line));
  const total = held.length + gaps.length;
  return (
    <Card pad="lg" className="flex h-full flex-col gap-2.5">
      <div className="flex items-baseline justify-between">
        <div>
          <Eyebrow>Coverage shape</Eyebrow>
          <p className="mt-1 text-xl font-semibold text-ink">
            {held.length} of {total} typical lines
          </p>
        </div>
        {gaps.length > 0 && (
          <Chip variant="spot" size="sm">
            {gaps.length} typical adds
          </Chip>
        )}
      </div>
      <div>
        <Micro className="mb-1.5 block">Held</Micro>
        <div className="flex flex-wrap gap-1.5">
          {held.length === 0 ? (
            <Micro>—</Micro>
          ) : (
            held.map((l) => (
              <Chip key={l} variant="pos" size="sm">
                <Check size={11} /> {l}
              </Chip>
            ))
          )}
        </div>
      </div>
      <div className="mt-auto">
        <Micro className="mb-1.5 block">Often added by peers</Micro>
        <div className="flex flex-wrap gap-1.5">
          {gaps.map((g) => (
            <span
              key={g.line}
              className="inline-flex items-center gap-1.5 rounded-chip border border-dashed border-rule-strong px-2.5 py-1 text-[11.5px] text-ink-soft"
            >
              <Circle size={11} /> {g.line}
              <span className="ml-0.5 text-[10px] opacity-60">{g.peerPct}%</span>
            </span>
          ))}
        </div>
      </div>
    </Card>
  );
});

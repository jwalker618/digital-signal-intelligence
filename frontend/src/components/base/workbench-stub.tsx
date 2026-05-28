"use client";

import { Sparkles } from "lucide-react";
import { WorkbenchTopbar } from "@/components/chrome/workbench-topbar";
import { Card } from "@/components/ui/card";
import { Eyebrow, Body, Micro } from "@/components/ui/typography";

/**
 * Placeholder for a workbench tab whose UI hasn't been ported yet. Renders
 * the standard workbench topbar (so submission context stays visible) and
 * a single card explaining what the tab will show.
 */
export function WorkbenchStub({
  title,
  description,
  shipsWith,
}: {
  title: string;
  description: string;
  shipsWith?: string[];
}) {
  return (
    <>
      <WorkbenchTopbar activeTabLabel={title} />
      <div className="flex flex-1 items-start justify-center overflow-y-auto px-9 py-12">
        <Card variant="info" pad="lg" className="max-w-2xl space-y-5">
          <div className="flex items-center gap-2 text-info">
            <Sparkles size={16} />
            <Eyebrow className="text-info">Up next</Eyebrow>
          </div>
          <div>
            <h1 className="font-display text-[28px] font-semibold leading-tight text-ink">
              {title}
            </h1>
            <Body className="mt-2">{description}</Body>
          </div>
          {shipsWith && shipsWith.length > 0 && (
            <ul className="space-y-1.5 border-t border-info/30 pt-4">
              {shipsWith.map((b) => (
                <li
                  key={b}
                  className="flex items-start gap-2 text-[13px] text-ink"
                >
                  <span className="mt-2 inline-block h-1.5 w-1.5 shrink-0 rounded-full bg-info" />
                  {b}
                </li>
              ))}
            </ul>
          )}
          <Micro className="block">
            Submission context above stays live as you tab; the canonical UI
            ships in the next pass.
          </Micro>
        </Card>
      </div>
    </>
  );
}

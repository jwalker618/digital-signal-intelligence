"use client";

/**
 * SummaryTab — dashboard composition for a submission.
 *
 * Every panel is a named section from `content/sections.ts` rendered through
 * SectionCard (StandardCard or PopupCard), with the decision banner itself
 * as a SubmissionHeaderCard.
 */

import "@/app/globals.css";

import { useDsiStore } from "@/store/dsiStore";

import {
  CardGrid,
  SectionCard,
  SubmissionHeaderCard,
  Decision,
} from "@/components/base/cards";

import DecisionStatusFields from "./content/DecisionStatusFields";
import HeroMetricsGrid from "./content/HeroMetricsGrid";
import { useNotesCountTitle } from "./content/NotesPanel";

export default function SummaryTab() {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const activeVersion = useDsiStore((s) => s.activeVersion) as any;

  const decision: Decision = (
    (activeVersion?.decision || "pending").toLowerCase()
  ) as Decision;
  const subtitle = activeVersion?.auto_approve
    ? "Auto-approved by engine"
    : undefined;

  const notesTitle = useNotesCountTitle();

  return (
    <div className="w-full no-scrollbar animate-in fade-in duration-500 pb-12">
      <CardGrid>
        <SubmissionHeaderCard
          decision={decision}
          title={decision}
          subtitle={subtitle}
          spanClass="col-span-1 md:col-span-2 lg:col-span-3"
          headerRight={<DecisionStatusFields />}
        >
          <HeroMetricsGrid />
        </SubmissionHeaderCard>

        {/* Popups */}
        <SectionCard section="who"       spanClass="col-span-1" />
        <SectionCard section="discovery" spanClass="col-span-1" />

        {/* Three-pillar assessment — full width */}
        <SectionCard
          section="threePillar"
          spanClass="col-span-1 md:col-span-2 lg:col-span-3"
        />

        {/* Commercial + Risk Terms */}
        <SectionCard
          section="commercial"
          spanClass="col-span-1 md:col-span-2 lg:col-span-1"
        />
        <SectionCard
          section="riskTerms"
          spanClass="col-span-1 md:col-span-2 lg:col-span-2"
        />

        {/* Notes — full width */}
        <SectionCard
          section="notes"
          title={notesTitle}
          spanClass="col-span-1 md:col-span-2 lg:col-span-3"
        />
      </CardGrid>
    </div>
  );
}

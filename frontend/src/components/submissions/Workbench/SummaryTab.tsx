"use client";

import "@/app/globals.css";

import { useDsiStore } from "@/store/dsiStore";

import {
  StandardCard,
  PopupCard,
  SubmissionHeaderCard,
  Decision,
} from "@/components/base/cards";
import CardGrid from "@/components/base/cardGrid";
import SectionCard from "@/components/base/sectionCard";

import DecisionStatusFields from "./content/DecisionStatusFields";
import HeroMetricsGrid from "./content/HeroMetricsGrid";
import { useNotesCountTitle } from "./content/NotesPanel";
import { SectionKey } from "./content/sections";

/**
 * Dispatch-by-component config. Each item names the card component it wants
 * to render as, plus the props that card expects. SectionCard is the
 * terse form for any section registered in `content/sections.ts`.
 */
type DashboardItem =
  | ({ id: string; card: typeof SectionCard } & React.ComponentProps<typeof SectionCard>)
  | ({ id: string; card: typeof StandardCard } & React.ComponentProps<typeof StandardCard>)
  | ({ id: string; card: typeof PopupCard } & React.ComponentProps<typeof PopupCard>)
  | ({ id: string; card: typeof SubmissionHeaderCard } & React.ComponentProps<typeof SubmissionHeaderCard>);

const section = (
  id: string,
  key: SectionKey,
  spanClass: string,
  title?: string,
): DashboardItem => ({
  id,
  card: SectionCard,
  section: key,
  spanClass,
  title,
});

export default function SummaryTab() {
  const { activeVersion } = useDsiStore() as any;
  const decision: Decision = (
    (activeVersion?.decision || "pending").toLowerCase()
  ) as Decision;

  const notesTitle = useNotesCountTitle();

  const config: DashboardItem[] = [
    /* ── Decision banner (full width) ─────────────────────────────────── */
    {
      id: "header",
      card: SubmissionHeaderCard,
      decision,
      title: decision,
      subtitle: activeVersion?.auto_approve ? "Auto-approved by engine" : undefined,
      spanClass: "col-span-1 md:col-span-2 lg:col-span-3",
      headerRight: <DecisionStatusFields />,
      children: <HeroMetricsGrid />,
    },

    /* ── Named sections ───────────────────────────────────────────────── */
    section("who", "who", "col-span-1"),
    section("discovery", "discovery", "col-span-1"),
    section("three-pillar", "threePillar", "col-span-1 md:col-span-2 lg:col-span-3"),
    section("commercial", "commercial", "col-span-1 md:col-span-2 lg:col-span-1"),
    section("risk-terms", "riskTerms", "col-span-1 md:col-span-2 lg:col-span-2"),
    section("notes", "notes", "col-span-1 md:col-span-2 lg:col-span-3", notesTitle),
  ];

  return (
    <div className="w-full no-scrollbar animate-in fade-in duration-500 pb-12">
      <CardGrid>
        {config.map(({ id, card: Card, ...props }) => (
          // eslint-disable-next-line @typescript-eslint/no-explicit-any
          <Card key={id} {...(props as any)} />
        ))}
      </CardGrid>
    </div>
  );
}

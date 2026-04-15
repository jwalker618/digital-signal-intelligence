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

import DecisionStatusFields from "./content/DecisionStatusFields";
import HeroMetricsGrid from "./content/HeroMetricsGrid";
import ThreePillarAssessment from "./content/ThreePillarAssessment";
import CommercialSummary from "./content/CommercialSummary";
import RiskTermsSummary from "./content/RiskTermsSummary";
import NotesPanel, { useNotesCountTitle } from "./content/NotesPanel";
import SubmissionDataList from "./content/SubmissionDataList";
import DiscoveryOutputList from "./content/DiscoveryOutputList";

import {
  Layers,
  Building2,
  Scale,
  MessageSquare,
  User,
  Search,
} from "lucide-react";

/**
 * Dispatch-by-component config. Each item carries the card component it wants
 * to render as, plus the props that card expects.
 */
type DashboardItem =
  | ({ id: string; card: typeof StandardCard } & React.ComponentProps<typeof StandardCard>)
  | ({ id: string; card: typeof PopupCard } & React.ComponentProps<typeof PopupCard>)
  | ({ id: string; card: typeof SubmissionHeaderCard } & React.ComponentProps<typeof SubmissionHeaderCard>);

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

    /* ── Popups ───────────────────────────────────────────────────────── */
    {
      id: "who",
      card: PopupCard,
      title: "Who are they?",
      lucideIcon: User,
      spanClass: "col-span-1",
      children: <SubmissionDataList />,
    },
    {
      id: "discovery",
      card: PopupCard,
      title: "Discovery",
      lucideIcon: Search,
      spanClass: "col-span-1",
      children: <DiscoveryOutputList />,
    },

    /* ── Three-pillar (full width) ────────────────────────────────────── */
    {
      id: "three-pillar",
      card: StandardCard,
      title: "Three Pillar Assessment",
      lucideIcon: Layers,
      spanClass: "col-span-1 md:col-span-2 lg:col-span-3",
      children: <ThreePillarAssessment />,
    },

    /* ── Commercial / Risk terms ──────────────────────────────────────── */
    {
      id: "commercial",
      card: StandardCard,
      title: "Commercial Summary",
      lucideIcon: Building2,
      spanClass: "col-span-1 md:col-span-2 lg:col-span-1",
      children: <CommercialSummary />,
    },
    {
      id: "risk-terms",
      card: StandardCard,
      title: "Risk Terms Summary",
      lucideIcon: Scale,
      spanClass: "col-span-1 md:col-span-2 lg:col-span-2",
      children: <RiskTermsSummary />,
    },

    /* ── Notes (full width) ───────────────────────────────────────────── */
    {
      id: "notes",
      card: StandardCard,
      title: notesTitle,
      lucideIcon: MessageSquare,
      spanClass: "col-span-1 md:col-span-2 lg:col-span-3",
      children: <NotesPanel />,
    },
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

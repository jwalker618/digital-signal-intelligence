import {
  LucideIcon, Building2, Layers, MessageSquare,
  Scale, Search, User,
} from "lucide-react";

import CommercialSummary from "./content/CommercialSummary";
import DiscoveryOutputList from "./content/DiscoveryOutputList";
import NotesPanel from "./content/NotesPanel";
import RiskTermsSummary from "./content/RiskTermsSummary";
import SubmissionDataList from "./content/SubmissionDataList";
import ThreePillarAssessment from "./content/ThreePillarAssessment";

export type SectionWrapper = "card" | "popup";

export interface SectionDefinition {
  title: string;
  icon: LucideIcon;
  content: React.ComponentType;
  wrapper: SectionWrapper;
}

export const SECTIONS = {
  
  commercial: {
    title: "Commercial Summary", icon: Building2, content: CommercialSummary, wrapper: "card",
  },

  riskTerms: {
    title: "Risk Terms Summary", icon: Scale,   content: RiskTermsSummary,   wrapper: "card",
  },

  threePillar: {
    title: "Three Pillar Assessment", icon: Layers, content: ThreePillarAssessment, wrapper: "card",
  },

  notes: {
    title: "Notes", icon: MessageSquare, content: NotesPanel, wrapper: "card",
  },

  who: {
    title: "Who are they?", icon: User, content: SubmissionDataList, wrapper: "popup",
  },

  discovery: {
    title: "Discovery", icon: Search, content: DiscoveryOutputList, wrapper: "popup",
  },
  
} as const satisfies Record<string, SectionDefinition>;

export type SectionKey = keyof typeof SECTIONS;

/**
 * Registry of named content sections for the workbench.
 *
 * Each entry declares the title, icon, body component, and the preferred
 * card wrapper (`card` for StandardCard, `popup` for PopupCard). SectionCard
 * reads this registry and drops the right card/body into place.
 *
 * Add a new row here to make a new section usable from a tab config as
 * `{ section: "my-key" }`.
 */

import {
  LucideIcon,
  Building2,
  Layers,
  MessageSquare,
  Scale,
  Search,
  User,
} from "lucide-react";

import CommercialSummary from "./CommercialSummary";
import DiscoveryOutputList from "./DiscoveryOutputList";
import NotesPanel from "./NotesPanel";
import RiskTermsSummary from "./RiskTermsSummary";
import SubmissionDataList from "./SubmissionDataList";
import ThreePillarAssessment from "./ThreePillarAssessment";

export type SectionWrapper = "card" | "popup";

export interface SectionDefinition {
  title: string;
  icon: LucideIcon;
  content: React.ComponentType;
  wrapper: SectionWrapper;
}

export const SECTIONS = {
  commercial: {
    title: "Commercial Summary",
    icon: Building2,
    content: CommercialSummary,
    wrapper: "card",
  },
  riskTerms: {
    title: "Risk Terms Summary",
    icon: Scale,
    content: RiskTermsSummary,
    wrapper: "card",
  },
  threePillar: {
    title: "Three Pillar Assessment",
    icon: Layers,
    content: ThreePillarAssessment,
    wrapper: "card",
  },
  notes: {
    title: "Notes",
    icon: MessageSquare,
    content: NotesPanel,
    wrapper: "card",
  },
  who: {
    title: "Who are they?",
    icon: User,
    content: SubmissionDataList,
    wrapper: "popup",
  },
  discovery: {
    title: "Discovery",
    icon: Search,
    content: DiscoveryOutputList,
    wrapper: "popup",
  },
} as const satisfies Record<string, SectionDefinition>;

export type SectionKey = keyof typeof SECTIONS;

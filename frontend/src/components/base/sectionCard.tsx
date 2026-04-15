"use client";

/**
 * SectionCard — convenience wrapper that mounts a registered content
 * component inside the card variant declared for it in SECTIONS.
 *
 * Use this from a tab config when the card is a "named section":
 *
 *     { id: "commercial", card: SectionCard, section: "commercial",
 *       spanClass: "col-span-1" }
 *
 * Set `wrapper` to override the default wrapper from the registry (e.g. to
 * force a section that is normally a popup into a full card).
 */

import { StandardCard, PopupCard } from "@/components/base/cards";
import {
  SECTIONS,
  SectionKey,
  SectionWrapper,
} from "@/components/submissions/Workbench/content/sections";

interface SectionCardProps {
  section: SectionKey;
  spanClass?: string;
  /** Override the registry title (e.g. `Notes (3)`). */
  title?: string;
  /** Override the registry wrapper. */
  wrapper?: SectionWrapper;
}

export default function SectionCard({
  section,
  spanClass,
  title,
  wrapper,
}: SectionCardProps) {
  const def = SECTIONS[section];
  const Wrapper = (wrapper ?? def.wrapper) === "popup" ? PopupCard : StandardCard;
  const Body = def.content;

  return (
    <Wrapper
      title={title ?? def.title}
      lucideIcon={def.icon}
      spanClass={spanClass}
    >
      <Body />
    </Wrapper>
  );
}

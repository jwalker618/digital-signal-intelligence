"use client";

import { useState } from "react";

import { ArrowUpRight, LucideIcon } from "lucide-react";

import Modal from "@/components/base/modal";

import {
  SECTIONS,
  SectionKey,
  SectionWrapper,
} from "@/components/submissions/content/summary/sections";

import {
  accentVars,
  getPalette,
  KEYTERM,
} from "@/lib/keytermPalette";

/* ────────────────────────────────────────────────────────────────────────── */
/*  CardGrid — the dashboard responsive grid wrapper.                         */
/* ────────────────────────────────────────────────────────────────────────── */
export interface CardGridProps {
  children: React.ReactNode;
  cols?: string;
  className?: string;
}
export const CardGrid = ({
  children,
  cols = "grid-cols-1 md:grid-cols-2 lg:grid-cols-3",
  className = "",
}: CardGridProps) => {
  return (
    <div className={`grid ${cols} gap-generate-pad ${className}`}>
      {children}
    </div>
  );
}

/**
 * Props shared by every card variant so they are interchangeable from a
 * dashboard config that dispatches on a `card: ComponentRef`.
 */
export interface BaseCardProps {
  title: string;
  lucideIcon?: LucideIcon;
  spanClass?: string;
  children?: React.ReactNode;
  /** Right-aligned slot on the header row — e.g. a count pill or action button. */
  headerRight?: React.ReactNode;
}

/** STANDARD CARD---------------------------------------------------------------------------------------------- */

export const StandardCard = ({
  lucideIcon: Icon,
  title,
  children,
  spanClass = "col-span-1",
  headerRight,
}: BaseCardProps) => {
  return (
    <div className={`flex flex-col h-full ${spanClass}`}>
      <div className="generate-light-sectionheader">
        {Icon && <Icon className="generate-app-icon"/>}
        <span className={`text-sm ${headerRight ? "flex-1" : ""}`}>{title}</span>
        {headerRight}
      </div>
      <div className="generate-light-sectionanalysis">{children}</div>
    </div>
  );
};

/** POPUP CARD---------------------------------------------------------------------------------------------- */

/** GUIDANCE
 * teaser: What is rendered inside the tile in the grid. Defaults to the title
 * modalIcon: Optional override for the icon shown in the modal header.
 */
export interface PopupCardProps extends BaseCardProps {
  teaser?: React.ReactNode;
  modalIcon?: LucideIcon;
}

export const PopupCard = ({
  title,
  lucideIcon,
  modalIcon,
  teaser,
  children,
  spanClass = "col-span-1",
}: PopupCardProps) => {
  const [isOpen, setIsOpen] = useState(false);
  const hasContent = Boolean(children);

  return (
    <>
      <div
        className={`flex flex-col h-full ${spanClass} ${
          hasContent ? "cursor-pointer group" : "opacity-60 cursor-not-allowed"
        }`}
        onClick={() => hasContent && setIsOpen(true)}
        role={hasContent ? "button" : undefined}
        tabIndex={hasContent ? 0 : undefined}
        onKeyDown={(e) => {
          if (hasContent && (e.key === "Enter" || e.key === " ")) {
            e.preventDefault();
            setIsOpen(true);
          }
        }}
      >
        <div className="generate-light-popupheader">
          <span className="text-xs content-center">Expand</span>
          <ArrowUpRight className="generate-app-icon" />
        </div>
        <div className="generate-light-sectionanalysis font-bold">
          {teaser ?? title}
        </div>
      </div>

      {hasContent && (
        <Modal
          isOpen={isOpen}
          onClose={() => setIsOpen(false)}
          title={title}
          icon={modalIcon ?? lucideIcon}
        >
          {children}
        </Modal>
      )}
    </>
  );
};

/** SUBMISSION HEADER CARD---------------------------------------------------------------------------------------------- */

/** GUIDANCE
 * decision: Drives bg colour + default icon
 * subtitle: Right-hand slot on the top row — typically status / dates / refs.
 * headerRight: Right-hand slot on the top row — typically status / dates / refs.
 * children: Bottom slot — the hero-numbers grid (composite score, tier, premium…).
 *           Consumers provide their own grid so the frame stays reusable.
 * lucideIcon: Override the default shield icon chosen from `decision`.
 */
export interface SubmissionHeaderCardProps extends BaseCardProps {
  decision: string;
  subtitle?: React.ReactNode;
  headerRight?: React.ReactNode;
  children?: React.ReactNode;
  lucideIcon?: LucideIcon;
}

export const SubmissionHeaderCard = ({
  decision,
  title,
  subtitle,
  headerRight,
  children,
  lucideIcon,
  spanClass = "",
}: SubmissionHeaderCardProps) => {
  const { color, icon } = getPalette(KEYTERM, decision);
  const Icon = lucideIcon ?? icon;

  return (
    <div className={`
      sticky top-0 z-999
      pt-generate-pad pb-0.5
      bg-generate-light-background
      ${spanClass}
    `}
    >

    <div
      style={accentVars(color)}
      className="
        rounded-xl
        pt-generate-pad pb-generate-pad
        border-b-3 border-generate-text-outline
        bg-generate-light-input
        shadow-sm"
    >
      {/* Top row — decision label + caller-supplied status info */}
      <div className="flex items-center justify-between pb-generate-pad border-b border-generate-text-outline">
        
        <div className="flex gap-4 pl-generate-pad items-center justify-between">
          {Icon && <Icon className="generate-app-icon scale-200 text-[var(--accent)] hover:text-[var(--accent)]" />}
          <div>
            <span className="text-3xl font-bold uppercase tracking-wider text-[var(--accent)]">
              {title}
            </span>
            {subtitle && <span className="block text-xs">{subtitle}</span>}
          </div>
        </div>

        {headerRight && (
          <div className="flex items-center justify-between gap-4 pr-generate-pad text-generate-text-placeholder">{headerRight}</div>
        )}
      </div>
      <div className="pl-generate-pad">
        {/* Bottom row — caller-supplied metrics grid */}
        {children}
      </div>
    </div>

    </div>
  );
};

/** SECTION CARD---------------------------------------------------------------------------------------------- */

/** GUIDANCE
 * title: Override the registry title (e.g. `Notes (3)`).
 * wrapper: Override the registry wrapper.
 */
export interface SectionCardProps {
  section: SectionKey;
  spanClass?: string;
  title?: string;
  wrapper?: SectionWrapper;
}

/**
 * Convenience wrapper that mounts a registered content component inside the
 * card variant declared for it in SECTIONS. Use this from a tab config when
 * the card is a "named section":
 *
 *     { id: "commercial", card: SectionCard, section: "commercial",
 *       spanClass: "col-span-1" }
 *
 * Set `wrapper` to override the default wrapper from the registry (e.g. to
 * force a section that is normally a popup into a full card).
 */
export const SectionCard = ({
  section,
  spanClass,
  title,
  wrapper,
}: SectionCardProps) => {
  
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
};

"use client";

import "@/app/globals.css";
import { useState } from "react";

import { ArrowUpRight, LucideIcon } from "lucide-react";

import Modal from "@/components/base/modal";

import {
  SECTIONS,
  SectionKey,
  SectionWrapper,
} from "@/components/submissions/Workbench/content/sections";

import {
  Decision,
  SUBMISSION_DECISION,
} from "@/lib/statusPalette";

export type { Decision };

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
    <div className={`grid ${cols} gap-dsi-pad ${className}`}>
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
      <div className="dsi-section-header">
        {Icon && <Icon className="icon"/>}
        <span className={`text-sm ${headerRight ? "flex-1" : ""}`}>{title}</span>
        {headerRight}
      </div>
      <div className="dsi-section-analysis">{children}</div>
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
        <div className="dsi-popup-header">
          <span className="text-xs content-center">Expand</span>
          <ArrowUpRight className="icon" />
        </div>
        <div className="dsi-section-analysis font-bold">
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
  decision: Decision;
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
  const Icon = lucideIcon ?? SUBMISSION_DECISION[decision].icon;

  return (
    <div className={`
      sticky top-0 z-999
      pt-dsi-pad pb-0.5
      bg-dsi-background
      ${spanClass}
    `}
    >

    <div
      className={`
        rounded-xl
        pt-dsi-pad pb-dsi-pad
        border-b-3 border-dsi-contrast-background
        ${SUBMISSION_DECISION[decision].bg}
        shadow-sm
      `}
    >
      {/* Top row — decision label + caller-supplied status info */}
      <div className="flex items-center justify-between pb-dsi-pad border-b border-dsi-outline/50">
        <div className="flex gap-4 pl-dsi-pad">
          <Icon className="largeicon" />
          <div>
            <span className="text-2xl font-bold uppercase tracking-wider text-dsi-selected">
              {title}
            </span>
            {subtitle && <span className="block text-xs">{subtitle}</span>}
          </div>
        </div>

        {headerRight && (
          <div className="flex items-center justify-between gap-4 pr-dsi-pad">{headerRight}</div>
        )}
      </div>
      <div className="pl-dsi-pad">
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

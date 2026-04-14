/**
 * Shared card stylings.
 *
 * Composable primitives for the workbench dashboards. All visual treatment is
 * driven by the utilities in `app/globals.css` (dsi-section-header,
 * dsi-section-analysis, dsi-popup-header, bg-dsi-{decision} etc.).
 */

"use client";

import "@/app/globals.css";
import { useState } from "react";
import {
  ArrowUpRight,
  LucideIcon,
  ShieldCheck,
  ShieldQuestionMark,
  ShieldX,
} from "lucide-react";

import Modal from "@/components/base/modal";

/* ────────────────────────────────────────────────────────────────────────── */
/*  Shared types                                                              */
/* ────────────────────────────────────────────────────────────────────────── */

export type Decision = "approve" | "refer" | "decline" | "pending";

/** bg-* class applied to decision-styled surfaces. */
const DECISION_BG: Record<Decision, string> = {
  approve: "bg-dsi-approve",
  refer:   "bg-dsi-refer",
  decline: "bg-dsi-decline",
  pending: "bg-dsi-muted",
};

/** Icon used on the decision banner — matches SummarySAFE semantics. */
const DECISION_ICON: Record<Decision, LucideIcon> = {
  approve: ShieldCheck,
  refer:   ShieldQuestionMark,
  decline: ShieldX,
  pending: ShieldX,
};

/**
 * Props shared by every card variant so they are interchangeable from a
 * dashboard config that dispatches on a `card: ComponentRef`.
 */
export interface BaseCardProps {
  title: string;
  lucideIcon?: LucideIcon;
  spanClass?: string;
  children?: React.ReactNode;
}

/* ────────────────────────────────────────────────────────────────────────── */
/*  StandardCard — section header + body                                      */
/* ────────────────────────────────────────────────────────────────────────── */

export const StandardCard = ({
  lucideIcon: Icon,
  title,
  children,
  spanClass = "col-span-1",
}: BaseCardProps) => {
  return (
    <div className={`flex flex-col h-full ${spanClass}`}>
      <div className="dsi-section-header">
        {Icon && <Icon className="icon" />}
        <span className="text-sm">{title}</span>
      </div>
      <div className="dsi-section-analysis">{children}</div>
    </div>
  );
};

/* ────────────────────────────────────────────────────────────────────────── */
/*  PopupCard — teaser tile that opens a Modal                                */
/* ────────────────────────────────────────────────────────────────────────── */

export interface PopupCardProps extends BaseCardProps {
  /**
   * What is rendered inside the tile in the grid. Defaults to the title,
   * styled with `dsi-section-analysis font-bold`.
   */
  teaser?: React.ReactNode;
  /** Optional override for the icon shown in the modal header. */
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

/* ────────────────────────────────────────────────────────────────────────── */
/*  SubmissionHeaderCard — sticky decision banner frame                       */
/* ────────────────────────────────────────────────────────────────────────── */

export interface SubmissionHeaderCardProps extends BaseCardProps {
  /** Drives bg colour + default icon. */
  decision: Decision;
  /** Secondary label under the decision (e.g. "Auto-approved by engine"). */
  subtitle?: React.ReactNode;
  /** Right-hand slot on the top row — typically status / dates / refs. */
  headerRight?: React.ReactNode;
  /**
   * Bottom slot — the hero-numbers grid (composite score, tier, premium…).
   * Consumers provide their own grid so the frame stays reusable.
   */
  children?: React.ReactNode;
  /** Override the default shield icon chosen from `decision`. */
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
  const Icon = lucideIcon ?? DECISION_ICON[decision];

  return (
    <div
      className={`
        sticky top-dsi-pad z-20 mb-24 bottom-12
        pt-3 pb-2
        rounded-xl
        border-b-3 border-dsi-contrast-background
        ${DECISION_BG[decision]}
        shadow-sm
        ${spanClass}
      `}
    >
      {/* Top row — decision label + caller-supplied status info */}
      <div className="flex items-center justify-between pb-3 border-b border-dsi-outline/50">
        <div className="flex items-center gap-4 pl-dsi-pad">
          <Icon className="w-10 h-10 text-dsi-selected" />
          <div>
            <span className="text-2xl font-bold uppercase tracking-wider text-dsi-selected">
              {title}
            </span>
            {subtitle && <span className="block text-xs">{subtitle}</span>}
          </div>
        </div>

        {headerRight && (
          <div className="flex items-center gap-6 pr-dsi-gap">{headerRight}</div>
        )}
      </div>

      {/* Bottom row — caller-supplied metrics grid */}
      {children}
    </div>
  );
};

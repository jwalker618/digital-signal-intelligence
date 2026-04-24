"use client";

/**
 * Navigation primitives used by the sidebar.
 *
 *  • NavItem     — leaf button with icon + label + active-fill styling.
 *  • NavGroup    — collapsible category header with chevron + children list.
 *  • SidebarIconBtn — minimal icon-only button used for the bottom-row tools.
 *
 * Active/inactive styling is derived from a single `isActive` boolean so
 * route-driven (pathname) and store-driven (activeMenu) call sites render
 * identically.
 */

import { ChevronDown, ChevronRight, LucideIcon } from "lucide-react";

/* ── NavItem ─────────────────────────────────────────────────────────── */

export interface NavItemProps {
  icon: LucideIcon;
  label: string;
  isActive?: boolean;
  onClick?: () => void;
  className?: string;
}

export const NavItem = ({
  icon: Icon,
  label,
  isActive = false,
  onClick,
  className = "",
}: NavItemProps) => (
  <button
    onClick={onClick}
    className={`flex items-center gap-3 w-full text-left py-2 px-2 rounded text-sm ${
      isActive
        ? "text-generate-contrast-background bg-generate-background font-semibold"
        : "text-generate-background hover:text-generate-selected"
    } ${className}`}
  >
    <Icon className="icon shrink-0" />
    <span className="truncate">{label}</span>
  </button>
);

/* ── NavGroup ────────────────────────────────────────────────────────── */

export interface NavGroupProps {
  icon: LucideIcon;
  label: string;
  /** Whether the category itself is the selected context (lighter highlight). */
  isActive?: boolean;
  isExpanded: boolean;
  onToggle: () => void;
  children: React.ReactNode;
}

export const NavGroup = ({
  icon: Icon,
  label,
  isActive = false,
  isExpanded,
  onToggle,
  children,
}: NavGroupProps) => (
  <li>
    <button
      onClick={onToggle}
      className={`flex items-center justify-between gap-3 w-full text-left py-2 px-2 rounded text-sm mt-1 ${
        isActive ? "text-generate-selected" : "text-generate-background hover:text-generate-selected"
      }`}
    >
      <div className="flex items-center gap-3">
        <Icon className="icon shrink-0" />
        <span className="truncate font-semibold tracking-wider normal-case">
          {label}
        </span>
      </div>
      {isExpanded ? (
        <ChevronDown className="w-3 h-3 shrink-0 opacity-50" />
      ) : (
        <ChevronRight className="w-3 h-3 shrink-0 opacity-50" />
      )}
    </button>

    {isExpanded && (
      <ul className="ml-3 pl-2 border-l border-generate-outline/20 flex flex-col gap-0.5 mt-0.5">
        {children}
      </ul>
    )}
  </li>
);

/* ── SidebarIconBtn ──────────────────────────────────────────────────── */

export interface SidebarIconBtnProps {
  icon: LucideIcon;
  onClick?: () => void;
  className?: string;
  style?: React.CSSProperties;
  title?: string;
}

export const SidebarIconBtn = ({
  icon: Icon,
  onClick,
  className = "",
  style,
  title,
}: SidebarIconBtnProps) => (
  <button
    onClick={onClick}
    title={title}
    className={`text-generate-background hover:text-generate-selected transition-colors ${className}`}
    style={style}
  >
    <Icon className="icon" />
  </button>
);

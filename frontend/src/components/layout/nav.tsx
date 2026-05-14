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
  <div className="group">
    
    <button
      onClick={onClick}
      className={`flex items-center w-full text-left rounded-md text-sm gap-generate-pad${
        isActive
          ? "text-generate-text-input bg-generate-dark-input font-bold"
          : "text-generate-text-placeholder group-hover:text-generate-text-input"
      } ${className}`}
    >
      
      <Icon 
      className={`generate-app-icon${
        isActive
          ? "text-generate-text-input bg-generate-dark-input font-bold"
          : "text-generate-text-placeholder group-hover:text-generate-text-input"
      } ${className}`}
      />
      
      <span className="truncate pl-3 pt-1.5 pb-1.5">{label}</span>
    </button>
  </div>
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
    
    <div className="group"> 
      <button
        onClick={onToggle}
        className="flex items-center w-full text-left rounded-md text-sm gap-generate-pad justify-between"
      >
        <div className="flex items-center gap-3">
          <Icon className="generate-app-icon group-hover:text-generate-text-input" />
          <span className="truncate tracking-wider normal-case group-hover:text-generate-text-input">{label}</span>
        </div>
        {isExpanded ? (
          <ChevronDown className="generate-app-icon group-hover:text-generate-text-input" />
        ) : (
          <ChevronRight className="generate-app-icon group-hover:text-generate-text-input" />
        )}
      </button>
    </div>

    {isExpanded && (
      <ul className="flex flex-col border-l-3 border-generate-text-placeholder ml-2 mt-2 p-generate-pad gap-generate-pad">
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
    className={`generate-app-icon ${className}`}
    style={style}
  >
    <Icon className="generate-app-icon" />
  </button>
);

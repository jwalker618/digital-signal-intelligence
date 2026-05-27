/**
 * Navigation configuration data for the sidebar.
 *
 * These drive the two navigation modes:
 *   • Top-level (no active submission)   — SUBMISSIONS_CHILDREN
 *   • Drill-down (active submission set) — DRILL_DOWN_CATEGORIES
 *
 * Each entry is pure data; the Sidebar component renders them via the
 * NavItem / NavGroup primitives.
 */

import {
  LucideIcon,  Activity,  Briefcase,  Building2,  Calculator,
  ChartNoAxesGantt,  ChartPie,  Clock,  FileCheck,  FileStack,
  FileText,  FileX,  FlaskConical,  Gauge,  Globe,  History,
  Inbox,  Layers,  Lightbulb,  ListChecks, MessagesSquare,  Network,
  RefreshCw,  Rows4,  Bot,  Scale,  ShieldCheck,  TrendingUpDown,
  Users,  UserStar,
} from "lucide-react";

export interface NavLeaf {
  name: string;
  icon: LucideIcon;
}

/** Admin children carry a route + permission; the Submissions children do not. */
export interface AdminNavLeaf extends NavLeaf {
  href: string;
  permission: string;
}

export interface NavCategory {
  category: string;
  icon: LucideIcon;
  tabs: NavLeaf[];
}

/** Children of the Submissions expander, shown in top-level mode. */
export const SUBMISSIONS_CHILDREN: NavLeaf[] = [
  { name: "Referral Pipeline",    icon: UserStar },
  { name: "Full Pipeline",        icon: Rows4 },
  { name: "Performance Metrics",  icon: Bot },
];

/** Children of the Admin expander, shown in top-level mode. */
export const ADMIN_CHILDREN: AdminNavLeaf[] = [
  { name: "System Health",  icon: Activity,        href: "/admin",                permission: "admin:system" },
  { name: "Configs",        icon: FileStack,       href: "/admin/configs",        permission: "config:read" },
  { name: "Users & Roles",  icon: Users,           href: "/admin/users",          permission: "admin:users" },
  { name: "Audit Log",      icon: History,         href: "/admin/audit",          permission: "admin:audit" },
  { name: "Loss Register",  icon: FileX,           href: "/admin/losses",         permission: "assessment:write" },
  { name: "Recalibration",  icon: TrendingUpDown,  href: "/admin/recalibration",  permission: "recalibration:view" },
];

/**
 * v8 Phase 8: client portal sidebar children.
 *
 * Two parallel sets -- one for BROKER, one for CLIENT -- so each role
 * sees a nav tailored to its workflow without permission-gating leaves
 * individually. The sidebar dispatches on role rather than on
 * per-leaf permission gating.
 */

/** Broker view: book + portfolio + coverages + communications + market. */
export const PORTAL_BROKER_CHILDREN: AdminNavLeaf[] = [
  { name: "Book of Clients",   icon: Briefcase,       href: "/portal",                permission: "portal:broker:read" },
  { name: "Portfolio Metrics", icon: ChartPie,        href: "/portal/portfolio",      permission: "portal:broker:read" },
  { name: "Coverages",         icon: ShieldCheck,     href: "/portal/coverages",      permission: "portal:broker:read" },
  { name: "Communications",    icon: MessagesSquare,  href: "/portal/communications", permission: "portal:broker:reply" },
  { name: "Market Conditions", icon: TrendingUpDown,  href: "/portal/market",         permission: "portal:broker:read" },
];

/** Client view: overview + coverages + insight pages + communications. */
export const PORTAL_CLIENT_CHILDREN: AdminNavLeaf[] = [
  { name: "Overview",        icon: Gauge,           href: "/portal",                  permission: "portal:client:read" },
  { name: "Coverages",       icon: ShieldCheck,     href: "/portal/coverages",        permission: "portal:client:read" },
  { name: "Signal Drivers",  icon: ListChecks,      href: "/portal/drivers",          permission: "portal:client:read" },
  { name: "Industry Benchmarks", icon: TrendingUpDown,  href: "/portal/peers",         permission: "portal:client:read" },
  { name: "Action Plan",     icon: Lightbulb,       href: "/portal/actions",          permission: "portal:client:read" },
  { name: "Communications",  icon: MessagesSquare,  href: "/portal/communications",   permission: "portal:client:read" },
];

/**
 * Portal drill-down: when a portal user opens a specific policy
 * (/portal/submissions/{code}), the sidebar shows these tabs scoped
 * to that policy. activeSubmission state from dsiStore drives the mode.
 */
export const PORTAL_POLICY_TABS: NavLeaf[] = [
  { name: "Policy Summary",   icon: Gauge },
  { name: "Signal Drivers",   icon: ListChecks },
  { name: "Peer Comparison",  icon: TrendingUpDown },
  { name: "Action Plan",      icon: Lightbulb },
  { name: "Quote History",    icon: History },
  { name: "Communications",   icon: MessagesSquare },
];

/** Drill-down categories shown when a submission is active. */
export const DRILL_DOWN_CATEGORIES: NavCategory[] = [
  {
    category: "Commercial Terms",
    icon: Building2,
    tabs: [
      { name: "Terms Overview",   icon: FileText },
      { name: "Premium Assembly", icon: Calculator },
      { name: "Distribution",     icon: Network },
    ],
  },
  {
    category: "Risk Terms",
    icon: Scale,
    tabs: [
      { name: "Deductible Structure",       icon: Layers },
      { name: "Coverage Terms",             icon: FileCheck },
      { name: "SIR & Waiting Periods",      icon: Clock },
      { name: "Aggregate & Reinstatement",  icon: RefreshCw },
    ],
  },
  {
    category: "Technical Assessment",
    icon: ChartNoAxesGantt,
    tabs: [
      { name: "Pricing Anatomy",      icon: Calculator },
      { name: "Risk Assessment",      icon: ChartNoAxesGantt },
      { name: "Loss Assessment",      icon: TrendingUpDown },
      { name: "Exposure Assessment",  icon: Globe },
      { name: "Scenarios",            icon: FlaskConical },
      { name: "Referral Actions",     icon: UserStar },
      { name: "Model Versions",       icon: FileStack },
    ],
  },
];

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
  LucideIcon,  Activity,  Building2,  Calculator,  ChartNoAxesGantt,
  Clock,  FileCheck,  FileStack,  FileText,  FileX,  FlaskConical,
  Globe,  History,  Layers,  Network,  RefreshCw,  Rows4,  Bot,
  Scale,  TrendingUpDown,  Users,  UserStar,
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

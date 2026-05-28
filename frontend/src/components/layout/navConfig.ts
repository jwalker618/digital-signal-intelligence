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
  FileText,  FileX,  FlaskConical,  Gauge,  Globe,  HeartPulse,
  History,  Inbox,  Layers,  Lightbulb,  ListChecks, MessagesSquare,
  Network,  PlusCircle,  RefreshCw,  Rows4,  Bot,  Scale,
  ShieldCheck,  Target as TargetIcon,  TrendingUpDown,  Users,
  UserCircle,  UserStar,
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

/**
 * Carrier sidebar (v8.2 reimagined): pipeline tabs + World Engine. Each
 * entry is a real route so the chrome sidebar can highlight via the URL.
 * When a submission is active the workbench layout swaps in DRILL_DOWN_CATEGORIES.
 */
export const PORTAL_CARRIER_CHILDREN: AdminNavLeaf[] = [
  { name: "Referral Pipeline",   icon: UserStar,       href: "/carrier",                permission: "submissions:read" },
  { name: "Full Pipeline",       icon: Rows4,          href: "/carrier/pipeline",       permission: "submissions:read" },
  { name: "Performance Metrics", icon: Bot,            href: "/carrier/metrics",        permission: "submissions:read" },
  { name: "World Engine",        icon: ChartNoAxesGantt, href: "/carrier/world-engine", permission: "submissions:read" },
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

/**
 * Broker portal (v8.2): the broker intelligence platform Marsh
 * recognises -- book, client health, carriers, placement, market
 * pulse, recommendations, communications, risk aggregation, book
 * health.
 */
export const PORTAL_BROKER_CHILDREN: AdminNavLeaf[] = [
  { name: "Book of Clients",   icon: Briefcase,       href: "/broker",                 permission: "portal:broker:read" },
  { name: "Client Health",     icon: HeartPulse,      href: "/broker/client-health",   permission: "portal:broker:read" },
  { name: "Coverages",         icon: ShieldCheck,     href: "/broker/coverages",       permission: "portal:broker:read" },
  { name: "Placement Strategy", icon: TargetIcon,     href: "/broker/placement",       permission: "portal:broker:read" },
  { name: "Carrier Intelligence", icon: Building2,    href: "/broker/carriers",        permission: "portal:broker:read" },
  { name: "Recommendations",   icon: Lightbulb,       href: "/broker/recommendations", permission: "portal:broker:read" },
  { name: "Communications",    icon: MessagesSquare,  href: "/broker/communications",  permission: "portal:broker:reply" },
  { name: "Market Pulse",      icon: TrendingUpDown,  href: "/broker/market",          permission: "portal:broker:read" },
  { name: "Risk Aggregation",  icon: Network,         href: "/broker/aggregation",     permission: "portal:broker:read" },
  { name: "Book Health",       icon: ChartPie,        href: "/broker/book-health",     permission: "portal:broker:read" },
];

/** Client view: overview + profile + coverages + insight pages + scenarios + request + comms. */
export const PORTAL_CLIENT_CHILDREN: AdminNavLeaf[] = [
  { name: "Overview",            icon: Gauge,           href: "/client",            permission: "portal:client:read" },
  { name: "Your Profile",        icon: UserCircle,      href: "/client/profile",    permission: "portal:client:read" },
  { name: "Coverages",           icon: ShieldCheck,     href: "/client/coverages",       permission: "portal:client:read" },
  { name: "Risk Insights",       icon: ListChecks,      href: "/client/drivers",         permission: "portal:client:read" },
  { name: "Industry Benchmarks", icon: TrendingUpDown,  href: "/client/peers",           permission: "portal:client:read" },
  { name: "Scenarios",           icon: FlaskConical,    href: "/client/scenarios",       permission: "portal:client:read" },
  { name: "Action Plan",         icon: Lightbulb,       href: "/client/actions",         permission: "portal:client:read" },
  { name: "Request Coverage",    icon: PlusCircle,      href: "/client/request",         permission: "portal:client:submit" },
  { name: "Communications",      icon: MessagesSquare,  href: "/client/communications",  permission: "portal:client:read" },
];

/**
 * Portal drill-down: when a portal user opens a specific policy
 * (/submissions/{code}), the sidebar shows these tabs scoped
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

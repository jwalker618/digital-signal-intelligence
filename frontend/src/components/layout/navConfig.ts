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
  LucideIcon,
  Building2,
  Calculator,
  ChartNoAxesGantt,
  Clock,
  FileCheck,
  FileStack,
  FileText,
  FlaskConical,
  Globe,
  Layers,
  Network,
  RefreshCw,
  Rows4,
  Bot,
  Scale,
  TrendingUpDown,
  UserStar,
} from "lucide-react";

export interface NavLeaf {
  name: string;
  icon: LucideIcon;
}

export interface NavCategory {
  category: string;
  icon: LucideIcon;
  tabs: NavLeaf[];
}

/** Children of the Submissions expander, shown in top-level mode. */
export const SUBMISSIONS_CHILDREN: NavLeaf[] = [
  { name: "Referral Pipeline", icon: UserStar },
  { name: "Full Pipeline", icon: Rows4 },
  { name: "Performance Metrics", icon: Bot },
];

/** Drill-down categories shown when a submission is active. */
export const DRILL_DOWN_CATEGORIES: NavCategory[] = [
  {
    category: "Commercial Terms",
    icon: Building2,
    tabs: [
      { name: "Terms Overview", icon: FileText },
      { name: "Premium Assembly", icon: Calculator },
      { name: "Distribution", icon: Network },
    ],
  },
  {
    category: "Risk Terms",
    icon: Scale,
    tabs: [
      { name: "Deductible Structure", icon: Layers },
      { name: "Coverage Terms", icon: FileCheck },
      { name: "SIR & Waiting Periods", icon: Clock },
      { name: "Aggregate & Reinstatement", icon: RefreshCw },
    ],
  },
  {
    category: "Technical Assessment",
    icon: ChartNoAxesGantt,
    tabs: [
      { name: "Pricing Anatomy", icon: Calculator },
      { name: "Risk Assessment", icon: ChartNoAxesGantt },
      { name: "Loss Assessment", icon: TrendingUpDown },
      { name: "Exposure Assessment", icon: Globe },
      { name: "Scenarios", icon: FlaskConical },
      { name: "Referral Actions", icon: UserStar },
      { name: "Model Versions", icon: FileStack },
    ],
  },
];

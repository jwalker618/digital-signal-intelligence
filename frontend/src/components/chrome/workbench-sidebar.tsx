"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { ArrowLeft } from "lucide-react";
import { cn } from "@/lib/utils";
import {
  DRILL_DOWN_CATEGORIES,
  type NavLeaf,
} from "@/components/layout/navConfig";

/**
 * Slugify a tab name to a URL path segment. Kept inline so the sidebar
 * and pages stay in lockstep without a shared constants file (the 14
 * names are stable; the existing carrier workbench uses the same set).
 */
export function tabSlug(name: string): string {
  const map: Record<string, string> = {
    "Terms Overview": "terms",
    "Premium Assembly": "premium",
    Distribution: "distribution",
    "Deductible Structure": "deductible",
    "Coverage Terms": "coverage",
    "SIR & Waiting Periods": "sir",
    "Aggregate & Reinstatement": "aggregate",
    "Pricing Anatomy": "pricing",
    "Risk Assessment": "risk",
    "Loss Assessment": "loss",
    "Exposure Assessment": "exposure",
    Scenarios: "scenarios",
    "Referral Actions": "referral",
    "Model Versions": "versions",
  };
  return map[name] ?? name.toLowerCase().replace(/\s+/g, "-");
}

/** Reverse — slug → display name. */
export function tabName(slug: string): string | null {
  for (const cat of DRILL_DOWN_CATEGORIES) {
    for (const t of cat.tabs) {
      if (tabSlug(t.name) === slug) return t.name;
    }
  }
  return null;
}

interface WorkbenchSidebarProps {
  /** Submission code currently being viewed; used to construct tab hrefs. */
  submissionCode: string;
}

/**
 * Drill-down sidebar. Shown when an underwriter opens a single submission.
 * Sticks to the dark chrome treatment so the workbench feels like a focused
 * workspace; categories group the 14 deep-dive tabs.
 */
export function WorkbenchSidebar({ submissionCode }: WorkbenchSidebarProps) {
  const pathname = usePathname();
  const base = `/carrier/submissions/${submissionCode}`;
  const onSummary = pathname === base;

  return (
    <aside className="chrome-sidebar relative flex h-full w-[240px] shrink-0 flex-col">
      <div className="flex items-center gap-2 border-b border-white/10 px-4 py-4">
        <Link
          href="/carrier"
          className="flex h-7 w-7 items-center justify-center rounded-md text-white/55 hover:bg-white/10 hover:text-white"
          title="Back to pipeline"
          aria-label="Back to pipeline"
        >
          <ArrowLeft size={15} />
        </Link>
        <span className="dsi-wordmark" aria-hidden />
      </div>

      <div className="flex-1 overflow-y-auto px-2 py-3">
        <SidebarLink href={base} active={onSummary}>
          Summary
        </SidebarLink>

        {DRILL_DOWN_CATEGORIES.map((cat) => {
          const CatIcon = cat.icon;
          return (
            <div key={cat.category} className="mt-4">
              <div className="flex items-center gap-2 px-3 py-1.5 text-[10.5px] font-semibold uppercase tracking-[0.1em] text-white/40">
                <CatIcon size={11} />
                {cat.category}
              </div>
              <ul className="space-y-0.5">
                {cat.tabs.map((t) => {
                  const slug = tabSlug(t.name);
                  const href = `${base}/${slug}`;
                  const active = pathname === href;
                  return (
                    <li key={t.name}>
                      <SidebarLink href={href} active={active} indent>
                        {t.name}
                      </SidebarLink>
                    </li>
                  );
                })}
              </ul>
            </div>
          );
        })}
      </div>
    </aside>
  );
}

function SidebarLink({
  href,
  active,
  indent,
  children,
}: {
  href: string;
  active: boolean;
  indent?: boolean;
  children: React.ReactNode;
}) {
  return (
    <Link
      href={href}
      aria-current={active ? "page" : undefined}
      className={cn(
        "relative flex items-center rounded-md px-3 py-1.5 text-[13px] transition",
        indent && "pl-7 text-[12.5px]",
        active
          ? "bg-white/10 font-semibold text-white"
          : "text-white/65 hover:bg-white/5 hover:text-white",
      )}
    >
      {active && !indent && (
        <span className="absolute -left-3 top-1.5 bottom-1.5 w-[3px] rounded-sm bg-spot" />
      )}
      {active && indent && (
        <span className="absolute left-3 top-2 bottom-2 w-[2px] rounded-sm bg-spot" />
      )}
      {children}
    </Link>
  );
}

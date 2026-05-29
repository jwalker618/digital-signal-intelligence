"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useRef, useState } from "react";
import {
  ArrowLeft,
  Gauge,
  PanelLeftClose,
  PanelLeftOpen,
  type LucideIcon,
} from "lucide-react";
import { cn } from "@/lib/utils";
import {
  DRILL_DOWN_CATEGORIES,
} from "@/components/layout/navConfig";

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

export function tabName(slug: string): string | null {
  for (const cat of DRILL_DOWN_CATEGORIES) {
    for (const t of cat.tabs) {
      if (tabSlug(t.name) === slug) return t.name;
    }
  }
  return null;
}

interface WorkbenchSidebarProps {
  submissionCode: string;
}

const HOVER_OPEN_MS = 150;
const HOVER_CLOSE_MS = 300;

/**
 * Drill-down sidebar for the submission workbench. Same collapse/expand
 * semantics as PersonaSidebar — 72px icon rail + 50vw overlay panel, hover
 * with delay opens, click-toggle pins, outside-click + Escape closes — but
 * with workbench-specific content: Back-to-pipeline, Summary, and the 14
 * deep-dive tabs grouped under Commercial / Risk / Technical categories.
 */
export function WorkbenchSidebar({ submissionCode }: WorkbenchSidebarProps) {
  const pathname = usePathname();
  const base = `/carrier/submissions/${submissionCode}`;
  const onSummary = pathname === base;

  const [pinned, setPinned] = useState(false);
  const [hovered, setHovered] = useState(false);
  const expanded = pinned || hovered;

  const wrapRef = useRef<HTMLDivElement | null>(null);
  const openTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const closeTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  const clearTimers = () => {
    if (openTimer.current) { clearTimeout(openTimer.current); openTimer.current = null; }
    if (closeTimer.current) { clearTimeout(closeTimer.current); closeTimer.current = null; }
  };

  const handleEnter = () => {
    if (closeTimer.current) { clearTimeout(closeTimer.current); closeTimer.current = null; }
    if (hovered) return;
    openTimer.current = setTimeout(() => {
      setHovered(true);
      openTimer.current = null;
    }, HOVER_OPEN_MS);
  };

  const handleLeave = () => {
    if (openTimer.current) { clearTimeout(openTimer.current); openTimer.current = null; }
    if (pinned) return;
    closeTimer.current = setTimeout(() => {
      setHovered(false);
      closeTimer.current = null;
    }, HOVER_CLOSE_MS);
  };

  const closeAll = () => {
    clearTimers();
    setPinned(false);
    setHovered(false);
  };

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => { if (e.key === "Escape") closeAll(); };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []);

  useEffect(() => {
    if (!expanded) return;
    const onDown = (e: PointerEvent) => {
      const node = wrapRef.current;
      if (!node) return;
      if (node.contains(e.target as Node)) return;
      closeAll();
    };
    document.addEventListener("pointerdown", onDown);
    return () => document.removeEventListener("pointerdown", onDown);
  }, [expanded]);

  useEffect(() => () => clearTimers(), []);

  useEffect(() => {
    closeAll();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [pathname]);

  const togglePinned = () => {
    if (pinned) closeAll();
    else {
      clearTimers();
      setPinned(true);
      setHovered(true);
    }
  };

  return (
    <div
      ref={wrapRef}
      onMouseEnter={handleEnter}
      onMouseLeave={handleLeave}
      className="contents"
    >
      <aside
        className="chrome-sidebar relative z-10 flex h-full w-[72px] shrink-0 flex-col items-center py-[18px]"
        aria-label="Workbench navigation"
      >
        <Link
          href="/carrier"
          className="mb-[12px] flex h-9 w-9 items-center justify-center rounded-lg text-white/55 hover:bg-white/10 hover:text-white"
          title="Back to pipeline"
          aria-label="Back to pipeline"
        >
          <ArrowLeft size={18} />
        </Link>
        <button
          type="button"
          onClick={togglePinned}
          aria-label={pinned ? "Collapse sidebar" : "Expand sidebar"}
          aria-expanded={expanded}
          className="mb-[18px] flex h-9 w-9 items-center justify-center rounded-lg text-white/55 hover:text-white"
        >
          {pinned ? <PanelLeftClose size={20} /> : <PanelLeftOpen size={20} />}
        </button>

        <RailIcon
          href={base}
          icon={Gauge}
          label="Summary"
          active={onSummary}
        />
        <div className="my-2 h-px w-7 bg-white/10" aria-hidden />
        {DRILL_DOWN_CATEGORIES.map((cat) => {
          const firstTab = cat.tabs[0];
          if (!firstTab) return null;
          const slug = tabSlug(firstTab.name);
          const catHref = `${base}/${slug}`;
          const catActive = cat.tabs.some(
            (t) => pathname === `${base}/${tabSlug(t.name)}`,
          );
          return (
            <RailIcon
              key={cat.category}
              href={catHref}
              icon={cat.icon}
              label={cat.category}
              active={catActive}
            />
          );
        })}
      </aside>

      {expanded && (
        <>
          <div
            className="fixed inset-0 z-40 bg-black/30"
            aria-hidden
            onClick={closeAll}
          />
          <aside
            className="chrome-sidebar fixed left-0 top-0 z-50 flex h-screen w-[50vw] flex-col py-[18px] pl-5 pr-6"
            aria-label="Workbench navigation expanded"
            onMouseEnter={handleEnter}
            onMouseLeave={handleLeave}
          >
            <div className="mb-[14px] flex items-center gap-3">
              <Link
                href="/carrier"
                className="flex h-9 w-9 items-center justify-center rounded-lg text-white/65 hover:bg-white/10 hover:text-white"
                aria-label="Back to pipeline"
              >
                <ArrowLeft size={18} />
              </Link>
              <button
                type="button"
                onClick={togglePinned}
                aria-label="Collapse sidebar"
                className="flex h-9 w-9 items-center justify-center rounded-lg text-white/65 hover:bg-white/10 hover:text-white"
              >
                <PanelLeftClose size={20} />
              </button>
              <span className="ml-1 text-[13px] font-semibold uppercase tracking-[0.12em] text-white/80">
                Workbench
              </span>
            </div>

            <div className="flex-1 overflow-y-auto pr-2">
              <PanelLink href={base} active={onSummary} icon={Gauge}>
                Summary
              </PanelLink>

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
                        const Icon = t.icon;
                        return (
                          <li key={t.name}>
                            <PanelLink
                              href={href}
                              active={active}
                              icon={Icon}
                              indent
                            >
                              {t.name}
                            </PanelLink>
                          </li>
                        );
                      })}
                    </ul>
                  </div>
                );
              })}
            </div>
          </aside>
        </>
      )}
    </div>
  );
}

function RailIcon({
  href,
  icon: Icon,
  label,
  active,
}: {
  href: string;
  icon: LucideIcon;
  label: string;
  active: boolean;
}) {
  return (
    <Link
      href={href}
      title={label}
      aria-label={label}
      aria-current={active ? "page" : undefined}
      className={cn(
        "relative mb-1 flex h-[38px] w-[38px] items-center justify-center rounded-lg text-white/55 transition-colors hover:text-white",
        active && "bg-white/10 text-white",
      )}
    >
      {active && (
        <span className="absolute -left-[18px] top-2 bottom-2 w-[3px] rounded-sm bg-spot" />
      )}
      <Icon size={18} />
    </Link>
  );
}

function PanelLink({
  href,
  active,
  icon: Icon,
  indent,
  children,
}: {
  href: string;
  active: boolean;
  icon: LucideIcon;
  indent?: boolean;
  children: React.ReactNode;
}) {
  return (
    <Link
      href={href}
      aria-current={active ? "page" : undefined}
      className={cn(
        "relative flex items-center gap-3 rounded-md px-3 py-1.5 text-[13px] transition",
        indent && "pl-6 text-[12.5px]",
        active
          ? "bg-white/10 font-semibold text-white"
          : "text-white/65 hover:bg-white/5 hover:text-white",
      )}
    >
      {active && (
        <span
          className={cn(
            "absolute top-2 bottom-2 w-[2px] rounded-sm bg-spot",
            indent ? "left-3" : "-left-3",
          )}
        />
      )}
      <Icon size={indent ? 14 : 16} className="shrink-0" />
      <span>{children}</span>
    </Link>
  );
}

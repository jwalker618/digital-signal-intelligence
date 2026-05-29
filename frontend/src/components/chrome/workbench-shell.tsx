"use client";

import Link from "next/link";
import { useEffect, useState, type ReactNode } from "react";
import {
  ArrowLeft,
  LogOut,
  PanelLeftClose,
  PanelLeftOpen,
  Settings,
  Moon,
  Sun,
  type LucideIcon,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { useThemeStore } from "@/store/themeStore";

/* ============================================================
 * Shared workbench shell — the unified drill-down chrome from
 * the revised design pack (primitives.jsx WorkbenchShell +
 * WorkbenchSidebar). Powers BOTH the carrier submission
 * workbench and the broker client workbench.
 *
 *   - 60px collapsed rail: expand toggle, top-level tab icons
 *     (active = spot left-bar), logout
 *   - click-toggle 50% overlay: account block, scope block,
 *     full drill-down tab tree, settings/logout footer
 *   - context topbar: back link, identity lead, context stats
 *     (deep tabs only), dark toggle pinned furthest-right
 *
 * The shell stays dark in both light + dark mode (the nav is
 * structural chrome, not body surface).
 * ============================================================ */

export type WbNavLeaf = {
  kind: "leaf";
  name: string;
  icon: LucideIcon;
  href: string;
};

export type WbNavGroup = {
  kind: "group";
  name: string;
  icon: LucideIcon;
  children: { name: string; icon: LucideIcon; href: string }[];
};

export type WbNavItem = WbNavLeaf | WbNavGroup;

export interface WbAccount {
  initials: string;
  name: string;
  email: string;
}

export interface WbScope {
  label: string;
  lines: string[];
}

export interface WbContextStat {
  label: string;
  value: ReactNode;
  tone?: "info" | "pos" | "spot" | "warn" | "neg";
}

const STAT_TONE: Record<NonNullable<WbContextStat["tone"]>, string> = {
  info: "text-info",
  pos: "text-pos",
  spot: "text-spot",
  warn: "text-warn",
  neg: "text-neg",
};

interface WorkbenchShellProps {
  nav: WbNavItem[];
  /** The active tab's display name (matches a leaf or a group child). */
  active: string;
  account: WbAccount;
  scope: WbScope;
  backLabel: string;
  backHref: string;
  /** Breadcrumb / identity cluster rendered after the back link. */
  lead: ReactNode;
  contextStats?: WbContextStat[];
  children: ReactNode;
}

export function WorkbenchShell({
  nav,
  active,
  account,
  scope,
  backLabel,
  backHref,
  lead,
  contextStats = [],
  children,
}: WorkbenchShellProps) {
  const [expanded, setExpanded] = useState(false);
  const isDark = useThemeStore((s) => s.isDark);
  const toggleDark = useThemeStore((s) => s.toggleDark);

  const activeGroup = nav.find(
    (n) => n.kind === "group" && n.children.some((c) => c.name === active),
  )?.name;
  const isSummary = active === "Summary";

  // Escape closes the overlay.
  useEffect(() => {
    if (!expanded) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") setExpanded(false);
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [expanded]);

  return (
    <div className="relative flex h-full w-full">
      {/* ── Collapsed rail ───────────────────────────────── */}
      <aside
        className="relative z-10 flex h-full w-[60px] shrink-0 flex-col items-center bg-[#0b2237] py-3.5 text-white/60 dark:bg-[#051322]"
        aria-label="Workbench navigation"
      >
        <RailButton
          icon={PanelLeftOpen}
          label="Expand menu"
          onClick={() => setExpanded(true)}
        />
        <div className="my-2 mb-3 h-px w-6 shrink-0 bg-white/15" />
        {nav.map((n) => {
          const act = n.kind === "leaf" ? n.name === active : activeGroup === n.name;
          const href = n.kind === "leaf" ? n.href : n.children[0]!.href;
          return (
            <Link
              key={n.name}
              href={href}
              title={n.name}
              aria-label={n.name}
              className={cn(
                "relative mb-1 flex h-[38px] w-[38px] items-center justify-center rounded-lg text-white/55 hover:bg-white/10 hover:text-white",
                act && "bg-white/[0.08] text-white",
              )}
            >
              {act && (
                <span className="absolute -left-[18px] top-2 bottom-2 w-[3px] rounded-sm bg-spot" />
              )}
              <n.icon size={20} />
            </Link>
          );
        })}
        <div className="flex-1" />
        <RailButton icon={LogOut} label="Log out" onClick={() => undefined} />
      </aside>

      {/* ── Expanded overlay ─────────────────────────────── */}
      {expanded && (
        <>
          <div
            className="absolute inset-0 z-40 bg-[#050c12]/40"
            aria-hidden
            onClick={() => setExpanded(false)}
          />
          <aside className="absolute left-0 top-0 bottom-0 z-50 flex w-1/2 min-w-[320px] flex-col bg-[#0b2237] px-4 pb-[18px] pt-3.5 text-white/85 shadow-[24px_0_60px_rgba(5,12,18,0.32)] dark:bg-[#051322]">
            <div className="flex">
              <RailButton
                icon={PanelLeftClose}
                label="Close menu"
                onClick={() => setExpanded(false)}
              />
            </div>

            {/* Account */}
            <div className="my-1.5 flex items-center gap-3 border-b border-white/10 px-2 pb-4 pt-2.5">
              <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-info text-[15px] font-semibold text-[#06222f]">
                {account.initials}
              </div>
              <div className="min-w-0">
                <div className="text-[14px] font-semibold leading-tight text-white">
                  {account.name}
                </div>
                <div className="mt-0.5 truncate text-[12px] text-white/55">
                  {account.email}
                </div>
              </div>
            </div>

            {/* Scope */}
            <div className="border-b border-white/10 px-2.5 pb-3 pt-2.5">
              <div className="text-[10px] uppercase tracking-wider text-white/50">
                {scope.label}
              </div>
              {scope.lines.map((ln, i) => (
                <div
                  key={i}
                  className={
                    i === 0
                      ? "mt-1 text-[13px] font-semibold text-white"
                      : "mt-0.5 text-[11px] text-white/50"
                  }
                >
                  {ln}
                </div>
              ))}
            </div>

            {/* Drill-down tree */}
            <nav className="mt-2 flex min-h-0 flex-1 flex-col gap-0.5 overflow-y-auto">
              {nav.map((n) =>
                n.kind === "leaf" ? (
                  <OverlayItem
                    key={n.name}
                    icon={n.icon}
                    name={n.name}
                    href={n.href}
                    active={n.name === active}
                    onNavigate={() => setExpanded(false)}
                  />
                ) : (
                  <div key={n.name}>
                    <div className="flex items-center gap-2.5 px-2.5 pb-1.5 pt-3 text-[10.5px] font-bold uppercase tracking-wider text-white/45">
                      <n.icon size={13} />
                      <span>{n.name}</span>
                    </div>
                    {n.children.map((c) => (
                      <OverlayItem
                        key={c.name}
                        icon={c.icon}
                        name={c.name}
                        href={c.href}
                        active={c.name === active}
                        sub
                        onNavigate={() => setExpanded(false)}
                      />
                    ))}
                  </div>
                ),
              )}
            </nav>

            {/* Footer */}
            <div className="flex flex-col gap-0.5 border-t border-white/10 pt-2.5">
              <OverlayItem icon={Settings} name="Settings" href="#" onNavigate={() => undefined} />
              <OverlayItem icon={LogOut} name="Log out" href="#" onNavigate={() => undefined} />
            </div>
          </aside>
        </>
      )}

      {/* ── Main column ──────────────────────────────────── */}
      <main className="flex min-w-0 flex-1 flex-col overflow-hidden bg-canvas">
        <header className="flex h-16 items-center justify-between border-b border-rule px-8">
          <div className="flex min-w-0 flex-1 items-center gap-3.5 py-3 text-[14px]">
            <Link
              href={backHref}
              className="flex items-center gap-1 text-[12px] text-ink-soft hover:text-ink"
            >
              <ArrowLeft size={12} /> {backLabel}
            </Link>
            {lead}
            <span className="flex-1" />
            {!isSummary && contextStats.length > 0 && (
              <div className="flex items-center gap-[18px]">
                {contextStats.map((s) => (
                  <div key={s.label} className="text-right">
                    <div className="text-[10px] text-ink-mute">{s.label}</div>
                    <div
                      className={cn(
                        "text-[16px] font-bold leading-none tabular-nums text-ink",
                        s.tone && STAT_TONE[s.tone],
                      )}
                    >
                      {s.value}
                    </div>
                  </div>
                ))}
              </div>
            )}
            <button
              type="button"
              onClick={toggleDark}
              aria-label="Toggle light or dark mode"
              className="ml-[18px] flex h-[34px] w-[34px] shrink-0 items-center justify-center rounded-lg text-ink-soft hover:bg-surface-sunken"
            >
              {isDark ? <Sun size={16} /> : <Moon size={16} />}
            </button>
          </div>
        </header>
        <div className="flex-1 overflow-hidden">{children}</div>
      </main>
    </div>
  );
}

function RailButton({
  icon: Icon,
  label,
  onClick,
}: {
  icon: LucideIcon;
  label: string;
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      title={label}
      aria-label={label}
      className="flex h-[38px] w-[38px] shrink-0 items-center justify-center rounded-lg text-white/60 hover:bg-white/10 hover:text-white"
    >
      <Icon size={20} />
    </button>
  );
}

function OverlayItem({
  icon: Icon,
  name,
  href,
  active,
  sub,
  onNavigate,
}: {
  icon: LucideIcon;
  name: string;
  href: string;
  active?: boolean;
  sub?: boolean;
  onNavigate: () => void;
}) {
  return (
    <Link
      href={href}
      onClick={onNavigate}
      className={cn(
        "flex items-center gap-3 rounded-lg px-2.5 py-2.5 text-[14px] font-medium text-white/72 hover:bg-white/[0.08] hover:text-white",
        sub && "pl-[30px] font-normal",
        active && "bg-white/10 text-white",
      )}
    >
      <Icon size={sub ? 16 : 18} />
      <span>{name}</span>
    </Link>
  );
}

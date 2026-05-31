"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useRef, useState, type ReactNode } from "react";
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
import { useAuthStore } from "@/store/authStore";
import { useThemeStore } from "@/store/themeStore";

// Mirror the persona sidebar's hover timing so the two surfaces feel
// identical to the user (the docx explicitly calls out the inconsistency).
const HOVER_OPEN_MS = 150;
const HOVER_CLOSE_MS = 300;

/* ============================================================
 * Shared workbench shell — the unified drill-down chrome from
 * the revised design pack. Powers BOTH the carrier submission
 * workbench and the broker client workbench.
 *
 *   - 60px collapsed rail: expand toggle, top-level tab icons
 *     (active = spot left-bar), logout pinned to bottom
 *   - hover-open 50% overlay: full drill-down tab tree +
 *     settings/logout footer (NO account or scope blocks —
 *     workbench sidebar is icons-only navigation, identity
 *     lives on the topbar lead)
 *   - context topbar: back link, identity lead, context stats
 *     (deep tabs only), dark toggle pinned furthest-right
 *
 * Behaviour mirrors the persona sidebar: hover-only open with
 * the same 150/300ms timings, no inner scrollbar.
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
  /** @deprecated kept for source compatibility; not rendered (the
   *  workbench sidebar is now icons-only, identity is on the topbar). */
  account?: WbAccount;
  /** @deprecated kept for source compatibility; not rendered. */
  scope?: WbScope;
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
  backLabel,
  backHref,
  lead,
  contextStats = [],
  children,
}: WorkbenchShellProps) {
  const [expanded, setExpanded] = useState(false);
  const isDark = useThemeStore((s) => s.isDark);
  const toggleDark = useThemeStore((s) => s.toggleDark);
  const router = useRouter();
  const logout = useAuthStore((s) => s.logout);
  const onSignOut = async () => {
    await logout();
    router.replace("/login");
  };

  const activeGroup = nav.find(
    (n) => n.kind === "group" && n.children.some((c) => c.name === active),
  )?.name;
  const isSummary = active === "Summary";

  // Hover open/close timers — identical to PersonaSidebar.
  const openTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const closeTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const clearTimers = () => {
    if (openTimer.current) { clearTimeout(openTimer.current); openTimer.current = null; }
    if (closeTimer.current) { clearTimeout(closeTimer.current); closeTimer.current = null; }
  };
  const close = () => { clearTimers(); setExpanded(false); };
  const handleEnter = () => {
    if (closeTimer.current) { clearTimeout(closeTimer.current); closeTimer.current = null; }
    if (expanded) return;
    openTimer.current = setTimeout(() => { setExpanded(true); openTimer.current = null; }, HOVER_OPEN_MS);
  };
  const handleLeave = () => {
    if (openTimer.current) { clearTimeout(openTimer.current); openTimer.current = null; }
    closeTimer.current = setTimeout(() => { setExpanded(false); closeTimer.current = null; }, HOVER_CLOSE_MS);
  };

  // Escape closes the overlay.
  useEffect(() => {
    if (!expanded) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") close();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [expanded]);
  useEffect(() => () => clearTimers(), []);

  return (
    <div
      className="relative flex h-full w-full"
      onMouseEnter={handleEnter}
      onMouseLeave={handleLeave}
    >
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
        <div className="mt-2 mb-3 h-px w-6 shrink-0 bg-white/15" />
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
                <span className="absolute -left-[11px] top-2 bottom-2 w-[3px] rounded-sm bg-spot" />
              )}
              <n.icon size={20} />
            </Link>
          );
        })}
        <div className="flex-1" />
        <RailButton icon={LogOut} label="Log out" onClick={onSignOut} />
      </aside>

      {/* ── Expanded overlay ─────────────────────────────── *
       * No account / scope blocks (the workbench sidebar is icons-only
       * for navigation; identity stays on the topbar lead). Structure
       * mirrors the persona sidebar so the two surfaces feel identical.
       */}
      {expanded && (
        <>
          <div
            className="absolute inset-0 z-40 bg-[#050c12]/40"
            aria-hidden
            onClick={close}
          />
          <aside className="absolute left-0 top-0 bottom-0 z-50 flex w-1/2 min-w-[320px] flex-col bg-[#0b2237] py-3.5 pl-[11px] pr-4 text-white/85 shadow-[24px_0_60px_rgba(5,12,18,0.32)] dark:bg-[#051322]">
            <RailButton
              icon={PanelLeftClose}
              label="Close menu"
              onClick={close}
            />
            <span
              className="mt-2 mb-3 h-px w-6 shrink-0 bg-white/15"
              style={{ marginLeft: 7 }}
              aria-hidden
            />

            {/* Drill-down tree — NO overflow-y-auto. If nav exceeds the
                viewport on small screens that's a separate issue to fix
                with a denser tree, not by adding a scrollbar to the chrome. */}
            <nav className="flex min-h-0 flex-1 flex-col gap-0.5">
              {nav.map((n) =>
                n.kind === "leaf" ? (
                  <OverlayItem
                    key={n.name}
                    icon={n.icon}
                    name={n.name}
                    href={n.href}
                    active={n.name === active}
                    onNavigate={close}
                  />
                ) : (
                  <div key={n.name}>
                    <div className="flex items-center gap-2.5 px-2.5 pb-1.5 pt-3 text-[10.5px] font-bold uppercase tracking-wider text-white/45">
                      <span className="flex h-[38px] w-[38px] shrink-0 items-center justify-center">
                        <n.icon size={13} />
                      </span>
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
                        onNavigate={close}
                      />
                    ))}
                  </div>
                ),
              )}
            </nav>

            {/* Footer */}
            <div className="flex flex-col gap-0.5 border-t border-white/10 pt-2.5">
              <OverlayItem icon={Settings} name="Settings" href="/profile" onNavigate={close} />
              <OverlayItemButton icon={LogOut} name="Log out" onClick={() => { close(); void onSignOut(); }} />
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
        "relative flex h-[38px] items-center gap-3 rounded-lg pl-0 pr-2.5 text-[14px] font-medium text-white/72 hover:bg-white/[0.08] hover:text-white",
        sub && "pl-[38px] font-normal",
        active && "bg-white/10 text-white",
      )}
    >
      {active && (
        <span className="absolute -left-[11px] top-2 bottom-2 w-[3px] rounded-sm bg-spot" />
      )}
      {!sub && (
        <span className="flex h-[38px] w-[38px] shrink-0 items-center justify-center">
          <Icon size={20} />
        </span>
      )}
      {sub && <Icon size={14} className="shrink-0" />}
      <span>{name}</span>
    </Link>
  );
}

function OverlayItemButton({
  icon: Icon,
  name,
  onClick,
}: {
  icon: LucideIcon;
  name: string;
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className="flex h-[38px] items-center gap-3 rounded-lg pl-0 pr-2.5 text-left text-[14px] font-medium text-white/72 hover:bg-white/[0.08] hover:text-white"
    >
      <span className="flex h-[38px] w-[38px] shrink-0 items-center justify-center">
        <Icon size={20} />
      </span>
      <span>{name}</span>
    </button>
  );
}

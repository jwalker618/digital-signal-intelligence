"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useRef, useState } from "react";
import {
  LogOut,
  PanelLeftClose,
  PanelLeftOpen,
  Settings,
  type LucideIcon,
} from "lucide-react";
import { cn } from "@/lib/utils";
import {
  PORTAL_CLIENT_CHILDREN,
  PORTAL_BROKER_CHILDREN,
  PORTAL_CARRIER_CHILDREN,
  ADMIN_CHILDREN,
  type AdminNavLeaf,
} from "@/components/layout/navConfig";
import { useAuthStore } from "@/store/authStore";
import { deriveUserDisplay } from "@/lib/userIdentity";

export type PersonaKey = "client" | "broker" | "carrier" | "admin";

interface PersonaSidebarProps {
  persona: PersonaKey;
  isActive?: (href: string, pathname: string) => boolean;
}

const PERSONA_NAV: Record<PersonaKey, AdminNavLeaf[]> = {
  client: PORTAL_CLIENT_CHILDREN,
  broker: PORTAL_BROKER_CHILDREN,
  carrier: PORTAL_CARRIER_CHILDREN,
  admin: ADMIN_CHILDREN,
};

const defaultIsActive = (href: string, pathname: string) => {
  if (href === pathname) return true;
  // Persona roots only match exactly — their tabs have separate entries.
  if (
    href === "/client" ||
    href === "/broker" ||
    href === "/admin" ||
    href === "/carrier"
  ) {
    return pathname === href;
  }
  return pathname.startsWith(href + "/") || pathname.startsWith(href + "?");
};

const HOVER_OPEN_MS = 150;
const HOVER_CLOSE_MS = 300;

/**
 * Persona icon rail with overlay expansion.
 *
 * Behaviour:
 *  - Collapsed rail is always visible (72px). It hosts the toggle button
 *    and the persona nav icons.
 *  - Expanded panel (50vw) is a `position: fixed` overlay so it escapes
 *    the (app)/layout.tsx `overflow-hidden`. It shows the same nav items
 *    with labels plus a Profile/Account link at the bottom.
 *  - The panel opens on hover after 150ms and closes on mouseleave after
 *    300ms — UNLESS the user has pinned it open by clicking the toggle.
 *  - A click on the toggle pins/unpins; Escape and outside-click unpin
 *    and close. Outside-click uses `pointerdown` so it fires before
 *    other handlers can swallow the event.
 */
export function PersonaSidebar({
  persona,
  isActive = defaultIsActive,
}: PersonaSidebarProps) {
  const pathname = usePathname();
  const router = useRouter();
  const nav = PERSONA_NAV[persona];

  const user = useAuthStore((s) => s.user);
  const logout = useAuthStore((s) => s.logout);
  const account = user ? deriveUserDisplay(user) : null;

  const onSignOut = async () => {
    await logout();
    router.replace("/login");
  };

  const [pinned, setPinned] = useState(false);
  const [hovered, setHovered] = useState(false);
  const expanded = pinned || hovered;

  // Wrap both the rail and the expanded panel so contains() works.
  const wrapRef = useRef<HTMLDivElement | null>(null);
  const openTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const closeTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  const clearTimers = () => {
    if (openTimer.current) {
      clearTimeout(openTimer.current);
      openTimer.current = null;
    }
    if (closeTimer.current) {
      clearTimeout(closeTimer.current);
      closeTimer.current = null;
    }
  };

  const handleEnter = () => {
    if (closeTimer.current) {
      clearTimeout(closeTimer.current);
      closeTimer.current = null;
    }
    if (hovered) return;
    openTimer.current = setTimeout(() => {
      setHovered(true);
      openTimer.current = null;
    }, HOVER_OPEN_MS);
  };

  const handleLeave = () => {
    if (openTimer.current) {
      clearTimeout(openTimer.current);
      openTimer.current = null;
    }
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

  // Escape closes.
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") closeAll();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []);

  // Outside-click closes — pointerdown so it fires before downstream
  // click handlers and before route changes complete.
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

  // Tidy up any pending timers on unmount.
  useEffect(() => () => clearTimers(), []);

  // Closing also happens on nav — when the path changes, drop hover/pin so
  // the user lands on the new page without a lingering overlay.
  useEffect(() => {
    closeAll();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [pathname]);

  const togglePinned = () => {
    if (pinned) {
      closeAll();
    } else {
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
      {/* Collapsed rail — always visible, lives in the flex layout */}
      <aside
        className="chrome-sidebar relative z-10 flex h-full w-[60px] shrink-0 flex-col items-center py-3.5"
        aria-label={`${persona} navigation`}
      >
        <button
          type="button"
          onClick={togglePinned}
          aria-label={pinned ? "Collapse sidebar" : "Expand sidebar"}
          aria-expanded={expanded}
          className="flex h-[38px] w-[38px] items-center justify-center rounded-lg text-white/60 transition-colors hover:bg-white/10 hover:text-white"
        >
          {pinned ? <PanelLeftClose size={20} /> : <PanelLeftOpen size={20} />}
        </button>
        <span className="mt-2 mb-3 h-px w-6 shrink-0 bg-white/15" aria-hidden />
        <nav className="flex w-full flex-col items-center gap-1">
          {nav.map((n) => {
            const Icon: LucideIcon = n.icon;
            const active = isActive(n.href, pathname);
            return (
              <Link
                key={n.href}
                href={n.href}
                title={n.name}
                aria-label={n.name}
                aria-current={active ? "page" : undefined}
                className={cn(
                  "relative flex h-[38px] w-[38px] items-center justify-center rounded-lg text-white/55 transition-colors hover:text-white",
                  active && "bg-white/10 text-white",
                )}
              >
                {active && (
                  <span className="absolute -left-[18px] top-2 bottom-2 w-[3px] rounded-sm bg-spot" />
                )}
                <Icon size={20} />
              </Link>
            );
          })}
        </nav>
        <div className="flex-1" />
        {/* Quick log-out — Settings stays in the expanded panel only, so it
            can't be reached from the collapsed rail (matches the design pack). */}
        <button
          type="button"
          onClick={onSignOut}
          title="Log out"
          aria-label="Log out"
          className="flex h-[38px] w-[38px] items-center justify-center rounded-lg text-white/60 transition-colors hover:bg-white/10 hover:text-white"
        >
          <LogOut size={20} />
        </button>
      </aside>

      {/* Backdrop + expanded overlay — fixed to viewport so it escapes
          the (app)/layout.tsx overflow-hidden clip. */}
      {expanded && (
        <>
          <div
            className="fixed inset-0 z-40 bg-black/30"
            aria-hidden
            onClick={closeAll}
          />
          <aside
            className="chrome-sidebar fixed left-0 top-0 z-50 flex h-screen w-[50vw] min-w-[320px] flex-col px-4 pt-3.5 pb-[18px]"
            aria-label={`${persona} navigation expanded`}
            onMouseEnter={handleEnter}
            onMouseLeave={handleLeave}
          >
            <div className="flex">
              <button
                type="button"
                onClick={togglePinned}
                aria-label={pinned ? "Collapse sidebar" : "Pin sidebar"}
                aria-expanded={expanded}
                className="flex h-[38px] w-[38px] items-center justify-center rounded-lg text-white/60 transition-colors hover:bg-white/10 hover:text-white"
              >
                {/* Panel is rendered, so it's open from the user's POV — always
                    show the "close" affordance regardless of pinned state. */}
                <PanelLeftClose size={20} />
              </button>
            </div>

            {/* Account — only visible while the sidebar is expanded. */}
            {account && (
              <div className="mt-1.5 mb-1.5 flex items-center gap-3 border-b border-white/10 px-2 pt-2.5 pb-4">
                <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-info text-[15px] font-semibold text-[#06222f]">
                  {account.initials}
                </div>
                <div className="min-w-0">
                  <div className="text-sm font-semibold leading-tight text-white">
                    {account.name}
                  </div>
                  <div className="mt-0.5 truncate text-xs text-white/55">
                    {account.email}
                  </div>
                </div>
              </div>
            )}

            <nav className="mt-2 flex flex-col gap-0.5">
              {nav.map((n) => {
                const Icon: LucideIcon = n.icon;
                const active = isActive(n.href, pathname);
                return (
                  <Link
                    key={n.href}
                    href={n.href}
                    aria-current={active ? "page" : undefined}
                    className={cn(
                      "relative flex h-[38px] items-center gap-3 rounded-lg px-2.5 text-[14px] font-medium text-white/70 transition-colors hover:bg-white/[0.08] hover:text-white",
                      active && "bg-white/10 text-white",
                    )}
                  >
                    {active && (
                      <span className="absolute -left-[18px] top-2 bottom-2 w-[3px] rounded-sm bg-spot" />
                    )}
                    <Icon size={18} className="shrink-0" />
                    <span>{n.name}</span>
                  </Link>
                );
              })}
            </nav>
            <div className="mt-auto flex flex-col gap-0.5 border-t border-white/10 pt-2.5">
              <Link
                href="/profile"
                aria-label="Settings"
                className="flex h-[38px] items-center gap-3 rounded-lg px-2.5 text-[14px] font-medium text-white/70 transition-colors hover:bg-white/[0.08] hover:text-white"
              >
                <Settings size={18} className="shrink-0" />
                <span>Settings</span>
              </Link>
              <button
                type="button"
                onClick={onSignOut}
                className="flex h-[38px] items-center gap-3 rounded-lg px-2.5 text-left text-[14px] font-medium text-white/70 transition-colors hover:bg-white/[0.08] hover:text-white"
              >
                <LogOut size={18} className="shrink-0" />
                <span>Log out</span>
              </button>
            </div>
          </aside>
        </>
      )}
    </div>
  );
}

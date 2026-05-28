"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useRef, useState } from "react";
import {
  PanelLeftClose,
  PanelLeftOpen,
  UserCircle,
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
  const nav = PERSONA_NAV[persona];

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
        className="chrome-sidebar relative z-10 flex h-full w-[72px] shrink-0 flex-col items-center py-[18px]"
        aria-label={`${persona} navigation`}
      >
        <button
          type="button"
          onClick={togglePinned}
          aria-label={pinned ? "Collapse sidebar" : "Expand sidebar"}
          aria-expanded={expanded}
          className="mb-[18px] flex h-9 w-9 items-center justify-center rounded-lg text-white/55 hover:text-white"
        >
          {pinned ? <PanelLeftClose size={20} /> : <PanelLeftOpen size={20} />}
        </button>
        <Link
          href={nav[0]?.href ?? "/"}
          className="mb-[16px] flex h-9 w-9 items-center justify-center rounded-lg"
          aria-label="DSI home"
        >
          <span className="dsi-wordmark" aria-hidden />
        </Link>
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
            className="chrome-sidebar fixed left-0 top-0 z-50 flex h-screen w-[50vw] flex-col py-[18px] pl-5 pr-6"
            aria-label={`${persona} navigation expanded`}
            onMouseEnter={handleEnter}
            onMouseLeave={handleLeave}
          >
            <button
              type="button"
              onClick={togglePinned}
              aria-label={pinned ? "Collapse sidebar" : "Pin sidebar"}
              aria-expanded={expanded}
              className="mb-[18px] flex h-9 w-9 items-center justify-center rounded-lg text-white/55 hover:text-white"
            >
              {pinned ? <PanelLeftClose size={20} /> : <PanelLeftOpen size={20} />}
            </button>
            <Link
              href={nav[0]?.href ?? "/"}
              className="mb-[22px] flex h-9 items-center gap-2 text-white"
              aria-label="DSI home"
            >
              <span className="dsi-wordmark" aria-hidden />
              <span className="text-[13px] font-semibold uppercase tracking-[0.12em] text-white/80">
                DSI
              </span>
            </Link>
            <nav className="flex flex-col gap-1">
              {nav.map((n) => {
                const Icon: LucideIcon = n.icon;
                const active = isActive(n.href, pathname);
                return (
                  <Link
                    key={n.href}
                    href={n.href}
                    aria-current={active ? "page" : undefined}
                    className={cn(
                      "relative flex h-[38px] items-center gap-3 rounded-lg px-2 text-[13.5px] text-white/65 transition-colors hover:bg-white/5 hover:text-white",
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
            <div className="mt-auto flex flex-col gap-1 border-t border-white/10 pt-3">
              <Link
                href="/profile"
                aria-label="Account"
                className="flex h-[38px] items-center gap-3 rounded-lg px-2 text-[13.5px] text-white/65 hover:bg-white/5 hover:text-white"
              >
                <UserCircle size={18} className="shrink-0" />
                <span>Profile</span>
              </Link>
            </div>
          </aside>
        </>
      )}
    </div>
  );
}

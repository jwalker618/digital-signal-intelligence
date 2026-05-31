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
 *  - Collapsed rail is always visible (60px). It hosts the toggle button
 *    and the persona nav icons.
 *  - Expanded panel (50vw) is a `position: fixed` overlay so it escapes
 *    the (app)/layout.tsx `overflow-hidden`. It shows the same nav items
 *    with labels plus a Settings + Log-out footer.
 *  - Open behaviour is **hover-only and consistent everywhere**: hover
 *    enters after 150ms, leaves after 300ms, Escape and outside-click
 *    close. No click-to-pin — the toggle button only opens (it's there
 *    for keyboard a11y and touch).
 *  - Collapsed + expanded states render the nav block at the SAME vertical
 *    position so menu items never shift up/down when the panel opens.
 */
export function PersonaSidebar({
  persona,
  isActive = defaultIsActive,
}: PersonaSidebarProps) {
  const pathname = usePathname();
  const router = useRouter();
  const nav = PERSONA_NAV[persona];

  const logout = useAuthStore((s) => s.logout);

  const onSignOut = async () => {
    await logout();
    router.replace("/login");
  };

  const [expanded, setExpanded] = useState(false);

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

  const open = () => {
    clearTimers();
    setExpanded(true);
  };
  const close = () => {
    clearTimers();
    setExpanded(false);
  };

  const handleEnter = () => {
    if (closeTimer.current) {
      clearTimeout(closeTimer.current);
      closeTimer.current = null;
    }
    if (expanded) return;
    openTimer.current = setTimeout(() => {
      setExpanded(true);
      openTimer.current = null;
    }, HOVER_OPEN_MS);
  };

  const handleLeave = () => {
    if (openTimer.current) {
      clearTimeout(openTimer.current);
      openTimer.current = null;
    }
    closeTimer.current = setTimeout(() => {
      setExpanded(false);
      closeTimer.current = null;
    }, HOVER_CLOSE_MS);
  };

  // Escape closes.
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") close();
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
      close();
    };
    document.addEventListener("pointerdown", onDown);
    return () => document.removeEventListener("pointerdown", onDown);
  }, [expanded]);

  // Tidy up any pending timers on unmount.
  useEffect(() => () => clearTimers(), []);

  // Close on navigation so the overlay doesn't linger on the new page.
  useEffect(() => {
    close();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [pathname]);

  return (
    <div
      ref={wrapRef}
      onMouseEnter={handleEnter}
      onMouseLeave={handleLeave}
      className="contents"
    >
      {/* Collapsed rail — always visible, lives in the flex layout. */}
      <aside
        className="chrome-sidebar relative z-10 flex h-full w-[60px] shrink-0 flex-col items-center py-3.5"
        aria-label={`${persona} navigation`}
      >
        <button
          type="button"
          onClick={open}
          aria-label="Expand sidebar"
          aria-expanded={expanded}
          className="flex h-[38px] w-[38px] items-center justify-center rounded-lg text-white/60 transition-colors hover:bg-white/10 hover:text-white"
        >
          <PanelLeftOpen size={20} />
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
          the (app)/layout.tsx overflow-hidden clip. The header structure
          mirrors the collapsed rail (toggle → rule divider → nav) so the
          first nav item stays at the same Y position across both states. */}
      {expanded && (
        <>
          <div
            className="fixed inset-0 z-40 bg-black/30"
            aria-hidden
            onClick={close}
          />
          <aside
            className="chrome-sidebar fixed left-0 top-0 z-50 flex h-screen w-[50vw] min-w-[320px] flex-col py-3.5 pl-[11px] pr-4"
            aria-label={`${persona} navigation expanded`}
            onMouseEnter={handleEnter}
            onMouseLeave={handleLeave}
          >
            {/* Toggle + divider sit in a 38px-wide column so their X position
                matches the collapsed rail's centered icons exactly — no nav
                shift when the panel opens. */}
            <button
              type="button"
              onClick={close}
              aria-label="Collapse sidebar"
              aria-expanded={expanded}
              className="flex h-[38px] w-[38px] shrink-0 items-center justify-center rounded-lg text-white/60 transition-colors hover:bg-white/10 hover:text-white"
            >
              <PanelLeftClose size={20} />
            </button>
            <span
              className="mt-2 mb-3 h-px w-6 shrink-0 bg-white/15"
              style={{ marginLeft: 7 }}
              aria-hidden
            />
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
                      "relative flex h-[38px] items-center gap-3 rounded-lg pl-0 pr-2.5 text-[14px] font-medium text-white/70 transition-colors hover:bg-white/[0.08] hover:text-white",
                      active && "bg-white/10 text-white",
                    )}
                  >
                    {active && (
                      <span className="absolute -left-[11px] top-2 bottom-2 w-[3px] rounded-sm bg-spot" />
                    )}
                    <span className="flex h-[38px] w-[38px] shrink-0 items-center justify-center">
                      <Icon size={20} />
                    </span>
                    <span>{n.name}</span>
                  </Link>
                );
              })}
            </nav>
            <div className="mt-auto flex flex-col gap-1 border-t border-white/10 pt-2.5">
              <Link
                href="/profile"
                aria-label="Settings"
                className="flex h-[38px] items-center gap-3 rounded-lg pl-0 pr-2.5 text-[14px] font-medium text-white/70 transition-colors hover:bg-white/[0.08] hover:text-white"
              >
                <span className="flex h-[38px] w-[38px] shrink-0 items-center justify-center">
                  <Settings size={18} />
                </span>
                <span>Settings</span>
              </Link>
              <button
                type="button"
                onClick={onSignOut}
                className="flex h-[38px] items-center gap-3 rounded-lg pl-0 pr-2.5 text-left text-[14px] font-medium text-white/70 transition-colors hover:bg-white/[0.08] hover:text-white"
              >
                <span className="flex h-[38px] w-[38px] shrink-0 items-center justify-center">
                  <LogOut size={18} />
                </span>
                <span>Log out</span>
              </button>
            </div>
          </aside>
        </>
      )}
    </div>
  );
}

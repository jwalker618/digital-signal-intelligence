"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Settings, type LucideIcon } from "lucide-react";
import { cn } from "@/lib/utils";
import {
  PORTAL_CLIENT_CHILDREN,
  PORTAL_BROKER_CHILDREN,
  PORTAL_CARRIER_CHILDREN,
  ADMIN_CHILDREN,
  type AdminNavLeaf,
} from "@/components/layout/navConfig";

interface PersonaSidebarProps {
  nav: AdminNavLeaf[];
  isActive?: (href: string, pathname: string) => boolean;
}

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

/**
 * Persona icon rail. Dark chrome in both themes. Active item gets a coral
 * accent rail on its left, matching the reimagined design.
 */
export function PersonaSidebar({
  nav,
  isActive = defaultIsActive,
}: PersonaSidebarProps) {
  const pathname = usePathname();
  return (
    <aside className="chrome-sidebar relative flex h-full w-[72px] shrink-0 flex-col items-center py-[18px]">
      <Link
        href={nav[0]?.href ?? "/"}
        className="mb-[22px] flex h-9 w-9 items-center justify-center rounded-lg"
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
      <div className="mt-auto flex w-full flex-col items-center gap-1">
        <Link
          href="/profile"
          aria-label="Account"
          className="flex h-[38px] w-[38px] items-center justify-center rounded-lg text-white/55 hover:text-white"
        >
          <Settings size={18} />
        </Link>
      </div>
    </aside>
  );
}

/** Convenience map — pick a persona's nav by key. */
export const SIDEBAR_NAV = {
  client: PORTAL_CLIENT_CHILDREN,
  broker: PORTAL_BROKER_CHILDREN,
  carrier: PORTAL_CARRIER_CHILDREN,
  admin: ADMIN_CHILDREN,
};

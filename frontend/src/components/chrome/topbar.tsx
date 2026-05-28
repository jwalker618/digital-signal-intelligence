"use client";

import { Building2, Moon, Sun } from "lucide-react";
import { Avatar } from "@/components/ui/avatar";
import { cn } from "@/lib/utils";
import { useAuthStore } from "@/store/authStore";
import { useThemeStore } from "@/store/themeStore";

interface TopbarProps {
  /** Breadcrumb segments. The last one is rendered as the active page. */
  crumbs: string[];
  /**
   * Optional context badge next to the right-side actions — used to show
   * the active entity (e.g. "Acme Industries") on persona pages.
   */
  entity?: string;
  /** Per-page actions slotted before the badge/avatar. */
  actions?: React.ReactNode;
}

/**
 * Application topbar. Persona-aware via the breadcrumb prop; entity
 * context, custom actions, theme toggle, and avatar live on the right.
 */
export function Topbar({ crumbs, entity, actions }: TopbarProps) {
  const user = useAuthStore((s) => s.user);
  const isDark = useThemeStore((s) => s.isDark);
  const toggle = useThemeStore((s) => s.toggleDark);

  const initials =
    (user?.email
      ?.split("@")[0]
      ?.split(/[._-]/)
      .map((p) => p[0] ?? "")
      .join("")
      .slice(0, 2)
      .toUpperCase() ||
      user?.email?.slice(0, 2).toUpperCase()) ??
    "—";

  return (
    <header className="flex h-16 items-center justify-between border-b border-rule bg-canvas px-8">
      <nav className="flex items-center gap-3.5 text-[14px] text-ink-soft" aria-label="Breadcrumb">
        {crumbs.map((c, i) => {
          const last = i === crumbs.length - 1;
          return (
            <span key={`${c}-${i}`} className="flex items-center gap-3.5">
              {i > 0 && <span className="text-ink-mute">/</span>}
              <span className={cn(last && "font-semibold text-ink")}>{c}</span>
            </span>
          );
        })}
      </nav>
      <div className="flex items-center gap-4">
        {actions}
        {entity && (
          <span className="inline-flex items-center gap-1.5 rounded-full border border-rule bg-surface px-2.5 py-1.5 text-xs text-ink-soft">
            <Building2 size={13} aria-hidden />
            {entity}
          </span>
        )}
        <button
          type="button"
          onClick={toggle}
          aria-label="Toggle dark mode"
          className="flex h-8 w-8 items-center justify-center rounded-full text-ink-soft hover:bg-surface-sunken"
        >
          {isDark ? <Sun size={16} /> : <Moon size={16} />}
        </button>
        <Avatar initials={initials} />
      </div>
    </header>
  );
}

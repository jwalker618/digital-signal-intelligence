"use client";

import { Building2, Moon, Sun } from "lucide-react";
import { cn } from "@/lib/utils";
import { useThemeStore } from "@/store/themeStore";

interface TopbarProps {
  crumbs: string[];
  entity?: string;
  actions?: React.ReactNode;
}

// Persona crumbs that pages pass as the first segment but the user wants
// stripped from display ("just start with a /").
const PORTAL_CRUMBS = new Set([
  "Carrier Portal",
  "Client Portal",
  "Broker Portal",
  "Admin",
]);

export function Topbar({ crumbs, entity, actions }: TopbarProps) {
  const isDark = useThemeStore((s) => s.isDark);
  const toggle = useThemeStore((s) => s.toggleDark);

  const display = crumbs.length > 0 && PORTAL_CRUMBS.has(crumbs[0]!)
    ? crumbs.slice(1)
    : crumbs;

  return (
    <header className="flex h-16 items-center justify-between border-b border-rule bg-canvas px-8">
      <nav className="flex items-center gap-3.5 text-[14px] text-ink-soft" aria-label="Breadcrumb">
        <span className="text-ink-mute" aria-hidden>/</span>
        {display.map((c, i) => {
          const last = i === display.length - 1;
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
      </div>
    </header>
  );
}

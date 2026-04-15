/**
 * StatusPill — uppercase coloured badge for decision/action/tone labels.
 *
 * Wraps the `bg-dsi-<tone>/15 text-dsi-<tone>` pattern used 15+ times
 * across the workbench. Pass either a `palette` + `status` pair (to look
 * the entry up by key) or a raw `tone` for ad-hoc use.
 */

import "@/app/globals.css";
import { LucideIcon } from "lucide-react";

import {
  StatusPaletteEntry,
  TONE_PALETTE,
  getStatusStyle,
} from "@/lib/statusPalette";

export type StatusTone = keyof typeof TONE_PALETTE;

export interface StatusPillProps {
  /** Pill label — usually the status name, rendered uppercase. */
  children: React.ReactNode;
  /** Optional leading icon. */
  lucideIcon?: LucideIcon;
  /**
   * Either provide a palette + status key to look up, or pass `tone`
   * directly for a generic positive/negative/warning/info/muted chip.
   */
  palette?: Record<string, StatusPaletteEntry>;
  status?: string | null;
  tone?: StatusTone;
  /** `"sm"` (default) = 10px / `"md"` = xs. */
  size?: "sm" | "md";
}

export default function StatusPill({
  children,
  lucideIcon: Icon,
  palette,
  status,
  tone,
  size = "sm",
}: StatusPillProps) {
  const entry: StatusPaletteEntry = tone
    ? TONE_PALETTE[tone]
    : palette
      ? getStatusStyle(palette, status)
      : TONE_PALETTE.muted;

  const sizeClass =
    size === "md"
      ? "text-xs px-2 py-1 gap-1.5"
      : "text-[10px] px-2 py-0.5 gap-1";

  return (
    <span
      className={`inline-flex items-center rounded font-bold uppercase tracking-wide whitespace-nowrap ${entry.bg} ${entry.text} ${sizeClass}`}
    >
      {Icon && <Icon className="w-3 h-3" />}
      {children}
    </span>
  );
}

// Null-safe coercion helpers shared across the portal pages. Centralised
// so the workbench tabs (and friends) stop each redefining identical
// copies. All return null/"—"-friendly values for missing data.

import { formatCurrency } from "@/lib/format";

export function numOrNull(v: unknown): number | null {
  if (v == null) return null;
  const n = Number(v);
  return Number.isFinite(n) ? n : null;
}

export function strOrNull(v: unknown): string | null {
  if (v == null) return null;
  const s = String(v).trim();
  return s.length > 0 ? s : null;
}

export function boolOrNull(v: unknown): boolean | null {
  if (v == null) return null;
  return Boolean(v);
}

/** A JSONB rate stored as a fraction (0.125) → percentage number (12.5). */
export function pctOrNull(v: unknown): number | null {
  const n = numOrNull(v);
  return n == null ? null : n * 100;
}

/** Compact $ — $1.2M / $185k / $940. Falls back to full currency < $1k. */
export function compactCurrency(v: number | null | undefined): string {
  if (v == null) return "—";
  const abs = Math.abs(v);
  if (abs >= 1_000_000)
    return `${v < 0 ? "-" : ""}$${(abs / 1_000_000).toFixed(abs >= 10_000_000 ? 0 : 1)}M`;
  if (abs >= 1_000) return `${v < 0 ? "-" : ""}$${Math.round(abs / 1_000)}k`;
  return formatCurrency(v);
}

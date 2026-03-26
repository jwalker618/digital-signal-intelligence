/**
 * Shared formatting utilities used across all tabs.
 */

export const formatNum = (num: number | null | undefined, decimals = 1): string =>
  num != null ? Number(num).toFixed(decimals) : "-";

export const formatDollar = (num: number | null | undefined): string =>
  num != null ? `$${Number(num).toLocaleString(undefined, { maximumFractionDigits: 0 })}` : "-";

export const formatPct = (num: number | null | undefined): string =>
  num != null ? `${(Number(num) * 100).toFixed(0)}%` : "-";

export const formatKey = (key: string): string =>
  key.replace(/_/g, ' ').toUpperCase();

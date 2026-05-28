/**
 * Shared utilities used across all tabs.
 */

import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

/** Tailwind-aware className merger. Used by every cva-driven primitive. */
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export const getJSONBItems = (
  data: Record<string, any> | null | undefined,
) => {
  if (!data) return [];

  // Map entries into a flat object structure { name: string, ...details } and return
  return Object.entries(data).map(([key, value]) => ({
    name: key,
    ...value,
  }));
};

export const getSortedItems = (
  data: Record<string, any> | null | undefined,
  sortBy: string | null = null,
  parentExclude: string | null = null,
) => {

  const items = getJSONBItems(data);

  const filteredItems = parentExclude ? items.filter((item) => item.name !== parentExclude) : items;

  if (!sortBy) return filteredItems;
  
  return filteredItems.sort((a, b) => (b[sortBy] ?? 0) - (a[sortBy] ?? 0));
};

export const getOtherRow = (
  data: any[] | null | undefined, 
  sumKeys: string[],              
  limit: number = 3,              
) => {
  if (!data || !Array.isArray(data)) return [];

  const others = data.slice(limit);

  if (others.length > 0) {
    const othersRow = {
      name: 'Others',
      ...sumKeys.reduce((acc, key) => ({
        ...acc,
        [key]: others.reduce((sum, curr) => sum + (curr[key] || 0), 0)
      }), {})
    };
    return [othersRow];
  }
  
  return [];
};

export function fmtRelative(s: string | null | undefined): string {
  if (!s) return "—";
  try {
    const d = new Date(s).getTime();
    const diff = Date.now() - d;
    const minutes = Math.round(diff / 60_000);
    if (minutes < 1) return "just now";
    if (minutes < 60) return `${minutes}m ago`;
    const hours = Math.round(minutes / 60);
    if (hours < 24) return `${hours}h ago`;
    const days = Math.round(hours / 24);
    return `${days}d ago`;
  } catch {
    return s;
  }
}

/**
 * Shared data-shaping helpers for score-group tables.
 *
 * NOTE: The original import from `@/lib/utils` in SummarySAFE.tsx pointed at
 * a file that did not exist. These implementations were reconstructed from
 * observed call-sites — adjust if the real semantics differ.
 */

/**
 * Turns a map of `{ key: item }` into a sorted array, attaching the key onto
 * each item as `.name`. Entries whose key ends with `excludeSuffix` (typically
 * "_composite" for roll-up rows) are filtered out before sorting.
 */
export function getSortedItems<T extends Record<string, unknown>>(
  map: Record<string, T> | null | undefined,
  sortKey: string,
  excludeSuffix?: string,
): Array<T & { name: string }> {
  if (!map) return [];

  return Object.entries(map)
    .filter(([k]) => !excludeSuffix || !k.endsWith(excludeSuffix))
    .map(([k, v]) => ({ ...(v as T), name: k }))
    .sort((a, b) => {
      const av = (a as Record<string, unknown>)[sortKey] as number | undefined;
      const bv = (b as Record<string, unknown>)[sortKey] as number | undefined;
      return (bv ?? 0) - (av ?? 0);
    });
}

/**
 * Collapses any items beyond the top-3 of `items` into a single "Other" row,
 * summing the given numeric fields across the tail.
 * Returns `[]` if there is nothing to aggregate, `[row]` otherwise.
 */
export function getOtherRow<T extends Record<string, unknown>>(
  items: T[],
  sumFields: string[],
): Array<Record<string, unknown> & { name: string }> {
  const rest = items.slice(3);
  if (rest.length === 0) return [];

  const row: Record<string, unknown> = { name: `Other (${rest.length})` };
  for (const field of sumFields) {
    row[field] = rest.reduce(
      (acc: number, r) => acc + ((r[field] as number | undefined) ?? 0),
      0,
    );
  }
  return [row as Record<string, unknown> & { name: string }];
}

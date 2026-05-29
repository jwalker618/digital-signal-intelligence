"use client";

import { useEffect, useRef } from "react";

/**
 * Fire-and-forget fetch coordinator for tab pages.
 *
 * Replaces the common `useEffect → setState("loading") → fetch()` pattern
 * with one that:
 *   - only fires the fetch when `enabled` is true and the inputs change
 *   - does NOT track a local loading state (avoids the "loading flash"
 *     when the store fetcher is already cached and returns synchronously)
 *   - is idempotent under React StrictMode double-invocation in dev
 *     because the fetcher itself owns the cache key
 *
 * Tab pages read data directly from the store; loading is implied by
 * empty/null store state. Pages render a skeleton until data arrives.
 *
 * Usage:
 *   useEnsureFetched(coverage, fetchLossAnalytics);
 *
 * The fetcher is expected to be cache-aware (see fetchLossAnalytics in
 * dsiStore — bails when its analyticsKey matches the input). For
 * cache-less fetchers, callers can still rely on the in-flight guard
 * (the hook short-circuits when the input hasn't changed since the
 * last call).
 */
export function useEnsureFetched<T extends string | undefined | null>(
  input: T,
  fetcher: (arg: NonNullable<T>) => Promise<unknown>,
): void {
  const lastInput = useRef<T | "__init__">("__init__");
  useEffect(() => {
    if (input == null) return;
    if (lastInput.current === input) return;
    lastInput.current = input;
    fetcher(input as NonNullable<T>).catch(() => {
      // Errors surface via store state — tab pages render their own
      // error/empty UI. Re-throwing here would just spam the console.
    });
  }, [input, fetcher]);
}

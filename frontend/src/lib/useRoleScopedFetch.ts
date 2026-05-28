"use client";

// Shared "fetch with role gate" hook used by every broker / client
// page. Replaces the cancelled-flag + try/catch effect that every
// page used to inline. The hook owns:
//   - loading state (true while the fetcher is in flight, false otherwise)
//   - error state (string message, null when ok)
//   - data state (the fetcher's resolved value, null until first success)
//   - cleanup on unmount or dep change
//   - gating: when enabled is false (e.g., wrong role, no token yet) the
//     fetcher is not called and loading flips to false immediately
//
// Usage:
//   const { data, error, loading } = useRoleScopedFetch({
//     fetcher: () => fetchCarriers(accessToken),
//     enabled: !!accessToken && userRole === "BROKER",
//   });

import { useCallback, useEffect, useState } from "react";


export interface UseRoleScopedFetchOptions<T> {
  /** The fetcher to call. Closes over whatever state it needs. */
  fetcher: () => Promise<T>;
  /** When false, the fetcher is NOT called -- caller is expected to render a RoleGate or wait-for-token state. */
  enabled: boolean;
  /** Optional additional dependencies. The hook always re-runs when `enabled` flips. */
  deps?: unknown[];
}


export interface UseRoleScopedFetchResult<T> {
  data: T | null;
  error: string | null;
  loading: boolean;
  /** Re-run the fetcher (caller can wire this to a refresh button). */
  reload: () => void;
}


export function useRoleScopedFetch<T>(
  opts: UseRoleScopedFetchOptions<T>,
): UseRoleScopedFetchResult<T> {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState<boolean>(opts.enabled);
  const [tick, setTick] = useState(0);

  const reload = useCallback(() => setTick((t) => t + 1), []);

  useEffect(() => {
    if (!opts.enabled) {
      setLoading(false);
      return;
    }

    let cancelled = false;
    setLoading(true);
    setError(null);

    opts.fetcher()
      .then((value) => {
        if (cancelled) return;
        setData(value);
        setLoading(false);
      })
      .catch((err: unknown) => {
        if (cancelled) return;
        setError(err instanceof Error ? err.message : String(err));
        setLoading(false);
      });

    return () => { cancelled = true; };
    // We intentionally do NOT track `fetcher` in deps -- callers
    // typically construct a new function on every render. They pass
    // their real deps via `opts.deps`.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [opts.enabled, tick, ...(opts.deps ?? [])]);

  return { data, error, loading, reload };
}

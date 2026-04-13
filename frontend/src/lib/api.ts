// FE: shared REST helper for authenticated calls.
//
// Every admin/world-engine/loss/recalibration page goes through this:
// - injects the bearer token via authStore.authorizedFetch()
// - auto-refreshes if the access token is within 30s of expiry
// - returns parsed JSON, throws Error with the server's message on !ok

import { useAuthStore } from "@/store/authStore";

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "";

export function apiUrl(path: string): string {
  return `${API_BASE}${path}`;
}

async function doRequest<T>(
  method: string,
  path: string,
  body?: unknown,
): Promise<T> {
  const fetcher = useAuthStore.getState().authorizedFetch;
  const res = await fetcher(apiUrl(path), {
    method,
    headers: body !== undefined ? { "Content-Type": "application/json" } : undefined,
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });
  const text = await res.text();
  const parsed = text ? JSON.parse(text) : null;
  if (!res.ok) {
    const msg =
      (parsed && (parsed.error || parsed.detail)) || `HTTP ${res.status}`;
    const err = new Error(msg) as Error & { status?: number };
    err.status = res.status;
    throw err;
  }
  return parsed as T;
}

export const api = {
  get: <T = unknown>(path: string) => doRequest<T>("GET", path),
  post: <T = unknown>(path: string, body?: unknown) =>
    doRequest<T>("POST", path, body ?? {}),
  put: <T = unknown>(path: string, body?: unknown) =>
    doRequest<T>("PUT", path, body ?? {}),
  patch: <T = unknown>(path: string, body?: unknown) =>
    doRequest<T>("PATCH", path, body ?? {}),
  delete: <T = unknown>(path: string) => doRequest<T>("DELETE", path),
};

// Utility for date/number formatting that pages use pervasively.
export function fmtDate(s: string | null | undefined): string {
  if (!s) return "—";
  try {
    const d = new Date(s);
    return d.toLocaleString();
  } catch {
    return s;
  }
}

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

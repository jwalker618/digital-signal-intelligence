// A-3a: Thin fetch wrappers around /api/v1/auth/*.
//
// No React, no Zustand here -- just typed calls that the auth store
// (and a handful of auth pages) consume.

import type {
  AuthUser,
  LoginResponse,
  MFASetupResponse,
  SSOStartResponse,
  TokenPair,
} from "@/types/auth";

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "";

function apiUrl(path: string): string {
  // Paths always start with /api/v1/... -- we allow a relative base
  // so Next.js `rewrites` can proxy in dev.
  return `${API_BASE}${path}`;
}

async function parseJsonOrError(res: Response): Promise<any> {
  const text = await res.text();
  const body = text ? JSON.parse(text) : null;
  if (!res.ok) {
    const message =
      (body && (body.error || body.detail)) || `HTTP ${res.status}`;
    const err = new Error(message) as Error & { status?: number };
    err.status = res.status;
    throw err;
  }
  return body;
}

function authHeaders(accessToken: string | null): Record<string, string> {
  return accessToken ? { Authorization: `Bearer ${accessToken}` } : {};
}

// =============================================================================
// Login / refresh / logout
// =============================================================================

export async function login(
  email: string,
  password: string,
): Promise<LoginResponse> {
  const res = await fetch(apiUrl("/api/v1/auth/login"), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password, }),
  });
  return parseJsonOrError(res);
}

export async function refresh(refreshToken: string): Promise<TokenPair> {
  const res = await fetch(apiUrl("/api/v1/auth/refresh"), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ refresh_token: refreshToken }),
  });
  return parseJsonOrError(res);
}

export async function logout(refreshToken: string): Promise<void> {
  await fetch(apiUrl("/api/v1/auth/logout"), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ refresh_token: refreshToken }),
  });
}

// =============================================================================
// MFA
// =============================================================================

export async function mfaSetup(accessToken: string): Promise<MFASetupResponse> {
  const res = await fetch(apiUrl("/api/v1/auth/mfa/setup"), {
    method: "POST",
    headers: authHeaders(accessToken),
  });
  return parseJsonOrError(res);
}

export async function mfaVerify(
  accessToken: string,
  code: string,
): Promise<{ mfa_enabled: boolean }> {
  const res = await fetch(apiUrl("/api/v1/auth/mfa/verify"), {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...authHeaders(accessToken),
    },
    body: JSON.stringify({ code }),
  });
  return parseJsonOrError(res);
}

export async function mfaBackupCodes(
  accessToken: string,
): Promise<{ codes: string[] }> {
  const res = await fetch(apiUrl("/api/v1/auth/mfa/backup-codes"), {
    method: "POST",
    headers: authHeaders(accessToken),
  });
  return parseJsonOrError(res);
}

// =============================================================================
// SSO
// =============================================================================

export async function ssoStart(tenantSlug: string): Promise<SSOStartResponse> {
  const res = await fetch(
    apiUrl(`/api/v1/auth/sso/${encodeURIComponent(tenantSlug)}`),
  );
  return parseJsonOrError(res);
}

// =============================================================================
// Password management
// =============================================================================

export async function passwordResetRequest(email: string): Promise<void> {
  await fetch(apiUrl("/api/v1/auth/password/reset-request"), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email }),
  });
}

export async function passwordResetConfirm(
  token: string,
  newPassword: string,
): Promise<void> {
  const res = await fetch(apiUrl("/api/v1/auth/password/reset-confirm"), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ token, new_password: newPassword }),
  });
  if (!res.ok) {
    await parseJsonOrError(res); // throws
  }
}

// =============================================================================
// Me
// =============================================================================

export async function me(accessToken: string): Promise<AuthUser> {
  const res = await fetch(apiUrl("/api/v1/auth/me"), {
    headers: authHeaders(accessToken),
  });
  return parseJsonOrError(res);
}

// =============================================================================
// Authorized fetch wrapper
// =============================================================================

/**
 * Fetch with Authorization header injected. Caller is responsible for
 * handling 401 by triggering a refresh (see authStore.authorizedFetch).
 */
export async function authorizedFetch(
  accessToken: string | null,
  input: RequestInfo | URL,
  init?: RequestInit,
): Promise<Response> {
  const headers = new Headers(init?.headers);
  if (accessToken) headers.set("Authorization", `Bearer ${accessToken}`);
  return fetch(input, { ...init, headers });
}

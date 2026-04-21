// A-3a: Auth store (Zustand)
//
// Owns auth tokens, the authenticated user profile, and the permission
// list. Consumers:
//   - SessionGuard: reads isAuthenticated + sessionExpiresAt
//   - Login / MFA pages: call login(), verifyMFA()
//   - Layout nav: calls hasPermission(perm) to gate items
//   - API clients: call authorizedFetch() to inject the bearer token
//
// Persisted to localStorage (refresh token + user) so a reload doesn't
// force re-login. Access tokens are kept in-memory only -- they are
// short-lived (15min) and we refresh from the refresh token on boot.

"use client";

import { create } from "zustand";
import { persist, createJSONStorage } from "zustand/middleware";

import type { AuthUser } from "@/types/auth";
import {
  login as apiLogin,
  logout as apiLogout,
  me as apiMe,
  mfaVerify as apiMfaVerify,
  refresh as apiRefresh,
  ssoStart as apiSsoStart,
} from "@/lib/authApi";

interface AuthState {
  // --- persisted ---
  user: AuthUser | null;
  refreshToken: string | null;
  sessionExpiresAt: number | null; // ms epoch

  // --- in-memory only ---
  accessToken: string | null;
  mfaChallengePending: boolean;
  error: string | null;
  isBooting: boolean;
  sessionWarning: string | null;

  // --- actions ---
  boot: () => Promise<void>;
  login: (email: string, password: string, ) => Promise<void>;
  verifyMFA: (code: string) => Promise<void>;
  loginSSO: (tenantSlug: string) => Promise<void>;
  refresh: () => Promise<boolean>;
  logout: () => Promise<void>;
  setError: (msg: string | null) => void;
  setSessionWarning: (msg: string | null) => void;

  // --- selectors ---
  isAuthenticated: () => boolean;
  hasPermission: (perm: string) => boolean;
  authorizedFetch: (
    input: RequestInfo | URL,
    init?: RequestInit,
  ) => Promise<Response>;
}

const REFRESH_LEEWAY_MS = 30_000; // refresh 30s before expiry

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      user: null,
      refreshToken: null,
      sessionExpiresAt: null,
      accessToken: null,
      mfaChallengePending: false,
      error: null,
      isBooting: true,
      sessionWarning: null,

      boot: async () => {
        // On app load: if we have a refresh token, swap it for a fresh
        // access token and reload /me.
        const { refreshToken } = get();
        if (!refreshToken) {
          set({ isBooting: false });
          return;
        }
        try {
          const pair = await apiRefresh(refreshToken);
          const user = await apiMe(pair.access_token);
          set({
            accessToken: pair.access_token,
            refreshToken: pair.refresh_token,
            sessionExpiresAt: Date.now() + pair.expires_in_seconds * 1000,
            user,
            isBooting: false,
            mfaChallengePending: false,
          });
        } catch {
          set({
            accessToken: null,
            refreshToken: null,
            sessionExpiresAt: null,
            user: null,
            isBooting: false,
          });
        }
      },

      login: async (email, password) => {
        set({ error: null });
        const resp = await apiLogin(email, password);
        set({
          accessToken: resp.access_token,
          refreshToken: resp.refresh_token,
          sessionExpiresAt: Date.now() + resp.expires_in_seconds * 1000,
          mfaChallengePending: resp.mfa_required,
        });
        if (!resp.mfa_required) {
          const user = await apiMe(resp.access_token);
          set({ user });
        }
      },

      verifyMFA: async (code) => {
        const token = get().accessToken;
        if (!token) throw new Error("Not logged in");
        await apiMfaVerify(token, code);
        const user = await apiMe(token);
        set({ user, mfaChallengePending: false });
      },

      loginSSO: async (tenantSlug) => {
        const resp = await apiSsoStart(tenantSlug);
        if (typeof window !== "undefined") {
          window.location.assign(resp.redirect_url);
        }
      },

      refresh: async () => {
        const { refreshToken } = get();
        if (!refreshToken) return false;
        try {
          const pair = await apiRefresh(refreshToken);
          set({
            accessToken: pair.access_token,
            refreshToken: pair.refresh_token,
            sessionExpiresAt: Date.now() + pair.expires_in_seconds * 1000,
          });
          return true;
        } catch {
          set({
            accessToken: null,
            refreshToken: null,
            sessionExpiresAt: null,
            user: null,
          });
          return false;
        }
      },

      logout: async () => {
        const { refreshToken } = get();
        if (refreshToken) {
          try {
            await apiLogout(refreshToken);
          } catch {
            // best-effort -- we'll wipe local state regardless
          }
        }
        set({
          user: null,
          accessToken: null,
          refreshToken: null,
          sessionExpiresAt: null,
          mfaChallengePending: false,
        });
      },

      setError: (msg) => set({ error: msg }),

      setSessionWarning: (msg) => set({ sessionWarning: msg }),

      isAuthenticated: () => {
        const s = get();
        if (!s.user || !s.accessToken || !s.sessionExpiresAt) return false;
        if (s.mfaChallengePending) return false;
        return s.sessionExpiresAt > Date.now();
      },

      hasPermission: (perm) => {
        const s = get();
        return Boolean(s.user?.permissions?.includes(perm));
      },

      authorizedFetch: async (input, init) => {
        let token = get().accessToken;
        const expires = get().sessionExpiresAt ?? 0;
        if (token && expires - Date.now() < REFRESH_LEEWAY_MS) {
          const ok = await get().refresh();
          if (ok) token = get().accessToken;
        }
        const headers = new Headers(init?.headers);
        if (token) headers.set("Authorization", `Bearer ${token}`);
        return fetch(input, { ...init, headers });
      },
    }),
    {
      name: "dsi-auth",
      storage: createJSONStorage(() => {
        if (typeof window === "undefined") {
          // SSR safe stub
          return {
            getItem: () => null,
            setItem: () => undefined,
            removeItem: () => undefined,
          } as Storage;
        }
        return window.localStorage;
      }),
      partialize: (state) => ({
        user: state.user,
        refreshToken: state.refreshToken,
        sessionExpiresAt: state.sessionExpiresAt,
      }),
    },
  ),
);

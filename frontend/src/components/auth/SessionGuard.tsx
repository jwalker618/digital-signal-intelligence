// A-3f: Session guard.
//
// Wraps the app. Responsibilities:
//   - Trigger authStore.boot() on first mount (refresh from persisted
//     refresh_token, fetch /me, populate user).
//   - Redirect to /login if the session is missing or expired.
//   - Auto-refresh on token near-expiry.
//   - Publish a session-expiry warning string to authStore 30 minutes
//     before expiry; TitleBar renders it.
//
// Public pages (/login, /reset-password, /sso/callback) bypass the guard.

"use client";

import { useEffect, useRef } from "react";
import { usePathname, useRouter } from "next/navigation";
import { Loader2 } from "lucide-react";

import { useAuthStore } from "@/store/authStore";
import {
  homePathForRole, isBrokerPath, isCarrierPath, isClientPath,
} from "@/lib/portalPaths";

const PUBLIC_PATHS = ["/login", "/reset-password", "/sso/callback"];
const WARN_THRESHOLD_MS = 30 * 60 * 1000;
const REFRESH_THRESHOLD_MS = 2 * 60 * 1000;

export function SessionGuard({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();

  const boot = useAuthStore((s) => s.boot);
  const isBooting = useAuthStore((s) => s.isBooting);
  const sessionExpiresAt = useAuthStore((s) => s.sessionExpiresAt);
  const refresh = useAuthStore((s) => s.refresh);
  const setSessionWarning = useAuthStore((s) => s.setSessionWarning);
  // Subscribe to the computed boolean, not the function reference, so the
  // guard re-runs its redirect effect whenever auth state actually changes.
  const isAuthed = useAuthStore((s) => s.isAuthenticated());
  const userRole = useAuthStore((s) => s.user?.role ?? null);

  const bootedRef = useRef(false);

  // Boot once
  useEffect(() => {
    if (bootedRef.current) return;
    bootedRef.current = true;
    void boot();
  }, [boot]);

  // Auth + role-vs-path gate
  useEffect(() => {
    if (isBooting) return;
    const isPublic = PUBLIC_PATHS.some((p) => pathname?.startsWith(p));
    if (isPublic) return;

    if (!isAuthed) {
      const next = encodeURIComponent(pathname ?? "/");
      router.replace(`/login?next=${next}`);
      return;
    }

    // Enforce role <-> persona URL tree. Every authenticated user gets
    // bounced to their persona home if they land on a different
    // persona's tree (or on / itself, which has no UI of its own).
    // Stops chrome mismatches (wrong sidebar, leaked breadcrumbs) that
    // happen when a user opens a path their role doesn't own.
    if (userRole) {
      const home = homePathForRole(userRole);
      const onOwnTree =
        (home === "/carrier" && isCarrierPath(pathname)) ||
        (home === "/broker"  && isBrokerPath(pathname))  ||
        (home === "/client"  && isClientPath(pathname));

      // Admin tree + the user-account /profile + /login + the mobile
      // companion (/m) are persona-agnostic; don't bounce off them.
      const personaAgnostic =
        !!pathname && (
          pathname === "/profile" || pathname.startsWith("/profile/") ||
          pathname.startsWith("/admin") ||
          pathname === "/m" || pathname.startsWith("/m/")
        );

      if (!onOwnTree && !personaAgnostic) {
        router.replace(home);
      }
    }
  }, [isBooting, isAuthed, pathname, router, userRole]);

  // Expiry watchdog -- refresh/warn/redirect
  useEffect(() => {
    if (!sessionExpiresAt) return;
    const interval = setInterval(() => {
      const remaining = sessionExpiresAt - Date.now();
      if (remaining <= 0) {
        router.replace("/login");
        return;
      }
      if (remaining < REFRESH_THRESHOLD_MS) {
        void refresh();
      } else if (remaining < WARN_THRESHOLD_MS) {
        const mins = Math.ceil(remaining / 60_000);
        setSessionWarning(`Session expires in ${mins} minute${mins === 1 ? "" : "s"}.`);
      } else {
        setSessionWarning(null);
      }
    }, 15_000);
    return () => clearInterval(interval);
  }, [sessionExpiresAt, refresh, router, setSessionWarning]);

  const isPublic = PUBLIC_PATHS.some((p) => pathname?.startsWith(p));

  if (isBooting && !isPublic) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-canvas">
        <Loader2 className="h-5 w-5 animate-spin text-ink-mute" />
      </div>
    );
  }

  return <>{children}</>;
}

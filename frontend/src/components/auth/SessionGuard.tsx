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

  const bootedRef = useRef(false);

  // Boot once
  useEffect(() => {
    if (bootedRef.current) return;
    bootedRef.current = true;
    void boot();
  }, [boot]);

  // Auth gate
  useEffect(() => {
    if (isBooting) return;
    const isPublic = PUBLIC_PATHS.some((p) => pathname?.startsWith(p));
    if (isPublic) return;
    if (!isAuthed) {
      const next = encodeURIComponent(pathname ?? "/");
      router.replace(`/login?next=${next}`);
    }
  }, [isBooting, isAuthed, pathname, router]);

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
      <div className="min-h-screen flex items-center justify-center bg-generate-background">
        <Loader2 className="icon animate-spin" />
      </div>
    );
  }

  return <>{children}</>;
}

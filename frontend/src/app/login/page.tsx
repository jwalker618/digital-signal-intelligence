// A-3b: Login page (email/password + SSO redirect).
//
// Public page -- no auth required. On success the auth store holds a
// valid session and SessionGuard in the root layout takes over routing.

"use client";

import { FormEvent, useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";
import { Loader2 } from "lucide-react";

import { useAuthStore } from "@/store/authStore";
import { MFAVerify } from "@/components/auth/MFAVerify";

export default function LoginPage() {
  const router = useRouter();
  const params = useSearchParams();
  const nextPath = params.get("next") ?? "/";

  const login = useAuthStore((s) => s.login);
  const loginSSO = useAuthStore((s) => s.loginSSO);
  // Subscribe to the *result* of isAuthenticated(), not the function
  // reference. The function itself is stable on the Zustand store, so
  // selecting it would never trigger a re-render when the underlying
  // user/token state flips to authenticated after login.
  const isAuthed = useAuthStore((s) => s.isAuthenticated());
  const mfaChallengePending = useAuthStore((s) => s.mfaChallengePending);

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [rememberMe, setRememberMe] = useState(false);
  const [tenantSlug, setTenantSlug] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Once fully authenticated, leave the login page
  useEffect(() => {
    if (isAuthed) router.replace(nextPath);
  }, [isAuthed, nextPath, router]);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setSubmitting(true);
    setError(null);
    try {
      await login(email.trim().toLowerCase(), password, rememberMe);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Login failed");
    } finally {
      setSubmitting(false);
    }
  }

  async function onSSO() {
    if (!tenantSlug.trim()) {
      setError("Enter your tenant identifier");
      return;
    }
    setSubmitting(true);
    setError(null);
    try {
      await loginSSO(tenantSlug.trim());
    } catch (err) {
      setError(err instanceof Error ? err.message : "SSO redirect failed");
      setSubmitting(false);
    }
  }

  return (
    <main className="min-h-screen flex items-center justify-center bg-dsi-background">
      <div className="w-full max-w-md border-3 border-dsi-outline rounded-lg p-8 bg-dsi-contrast-background/5">
        <header className="mb-6">
          <h1 className="font-inter text-3xl tracking-wide">
            Digital Signal Intelligence
          </h1>
          <p className="opacity-70 text-sm mt-1">
            Sign in to continue
          </p>
        </header>

        {mfaChallengePending ? (
          <MFAVerify />
        ) : (
          <>
            <form onSubmit={onSubmit} className="flex flex-col gap-4">
              <label className="flex flex-col gap-1">
                <span className="text-sm opacity-70">Email</span>
                <input
                  type="email"
                  autoComplete="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="border-2 border-dsi-outline bg-dsi-background px-3 py-2 rounded"
                />
              </label>
              <label className="flex flex-col gap-1">
                <span className="text-sm opacity-70">Password</span>
                <input
                  type="password"
                  autoComplete="current-password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="border-2 border-dsi-outline bg-dsi-background px-3 py-2 rounded"
                />
              </label>
              <label className="flex items-center gap-2 text-sm">
                <input
                  type="checkbox"
                  checked={rememberMe}
                  onChange={(e) => setRememberMe(e.target.checked)}
                />
                Remember me on this device
              </label>
              {error && <div className="text-sm text-red-500">{error}</div>}
              <button
                type="submit"
                disabled={submitting}
                className="flex items-center justify-center gap-2 bg-dsi-contrast-background text-dsi-background py-2 rounded font-semibold disabled:opacity-50"
              >
                {submitting && <Loader2 className="icon animate-spin" />}
                Sign in
              </button>
              <Link
                href="/reset-password"
                className="text-sm text-dsi-selected self-center hover:underline"
              >
                Forgot password?
              </Link>
            </form>

            <div className="my-6 flex items-center gap-3 opacity-60">
              <span className="flex-1 border-t border-dsi-outline/40" />
              <span className="text-xs tracking-widest">OR</span>
              <span className="flex-1 border-t border-dsi-outline/40" />
            </div>

            <div className="flex flex-col gap-2">
              <label className="flex flex-col gap-1">
                <span className="text-sm opacity-70">Tenant (for SSO)</span>
                <input
                  value={tenantSlug}
                  onChange={(e) => setTenantSlug(e.target.value)}
                  placeholder="e.g. acme-re"
                  className="border-2 border-dsi-outline bg-dsi-background px-3 py-2 rounded"
                />
              </label>
              <button
                type="button"
                onClick={onSSO}
                disabled={submitting}
                className="border-2 border-dsi-outline text-dsi-contrast-background py-2 rounded hover:bg-dsi-outline/10 disabled:opacity-50"
              >
                Continue with SSO
              </button>
            </div>
          </>
        )}
      </div>
    </main>
  );
}

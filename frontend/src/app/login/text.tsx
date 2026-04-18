// A-3b: Login page (email/password + SSO redirect).
//
// Public page -- no auth required. On success the auth store holds a
// valid session and SessionGuard in the root layout takes over routing.

"use client";

import { FormEvent, useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";
import { Check, Loader2, Lightbulb, LightbulbOff } from "lucide-react";

import { useAuthStore } from "@/store/authStore";
import { MFAVerify } from "@/components/auth/MFAVerify";
import { SidebarIconBtn } from "@/components/layout/nav";

export default function LoginPage() {

  const [isDark, setIsDark] = useState(false);

  useEffect(() => {
    const html = document.documentElement;
    if (isDark) html.classList.add("dark");
    else html.classList.remove("dark");
  }, [isDark]);

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
  
      <main className="h-full w-full bg-dsi-contrast-background">

        <div>
          <img
            src={
              isDark
                ? "/Standard_Generate_Logo_and_DSI.svg"
                : "/BlackWhite_Generate_Logo_and_DSI.svg"
            }
            className="absolute top-dsi-pad left-dsi-pad h-12 w-auto object-contain"
            alt="DSI Logo"
          />
        </div>

        <div className="
          flex
          fixed inset-0 
          items-center 
          justify-center">
          
              

          <div className="
            w-full max-w-md 
            border-3 border-dsi-outline 
            rounded-lg 
            p-dsi-main
            bg-dsi-background">
              
            <header className="mb-6">


              <div className="flex items-center justify-between">
                
                <p className="text-xs text-dsi-contrast-background">Sign in to continue </p>
                <SidebarIconBtn
                  icon={isDark ? LightbulbOff : Lightbulb}
                  onClick={() => setIsDark(!isDark)}
                  className="text-dsi-contrast-background hover:text-dsi-selected"
                />
              </div>
              
            </header>

            {mfaChallengePending ? (
              <MFAVerify />
            ) : (
              <>
                <form onSubmit={onSubmit} className="flex flex-col gap-4">
                  
                  <label className="flex flex-col gap-1">
                    <span className="text-sm text-dsi-contrast-background">Email</span>
                    <input
                      type="email"
                      autoComplete="email"
                      required
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      className="border-1 border-dsi-outline bg-dsi-background px-2 py-2 rounded text-dsi-selected"
                    />
                  </label>
                  
                  <label className="flex flex-col gap-1">
                    <span className="text-sm text-dsi-contrast-background">Password</span>
                    <input
                      type="password"
                      autoComplete="current-password"
                      required
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      className="border-1 border-dsi-outline bg-dsi-background px-2 py-2 rounded text-dsi-selected"
                    />
                  </label>
                  
                  <label className="flex items-center gap-2 text-sm text-dsi-contrast-background">
                    <input
                      type="checkbox"
                      checked={rememberMe}
                      onChange={(e) => setRememberMe(e.target.checked)}
                      className="peer sr-only"
                    />
                    <div className="
                      icon rounded
                      border-1 border-dsi-outline 
                      peer-checked:bg-dsi-selected"
                      >
                        <Check className="absolute w-3 h-3 ml-1 mt-1 peer-checked:text-dsi-outline" />
                    </div>
                      Remember me on this device
                  </label>

                  {error && <div className="text-sm text-dsi-negative">{error}</div>}
                  <button
                    type="submit"
                    disabled={submitting}
                    className="
                      flex 
                      items-center justify-center 
                      bg-dsi-contrast-background 
                      text-dsi-background
                      hover:text-dsi-selected hover:border-1 border-dsi-selected
                      py-2 
                      rounded
                      font-bold"
                  >
                    {submitting && <Loader2 className="icon animate-spin" />}
                    Sign in
                  </button>
                  <Link
                    href="/reset-password"
                    className="
                      text-xs text-dsi-contrast-background hover:text-dsi-selected
                      self-center 
                      "
                  >
                    Forgot password?
                  </Link>
                </form>

                <div className="my-6 flex items-center gap-3 opacity-60">
                  <span className="flex-1 border-t border-dsi-outline" />
                  <span className="text-xs tracking-widest">OR</span>
                  <span className="flex-1 border-t border-dsi-outline/50" />
                </div>

                <div className="flex flex-col gap-2">
                  <label className="flex flex-col gap-1">
                    <span className="text-sm text-dsi-contrast-background">Tenant (for SSO)</span>
                    <input
                      value={tenantSlug}
                      onChange={(e) => setTenantSlug(e.target.value)}
                      placeholder="e.g. acme-re"
                      className="border-1 border-dsi-outline bg-dsi-background px-2 py-2 rounded text-dsi-contrast-background"
                    />
                  </label>
                  <button
                    type="button"
                    onClick={onSSO}
                    disabled={submitting}
                    className="
                      flex 
                      items-center justify-center 
                      bg-dsi-contrast-background 
                      text-dsi-background
                      hover:text-dsi-selected hover:border-1 border-dsi-selected
                      py-2 
                      rounded
                      font-bold"
                  >
                    Continue with SSO
                  </button>
                </div>
              </>
            )}
          </div>
        </div>

      </main>

  );
}



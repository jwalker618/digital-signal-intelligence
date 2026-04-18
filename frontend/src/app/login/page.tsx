"use client";

import { FormEvent, useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";
import { Check, Loader2, Lightbulb, LightbulbOff } from "lucide-react";

import "@/app/globals.css";
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
    <>
      <div className="flex min-h-full flex-col justify-center px-6 py-12 lg:px-8 bg-dsi-contrast-background">
        
        <div className="sm:mx-auto sm:w-full sm:max-w-sm">
          
          <img
             alt="DSI Logo"
             src={
              isDark
                ? "/Standard_Generate_Logo_and_DSI.svg"
                : "/BlackWhite_Generate_Logo_and_DSI.svg"
            }
            className="w-20 h-20 mx-auto w-auto" 
          />

          <div className="flex items-center justify-between mt-10">
            
            <h2 className="text-center text-2xl/9 font-bold tracking-tight text-dsi-background">
              Sign in to your account
            </h2>
            <SidebarIconBtn
              icon={isDark ? LightbulbOff : Lightbulb}
              onClick={() => setIsDark(!isDark)}
              className="text-dsi-background hover:text-dsi-selected"
            />
          </div>
      
        </div>

        <div className="mt-10 sm:mx-auto sm:w-full sm:max-w-sm">
          <form action="#" method="POST" className="space-y-6">
            <div>
              <label htmlFor="email" className="block text-sm/6 font-medium text-dsi-background">
                Email address
              </label>
              <div className="mt-2">
                <input
                  id="email"
                  name="email"
                  type="email"
                  required
                  autoComplete="email"
                  className="block w-full rounded-md bg-white/5 px-3 py-1.5 text-base text-white outline-1 -outline-offset-1 outline-white/10 placeholder:text-gray-500 focus:outline-2 focus:-outline-offset-2 focus:outline-indigo-500 sm:text-sm/6"
                />
              </div>
            </div>

            <div>
              <div className="flex items-center justify-between">
                <label htmlFor="password" className="block text-sm/6 font-medium text-dsi-background">
                  Password
                </label>
                <div className="text-sm">
                  <a href="#" className="font-semibold text-indigo-400 hover:text-indigo-300">
                    Forgot password?
                  </a>
                </div>
              </div>
              <div className="mt-2">
                <input
                  id="password"
                  name="password"
                  type="password"
                  required
                  autoComplete="current-password"
                  className="block w-full rounded-md bg-white/5 px-3 py-1.5 text-base text-white outline-1 -outline-offset-1 outline-white/10 placeholder:text-gray-500 focus:outline-2 focus:-outline-offset-2 focus:outline-indigo-500 sm:text-sm/6"
                />
              </div>
            </div>

            <div>
              <button
                type="submit"
                className="flex w-full justify-center rounded-md bg-indigo-500 px-3 py-1.5 text-sm/6 font-semibold text-white hover:bg-indigo-400 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-indigo-500"
              >
                Sign in
              </button>
            </div>
          </form>

          <p className="mt-10 text-center text-sm/6 text-gray-400">
            Not a member?{' '}
            <a href="#" className="font-semibold text-indigo-400 hover:text-indigo-300">
              Start a 14 day free trial
            </a>
          </p>
        </div>
      </div>
    </>
  )
}

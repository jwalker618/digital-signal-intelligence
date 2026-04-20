"use client";

import { FormEvent, useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { Loader2, Lightbulb, LightbulbOff } from "lucide-react";

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
  const isAuthed = useAuthStore((s) => s.isAuthenticated());
  const mfaChallengePending = useAuthStore((s) => s.mfaChallengePending);

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
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
      await login(email.trim().toLowerCase(), password,);
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
      <div className="flex min-h-full flex-col justify-center bg-dsi-contrast-background">
        
        <div className="sm:mx-auto sm:w-full sm:max-w-sm">
          
          <img
             alt="DSI Logo"
             src={isDark ? 
              "/Standard_Generate_Logo_and_DSI.svg" : "/BlackWhite_Generate_Logo_and_DSI.svg"
              }
            className="w-20 h-20 mx-auto w-auto" 
          />

          <div className="flex items-center justify-between mt-10 mb-5">
            
            <h2 className="text-center text-2xl font-bold text-dsi-background">
              Sign in to your account
            </h2>
            
            <SidebarIconBtn
              icon={isDark ? LightbulbOff : Lightbulb}
              onClick={() => setIsDark(!isDark)}
              className="text-dsi-background hover:text-dsi-selected"
            />

          </div>
      
        </div>

        {mfaChallengePending ? (
          <MFAVerify />
        ) : (
          <>

          <div className="sm:mx-auto sm:w-full sm:max-w-sm">
            
            <form onSubmit={onSubmit} className="space-y-3">

              <div>
                
                <label 
                  htmlFor="email" 
                  className="
                    block mb-1
                    text-xs text-dsi-background"
                  >Email Address
                </label>
                
                <div> 
                  <input
                    id="email" name="email" type="email" autoComplete="email"
                    required
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    
                    className="w-full dsi-inputbox"
                  />
                </div>
                
              </div>

              <div>
                
                <div className="flex items-center justify-between content-center">
                  <label   
                    htmlFor="password" 
                    className="
                      block mb-1
                      text-xs text-dsi-background
                      ">Password
                    </label>
                </div>
                
                <div>  
                  <input
                    id="password" name="password" type="password" autoComplete="current-password"
                    required
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    
                    className="w-full dsi-inputbox"
                  />
                </div>

              </div>

              <div>

                {error && <div className="text-sm text-dsi-negative">{error}</div>}
                <button
                  id="submit" name="submit" type="submit" disabled={submitting}
                  
                  className="w-full flex flex-col dsi-actionbutton"
                >
                  {submitting && <Loader2 className="icon animate-spin" />}
                  Sign in
                </button>

                <div className="text-sm mt-2">
                  <a href="/login/reset-password" 
                    className="
                      font-bold
                      text-dsi-outline hover:text-dsi-selected">
                    Forgot Password?
                  </a>
                </div>

              </div>
              
            </form>

            <div className="my-6 flex items-center gap-3">
              <span className="flex-1 border-t border-dsi-outline/50" />
              <span className="text-xs tracking-widest text-dsi-selected">OR</span>
              <span className="flex-1 border-t border-dsi-outline/50" />
            </div>

            <div className="flex flex-col">
              
              <label className="flex flex-col">
                <span className="
                  block mb-1
                  text-xs text-dsi-background"
                  >Tenant (for SSO)</span>
                
                <input
                  value={tenantSlug}
                  onChange={(e) => setTenantSlug(e.target.value)}
                  placeholder="e.g. your company domain"
                  
                  className="w-full dsi-inputbox"
                />
              </label>
              
              <button
                type="button"
                onClick={onSSO}
                disabled={submitting}
                
                className="mt-3 dsi-actionbutton"
                > Continue with SSO
              </button>

            </div>
        
          </div>
          
          </>
        )}
      </div>
    </>
  )
}

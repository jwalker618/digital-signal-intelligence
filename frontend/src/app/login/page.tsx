"use client";

import { FormEvent, useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";

import { 
  Loader2, 
  Lightbulb, 
  LightbulbOff,
  PanelBottomClose,
  PanelBottomOpen,
} from "lucide-react";

import "@/app/globals.css";

import { useAuthStore } from "@/store/authStore";
import { useThemeStore } from "@/store/themeStore";
import { MFAVerify } from "@/components/auth/MFAVerify";
import { SidebarIconBtn } from "@/components/layout/nav";

export default function LoginPage() {

  const [isSSO, onToggleSSO] = useState(false);

  const isDark = useThemeStore((s) => s.isDark);
  const toggleDark = useThemeStore((s) => s.toggleDark);

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

        <div>
          <img
              alt="DSI Logo"
              src={isDark ? 
                "/Standard_Generate_Logo_and_DSI.svg" : "/BlackWhite_Generate_Logo_and_DSI.svg"
                }
              className="w-25 h-25 mx-auto w-auto absolute left-dsi-gap top-dsi-gap" 
            />
          <SidebarIconBtn
              icon={isDark ? LightbulbOff : Lightbulb}
              onClick={toggleDark}
              className="text-dsi-background hover:text-dsi-selected absolute right-dsi-gap top-dsi-gap"
            />

        </div>

        <div className="sm:mx-auto sm:w-full sm:max-w-sm">
          <div>
            
            <h2 className="
              flex mt-10 mb-5
              text-center text-2xl font-bold text-dsi-background"
              >Sign in to your account
            </h2>

            <button
              onClick={() => onToggleSSO(prev => !prev)}
              className="
                flex 
                gap-2 mb-4 items-center
                text-dsi-background hover:text-dsi-selected"
            >
              {isSSO ? (
                <PanelBottomOpen className="icon"/> 
              ) : (
                <PanelBottomClose className="icon"/>
              )}{isSSO ? "Tenant (for SSO)" : "Email Address / Password"}
            </button>
          
          </div>
        </div>

        {mfaChallengePending ? ( <MFAVerify/> ) 
        : (
          <>
            
            {isSSO ? (

              <div className="sm:mx-auto sm:w-full sm:max-w-sm">
                <div className="flex flex-col">  
                  <label className="flex flex-col">                     
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

            ) : (

              <div className="sm:mx-auto sm:w-full sm:max-w-sm">

                <form onSubmit={onSubmit} className="space-y-3">

                  <div>
                                       
                    <div> 
                      <input
                        id="email" name="email" type="email" autoComplete="email"
                        required
                        value={email}
                        onChange={(e) => setEmail(e.target.value)}
                        placeholder="email address"
                        className="w-full dsi-inputbox"
                      />
                    </div>
                    
                  </div>

                  <div>
                    
                    <div>  
                      <input
                        id="password" name="password" type="password" autoComplete="current-password"
                        required
                        value={password}
                        onChange={(e) => setPassword(e.target.value)}
                        placeholder="password"
                        className="w-full dsi-inputbox"
                      />
                    </div>

                  </div>

                  <div>

                    {error && <div className="text-sm text-dsi-decline">{error}</div>}
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
              </div>
           
           )}
                  
          </>
        )}
      </div>
    </>
  )
}

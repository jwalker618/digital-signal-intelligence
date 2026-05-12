"use client";

import { FormEvent, useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";

import { 
  Loader2, Lightbulb, LightbulbOff, PanelBottomClose, PanelBottomOpen,
} from "lucide-react";

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
      <div className="generate-app-page">

        <div>
          <img
              alt="Generate Logo"
              src={isDark ? 
                "/Standard_Generate_Logo_and_Product.svg" : "/BlackWhite_Generate_Logo_and_Product.svg"
                }
              className="generate-login-icon absolute top-generate-gap left-generate-gap " 
            />
          <SidebarIconBtn
              icon={isDark ? LightbulbOff : Lightbulb}
              onClick={toggleDark}
              className="generate-app-icon absolute top-generate-gap right-generate-gap "
            />

        </div>

        <div className="absolute top-1/3 left-1/3 w-1/4">
    
            <h2 className="text-2xl font-bold mb-4">
              Sign in to your account
            </h2>

            <button
              onClick={() => onToggleSSO(prev => !prev)}
              className="flex gap-2 mb-2 items-center text-sm">
              {isSSO ? (
                <PanelBottomOpen className="generate-app-icon"/> 
              ) : (
                <PanelBottomClose className="generate-app-icon"/>
              )}{isSSO ? "Tenant (for SSO)" : "Email Address / Password"}
            </button>

            {mfaChallengePending ? ( <MFAVerify/> ) 
            : (
              <>             
                {isSSO ? (               
                  <div>                     
                    
                    <input
                      value={tenantSlug}
                      onChange={(e) => setTenantSlug(e.target.value)}
                      placeholder="e.g. your company domain"
                      className="generate-dark-inputbox w-full mb-2"
                    />
                    <input
                      value={password}
                      className="generate-dark-inputbox w-full mb-2 opacity-5 cursor-not-allowed"
                      disabled 
                    />

                    <button
                        type="button"
                        onClick={onSSO}
                        disabled={submitting} 
                        className="generate-dark-actionbutton w-full mb-2"
                        > Continue with SSO
                    </button>

                  </div>
                 
                ) : (
                  
                  <div> 
                    <input
                      id="email" name="email" type="email" autoComplete="email"
                      required
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      placeholder="email address"
                      className="generate-dark-inputbox w-full mb-2"
                    />      
                    <input
                      id="password" name="password" type="password" autoComplete="current-password"
                      required
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      placeholder="password"
                      className="generate-dark-inputbox w-full mb-2"
                    />
                  
                    <form onSubmit={onSubmit}>                            
                      <div>
                        
                        {error && <div className="generate-error-message mb-2">{error}</div>}
                        
                        <button
                          id="submit" name="submit" type="submit" 
                          disabled={submitting}                      
                          className="generate-dark-actionbutton w-full mb-2 flex gap-4"
                        >
                          Sign in
                          {submitting && <Loader2 className="generate-dark-icon animate-spin" />}
                        </button>

                        <div>
                          <a href="/login/reset-password" 
                            className="
                              text-sm font-bold
                              text-generate-text-outline 
                              hover:text-generate-text-input">
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

      </div>
    </>
  )
}



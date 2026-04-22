// A-3d: Password reset page.
//
// Two modes:
//   - No ?token=... in the URL: show the email-request form.
//   - ?token=... present: show the set-new-password form.

"use client";

import { FormEvent, useState } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import Link from "next/link";
import { Loader2 } from "lucide-react";

import {
  passwordResetConfirm,
  passwordResetRequest,
} from "@/lib/authApi";

function passwordStrength(pw: string): { score: number; label: string } {
  let score = 0;
  if (pw.length >= 12) score += 1;
  if (/[A-Z]/.test(pw)) score += 1;
  if (/[a-z]/.test(pw)) score += 1;
  if (/\d/.test(pw)) score += 1;
  if (/[^\w\s]/.test(pw)) score += 1;
  const labels = ["Very weak", "Weak", "Fair", "Good", "Strong", "Excellent"];
  return { score, label: labels[score] };
}

export default function ResetPasswordPage() {
  const params = useSearchParams();
  const router = useRouter();
  const token = params.get("token");

  if (token) return <SetNewPasswordForm token={token} onDone={() => router.replace("/login")} />;
  return <RequestResetForm />;
}

function RequestResetForm() {
  const [email, setEmail] = useState("");
  const [submitted, setSubmitted] = useState(false);
  const [busy, setBusy] = useState(false);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setBusy(true);
    try {
      await passwordResetRequest(email.trim().toLowerCase());
    } finally {
      setBusy(false);
      setSubmitted(true);
    }
  }

  return (
    
    <main className="flex min-h-full flex-col justify-center bg-dsi-contrast-background">

      <div className="sm:mx-auto sm:w-full sm:max-w-sm">
        
        <h1 className="text-left text-2xl font-bold text-dsi-background mb-5">
          Reset password
        </h1>
        {submitted ? (
          <p className="text-sm">
            If an account exists for <strong>{email}</strong>, a reset link
            has been sent. Check your inbox.
          </p>
        ) : (
          
          <form onSubmit={onSubmit} className="space-y-3">
            
            <label className="flex flex-col gap-1">
              
              <span className="
                block mb-1
                text-xs text-dsi-background"
                >Email
              </span>
              
              <input
                id="email" name="email" type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                
                className="w-full dsi-inputbox"
              />

            </label>
            
            <button
              type="submit"
              disabled={busy}
              className="w-full flex flex-col dsi-actionbutton"
            >
              {busy && <Loader2 className="icon animate-spin" />}
              Send Reset Link
            </button>
          </form>
        )}
        <div className="mt-3">
          <Link 
            href="/login" 
            className="
              font-bold
              text-dsi-outline hover:text-dsi-selected">
            Back To Sign In
          </Link>
        </div>
      </div>
    </main>
  );
}

function SetNewPasswordForm({
  token,
  onDone,
}: {
  token: string;
  onDone: () => void;
}) {
  const [pw, setPw] = useState("");
  const [confirmPw, setConfirmPw] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const strength = passwordStrength(pw);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    if (pw !== confirmPw) {
      setError("Passwords do not match");
      return;
    }
    if (pw.length < 12) {
      setError("Password must be at least 12 characters");
      return;
    }
    setBusy(true);
    setError(null);
    try {
      await passwordResetConfirm(token, pw);
      onDone();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Reset failed");
    } finally {
      setBusy(false);
    }
  }

  return (
    
    <main className="flex min-h-full flex-col justify-center bg-dsi-contrast-background">
      
      <div className="sm:mx-auto sm:w-full sm:max-w-sm">

        <h1 className="text-left text-2xl font-bold text-dsi-background mb-5">
          Choose a new password
        </h1>
        
        <form onSubmit={onSubmit} className="space-y-3">
          
          <label className="flex flex-col gap-1">
            <span className="
              block mb-1
              text-xs text-dsi-background"
              >New password
            </span>
            
            <input
              id="password" name="password" type="password"
              required
              value={pw}
              onChange={(e) => setPw(e.target.value)}
              
              className="w-full dsi-inputbox"
            />
          </label>

          <div className="flex items-center gap-2 text-xs opacity-80">
            <div className="flex-1 h-1 bg-dsi-outline/30 rounded overflow-hidden">
              <div
                className="h-full bg-dsi-selected transition-all"
                style={{ width: `${(strength.score / 5) * 100}%` }}
              />
            </div>
            <span>{strength.label}</span>
          </div>
          
          <label className="flex flex-col gap-1">
            <span className="
              block mb-1
              text-xs text-dsi-background"
            >Confirm
            </span>
            
            <input
              id="password" name="password" type="password"
              required
              value={confirmPw}
              onChange={(e) => setConfirmPw(e.target.value)}
              
              className="w-full dsi-inputbox"
            />
          </label>

          {error && <div className="text-sm text-dsi-decline">{error}</div>}
          
          <button
            type="submit"
            disabled={busy}
            
            className="w-full flex flex-col dsi-actionbutton"
          >
            {busy && <Loader2 className="icon animate-spin" />}
            Set new password
          </button>

        </form>
      </div>
    </main>
  );
}

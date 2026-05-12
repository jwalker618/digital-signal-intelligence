"use client";

import { FormEvent, useState } from "react";
import { useSearchParams, useRouter } from "next/navigation";
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

  if (token) 
    return <SetNewPasswordForm 
      token={token} 
      onDone={() => router.replace("/login")} 
    />;
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
    
    <main className="generate-app-page">

      <div className="absolute top-1/3 left-1/3 w-1/4">

         <h1 className="text-2xl font-bold mb-4">Reset password</h1>
        
        {submitted ? 
        (
          <p className="text-sm mb-2">
            If an account exists for <strong className="hover:text-generate-selected">{email}</strong>, a reset link
            has been sent. Check your inbox.
          </p>
        ) : 
        (
          
          <form onSubmit={onSubmit}>           
            <label>
              <input
                id="email" name="email" type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="email address"
                className="generate-inputbox w-full mb-2"
              />
            </label>
            
            <button
              type="submit"
              disabled={busy}
              className="generate-actionbutton w-full mb-2 flex gap-4"
            >
              Send Reset Link
              {busy && <Loader2 className="generate-app-icon animate-spin" />}
            </button>
          </form>
        )}
        
        <div>
          <a href="/login" 
            className="
              text-sm font-bold
              text-generate-outline 
              hover:text-generate-selected">
            Back To Sign In
          </a>
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
    <main className="generate-app-page">
      
      <div className="absolute top-1/3 left-1/3 w-1/4">

        <h1 className="text-2xl font-bold mb-4">Choose a new password</h1>
        
        <form onSubmit={onSubmit}>
          <div>
            <input
              id="password" name="password" type="password"
              required
              value={pw}
              onChange={(e) => setPw(e.target.value)}
              placeholder="new password"
              className="generate-inputbox w-full mb-4"
            />
          
            <div className="flex items-center gap-2 text-xs opacity-80 mb-4">
              
              <div className="flex-1 h-1 bg-generate-sidebar-text-selected rounded overflow-hidden">
                <div
                  className="h-full bg-generate-main-outline transition-all"
                  style={{ width: `${(strength.score / 5) * 100}%` }}
                />
              </div>

              <span className="font-bold">{strength.label}</span>
            </div>

            <input
              id="password" name="password" type="password"
              required
              value={confirmPw}
              onChange={(e) => setConfirmPw(e.target.value)}
              placeholder="confirm new password"
              className="generate-inputbox w-full mb-2"
            />

          </div>

          {error && <div className="text-sm text-generate-decline">{error}</div>}
          
          <button
            type="submit"
            disabled={busy}
            className="generate-actionbutton w-full mb-2 flex gap-4"
          >
            Set new password
            {busy && <Loader2 className="generate-app-icon animate-spin" />}
          </button>

        </form>
      </div>
    </main>
  );
}



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
    <main className="min-h-screen flex items-center justify-center bg-dsi-background">
      <div className="w-full max-w-md border-3 border-dsi-outline rounded-lg p-8">
        <h1 className="font-inter text-2xl tracking-wide mb-4">
          Reset password
        </h1>
        {submitted ? (
          <p className="text-sm opacity-80">
            If an account exists for <strong>{email}</strong>, a reset link
            has been sent. Check your inbox.
          </p>
        ) : (
          <form onSubmit={onSubmit} className="flex flex-col gap-4">
            <label className="flex flex-col gap-1">
              <span className="text-sm opacity-70">Email</span>
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="border-2 border-dsi-outline bg-dsi-background px-3 py-2 rounded"
              />
            </label>
            <button
              type="submit"
              disabled={busy}
              className="flex items-center justify-center gap-2 bg-dsi-contrast-background text-dsi-background py-2 rounded font-semibold disabled:opacity-50"
            >
              {busy && <Loader2 className="icon animate-spin" />}
              Send reset link
            </button>
          </form>
        )}
        <div className="mt-6">
          <Link href="/login" className="text-sm text-dsi-selected hover:underline">
            Back to sign in
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
    <main className="min-h-screen flex items-center justify-center bg-dsi-background">
      <div className="w-full max-w-md border-3 border-dsi-outline rounded-lg p-8">
        <h1 className="font-inter text-2xl tracking-wide mb-4">
          Choose a new password
        </h1>
        <form onSubmit={onSubmit} className="flex flex-col gap-4">
          <label className="flex flex-col gap-1">
            <span className="text-sm opacity-70">New password</span>
            <input
              type="password"
              required
              value={pw}
              onChange={(e) => setPw(e.target.value)}
              className="border-2 border-dsi-outline bg-dsi-background px-3 py-2 rounded"
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
            <span className="text-sm opacity-70">Confirm</span>
            <input
              type="password"
              required
              value={confirmPw}
              onChange={(e) => setConfirmPw(e.target.value)}
              className="border-2 border-dsi-outline bg-dsi-background px-3 py-2 rounded"
            />
          </label>
          {error && <div className="text-sm text-dsi-negative">{error}</div>}
          <button
            type="submit"
            disabled={busy}
            className="flex items-center justify-center gap-2 bg-dsi-contrast-background text-dsi-background py-2 rounded font-semibold disabled:opacity-50"
          >
            {busy && <Loader2 className="icon animate-spin" />}
            Set new password
          </button>
        </form>
      </div>
    </main>
  );
}

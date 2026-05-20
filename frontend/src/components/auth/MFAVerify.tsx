// A-3c: MFA verification form (6-digit TOTP code).
//
// Used inline on the login page when the server returns
// mfa_required=true. On success, the auth store clears the challenge
// and the SessionGuard proceeds to render the app.

"use client";

import { useState, useRef, useEffect, FormEvent } from "react";
import { Loader2, ShieldCheck } from "lucide-react";

import { useAuthStore } from "@/store/authStore";

export function MFAVerify() {
  const verifyMFA = useAuthStore((s) => s.verifyMFA);
  const [code, setCode] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    if (code.length !== 6 || !/^\d{6}$/.test(code)) {
      setError("Code must be 6 digits");
      return;
    }
    setSubmitting(true);
    setError(null);
    try {
      await verifyMFA(code);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Verification failed");
      setCode("");
      inputRef.current?.focus();
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <form onSubmit={onSubmit} className="flex flex-col gap-4">
      <div className="flex items-center gap-3 text-generate-text-input">
        <ShieldCheck className="icon" />
        <span className="font-semibold tracking-wider">
          Two-Factor Authentication
        </span>
      </div>
      <label className="flex flex-col gap-1">
        <span className="text-sm opacity-70">Authenticator code</span>
        <input
          ref={inputRef}
          value={code}
          onChange={(e) => setCode(e.target.value.replace(/\D/g, "").slice(0, 6))}
          inputMode="numeric"
          autoComplete="one-time-code"
          maxLength={6}
          className="border-2 border-generate-text-outline bg-generate-light-background px-3 py-2 font-mono text-2xl tracking-[0.5em] text-center rounded"
          placeholder="000000"
          aria-label="TOTP code"
        />
      </label>
      {error && <div className="text-sm text-generate-text-bad">{error}</div>}
      <button
        type="submit"
        disabled={submitting || code.length !== 6}
        className="flex items-center justify-center gap-2 bg-generate-text-input text-generate-light-background py-2 rounded font-semibold disabled:opacity-50"
      >
        {submitting && <Loader2 className="icon animate-spin" />}
        Verify
      </button>
    </form>
  );
}

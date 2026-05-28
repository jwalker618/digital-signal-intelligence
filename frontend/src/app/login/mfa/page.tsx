"use client";

import { useRouter } from "next/navigation";
import Link from "next/link";
import { FormEvent, useEffect, useState } from "react";
import { ArrowLeft } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Eyebrow, Body, Micro } from "@/components/ui/typography";
import { useAuthStore } from "@/store/authStore";

export default function MFAPage() {
  const router = useRouter();
  const verifyMFA = useAuthStore((s) => s.verifyMFA);
  const challengePending = useAuthStore((s) => s.mfaChallengePending);

  const [code, setCode] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // If the user lands here without a pending challenge (e.g. refresh), bounce.
  useEffect(() => {
    if (!challengePending) router.replace("/login");
  }, [challengePending, router]);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    if (code.length < 6 || submitting) return;
    setError(null);
    setSubmitting(true);
    try {
      await verifyMFA(code);
      router.replace("/client");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Verification failed.");
      setSubmitting(false);
    }
  }

  return (
    <div className="space-y-7">
      <header>
        <Eyebrow>Two-factor</Eyebrow>
        <h1 className="mt-2 font-display text-[28px] font-semibold leading-none text-ink">
          Enter your 6-digit code
        </h1>
        <Body className="mt-2">
          Open your authenticator app and enter the current code for DSI.
        </Body>
      </header>

      <form className="space-y-5" onSubmit={onSubmit}>
        <input
          inputMode="numeric"
          autoComplete="one-time-code"
          maxLength={6}
          pattern="\d{6}"
          required
          value={code}
          onChange={(e) => setCode(e.target.value.replace(/\D/g, ""))}
          className="block h-14 w-full rounded-btn border border-rule-strong bg-surface px-3 text-center text-[28px] font-semibold tracking-[0.6em] text-ink tabular-nums focus:border-info focus:outline-none focus:ring-2 focus:ring-info/30"
          aria-label="Authentication code"
        />

        {error && (
          <div
            role="alert"
            className="rounded-btn border border-neg bg-neg-soft px-3 py-2 text-[13px] text-neg"
          >
            {error}
          </div>
        )}

        <Button
          type="submit"
          size="lg"
          className="w-full"
          disabled={submitting || code.length < 6}
        >
          {submitting ? "Verifying…" : "Verify"}
        </Button>
      </form>

      <Micro className="block text-center">
        Lost access? Use a backup code or contact your administrator.
      </Micro>

      <Link
        href="/login"
        className="inline-flex items-center gap-1.5 text-[13px] font-medium text-info hover:underline"
      >
        <ArrowLeft size={14} /> Use a different account
      </Link>
    </div>
  );
}

"use client";

import { useRouter } from "next/navigation";
import Link from "next/link";
import {
  ChangeEvent,
  ClipboardEvent,
  FormEvent,
  KeyboardEvent,
  useEffect,
  useRef,
  useState,
} from "react";
import { Button } from "@/components/ui/button";
import { Eyebrow, Body } from "@/components/ui/typography";
import { cn } from "@/lib/utils";
import { useAuthStore } from "@/store/authStore";

const SLOTS = 6;

export default function MFAPage() {
  const router = useRouter();
  const verifyMFA = useAuthStore((s) => s.verifyMFA);
  const challengePending = useAuthStore((s) => s.mfaChallengePending);

  const [digits, setDigits] = useState<string[]>(() =>
    Array.from({ length: SLOTS }, () => ""),
  );
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const inputs = useRef<Array<HTMLInputElement | null>>([]);

  useEffect(() => {
    if (!challengePending) router.replace("/login");
  }, [challengePending, router]);

  const code = digits.join("");

  function focusSlot(i: number) {
    const target = inputs.current[i];
    if (target) target.focus();
  }

  function setSlot(i: number, value: string) {
    const clean = value.replace(/\D/g, "").slice(0, 1);
    setDigits((prev) => {
      const next = [...prev];
      next[i] = clean;
      return next;
    });
    if (clean && i < SLOTS - 1) focusSlot(i + 1);
  }

  function handleKey(i: number, e: KeyboardEvent<HTMLInputElement>) {
    if (e.key === "Backspace" && !digits[i] && i > 0) {
      e.preventDefault();
      focusSlot(i - 1);
      setDigits((prev) => {
        const next = [...prev];
        next[i - 1] = "";
        return next;
      });
    } else if (e.key === "ArrowLeft" && i > 0) {
      focusSlot(i - 1);
    } else if (e.key === "ArrowRight" && i < SLOTS - 1) {
      focusSlot(i + 1);
    }
  }

  function handlePaste(e: ClipboardEvent<HTMLInputElement>) {
    const text = e.clipboardData.getData("text").replace(/\D/g, "").slice(0, SLOTS);
    if (!text) return;
    e.preventDefault();
    const next = Array.from({ length: SLOTS }, (_, i) => text[i] ?? "");
    setDigits(next);
    const last = Math.min(text.length, SLOTS) - 1;
    if (last >= 0) focusSlot(last);
  }

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    if (code.length < SLOTS || submitting) return;
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
    <div>
      <header className="mb-7">
        <Eyebrow className="text-info">Two-factor authentication</Eyebrow>
        <h1 className="mt-1.5 font-display text-[28px] font-semibold leading-[1.2] text-ink">
          Enter your code
        </h1>
        <Body className="mt-2 leading-[1.55]">
          Open your authenticator app and enter the 6-digit code for DSI.
        </Body>
      </header>

      <form onSubmit={onSubmit}>
        <div className="mb-[18px] flex justify-between gap-2">
          {digits.map((d, i) => (
            <input
              key={i}
              ref={(el) => {
                inputs.current[i] = el;
              }}
              value={d}
              onChange={(e: ChangeEvent<HTMLInputElement>) =>
                setSlot(i, e.target.value)
              }
              onKeyDown={(e) => handleKey(i, e)}
              onPaste={handlePaste}
              inputMode="numeric"
              autoComplete={i === 0 ? "one-time-code" : "off"}
              maxLength={1}
              aria-label={`Digit ${i + 1}`}
              className={cn(
                "h-14 flex-1 rounded-[10px] border bg-surface text-center text-[22px] font-bold tabular-nums text-ink focus:outline-none",
                d ? "border-info" : "border-rule-strong",
                "focus:border-info focus:ring-2 focus:ring-info/30",
              )}
            />
          ))}
        </div>

        {error && (
          <div
            role="alert"
            className="mb-4 rounded-btn border border-neg bg-neg-soft px-3 py-2 text-[13px] text-neg"
          >
            {error}
          </div>
        )}

        <Button
          type="submit"
          size="lg"
          className="w-full"
          disabled={submitting || code.length < SLOTS}
        >
          {submitting ? "Verifying…" : "Verify"}
        </Button>
      </form>

      <div className="mt-[22px] flex items-center justify-between border-t border-rule pt-[18px]">
        <Link
          href="/login"
          className="text-[13px] font-medium text-ink-soft hover:text-ink"
        >
          ← Back to sign in
        </Link>
        <span className="text-[13px] font-medium text-ink-mute">
          Use a recovery code
        </span>
      </div>
    </div>
  );
}

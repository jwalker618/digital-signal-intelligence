"use client";

import { useRouter } from "next/navigation";
import Link from "next/link";
import { FormEvent, useState } from "react";
import { Eye, EyeOff } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Eyebrow, Body, Caption } from "@/components/ui/typography";
import { cn } from "@/lib/utils";
import { useAuthStore } from "@/store/authStore";

export default function LoginPage() {
  const router = useRouter();
  const login = useAuthStore((s) => s.login);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    if (submitting) return;
    setError(null);
    setSubmitting(true);
    try {
      await login(email, password);
      const pending = useAuthStore.getState().mfaChallengePending;
      router.replace(pending ? "/login/mfa" : "/client");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Sign-in failed.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div>
      <header className="mb-7">
        <Eyebrow className="text-info">Welcome</Eyebrow>
        <h1 className="mt-1.5 font-display text-[28px] font-semibold leading-[1.2] text-ink">
          Sign in to your account
        </h1>
        <Body className="mt-2 leading-[1.55]">
          Use your work email + password, or switch to SSO if your
          organisation has it set up.
        </Body>
      </header>

      <div className="mb-[22px] grid grid-cols-2 gap-1 rounded-[10px] bg-surface-sunken p-1">
        <div className="flex items-center justify-center rounded-lg bg-surface px-3 py-2 text-[13px] font-semibold text-ink shadow-[0_1px_2px_rgba(0,0,0,0.08)]">
          Email + password
        </div>
        <Link
          href="/login/sso"
          className="flex items-center justify-center rounded-lg px-3 py-2 text-[13px] font-semibold text-ink-soft hover:text-ink"
        >
          SSO
        </Link>
      </div>

      <form className="space-y-3.5" onSubmit={onSubmit}>
        <Field id="email" label="Work email">
          <input
            id="email"
            type="email"
            autoComplete="email"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className={authInputClass}
            placeholder="you@company.com"
          />
        </Field>

        <Field id="password" label="Password">
          <div className="relative">
            <input
              id="password"
              type={showPassword ? "text" : "password"}
              autoComplete="current-password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className={cn(
                authInputClass,
                "pr-10",
                !showPassword && password ? "font-mono tracking-[0.2em]" : null,
              )}
            />
            <button
              type="button"
              onClick={() => setShowPassword((v) => !v)}
              className="absolute inset-y-0 right-2 my-auto flex h-8 w-8 items-center justify-center rounded-md text-ink-soft hover:bg-surface-sunken"
              aria-label={showPassword ? "Hide password" : "Show password"}
            >
              {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
            </button>
          </div>
        </Field>

        <div className="flex justify-end pb-1">
          <Link
            href="/login/reset-password"
            className="text-[13px] font-medium text-ink-soft hover:text-ink"
          >
            Forgot password?
          </Link>
        </div>

        {error && (
          <div
            role="alert"
            className="rounded-btn border border-neg bg-neg-soft px-3 py-2 text-[13px] text-neg"
          >
            {error}
          </div>
        )}

        <Button type="submit" size="lg" className="w-full" disabled={submitting}>
          {submitting ? "Signing in…" : "Sign in"}
        </Button>
      </form>

      <div className="mt-6 flex items-center justify-between border-t border-rule pt-[18px]">
        <Caption>First time here?</Caption>
        <Link
          href="/login/sso"
          className="text-[13px] font-medium text-ink-soft hover:text-ink"
        >
          Get an invite from your broker →
        </Link>
      </div>
    </div>
  );
}

function Field({
  id,
  label,
  children,
}: {
  id: string;
  label: string;
  children: React.ReactNode;
}) {
  return (
    <label htmlFor={id} className="block">
      <span className="mb-1.5 block text-[12px] font-medium text-ink-soft">
        {label}
      </span>
      {children}
    </label>
  );
}

const authInputClass =
  "block h-11 w-full rounded-btn border border-rule-strong bg-surface px-3.5 text-[14px] text-ink placeholder:text-ink-mute focus:border-info focus:outline-none focus:ring-2 focus:ring-info/30";

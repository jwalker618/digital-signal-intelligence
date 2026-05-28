"use client";

import { useRouter } from "next/navigation";
import Link from "next/link";
import { FormEvent, useState } from "react";
import { Eye, EyeOff, KeyRound } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Eyebrow, Body, Micro } from "@/components/ui/typography";
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
      // mfaChallengePending is set inside the store on response; check after.
      const pending = useAuthStore.getState().mfaChallengePending;
      router.replace(pending ? "/login/mfa" : "/client");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Sign-in failed.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="space-y-7">
      <header>
        <Eyebrow>Sign in</Eyebrow>
        <h1 className="mt-2 font-display text-[28px] font-semibold leading-none text-ink">
          Welcome back
        </h1>
        <Body className="mt-2">
          Use your work email and password. SSO and MFA are supported.
        </Body>
      </header>

      <form className="space-y-5" onSubmit={onSubmit}>
        <Field id="email" label="Email">
          <input
            id="email"
            type="email"
            autoComplete="email"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className={inputClass}
          />
        </Field>
        <Field
          id="password"
          label="Password"
          aside={
            <Link
              href="/login/reset-password"
              className="text-[12px] font-medium text-info hover:underline"
            >
              Forgot password?
            </Link>
          }
        >
          <div className="relative">
            <input
              id="password"
              type={showPassword ? "text" : "password"}
              autoComplete="current-password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className={cn(inputClass, "pr-10")}
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

      <div className="flex items-center gap-3 text-[12px] text-ink-mute">
        <span className="h-px flex-1 bg-rule" />
        <span>or</span>
        <span className="h-px flex-1 bg-rule" />
      </div>

      <Link
        href="/login/sso"
        className="flex h-12 items-center justify-center gap-2 rounded-btn border border-rule-strong bg-surface text-[13px] font-semibold text-ink hover:bg-surface-sunken"
      >
        <KeyRound size={15} />
        Continue with SSO
      </Link>

      <Micro className="block text-center">
        Need access? Ask your broker administrator to add you.
      </Micro>
    </div>
  );
}

function Field({
  id,
  label,
  aside,
  children,
}: {
  id: string;
  label: string;
  aside?: React.ReactNode;
  children: React.ReactNode;
}) {
  return (
    <div>
      <div className="mb-1.5 flex items-baseline justify-between">
        <label htmlFor={id} className="text-[12.5px] font-medium text-ink-soft">
          {label}
        </label>
        {aside}
      </div>
      {children}
    </div>
  );
}

const inputClass =
  "block h-11 w-full rounded-btn border border-rule-strong bg-surface px-3 text-[14px] text-ink placeholder:text-ink-mute focus:border-info focus:outline-none focus:ring-2 focus:ring-info/30";

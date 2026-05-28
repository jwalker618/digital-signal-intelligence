"use client";

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { FormEvent, useMemo, useState } from "react";
import { ArrowLeft, Check } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Eyebrow, Body, Micro } from "@/components/ui/typography";
import { passwordResetConfirm } from "@/lib/authApi";
import { cn } from "@/lib/utils";

interface PolicyCheck {
  label: string;
  ok: boolean;
}

function checkPolicy(pw: string): PolicyCheck[] {
  return [
    { label: "At least 12 characters", ok: pw.length >= 12 },
    { label: "Contains a number", ok: /\d/.test(pw) },
    { label: "Contains upper & lower case", ok: /[a-z]/.test(pw) && /[A-Z]/.test(pw) },
    { label: "Contains a symbol", ok: /[^A-Za-z0-9]/.test(pw) },
  ];
}

export default function ResetSetPage() {
  const router = useRouter();
  const params = useSearchParams();
  const token = params.get("token") ?? "";
  const [pw, setPw] = useState("");
  const [pw2, setPw2] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const checks = useMemo(() => checkPolicy(pw), [pw]);
  const allOk = checks.every((c) => c.ok) && pw === pw2 && pw.length > 0;

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    if (!allOk || submitting) return;
    setError(null);
    setSubmitting(true);
    try {
      await passwordResetConfirm(token, pw);
      router.replace("/login");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Couldn't update password.");
      setSubmitting(false);
    }
  }

  return (
    <div className="space-y-7">
      <header>
        <Eyebrow>Reset password</Eyebrow>
        <h1 className="mt-2 font-display text-[28px] font-semibold leading-none text-ink">
          Choose a new password
        </h1>
        <Body className="mt-2">
          Pick something you haven't used before. We'll sign you in after you
          set it.
        </Body>
      </header>

      <form className="space-y-5" onSubmit={onSubmit}>
        <PasswordField id="pw" label="New password" value={pw} onChange={setPw} />
        <PasswordField id="pw2" label="Confirm password" value={pw2} onChange={setPw2} />

        <ul className="space-y-1.5">
          {checks.map((c) => (
            <li
              key={c.label}
              className={cn(
                "flex items-center gap-2 text-[12.5px]",
                c.ok ? "text-pos" : "text-ink-soft",
              )}
            >
              <Check
                size={14}
                className={c.ok ? "opacity-100" : "opacity-30"}
              />
              {c.label}
            </li>
          ))}
          {pw.length > 0 && (
            <li
              className={cn(
                "flex items-center gap-2 text-[12.5px]",
                pw === pw2 ? "text-pos" : "text-ink-soft",
              )}
            >
              <Check size={14} className={pw === pw2 ? "opacity-100" : "opacity-30"} />
              Passwords match
            </li>
          )}
        </ul>

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
          disabled={submitting || !allOk}
        >
          {submitting ? "Updating…" : "Update password"}
        </Button>
      </form>

      <Micro className="block text-center">
        Reset link will expire when this page is updated.
      </Micro>

      <Link
        href="/login"
        className="inline-flex items-center gap-1.5 text-[13px] font-medium text-info hover:underline"
      >
        <ArrowLeft size={14} /> Back to sign in
      </Link>
    </div>
  );
}

function PasswordField({
  id,
  label,
  value,
  onChange,
}: {
  id: string;
  label: string;
  value: string;
  onChange: (v: string) => void;
}) {
  return (
    <div>
      <label htmlFor={id} className="mb-1.5 block text-[12.5px] font-medium text-ink-soft">
        {label}
      </label>
      <input
        id={id}
        type="password"
        autoComplete="new-password"
        required
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="block h-11 w-full rounded-btn border border-rule-strong bg-surface px-3 text-[14px] text-ink placeholder:text-ink-mute focus:border-info focus:outline-none focus:ring-2 focus:ring-info/30"
      />
    </div>
  );
}

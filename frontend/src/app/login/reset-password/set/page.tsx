"use client";

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { FormEvent, useMemo, useState } from "react";
import { Button } from "@/components/ui/button";
import { Eyebrow, Body } from "@/components/ui/typography";
import { passwordResetConfirm } from "@/lib/authApi";
import { cn } from "@/lib/utils";

const authInputClass =
  "block h-11 w-full rounded-btn border border-rule-strong bg-surface px-3.5 text-[14px] text-ink placeholder:text-ink-mute focus:border-info focus:outline-none focus:ring-2 focus:ring-info/30";

interface Strength {
  score: number;
  label: string;
  tone: "neg" | "warn" | "pos";
}

function scorePassword(pw: string): Strength {
  let score = 0;
  if (pw.length >= 8) score += 1;
  if (pw.length >= 12) score += 1;
  if (/\d/.test(pw)) score += 1;
  if (/[a-z]/.test(pw) && /[A-Z]/.test(pw)) score += 1;
  if (/[^A-Za-z0-9]/.test(pw)) score += 1;
  let label = "Too short";
  let tone: "neg" | "warn" | "pos" = "neg";
  if (score >= 5) {
    label = "Strong";
    tone = "pos";
  } else if (score >= 4) {
    label = "Good";
    tone = "pos";
  } else if (score >= 2) {
    label = "Fair";
    tone = "warn";
  } else if (pw.length > 0) {
    label = "Weak";
    tone = "neg";
  }
  return { score, label, tone };
}

function meetsPolicy(pw: string): boolean {
  return (
    pw.length >= 12 &&
    /\d/.test(pw) &&
    /[a-z]/.test(pw) &&
    /[A-Z]/.test(pw) &&
    /[^A-Za-z0-9]/.test(pw)
  );
}

export default function ResetSetPage() {
  const router = useRouter();
  const params = useSearchParams();
  const token = params.get("token") ?? "";
  const [pw, setPw] = useState("");
  const [pw2, setPw2] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const strength = useMemo(() => scorePassword(pw), [pw]);
  const valid = meetsPolicy(pw) && pw === pw2 && pw.length > 0;

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    if (!valid || submitting) return;
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
    <div>
      <header className="mb-7">
        <Eyebrow className="text-info">Reset password</Eyebrow>
        <h1 className="mt-1.5 font-display text-[28px] font-semibold leading-[1.2] text-ink">
          Choose a new password
        </h1>
        <Body className="mt-2 leading-[1.55]">
          Pick something at least 12 characters with a mix of upper/lower
          case, a digit, and a symbol.
        </Body>
      </header>

      <form className="space-y-3.5" onSubmit={onSubmit}>
        <PasswordField
          id="pw"
          label="New password"
          value={pw}
          onChange={setPw}
        />

        <StrengthMeter strength={strength} hasInput={pw.length > 0} />

        <PasswordField
          id="pw2"
          label="Confirm password"
          value={pw2}
          onChange={setPw2}
        />

        {pw.length > 0 && pw2.length > 0 && pw !== pw2 && (
          <p className="text-[12px] font-medium text-neg">
            Passwords don&apos;t match.
          </p>
        )}

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
          disabled={submitting || !valid}
        >
          {submitting ? "Updating…" : "Set new password"}
        </Button>
      </form>

      <div className="mt-[22px] border-t border-rule pt-[18px]">
        <Link
          href="/login"
          className="text-[13px] font-medium text-ink-soft hover:text-ink"
        >
          ← Back to sign in
        </Link>
      </div>
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
    <label htmlFor={id} className="block">
      <span className="mb-1.5 block text-[12px] font-medium text-ink-soft">
        {label}
      </span>
      <input
        id={id}
        type="password"
        autoComplete="new-password"
        required
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className={cn(
          authInputClass,
          value ? "font-mono tracking-[0.2em]" : null,
        )}
      />
    </label>
  );
}

function StrengthMeter({
  strength,
  hasInput,
}: {
  strength: Strength;
  hasInput: boolean;
}) {
  const barColor =
    strength.tone === "neg"
      ? "bg-neg"
      : strength.tone === "warn"
        ? "bg-warn"
        : "bg-pos";
  const labelColor =
    strength.tone === "neg"
      ? "text-neg"
      : strength.tone === "warn"
        ? "text-warn"
        : "text-pos";
  return (
    <div className="flex items-center gap-2.5 -mt-1">
      <div className="flex flex-1 gap-[3px]">
        {[0, 1, 2, 3, 4].map((i) => (
          <div
            key={i}
            className={cn(
              "h-1 flex-1 rounded-sm",
              i < strength.score ? barColor : "bg-rule",
            )}
          />
        ))}
      </div>
      <span
        className={cn(
          "text-[11px] font-semibold",
          hasInput ? labelColor : "text-ink-mute",
        )}
      >
        {hasInput ? strength.label : "—"}
      </span>
    </div>
  );
}

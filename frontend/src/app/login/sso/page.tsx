"use client";

import Link from "next/link";
import { FormEvent, useState } from "react";
import { KeyRound } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Eyebrow, Body, Caption } from "@/components/ui/typography";
import { useAuthStore } from "@/store/authStore";

const authInputClass =
  "block h-11 w-full rounded-btn border border-rule-strong bg-surface px-3.5 text-[14px] text-ink placeholder:text-ink-mute focus:border-info focus:outline-none focus:ring-2 focus:ring-info/30";

export default function SSOPage() {
  const loginSSO = useAuthStore((s) => s.loginSSO);
  const [tenant, setTenant] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    if (!tenant || submitting) return;
    setError(null);
    setSubmitting(true);
    try {
      await loginSSO(tenant.trim().toLowerCase());
    } catch (err) {
      setError(err instanceof Error ? err.message : "SSO start failed.");
      setSubmitting(false);
    }
  }

  return (
    <div>
      <header className="mb-7">
        <Eyebrow className="text-info">Welcome</Eyebrow>
        <h1 className="mt-1.5 font-display text-[28px] font-semibold leading-[1.2] text-ink">
          Sign in via SSO
        </h1>
        <Body className="mt-2 leading-[1.55]">
          Enter your organisation&apos;s tenant identifier. We&apos;ll bounce
          you to your identity provider to finish signing in.
        </Body>
      </header>

      <div className="mb-[22px] grid grid-cols-2 gap-1 rounded-[10px] bg-surface-sunken p-1">
        <Link
          href="/login"
          className="flex items-center justify-center rounded-lg px-3 py-2 text-[13px] font-semibold text-ink-soft hover:text-ink"
        >
          Email + password
        </Link>
        <div className="flex items-center justify-center rounded-lg bg-surface px-3 py-2 text-[13px] font-semibold text-ink shadow-[0_1px_2px_rgba(0,0,0,0.08)]">
          SSO
        </div>
      </div>

      <form className="space-y-3.5" onSubmit={onSubmit}>
        <label htmlFor="tenant" className="block">
          <span className="mb-1.5 block text-[12px] font-medium text-ink-soft">
            Tenant identifier
          </span>
          <input
            id="tenant"
            type="text"
            required
            value={tenant}
            onChange={(e) => setTenant(e.target.value)}
            placeholder="e.g. your company domain"
            className={authInputClass}
          />
        </label>

        {error && (
          <div
            role="alert"
            className="rounded-btn border border-neg bg-neg-soft px-3 py-2 text-[13px] text-neg"
          >
            {error}
          </div>
        )}

        <Button type="submit" size="lg" className="w-full" disabled={submitting}>
          <KeyRound size={14} />
          {submitting ? "Redirecting…" : "Continue with SSO"}
        </Button>
      </form>

      <div className="mt-[22px] border-t border-rule pt-[18px]">
        <Caption className="leading-[1.5]">
          You&apos;ll be redirected to your identity provider (Okta, Azure
          AD, Google Workspace, etc.). MFA is enforced by your tenant&apos;s
          policy.
        </Caption>
      </div>
    </div>
  );
}

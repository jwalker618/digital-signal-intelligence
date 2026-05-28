"use client";

import Link from "next/link";
import { FormEvent, useState } from "react";
import { ArrowLeft } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Eyebrow, Body } from "@/components/ui/typography";
import { useAuthStore } from "@/store/authStore";

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
      // The store handles the redirect to the IdP's authorize URL.
    } catch (err) {
      setError(err instanceof Error ? err.message : "SSO start failed.");
      setSubmitting(false);
    }
  }

  return (
    <div className="space-y-7">
      <header>
        <Eyebrow>Single sign-on</Eyebrow>
        <h1 className="mt-2 font-display text-[28px] font-semibold leading-none text-ink">
          Continue with SSO
        </h1>
        <Body className="mt-2">
          Enter your organization's tenant identifier to sign in via SAML / OIDC.
        </Body>
      </header>

      <form className="space-y-5" onSubmit={onSubmit}>
        <div>
          <label
            htmlFor="tenant"
            className="mb-1.5 block text-[12.5px] font-medium text-ink-soft"
          >
            Tenant identifier
          </label>
          <input
            id="tenant"
            type="text"
            required
            value={tenant}
            onChange={(e) => setTenant(e.target.value)}
            placeholder="e.g. marsh-northeast"
            className="block h-11 w-full rounded-btn border border-rule-strong bg-surface px-3 text-[14px] text-ink placeholder:text-ink-mute focus:border-info focus:outline-none focus:ring-2 focus:ring-info/30"
          />
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
          {submitting ? "Redirecting…" : "Continue"}
        </Button>
      </form>

      <Link
        href="/login"
        className="inline-flex items-center gap-1.5 text-[13px] font-medium text-info hover:underline"
      >
        <ArrowLeft size={14} /> Back to sign in
      </Link>
    </div>
  );
}

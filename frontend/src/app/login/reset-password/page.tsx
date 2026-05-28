"use client";

import Link from "next/link";
import { FormEvent, useState } from "react";
import { ArrowLeft, MailCheck } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Eyebrow, Body } from "@/components/ui/typography";
import { passwordResetRequest } from "@/lib/authApi";

export default function ResetRequestPage() {
  const [email, setEmail] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [sent, setSent] = useState(false);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    if (!email || submitting) return;
    setSubmitting(true);
    try {
      await passwordResetRequest(email);
      // Always show success — don't leak whether the address exists.
      setSent(true);
    } finally {
      setSubmitting(false);
    }
  }

  if (sent) {
    return (
      <div className="space-y-5">
        <div className="flex h-12 w-12 items-center justify-center rounded-full bg-info-soft text-info">
          <MailCheck size={22} />
        </div>
        <h1 className="font-display text-[24px] font-semibold leading-none text-ink">
          Check your inbox
        </h1>
        <Body>
          If an account exists for <strong className="text-ink">{email}</strong>,
          you'll receive a reset link shortly. The link expires in 30 minutes.
        </Body>
        <Link
          href="/login"
          className="inline-flex items-center gap-1.5 text-[13px] font-medium text-info hover:underline"
        >
          <ArrowLeft size={14} /> Back to sign in
        </Link>
      </div>
    );
  }

  return (
    <div className="space-y-7">
      <header>
        <Eyebrow>Reset password</Eyebrow>
        <h1 className="mt-2 font-display text-[28px] font-semibold leading-none text-ink">
          We'll email a reset link
        </h1>
        <Body className="mt-2">
          Enter the email you use to sign in. We won't confirm whether the
          address is registered.
        </Body>
      </header>

      <form className="space-y-5" onSubmit={onSubmit}>
        <div>
          <label
            htmlFor="email"
            className="mb-1.5 block text-[12.5px] font-medium text-ink-soft"
          >
            Email
          </label>
          <input
            id="email"
            type="email"
            autoComplete="email"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="block h-11 w-full rounded-btn border border-rule-strong bg-surface px-3 text-[14px] text-ink placeholder:text-ink-mute focus:border-info focus:outline-none focus:ring-2 focus:ring-info/30"
          />
        </div>

        <Button type="submit" size="lg" className="w-full" disabled={submitting}>
          {submitting ? "Sending…" : "Email me a reset link"}
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

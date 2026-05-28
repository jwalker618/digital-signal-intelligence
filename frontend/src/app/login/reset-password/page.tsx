"use client";

import Link from "next/link";
import { FormEvent, useState } from "react";
import { Mail, MailCheck } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Eyebrow, Body } from "@/components/ui/typography";
import { passwordResetRequest } from "@/lib/authApi";

const authInputClass =
  "block h-11 w-full rounded-btn border border-rule-strong bg-surface px-3.5 text-[14px] text-ink placeholder:text-ink-mute focus:border-info focus:outline-none focus:ring-2 focus:ring-info/30";

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
      setSent(true);
    } finally {
      setSubmitting(false);
    }
  }

  if (sent) {
    return (
      <div>
        <header className="mb-7">
          <Eyebrow className="text-info">Reset password</Eyebrow>
          <h1 className="mt-1.5 font-display text-[28px] font-semibold leading-[1.2] text-ink">
            Check your inbox
          </h1>
          <Body className="mt-2 leading-[1.55]">
            If an account exists for{" "}
            <strong className="text-ink">{email}</strong>, a one-time reset
            link is on its way. The link expires in 30 minutes.
          </Body>
        </header>

        <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-info-soft text-info">
          <MailCheck size={22} />
        </div>

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

  return (
    <div>
      <header className="mb-7">
        <Eyebrow className="text-info">Reset password</Eyebrow>
        <h1 className="mt-1.5 font-display text-[28px] font-semibold leading-[1.2] text-ink">
          Get a reset link
        </h1>
        <Body className="mt-2 leading-[1.55]">
          Enter the email you sign in with. We&apos;ll send a one-time link
          that expires in 30 minutes.
        </Body>
      </header>

      <form className="space-y-3.5" onSubmit={onSubmit}>
        <label htmlFor="email" className="block">
          <span className="mb-1.5 block text-[12px] font-medium text-ink-soft">
            Work email
          </span>
          <input
            id="email"
            type="email"
            autoComplete="email"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="you@company.com"
            className={authInputClass}
          />
        </label>

        <Button type="submit" size="lg" className="w-full" disabled={submitting}>
          <Mail size={14} />
          {submitting ? "Sending…" : "Send reset link"}
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

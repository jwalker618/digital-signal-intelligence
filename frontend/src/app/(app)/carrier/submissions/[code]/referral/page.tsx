"use client";

import { FormEvent, useState } from "react";
import {
  CheckCircle2,
  CornerDownLeft,
  FileQuestion,
  Loader2,
} from "lucide-react";
import { WorkbenchTopbar } from "@/components/chrome/workbench-topbar";
import { Card } from "@/components/ui/card";
import { Chip } from "@/components/ui/chip";
import { Button } from "@/components/ui/button";
import { Eyebrow, Body, Micro } from "@/components/ui/typography";
import { LabelRow } from "@/components/ui/label-row";
import { PageLoading } from "@/components/base/pageStates";
import { postBrokerReply } from "@/lib/portalApi";
import { useAuthStore } from "@/store/authStore";
import { useDsiStore } from "@/store/dsiStore";
import { formatText } from "@/lib/format";
import { fmtRelative } from "@/lib/utils";

/**
 * Referral Actions — the underwriter's workspace for handling a referral.
 * Reply with body + optional signal_value_update. Reassessment is fired
 * server-side; the response carries `triggered_reassessment` + a new quote
 * id if applicable.
 */
export default function ReferralActionsPage() {
  const accessToken = useAuthStore((s) => s.accessToken);
  const sub = useDsiStore((s) => s.activeSubmission);
  const referral = useDsiStore((s) => s.activeReferral);
  const signals = useDsiStore((s) => s.riskSignals);

  const [body, setBody] = useState("");
  const [signalId, setSignalId] = useState("");
  const [signalValue, setSignalValue] = useState("");
  const [evidence, setEvidence] = useState("");

  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<{
    triggered_reassessment: boolean;
    new_quote_id: string | null;
  } | null>(null);

  if (!sub) {
    return (
      <>
        <WorkbenchTopbar activeTabLabel="Referral Actions" />
        <PageLoading message="Loading submission…" />
      </>
    );
  }

  if (!referral) {
    return (
      <>
        <WorkbenchTopbar activeTabLabel="Referral Actions" />
        <div className="flex flex-1 items-start justify-center px-9 py-12">
          <Card pad="lg" className="max-w-md">
            <Eyebrow>No referral</Eyebrow>
            <Body className="mt-2">
              This submission isn't currently referred. Referral actions become
              available once the engine flags a submission for review.
            </Body>
          </Card>
        </div>
      </>
    );
  }

  const referralCode = String(referral.referral_code ?? "");
  const reasons = (referral.reasons as string[] | undefined) ?? [];
  const status = String(referral.referral_state ?? referral.status ?? "open");
  const awaiting = String(referral.awaiting_party ?? "");

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    if (!body.trim() || submitting) return;
    setSubmitting(true);
    setError(null);
    try {
      const payload = {
        body,
        ...(signalId && signalValue
          ? {
              signal_value_update: {
                signal_id: signalId,
                new_value: isNaN(Number(signalValue))
                  ? signalValue
                  : Number(signalValue),
                evidence_basis: evidence || undefined,
              },
            }
          : {}),
      };
      const resp = await postBrokerReply(accessToken, referralCode, payload);
      setSuccess({
        triggered_reassessment: resp.triggered_reassessment,
        new_quote_id: resp.new_quote_id ?? null,
      });
      setBody("");
      setSignalId("");
      setSignalValue("");
      setEvidence("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Couldn't send reply.");
    } finally {
      setSubmitting(false);
    }
  }

  const showSignalForm = !!signalId || signals.length > 0;

  return (
    <>
      <WorkbenchTopbar activeTabLabel="Referral Actions" />
      <div className="flex-1 overflow-y-auto px-9 py-7">
        <div className="mx-auto grid max-w-[1080px] gap-6">
          <header>
            <Eyebrow>Underwriting</Eyebrow>
            <h1 className="mt-1 font-display text-[28px] font-semibold leading-tight text-ink">
              Referral actions
            </h1>
            <Body className="mt-2">
              Reply to the broker, optionally update a signal value and
              trigger a reassessment.
            </Body>
          </header>

          {/* Referral context */}
          <Card pad="md" className="space-y-3">
            <div className="flex items-start justify-between gap-3">
              <div>
                <Eyebrow>Referral</Eyebrow>
                <p className="mt-1 font-mono text-[13px] text-ink">
                  {referralCode}
                </p>
                {referral.opened_at != null && (
                  <Micro className="mt-1 block">
                    opened {fmtRelative(String(referral.opened_at))}
                  </Micro>
                )}
              </div>
              <div className="space-y-1 text-right">
                <Chip
                  variant={/awaiting/i.test(status) ? "spot" : "info"}
                  size="sm"
                >
                  {formatText(status, "capitalize")}
                </Chip>
                {awaiting && (
                  <Micro className="block">
                    awaiting {formatText(awaiting, "capitalize")}
                  </Micro>
                )}
              </div>
            </div>
            {reasons.length > 0 && (
              <div className="rounded-card border border-rule bg-surface-sunken px-4 py-3">
                <Eyebrow className="mb-1.5">Reasons</Eyebrow>
                <ul className="space-y-1">
                  {reasons.map((r, i) => (
                    <li
                      key={i}
                      className="flex items-start gap-2 text-[13px] text-ink"
                    >
                      <FileQuestion
                        size={13}
                        className="mt-1 shrink-0 text-ink-mute"
                      />
                      {r}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </Card>

          {/* Success state */}
          {success && (
            <Card variant="pos" pad="md" className="flex items-start gap-3">
              <CheckCircle2 size={18} className="mt-0.5 shrink-0 text-pos" />
              <div>
                <Eyebrow className="text-pos">Reply sent</Eyebrow>
                <Body className="mt-1">
                  {success.triggered_reassessment
                    ? "Your reply triggered a reassessment."
                    : "Your reply has been posted to the thread."}
                  {success.new_quote_id && (
                    <>
                      {" "}
                      New quote{" "}
                      <span className="font-mono">{success.new_quote_id}</span>{" "}
                      created.
                    </>
                  )}
                </Body>
              </div>
            </Card>
          )}

          {/* Composer */}
          <Card variant="spot" pad="lg">
            <form className="space-y-4" onSubmit={onSubmit}>
              <header>
                <Eyebrow className="text-spot-deep dark:text-spot">
                  Your reply
                </Eyebrow>
                <Micro>
                  Posts to /portal/queries/{referralCode}/reply. Visible to
                  the broker (and the insured if open thread).
                </Micro>
              </header>
              <textarea
                value={body}
                onChange={(e) => setBody(e.target.value)}
                rows={6}
                placeholder="Explain the decision, request evidence, set conditions…"
                className="block w-full resize-y rounded-btn border border-spot bg-surface px-3 py-2.5 text-[14px] text-ink placeholder:text-ink-mute focus:border-spot focus:outline-none focus:ring-2 focus:ring-spot/30"
              />

              {/* Signal value update */}
              {showSignalForm && (
                <details className="rounded-btn border border-rule bg-surface px-3 py-2">
                  <summary className="cursor-pointer text-[12.5px] font-semibold text-ink">
                    Optional: update a signal value
                  </summary>
                  <div className="mt-3 grid gap-3 md:grid-cols-2">
                    <Field id="ref-sig" label="Signal">
                      <select
                        id="ref-sig"
                        value={signalId}
                        onChange={(e) => setSignalId(e.target.value)}
                        className="block h-10 w-full rounded-btn border border-rule-strong bg-surface px-3 text-[13px] text-ink focus:border-info focus:outline-none focus:ring-2 focus:ring-info/30"
                      >
                        <option value="">— none —</option>
                        {signals.map((s) => (
                          <option
                            key={String(s.signal_id ?? s.signal_code)}
                            value={String(s.signal_id ?? s.signal_code)}
                          >
                            {String(s.signal_id ?? s.signal_code)}
                          </option>
                        ))}
                      </select>
                    </Field>
                    <Field id="ref-val" label="New value">
                      <input
                        id="ref-val"
                        type="text"
                        value={signalValue}
                        onChange={(e) => setSignalValue(e.target.value)}
                        placeholder="true / false / 0.85 / etc."
                        className="block h-10 w-full rounded-btn border border-rule-strong bg-surface px-3 text-[13px] text-ink focus:border-info focus:outline-none focus:ring-2 focus:ring-info/30"
                      />
                    </Field>
                    <Field
                      id="ref-evi"
                      label="Evidence basis"
                      className="md:col-span-2"
                    >
                      <input
                        id="ref-evi"
                        type="text"
                        value={evidence}
                        onChange={(e) => setEvidence(e.target.value)}
                        placeholder="What backs this change — broker email, attestation, report…"
                        className="block h-10 w-full rounded-btn border border-rule-strong bg-surface px-3 text-[13px] text-ink focus:border-info focus:outline-none focus:ring-2 focus:ring-info/30"
                      />
                    </Field>
                  </div>
                  <Micro className="mt-2 block">
                    Updating a signal value triggers a fresh assessment and may
                    produce a new quote version.
                  </Micro>
                </details>
              )}

              {error && (
                <div
                  role="alert"
                  className="rounded-btn border border-neg bg-neg-soft px-3 py-2 text-[13px] text-neg"
                >
                  {error}
                </div>
              )}

              <div className="flex items-center justify-end gap-3">
                <Micro>⌘↵ to send</Micro>
                <Button
                  type="submit"
                  variant="spot"
                  disabled={submitting || body.trim().length === 0}
                >
                  {submitting ? (
                    <>
                      <Loader2 size={14} className="animate-spin" />
                      Sending…
                    </>
                  ) : (
                    <>
                      <CornerDownLeft size={14} />
                      Send reply
                    </>
                  )}
                </Button>
              </div>
            </form>
          </Card>

          {/* Quick reference */}
          <LabelRow
            label="Submission"
            value={
              <span className="font-mono text-[12.5px]">
                {String(sub.submission_code)}
              </span>
            }
          />
        </div>
      </div>
    </>
  );
}

function Field({
  id,
  label,
  className,
  children,
}: {
  id: string;
  label: string;
  className?: string;
  children: React.ReactNode;
}) {
  return (
    <div className={className}>
      <label
        htmlFor={id}
        className="mb-1.5 block text-[11.5px] font-semibold uppercase tracking-[0.08em] text-ink-soft"
      >
        {label}
      </label>
      {children}
    </div>
  );
}

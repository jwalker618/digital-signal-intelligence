"use client";

import { FormEvent, useState } from "react";
import Link from "next/link";
import {
  ArrowLeft,
  CheckCircle2,
  CornerDownLeft,
  FileQuestion,
  Loader2,
  Paperclip,
} from "lucide-react";
import { Topbar } from "@/components/chrome/topbar";
import { Card } from "@/components/ui/card";
import { Chip } from "@/components/ui/chip";
import { Button } from "@/components/ui/button";
import { Avatar } from "@/components/ui/avatar";
import { Eyebrow, Body, Micro } from "@/components/ui/typography";
import { postBrokerReply } from "@/lib/portalApi";
import { useAuthStore } from "@/store/authStore";
import { formatText } from "@/lib/format";
import { fmtRelative } from "@/lib/utils";
import { cn } from "@/lib/utils";
import type {
  CommunicationsThreadResponse,
  CommunicationThreadMessage,
} from "@/types/portal";

interface ThreadViewProps {
  data: CommunicationsThreadResponse;
  /** Who's looking — drives the "you" label, message bubble alignment, and
   *  whether the reply composer renders. */
  viewerRole: "client" | "broker";
  /** Path back to the inbox. */
  inboxPath: string;
  /** Crumb root, e.g. "Client Portal" / "Broker Portal". */
  personaCrumb: string;
  /** Callback fired after a successful reply, so the parent reloads. */
  onReplied: () => void;
}

/**
 * Communications thread renderer. Same visual treatment for client and
 * broker viewers; only the "you" label, awaiting test, and back-link change.
 */
export function ThreadView({
  data,
  viewerRole,
  inboxPath,
  personaCrumb,
  onReplied,
}: ThreadViewProps) {
  const youParty = viewerRole === "client" ? /client|insured|you/i : /broker|me/i;
  const awaitingYou = data.awaiting_party && youParty.test(data.awaiting_party);

  return (
    <>
      <Topbar
        crumbs={[personaCrumb, "Communications", data.referral_code]}
        entity={viewerRole === "client" ? data.entity_name : undefined}
      />
      <div className="flex-1 overflow-y-auto px-9 py-7">
        <div className="mx-auto grid max-w-[1000px] gap-6">
          <Link
            href={inboxPath}
            className="inline-flex items-center gap-1.5 text-[13px] font-medium text-info hover:underline"
          >
            <ArrowLeft size={14} /> All threads
          </Link>

          <Card pad="lg" className="space-y-4">
            <div className="flex items-start justify-between gap-4">
              <div>
                <Eyebrow>Coverage</Eyebrow>
                <h1 className="mt-1 font-display text-[28px] font-semibold leading-tight text-ink">
                  {data.coverage}
                  {data.policy_label && (
                    <span className="ml-2 text-[18px] font-medium text-ink-soft">
                      · {data.policy_label}
                    </span>
                  )}
                </h1>
                <Micro className="mt-1 block font-mono">
                  {data.referral_code} ·{" "}
                  <span className="text-ink-soft">{data.entity_name}</span>
                  {" · "}
                  submission{" "}
                  <Link
                    href={`/client/submissions/${data.submission_code}`}
                    className="text-info hover:underline"
                  >
                    {data.submission_code}
                  </Link>
                </Micro>
              </div>
              <Chip
                variant={
                  awaitingYou ? "spot" : data.status === "closed" ? "mute" : "info"
                }
              >
                {awaitingYou
                  ? "Awaiting you"
                  : formatText(data.status, "capitalize")}
              </Chip>
            </div>

            {data.reasons.length > 0 && (
              <div className="rounded-card border border-rule bg-surface-sunken px-4 py-3">
                <Eyebrow className="mb-1.5">Reasons</Eyebrow>
                <ul className="space-y-1">
                  {data.reasons.map((r, i) => (
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

          <section className="space-y-4">
            <Eyebrow>Conversation ({data.messages.length})</Eyebrow>
            <ol className="space-y-3">
              {data.messages.map((m) => (
                <MessageBubble
                  key={m.id}
                  message={m}
                  viewerRole={viewerRole}
                />
              ))}
            </ol>
          </section>

          {awaitingYou && (
            <ReplyComposer
              referralCode={data.referral_code}
              onSent={onReplied}
              viewerRole={viewerRole}
            />
          )}
        </div>
      </div>
    </>
  );
}

function MessageBubble({
  message,
  viewerRole,
}: {
  message: CommunicationThreadMessage;
  viewerRole: "client" | "broker";
}) {
  const dir = message.direction;
  const isYou =
    viewerRole === "client"
      ? /client|insured|you/i.test(dir)
      : /broker|me/i.test(dir);
  const isUw = /uw|underwriter/i.test(dir);
  const isBroker = /broker/i.test(dir);
  const isClient = /client|insured/i.test(dir);

  const fromLabel = isYou
    ? "You"
    : isUw
      ? "Underwriter"
      : isBroker
        ? "Broker"
        : isClient
          ? "Client"
          : dir;
  const initials = isYou ? "YO" : isUw ? "UW" : isBroker ? "BR" : "CL";

  return (
    <li className={cn("flex gap-3", isYou && "flex-row-reverse")}>
      <Avatar initials={initials} size="sm" />
      <div
        className={cn(
          "flex max-w-[78%] flex-col gap-1.5",
          isYou && "items-end",
        )}
      >
        <div className="flex items-baseline gap-2 text-[12px]">
          <span className="font-semibold text-ink">{fromLabel}</span>
          <Micro>{fmtRelative(message.created_at)}</Micro>
          {message.triggered_reassessment && (
            <Chip variant="info" size="sm">
              <CheckCircle2 size={11} />
              Reassessed
            </Chip>
          )}
        </div>
        <div
          className={cn(
            "rounded-card border px-4 py-3 text-[13.5px] leading-[1.55]",
            isYou
              ? "border-info bg-info-soft text-ink"
              : "border-rule bg-surface text-ink",
          )}
        >
          {message.body}
          {message.request_signal_evidence && (
            <div className="mt-2.5 border-t border-rule pt-2 text-[12px] text-spot-deep dark:text-spot">
              <strong>Evidence requested:</strong>{" "}
              {message.request_signal_evidence}
            </div>
          )}
        </div>
      </div>
    </li>
  );
}

function ReplyComposer({
  referralCode,
  onSent,
  viewerRole,
}: {
  referralCode: string;
  onSent: () => void;
  viewerRole: "client" | "broker";
}) {
  const accessToken = useAuthStore((s) => s.accessToken);
  const [body, setBody] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    if (!body.trim() || submitting) return;
    setSubmitting(true);
    setError(null);
    try {
      await postBrokerReply(accessToken, referralCode, { body });
      setBody("");
      onSent();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Couldn't send reply.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <Card variant="spot" pad="lg">
      <form className="space-y-3" onSubmit={onSubmit}>
        <header className="flex items-center justify-between">
          <Eyebrow className="text-spot-deep dark:text-spot">Your reply</Eyebrow>
          <Micro>
            {viewerRole === "broker"
              ? "Visible to the client and underwriter."
              : "Visible to the underwriter and broker."}
          </Micro>
        </header>
        <textarea
          value={body}
          onChange={(e) => setBody(e.target.value)}
          rows={5}
          placeholder="Type your response, paste evidence URLs, or attach documents…"
          className="block w-full resize-y rounded-btn border border-spot bg-surface px-3 py-2.5 text-[14px] text-ink placeholder:text-ink-mute focus:border-spot focus:outline-none focus:ring-2 focus:ring-spot/30"
        />
        {error && (
          <div
            role="alert"
            className="rounded-btn border border-neg bg-neg-soft px-3 py-2 text-[13px] text-neg"
          >
            {error}
          </div>
        )}
        <div className="flex items-center gap-3">
          <Button
            type="button"
            variant="ghost"
            size="sm"
            title="Attachments coming soon"
          >
            <Paperclip size={14} />
            Attach
          </Button>
          <div className="ml-auto flex items-center gap-2">
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
        </div>
      </form>
    </Card>
  );
}

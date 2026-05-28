"use client";

import { FormEvent, use, useState } from "react";
import Link from "next/link";
import {
  ArrowLeft,
  CheckCircle2,
  Loader2,
  Paperclip,
  Send,
} from "lucide-react";
import { Topbar } from "@/components/chrome/topbar";
import { Card } from "@/components/ui/card";
import { Chip } from "@/components/ui/chip";
import { Button } from "@/components/ui/button";
import { Avatar } from "@/components/ui/avatar";
import { Eyebrow, Micro, Caption } from "@/components/ui/typography";
import { PageError, PageLoading, RoleGate } from "@/components/base/pageStates";
import { useRoleScopedFetch } from "@/lib/useRoleScopedFetch";
import {
  fetchCommunicationThread,
  postBrokerReply,
} from "@/lib/portalApi";
import { useAuthStore } from "@/store/authStore";
import { formatText } from "@/lib/format";
import { fmtRelative } from "@/lib/utils";
import { cn } from "@/lib/utils";
import type {
  CommunicationsThreadResponse,
  CommunicationThreadMessage,
} from "@/types/portal";

export default function ClientThreadPage(props: {
  params: Promise<{ code: string }>;
}) {
  const { code } = use(props.params);
  const accessToken = useAuthStore((s) => s.accessToken);
  const user = useAuthStore((s) => s.user);
  const enabled = !!accessToken && user?.role === "CLIENT";

  const { data, error, loading, reload } =
    useRoleScopedFetch<CommunicationsThreadResponse>({
      fetcher: () => fetchCommunicationThread(accessToken, code),
      enabled,
      deps: [accessToken, code],
    });

  if (!user) return <PageLoading message="Signing in…" />;
  if (user.role && user.role !== "CLIENT") return <RoleGate expected="client" />;
  if (loading) return <PageLoading />;
  if (error) return <PageError message={error} />;
  if (!data) return <PageLoading />;

  return <ThreadBody data={data} onReplied={reload} />;
}

function ThreadBody({
  data,
  onReplied,
}: {
  data: CommunicationsThreadResponse;
  onReplied: () => void;
}) {
  const awaitingYou =
    data.awaiting_party && /client|insured|you/i.test(data.awaiting_party);

  return (
    <>
      <Topbar
        crumbs={["Client Portal", "Communications", data.referral_code]}
        entity={data.entity_name}
      />
      <div className="flex-1 overflow-y-auto px-9 py-7">
        <div className="mx-auto grid max-w-[1100px] gap-4">
          {/* ────────── breadcrumb + header ────────── */}
          <div>
            <div className="flex items-center gap-2">
              <Link
                href="/client/communications"
                className="inline-flex items-center gap-1 text-[11px] text-ink-mute hover:text-ink"
              >
                <ArrowLeft size={12} /> All threads
              </Link>
              <Micro>/</Micro>
              <Micro className="font-mono">{data.referral_code}</Micro>
            </div>
            <h1 className="mt-2.5 font-display text-[32px] font-semibold leading-tight tracking-tight text-ink">
              {data.entity_name}{" "}
              <span className="font-normal text-ink-mute">—</span>{" "}
              {data.coverage} referral
            </h1>
            <div className="mt-2 flex flex-wrap gap-2">
              {awaitingYou && (
                <Chip variant="spot" size="md">
                  awaiting you
                </Chip>
              )}
              <Chip variant="mute" size="md">
                {data.coverage}
                {data.policy_label && ` · ${data.policy_label}`}
              </Chip>
              <Chip variant="mute" size="md">
                {formatText(data.status, "capitalize")}
              </Chip>
              {data.reasons.length > 0 && (
                <Chip variant="mute" size="md">
                  <Paperclip size={11} /> evidence requested
                </Chip>
              )}
            </div>
          </div>

          {/* ────────── reasons + evidence ────────── */}
          {data.reasons.length > 0 && (
            <div className="grid gap-4 lg:grid-cols-[1.4fr_1fr]">
              <Card pad="lg">
                <Eyebrow>Underwriter is asking about</Eyebrow>
                <ul className="mt-2 list-disc space-y-1.5 pl-5 text-[13.5px] leading-relaxed text-ink">
                  {data.reasons.map((r, i) => (
                    <li key={i}>{r}</li>
                  ))}
                </ul>
              </Card>
              <Card variant="spot" pad="lg">
                <Eyebrow className="text-spot-deep dark:text-spot">
                  Evidence requested
                </Eyebrow>
                <div className="mt-2.5 flex flex-col gap-2">
                  {data.reasons.slice(0, 4).map((r, i) => (
                    <div
                      key={i}
                      className="flex items-center justify-between gap-2 rounded-card border border-rule bg-surface-elev px-3 py-2"
                    >
                      <div className="flex min-w-0 items-center gap-2">
                        <Paperclip size={13} className="shrink-0 text-spot" />
                        <span className="truncate font-mono text-[12.5px] text-ink">
                          {r}
                        </span>
                      </div>
                      <Chip variant="spot" size="sm">
                        missing
                      </Chip>
                    </div>
                  ))}
                </div>
              </Card>
            </div>
          )}

          {/* ────────── messages thread ────────── */}
          <Card pad="lg">
            <div className="mb-3.5 flex items-baseline justify-between">
              <h3 className="font-display text-[17px] font-semibold leading-tight text-ink">
                Thread · {data.messages.length} message
                {data.messages.length === 1 ? "" : "s"}
              </h3>
              <Micro>Newest at bottom</Micro>
            </div>
            <ol className="flex flex-col gap-3.5">
              {data.messages.map((m) => (
                <MessageBubble key={m.id} message={m} />
              ))}
            </ol>
          </Card>

          {/* ────────── reply composer ────────── */}
          {awaitingYou && (
            <ReplyComposer referralCode={data.referral_code} onSent={onReplied} />
          )}
        </div>
      </div>
    </>
  );
}

function MessageBubble({ message }: { message: CommunicationThreadMessage }) {
  const dir = message.direction;
  const isYou = /client|insured|you/i.test(dir);
  const isUw = /uw|underwriter/i.test(dir);
  const isBroker = /broker/i.test(dir);
  const fromLabel = isYou
    ? "You"
    : isUw
      ? "Underwriter"
      : isBroker
        ? "Broker"
        : dir;
  const initials = isYou ? "YO" : isUw ? "UW" : isBroker ? "BR" : "CL";
  const accent = isUw
    ? "border-info text-info"
    : isBroker
      ? "border-aux text-aux"
      : "border-spot text-spot";

  return (
    <li
      className={cn(
        "grid grid-cols-[40px_1fr] gap-3",
        isYou ? "ml-[60px]" : "mr-[60px]",
      )}
    >
      <Avatar initials={initials} size="sm" className={accent} />
      <div
        className={cn(
          "rounded-card border border-rule px-3.5 py-3",
          isYou ? "bg-spot-soft/50" : "bg-surface-elev",
        )}
      >
        <div className="mb-1 flex items-baseline justify-between gap-2">
          <div className="flex items-baseline gap-2">
            <span className="text-[13px] font-semibold text-ink">
              {fromLabel}
            </span>
            {message.triggered_reassessment && (
              <Chip variant="info" size="sm">
                <CheckCircle2 size={11} /> Reassessed
              </Chip>
            )}
          </div>
          <Micro>{fmtRelative(message.created_at)}</Micro>
        </div>
        <p className="text-[13.5px] leading-[1.55] text-ink">{message.body}</p>
        {message.request_signal_evidence && (
          <div className="mt-2.5 border-t border-rule pt-2 text-[12px] text-spot-deep dark:text-spot">
            <strong>Evidence requested:</strong>{" "}
            {message.request_signal_evidence}
          </div>
        )}
      </div>
    </li>
  );
}

function ReplyComposer({
  referralCode,
  onSent,
}: {
  referralCode: string;
  onSent: () => void;
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
      <form className="flex flex-col gap-3" onSubmit={onSubmit}>
        <div className="flex items-baseline justify-between">
          <Eyebrow className="text-spot-deep dark:text-spot">Your reply</Eyebrow>
          <Chip variant="spot" size="sm">
            they&apos;re waiting
          </Chip>
        </div>
        <textarea
          value={body}
          onChange={(e) => setBody(e.target.value)}
          rows={5}
          placeholder="Type your reply…"
          className="block min-h-[100px] w-full resize-y rounded-btn border border-rule-strong bg-surface px-3.5 py-3 text-[13.5px] leading-[1.55] text-ink placeholder:text-ink-mute focus:border-spot focus:outline-none focus:ring-2 focus:ring-spot/30"
        />
        {error && (
          <div
            role="alert"
            className="rounded-btn border border-neg bg-neg-soft px-3 py-2 text-[13px] text-neg"
          >
            {error}
          </div>
        )}
        <div className="flex items-center justify-between gap-3">
          <div className="flex items-center gap-2">
            <Button type="button" variant="ghost" size="sm" disabled>
              <Paperclip size={13} /> Attach evidence
            </Button>
            <Caption>Files requested above</Caption>
          </div>
          <div className="flex gap-2">
            <Button type="button" variant="ghost" size="md" disabled>
              Save draft
            </Button>
            <Button
              type="submit"
              variant="spot"
              size="md"
              disabled={submitting || body.trim().length === 0}
            >
              {submitting ? (
                <>
                  <Loader2 size={14} className="animate-spin" /> Sending…
                </>
              ) : (
                <>
                  <Send size={13} /> Send reply
                </>
              )}
            </Button>
          </div>
        </div>
      </form>
    </Card>
  );
}

"use client";

// v8 Phase 8 polish — /communications/[code]
//
// Full thread view for one referral with reply form (for brokers
// when state is AWAITING_BROKER, or for clients when AWAITING_CLIENT).

import { use, useEffect, useState } from "react";
import Link from "next/link";

import {
  AlertTriangle,
  ArrowLeft,
  ArrowRight,
  Building2,
  CheckCircle2,
  MessageSquare,
  MessagesSquare,
  Send,
  UserStar,
} from "lucide-react";

import ViewCanvas from "@/components/ViewCanvas";
import {
  CardGrid,
  StandardCard,
  SubmissionHeaderCard,
} from "@/components/base/cards";
import {
  InfoPanel,
  KpiTile,
  LabelValueList,
} from "@/components/base/content/primatives";

import { useAuthStore } from "@/store/authStore";
import { useDsiStore } from "@/store/dsiStore";
import {
  fetchCommunicationThread,
  postBrokerReply,
} from "@/lib/portalApi";
import { homePathForRole } from "@/lib/portalPaths";
import type {
  CommunicationsThreadResponse,
  CommunicationThreadMessage,
} from "@/types/portal";


export default function CommunicationsThreadView({
  params,
}: {
  params: Promise<{ code: string }>;
}) {
  const { code } = use(params);
  const accessToken = useAuthStore((s) => s.accessToken);
  const userRole = useAuthStore((s) => s.user?.role ?? null);
  const setActiveMenu = useDsiStore((s) => s.setActiveMenu);

  const [thread, setThread] = useState<CommunicationsThreadResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [reloadKey, setReloadKey] = useState(0);

  useEffect(() => { setActiveMenu("Communications"); }, [setActiveMenu]);

  useEffect(() => {
    let cancelled = false;
    async function load() {
      try {
        const resp = await fetchCommunicationThread(accessToken, code);
        if (!cancelled) setThread(resp);
      } catch (e) {
        if (!cancelled) setError(e instanceof Error ? e.message : String(e));
      }
    }
    if (accessToken) load();
    return () => { cancelled = true; };
  }, [accessToken, code, reloadKey]);

  if (error) return <ErrShell msg={error} />;
  if (!thread) return <LoadShell />;

  const isBroker = userRole === "BROKER";
  const canReply = isBroker && thread.awaiting_party === "broker";
  const lastUWMessage = [...thread.messages]
    .reverse()
    .find((m) => m.direction === "u2b");

  return (
    <ViewCanvas>
      <CardGrid cols="grid-cols-1" className="gap-4">

        <SubmissionHeaderCard
          decision={thread.awaiting_party ? "refer" : "approve"}
          title={`${thread.entity_name} — ${thread.policy_label ?? thread.coverage}`}
          subtitle={`Referral ${thread.referral_code}`}
          lucideIcon={MessagesSquare}
          headerRight={
            <Link
              href={`${homePathForRole(userRole)}/communications`}
              className="text-xs underline hover:text-generate-text-input flex items-center gap-1"
            >
              <ArrowLeft className="generate-app-icon" /> All threads
            </Link>
          }
        >
          <div className="grid grid-cols-2 md:grid-cols-4 gap-6 py-2">
            <KpiTile label="Status" value={thread.status.replace(/_/g, " ")} />
            <KpiTile
              label="Awaiting"
              value={thread.awaiting_party ?? "—"}
              subtext={canReply ? "Action required" : undefined}
            />
            <KpiTile label="Messages" value={thread.messages.length} />
            <KpiTile
              label="Evidence requested"
              value={
                <span className="text-sm">
                  {lastUWMessage?.request_signal_evidence ?? "—"}
                </span>
              }
            />
          </div>
        </SubmissionHeaderCard>

        {thread.reasons.length > 0 && (
          <StandardCard title="Underwriter reasons" lucideIcon={UserStar}>
            <ul className="list-disc pl-5 text-sm space-y-1">
              {thread.reasons.map((r, i) => (
                <li key={i}>{r}</li>
              ))}
            </ul>
          </StandardCard>
        )}

        <StandardCard title={`Thread (${thread.messages.length})`} lucideIcon={MessageSquare}>
          {thread.messages.length === 0 ? (
            <p className="text-sm">No messages yet.</p>
          ) : (
            <div className="space-y-3 py-2">
              {thread.messages.map((m) => (
                <MessageBubble key={m.id} message={m} />
              ))}
            </div>
          )}
        </StandardCard>

        {canReply && (
          <StandardCard title="Reply" lucideIcon={Send}>
            <BrokerReplyForm
              referralCode={thread.referral_code}
              accessToken={accessToken}
              suggestedSignal={lastUWMessage?.request_signal_evidence ?? "mfa_enabled"}
              onSubmitted={() => setReloadKey((k) => k + 1)}
            />
          </StandardCard>
        )}

        {!canReply && thread.awaiting_party && (
          <InfoPanel label="Status">
            <p className="text-sm">
              Awaiting {thread.awaiting_party} response. {isBroker ? "" : "Your broker is working on a reply."}
            </p>
          </InfoPanel>
        )}

        {!thread.awaiting_party && (
          <InfoPanel label="Status">
            <p className="text-sm text-generate-text-good flex items-center gap-2">
              <CheckCircle2 className="generate-app-icon" /> No pending action on this thread.
            </p>
          </InfoPanel>
        )}

      </CardGrid>
    </ViewCanvas>
  );
}


function MessageBubble({ message }: { message: CommunicationThreadMessage }) {
  const isUnderwriter = message.direction === "u2b";
  const align = isUnderwriter ? "" : "ml-auto";
  const tone = isUnderwriter
    ? "border-generate-text-outline bg-generate-light-input"
    : "border-generate-text-comment/30 bg-generate-text-comment/5";

  return (
    <div
      className={`max-w-[85%] border rounded-lg p-3 ${align} ${tone}`}
    >
      <div className="flex items-center justify-between mb-2 text-xs">
        <span className="font-bold flex items-center gap-1">
          {isUnderwriter ? (
            <>
              <Building2 className="generate-app-icon" /> Underwriter
            </>
          ) : (
            <>
              <UserStar className="generate-app-icon" /> Broker
            </>
          )}
        </span>
        <span className="text-generate-text-placeholder">
          {new Date(message.created_at).toLocaleString()}
        </span>
      </div>
      <p className="text-sm whitespace-pre-line">{message.body}</p>

      {message.request_signal_evidence && (
        <div className="text-xs mt-2 text-generate-text-placeholder">
          Evidence requested: <code className="text-generate-text-comment">{message.request_signal_evidence}</code>
        </div>
      )}

      {message.signal_value_update && (
        <div className="mt-2 text-xs">
          <span className="text-generate-text-placeholder">Signal update: </span>
          <code className="text-generate-text-good">
            {(message.signal_value_update.signal_id as string) ?? "?"}
            {" = "}
            {String(message.signal_value_update.new_value)}
          </code>
        </div>
      )}

      {message.triggered_reassessment && (
        <div className="mt-2 text-xs text-generate-text-good flex items-center gap-1">
          <CheckCircle2 className="generate-app-icon" />
          Triggered re-assessment{message.new_quote_id ? " (new quote produced)" : ""}
        </div>
      )}
    </div>
  );
}


function BrokerReplyForm({
  referralCode, accessToken, suggestedSignal, onSubmitted,
}: {
  referralCode: string;
  accessToken: string | null;
  suggestedSignal: string;
  onSubmitted: () => void;
}) {
  const [body, setBody] = useState(
    "Confirmation attached. Please see evidence and let me know if you need anything further."
  );
  const [signalId, setSignalId] = useState(suggestedSignal);
  const [newValue, setNewValue] = useState<"true" | "false">("true");
  const [updateSignal, setUpdateSignal] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setSubmitting(true); setErr(null);
    try {
      await postBrokerReply(accessToken, referralCode, {
        body,
        signal_value_update: updateSignal
          ? {
              signal_id: signalId,
              new_value: newValue === "true",
            }
          : undefined,
      });
      onSubmitted();
    } catch (e) {
      setErr(e instanceof Error ? e.message : String(e));
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <form onSubmit={onSubmit} className="space-y-3 py-2">
      <div>
        <label className="block text-xs text-generate-text-placeholder mb-1">
          Response to underwriter
        </label>
        <textarea
          value={body}
          onChange={(e) => setBody(e.target.value)}
          rows={3}
          className="
            w-full text-sm
            bg-generate-light-input
            border border-generate-text-outline
            rounded-md p-2
            focus:outline-none focus:border-generate-text-input"
          required
        />
      </div>

      <label className="flex items-center gap-2 text-sm cursor-pointer">
        <input
          type="checkbox"
          checked={updateSignal}
          onChange={(e) => setUpdateSignal(e.target.checked)}
          className="w-4 h-4"
        />
        Update signal value and trigger re-assessment
      </label>

      {updateSignal && (
        <div className="grid grid-cols-3 gap-3">
          <div className="col-span-2">
            <label className="block text-xs text-generate-text-placeholder mb-1">
              Signal to update
            </label>
            <input
              value={signalId}
              onChange={(e) => setSignalId(e.target.value)}
              className="
                w-full text-sm
                bg-generate-light-input
                border border-generate-text-outline
                rounded-md p-2"
            />
          </div>
          <div>
            <label className="block text-xs text-generate-text-placeholder mb-1">
              Value
            </label>
            <select
              value={newValue}
              onChange={(e) => setNewValue(e.target.value as "true" | "false")}
              className="
                w-full text-sm
                bg-generate-light-input
                border border-generate-text-outline
                rounded-md p-2"
            >
              <option value="true">true (in place)</option>
              <option value="false">false (not in place)</option>
            </select>
          </div>
        </div>
      )}

      {err && <p className="text-xs text-generate-text-bad">{err}</p>}

      <button
        type="submit"
        disabled={submitting}
        className="
          flex items-center gap-2
          bg-generate-dark-background text-generate-text-input
          rounded-md px-4 py-2 text-sm font-bold
          hover:opacity-90 disabled:opacity-50"
      >
        <Send className="generate-app-icon" />
        {submitting ? "Submitting…" : "Submit reply"}
        <ArrowRight className="generate-app-icon" />
      </button>
    </form>
  );
}


function LoadShell() {
  return (
    <ViewCanvas>
      <CardGrid cols="grid-cols-1">
        <StandardCard title="Loading" lucideIcon={MessagesSquare}>
          <p className="text-sm">Loading thread…</p>
        </StandardCard>
      </CardGrid>
    </ViewCanvas>
  );
}

function ErrShell({ msg }: { msg: string }) {
  return (
    <ViewCanvas>
      <CardGrid cols="grid-cols-1">
        <StandardCard title="Unable to load" lucideIcon={AlertTriangle}>
          <p className="text-sm text-generate-text-bad">{msg}</p>
        </StandardCard>
      </CardGrid>
    </ViewCanvas>
  );
}

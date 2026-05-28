"use client";

import { FormEvent, useState } from "react";
import { CheckCircle2, Lightbulb, Loader2, Send, X } from "lucide-react";
import { Topbar } from "@/components/chrome/topbar";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Eyebrow, Body, Micro } from "@/components/ui/typography";
import { PageError, PageLoading, RoleGate } from "@/components/base/pageStates";
import { useRoleScopedFetch } from "@/lib/useRoleScopedFetch";
import {
  fetchBrokerRecommendations,
  postSendRecommendation,
} from "@/lib/portalApi";
import { useAuthStore } from "@/store/authStore";
import { formatCurrency } from "@/lib/format";
import type {
  BookGapRecommendation,
  BrokerRecommendationsResponse,
} from "@/types/portal";

export default function BrokerRecommendationsPage() {
  const accessToken = useAuthStore((s) => s.accessToken);
  const user = useAuthStore((s) => s.user);
  const enabled = !!accessToken && user?.role === "BROKER";

  const { data, error, loading, reload } =
    useRoleScopedFetch<BrokerRecommendationsResponse>({
      fetcher: () => fetchBrokerRecommendations(accessToken),
      enabled,
      deps: [accessToken],
    });

  if (!user) return <PageLoading message="Signing in…" />;
  if (user.role && user.role !== "BROKER") return <RoleGate expected="broker" />;
  if (loading) return <PageLoading />;
  if (error) return <PageError message={error} />;
  if (!data) return <PageLoading />;

  return <RecsBody data={data} onSent={reload} />;
}

function RecsBody({
  data,
  onSent,
}: {
  data: BrokerRecommendationsResponse;
  onSent: () => void;
}) {
  const recs = data.recommendations;
  const totalLow = recs.reduce(
    (sum, r) => sum + r.estimated_premium_range_usd[0],
    0,
  );
  const totalHigh = recs.reduce(
    (sum, r) => sum + r.estimated_premium_range_usd[1],
    0,
  );

  const grouped = new Map<string, BookGapRecommendation[]>();
  for (const r of recs) {
    const list = grouped.get(r.client_entity_name) ?? [];
    list.push(r);
    grouped.set(r.client_entity_name, list);
  }

  return (
    <>
      <Topbar
        crumbs={["Broker Portal", "Recommendations"]}
        entity={data.broker_name}
      />
      <div className="flex-1 overflow-y-auto px-9 py-7">
        <div className="mx-auto grid max-w-[1400px] gap-6">
          <header>
            <Eyebrow>Cross-sell</Eyebrow>
            <h1 className="mt-1 font-display text-[32px] font-semibold leading-none tracking-tight text-ink">
              Recommendations
            </h1>
            <Body className="mt-2">
              Coverage lines your clients are likely under-protected on,
              ranked by industry-fit. Send each as a draft to start a
              conversation.
            </Body>
          </header>

          <Card variant="info" pad="lg" className="grid gap-6 sm:grid-cols-3">
            <Stat label="Recommendations">{recs.length}</Stat>
            <Stat label="Affected clients">{grouped.size}</Stat>
            <Stat label="Potential premium" emphasis>
              {recs.length === 0
                ? "—"
                : `${formatCurrency(totalLow)} – ${formatCurrency(totalHigh)}`}
            </Stat>
          </Card>

          {grouped.size === 0 ? (
            <Card pad="lg" className="text-center">
              <Body className="italic">
                Your book is fully covered relative to peer norms. No gaps to
                recommend.
              </Body>
            </Card>
          ) : (
            <div className="space-y-5">
              {[...grouped.entries()]
                .sort((a, b) => a[0].localeCompare(b[0]))
                .map(([entityName, list]) => (
                  <Card key={entityName} pad="md" className="space-y-3">
                    <header className="flex items-baseline justify-between">
                      <div>
                        <h2 className="text-[16px] font-semibold text-ink">
                          {entityName}
                        </h2>
                        {list[0]?.industry_label && (
                          <Micro className="block">
                            {list[0].industry_label}
                          </Micro>
                        )}
                      </div>
                      <Micro>
                        {list.length} gap{list.length === 1 ? "" : "s"}
                      </Micro>
                    </header>
                    <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
                      {list.map((r, i) => (
                        <RecCard
                          key={`${r.client_entity_name}-${i}`}
                          rec={r}
                          onSent={onSent}
                        />
                      ))}
                    </div>
                  </Card>
                ))}
            </div>
          )}
        </div>
      </div>
    </>
  );
}

function RecCard({
  rec,
  onSent,
}: {
  rec: BookGapRecommendation;
  onSent: () => void;
}) {
  const [open, setOpen] = useState(false);
  return (
    <>
      <Card pad="md" variant="default" className="space-y-3">
        <div className="flex items-start justify-between gap-3">
          <div>
            <Eyebrow>{rec.coverage}</Eyebrow>
            <p className="mt-1 text-[14.5px] font-semibold text-ink">
              {rec.coverage}
            </p>
          </div>
          <Lightbulb size={16} className="shrink-0 text-spot" />
        </div>
        <Body className="text-[13px]">{rec.rationale}</Body>
        <div className="flex items-baseline justify-between border-t border-rule pt-3">
          <span className="text-[12.5px] text-ink-soft">Est. premium</span>
          <span className="text-[13px] font-semibold tabular-nums text-ink">
            {formatCurrency(rec.estimated_premium_range_usd[0])} –{" "}
            {formatCurrency(rec.estimated_premium_range_usd[1])}
          </span>
        </div>
        <Button
          type="button"
          variant="spot"
          size="sm"
          className="w-full"
          onClick={() => setOpen(true)}
        >
          <Send size={13} />
          Draft & send
        </Button>
      </Card>
      {open && (
        <SendModal
          rec={rec}
          onClose={() => setOpen(false)}
          onSent={() => {
            setOpen(false);
            onSent();
          }}
        />
      )}
    </>
  );
}

function SendModal({
  rec,
  onClose,
  onSent,
}: {
  rec: BookGapRecommendation;
  onClose: () => void;
  onSent: () => void;
}) {
  const accessToken = useAuthStore((s) => s.accessToken);
  const [message, setMessage] = useState(
    `Hi ${rec.client_entity_name.split(" ")[0]} team,\n\nBased on what we're seeing across your cohort, ${rec.coverage} stands out as a likely gap for you — ${rec.rationale.toLowerCase()} Indicative premium is in the ${formatCurrency(rec.estimated_premium_range_usd[0])}–${formatCurrency(rec.estimated_premium_range_usd[1])} range.\n\nHappy to talk if it's worth exploring.\n\n— Your broker`,
  );
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    if (submitting) return;
    setSubmitting(true);
    setError(null);
    try {
      await postSendRecommendation(accessToken, {
        client_entity_name: rec.client_entity_name,
        coverage: rec.coverage,
        message,
      });
      setSuccess(true);
      setTimeout(onSent, 1200);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Couldn't send.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-ink/40 p-4 backdrop-blur-sm"
      onClick={onClose}
    >
      <div onClick={(e) => e.stopPropagation()} className="w-full max-w-xl">
        <Card pad="lg" className="space-y-4">
          <header className="flex items-start justify-between gap-3">
            <div>
              <Eyebrow>Send recommendation</Eyebrow>
              <h2 className="mt-1 font-display text-[20px] font-semibold text-ink">
                {rec.coverage} → {rec.client_entity_name}
              </h2>
            </div>
            <button
              type="button"
              onClick={onClose}
              className="flex h-8 w-8 items-center justify-center rounded-md text-ink-mute hover:bg-surface-sunken"
              aria-label="Close"
            >
              <X size={16} />
            </button>
          </header>

          {success ? (
            <div className="flex items-center gap-3 rounded-card border border-pos bg-pos-soft px-4 py-3 text-pos">
              <CheckCircle2 size={18} />
              <span className="text-[13.5px] font-medium">
                Sent. They'll see it in their inbox.
              </span>
            </div>
          ) : (
            <form className="space-y-3" onSubmit={onSubmit}>
              <textarea
                value={message}
                onChange={(e) => setMessage(e.target.value)}
                rows={9}
                className="block w-full resize-y rounded-btn border border-rule-strong bg-surface px-3 py-2.5 text-[13.5px] leading-[1.55] text-ink focus:border-info focus:outline-none focus:ring-2 focus:ring-info/30"
              />
              {error && (
                <div className="rounded-btn border border-neg bg-neg-soft px-3 py-2 text-[13px] text-neg">
                  {error}
                </div>
              )}
              <div className="flex items-center justify-end gap-2">
                <Button
                  type="button"
                  variant="ghost"
                  onClick={onClose}
                  disabled={submitting}
                >
                  Cancel
                </Button>
                <Button type="submit" variant="primary" disabled={submitting}>
                  {submitting ? (
                    <>
                      <Loader2 size={14} className="animate-spin" />
                      Sending…
                    </>
                  ) : (
                    <>
                      <Send size={14} />
                      Send
                    </>
                  )}
                </Button>
              </div>
            </form>
          )}
        </Card>
      </div>
    </div>
  );
}

function Stat({
  label,
  emphasis,
  children,
}: {
  label: string;
  emphasis?: boolean;
  children: React.ReactNode;
}) {
  return (
    <div>
      <Micro className="block">{label}</Micro>
      <div
        className={
          emphasis
            ? "mt-1 font-display text-[22px] font-semibold tabular-nums text-ink"
            : "mt-1 font-display text-[28px] font-semibold tabular-nums text-ink"
        }
      >
        {children}
      </div>
    </div>
  );
}


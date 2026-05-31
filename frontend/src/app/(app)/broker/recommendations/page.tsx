"use client";

import { FormEvent, useState } from "react";
import { Briefcase, CheckCircle2, Info, Loader2, Send, X } from "lucide-react";
import { Topbar } from "@/components/chrome/topbar";
import {
  Body,
  Button,
  Card,
  Caption,
  Chip,
  Eyebrow,
  KpiSnug,
  Micro,
} from "@/components/ui";
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
  const grouped = new Map<string, BookGapRecommendation[]>();
  for (const r of recs) {
    const list = grouped.get(r.client_entity_name) ?? [];
    list.push(r);
    grouped.set(r.client_entity_name, list);
  }

  const totalGaps = recs.length;
  const clientsTouched = grouped.size;
  const totalPotential = recs.reduce(
    (s, r) =>
      s + (r.estimated_premium_range_usd[0] + r.estimated_premium_range_usd[1]) / 2,
    0,
  );

  return (
    <>
      <Topbar
        crumbs={["Broker Portal", "Recommendations"]}
        entity={data.broker_name}
      />
      <div className="flex-1 overflow-y-auto px-9 py-7">
        <div className="grid gap-4">
          {/* Title + KPIs */}
          <header className="flex flex-wrap items-end justify-between gap-6">
            <div>
              <h1 className="mt-1.5 font-display text-[32px] font-semibold leading-tight tracking-tight text-ink">
                Coverage gaps across your book
              </h1>
              <Body className="mt-1.5 max-w-[640px]">
                Industry-by-coverage rule analysis. Each gap is a credible upsell opportunity —
                review the rationale, then send the prompt to the client when you&apos;re ready.
              </Body>
            </div>
            <div className="flex flex-wrap gap-7">
              <KpiSnug label="Gaps identified" value={totalGaps} tone="spot" />
              <KpiSnug label="Clients touched" value={clientsTouched} />
              <KpiSnug
                label="Indicative new premium"
                value={formatCurrency(totalPotential)}
                tone="pos"
              />
            </div>
          </header>

          {/* Info bar */}
          <div className="flex items-center gap-3 rounded-card border border-rule bg-surface-sunken px-4 py-3">
            <Info size={15} className="shrink-0 text-ink-soft" />
            <Caption className="leading-snug">
              Rules: tech firms → cyber + PI + D&amp;O; healthcare → +MedProf; manufacturers → +
              Product Liability + Casualty; pharma → +Clinical Trials. We flag where a client is
              missing one of these by-industry defaults.
            </Caption>
          </div>

          {grouped.size === 0 ? (
            <Card pad="lg" className="text-center">
              <Body className="italic">
                Your book is fully covered relative to peer norms. No gaps to recommend.
              </Body>
            </Card>
          ) : (
            <div className="flex flex-col gap-3.5">
              {[...grouped.entries()]
                .sort((a, b) => a[0].localeCompare(b[0]))
                .map(([entity, items]) => (
                  <ClientGapCard
                    key={entity}
                    entity={entity}
                    items={items}
                    onSent={onSent}
                  />
                ))}
            </div>
          )}
        </div>
      </div>
    </>
  );
}

function ClientGapCard({
  entity,
  items,
  onSent,
}: {
  entity: string;
  items: BookGapRecommendation[];
  onSent: () => void;
}) {
  const industry = items[0]?.industry_label;
  return (
    <Card pad="none" className="overflow-hidden">
      <header className="flex items-center justify-between border-b border-rule bg-surface-elev px-5 py-3">
        <div className="flex items-center gap-3">
          <div className="flex h-8 w-8 items-center justify-center rounded-md border border-rule bg-surface">
            <Briefcase size={15} className="text-ink-soft" />
          </div>
          <div>
            <div className="text-[15px] font-bold text-ink">{entity}</div>
            {industry && <Micro className="block">{industry}</Micro>}
          </div>
        </div>
        <Chip variant="spot" size="sm">
          {items.length} gap{items.length === 1 ? "" : "s"}
        </Chip>
      </header>
      <div>
        {items.map((r, i) => (
          <GapRow key={`${r.client_entity_name}-${r.coverage}-${i}`} rec={r} onSent={onSent} />
        ))}
      </div>
    </Card>
  );
}

function GapRow({
  rec,
  onSent,
}: {
  rec: BookGapRecommendation;
  onSent: () => void;
}) {
  const [open, setOpen] = useState(false);
  return (
    <>
      <div className="grid items-center gap-4 border-t border-rule px-5 py-4 first:border-t-0 md:grid-cols-[1.4fr_1.4fr_1fr_auto]">
        <div>
          <div className="text-[14px] font-bold text-ink">{rec.coverage}</div>
          <Micro className="mt-1 block">Industry default</Micro>
        </div>
        <Caption className="text-[12.5px] leading-snug">{rec.rationale}</Caption>
        <div className="text-right">
          <Micro className="block">Indicative range</Micro>
          <span className="font-bold tabular-nums text-ink">
            {formatCurrency(rec.estimated_premium_range_usd[0])} –{" "}
            {formatCurrency(rec.estimated_premium_range_usd[1])}
          </span>
        </div>
        <Button variant="spot" size="sm" onClick={() => setOpen(true)}>
          <Send size={13} />
          Send to client
        </Button>
      </div>
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
  const [err, setErr] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    if (submitting) return;
    setSubmitting(true);
    setErr(null);
    try {
      await postSendRecommendation(accessToken, {
        client_entity_name: rec.client_entity_name,
        coverage: rec.coverage,
        message,
      });
      setSuccess(true);
      setTimeout(onSent, 1200);
    } catch (e2) {
      setErr(e2 instanceof Error ? e2.message : "Couldn't send.");
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
                Sent. They&apos;ll see it in their inbox.
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
              {err && (
                <div className="rounded-btn border border-neg bg-neg-soft px-3 py-2 text-[13px] text-neg">
                  {err}
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

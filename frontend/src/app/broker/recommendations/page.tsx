"use client";

// v8.1 Phase F — /portal/recommendations (BROKER-only)
//
// Rule-based coverage-gap analysis across the broker's book. Each
// recommendation has a Send-to-client action that posts a new
// message in the client's Communications inbox -- the up-sell path
// the user wanted broker-driven, not auto-shown to the client.

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";

import {
  AlertTriangle,
  Briefcase,
  CheckCircle2,
  Lightbulb,
  Send,
  ShieldCheck,
} from "lucide-react";

import ViewCanvas from "@/components/ViewCanvas";
import VerticalFilter from "@/components/broker/VerticalFilter";
import {
  CardGrid,
  StandardCard,
  SubmissionHeaderCard,
} from "@/components/base/cards";
import {
  InfoPanel,
  KpiTile,
  LabelValueList,
  NoData,
  StatsGrid,
} from "@/components/base/content/primatives";

import { useAuthStore } from "@/store/authStore";
import { useDsiStore } from "@/store/dsiStore";
import {
  fetchBrokerRecommendations,
  postSendRecommendation,
} from "@/lib/portalApi";
import { formatCurrency } from "@/lib/format";
import type {
  BookGapRecommendation,
  BrokerRecommendationsResponse,
} from "@/types/portal";


export default function RecommendationsPage() {
  const router = useRouter();
  const accessToken = useAuthStore((s) => s.accessToken);
  const userRole = useAuthStore((s) => s.user?.role ?? null);
  const setActiveMenu = useDsiStore((s) => s.setActiveMenu);

  const [data, setData] = useState<BrokerRecommendationsResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [active, setActive] = useState<BookGapRecommendation | null>(null);

  useEffect(() => { setActiveMenu("Recommendations"); }, [setActiveMenu]);

  useEffect(() => {
    let cancelled = false;
    async function load() {
      try {
        const resp = await fetchBrokerRecommendations(accessToken);
        if (!cancelled) setData(resp);
      } catch (e) {
        if (!cancelled) setError(e instanceof Error ? e.message : String(e));
      }
    }
    if (accessToken && userRole === "BROKER") load();
    return () => { cancelled = true; };
  }, [accessToken, userRole]);

  if (userRole !== "BROKER") {
    return (
      <ViewCanvas>
        <CardGrid cols="grid-cols-1">
          <StandardCard title="Broker-only" lucideIcon={AlertTriangle}>
            <NoData message="The Recommendations view is for broker users only." />
          </StandardCard>
        </CardGrid>
      </ViewCanvas>
    );
  }
  if (error) {
    return (
      <ViewCanvas>
        <CardGrid cols="grid-cols-1">
          <StandardCard title="Unable to load" lucideIcon={AlertTriangle}>
            <NoData message={error} />
          </StandardCard>
        </CardGrid>
      </ViewCanvas>
    );
  }
  if (!data) {
    return (
      <ViewCanvas>
        <CardGrid cols="grid-cols-1">
          <StandardCard title="Loading" lucideIcon={Lightbulb}>
            <NoData message="Analysing your book…" />
          </StandardCard>
        </CardGrid>
      </ViewCanvas>
    );
  }

  const byEntity = data.recommendations.reduce<Map<string, BookGapRecommendation[]>>((acc, r) => {
    const list = acc.get(r.client_entity_name) ?? [];
    list.push(r);
    acc.set(r.client_entity_name, list);
    return acc;
  }, new Map());

  return (
    <ViewCanvas>
      <CardGrid cols="grid-cols-1" className="gap-4">

        <SubmissionHeaderCard
          decision="approve"
          title="Recommendations"
          subtitle={`${data.broker_name} · coverage-gap analysis across your book`}
          lucideIcon={Lightbulb}
        >
          <StatsGrid
            columns={[
              { label: "Total gaps",      value: data.recommendations.length, align: "center" },
              { label: "Clients touched", value: byEntity.size, align: "center" },
              { label: "Method",          value: "Rule-based", align: "center" },
              { label: "Updated",         value: "Live from book", align: "center" },
            ]}
          />
        </SubmissionHeaderCard>

        <VerticalFilter />

        {data.recommendations.length === 0 ? (
          <StandardCard title="No gaps detected" lucideIcon={CheckCircle2}>
            <NoData message="Every client in your book carries the coverages we'd recommend for their industry. Nothing to push." />
          </StandardCard>
        ) : (
          [...byEntity.entries()].map(([entityName, recs]) => (
            <StandardCard
              key={entityName}
              title={entityName}
              lucideIcon={Briefcase}
              headerRight={
                <span className="text-xs text-generate-text-placeholder">
                  {recs.length} gap{recs.length === 1 ? "" : "s"}
                </span>
              }
            >
              <div className="space-y-3 py-2">
                {recs.map((r) => (
                  <RecommendationRow
                    key={`${entityName}-${r.coverage}`}
                    rec={r}
                    onSend={() => setActive(r)}
                  />
                ))}
              </div>
            </StandardCard>
          ))
        )}

        <InfoPanel label="How this works">
          <p className="text-xs">
            Recommendations come from a simple industry-by-coverage rule set:
            tech companies should typically carry cyber + PI + D&O; healthcare
            providers add medprof; manufacturers add product liability and
            casualty. We flag where a client is missing one of these by-
            industry defaults. Premium ranges are illustrative based on size +
            line; placement context can shift them materially.
          </p>
        </InfoPanel>

      </CardGrid>

      {active && (
        <SendRecommendationModal
          rec={active}
          accessToken={accessToken}
          onClose={() => setActive(null)}
          onSent={() => {
            setActive(null);
            router.push("/communications");
          }}
        />
      )}
    </ViewCanvas>
  );
}


function RecommendationRow({
  rec, onSend,
}: {
  rec: BookGapRecommendation;
  onSend: () => void;
}) {
  const [lo, hi] = rec.estimated_premium_range_usd;
  return (
    <div className="
      border border-generate-text-outline rounded-lg p-3
      grid gap-3"
      style={{ gridTemplateColumns: "1fr 200px 140px" }}
    >
      <div>
        <div className="text-sm font-bold capitalize mb-1">
          {rec.coverage}
        </div>
        <p className="text-xs text-generate-text-placeholder">
          {rec.rationale}
        </p>
      </div>
      <div className="text-sm flex flex-col items-end justify-center">
        <span className="text-xs text-generate-text-placeholder">Estimated range</span>
        <span className="font-bold">
          {formatCurrency(lo, 0)} – {formatCurrency(hi, 0)}
        </span>
      </div>
      <div className="flex items-center justify-end">
        <button
          onClick={onSend}
          className="
            flex items-center gap-2
            bg-generate-dark-background text-generate-text-input
            rounded-md px-3 py-2 text-sm font-bold
            hover:opacity-90"
        >
          <Send className="generate-app-icon" />
          Send to client
        </button>
      </div>
    </div>
  );
}


function SendRecommendationModal({
  rec, accessToken, onClose, onSent,
}: {
  rec: BookGapRecommendation;
  accessToken: string | null;
  onClose: () => void;
  onSent: () => void;
}) {
  const [message, setMessage] = useState<string>(
    `Hi — given your profile, I'd recommend exploring ${rec.coverage} cover. ` +
    `${rec.rationale} Indicative premium range: ${formatCurrency(rec.estimated_premium_range_usd[0], 0)}` +
    ` – ${formatCurrency(rec.estimated_premium_range_usd[1], 0)}. Let me know if you'd like to discuss.`
  );
  const [submitting, setSubmitting] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setSubmitting(true); setErr(null);
    try {
      await postSendRecommendation(accessToken, {
        client_entity_name: rec.client_entity_name,
        coverage: rec.coverage,
        message,
      });
      onSent();
    } catch (e) {
      setErr(e instanceof Error ? e.message : String(e));
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div
      onClick={onClose}
      className="fixed inset-0 z-1000 bg-black/40 flex items-center justify-center p-8"
    >
      <div
        onClick={(e) => e.stopPropagation()}
        className="
          bg-generate-light-background
          border-3 border-generate-text-outline
          rounded-lg p-6
          max-w-2xl w-full
          shadow-lg"
      >
        <h2 className="font-inter text-xl mb-4">
          Send {rec.coverage} recommendation to {rec.client_entity_name}
        </h2>
        <form onSubmit={onSubmit} className="space-y-3">
          <textarea
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            rows={5}
            required
            className="
              w-full text-sm
              bg-generate-light-input
              border border-generate-text-outline
              rounded-md p-2"
          />
          {err && <p className="text-xs text-generate-text-bad">{err}</p>}
          <div className="flex justify-end gap-3">
            <button
              type="button"
              onClick={onClose}
              className="
                border border-generate-text-outline
                rounded-md px-4 py-2 text-sm
                hover:bg-generate-light-input"
            >
              Cancel
            </button>
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
              {submitting ? "Sending…" : "Send"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

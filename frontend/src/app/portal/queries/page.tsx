"use client";

// v8 Phase 8 — /portal/queries (BROKER-only)
//
// Inbox of open underwriter queries across the broker's book. Each
// entry links to /portal/submissions/{code} where the reply form lives.

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import {
  AlertTriangle,
  ChevronRight,
  Inbox,
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
import { fetchBrokerQueries } from "@/lib/portalApi";
import { formatNumber } from "@/lib/format";
import type { BrokerQueriesResponse, OpenQueryEntry } from "@/types/portal";


export default function BrokerQueriesPage() {
  const router = useRouter();
  const accessToken = useAuthStore((s) => s.accessToken);
  const userRole = useAuthStore((s) => s.user?.role ?? null);
  const setActiveMenu = useDsiStore((s) => s.setActiveMenu);

  const [data, setData] = useState<BrokerQueriesResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setActiveMenu("Open Queries");
  }, [setActiveMenu]);

  useEffect(() => {
    let cancelled = false;
    async function load() {
      try {
        const resp = await fetchBrokerQueries(accessToken);
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
          <StandardCard title="Broker-only page" lucideIcon={AlertTriangle}>
            <p className="text-sm">
              This page is restricted to broker users.
            </p>
          </StandardCard>
        </CardGrid>
      </ViewCanvas>
    );
  }

  if (error) {
    return (
      <ViewCanvas>
        <CardGrid cols="grid-cols-1">
          <StandardCard title="Unable to load queries" lucideIcon={AlertTriangle}>
            <p className="text-sm text-generate-text-bad">{error}</p>
          </StandardCard>
        </CardGrid>
      </ViewCanvas>
    );
  }
  if (!data) {
    return (
      <ViewCanvas>
        <CardGrid cols="grid-cols-1">
          <StandardCard title="Loading" lucideIcon={Inbox}>
            <p className="text-sm">Fetching queries…</p>
          </StandardCard>
        </CardGrid>
      </ViewCanvas>
    );
  }

  return (
    <ViewCanvas>
      <CardGrid cols="grid-cols-1" className="gap-4">

        <SubmissionHeaderCard
          decision={data.open_queries.length > 0 ? "refer" : "approve"}
          title={`${data.broker.name} — Open Queries`}
          subtitle="Underwriter requests awaiting your response"
          lucideIcon={Inbox}
        >
          <div className="grid grid-cols-2 md:grid-cols-3 gap-6 py-2">
            <KpiTile
              label="Open queries"
              value={data.open_queries.length}
              variant="emphasis"
              lucideIcon={Inbox}
            />
            <KpiTile
              label="Status"
              value={data.open_queries.length > 0 ? "Action required" : "All clear"}
              lucideIcon={UserStar}
            />
            <KpiTile
              label="Oldest"
              value={
                data.open_queries.length > 0 && data.open_queries[0].opened_at
                  ? formatRelative(data.open_queries[0].opened_at)
                  : "—"
              }
            />
          </div>
        </SubmissionHeaderCard>

        <StandardCard
          title={`Queue (${data.open_queries.length})`}
          lucideIcon={UserStar}
        >
          {data.open_queries.length === 0 ? (
            <p className="text-sm">
              No open queries. Your underwriters are not waiting on anything.
            </p>
          ) : (
            <div className="space-y-3 py-2">
              {data.open_queries.map((q) => (
                <QueryCard
                  key={q.referral_code}
                  query={q}
                  onClick={() => router.push(`/portal/submissions/${q.submission_code}`)}
                />
              ))}
            </div>
          )}
        </StandardCard>

      </CardGrid>
    </ViewCanvas>
  );
}


function QueryCard({
  query, onClick,
}: {
  query: OpenQueryEntry;
  onClick: () => void;
}) {
  return (
    <button
      onClick={onClick}
      className="
        w-full text-left
        border border-generate-text-outline rounded-lg
        p-4 hover:border-generate-text-input
        group transition-colors"
    >
      <div className="flex justify-between items-baseline mb-2">
        <span className="text-sm font-bold group-hover:text-generate-text-input">
          {query.entity_name}
        </span>
        <div className="flex items-center gap-2">
          <span className="text-xs text-generate-text-placeholder capitalize">
            {query.coverage}
          </span>
          <ChevronRight className="generate-app-icon group-hover:text-generate-text-input" />
        </div>
      </div>
      {query.request_signal_evidence && (
        <div className="text-xs text-generate-text-placeholder mb-2">
          Evidence requested:{" "}
          <code className="text-generate-text-comment">{query.request_signal_evidence}</code>
        </div>
      )}
      {query.open_query_body && (
        <p className="text-sm italic">"{query.open_query_body}"</p>
      )}
      {query.opened_at && (
        <div className="text-xs text-generate-text-placeholder mt-2">
          Opened {new Date(query.opened_at).toLocaleString()}
        </div>
      )}
    </button>
  );
}


function formatRelative(iso: string): string {
  try {
    const d = new Date(iso);
    const diffMs = Date.now() - d.getTime();
    const diffHrs = diffMs / (1000 * 60 * 60);
    if (diffHrs < 24) return `${formatNumber(diffHrs, 0)}h ago`;
    const diffDays = diffHrs / 24;
    return `${formatNumber(diffDays, 0)}d ago`;
  } catch {
    return "—";
  }
}

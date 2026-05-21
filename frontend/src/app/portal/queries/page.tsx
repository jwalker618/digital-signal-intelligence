"use client";

// v8 Phase 8 — /portal/queries -- broker inbox of open underwriter queries.
//
// BROKER-only. Each entry links to the submission detail page where
// the reply form lives.

import { useEffect, useState } from "react";
import Link from "next/link";

import { useAuthStore } from "@/store/authStore";
import { fetchBrokerQueries } from "@/lib/portalApi";
import type { BrokerQueriesResponse } from "@/types/portal";

export default function BrokerQueriesPage() {
  const accessToken = useAuthStore((s) => s.accessToken);
  const userRole = useAuthStore((s) => s.user?.role ?? null);

  const [data, setData] = useState<BrokerQueriesResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

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
      <Shell>
        <p className="opacity-70">This page is for brokers only.</p>
      </Shell>
    );
  }
  if (error) return <Shell><p className="text-red-600">{error}</p></Shell>;
  if (!data) return <Shell><p>Loading…</p></Shell>;

  return (
    <Shell>
      <div className="mb-6">
        <Link href="/portal" className="text-sm underline opacity-70">
          ← Overview
        </Link>
      </div>
      <h1 className="text-2xl font-semibold mb-1">{data.broker.name} — Open Queries</h1>
      <p className="text-sm opacity-70 mb-6">
        Underwriter requests awaiting your response.
      </p>
      {data.open_queries.length === 0 ? (
        <p className="opacity-70">No open queries.</p>
      ) : (
        <div className="space-y-3">
          {data.open_queries.map((q) => (
            <Link
              key={q.referral_code}
              href={`/portal/submissions/${q.submission_code}`}
              className="block border rounded-lg p-4 hover:bg-black/5"
            >
              <div className="flex justify-between items-baseline">
                <span className="font-medium">{q.entity_name}</span>
                <span className="text-xs opacity-70 capitalize">{q.coverage}</span>
              </div>
              {q.request_signal_evidence && (
                <div className="text-xs mt-1 opacity-70">
                  Evidence requested: <code>{q.request_signal_evidence}</code>
                </div>
              )}
              {q.open_query_body && (
                <p className="text-sm mt-2 italic">"{q.open_query_body}"</p>
              )}
              {q.opened_at && (
                <div className="text-xs mt-2 opacity-60">
                  Opened {new Date(q.opened_at).toLocaleString()}
                </div>
              )}
            </Link>
          ))}
        </div>
      )}
    </Shell>
  );
}

function Shell({ children }: { children: React.ReactNode }) {
  return <div className="p-8 max-w-5xl mx-auto">{children}</div>;
}

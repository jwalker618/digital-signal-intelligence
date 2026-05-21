"use client";

// v8 Phase 8 — /portal -- role-aware overview.
//
// BROKER: book of clients with score / tier / percentile / open queries
// CLIENT: own coverages with the same summary numbers, linking to
//         /portal/submissions/{code} for detail

import { useEffect, useState } from "react";
import Link from "next/link";

import { useAuthStore } from "@/store/authStore";
import { fetchOverview } from "@/lib/portalApi";
import type {
  BrokerOverviewResponse,
  ClientOverviewResponse,
  OverviewResponse,
} from "@/types/portal";

export default function PortalOverviewPage() {
  const accessToken = useAuthStore((s) => s.accessToken);
  const userRole = useAuthStore((s) => s.user?.role ?? null);

  const [data, setData] = useState<OverviewResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    async function load() {
      setLoading(true);
      try {
        const resp = await fetchOverview(accessToken);
        if (!cancelled) setData(resp);
      } catch (e) {
        if (!cancelled) setError(e instanceof Error ? e.message : String(e));
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    if (accessToken) load();
    return () => { cancelled = true; };
  }, [accessToken]);

  if (loading) return <PortalShell><p>Loading…</p></PortalShell>;
  if (error) return <PortalShell><p className="text-red-600">{error}</p></PortalShell>;
  if (!data) return <PortalShell><p>No data available.</p></PortalShell>;

  if (data.role === "BROKER") return <BrokerOverview data={data} />;
  return <ClientOverview data={data} />;
}

function PortalShell({ children }: { children: React.ReactNode }) {
  return (
    <div className="p-8 max-w-6xl mx-auto">
      <header className="mb-6">
        <h1 className="text-3xl font-semibold mb-1">Client Portal</h1>
        <p className="text-sm opacity-70">
          Signal-driven insights for brokers and insureds.
        </p>
      </header>
      {children}
    </div>
  );
}

// ---------------------------------------------------------------------------
// BROKER view
// ---------------------------------------------------------------------------

function BrokerOverview({ data }: { data: BrokerOverviewResponse }) {
  return (
    <PortalShell>
      <div className="mb-6 flex items-baseline gap-4">
        <span className="text-lg font-medium">{data.broker.name}</span>
        <span className="text-sm opacity-70">book of clients</span>
        {data.open_queries_count > 0 && (
          <Link
            href="/portal/queries"
            className="ml-auto text-sm underline"
          >
            {data.open_queries_count} open quer{data.open_queries_count === 1 ? "y" : "ies"} →
          </Link>
        )}
      </div>
      {data.clients.length === 0 ? (
        <p className="opacity-70">No clients in your book yet.</p>
      ) : (
        <table className="w-full text-sm border-collapse">
          <thead>
            <tr className="text-left border-b">
              <th className="py-2 pr-4">Client</th>
              <th className="py-2 pr-4">Coverage</th>
              <th className="py-2 pr-4">Score</th>
              <th className="py-2 pr-4">Tier</th>
              <th className="py-2 pr-4">Percentile</th>
              <th className="py-2 pr-4">Premium</th>
              <th className="py-2 pr-4">Status</th>
            </tr>
          </thead>
          <tbody>
            {data.clients.map((c) => (
              <tr key={c.submission_code} className="border-b hover:bg-black/5">
                <td className="py-2 pr-4">
                  <Link
                    href={`/portal/submissions/${c.submission_code}`}
                    className="underline"
                  >
                    {c.entity_name}
                  </Link>
                </td>
                <td className="py-2 pr-4 capitalize">{c.coverage}</td>
                <td className="py-2 pr-4">{c.composite_score?.toFixed(0) ?? "—"}</td>
                <td className="py-2 pr-4">{c.tier ?? "—"}</td>
                <td className="py-2 pr-4">
                  {c.peer_percentile_rank != null ? `${c.peer_percentile_rank.toFixed(0)}th` : "—"}
                </td>
                <td className="py-2 pr-4">
                  {c.recommended_premium != null ? `$${c.recommended_premium.toLocaleString()}` : "—"}
                </td>
                <td className="py-2 pr-4">
                  {c.referral_state === "awaiting_broker" ? (
                    <span className="font-medium text-amber-700">
                      Awaiting reply
                    </span>
                  ) : (
                    c.status
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </PortalShell>
  );
}

// ---------------------------------------------------------------------------
// CLIENT view
// ---------------------------------------------------------------------------

function ClientOverview({ data }: { data: ClientOverviewResponse }) {
  return (
    <PortalShell>
      <div className="mb-6">
        <div className="text-lg font-medium">{data.entity_name}</div>
        {data.broker && (
          <div className="text-sm opacity-70">
            Placed by {data.broker.name}
          </div>
        )}
      </div>
      {data.active_coverages.length === 0 ? (
        <p className="opacity-70">No active coverages yet.</p>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2">
          {data.active_coverages.map((c) => (
            <Link
              key={c.submission_code}
              href={`/portal/submissions/${c.submission_code}`}
              className="block border rounded-lg p-4 hover:bg-black/5"
            >
              <div className="text-sm opacity-70 capitalize">{c.coverage}</div>
              <div className="text-3xl font-semibold mt-1">
                {c.composite_score?.toFixed(0) ?? "—"}
              </div>
              <div className="text-sm opacity-70 mt-1">
                Tier {c.tier ?? "—"} · {
                  c.peer_percentile_rank != null
                    ? `${c.peer_percentile_rank.toFixed(0)}th percentile`
                    : "—"
                }
              </div>
              <div className="text-sm mt-2">
                Premium: {
                  c.recommended_premium != null
                    ? `$${c.recommended_premium.toLocaleString()}`
                    : "—"
                }
              </div>
              {c.referral_state === "awaiting_broker" && (
                <div className="text-xs mt-2 text-amber-700">
                  Broker reply pending
                </div>
              )}
            </Link>
          ))}
        </div>
      )}
    </PortalShell>
  );
}

"use client";

// /broker — Book of Clients (broker portal home).
//
// Extracted from the old /portal role-router in the v8.2 portal
// architecture cleanup. The broker overview is now a first-class
// page at its own persona URL; SessionGuard routes BROKER users
// here on login.

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";

import {
  AlertTriangle,
  Briefcase,
  Gauge,
  Layers,
  UserStar,
} from "lucide-react";

import ViewCanvas from "@/components/ViewCanvas";
import VerticalFilter from "@/components/portal/VerticalFilter";
import {
  CardGrid,
  StandardCard,
  SubmissionHeaderCard,
} from "@/components/base/cards";
import {
  InfoPanel,
  StatsGrid,
} from "@/components/base/content/primatives";
import PendingQueryRow, { formatCoverageLabel } from "@/components/shared/PendingQueryRow";

import { useAuthStore } from "@/store/authStore";
import { useDsiStore } from "@/store/dsiStore";
import {
  fetchCommunications,
  fetchOverview,
} from "@/lib/portalApi";
import { formatCurrency, formatNumber } from "@/lib/format";
import type {
  BrokerOverviewResponse,
  ClientBookEntry,
  CommunicationItem,
  OverviewResponse,
} from "@/types/portal";


export default function BrokerOverviewPage() {
  const router = useRouter();
  const accessToken = useAuthStore((s) => s.accessToken);
  const userRole = useAuthStore((s) => s.user?.role ?? null);
  const setActiveMenu = useDsiStore((s) => s.setActiveMenu);

  const [data, setData] = useState<BrokerOverviewResponse | null>(null);
  const [comms, setComms] = useState<CommunicationItem[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => { setActiveMenu("Book of Clients"); }, [setActiveMenu]);

  useEffect(() => {
    let cancelled = false;
    async function load() {
      try {
        const [resp, communicationsResp] = await Promise.all([
          fetchOverview(accessToken),
          fetchCommunications(accessToken, true),
        ]);
        if (cancelled) return;
        if (resp.role !== "BROKER") {
          setError("The Book of Clients view is for broker users only.");
          return;
        }
        setData(resp as BrokerOverviewResponse);
        setComms(communicationsResp.items);
      } catch (e) {
        if (!cancelled) setError(e instanceof Error ? e.message : String(e));
      }
    }
    if (accessToken && userRole === "BROKER") load();
    return () => { cancelled = true; };
  }, [accessToken, userRole]);

  if (userRole !== "BROKER") return <BrokerOnly />;
  if (error) return <ErrShell msg={error} />;
  if (!data) return <LoadShell />;

  const clients = data.clients;
  const scoredClients = clients.filter((c) => c.composite_score != null);
  const avgScore = scoredClients.length
    ? scoredClients.reduce((a, c) => a + (c.composite_score ?? 0), 0) / scoredClients.length
    : 0;
  const totalPremium = clients.reduce((a, c) => a + (c.recommended_premium ?? 0), 0);
  const uniqueEntities = new Set(clients.map((c) => c.entity_name)).size;
  const awaiting = comms.filter((c) => c.awaiting_party === "broker").length;

  return (
    <ViewCanvas>
      <CardGrid cols="grid-cols-1" className="gap-4">

        <SubmissionHeaderCard
          decision={awaiting > 0 ? "refer" : "approve"}
          title={data.broker.name}
          subtitle={`Book of ${uniqueEntities} client${uniqueEntities === 1 ? "" : "s"} · ${clients.length} polic${clients.length === 1 ? "y" : "ies"}`}
          lucideIcon={Briefcase}
          headerRight={
            awaiting > 0 ? (
              <span className="text-xs text-generate-text-maybe font-bold">
                {awaiting} awaiting your reply
              </span>
            ) : (
              <span className="text-xs text-generate-text-good font-bold">All clear</span>
            )
          }
        >
          <StatsGrid
            columns={[
              { label: "Clients",       value: uniqueEntities, align: "center" },
              { label: "Policies",      value: clients.length, align: "center" },
              { label: "Avg score",     value: formatNumber(avgScore, 0), align: "center" },
              { label: "Aggregate premium", value: formatCurrency(totalPremium, 0), align: "center" },
              { label: "Open queries",  value: comms.length, align: "center" },
            ]}
          />
        </SubmissionHeaderCard>

        <VerticalFilter />

        <StandardCard
          title={`Book of Clients (${clients.length} policies)`}
          lucideIcon={Briefcase}
        >
          <BrokerBookTable clients={clients} router={router} />
        </StandardCard>

        <CardGrid cols="grid-cols-1 lg:grid-cols-2" className="gap-4">
          <StandardCard title="Tier mix" lucideIcon={Layers}>
            <TierMix clients={clients} />
          </StandardCard>

          {comms.length > 0 && (
            <StandardCard title="Open queries snapshot" lucideIcon={UserStar}>
              <div className="space-y-2 py-2">
                {comms.slice(0, 4).map((c) => (
                  <PendingQueryRow
                    key={c.referral_code}
                    query={c}
                    onClick={() => router.push(`/communications/${c.referral_code}`)}
                  />
                ))}
              </div>
            </StandardCard>
          )}

          {comms.length === 0 && (
            <StandardCard title="Communications status" lucideIcon={UserStar}>
              <InfoPanel label="Status">
                <p className="text-sm text-generate-text-good">
                  No open queries across your book. Underwriters are not
                  currently waiting on you for anything.
                </p>
              </InfoPanel>
            </StandardCard>
          )}
        </CardGrid>

      </CardGrid>
    </ViewCanvas>
  );
}


function BrokerBookTable({
  clients, router,
}: {
  clients: ClientBookEntry[];
  router: ReturnType<typeof useRouter>;
}) {
  return (
    <div className="grid"
      style={{ gridTemplateColumns: "2fr 1fr 80px 80px 100px 1fr 1fr" }}
    >
      {["Client", "Coverage", "Score", "Tier", "Percentile", "Premium", "Status"].map((h, i) => (
        <div key={i} className="text-xs text-generate-text-placeholder border-b border-generate-text-outline pb-1.5 pt-1.5">
          {h}
        </div>
      ))}
      {clients.map((c) => (
        <div
          key={c.submission_code}
          onClick={() => router.push(`/submissions/${c.submission_code}`)}
          className="contents cursor-pointer group"
        >
          <div className="text-sm py-2 group-hover:text-generate-text-input group-hover:font-bold">
            {c.entity_name}
          </div>
          <div className="text-sm py-2 capitalize group-hover:text-generate-text-input">
            {formatCoverageLabel(c.coverage)}
          </div>
          <div className="text-sm py-2 font-bold group-hover:text-generate-text-input">
            {c.composite_score != null ? formatNumber(c.composite_score, 0) : "—"}
          </div>
          <div className="text-sm py-2 group-hover:text-generate-text-input">
            {c.tier ?? "—"}
          </div>
          <div className="text-sm py-2 group-hover:text-generate-text-input">
            {c.peer_percentile_rank != null
              ? `${formatNumber(c.peer_percentile_rank, 0)}th`
              : "—"}
          </div>
          <div className="text-sm py-2 group-hover:text-generate-text-input">
            {c.recommended_premium != null
              ? formatCurrency(c.recommended_premium, 0)
              : "—"}
          </div>
          <div className="text-sm py-2">
            {c.referral_state === "awaiting_broker" ? (
              <span className="text-generate-text-maybe font-bold">Awaiting reply</span>
            ) : c.referral_state === "pending" ? (
              <span className="text-generate-text-comment font-bold">In review</span>
            ) : (
              <span className="text-generate-text-good">{c.status}</span>
            )}
          </div>
        </div>
      ))}
    </div>
  );
}


function TierMix({ clients }: { clients: ClientBookEntry[] }) {
  const counts: Record<number, number> = {};
  clients.forEach((c) => {
    if (c.tier != null) counts[c.tier] = (counts[c.tier] ?? 0) + 1;
  });
  const total = clients.length;
  const tierTone: Record<number, string> = {
    1: "var(--color-generate-text-good)",
    2: "var(--color-generate-text-good)",
    3: "var(--color-generate-text-comment)",
    4: "var(--color-generate-text-maybe)",
    5: "var(--color-generate-text-bad)",
  };
  return (
    <div className="space-y-2">
      {[1, 2, 3, 4, 5].map((t) => {
        const n = counts[t] ?? 0;
        const pct = total ? (n / total) * 100 : 0;
        return (
          <div key={t} className="grid items-center gap-2" style={{ gridTemplateColumns: "60px 1fr 80px" }}>
            <span className="text-xs">Tier {t}</span>
            <div className="h-2 bg-generate-light-background rounded-full overflow-hidden">
              <div
                className="h-full rounded-full"
                style={{ width: `${pct}%`, backgroundColor: tierTone[t] }}
              />
            </div>
            <span className="text-xs text-right">
              {n} <span className="text-generate-text-placeholder">({formatNumber(pct, 0)}%)</span>
            </span>
          </div>
        );
      })}
    </div>
  );
}


function LoadShell() {
  return (
    <ViewCanvas>
      <CardGrid cols="grid-cols-1">
        <StandardCard title="Loading" lucideIcon={Gauge}>
          <p className="text-sm">Fetching your book…</p>
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

function BrokerOnly() {
  return (
    <ViewCanvas>
      <CardGrid cols="grid-cols-1">
        <StandardCard title="Broker-only" lucideIcon={AlertTriangle}>
          <p className="text-sm">The Book of Clients view is for broker users only.</p>
        </StandardCard>
      </CardGrid>
    </ViewCanvas>
  );
}

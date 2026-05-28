"use client";

// v8.2 Client Health — /broker/client-health
//
// Beyond what clients tell you: engagement score, opportunity / risk
// flags, renewal calendar, quiet-client alerts.

import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import {
  AlertTriangle,
  ArrowRight,
  Calendar,
  CircleDot,
  HeartPulse,
  TrendingDown,
  TrendingUp,
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
  NoData,
  ScoreBar,
  StatsGrid,
} from "@/components/base/content/primatives";
import VerticalFilter, { useVerticalFilter } from "@/components/portal/VerticalFilter";

import { useAuthStore } from "@/store/authStore";
import { useDsiStore } from "@/store/dsiStore";
import { fetchClientHealth } from "@/lib/portalApi";
import { formatCurrency, formatNumber } from "@/lib/format";
import type { ClientHealthEntry, ClientHealthResponse } from "@/types/portal";


export default function ClientHealthPage() {
  const router = useRouter();
  const accessToken = useAuthStore((s) => s.accessToken);
  const userRole = useAuthStore((s) => s.user?.role ?? null);
  const setActiveMenu = useDsiStore((s) => s.setActiveMenu);
  const filter = useVerticalFilter();

  const [data, setData] = useState<ClientHealthResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => { setActiveMenu("Client Health"); }, [setActiveMenu]);

  useEffect(() => {
    let cancelled = false;
    async function load() {
      try {
        const resp = await fetchClientHealth(accessToken);
        if (!cancelled) setData(resp);
      } catch (e) {
        if (!cancelled) setError(e instanceof Error ? e.message : String(e));
      }
    }
    if (accessToken && userRole === "BROKER") load();
    return () => { cancelled = true; };
  }, [accessToken, userRole]);

  const filtered = useMemo(() => {
    if (!data) return [];
    return data.clients.filter((c) => filter.matches(c.vertical_slug));
  }, [data, filter]);

  if (userRole !== "BROKER") return <BrokerOnly />;
  if (error) return <ErrShell msg={error} />;
  if (!data) return <LoadShell />;

  const strong = filtered.filter((c) => c.engagement_score >= 80).length;
  const quiet = filtered.filter((c) => c.engagement_score < 40).length;
  const opportunities = filtered.reduce((a, c) => a + c.opportunity_flags.length, 0);
  const risks = filtered.reduce((a, c) => a + c.risk_flags.length, 0);
  const renewalSoon = filtered.filter((c) => (c.next_renewal_in_days ?? 999) <= 60).length;

  return (
    <ViewCanvas>
      <CardGrid cols="grid-cols-1" className="gap-4">

        <SubmissionHeaderCard
          decision="approve"
          title="Client Health"
          subtitle="Engagement, growth signals, and forward-looking opportunity / risk flags"
          lucideIcon={HeartPulse}
        >
          <StatsGrid
            columns={[
              { label: "Clients", value: filtered.length, align: "center" },
              { label: "Strong engagement", value: strong, align: "center" },
              { label: "Quiet / dormant", value: quiet, align: "center" },
              { label: "Open opportunities", value: opportunities, align: "center" },
              { label: "Risk flags", value: risks, align: "center" },
              { label: "Renewal ≤60d", value: renewalSoon, align: "center" },
            ]}
          />
        </SubmissionHeaderCard>

        <VerticalFilter />

        {quiet > 0 && (
          <StandardCard title={`Quiet client alerts (${quiet})`} lucideIcon={AlertTriangle}>
            <p className="text-xs text-generate-text-placeholder mb-3">
              These clients are showing dormant engagement signals. Worth a
              proactive touchpoint before their next renewal cycle.
            </p>
            <div className="space-y-2">
              {filtered.filter((c) => c.engagement_score < 40).map((c) => (
                <QuietClientRow
                  key={c.entity_name}
                  client={c}
                  onClick={() => router.push("/broker/communications")}
                />
              ))}
            </div>
          </StandardCard>
        )}

        <StandardCard
          title={`Client roster (${filtered.length})`}
          lucideIcon={UserStar}
          headerRight={
            <span className="text-xs text-generate-text-placeholder">
              Sorted by engagement score
            </span>
          }
        >
          <div className="space-y-3 py-2">
            {filtered.map((c) => (
              <ClientHealthCard
                key={c.entity_name}
                client={c}
                onOpen={() => router.push("/broker/communications")}
              />
            ))}
          </div>
        </StandardCard>

        <InfoPanel label="How engagement is measured" aside="v8.2 — derived from comms history">
          <p className="text-xs">
            Engagement score combines open-query count, average reply time,
            recency of last message, and whether the client has acted on
            broker signals recently. It's a leading indicator -- a client
            scoring "Quiet" or "Dormant" today is at elevated risk of
            non-renewal in the next 6 months unless re-engaged.
          </p>
        </InfoPanel>

      </CardGrid>
    </ViewCanvas>
  );
}


function ClientHealthCard({
  client, onOpen,
}: {
  client: ClientHealthEntry;
  onOpen: () => void;
}) {
  return (
    <div
      onClick={onOpen}
      className="
        border border-generate-text-outline rounded-lg p-4
        cursor-pointer group hover:border-generate-text-input
        transition-colors
      "
    >
      <div className="grid gap-4" style={{ gridTemplateColumns: "1.5fr 1fr 1.5fr" }}>
        <div>
          <div className="flex items-baseline gap-3 mb-1">
            <span className="text-sm font-bold group-hover:text-generate-text-input">
              {client.entity_name}
            </span>
            {client.vertical_name && (
              <span className="text-xs text-generate-text-placeholder">
                {client.vertical_name}
              </span>
            )}
          </div>
          <div className="text-xs text-generate-text-placeholder">
            {client.policy_count} polic{client.policy_count === 1 ? "y" : "ies"}
            {" · "}
            {formatCurrency(client.total_premium_usd, 0)} premium
          </div>

          {client.next_renewal_in_days != null && (
            <div className="text-xs mt-2 flex items-center gap-1">
              <Calendar className="generate-app-icon" />
              <span className={
                client.next_renewal_in_days <= 60
                  ? "text-generate-text-maybe font-bold"
                  : "text-generate-text-placeholder"
              }>
                Renewal in {client.next_renewal_in_days}d
              </span>
            </div>
          )}
        </div>

        <div>
          <div className="text-xs text-generate-text-placeholder mb-1">
            Engagement
          </div>
          <div className="text-2xl font-bold">
            {client.engagement_score}
            <span className="text-xs ml-2 text-generate-text-placeholder">
              {client.engagement_label}
            </span>
          </div>
          <div className="mt-2">
            <ScoreBar
              value={client.engagement_score}
              min={0}
              max={100}
              decimals={0}
              hideValue
              thresholds={[
                { at: 20, color: "var(--color-generate-text-bad)" },
                { at: 40, color: "var(--color-generate-text-maybe)" },
                { at: 60, color: "var(--color-generate-text-comment)" },
                { at: 80, color: "var(--color-generate-text-good)" },
                { at: Infinity, color: "var(--color-generate-text-good)" },
              ]}
            />
          </div>
          <div className="text-xs mt-1 text-generate-text-placeholder space-y-0.5">
            {client.avg_response_hours != null && (
              <div>Avg response {formatNumber(client.avg_response_hours, 0)}h</div>
            )}
            {client.months_since_last_message != null && (
              <div>Last contact {formatNumber(client.months_since_last_message, 1)}mo ago</div>
            )}
            <div>{client.open_query_count} open quer{client.open_query_count === 1 ? "y" : "ies"}</div>
          </div>
        </div>

        <div className="space-y-2">
          {client.opportunity_flags.length > 0 && (
            <div>
              <div className="text-xs text-generate-text-good font-bold mb-1 flex items-center gap-1">
                <TrendingUp className="generate-app-icon" /> Opportunities
              </div>
              <ul className="text-xs space-y-0.5">
                {client.opportunity_flags.map((f) => (
                  <li key={f}>· {f}</li>
                ))}
              </ul>
            </div>
          )}

          {client.risk_flags.length > 0 && (
            <div>
              <div className="text-xs text-generate-text-bad font-bold mb-1 flex items-center gap-1">
                <TrendingDown className="generate-app-icon" /> Risks
              </div>
              <ul className="text-xs space-y-0.5">
                {client.risk_flags.map((f) => (
                  <li key={f}>· {f}</li>
                ))}
              </ul>
            </div>
          )}

          {client.opportunity_flags.length === 0 && client.risk_flags.length === 0 && (
            <div className="text-xs text-generate-text-placeholder italic">
              No flags — clean status.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}


function QuietClientRow({
  client, onClick,
}: {
  client: ClientHealthEntry;
  onClick: () => void;
}) {
  return (
    <button
      onClick={onClick}
      className="
        w-full text-left
        border border-generate-text-maybe/30 bg-generate-text-maybe/5
        rounded-lg p-3
        hover:border-generate-text-input
        flex items-center justify-between gap-3
      "
    >
      <div>
        <div className="text-sm font-bold">{client.entity_name}</div>
        <div className="text-xs text-generate-text-placeholder">
          {client.engagement_label} · score {client.engagement_score}
          {client.months_since_last_message != null && (
            <span> · last contact {formatNumber(client.months_since_last_message, 1)}mo ago</span>
          )}
        </div>
      </div>
      <ArrowRight className="generate-app-icon" />
    </button>
  );
}


function LoadShell() {
  return (
    <ViewCanvas>
      <CardGrid cols="grid-cols-1">
        <StandardCard title="Loading" lucideIcon={HeartPulse}>
          <NoData message="Loading client health…" />
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
          <NoData message={msg} />
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
          <NoData message="Client Health is for broker users only." />
        </StandardCard>
      </CardGrid>
    </ViewCanvas>
  );
}

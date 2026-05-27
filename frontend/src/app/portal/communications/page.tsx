"use client";

// v8 Phase 8 polish — /portal/communications
//
// Role-aware inbox. Both BROKER and CLIENT see the threads they have
// visibility into:
//   BROKER: queries across their book of clients
//   CLIENT: queries on their own submissions

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";

import {
  AlertTriangle,
  ArrowRight,
  CircleDot,
  ListChecks,
  MessageSquare,
  MessagesSquare,
} from "lucide-react";

import ViewCanvas from "@/components/ViewCanvas";
import VerticalFilter from "@/components/broker/VerticalFilter";
import {
  CardGrid,
  StandardCard,
  SubmissionHeaderCard,
} from "@/components/base/cards";
import { KpiTile } from "@/components/base/content/primatives";

import { useAuthStore } from "@/store/authStore";
import { useDsiStore } from "@/store/dsiStore";
import { fetchCommunications } from "@/lib/portalApi";
import type {
  CommunicationItem,
  CommunicationsListResponse,
} from "@/types/portal";


export default function CommunicationsListPage() {
  const router = useRouter();
  const accessToken = useAuthStore((s) => s.accessToken);
  const setActiveMenu = useDsiStore((s) => s.setActiveMenu);

  const [data, setData] = useState<CommunicationsListResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [showOpenOnly, setShowOpenOnly] = useState(true);

  useEffect(() => { setActiveMenu("Communications"); }, [setActiveMenu]);

  useEffect(() => {
    let cancelled = false;
    async function load() {
      try {
        const resp = await fetchCommunications(accessToken, false);
        if (!cancelled) setData(resp);
      } catch (e) {
        if (!cancelled) setError(e instanceof Error ? e.message : String(e));
      }
    }
    if (accessToken) load();
    return () => { cancelled = true; };
  }, [accessToken]);

  if (error) return <ErrShell msg={error} />;
  if (!data) return <LoadShell />;

  const items = showOpenOnly ? data.items.filter((i) => i.is_open) : data.items;

  const awaitingMe = items.filter((i) =>
    data.role === "BROKER"
      ? i.awaiting_party === "broker"
      : i.awaiting_party === "client",
  ).length;

  return (
    <ViewCanvas>
      <CardGrid cols="grid-cols-1" className="gap-4">

        <SubmissionHeaderCard
          decision={data.open_count > 0 ? "refer" : "approve"}
          title={
            data.role === "BROKER"
              ? "Communications — Book"
              : "Communications — Your Policies"
          }
          subtitle={
            data.role === "BROKER"
              ? "Carrier queries and broker replies across your book of clients"
              : "Queries from your carrier and broker concerning your policies"
          }
          lucideIcon={MessagesSquare}
        >
          <div className="grid grid-cols-2 md:grid-cols-4 gap-6 py-2">
            <KpiTile
              label="Open threads"
              value={data.open_count}
              variant="emphasis"
              lucideIcon={CircleDot}
            />
            <KpiTile
              label={data.role === "BROKER" ? "Awaiting your reply" : "Awaiting your input"}
              value={awaitingMe}
              lucideIcon={ListChecks}
              subtext={awaitingMe > 0 ? "Action required" : "All clear"}
            />
            <KpiTile
              label="Total threads"
              value={data.items.length}
              lucideIcon={MessageSquare}
            />
            <KpiTile
              label="Filter"
              value={
                <button
                  onClick={() => setShowOpenOnly((v) => !v)}
                  className="text-sm underline hover:text-generate-text-input"
                >
                  {showOpenOnly ? "Showing open only" : "Showing all"}
                </button>
              }
            />
          </div>
        </SubmissionHeaderCard>

        <VerticalFilter />

        <StandardCard
          title={`${showOpenOnly ? "Open" : "All"} threads (${items.length})`}
          lucideIcon={MessageSquare}
        >
          {items.length === 0 ? (
            <p className="text-sm">
              {showOpenOnly
                ? "No open threads. All conversations are resolved."
                : "No communications yet."}
            </p>
          ) : (
            <div className="space-y-2 py-2">
              {items.map((item) => (
                <CommunicationRow
                  key={item.referral_code}
                  item={item}
                  role={data.role}
                  onClick={() => router.push(`/portal/communications/${item.referral_code}`)}
                />
              ))}
            </div>
          )}
        </StandardCard>

      </CardGrid>
    </ViewCanvas>
  );
}


function CommunicationRow({
  item, role, onClick,
}: {
  item: CommunicationItem;
  role: string;
  onClick: () => void;
}) {
  const awaitingMe =
    (role === "BROKER" && item.awaiting_party === "broker") ||
    (role === "CLIENT" && item.awaiting_party === "client");

  const statusTone = awaitingMe
    ? "text-generate-text-maybe"
    : item.is_open
    ? "text-generate-text-comment"
    : "text-generate-text-good";

  return (
    <button
      onClick={onClick}
      className="
        w-full text-left
        border border-generate-text-outline rounded-lg
        p-4 hover:border-generate-text-input
        group transition-colors"
    >
      <div className="grid gap-4" style={{ gridTemplateColumns: "1fr 90px" }}>
        <div>
          <div className="flex items-baseline gap-3 mb-1">
            <span className="text-sm font-bold group-hover:text-generate-text-input">
              {item.entity_name}
            </span>
            <span className="text-xs text-generate-text-placeholder">
              {item.policy_label ?? item.coverage}
            </span>
          </div>
          {item.last_message_excerpt && (
            <div className="text-xs italic line-clamp-2">
              "{item.last_message_excerpt}"
            </div>
          )}
          {item.request_signal_evidence && (
            <div className="text-xs mt-1">
              <span className="text-generate-text-placeholder">Evidence requested: </span>
              <code className="text-generate-text-comment">{item.request_signal_evidence}</code>
            </div>
          )}
        </div>
        <div className="flex flex-col items-end justify-between">
          <span className={`text-xs font-bold ${statusTone}`}>
            {awaitingMe ? "AWAITING YOU" : item.status.replace(/_/g, " ").toUpperCase()}
          </span>
          <div className="flex items-center gap-1 text-xs text-generate-text-placeholder group-hover:text-generate-text-input">
            <span>{item.last_message_at ? formatRelative(item.last_message_at) : ""}</span>
            <ArrowRight className="generate-app-icon" />
          </div>
        </div>
      </div>
    </button>
  );
}


function formatRelative(iso: string): string {
  try {
    const d = new Date(iso);
    const diffMs = Date.now() - d.getTime();
    const diffHrs = diffMs / (1000 * 60 * 60);
    if (diffHrs < 1) return "just now";
    if (diffHrs < 24) return `${Math.floor(diffHrs)}h ago`;
    const diffDays = diffHrs / 24;
    if (diffDays < 30) return `${Math.floor(diffDays)}d ago`;
    return d.toLocaleDateString();
  } catch {
    return "—";
  }
}


function LoadShell() {
  return (
    <ViewCanvas>
      <CardGrid cols="grid-cols-1">
        <StandardCard title="Loading" lucideIcon={MessagesSquare}>
          <p className="text-sm">Loading communications…</p>
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

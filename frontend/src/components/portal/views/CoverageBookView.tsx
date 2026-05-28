"use client";

// v8 Phase 8 polish — /coverages
//
// Role-aware policy roster, aggregated by coverage line. Each coverage
// group shows aggregate KPIs (policy count, premium total, average
// score) over the underlying policies, then a row per policy that
// links to the policy detail view.

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";

import {
  ArrowRight,
  ChartPie,
  Layers,
  ShieldCheck,
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
  ExpandableGroupTable,
  KpiTile,
  type ExpandableGroup,
} from "@/components/base/content/primatives";

import { useAuthStore } from "@/store/authStore";
import { useDsiStore } from "@/store/dsiStore";
import { fetchOverview } from "@/lib/portalApi";
import { formatCurrency, formatNumber } from "@/lib/format";
import { homePathForRole } from "@/lib/portalPaths";
import { peerStandingPositive, tierStatus } from "@/lib/portalTone";
import type {
  BrokerOverviewResponse,
  ClientBookEntry,
  ClientCoverageEntry,
  ClientOverviewResponse,
  OverviewResponse,
} from "@/types/portal";
import { PageLoading, PageError } from "@/components/base/pageStates";


type AnyPolicy = ClientBookEntry | ClientCoverageEntry;


export default function CoverageBookView() {
  const router = useRouter();
  const accessToken = useAuthStore((s) => s.accessToken);
  const userRole = useAuthStore((s) => s.user?.role ?? null);
  const setActiveMenu = useDsiStore((s) => s.setActiveMenu);

  const personaHome = homePathForRole(userRole);

  const [data, setData] = useState<OverviewResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => { setActiveMenu("Coverages"); }, [setActiveMenu]);

  useEffect(() => {
    let cancelled = false;
    async function load() {
      try {
        const resp = await fetchOverview(accessToken);
        if (!cancelled) setData(resp);
      } catch (e) {
        if (!cancelled) setError(e instanceof Error ? e.message : String(e));
      }
    }
    if (accessToken) load();
    return () => { cancelled = true; };
  }, [accessToken]);

  if (error) return <PageError message={error} />;
  if (!data) return <PageLoading icon={ShieldCheck} message="Loading coverages…" />;

  const allPolicies: AnyPolicy[] =
    data.role === "BROKER"
      ? data.clients
      : data.active_coverages;

  const groupedByCoverage = groupByCoverage(allPolicies);

  const totalPolicies = allPolicies.length;
  const totalPremium = allPolicies.reduce(
    (a, p) => a + (p.recommended_premium ?? 0), 0,
  );
  const scoredPolicies = allPolicies.filter((p) => p.composite_score != null);
  const avgScore = scoredPolicies.length
    ? scoredPolicies.reduce((a, p) => a + (p.composite_score ?? 0), 0) / scoredPolicies.length
    : 0;
  const referredCount = allPolicies.filter(
    (p) => p.referral_state === "awaiting_broker" || p.referral_state === "pending",
  ).length;

  return (
    <ViewCanvas>
      <CardGrid cols="grid-cols-1" className="gap-4">

        <SubmissionHeaderCard
          decision={referredCount > 0 ? "refer" : "approve"}
          title={data.role === "BROKER" ? "Coverages — Book" : "Coverages"}
          subtitle={
            data.role === "BROKER"
              ? "All policies across your book, grouped by line"
              : "All your active policies, grouped by line"
          }
          lucideIcon={ShieldCheck}
        >
          <div className="grid grid-cols-2 md:grid-cols-4 gap-6 py-2">
            <KpiTile
              label="Total policies"
              value={totalPolicies}
              lucideIcon={Layers}
              variant="emphasis"
            />
            <KpiTile
              label="Coverage lines"
              value={groupedByCoverage.length}
              lucideIcon={ShieldCheck}
            />
            <KpiTile
              label="Aggregate premium"
              value={formatCurrency(totalPremium, 0)}
              lucideIcon={ChartPie}
            />
            <KpiTile
              label={data.role === "BROKER" ? "Awaiting reply" : "Pending queries"}
              value={referredCount}
              lucideIcon={UserStar}
              subtext={referredCount > 0 ? "Action required" : "All clear"}
            />
          </div>
        </SubmissionHeaderCard>

        <VerticalFilter />

        {groupedByCoverage.map((group) => (
          <StandardCard
            key={group.coverage}
            title={`${formatCoverageLabel(group.coverage)} — ${group.policies.length} polic${group.policies.length === 1 ? "y" : "ies"}`}
            lucideIcon={ShieldCheck}
            headerRight={
              <span className="text-xs text-generate-text-placeholder">
                Aggregate {formatCurrency(group.premiumTotal, 0)}
                {" · "}
                Avg score {formatNumber(group.avgScore, 0)}
              </span>
            }
          >
            <PolicyTable
              policies={group.policies}
              showEntity={data.role === "BROKER"}
              onRowClick={(code) => router.push(`${personaHome}/submissions/${code}`)}
            />
          </StandardCard>
        ))}

      </CardGrid>
    </ViewCanvas>
  );
}


// ----------------------------------------------------------------------------
// Helpers
// ----------------------------------------------------------------------------

interface CoverageGroup {
  coverage: string;
  policies: AnyPolicy[];
  premiumTotal: number;
  avgScore: number;
  referredCount: number;
}

function groupByCoverage(policies: AnyPolicy[]): CoverageGroup[] {
  const map = new Map<string, AnyPolicy[]>();
  policies.forEach((p) => {
    const list = map.get(p.coverage) ?? [];
    list.push(p);
    map.set(p.coverage, list);
  });
  const out: CoverageGroup[] = [];
  map.forEach((list, coverage) => {
    const premiumTotal = list.reduce((a, p) => a + (p.recommended_premium ?? 0), 0);
    const scored = list.filter((p) => p.composite_score != null);
    const avgScore = scored.length
      ? scored.reduce((a, p) => a + (p.composite_score ?? 0), 0) / scored.length
      : 0;
    const referredCount = list.filter(
      (p) => p.referral_state === "awaiting_broker" || p.referral_state === "pending",
    ).length;
    out.push({ coverage, policies: list, premiumTotal, avgScore, referredCount });
  });
  // Sort by premium total desc (largest line first)
  out.sort((a, b) => b.premiumTotal - a.premiumTotal);
  return out;
}

function formatCoverageLabel(c: string): string {
  return c
    .split("_")
    .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
    .join(" ");
}


// ----------------------------------------------------------------------------
// Policy table
// ----------------------------------------------------------------------------

function PolicyTable({
  policies, showEntity, onRowClick,
}: {
  policies: AnyPolicy[];
  showEntity: boolean;
  onRowClick: (submissionCode: string) => void;
}) {
  const cols = showEntity
    ? "2fr 80px 80px 100px 1fr 1fr 40px"
    : "80px 80px 100px 1fr 1fr 40px";
  // Broker columns show the carrier-internal tier number (brokers are
  // multi-carrier and need the raw rank). Client columns show the
  // translated status label only.
  const headers = showEntity
    ? ["Client", "Score", "Tier", "Percentile", "Premium", "Status", ""]
    : ["Score", "Status", "Peer standing", "Premium", "State", ""];

  return (
    <div className="grid" style={{ gridTemplateColumns: cols }}>
      {headers.map((h, i) => (
        <div
          key={i}
          className="text-xs text-generate-text-placeholder border-b border-generate-text-outline pb-1.5 pt-1.5"
        >
          {h}
        </div>
      ))}
      {policies.map((p) => (
        <div
          key={p.submission_code}
          onClick={() => onRowClick(p.submission_code)}
          className="contents cursor-pointer group"
        >
          {showEntity && (
            <div className="text-sm py-2 group-hover:text-generate-text-input group-hover:font-bold">
              {(p as ClientBookEntry).entity_name}
            </div>
          )}
          <div className="text-sm py-2 font-bold group-hover:text-generate-text-input">
            {p.composite_score != null ? formatNumber(p.composite_score, 0) : "—"}
          </div>
          <div className="text-sm py-2 group-hover:text-generate-text-input">
            {showEntity ? (p.tier ?? "—") : tierStatus(p.tier).label}
          </div>
          <div className="text-sm py-2 group-hover:text-generate-text-input">
            {showEntity
              ? (p.peer_percentile_rank != null ? `${formatNumber(p.peer_percentile_rank, 0)}th` : "—")
              : peerStandingPositive(p.peer_percentile_rank)}
          </div>
          <div className="text-sm py-2 group-hover:text-generate-text-input">
            {p.recommended_premium != null
              ? formatCurrency(p.recommended_premium, 0)
              : "—"}
          </div>
          <div className="text-sm py-2">
            {p.referral_state === "awaiting_broker" ? (
              <span className="text-generate-text-maybe font-bold">Awaiting reply</span>
            ) : p.referral_state === "pending" ? (
              <span className="text-generate-text-comment">In review</span>
            ) : (
              <span className="text-generate-text-good">{p.status ?? "Active"}</span>
            )}
          </div>
          <div className="text-sm py-2 flex justify-end">
            <ArrowRight className="generate-app-icon group-hover:text-generate-text-input" />
          </div>
        </div>
      ))}
    </div>
  );
}
"use client";

import Link from "next/link";
import { Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { Leaf } from "lucide-react";
import { Topbar } from "@/components/chrome/topbar";
import {
  Body,
  Card,
  Caption,
  Chip,
  Eyebrow,
  Micro,
  NumDisplay,
} from "@/components/ui";
import { PageError, PageLoading, RoleGate } from "@/components/base/pageStates";
import { useRoleScopedFetch } from "@/lib/useRoleScopedFetch";
import { fetchOverview, fetchPlacementStrategy } from "@/lib/portalApi";
import { useAuthStore } from "@/store/authStore";
import { formatCurrency, formatText } from "@/lib/format";
import { cn } from "@/lib/utils";
import type {
  CarrierMatch,
  ClientBookEntry,
  OverviewResponse,
  PlacementStrategyResponse,
} from "@/types/portal";

export default function BrokerPlacementPage() {
  return (
    <Suspense fallback={<PageLoading />}>
      <PlacementInner />
    </Suspense>
  );
}

function PlacementInner() {
  const accessToken = useAuthStore((s) => s.accessToken);
  const user = useAuthStore((s) => s.user);
  const enabled = !!accessToken && user?.role === "BROKER";
  const params = useSearchParams();
  const explicitCode = params.get("code");

  const overview = useRoleScopedFetch<OverviewResponse>({
    fetcher: () => fetchOverview(accessToken),
    enabled,
    deps: [accessToken],
  });

  const inFlight =
    overview.data?.role === "BROKER"
      ? overview.data.clients.filter(
          (c) =>
            /review|awaiting/i.test(c.status ?? "") ||
            /awaiting/i.test(c.referral_state ?? ""),
        )
      : [];

  const code =
    explicitCode ??
    (overview.data?.role === "BROKER"
      ? (inFlight[0]?.submission_code ?? overview.data.clients[0]?.submission_code)
      : undefined);

  const placement = useRoleScopedFetch<PlacementStrategyResponse>({
    fetcher: () => fetchPlacementStrategy(accessToken, code!),
    enabled: enabled && !!code,
    deps: [accessToken, code],
  });

  if (!user) return <PageLoading message="Signing in…" />;
  if (user.role && user.role !== "BROKER") return <RoleGate expected="broker" />;
  if (overview.loading) return <PageLoading />;
  if (overview.error) return <PageError message={overview.error} />;
  if (!overview.data || overview.data.role !== "BROKER")
    return <RoleGate expected="broker" />;
  if (!code) {
    return (
      <>
        <Topbar crumbs={["Broker Portal", "Placement Strategy"]} />
        <div className="flex flex-1 items-start justify-center px-9 py-12">
          <Card pad="lg" className="max-w-md">
            <Eyebrow>No submission selected</Eyebrow>
            <Body className="mt-2">
              Open one from{" "}
              <Link href="/broker" className="font-semibold text-info hover:underline">
                the book
              </Link>{" "}
              to see carrier-fit strategy.
            </Body>
          </Card>
        </div>
      </>
    );
  }
  if (placement.loading) return <PageLoading />;
  if (placement.error) return <PageError message={placement.error} />;
  if (!placement.data) return <PageLoading />;

  return (
    <PlacementBody
      data={placement.data}
      inFlight={inFlight}
      activeCode={code}
    />
  );
}

function PlacementBody({
  data,
  inFlight,
  activeCode,
}: {
  data: PlacementStrategyResponse;
  inFlight: ClientBookEntry[];
  activeCode: string;
}) {
  const ranked = [...data.carrier_matches].sort(
    (a, b) => b.suitability_score - a.suitability_score,
  );
  const lead = ranked[0];
  const others = ranked.slice(1);
  const selected = inFlight.find((c) => c.submission_code === activeCode);

  return (
    <>
      <Topbar
        crumbs={[
          "Broker Portal",
          "Placement Strategy",
          `${data.entity_name} · ${data.coverage}`,
        ]}
      />
      <div className="flex-1 overflow-y-auto px-9 py-7">
        <div className="grid gap-4">
          <header className="flex flex-wrap items-end justify-between gap-6">
            <div>
              <Eyebrow>Placement strategy</Eyebrow>
              <h1 className="mt-1.5 font-display text-[32px] font-semibold leading-tight tracking-tight text-ink">
                Ranked carrier matches for in-flight risks
              </h1>
              <Body className="mt-1.5">
                For each policy, score every carrier in the universe by appetite, ESG fit,
                pricing position, and historical win rate.
              </Body>
            </div>
            <Chip variant="info" size="md">
              Composite scoring v8.2
            </Chip>
          </header>

          <div className="grid gap-4 md:grid-cols-[280px_1fr]">
            {/* Policy picker */}
            <Card pad="md" className="flex flex-col gap-2.5">
              <Eyebrow>In-flight ({inFlight.length})</Eyebrow>
              {inFlight.length === 0 && (
                <Caption className="italic">No in-flight submissions.</Caption>
              )}
              {inFlight.map((p) => (
                <PolicyPickerRow
                  key={p.submission_code}
                  entry={p}
                  active={p.submission_code === activeCode}
                />
              ))}
              <Caption className="mt-2 border-t border-rule pt-2.5">
                Click a policy to recompute ranked matches.
              </Caption>
            </Card>

            {/* Strategy detail */}
            <div className="flex flex-col gap-3.5">
              {/* Active submission */}
              <Card variant="info" pad="lg">
                <div className="flex items-start justify-between gap-4">
                  <div>
                    <Eyebrow className="text-info-deep dark:text-info">
                      Active submission
                    </Eyebrow>
                    <h2 className="mt-1.5 font-display text-[22px] font-semibold leading-snug text-ink">
                      {data.entity_name} — {data.coverage}
                    </h2>
                    {selected && (
                      <Caption className="mt-1 block">
                        {selected.recommended_premium != null
                          ? `Current quote ${formatCurrency(selected.recommended_premium)}`
                          : "No current quote"}
                      </Caption>
                    )}
                  </div>
                </div>
                {data.placement_note && (
                  <Body className="mt-3 text-ink">{data.placement_note}</Body>
                )}
              </Card>

              {/* Lead recommendation */}
              {lead && <CarrierMatchCard match={lead} lead />}

              {/* Other matches */}
              {others.length > 0 && (
                <div className="flex flex-col gap-2.5">
                  <Eyebrow>Other matches</Eyebrow>
                  {others.map((m) => (
                    <CarrierMatchCard key={m.slug} match={m} />
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </>
  );
}

function PolicyPickerRow({
  entry,
  active,
}: {
  entry: ClientBookEntry;
  active: boolean;
}) {
  const router = useRouter();
  return (
    <button
      type="button"
      onClick={() => router.push(`/broker/placement?code=${entry.submission_code}`)}
      className={cn(
        "rounded-card border px-3 py-2.5 text-left transition",
        active
          ? "border-spot bg-spot-soft"
          : "border-rule bg-surface-elev hover:bg-surface-sunken",
      )}
    >
      <div className="text-[13px] font-semibold text-ink">{entry.entity_name}</div>
      <Micro className="mt-0.5 block">
        {entry.coverage}
        {entry.recommended_premium != null && (
          <> · {formatCurrency(entry.recommended_premium)} current</>
        )}
      </Micro>
      {entry.status && (
        <Chip variant={active ? "spot" : "mute"} size="sm" className="mt-1.5">
          {formatText(entry.status, "capitalize")}
        </Chip>
      )}
    </button>
  );
}

function CarrierMatchCard({
  match,
  lead,
}: {
  match: CarrierMatch;
  lead?: boolean;
}) {
  const stanceColor =
    match.appetite_stance === "leaning_in"
      ? "text-pos"
      : match.appetite_stance === "neutral"
        ? "text-info"
        : match.appetite_stance === "selective"
          ? "text-warn"
          : "text-neg";
  const stanceBorder =
    match.appetite_stance === "leaning_in"
      ? "border-pos"
      : match.appetite_stance === "neutral"
        ? "border-info"
        : match.appetite_stance === "selective"
          ? "border-warn"
          : "border-neg";
  const esgColor =
    match.esg_stance === "leader"
      ? "text-pos"
      : match.esg_stance === "progressive"
        ? "text-info"
        : match.esg_stance === "restrictive"
          ? "text-warn"
          : "text-ink-soft";
  return (
    <Card
      pad={lead ? "lg" : "md"}
      className={cn(lead ? "border-l-4 border-l-info" : undefined)}
    >
      <div className="grid items-center gap-4 md:grid-cols-[2fr_110px_160px]">
        <div>
          <div className="mb-1.5 flex flex-wrap items-baseline gap-2.5">
            {lead && (
              <Chip variant="info" size="sm">
                LEAD
              </Chip>
            )}
            <span className={cn("font-bold text-ink", lead ? "text-[18px]" : "text-[15px]")}>
              {match.name}
            </span>
            <span
              className={cn(
                "rounded-chip border bg-surface px-2 py-0.5 text-[11px] font-semibold capitalize",
                stanceColor,
                stanceBorder,
              )}
            >
              {match.appetite_stance.replace("_", " ")}
            </span>
            <span
              className={cn(
                "flex items-center gap-1 text-[11px] font-semibold capitalize",
                esgColor,
              )}
            >
              <Leaf size={11} /> ESG {match.esg_stance}
            </span>
          </div>
          <Caption className={cn("leading-snug", lead ? "text-[13.5px]" : "text-[12.5px]")}>
            {match.rationale}
          </Caption>
        </div>
        <div>
          <Micro className="block">Suitability</Micro>
          <NumDisplay
            size={lead ? "lg" : "md"}
            className="mt-0.5 block text-info"
          >
            {match.suitability_score.toFixed(0)}
          </NumDisplay>
          <div className="mt-1 h-1 overflow-hidden rounded-full bg-rule">
            <div
              className="h-full bg-info"
              style={{
                width: `${Math.max(0, Math.min(100, match.suitability_score))}%`,
              }}
            />
          </div>
        </div>
        <div className="text-right">
          <Micro className="block">Predicted premium</Micro>
          <div
            className={cn(
              "mt-0.5 font-bold tabular-nums",
              lead ? "text-[15px]" : "text-[13px]",
            )}
          >
            {formatCurrency(match.predicted_premium_low)} –{" "}
            {formatCurrency(match.predicted_premium_high)}
          </div>
          <Micro className="mt-1 block">
            Cmsn {match.typical_commission_pct.toFixed(1)}% · Win{" "}
            {match.win_rate_pct.toFixed(0)}%
          </Micro>
        </div>
      </div>
    </Card>
  );
}

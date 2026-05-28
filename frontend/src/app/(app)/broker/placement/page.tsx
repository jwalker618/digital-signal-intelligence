"use client";

import Link from "next/link";
import { Suspense } from "react";
import { useSearchParams } from "next/navigation";
import { Building2, Leaf, Target, TrendingDown } from "lucide-react";
import { Topbar } from "@/components/chrome/topbar";
import { Card } from "@/components/ui/card";
import { Chip } from "@/components/ui/chip";
import { Eyebrow, NumDisplay, Body, Micro } from "@/components/ui/typography";
import { ScoreBar } from "@/components/ui/score-bar";
import { PageError, PageLoading, RoleGate } from "@/components/base/pageStates";
import { useRoleScopedFetch } from "@/lib/useRoleScopedFetch";
import { fetchOverview, fetchPlacementStrategy } from "@/lib/portalApi";
import { useAuthStore } from "@/store/authStore";
import { formatCurrency, formatPercent, formatText } from "@/lib/format";
import type {
  AppetiteStance,
  CarrierMatch,
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

  const code =
    explicitCode ??
    (overview.data?.role === "BROKER"
      ? overview.data.clients[0]?.submission_code
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
              <Link
                href="/broker"
                className="font-semibold text-info hover:underline"
              >
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
      allSubmissions={overview.data.clients.map((c) => ({
        code: c.submission_code,
        label: `${c.entity_name} · ${c.coverage}`,
      }))}
      activeCode={code}
    />
  );
}

function PlacementBody({
  data,
  allSubmissions,
  activeCode,
}: {
  data: PlacementStrategyResponse;
  allSubmissions: { code: string; label: string }[];
  activeCode: string;
}) {
  const ranked = [...data.carrier_matches].sort(
    (a, b) => b.suitability_score - a.suitability_score,
  );

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
        <div className="mx-auto grid max-w-[1400px] gap-6">
          <header className="flex items-end justify-between gap-6">
            <div>
              <Eyebrow>Placement</Eyebrow>
              <h1 className="mt-1 font-display text-[32px] font-semibold leading-none tracking-tight text-ink">
                {data.entity_name} · {data.coverage}
              </h1>
              <Body className="mt-2">
                Carrier fit ranked by suitability — appetite, pricing position,
                and your placement history.
              </Body>
            </div>
            <SubmissionPicker
              all={allSubmissions}
              activeCode={activeCode}
              baseHref="/broker/placement"
            />
          </header>

          {data.placement_note && (
            <Card variant="info" pad="lg">
              <Eyebrow className="text-info-deep dark:text-info">
                Placement note
              </Eyebrow>
              <Body className="mt-2 text-ink">{data.placement_note}</Body>
            </Card>
          )}

          <section className="space-y-3">
            <Eyebrow>Ranked carriers ({ranked.length})</Eyebrow>
            {ranked.map((c) => (
              <CarrierMatchCard key={c.slug} match={c} />
            ))}
          </section>
        </div>
      </div>
    </>
  );
}

function CarrierMatchCard({ match }: { match: CarrierMatch }) {
  const apTone =
    match.appetite_stance === "leaning_in"
      ? "pos"
      : match.appetite_stance === "leaning_out"
        ? "neg"
        : match.appetite_stance === "selective"
          ? "warn"
          : "mute";

  return (
    <Card pad="md" className="grid gap-4 md:grid-cols-[2fr_1fr_1fr_1fr]">
      <div>
        <div className="flex items-center gap-2">
          <Building2 size={15} className="text-ink-mute" />
          <h3 className="text-[16px] font-semibold text-ink">{match.name}</h3>
        </div>
        <div className="mt-2 flex items-baseline gap-3">
          <span className="font-display text-[22px] font-semibold tabular-nums text-info">
            {match.suitability_score.toFixed(0)}
          </span>
          <Micro>suitability</Micro>
        </div>
        <ScoreBar
          value={match.suitability_score}
          max={100}
          className="mt-2 max-w-[280px]"
          showValue={false}
          thresholds={[
            { at: 40, tone: "neg" },
            { at: 60, tone: "warn" },
            { at: 80, tone: "info" },
            { at: 100, tone: "pos" },
          ]}
        />
        <Body className="mt-3 text-[12.5px]">{match.rationale}</Body>
      </div>

      <div>
        <Micro>Predicted premium</Micro>
        <p className="mt-1 text-[14px] font-semibold tabular-nums text-ink">
          {formatCurrency(match.predicted_premium_low)} –{" "}
          {formatCurrency(match.predicted_premium_high)}
        </p>
        <Micro className="mt-2 block">Commission</Micro>
        <p className="text-[14px] font-semibold tabular-nums text-ink">
          {formatPercent(match.typical_commission_pct / 100, 1)}
        </p>
      </div>

      <div className="space-y-1.5">
        <Micro>Appetite</Micro>
        <Chip variant={apTone} size="sm">
          {formatText(match.appetite_stance.replace("_", " "), "capitalize")}
        </Chip>
        <Micro className="mt-2 block">Pricing</Micro>
        <Chip
          variant={
            match.pricing_position === "light"
              ? "pos"
              : match.pricing_position === "tight"
                ? "neg"
                : "info"
          }
          size="sm"
        >
          {match.pricing_position === "light" ? (
            <TrendingDown size={11} />
          ) : null}
          {formatText(match.pricing_position, "capitalize")}
        </Chip>
      </div>

      <div>
        <Micro>Your win rate</Micro>
        <p className="text-[16px] font-semibold tabular-nums text-ink">
          {match.win_rate_pct.toFixed(0)}%
        </p>
        <Micro className="mt-2 block">ESG</Micro>
        <span className="flex items-center gap-1 text-[13px] font-semibold text-ink">
          <Leaf
            size={11}
            className={
              match.esg_stance === "leader"
                ? "text-pos"
                : match.esg_stance === "progressive"
                  ? "text-info"
                  : match.esg_stance === "restrictive"
                    ? "text-neg"
                    : "text-ink-mute"
            }
          />
          {formatText(match.esg_stance, "capitalize")}
        </span>
      </div>
    </Card>
  );
}

function SubmissionPicker({
  all,
  activeCode,
  baseHref,
}: {
  all: { code: string; label: string }[];
  activeCode: string;
  baseHref: string;
}) {
  if (all.length <= 1) return null;
  return (
    <label className="flex items-center gap-2 text-[12.5px]">
      <span className="text-ink-mute">Submission:</span>
      <select
        value={activeCode}
        onChange={(e) => {
          window.location.href = `${baseHref}?code=${e.target.value}`;
        }}
        className="rounded-btn border border-rule-strong bg-surface px-3 py-1.5 text-[13px] font-medium text-ink focus:border-info focus:outline-none focus:ring-2 focus:ring-info/30"
      >
        {all.map((c) => (
          <option key={c.code} value={c.code}>
            {c.label}
          </option>
        ))}
      </select>
    </label>
  );
}

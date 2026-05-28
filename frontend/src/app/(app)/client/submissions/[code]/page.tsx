"use client";

import { use } from "react";
import Link from "next/link";
import { ArrowLeft, MessageSquare, TrendingUp, AlertCircle } from "lucide-react";
import { Topbar } from "@/components/chrome/topbar";
import { Card } from "@/components/ui/card";
import { Chip } from "@/components/ui/chip";
import { Button } from "@/components/ui/button";
import { Eyebrow, NumDisplay, Body, Micro } from "@/components/ui/typography";
import { LabelRow } from "@/components/ui/label-row";
import { ScoreBar } from "@/components/ui/score-bar";
import { PageError, PageLoading, RoleGate } from "@/components/base/pageStates";
import { useRoleScopedFetch } from "@/lib/useRoleScopedFetch";
import { fetchSubmissionDetail, fetchSubmissionScore } from "@/lib/portalApi";
import { useAuthStore } from "@/store/authStore";
import { formatCurrency, formatDate, formatText } from "@/lib/format";
import { tierStatus } from "@/lib/portalTone";
import { portalToneToTone } from "@/lib/design-tokens";
import type {
  SubmissionDetailResponse,
  ScoreResponse,
  QuoteEvolutionEntry,
} from "@/types/portal";

export default function CoverageDetailPage(props: {
  params: Promise<{ code: string }>;
}) {
  const { code } = use(props.params);
  const accessToken = useAuthStore((s) => s.accessToken);
  const user = useAuthStore((s) => s.user);
  const enabled = !!accessToken && user?.role === "CLIENT";

  const detail = useRoleScopedFetch<SubmissionDetailResponse>({
    fetcher: () => fetchSubmissionDetail(accessToken, code),
    enabled,
    deps: [accessToken, code],
  });

  const score = useRoleScopedFetch<ScoreResponse>({
    fetcher: () => fetchSubmissionScore(accessToken, code),
    enabled,
    deps: [accessToken, code],
  });

  if (!user) return <PageLoading message="Signing in…" />;
  if (user.role && user.role !== "CLIENT") return <RoleGate expected="client" />;
  if (detail.loading || score.loading) return <PageLoading />;
  if (detail.error) return <PageError message={detail.error} />;
  if (!detail.data) return <PageLoading />;

  return (
    <DetailBody detail={detail.data} score={score.data} scoreError={score.error} />
  );
}

function DetailBody({
  detail,
  score,
  scoreError,
}: {
  detail: SubmissionDetailResponse;
  score: ScoreResponse | null;
  scoreError: string | null;
}) {
  const latestQuote = detail.quotes[0];
  const tone = tierStatus(latestQuote?.tier ?? score?.tier ?? null);
  const compositeScore =
    score?.composite_score ?? latestQuote?.composite_score ?? null;
  const finalPremium =
    score?.final_premium ?? latestQuote?.final_premium ?? null;

  return (
    <>
      <Topbar
        crumbs={["Client Portal", "Coverages", detail.coverage]}
        entity={detail.entity_name}
      />
      <div className="flex-1 overflow-y-auto px-9 py-7">
        <div className="mx-auto grid max-w-[1280px] gap-6">
          <Link
            href="/client/coverages"
            className="inline-flex items-center gap-1.5 text-[13px] font-medium text-info hover:underline"
          >
            <ArrowLeft size={14} /> All coverages
          </Link>

          {/* Header */}
          <Card pad="lg" className="space-y-4">
            <div className="flex items-start justify-between gap-6">
              <div>
                <Eyebrow>Coverage</Eyebrow>
                <h1 className="mt-1 font-display text-[32px] font-semibold leading-tight tracking-tight text-ink">
                  {detail.coverage}
                </h1>
                <Micro className="mt-1 block font-mono">
                  {detail.submission_code} · placed{" "}
                  {formatDate(detail.created_at)}
                </Micro>
              </div>
              <div className="flex flex-col items-end gap-2">
                <Chip variant={portalToneToTone(tone.tone)}>
                  {tone.label}
                </Chip>
                {detail.referral && /awaiting/i.test(detail.referral.status) && (
                  <Chip variant="spot" size="sm">
                    <AlertCircle size={11} />
                    {formatText(detail.referral.status, "capitalize")}
                  </Chip>
                )}
              </div>
            </div>

            {detail.referral && (
              <Body className="text-ink-soft">
                Referral {detail.referral.referral_code}
                {detail.referral.awaiting_party &&
                  ` — awaiting ${detail.referral.awaiting_party}`}
                .{" "}
                <Link
                  href={`/client/communications/${detail.referral.referral_code}`}
                  className="font-semibold text-info hover:underline"
                >
                  Open thread →
                </Link>
              </Body>
            )}
          </Card>

          {/* Hero metrics */}
          {scoreError ? (
            <Card variant="warn" pad="lg">
              <Eyebrow>Score unavailable</Eyebrow>
              <Body className="mt-1">{scoreError}</Body>
            </Card>
          ) : score ? (
            <ScoreHeroCard score={score} compositeScore={compositeScore} finalPremium={finalPremium} />
          ) : null}

          {/* Premium breakdown */}
          {score?.impact_breakdown && (
            <ImpactBreakdownCard data={score.impact_breakdown} />
          )}

          {/* Quote history */}
          {detail.quotes.length > 0 && (
            <QuoteHistoryCard quotes={detail.quotes} />
          )}

          {/* Drill-down links — these surfaces ship next */}
          <DrillDownGrid code={detail.submission_code} />
        </div>
      </div>
    </>
  );
}

function ScoreHeroCard({
  score,
  compositeScore,
  finalPremium,
}: {
  score: ScoreResponse;
  compositeScore: number | null;
  finalPremium: number | null;
}) {
  return (
    <Card variant="info" pad="lg" className="space-y-5">
      <Eyebrow>This coverage</Eyebrow>
      <div className="grid grid-cols-1 gap-6 md:grid-cols-3">
        <Metric label="Composite score">
          {compositeScore != null ? (
            <>
              <NumDisplay size="xl">{compositeScore.toFixed(0)}</NumDisplay>
              <ScoreBar
                value={compositeScore}
                max={1000}
                className="mt-3"
                showValue={false}
                thresholds={[
                  { at: 400, tone: "neg" },
                  { at: 650, tone: "warn" },
                  { at: 800, tone: "info" },
                  { at: 1000, tone: "pos" },
                ]}
              />
            </>
          ) : (
            <Body className="italic">Pending</Body>
          )}
        </Metric>
        <Metric label="Final premium">
          {finalPremium != null ? (
            <NumDisplay size="lg">{formatCurrency(finalPremium)}</NumDisplay>
          ) : (
            <Body className="italic">Pending</Body>
          )}
          {score.base_premium != null && finalPremium != null && (
            <Micro className="mt-2 block">
              Base {formatCurrency(score.base_premium)} ·{" "}
              {Math.round(
                ((finalPremium - score.base_premium) / score.base_premium) * 100,
              )}
              % adjustment
            </Micro>
          )}
        </Metric>
        <Metric label="Exposure">
          {score.exposure_value != null ? (
            <NumDisplay size="lg">
              {formatCurrency(score.exposure_value)}
            </NumDisplay>
          ) : (
            <Body className="italic">—</Body>
          )}
          {score.exposure_band_label && (
            <Micro className="mt-2 block">{score.exposure_band_label}</Micro>
          )}
        </Metric>
      </div>
      {(score.loss_propensity_band || score.loss_trend_direction) && (
        <div className="flex flex-wrap items-center gap-2 border-t border-info/30 pt-4">
          <Eyebrow className="mr-2">Loss outlook</Eyebrow>
          {score.loss_propensity_band && (
            <Chip variant="pos">{score.loss_propensity_band}</Chip>
          )}
          {score.loss_trend_direction && (
            <Chip variant="aux">
              <TrendingUp size={11} />
              {formatText(score.loss_trend_direction, "capitalize")}
            </Chip>
          )}
        </div>
      )}
    </Card>
  );
}

function Metric({
  label,
  children,
}: {
  label: string;
  children: React.ReactNode;
}) {
  return (
    <div>
      <Micro className="block">{label}</Micro>
      <div className="mt-2">{children}</div>
    </div>
  );
}

function ImpactBreakdownCard({
  data,
}: {
  data: NonNullable<ScoreResponse["impact_breakdown"]>;
}) {
  return (
    <Card pad="lg" className="space-y-4">
      <Eyebrow>Premium build-up</Eyebrow>
      <div className="grid gap-2 sm:grid-cols-2">
        <LabelRow label="Base premium" value={formatCurrency(data.base_premium)} />
        <LabelRow
          label="Final premium"
          value={formatCurrency(data.final_premium)}
        />
        <LabelRow
          label="Total modifier"
          value={`${data.total_modifier > 0 ? "+" : ""}${(data.total_modifier * 100).toFixed(1)}%`}
        />
        <LabelRow
          label="Strengths / drags"
          value={`${data.strengths.length} / ${data.drags.length}`}
        />
      </div>

      <div className="grid gap-5 border-t border-rule pt-4 md:grid-cols-2">
        <ImpactList
          title={`Strengths (${data.strengths.length})`}
          accent="pos"
          empty="No captured strengths yet."
          items={data.strengths.slice(0, 5)}
        />
        <ImpactList
          title={`Opportunities (${data.drags.length})`}
          accent="spot"
          empty="No drags."
          items={data.drags.slice(0, 5)}
        />
      </div>
    </Card>
  );
}

function ImpactList({
  title,
  accent,
  empty,
  items,
}: {
  title: string;
  accent: "pos" | "spot";
  empty: string;
  items: NonNullable<ScoreResponse["impact_breakdown"]>["strengths"];
}) {
  return (
    <div>
      <Eyebrow className={accent === "pos" ? "text-pos" : "text-spot"}>
        {title}
      </Eyebrow>
      {items.length === 0 ? (
        <Body className="mt-2 italic">{empty}</Body>
      ) : (
        <ul className="mt-2 space-y-1.5 text-[13px]">
          {items.map((s) => (
            <li
              key={s.signal_key}
              className="flex items-baseline justify-between gap-3"
            >
              <span className="text-ink">{s.signal_label}</span>
              <span
                className={`shrink-0 font-semibold tabular-nums ${accent === "pos" ? "text-pos" : "text-spot"}`}
              >
                {s.premium_delta_usd > 0 ? "+" : ""}
                {formatCurrency(s.premium_delta_usd)}
              </span>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

function QuoteHistoryCard({ quotes }: { quotes: QuoteEvolutionEntry[] }) {
  return (
    <Card pad="lg" className="space-y-3">
      <header className="flex items-center justify-between">
        <Eyebrow>Quote history</Eyebrow>
        <Micro>{quotes.length} versions</Micro>
      </header>
      <ul className="space-y-2">
        {quotes.slice(0, 8).map((q, i) => (
          <li
            key={q.quote_code}
            className="flex items-baseline justify-between gap-3 border-b border-rule pb-2 last:border-0 last:pb-0"
          >
            <div className="flex items-baseline gap-3">
              <span className="text-[13px] font-semibold text-ink">
                v{q.version_number}
              </span>
              <Micro className="font-mono">{q.quote_code}</Micro>
              {i === 0 && (
                <Chip variant="info" size="sm">
                  Current
                </Chip>
              )}
            </div>
            <div className="flex items-baseline gap-4">
              {q.composite_score != null && (
                <span className="text-[13px] tabular-nums text-ink-soft">
                  {q.composite_score.toFixed(0)} pts
                </span>
              )}
              {q.final_premium != null && (
                <span className="text-[13px] font-semibold tabular-nums text-ink">
                  {formatCurrency(q.final_premium)}
                </span>
              )}
              <Micro>{formatDate(q.created_at)}</Micro>
            </div>
          </li>
        ))}
      </ul>
    </Card>
  );
}

function DrillDownGrid({ code }: { code: string }) {
  const tiles = [
    {
      title: "Signal drivers",
      hint: "What's moving the score",
      href: `/client/drivers?code=${code}`,
    },
    {
      title: "Peer comparison",
      hint: "Where you sit in your cohort",
      href: `/client/peers?code=${code}`,
    },
    {
      title: "Action plan",
      hint: "Top remediations ranked by leverage",
      href: `/client/actions?code=${code}`,
    },
    {
      title: "Scenarios",
      hint: "What-if calculations",
      href: `/client/scenarios?code=${code}`,
    },
  ];
  return (
    <section>
      <Eyebrow className="mb-3">Drill in</Eyebrow>
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {tiles.map((t) => (
          <Link key={t.title} href={t.href}>
            <Card pad="md" className="h-full transition hover:border-rule-strong">
              <Eyebrow>{t.title}</Eyebrow>
              <p className="mt-1.5 text-[14px] font-medium text-ink">
                {t.hint}
              </p>
              <Micro className="mt-3 block text-info">Open →</Micro>
            </Card>
          </Link>
        ))}
      </div>
    </section>
  );
}

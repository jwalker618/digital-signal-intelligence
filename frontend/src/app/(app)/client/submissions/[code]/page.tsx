// No direct design counterpart; adapted from reim_overview.jsx (per-coverage hero + cards).
"use client";

import { use } from "react";
import Link from "next/link";
import {
  AlertCircle,
  ArrowRight,
  TrendingDown,
  TrendingUp,
} from "lucide-react";
import { Topbar } from "@/components/chrome/topbar";
import { Card } from "@/components/ui/card";
import { Chip } from "@/components/ui/chip";
import { Eyebrow, NumDisplay, Body, Micro, Caption } from "@/components/ui/typography";
import { BackButton } from "@/components/ui/back-button";
import { ScoreHistory, type ScorePoint } from "@/components/charts/score-history";
import { PageError, PageLoading, RoleGate } from "@/components/base/pageStates";
import { useRoleScopedFetch } from "@/lib/useRoleScopedFetch";
import { fetchSubmissionDetail, fetchSubmissionScore } from "@/lib/portalApi";
import { useAuthStore } from "@/store/authStore";
import { formatCurrency, formatDate, formatText } from "@/lib/format";
import { tierStatus } from "@/lib/portalTone";
import { portalToneToTone } from "@/lib/design-tokens";
import { cn } from "@/lib/utils";
import type {
  ImpactBreakdown,
  QuoteEvolutionEntry,
  ScoreResponse,
  SubmissionDetailResponse,
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
    <DetailBody
      detail={detail.data}
      score={score.data}
      scoreError={score.error}
    />
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
  const basePremium = score?.base_premium ?? null;

  return (
    <>
      <Topbar
        crumbs={["Client Portal", "Coverages", detail.coverage]}
        entity={detail.entity_name}
      />
      <div className="flex-1 overflow-y-auto px-9 py-7">
        <div className="mx-auto grid max-w-[1400px] gap-4">
          <BackButton label="All coverages" />

          {/* ────────── hero strip ────────── */}
          <Card pad="lg" className="space-y-3">
            <div className="flex items-start justify-between gap-6">
              <div className="min-w-0">
                <Eyebrow>Coverage</Eyebrow>
                <h1 className="mt-1.5 font-display text-[32px] font-semibold leading-tight tracking-tight text-ink">
                  {detail.coverage}
                </h1>
                <Micro className="mt-1 block font-mono">
                  {detail.submission_code} · placed{" "}
                  {formatDate(detail.created_at)}
                </Micro>
              </div>
              <div className="flex flex-col items-end gap-2">
                <Chip variant={portalToneToTone(tone.tone)}>{tone.label}</Chip>
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

          {/* ────────── row 1 — score / premium / exposure ────────── */}
          {scoreError ? (
            <Card variant="warn" pad="lg">
              <Eyebrow>Score unavailable</Eyebrow>
              <Body className="mt-1">{scoreError}</Body>
            </Card>
          ) : score ? (
            <div className="grid gap-4 lg:grid-cols-[1.25fr_1fr_1.1fr]">
              <ScoreHeroCard
                score={score}
                compositeScore={compositeScore}
                detail={detail}
              />
              <PremiumCard
                basePremium={basePremium}
                finalPremium={finalPremium}
                breakdown={score.impact_breakdown ?? null}
              />
              <ExposureCard score={score} />
            </div>
          ) : null}

          {/* ────────── row 2 — premium build-up ────────── */}
          {score?.impact_breakdown && (
            <ImpactBreakdownCard data={score.impact_breakdown} />
          )}

          {/* ────────── row 3 — quote history (preserve version list) ────────── */}
          {detail.quotes.length > 0 && (
            <QuoteHistoryCard quotes={detail.quotes} />
          )}

          {/* ────────── drill-down ────────── */}
          <DrillDownGrid code={detail.submission_code} />
        </div>
      </div>
    </>
  );
}

function ScoreHeroCard({
  score,
  compositeScore,
  detail,
}: {
  score: ScoreResponse;
  compositeScore: number | null;
  detail: SubmissionDetailResponse;
}) {
  const history: ScorePoint[] = detail.quotes
    .slice()
    .reverse()
    .map((q, i, all) => ({
      label: `v${q.version_number}`,
      value: q.composite_score ?? 0,
      marker:
        i === all.length - 1 ? "now" : i === all.length - 2 ? "prev" : undefined,
    }))
    .filter((p) => p.value > 0);

  return (
    <Card variant="info" pad="lg" className="flex flex-col">
      <Eyebrow className="text-info-deep dark:text-info">
        Composite score
      </Eyebrow>
      <div className="mt-2 flex items-start gap-5">
        <NumDisplay size="xl" className="text-info">
          {compositeScore != null ? compositeScore.toFixed(0) : "—"}
        </NumDisplay>
        <div className="flex flex-col gap-1.5 pt-1">
          {score.tier != null && (
            <Chip variant="info" size="sm">
              Tier {score.tier}
            </Chip>
          )}
          {score.loss_propensity_band && (
            <Chip variant="pos" size="sm">
              {score.loss_propensity_band} loss
            </Chip>
          )}
        </div>
      </div>
      {history.length > 0 && (
        <div className="mt-4 min-h-[120px] flex-1">
          <ScoreHistory history={history} height={140} />
        </div>
      )}
    </Card>
  );
}

function PremiumCard({
  basePremium,
  finalPremium,
  breakdown,
}: {
  basePremium: number | null;
  finalPremium: number | null;
  breakdown: ImpactBreakdown | null;
}) {
  const adjustmentPct =
    basePremium != null && finalPremium != null && basePremium > 0
      ? Math.round(((finalPremium - basePremium) / basePremium) * 100)
      : null;
  return (
    <Card pad="lg" className="flex flex-col">
      <Eyebrow>Final premium</Eyebrow>
      <NumDisplay size="xl" className="mt-2">
        {finalPremium != null ? formatCurrency(finalPremium) : "—"}
      </NumDisplay>
      {basePremium != null && (
        <Caption className="mt-1 block">
          Base {formatCurrency(basePremium)}
          {adjustmentPct != null && ` · ${adjustmentPct >= 0 ? "+" : ""}${adjustmentPct}% adjustment`}
        </Caption>
      )}
      {breakdown && (
        <div className="mt-auto grid grid-cols-2 gap-2 border-t border-rule pt-3">
          <div>
            <Micro>Strengths</Micro>
            <p className="mt-0.5 text-[15px] font-semibold tabular-nums text-pos">
              {breakdown.strengths.length}
            </p>
          </div>
          <div>
            <Micro>Drags</Micro>
            <p className="mt-0.5 text-[15px] font-semibold tabular-nums text-spot">
              {breakdown.drags.length}
            </p>
          </div>
        </div>
      )}
    </Card>
  );
}

function ExposureCard({ score }: { score: ScoreResponse }) {
  const TrendIcon =
    score.loss_trend_direction && /improv|down/i.test(score.loss_trend_direction)
      ? TrendingDown
      : TrendingUp;
  return (
    <Card variant="aux" pad="lg" className="flex flex-col gap-3">
      <div className="flex items-baseline justify-between">
        <div>
          <Eyebrow className="text-aux">Exposure</Eyebrow>
          <p className="mt-1 text-xl font-semibold text-aux">
            {score.exposure_value != null
              ? formatCurrency(score.exposure_value)
              : "—"}
          </p>
          {score.exposure_band_label && (
            <Caption className="mt-0.5 block">
              {score.exposure_band_label}
            </Caption>
          )}
        </div>
        {score.loss_trend_direction && (
          <Chip variant="pos" size="sm">
            <TrendIcon size={11} />
            {formatText(score.loss_trend_direction, "capitalize")}
          </Chip>
        )}
      </div>
      {score.exposure_size_score != null && (
        <div>
          <Micro className="mb-1 block">Market scale</Micro>
          <div className="relative h-7">
            <div
              className="absolute left-0 right-0 h-1.5 rounded-full border border-rule-strong"
              style={{
                top: 12,
                background:
                  "linear-gradient(to right, var(--color-surface) 0%, var(--color-aux-soft) 50%, var(--color-aux) 100%)",
              }}
            />
            <div
              className="absolute flex -translate-x-1/2 flex-col items-center"
              style={{ left: `${score.exposure_size_score}%`, top: 0 }}
            >
              <span className="rounded bg-aux px-1.5 py-0.5 text-[10px] font-semibold text-white">
                YOU
              </span>
              <div className="h-3 w-0.5 bg-aux" />
            </div>
          </div>
        </div>
      )}
    </Card>
  );
}

function ImpactBreakdownCard({ data }: { data: ImpactBreakdown }) {
  return (
    <Card pad="lg">
      <div className="mb-3 flex items-baseline justify-between">
        <div>
          <Eyebrow>Premium build-up</Eyebrow>
          <h3 className="mt-1.5 font-display text-[17px] font-semibold leading-tight text-ink">
            What&apos;s moving your premium
          </h3>
        </div>
        <Micro>
          Modifier {data.total_modifier > 0 ? "+" : ""}
          {(data.total_modifier * 100).toFixed(1)}%
        </Micro>
      </div>
      <div className="grid gap-5 md:grid-cols-2">
        <ImpactColumn
          title="Strengths"
          accent="pos"
          items={data.strengths}
          empty="No captured strengths yet."
        />
        <ImpactColumn
          title="Opportunities"
          accent="spot"
          items={data.drags}
          empty="No drags."
        />
      </div>
    </Card>
  );
}

function ImpactColumn({
  title,
  accent,
  items,
  empty,
}: {
  title: string;
  accent: "pos" | "spot";
  items: ImpactBreakdown["strengths"];
  empty: string;
}) {
  return (
    <div>
      <Chip variant={accent} size="sm" className="mb-2">
        {title} · {items.length}
      </Chip>
      {items.length === 0 ? (
        <Body className="italic">{empty}</Body>
      ) : (
        <ul className="space-y-2">
          {items.slice(0, 6).map((s) => (
            <li
              key={s.signal_key}
              className="flex items-baseline justify-between gap-3 border-b border-rule/40 pb-2 last:border-0 last:pb-0"
            >
              <div className="min-w-0 flex-1">
                <p className="truncate text-[13.5px] font-medium text-ink">
                  {s.signal_label}
                </p>
                <Micro className="block">
                  {s.signal_source} · modifier{" "}
                  {(s.combined_modifier * 100).toFixed(1)}%
                </Micro>
              </div>
              <span
                className={cn(
                  "shrink-0 text-[13px] font-semibold tabular-nums",
                  accent === "pos" ? "text-pos" : "text-spot",
                )}
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
    <Card pad="lg">
      <div className="mb-3 flex items-baseline justify-between">
        <div>
          <Eyebrow>Version history</Eyebrow>
          <h3 className="mt-1.5 font-display text-[17px] font-semibold leading-tight text-ink">
            How this quote evolved
          </h3>
        </div>
        <Micro>{quotes.length} versions</Micro>
      </div>
      <ul className="flex flex-col">
        {quotes.slice(0, 10).map((q, i) => (
          <li
            key={q.quote_code}
            className="grid grid-cols-[80px_1fr_auto_auto] items-center gap-3 border-t border-rule py-2.5 first:border-t-0"
          >
            <div className="flex items-baseline gap-2">
              <span className="text-[13px] font-semibold text-ink">
                v{q.version_number}
              </span>
              {i === 0 && (
                <Chip variant="info" size="sm">
                  Current
                </Chip>
              )}
            </div>
            <Micro className="font-mono">{q.quote_code}</Micro>
            <span className="text-[13px] tabular-nums text-ink-soft">
              {q.composite_score != null
                ? `${q.composite_score.toFixed(0)} pts`
                : "—"}
            </span>
            <span className="text-right text-[13px] font-semibold tabular-nums text-ink">
              {q.final_premium != null
                ? formatCurrency(q.final_premium)
                : "—"}
              <Micro className="ml-2 font-normal">
                {formatDate(q.created_at)}
              </Micro>
            </span>
          </li>
        ))}
      </ul>
    </Card>
  );
}

function DrillDownGrid({ code }: { code: string }) {
  const tiles = [
    {
      title: "Risk insights",
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
              <span className="mt-3 inline-flex items-center gap-1 text-[12px] font-semibold text-info">
                Open <ArrowRight size={12} />
              </span>
            </Card>
          </Link>
        ))}
      </div>
    </section>
  );
}

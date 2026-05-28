"use client";

import Link from "next/link";
import { Suspense } from "react";
import { useSearchParams } from "next/navigation";
import { ArrowRight } from "lucide-react";
import { Topbar } from "@/components/chrome/topbar";
import { Card } from "@/components/ui/card";
import { Chip } from "@/components/ui/chip";
import { Eyebrow, NumDisplay, Body, Micro } from "@/components/ui/typography";
import { LabelRow } from "@/components/ui/label-row";
import { Waterfall } from "@/components/charts/waterfall";
import { PageError, PageLoading, RoleGate } from "@/components/base/pageStates";
import { useRoleScopedFetch } from "@/lib/useRoleScopedFetch";
import { fetchOverview, fetchSubmissionScore } from "@/lib/portalApi";
import { useAuthStore } from "@/store/authStore";
import { formatCurrency } from "@/lib/format";
import type {
  OverviewResponse,
  ScoreResponse,
  SignalImpact,
} from "@/types/portal";

export default function ClientDriversPage() {
  return (
    <Suspense fallback={<PageLoading />}>
      <DriversInner />
    </Suspense>
  );
}

function DriversInner() {
  const accessToken = useAuthStore((s) => s.accessToken);
  const user = useAuthStore((s) => s.user);
  const enabled = !!accessToken && user?.role === "CLIENT";
  const params = useSearchParams();
  const explicitCode = params.get("code");

  // Always need /overview to know which coverages exist and pick a default.
  const overview = useRoleScopedFetch<OverviewResponse>({
    fetcher: () => fetchOverview(accessToken),
    enabled,
    deps: [accessToken],
  });

  const code =
    explicitCode ??
    (overview.data?.role === "CLIENT"
      ? overview.data.active_coverages[0]?.submission_code
      : undefined);

  const score = useRoleScopedFetch<ScoreResponse>({
    fetcher: () => fetchSubmissionScore(accessToken, code!),
    enabled: enabled && !!code,
    deps: [accessToken, code],
  });

  if (!user) return <PageLoading message="Signing in…" />;
  if (user.role && user.role !== "CLIENT") return <RoleGate expected="client" />;
  if (overview.loading) return <PageLoading />;
  if (overview.error) return <PageError message={overview.error} />;
  if (!overview.data || overview.data.role !== "CLIENT")
    return <RoleGate expected="client" />;
  if (!code) return <NoCoverage entityName={overview.data.entity_name} />;
  if (score.loading) return <PageLoading />;
  if (score.error) return <PageError message={score.error} />;
  if (!score.data) return <PageLoading />;

  return (
    <DriversBody
      entityName={overview.data.entity_name}
      score={score.data}
      allCoverages={overview.data.active_coverages.map((c) => ({
        code: c.submission_code,
        coverage: c.coverage,
      }))}
      activeCode={code}
    />
  );
}

function NoCoverage({ entityName }: { entityName: string }) {
  return (
    <>
      <Topbar
        crumbs={["Client Portal", "Risk Insights"]}
        entity={entityName}
      />
      <div className="flex flex-1 items-start justify-center px-9 py-12">
        <Card pad="lg" className="max-w-md">
          <Eyebrow>No coverage selected</Eyebrow>
          <Body className="mt-2">
            Risk Insights scopes to a single coverage. Open one from{" "}
            <Link
              href="/client/coverages"
              className="font-semibold text-info hover:underline"
            >
              Coverages
            </Link>{" "}
            to view its score build-up.
          </Body>
        </Card>
      </div>
    </>
  );
}

function DriversBody({
  entityName,
  score,
  allCoverages,
  activeCode,
}: {
  entityName: string;
  score: ScoreResponse;
  allCoverages: { code: string; coverage: string }[];
  activeCode: string;
}) {
  const ib = score.impact_breakdown;

  return (
    <>
      <Topbar
        crumbs={["Client Portal", "Risk Insights", score.coverage]}
        entity={entityName}
      />
      <div className="flex-1 overflow-y-auto px-9 py-7">
        <div className="mx-auto grid max-w-[1280px] gap-6">
          <header className="flex items-end justify-between gap-6">
            <div>
              <Eyebrow>Risk Insights</Eyebrow>
              <h1 className="mt-1.5 font-display text-[32px] font-semibold leading-none tracking-tight text-ink">
                {score.coverage}
              </h1>
              <Body className="mt-2">
                What's pushing your composite up or down — strengths captured
                vs. signals still pending.
              </Body>
            </div>
            <CoveragePicker
              all={allCoverages}
              activeCode={activeCode}
              baseHref="/client/drivers"
            />
          </header>

          {/* Headline metrics */}
          <div className="grid gap-4 md:grid-cols-4">
            <HeadlineCard
              variant="default"
              label="Base premium"
              value={ib?.base_premium ?? score.base_premium}
            />
            <HeadlineCard
              variant="pos"
              label="Strengths captured"
              value={ib ? ib.strengths.reduce((s, x) => s + x.premium_delta_usd, 0) : null}
              countSuffix={ib ? `${ib.strengths.length} signals` : undefined}
            />
            <HeadlineCard
              variant="spot"
              label="Opportunity gap"
              value={ib ? ib.drags.reduce((s, x) => s + x.premium_delta_usd, 0) : null}
              countSuffix={ib ? `${ib.drags.length} signals` : undefined}
            />
            <HeadlineCard
              variant="info"
              label="Final premium"
              value={ib?.final_premium ?? score.final_premium}
              emphasis
            />
          </div>

          {/* Waterfall */}
          {ib && (
            <Card pad="lg">
              <header className="mb-4 flex items-center justify-between">
                <Eyebrow>Premium waterfall</Eyebrow>
                <Micro>
                  Modifier {ib.total_modifier > 0 ? "+" : ""}
                  {(ib.total_modifier * 100).toFixed(1)}%
                </Micro>
              </header>
              <Waterfall
                items={[
                  {
                    id: "base",
                    label: "Base",
                    value: ib.base_premium,
                    type: "base",
                  },
                  {
                    id: "strengths",
                    label: "Strengths",
                    value: ib.strengths.reduce((s, x) => s + x.premium_delta_usd, 0),
                    type: "pos",
                  },
                  {
                    id: "drags",
                    label: "Drags",
                    value: ib.drags.reduce((s, x) => s + x.premium_delta_usd, 0),
                    type: "opp",
                  },
                  {
                    id: "final",
                    label: "Final",
                    value: ib.final_premium,
                    type: "final",
                  },
                ]}
              />
            </Card>
          )}

          {/* Signal lists */}
          {ib && (
            <div className="grid gap-5 md:grid-cols-2">
              <SignalImpactList
                title="What's helping"
                accent="pos"
                items={ib.strengths}
                empty="No strengths captured yet — opportunities below."
              />
              <SignalImpactList
                title="Opportunities"
                accent="spot"
                items={ib.drags}
                empty="No drags — everything is captured. 🎉"
              />
            </div>
          )}

          {/* Loss + exposure quick stats */}
          {(score.loss_propensity_score != null ||
            score.exposure_value != null) && (
            <Card pad="lg" className="space-y-3">
              <Eyebrow>Loss + exposure</Eyebrow>
              <div className="grid gap-2 md:grid-cols-2">
                {score.loss_propensity_score != null && (
                  <LabelRow
                    label="Loss propensity"
                    value={`${score.loss_propensity_score.toFixed(0)} ${score.loss_propensity_band ? `· ${score.loss_propensity_band}` : ""}`}
                  />
                )}
                {score.severity_propensity_score != null && (
                  <LabelRow
                    label="Severity propensity"
                    value={score.severity_propensity_score.toFixed(0)}
                  />
                )}
                {score.exposure_value != null && (
                  <LabelRow
                    label="Exposure value"
                    value={formatCurrency(score.exposure_value)}
                  />
                )}
                {score.exposure_size_score != null && (
                  <LabelRow
                    label="Exposure size score"
                    value={score.exposure_size_score.toFixed(0)}
                  />
                )}
              </div>
            </Card>
          )}

          <Link
            href={`/client/actions?code=${activeCode}`}
            className="inline-flex items-center gap-2 self-start rounded-card border border-info bg-info-soft px-4 py-3 text-[13px] font-semibold text-info-deep transition hover:bg-info hover:text-white dark:text-info"
          >
            See action plan for these opportunities <ArrowRight size={14} />
          </Link>
        </div>
      </div>
    </>
  );
}

function HeadlineCard({
  variant,
  label,
  value,
  countSuffix,
  emphasis,
}: {
  variant: "default" | "pos" | "spot" | "info";
  label: string;
  value: number | null | undefined;
  countSuffix?: string;
  emphasis?: boolean;
}) {
  return (
    <Card pad="md" variant={variant}>
      <Micro
        className={
          variant === "info"
            ? "text-info-deep dark:text-info"
            : variant === "pos"
              ? "text-pos"
              : variant === "spot"
                ? "text-spot-deep dark:text-spot"
                : ""
        }
      >
        {label}
      </Micro>
      <div className="mt-2">
        {value != null ? (
          <NumDisplay size={emphasis ? "lg" : "md"}>
            {value > 0 ? "" : ""}
            {formatCurrency(value)}
          </NumDisplay>
        ) : (
          <Body className="italic">Pending</Body>
        )}
      </div>
      {countSuffix && <Micro className="mt-1.5 block">{countSuffix}</Micro>}
    </Card>
  );
}

function SignalImpactList({
  title,
  accent,
  items,
  empty,
}: {
  title: string;
  accent: "pos" | "spot";
  items: SignalImpact[];
  empty: string;
}) {
  const sorted = [...items].sort(
    (a, b) => Math.abs(b.premium_delta_usd) - Math.abs(a.premium_delta_usd),
  );
  return (
    <Card pad="lg" variant={accent}>
      <header className="flex items-center justify-between">
        <Eyebrow className={accent === "pos" ? "text-pos" : "text-spot-deep dark:text-spot"}>
          {title}
        </Eyebrow>
        <Micro>{items.length} signals</Micro>
      </header>
      {items.length === 0 ? (
        <Body className="mt-3 italic">{empty}</Body>
      ) : (
        <ul className="mt-3 space-y-2">
          {sorted.slice(0, 8).map((s) => (
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
                className={`shrink-0 text-[13px] font-semibold tabular-nums ${accent === "pos" ? "text-pos" : "text-spot"}`}
              >
                {s.premium_delta_usd > 0 ? "+" : ""}
                {formatCurrency(s.premium_delta_usd)}
              </span>
            </li>
          ))}
          {items.length > 8 && (
            <li>
              <Micro>+{items.length - 8} more</Micro>
            </li>
          )}
        </ul>
      )}
    </Card>
  );
}

function CoveragePicker({
  all,
  activeCode,
  baseHref,
}: {
  all: { code: string; coverage: string }[];
  activeCode: string;
  baseHref: string;
}) {
  if (all.length <= 1) return null;
  return (
    <label className="flex items-center gap-2 text-[12.5px]">
      <span className="text-ink-mute">Coverage:</span>
      <select
        value={activeCode}
        onChange={(e) => {
          window.location.href = `${baseHref}?code=${e.target.value}`;
        }}
        className="rounded-btn border border-rule-strong bg-surface px-3 py-1.5 text-[13px] font-medium text-ink focus:border-info focus:outline-none focus:ring-2 focus:ring-info/30"
      >
        {all.map((c) => (
          <option key={c.code} value={c.code}>
            {c.coverage}
          </option>
        ))}
      </select>
    </label>
  );
}

"use client";

import Link from "next/link";
import { ChevronRight } from "lucide-react";
import { Topbar } from "@/components/chrome/topbar";
import { Card } from "@/components/ui/card";
import { Eyebrow, Body, Micro } from "@/components/ui/typography";
import { type PremiumSlice } from "@/components/charts/premium-breakdown";
import { PageError, PageLoading, RoleGate } from "@/components/base/pageStates";
import { useRoleScopedFetch } from "@/lib/useRoleScopedFetch";
import { fetchOverview, fetchSubmissionScore } from "@/lib/portalApi";
import { useAuthStore } from "@/store/authStore";
import type {
  ClientOverviewResponse,
  OverviewResponse,
  ScoreResponse,
} from "@/types/portal";
import { ScoreCard } from "./_components/ScoreCard";
import { PremiumCard } from "./_components/PremiumCard";
import { AwaitingCard } from "./_components/AwaitingCard";
import { SignalPulseCard } from "./_components/SignalPulseCard";
import { CohortStandingCard } from "./_components/CohortStandingCard";
import { LossOutlookCard } from "./_components/LossOutlookCard";
import { ExposureCard } from "./_components/ExposureCard";
import { CoverageShapeCard } from "./_components/CoverageShapeCard";

/**
 * Client Overview — landing page.
 *
 * Mirrors the reimagined Overview design (client_review/reim_overview.jsx)
 * in three rows; each card lives in ./_components/ and is memoised, so
 * unrelated store updates and search/filter clicks don't re-render the
 * full dashboard.
 */
export default function ClientOverviewPage() {
  const accessToken = useAuthStore((s) => s.accessToken);
  const user = useAuthStore((s) => s.user);
  const enabled = !!accessToken && user?.role === "CLIENT";
  const { data, error, loading } = useRoleScopedFetch<OverviewResponse>({
    fetcher: () => fetchOverview(accessToken),
    enabled,
    deps: [accessToken],
  });

  if (!user) return <PageLoading message="Signing in…" />;
  if (user.role && user.role !== "CLIENT") return <RoleGate expected="client" />;
  if (loading) return <PageLoading />;
  if (error) return <PageError message={error} />;
  if (!data) return <PageLoading />;
  if (data.role !== "CLIENT") return <RoleGate expected="client" />;

  return <OverviewBody data={data} />;
}

function OverviewBody({ data }: { data: ClientOverviewResponse }) {
  const accessToken = useAuthStore((s) => s.accessToken);
  const coverages = data.active_coverages;
  const hero = coverages[0];

  // Secondary fetch: the hero coverage's impact breakdown for the
  // Signal Pulse card. Intentionally not awaited at the page level —
  // the card renders its own empty state while loading.
  const heroCode = hero?.submission_code ?? null;
  const score = useRoleScopedFetch<ScoreResponse>({
    fetcher: () => fetchSubmissionScore(accessToken, heroCode as string),
    enabled: !!accessToken && !!heroCode,
    deps: [accessToken, heroCode],
  });

  const slices: PremiumSlice[] = coverages
    .filter((c) => c.recommended_premium != null)
    .map((c) => ({ line: c.coverage, amount: c.recommended_premium as number }));

  const awaitingItems = coverages
    .filter((c) => c.referral_state && /await/i.test(c.referral_state))
    .map((c) => ({
      ask: `${c.coverage} referral awaiting your response`,
      line: `${c.coverage} · ${c.submission_code}`,
      age: "Pending",
      href: `/client/submissions/${c.submission_code}`,
    }));

  return (
    <>
      <Topbar
        crumbs={["Client Portal", "Overview"]}
        entity={data.entity_name}
      />
      <div className="flex-1 overflow-y-auto px-9 py-7">
        <div className="mx-auto grid max-w-[1400px] gap-4">
          {/* ────────── ROW 1 — hero strip ────────── */}
          <div className="grid gap-4 lg:grid-cols-[1.25fr_1fr_1.1fr]">
            <ScoreCard hero={hero} />
            <PremiumCard slices={slices} fallbackTotal={null} />
            <AwaitingCard items={awaitingItems} />
          </div>

          {/* ────────── ROW 2 — signal pulse + cohort ────────── */}
          <div className="grid gap-4 lg:grid-cols-[1.4fr_1fr]">
            <SignalPulseCard
              breakdown={score.data?.impact_breakdown ?? null}
              loading={score.loading}
            />
            <CohortStandingCard hero={hero} />
          </div>

          {/* ────────── ROW 3 — loss / exposure / coverage shape ────────── */}
          <div className="grid gap-4 lg:grid-cols-3">
            <LossOutlookCard hero={hero} />
            <ExposureCard hero={hero} />
            <CoverageShapeCard coverages={coverages} />
          </div>

          {hero && (
            <Card pad="md" className="flex items-center justify-between gap-4">
              <div>
                <Eyebrow>Primary coverage</Eyebrow>
                <p className="mt-1 text-[15px] font-semibold text-ink">
                  {hero.coverage}
                </p>
                <Micro className="mt-0.5 block font-mono">
                  {hero.submission_code}
                </Micro>
              </div>
              <Link
                href={`/client/submissions/${hero.submission_code}`}
                className="inline-flex h-10 items-center gap-2 rounded-btn border border-rule-strong px-4 text-[13px] font-semibold text-ink hover:bg-surface-sunken"
              >
                Open coverage detail
                <ChevronRight size={14} />
              </Link>
            </Card>
          )}

          {coverages.length === 0 && (
            <Card pad="lg">
              <Eyebrow>No active coverages</Eyebrow>
              <Body className="mt-2">
                Your broker hasn&apos;t placed any coverages on this portal yet.
              </Body>
            </Card>
          )}
        </div>
      </div>
    </>
  );
}

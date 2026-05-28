"use client";

import Link from "next/link";
import { ShieldCheck } from "lucide-react";
import { Topbar } from "@/components/chrome/topbar";
import { Card } from "@/components/ui/card";
import { Chip } from "@/components/ui/chip";
import { Eyebrow, NumDisplay, Body, Micro } from "@/components/ui/typography";
import { Button } from "@/components/ui/button";
import { PageError, PageLoading, RoleGate } from "@/components/base/pageStates";
import { useRoleScopedFetch } from "@/lib/useRoleScopedFetch";
import { fetchOverview } from "@/lib/portalApi";
import { useAuthStore } from "@/store/authStore";
import { formatCurrency } from "@/lib/format";
import { tierStatus, peerStandingPositive } from "@/lib/portalTone";
import type {
  ClientOverviewResponse,
  ClientCoverageEntry,
  OverviewResponse,
} from "@/types/portal";

/**
 * Client Overview — landing page.
 *
 * The portal /overview endpoint returns the entity name + a flat list of
 * the client's active coverages. Rich per-coverage detail (score, peers,
 * actions) hangs off the per-submission endpoints; the design's hero
 * surfaces are populated on-demand when the user opens a coverage.
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
  const coverages = data.active_coverages;
  const hero = coverages[0];
  const others = coverages.slice(1);

  return (
    <>
      <Topbar crumbs={["Client Portal", "Overview"]} entity={data.entity_name} />
      <div className="flex-1 overflow-y-auto px-9 py-7">
        <div className="mx-auto grid max-w-[1280px] gap-6">
          <header className="flex items-end justify-between gap-6">
            <div>
              <Eyebrow>Insured</Eyebrow>
              <h1 className="mt-1 font-display text-[36px] font-semibold leading-none tracking-tight text-ink">
                {data.entity_name}
              </h1>
              {data.broker && (
                <Body className="mt-2">
                  Placed by{" "}
                  <span className="font-semibold text-ink">
                    {data.broker.name}
                  </span>
                </Body>
              )}
            </div>
            <Button variant="ghost">
              <ShieldCheck size={15} />
              Request coverage
            </Button>
          </header>

          {coverages.length === 0 ? (
            <Card pad="lg">
              <Eyebrow>No active coverages</Eyebrow>
              <Body className="mt-2">
                Your broker hasn't placed any coverages on this portal yet.
              </Body>
            </Card>
          ) : (
            <>
              {hero && <HeroCoverageCard entry={hero} />}
              {others.length > 0 && (
                <section>
                  <Eyebrow className="mb-3">Other coverages</Eyebrow>
                  <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
                    {others.map((c) => (
                      <CoverageTile key={c.submission_code} entry={c} />
                    ))}
                  </div>
                </section>
              )}
            </>
          )}
        </div>
      </div>
    </>
  );
}

function HeroCoverageCard({ entry }: { entry: ClientCoverageEntry }) {
  const tone = tierStatus(entry.tier);
  const peer = peerStandingPositive(entry.peer_percentile_rank);
  return (
    <Card variant="info" pad="lg" className="space-y-5">
      <div className="flex items-start justify-between gap-4">
        <div>
          <Eyebrow>{toneToEyebrow(tone.tone)}</Eyebrow>
          <h2 className="mt-1 font-display text-[32px] font-semibold leading-none text-ink">
            {entry.coverage}
          </h2>
          <Body className="mt-1.5">{tone.description}</Body>
        </div>
        <Chip variant={toneToChip(tone.tone)}>{tone.label}</Chip>
      </div>

      <div className="grid grid-cols-3 gap-6 border-t border-info/30 pt-5">
        <Metric label="Composite score">
          {entry.composite_score != null ? (
            <NumDisplay size="xl">{entry.composite_score.toFixed(0)}</NumDisplay>
          ) : (
            <Body className="italic">Pending</Body>
          )}
        </Metric>
        <Metric label="Recommended premium">
          {entry.recommended_premium != null ? (
            <NumDisplay>{formatCurrency(entry.recommended_premium)}</NumDisplay>
          ) : (
            <Body className="italic">Pending</Body>
          )}
        </Metric>
        <Metric label="Peer cohort">
          <Body className="text-ink">{peer}</Body>
        </Metric>
      </div>

      <div className="flex items-center gap-3">
        <Link
          href={`/client/submissions/${entry.submission_code}`}
          className="text-[13px] font-semibold text-info hover:underline"
        >
          Open coverage detail →
        </Link>
        {entry.referral_state && (
          <Micro>Status: {entry.referral_state.toLowerCase()}</Micro>
        )}
      </div>
    </Card>
  );
}

function CoverageTile({ entry }: { entry: ClientCoverageEntry }) {
  const tone = tierStatus(entry.tier);
  return (
    <Link
      href={`/client/submissions/${entry.submission_code}`}
      className="block rounded-card border border-rule bg-surface p-5 transition hover:border-rule-strong"
    >
      <div className="flex items-start justify-between gap-3">
        <div>
          <Eyebrow>{toneToEyebrow(tone.tone)}</Eyebrow>
          <p className="mt-1 text-[18px] font-semibold leading-tight text-ink">
            {entry.coverage}
          </p>
        </div>
        <Chip variant={toneToChip(tone.tone)} size="sm">
          {tone.label}
        </Chip>
      </div>
      <div className="mt-4 grid grid-cols-2 gap-3 text-[12.5px]">
        <div>
          <Micro>Score</Micro>
          <p className="mt-0.5 font-semibold text-ink tabular-nums">
            {entry.composite_score?.toFixed(0) ?? "—"}
          </p>
        </div>
        <div>
          <Micro>Premium</Micro>
          <p className="mt-0.5 font-semibold text-ink tabular-nums">
            {entry.recommended_premium != null
              ? formatCurrency(entry.recommended_premium)
              : "—"}
          </p>
        </div>
      </div>
    </Link>
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
      <div className="mt-1.5">{children}</div>
    </div>
  );
}

function toneToChip(
  tone: "positive" | "warning" | "negative" | "muted",
): "pos" | "warn" | "neg" | "mute" {
  return tone === "positive"
    ? "pos"
    : tone === "warning"
      ? "warn"
      : tone === "negative"
        ? "neg"
        : "mute";
}
function toneToEyebrow(tone: string): string {
  return tone === "positive"
    ? "Preferred"
    : tone === "warning"
      ? "Under review"
      : tone === "negative"
        ? "Constrained"
        : "Standard";
}


"use client";

import Link from "next/link";
import { Suspense, useMemo, useState } from "react";
import { useSearchParams } from "next/navigation";
import { Check, FlaskConical, Sigma } from "lucide-react";
import { Topbar } from "@/components/chrome/topbar";
import { Card } from "@/components/ui/card";
import { Chip } from "@/components/ui/chip";
import { Eyebrow, NumDisplay, Body, Micro } from "@/components/ui/typography";
import { Button } from "@/components/ui/button";
import { PageError, PageLoading, RoleGate } from "@/components/base/pageStates";
import { useRoleScopedFetch } from "@/lib/useRoleScopedFetch";
import { fetchOverview, fetchSubmissionScore } from "@/lib/portalApi";
import { useAuthStore } from "@/store/authStore";
import { formatCurrency } from "@/lib/format";
import { cn } from "@/lib/utils";
import type {
  OverviewResponse,
  ScoreResponse,
  SignalImpact,
} from "@/types/portal";

export default function ClientScenariosPage() {
  return (
    <Suspense fallback={<PageLoading />}>
      <ScenariosInner />
    </Suspense>
  );
}

function ScenariosInner() {
  const accessToken = useAuthStore((s) => s.accessToken);
  const user = useAuthStore((s) => s.user);
  const enabled = !!accessToken && user?.role === "CLIENT";
  const params = useSearchParams();
  const explicitCode = params.get("code");

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
  if (!code) {
    return (
      <>
        <Topbar
          crumbs={["Client Portal", "Scenarios"]}
          entity={overview.data.entity_name}
        />
        <div className="flex flex-1 items-start justify-center px-9 py-12">
          <Card pad="lg" className="max-w-md">
            <Eyebrow>No coverage selected</Eyebrow>
            <Body className="mt-2">
              Open one from{" "}
              <Link
                href="/client/coverages"
                className="font-semibold text-info hover:underline"
              >
                Coverages
              </Link>{" "}
              to model what-if scenarios for it.
            </Body>
          </Card>
        </div>
      </>
    );
  }
  if (score.loading) return <PageLoading />;
  if (score.error) return <PageError message={score.error} />;
  if (!score.data) return <PageLoading />;

  return (
    <ScenariosBody
      entityName={overview.data.entity_name}
      score={score.data}
    />
  );
}

function ScenariosBody({
  entityName,
  score,
}: {
  entityName: string;
  score: ScoreResponse;
}) {
  const ib = score.impact_breakdown;
  const basePremium = ib?.base_premium ?? score.base_premium ?? 0;
  const finalPremium = ib?.final_premium ?? score.final_premium ?? 0;

  const drags = useMemo<SignalImpact[]>(
    () =>
      (ib?.drags ?? [])
        .slice()
        .sort(
          (a, b) =>
            Math.abs(b.premium_delta_usd) - Math.abs(a.premium_delta_usd),
        ),
    [ib],
  );

  const [picked, setPicked] = useState<Record<string, boolean>>({});
  const projectedDelta = drags
    .filter((d) => picked[d.signal_key])
    .reduce((sum, d) => sum + d.premium_delta_usd, 0);
  // Drags are dollars added by the drag; capturing them removes that drag.
  // So projected savings is the sum of positive deltas we'd eliminate.
  const projectedSavings = projectedDelta;
  const projectedFinal = finalPremium - Math.abs(projectedSavings);
  const pickedCount = Object.values(picked).filter(Boolean).length;

  return (
    <>
      <Topbar
        crumbs={["Client Portal", "Scenarios", score.coverage]}
        entity={entityName}
      />
      <div className="flex-1 overflow-y-auto px-9 py-7">
        <div className="mx-auto grid max-w-[1280px] gap-6">
          <header>
            <Eyebrow>Scenarios</Eyebrow>
            <h1 className="mt-1.5 font-display text-[32px] font-semibold leading-none tracking-tight text-ink">
              {score.coverage}
            </h1>
            <Body className="mt-2">
              Pick the signals you could realistically capture. We'll project
              what your premium would look like after the next reassessment.
            </Body>
          </header>

          {/* Live projection */}
          <Card variant="info" pad="lg" className="space-y-4">
            <div className="grid grid-cols-1 gap-6 sm:grid-cols-3">
              <Projection
                label="Current final premium"
                value={finalPremium}
              />
              <Projection
                label="Projected savings"
                value={-Math.abs(projectedSavings)}
                tone="pos"
                emphasis
              />
              <Projection
                label="Projected final"
                value={projectedFinal}
              />
            </div>
            <div className="flex items-center justify-between gap-3 border-t border-info/30 pt-4 text-[13px]">
              <span className="text-ink-soft">
                {pickedCount} signal{pickedCount === 1 ? "" : "s"} captured ·{" "}
                {drags.length - pickedCount} remaining
              </span>
              <div className="flex items-center gap-2">
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  onClick={() => setPicked({})}
                  disabled={pickedCount === 0}
                >
                  Reset
                </Button>
                <Button
                  type="button"
                  variant="info"
                  size="sm"
                  onClick={() => {
                    const all: Record<string, boolean> = {};
                    drags.forEach((d) => (all[d.signal_key] = true));
                    setPicked(all);
                  }}
                  disabled={pickedCount === drags.length}
                >
                  Capture all
                </Button>
              </div>
            </div>
          </Card>

          {/* Pickable signals */}
          {drags.length === 0 ? (
            <Card variant="pos" pad="lg">
              <Eyebrow className="text-pos">Nothing to model</Eyebrow>
              <Body className="mt-2">
                Your signal apparatus is fully captured for this coverage —
                there are no drags to convert into savings.
              </Body>
            </Card>
          ) : (
            <section>
              <Eyebrow className="mb-3">Pickable signals (drags)</Eyebrow>
              <div className="grid gap-3 md:grid-cols-2">
                {drags.map((d) => (
                  <SignalToggle
                    key={d.signal_key}
                    signal={d}
                    picked={!!picked[d.signal_key]}
                    onToggle={(v) =>
                      setPicked((s) => ({ ...s, [d.signal_key]: v }))
                    }
                  />
                ))}
              </div>
            </section>
          )}

          <Card pad="md" className="flex items-start gap-3">
            <Sigma size={16} className="mt-0.5 shrink-0 text-ink-mute" />
            <div>
              <Micro>Methodology</Micro>
              <Body className="text-[12.5px]">
                Projections sum the premium delta the underwriting model
                already attributes to each captured signal. Real reassessment
                may produce small differences due to interaction effects;
                ranges are indicative only.
              </Body>
            </div>
          </Card>

          <Link
            href={`/client/actions?code=${score.submission_code}`}
            className="inline-flex items-center gap-2 self-start rounded-card border border-spot bg-spot-soft px-4 py-3 text-[13px] font-semibold text-spot-deep dark:text-spot transition hover:bg-spot hover:text-white"
          >
            <FlaskConical size={14} />
            See how to actually capture these →
          </Link>
        </div>
      </div>
    </>
  );
}

function Projection({
  label,
  value,
  tone,
  emphasis,
}: {
  label: string;
  value: number;
  tone?: "pos";
  emphasis?: boolean;
}) {
  return (
    <div>
      <Micro className="block">{label}</Micro>
      <div
        className={cn(
          "mt-1",
          tone === "pos" && "text-pos",
          emphasis && tone === "pos" && "font-semibold",
        )}
      >
        <NumDisplay
          size={emphasis ? "lg" : "md"}
          className={tone === "pos" ? "text-pos" : ""}
        >
          {formatCurrency(value)}
        </NumDisplay>
      </div>
    </div>
  );
}

function SignalToggle({
  signal,
  picked,
  onToggle,
}: {
  signal: SignalImpact;
  picked: boolean;
  onToggle: (v: boolean) => void;
}) {
  return (
    <button
      type="button"
      onClick={() => onToggle(!picked)}
      className={cn(
        "flex items-start gap-3 rounded-card border p-4 text-left transition",
        picked
          ? "border-pos bg-pos-soft"
          : "border-rule bg-surface hover:border-rule-strong",
      )}
      aria-pressed={picked}
    >
      <div
        className={cn(
          "mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded-md border transition",
          picked
            ? "border-pos bg-pos text-white"
            : "border-rule-strong bg-surface",
        )}
        aria-hidden
      >
        {picked && <Check size={13} />}
      </div>
      <div className="min-w-0 flex-1">
        <p className="truncate text-[14px] font-semibold text-ink">
          {signal.signal_label}
        </p>
        <Micro className="block">
          {signal.signal_source} · modifier{" "}
          {(signal.combined_modifier * 100).toFixed(1)}%
        </Micro>
      </div>
      <div className="text-right">
        <span className="block text-[14px] font-semibold tabular-nums text-pos">
          −{formatCurrency(Math.abs(signal.premium_delta_usd))}
        </span>
        <Micro>per year</Micro>
      </div>
    </button>
  );
}

"use client";

import Link from "next/link";
import { Suspense } from "react";
import { useSearchParams } from "next/navigation";
import { Clock, ExternalLink, FileCheck2, Gauge, Lightbulb, TrendingDown } from "lucide-react";
import { Topbar } from "@/components/chrome/topbar";
import { Card } from "@/components/ui/card";
import { Chip } from "@/components/ui/chip";
import { Eyebrow, NumDisplay, Body, Micro } from "@/components/ui/typography";
import { PageError, PageLoading, RoleGate } from "@/components/base/pageStates";
import { useRoleScopedFetch } from "@/lib/useRoleScopedFetch";
import { fetchOverview, fetchSubmissionActions } from "@/lib/portalApi";
import { useAuthStore } from "@/store/authStore";
import { formatCurrency } from "@/lib/format";
import { cn } from "@/lib/utils";
import type {
  ActionsResponse,
  OverviewResponse,
  RemediationAction,
} from "@/types/portal";

export default function ClientActionsPage() {
  return (
    <Suspense fallback={<PageLoading />}>
      <ActionsInner />
    </Suspense>
  );
}

function ActionsInner() {
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

  const actions = useRoleScopedFetch<ActionsResponse>({
    fetcher: () => fetchSubmissionActions(accessToken, code!),
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
          crumbs={["Client Portal", "Action Plan"]}
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
              to see actionable remediations.
            </Body>
          </Card>
        </div>
      </>
    );
  }
  if (actions.loading) return <PageLoading />;
  if (actions.error) return <PageError message={actions.error} />;
  if (!actions.data) return <PageLoading />;

  return (
    <ActionsBody
      entityName={overview.data.entity_name}
      data={actions.data}
    />
  );
}

function ActionsBody({
  entityName,
  data,
}: {
  entityName: string;
  data: ActionsResponse;
}) {
  const sorted = [...data.remediation_plan.actions].sort((a, b) => {
    // Highest leverage first; tie-break on dollar impact.
    if (b.leverage !== a.leverage) return b.leverage - a.leverage;
    return (
      Math.abs(b.estimated_premium_delta_usd) -
      Math.abs(a.estimated_premium_delta_usd)
    );
  });
  const real = sorted.filter((a) => !a.is_placeholder);
  const hero = real[0];
  const others = real.slice(1, 4);
  const remaining = real.slice(4);
  const totalSavings = real.reduce(
    (sum, a) => sum + Math.min(0, a.estimated_premium_delta_usd),
    0,
  );

  return (
    <>
      <Topbar
        crumbs={["Client Portal", "Action Plan", data.coverage]}
        entity={entityName}
      />
      <div className="flex-1 overflow-y-auto px-9 py-7">
        <div className="mx-auto grid max-w-[1280px] gap-6">
          <header className="flex items-end justify-between gap-6">
            <div>
              <Eyebrow>Action Plan</Eyebrow>
              <h1 className="mt-1.5 font-display text-[32px] font-semibold leading-none tracking-tight text-ink">
                {data.coverage}
              </h1>
              <Body className="mt-2">
                Ranked by leverage — the score and premium movement you'd get
                per unit of effort.
              </Body>
            </div>
            {totalSavings < 0 && (
              <div className="text-right">
                <Eyebrow>Total potential savings</Eyebrow>
                <p className="mt-1 font-display text-[28px] font-semibold leading-none tabular-nums text-pos">
                  {formatCurrency(totalSavings)}
                </p>
                <Micro>if every action is taken</Micro>
              </div>
            )}
          </header>

          {real.length === 0 ? (
            <Card variant="pos" pad="lg">
              <Eyebrow className="text-pos">Nothing to do</Eyebrow>
              <Body className="mt-2">
                Your signal apparatus is fully captured for this coverage —
                there's no concrete remediation to recommend right now.
              </Body>
            </Card>
          ) : (
            <>
              {hero && <HeroAction action={hero} />}
              {others.length > 0 && (
                <section>
                  <Eyebrow className="mb-3">Supporting actions</Eyebrow>
                  <div className="grid gap-4 md:grid-cols-3">
                    {others.map((a) => (
                      <SupportingAction key={a.signal_key} action={a} />
                    ))}
                  </div>
                </section>
              )}
              {remaining.length > 0 && (
                <Card pad="md">
                  <header className="mb-3 flex items-center justify-between">
                    <Eyebrow>+{remaining.length} more</Eyebrow>
                    <Micro>Lower leverage but still worth pursuing</Micro>
                  </header>
                  <ul className="space-y-2">
                    {remaining.map((a) => (
                      <li
                        key={a.signal_key}
                        className="flex items-baseline justify-between gap-3 border-b border-rule pb-2 last:border-0 last:pb-0"
                      >
                        <div className="min-w-0 flex-1">
                          <p className="truncate text-[13.5px] font-medium text-ink">
                            {a.remediation.headline}
                          </p>
                          <Micro className="block">{a.signal_label}</Micro>
                        </div>
                        <span className="text-[13px] font-semibold tabular-nums text-pos">
                          {formatCurrency(a.estimated_premium_delta_usd)}
                        </span>
                      </li>
                    ))}
                  </ul>
                </Card>
              )}
            </>
          )}

          {data.remediation_plan.placeholder_count > 0 && (
            <Card variant="aux" pad="md">
              <Eyebrow className="text-aux">Data gap</Eyebrow>
              <Body className="mt-1">
                {data.remediation_plan.placeholder_count} additional signal
                {data.remediation_plan.placeholder_count === 1 ? "" : "s"} could
                generate further actions once we capture more data from your
                profile.
              </Body>
            </Card>
          )}
        </div>
      </div>
    </>
  );
}

function HeroAction({ action }: { action: RemediationAction }) {
  return (
    <Card variant="info" pad="lg" className="space-y-5">
      <header className="flex items-start justify-between gap-4">
        <div>
          <Eyebrow className="text-info-deep dark:text-info">
            #1 lever
          </Eyebrow>
          <h2 className="mt-1 font-display text-[26px] font-semibold leading-tight text-ink">
            {action.remediation.headline}
          </h2>
          <Body className="mt-2 text-ink-soft">
            {action.remediation.description}
          </Body>
        </div>
        <div className="text-right">
          <NumDisplay size="xl">
            {formatCurrency(action.estimated_premium_delta_usd)}
          </NumDisplay>
          <Micro>est. annual saving</Micro>
        </div>
      </header>

      <div className="grid grid-cols-2 gap-4 border-t border-info/30 pt-4 md:grid-cols-4">
        <MetaItem
          icon={Gauge}
          label="Leverage"
          value={`${action.leverage} / 5`}
        />
        <MetaItem
          icon={TrendingDown}
          label="Effort"
          value={action.remediation.effort}
        />
        <MetaItem
          icon={Clock}
          label="Duration"
          value={action.remediation.typical_duration}
        />
        <MetaItem
          icon={FileCheck2}
          label="Typical cost"
          value={
            action.remediation.typical_cost_usd > 0
              ? formatCurrency(action.remediation.typical_cost_usd)
              : "—"
          }
        />
      </div>

      {action.remediation.evidence_required && (
        <div className="rounded-card border border-info/30 bg-surface px-4 py-3">
          <Eyebrow className="mb-1">Evidence required</Eyebrow>
          <Body className="text-ink">{action.remediation.evidence_required}</Body>
        </div>
      )}

      {action.remediation.references.length > 0 && (
        <div className="flex flex-wrap items-center gap-2 text-[12.5px]">
          <Micro>References:</Micro>
          {action.remediation.references.map((r, i) => (
            <a
              key={i}
              href={r}
              target="_blank"
              rel="noreferrer"
              className="inline-flex items-center gap-1 text-info hover:underline"
            >
              {new URL(r, "https://x").hostname.replace(/^x$/, r)}
              <ExternalLink size={11} />
            </a>
          ))}
        </div>
      )}
    </Card>
  );
}

function SupportingAction({ action }: { action: RemediationAction }) {
  return (
    <Card pad="md" className="space-y-3">
      <header>
        <Eyebrow>{action.signal_label}</Eyebrow>
        <h3 className="mt-1 text-[15px] font-semibold leading-snug text-ink">
          {action.remediation.headline}
        </h3>
      </header>
      <Body className="text-[13px]">
        {action.remediation.description}
      </Body>
      <div className="flex items-center justify-between border-t border-rule pt-3">
        <span className="text-[13px] font-semibold tabular-nums text-pos">
          {formatCurrency(action.estimated_premium_delta_usd)}
        </span>
        <div className="flex items-center gap-1.5">
          <EffortChip effort={action.remediation.effort} />
          <Chip variant="mute" size="sm">
            <Clock size={10} />
            {action.remediation.typical_duration}
          </Chip>
        </div>
      </div>
    </Card>
  );
}

function MetaItem({
  icon: Icon,
  label,
  value,
}: {
  icon: typeof Lightbulb;
  label: string;
  value: string;
}) {
  return (
    <div>
      <div className="flex items-center gap-1.5">
        <Icon size={13} className="text-ink-mute" />
        <Micro>{label}</Micro>
      </div>
      <p className="mt-1 text-[14px] font-semibold text-ink">{value}</p>
    </div>
  );
}

function EffortChip({ effort }: { effort: "LOW" | "MEDIUM" | "HIGH" }) {
  const variant = effort === "LOW" ? "pos" : effort === "MEDIUM" ? "warn" : "neg";
  return (
    <Chip variant={variant} size="sm">
      {effort.toLowerCase()}
    </Chip>
  );
}

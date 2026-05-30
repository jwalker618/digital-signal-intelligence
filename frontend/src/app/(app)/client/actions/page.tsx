// No direct design counterpart; adapted from reim_broker_recs.jsx (per-client recommendation rows).
"use client";

import Link from "next/link";
import { Suspense } from "react";
import { useSearchParams } from "next/navigation";
import {
  Briefcase,
  Clock,
  ExternalLink,
  Info,
  Send,
} from "lucide-react";
import { Topbar } from "@/components/chrome/topbar";
import { Card } from "@/components/ui/card";
import { Chip } from "@/components/ui/chip";
import { Button } from "@/components/ui/button";
import { Eyebrow, Body, Micro, Caption } from "@/components/ui/typography";
import { KpiSnug } from "@/components/ui/kpi-snug";
import { PageError, PageLoading, RoleGate } from "@/components/base/pageStates";
import { useRoleScopedFetch } from "@/lib/useRoleScopedFetch";
import { fetchOverview, fetchSubmissionActions } from "@/lib/portalApi";
import { useAuthStore } from "@/store/authStore";
import { formatCurrency } from "@/lib/format";
import type {
  ActionsResponse,
  OverviewResponse,
  RemediationAction,
  RemediationEffort,
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
    <ActionsBody entityName={overview.data.entity_name} data={actions.data} />
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
    if (b.leverage !== a.leverage) return b.leverage - a.leverage;
    return (
      Math.abs(b.estimated_premium_delta_usd) -
      Math.abs(a.estimated_premium_delta_usd)
    );
  });
  const real = sorted.filter((a) => !a.is_placeholder);
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
        <div className="grid gap-4">
          {/* ────────── title + KPI strip ────────── */}
          <div className="flex flex-wrap items-end justify-between gap-6">
            <div className="max-w-xl">
              <Eyebrow>Action plan</Eyebrow>
              <h1 className="mt-1.5 font-display text-[32px] font-semibold leading-none tracking-tight text-ink">
                Concrete steps to move your premium
              </h1>
              <Caption className="mt-2 block max-w-[640px]">
                Ranked by leverage (impact ÷ effort). Each item links a signal
                in your apparatus to a concrete remediation — request it from
                your broker when you&apos;re ready.
              </Caption>
            </div>
            <div className="flex flex-wrap gap-7">
              <KpiSnug
                label="Actions identified"
                value={real.length}
                tone={real.length > 0 ? "spot" : "default"}
              />
              <KpiSnug label="Coverage" value={data.coverage} />
              <KpiSnug
                label="Potential annual saving"
                value={totalSavings < 0 ? formatCurrency(totalSavings) : "—"}
                tone={totalSavings < 0 ? "pos" : "default"}
              />
            </div>
          </div>

          {/* ────────── info bar ────────── */}
          <div className="flex items-center gap-3 rounded-card border border-rule bg-surface-sunken px-4 py-3">
            <Info size={16} className="shrink-0 text-ink-soft" />
            <Caption>
              Rules: every action below maps to one or more signals DSI already
              tracks in your apparatus. Closing the signal moves the carrier
              modifier; the dollar impact is the modelled annualised premium
              delta.
            </Caption>
          </div>

          {/* ────────── per-action cards ────────── */}
          {real.length === 0 ? (
            <Card variant="pos" pad="lg">
              <Eyebrow className="text-pos">Nothing to do</Eyebrow>
              <Body className="mt-2">
                Your signal apparatus is fully captured for this coverage —
                there&apos;s no concrete remediation to recommend right now.
              </Body>
            </Card>
          ) : (
            <div className="flex flex-col gap-3.5">
              {real.map((action, i) => (
                <ActionGroupCard
                  key={action.signal_key}
                  action={action}
                  rank={i + 1}
                />
              ))}
            </div>
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

function ActionGroupCard({
  action,
  rank,
}: {
  action: RemediationAction;
  rank: number;
}) {
  return (
    <Card pad="none" className="overflow-hidden">
      <div className="flex items-center justify-between gap-3 border-b border-rule bg-surface-elev px-5 py-3.5">
        <div className="flex items-center gap-3">
          <div className="flex h-8 w-8 items-center justify-center rounded-card border border-rule bg-surface">
            <Briefcase size={16} className="text-ink" />
          </div>
          <div>
            <p className="text-[15px] font-bold text-ink">
              #{rank} {action.signal_label}
            </p>
            <Micro>Leverage {action.leverage} / 5</Micro>
          </div>
        </div>
        <Chip variant="spot" size="md">
          {formatCurrency(action.estimated_premium_delta_usd)} potential
        </Chip>
      </div>
      <div className="grid grid-cols-1 items-center gap-5 px-5 py-4 lg:grid-cols-[1.4fr_1.4fr_1fr_auto]">
        <div>
          <p className="text-[14px] font-bold text-ink">
            {action.remediation.headline}
          </p>
          <Micro className="mt-1 block">
            <EffortLabel effort={action.remediation.effort} /> ·{" "}
            <Clock size={10} className="inline" />{" "}
            {action.remediation.typical_duration}
          </Micro>
        </div>
        <Caption className="leading-relaxed">
          {action.remediation.description}
        </Caption>
        <div className="text-right">
          <Micro className="block">Typical cost</Micro>
          <p className="mt-0.5 text-[15px] font-bold tabular-nums text-ink">
            {action.remediation.typical_cost_usd > 0
              ? formatCurrency(action.remediation.typical_cost_usd)
              : "—"}
          </p>
        </div>
        <Link href="/client/communications">
          <Button variant="spot" size="md">
            <Send size={13} /> Send to broker
          </Button>
        </Link>
      </div>
      {(action.remediation.evidence_required ||
        action.remediation.references.length > 0) && (
        <div className="flex flex-wrap items-center gap-3 border-t border-rule bg-surface-sunken px-5 py-2.5">
          {action.remediation.evidence_required && (
            <Micro>
              <strong className="font-semibold">Evidence:</strong>{" "}
              {action.remediation.evidence_required}
            </Micro>
          )}
          {action.remediation.references.map((r, i) => (
            <a
              key={i}
              href={r}
              target="_blank"
              rel="noreferrer"
              className="inline-flex items-center gap-1 text-[11px] text-info hover:underline"
            >
              {hostOrPath(r)}
              <ExternalLink size={10} />
            </a>
          ))}
        </div>
      )}
    </Card>
  );
}

function hostOrPath(url: string): string {
  try {
    return new URL(url).hostname;
  } catch {
    return url;
  }
}

function EffortLabel({ effort }: { effort: RemediationEffort }) {
  const label =
    effort === "LOW"
      ? "Low effort"
      : effort === "MEDIUM"
        ? "Medium effort"
        : "High effort";
  return <span>{label}</span>;
}

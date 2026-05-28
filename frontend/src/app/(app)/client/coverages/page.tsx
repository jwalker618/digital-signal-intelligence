"use client";

import Link from "next/link";
import { ChevronRight, ShieldCheck } from "lucide-react";
import { Topbar } from "@/components/chrome/topbar";
import { Card } from "@/components/ui/card";
import { Chip } from "@/components/ui/chip";
import { Button } from "@/components/ui/button";
import { Eyebrow, Body, Micro, Caption } from "@/components/ui/typography";
import { KpiSnug } from "@/components/ui/kpi-snug";
import { PageError, PageLoading, RoleGate } from "@/components/base/pageStates";
import { useRoleScopedFetch } from "@/lib/useRoleScopedFetch";
import { fetchOverview } from "@/lib/portalApi";
import { useAuthStore } from "@/store/authStore";
import { formatCurrency, formatText } from "@/lib/format";
import { tierStatus, peerStanding } from "@/lib/portalTone";
import { portalToneToTone } from "@/lib/design-tokens";
import type {
  ClientCoverageEntry,
  ClientOverviewResponse,
  OverviewResponse,
} from "@/types/portal";

export default function ClientCoveragesPage() {
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
  if (!data || data.role !== "CLIENT") return <RoleGate expected="client" />;

  return <CoveragesBody data={data} />;
}

function CoveragesBody({ data }: { data: ClientOverviewResponse }) {
  const coverages = data.active_coverages;
  const totalPremium = coverages.reduce(
    (sum, c) => sum + (c.recommended_premium ?? 0),
    0,
  );
  const awaiting = coverages.filter(
    (c) => c.referral_state && /awaiting/i.test(c.referral_state),
  ).length;

  const grouped = new Map<string, ClientCoverageEntry[]>();
  for (const c of coverages) {
    const arr = grouped.get(c.coverage) ?? [];
    arr.push(c);
    grouped.set(c.coverage, arr);
  }
  const groups = Array.from(grouped.entries());
  const lineCount = groups.length;

  return (
    <>
      <Topbar
        crumbs={["Client Portal", "Coverages"]}
        entity={data.entity_name}
      />
      <div className="flex-1 overflow-y-auto px-9 py-7">
        <div className="mx-auto grid max-w-[1400px] gap-5">
          {/* ────────── ROW 1 — title + KPI strip ────────── */}
          <div className="flex flex-wrap items-end justify-between gap-6">
            <div className="max-w-xl">
              <Eyebrow>Coverages</Eyebrow>
              <h1 className="mt-1.5 font-display text-[32px] font-semibold leading-none tracking-tight text-ink">
                Your active book at a glance
              </h1>
              <Body className="mt-2">
                All policies currently in force, grouped by line. Status, peer
                standing, and the next action are surfaced for each.
              </Body>
            </div>
            <div className="flex flex-wrap items-start gap-7">
              <KpiSnug label="Policies" value={coverages.length} />
              <KpiSnug label="Lines" value={lineCount} />
              <KpiSnug
                label="Annual premium"
                value={totalPremium > 0 ? formatCurrency(totalPremium) : "—"}
              />
              <KpiSnug
                label="Awaiting you"
                value={awaiting}
                tone={awaiting > 0 ? "spot" : "default"}
              />
            </div>
          </div>

          {/* ────────── ROW 2 — filter bar ────────── */}
          <div className="flex items-center gap-2">
            <Micro className="mr-1">Filter:</Micro>
            <span className="inline-flex items-center gap-1.5 rounded-chip bg-ink px-2.5 py-1 text-[11.5px] font-medium text-canvas">
              All lines
            </span>
            {groups.slice(0, 4).map(([line]) => (
              <Chip key={line} variant="mute" size="md">
                {line}
              </Chip>
            ))}
            <div className="flex-1" />
            <Caption>Sort: by premium</Caption>
          </div>

          {/* ────────── ROW 3 — per-line cards ────────── */}
          {coverages.length === 0 ? (
            <Card pad="lg" className="flex items-center justify-between gap-4">
              <div>
                <Eyebrow>No active coverages</Eyebrow>
                <Body className="mt-2">
                  Your broker hasn&apos;t placed any coverages on this portal yet.
                </Body>
              </div>
              <Link href="/client/request">
                <Button variant="primary">
                  <ShieldCheck size={15} />
                  Request coverage
                </Button>
              </Link>
            </Card>
          ) : (
            <div className="flex flex-col gap-3.5">
              {groups.map(([line, policies]) => (
                <LineGroupCard key={line} line={line} policies={policies} />
              ))}
            </div>
          )}
        </div>
      </div>
    </>
  );
}

function LineGroupCard({
  line,
  policies,
}: {
  line: string;
  policies: ClientCoverageEntry[];
}) {
  const total = policies.reduce(
    (sum, p) => sum + (p.recommended_premium ?? 0),
    0,
  );
  return (
    <Card pad="none" className="overflow-hidden">
      <div className="flex items-center justify-between gap-3 border-b border-rule bg-surface-elev px-5 py-3.5">
        <div className="flex items-center gap-3">
          <div className="flex h-8 w-8 items-center justify-center rounded-card border border-rule bg-surface">
            <ShieldCheck size={16} className="text-ink" />
          </div>
          <h3 className="font-display text-[17px] font-semibold leading-none text-ink">
            {line}
          </h3>
          <Chip variant="mute" size="sm">
            {policies.length} polic{policies.length === 1 ? "y" : "ies"}
          </Chip>
        </div>
        <Caption>
          Total {total > 0 ? formatCurrency(total) : "—"}
        </Caption>
      </div>
      {policies.map((p) => (
        <PolicyRow key={p.submission_code} policy={p} />
      ))}
    </Card>
  );
}

function PolicyRow({ policy }: { policy: ClientCoverageEntry }) {
  const tone = tierStatus(policy.tier);
  const chipTone = portalToneToTone(tone.tone);
  const awaiting =
    policy.referral_state && /awaiting/i.test(policy.referral_state);

  return (
    <Link
      href={`/client/submissions/${policy.submission_code}`}
      className="grid grid-cols-[1.4fr_1fr_0.9fr_1fr_24px] items-center gap-4 border-t border-rule px-5 py-4 transition hover:bg-surface-sunken/40"
    >
      <div className="min-w-0">
        <p className="truncate text-[14px] font-semibold text-ink">
          {policy.submission_code}
        </p>
        <Micro>{peerStanding(policy.peer_percentile_rank)}</Micro>
      </div>
      <div>
        <Micro className="block">Signal score</Micro>
        <p className="mt-0.5 text-[18px] font-semibold tabular-nums leading-none text-info">
          {policy.composite_score != null
            ? policy.composite_score.toFixed(0)
            : "—"}
        </p>
      </div>
      <div>
        <Chip variant={awaiting ? "spot" : chipTone} size="sm">
          {awaiting
            ? formatText(policy.referral_state, "capitalize")
            : tone.label}
        </Chip>
      </div>
      <div className="text-right">
        <Micro className="block">Premium</Micro>
        <p className="mt-0.5 text-[16px] font-bold tabular-nums leading-none text-ink">
          {policy.recommended_premium != null
            ? `$${(policy.recommended_premium / 1000).toFixed(0)}k`
            : "—"}
        </p>
      </div>
      <ChevronRight size={18} className="text-ink-mute" />
    </Link>
  );
}

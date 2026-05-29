"use client";

import Link from "next/link";
import {
  Building2,
  Check,
  CheckCircle2,
  ChevronRight,
  Circle,
  Cpu,
  Globe,
  Lock,
} from "lucide-react";
import { Topbar } from "@/components/chrome/topbar";
import { Card } from "@/components/ui/card";
import { Chip } from "@/components/ui/chip";
import { Eyebrow, NumDisplay, Body, Micro, Caption } from "@/components/ui/typography";
import { PageError, PageLoading, RoleGate } from "@/components/base/pageStates";
import { useRoleScopedFetch } from "@/lib/useRoleScopedFetch";
import { fetchClientProfile, fetchOverview } from "@/lib/portalApi";
import { useAuthStore } from "@/store/authStore";
import { formatCurrency, formatText } from "@/lib/format";
import { cn } from "@/lib/utils";
import type {
  ClientCoverageEntry,
  ClientProfileResponse,
  OverviewResponse,
} from "@/types/portal";

export default function ClientProfilePage() {
  const accessToken = useAuthStore((s) => s.accessToken);
  const user = useAuthStore((s) => s.user);
  const enabled = !!accessToken && user?.role === "CLIENT";

  const profile = useRoleScopedFetch<ClientProfileResponse>({
    fetcher: () => fetchClientProfile(accessToken),
    enabled,
    deps: [accessToken],
  });
  const overview = useRoleScopedFetch<OverviewResponse>({
    fetcher: () => fetchOverview(accessToken),
    enabled,
    deps: [accessToken],
  });

  if (!user) return <PageLoading message="Signing in…" />;
  if (user.role && user.role !== "CLIENT") return <RoleGate expected="client" />;
  if (profile.loading || overview.loading) return <PageLoading />;
  if (profile.error) return <PageError message={profile.error} />;
  if (overview.error) return <PageError message={overview.error} />;
  if (!profile.data || !overview.data) return <PageLoading />;
  if (overview.data.role !== "CLIENT") return <RoleGate expected="client" />;

  return <ProfileBody profile={profile.data} coverages={overview.data.active_coverages} />;
}

interface FactRow {
  label: string;
  value: React.ReactNode;
}

function ProfileBody({
  profile,
  coverages,
}: {
  profile: ClientProfileResponse;
  coverages: ClientCoverageEntry[];
}) {
  const captured = profile.signal_categories_observed;
  const pending = profile.signal_categories_pending;
  const total = captured.length + pending.length;
  const completion = total > 0 ? captured.length / total : 0;
  const totalPremium = coverages.reduce(
    (sum, c) => sum + (c.recommended_premium ?? 0),
    0,
  );

  const facts: FactRow[] = [
    { label: "Legal entity", value: profile.entity_name },
    profile.domain && { label: "Domain", value: profile.domain },
    profile.country && { label: "Country", value: profile.country },
    profile.naics_code && {
      label: "NAICS",
      value: (
        <>
          <span className="font-mono">{profile.naics_code}</span>
          {profile.industry_label && (
            <span className="ml-1 text-ink-mute">— {profile.industry_label}</span>
          )}
        </>
      ),
    },
    profile.revenue_band && { label: "Revenue band", value: profile.revenue_band },
    profile.broker_name && { label: "Broker of record", value: profile.broker_name },
  ].filter(Boolean) as FactRow[];

  return (
    <>
      <Topbar
        crumbs={["Client Portal", "Your Profile"]}
        entity={profile.entity_name}
      />
      <div className="flex-1 overflow-y-auto px-9 py-7">
        <div className="mx-auto grid max-w-[1280px] gap-4">
          {/* ────────── ROW 1 — identity hero + signal apparatus ────────── */}
          <div className="grid gap-4 lg:grid-cols-[1.6fr_1fr]">
            <Card pad="lg" className="flex items-center gap-6">
              <div className="flex h-[72px] w-[72px] shrink-0 items-center justify-center rounded-card bg-info-soft text-info-deep dark:text-info">
                <Cpu size={36} />
              </div>
              <div className="min-w-0 flex-1">
                <Eyebrow>Insured</Eyebrow>
                <h2 className="mt-1 font-display text-[28px] font-semibold leading-tight tracking-tight text-ink">
                  {profile.entity_name}
                </h2>
                <Caption className="mt-1.5 block">
                  {[
                    profile.industry_label,
                    profile.naics_code && `NAICS ${profile.naics_code}`,
                    profile.country,
                    profile.revenue_band,
                  ]
                    .filter(Boolean)
                    .join(" · ")}
                </Caption>
                <div className="mt-3 flex flex-wrap gap-2">
                  {profile.broker_name && (
                    <Chip variant="mute" size="sm">
                      <Building2 size={11} /> {profile.broker_name}, broker
                    </Chip>
                  )}
                  <Chip variant="pos" size="sm">
                    <Check size={11} /> {profile.active_coverage_count} polic
                    {profile.active_coverage_count === 1 ? "y" : "ies"} active
                  </Chip>
                  {profile.country && (
                    <Chip variant="mute" size="sm">
                      <Globe size={11} /> {profile.country}
                    </Chip>
                  )}
                </div>
              </div>
            </Card>

            <Card variant="info" pad="lg">
              <Eyebrow className="text-info-deep dark:text-info">
                Signal apparatus
              </Eyebrow>
              <div className="mt-2 flex items-baseline gap-3">
                <NumDisplay size="xl" className="text-info">
                  {total > 0 ? `${captured.length}/${total}` : "—"}
                </NumDisplay>
                <Caption>categories captured</Caption>
              </div>
              <div className="mt-3 h-1.5 overflow-hidden rounded-full bg-info/15">
                <div
                  className="h-full rounded-full bg-info"
                  style={{ width: `${completion * 100}%` }}
                />
              </div>
              <Caption className="mt-2.5 block">
                {pending.length > 0
                  ? `${pending.length} categor${pending.length === 1 ? "y" : "ies"} pending — see below for what would strengthen the picture.`
                  : "Every category captured."}
              </Caption>
            </Card>
          </div>

          {/* ────────── ROW 2 — identity facts + active coverage lines ────────── */}
          <div className="grid gap-4 lg:grid-cols-[1fr_1.3fr]">
            <Card pad="lg">
              <Eyebrow>Identity</Eyebrow>
              <h3 className="mt-1.5 font-display text-[17px] font-semibold leading-tight text-ink">
                Registered details
              </h3>
              <div className="mt-3.5 flex flex-col">
                {facts.map((f, i) => (
                  <div
                    key={f.label}
                    className={cn(
                      "flex items-baseline justify-between gap-3 py-2",
                      i < facts.length - 1 && "border-b border-rule",
                    )}
                  >
                    <Micro>{f.label}</Micro>
                    <span className="text-right text-[13px] font-semibold text-ink">
                      {f.value}
                    </span>
                  </div>
                ))}
              </div>
            </Card>

            <Card pad="lg">
              <div className="flex items-baseline justify-between">
                <div>
                  <Eyebrow>Active coverage lines</Eyebrow>
                  <h3 className="mt-1.5 font-display text-[17px] font-semibold leading-tight text-ink">
                    What you currently hold
                  </h3>
                </div>
                <Caption>
                  {coverages.length} line{coverages.length === 1 ? "" : "s"}
                  {totalPremium > 0 && ` · ${formatCurrency(totalPremium)} total`}
                </Caption>
              </div>
              <div className="mt-3.5 flex flex-col gap-2.5">
                {coverages.length === 0 ? (
                  <Body className="italic">No coverages on file yet.</Body>
                ) : (
                  coverages.map((c) => (
                    <Link
                      key={c.submission_code}
                      href={`/client/submissions/${c.submission_code}`}
                      className="grid grid-cols-[1fr_80px_100px_18px] items-center gap-3 rounded-card border border-rule bg-surface-elev px-3.5 py-2.5 transition hover:border-rule-strong"
                    >
                      <div className="min-w-0">
                        <p className="truncate text-[14px] font-semibold text-ink">
                          {c.coverage}
                        </p>
                        <Micro>
                          {c.tier != null ? `Tier ${c.tier}` : c.submission_code}
                        </Micro>
                      </div>
                      <Chip variant="pos" size="sm" className="justify-self-start">
                        Active
                      </Chip>
                      <span className="text-right text-[13px] font-semibold tabular-nums text-ink">
                        {c.recommended_premium != null
                          ? `$${(c.recommended_premium / 1000).toFixed(0)}k`
                          : "—"}
                      </span>
                      <ChevronRight size={16} className="text-ink-mute" />
                    </Link>
                  ))
                )}
              </div>
            </Card>
          </div>

          {/* ────────── ROW 3 — signal apparatus detail ────────── */}
          <Card pad="lg">
            <div className="mb-3.5 flex items-baseline justify-between">
              <div>
                <Eyebrow>Signal apparatus</Eyebrow>
                <h3 className="mt-1.5 font-display text-[17px] font-semibold leading-tight text-ink">
                  What DSI observes about you
                </h3>
                <Caption className="mt-1 block">
                  Captured categories contributed to your current quote; pending
                  categories would strengthen the picture if data became available.
                </Caption>
              </div>
            </div>
            <div className="grid gap-4 md:grid-cols-2">
              <div>
                <Chip variant="pos" size="sm" className="mb-2.5">
                  <CheckCircle2 size={12} /> Captured · {captured.length} categor
                  {captured.length === 1 ? "y" : "ies"}
                </Chip>
                {captured.length === 0 ? (
                  <Body className="italic">No categories captured yet.</Body>
                ) : (
                  <div className="grid gap-2 sm:grid-cols-2">
                    {captured.map((c) => (
                      <div
                        key={c}
                        className="flex items-center gap-2 rounded-card border border-pos-soft bg-pos-soft/60 px-3 py-2.5 text-[13px] text-ink"
                      >
                        <CheckCircle2 size={14} className="shrink-0 text-pos" />
                        <span>{formatText(c, "capitalize")}</span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
              <div>
                <Chip variant="spot" size="sm" className="mb-2.5">
                  <Circle size={12} /> Pending · {pending.length} categor
                  {pending.length === 1 ? "y" : "ies"}
                </Chip>
                {pending.length === 0 ? (
                  <Body className="italic">All categories captured.</Body>
                ) : (
                  <div className="flex flex-col gap-2">
                    {pending.map((c) => (
                      <div
                        key={c}
                        className="flex items-center justify-between gap-2 rounded-card border border-dashed border-spot px-3.5 py-3 text-[13px] text-ink"
                      >
                        <span className="flex items-center gap-2.5">
                          <Circle size={14} className="shrink-0 text-spot" />
                          {formatText(c, "capitalize")}
                        </span>
                        <Link
                          href="/client/communications"
                          className="text-[12px] font-semibold text-spot-deep dark:text-spot hover:underline"
                        >
                          Share with broker →
                        </Link>
                      </div>
                    ))}
                    <Caption className="mt-1">
                      Sharing these would close additional headroom signals on
                      your renewal.
                    </Caption>
                  </div>
                )}
              </div>
            </div>
          </Card>

          {/* ────────── ROW 4 — privacy ────────── */}
          <div className="flex items-start gap-3 rounded-card border border-rule bg-surface-sunken px-4 py-3.5">
            <Lock size={18} className="mt-0.5 shrink-0 text-ink-soft" />
            <div>
              <p className="text-[12.5px] font-semibold text-ink">Privacy</p>
              <Caption className="mt-0.5 block leading-relaxed">
                Your DSI profile is built from publicly-observable signals and
                information you&apos;ve shared through your broker. We never use
                your data to make decisions affecting other clients, and you can
                request the full audit trail of any signal at any time.
              </Caption>
            </div>
          </div>
        </div>
      </div>
    </>
  );
}

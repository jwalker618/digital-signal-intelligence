"use client";

import { Building2, CheckCircle2, Globe, MapPin, Hash, Banknote, ShieldCheck, Circle } from "lucide-react";
import { Topbar } from "@/components/chrome/topbar";
import { Card } from "@/components/ui/card";
import { Chip } from "@/components/ui/chip";
import { Eyebrow, NumDisplay, Body, Micro } from "@/components/ui/typography";
import { LabelRow } from "@/components/ui/label-row";
import { PageError, PageLoading, RoleGate } from "@/components/base/pageStates";
import { useRoleScopedFetch } from "@/lib/useRoleScopedFetch";
import { fetchClientProfile } from "@/lib/portalApi";
import { useAuthStore } from "@/store/authStore";
import { formatCurrency, formatText } from "@/lib/format";
import type { ClientProfileResponse } from "@/types/portal";
import { cn } from "@/lib/utils";

export default function ClientProfilePage() {
  const accessToken = useAuthStore((s) => s.accessToken);
  const user = useAuthStore((s) => s.user);
  const enabled = !!accessToken && user?.role === "CLIENT";

  const { data, error, loading } = useRoleScopedFetch<ClientProfileResponse>({
    fetcher: () => fetchClientProfile(accessToken),
    enabled,
    deps: [accessToken],
  });

  if (!user) return <PageLoading message="Signing in…" />;
  if (user.role && user.role !== "CLIENT") return <RoleGate expected="client" />;
  if (loading) return <PageLoading />;
  if (error) return <PageError message={error} />;
  if (!data) return <PageLoading />;

  return <ProfileBody data={data} />;
}

function ProfileBody({ data }: { data: ClientProfileResponse }) {
  const captured = data.signal_categories_observed;
  const pending = data.signal_categories_pending;
  const total = captured.length + pending.length;
  const completion = total > 0 ? captured.length / total : 0;

  return (
    <>
      <Topbar
        crumbs={["Client Portal", "Your Profile"]}
        entity={data.entity_name}
      />
      <div className="flex-1 overflow-y-auto px-9 py-7">
        <div className="mx-auto grid max-w-[1280px] gap-6">
          {/* Identity */}
          <Card pad="lg" className="space-y-5">
            <div className="flex items-start justify-between gap-6">
              <div>
                <Eyebrow>Insured</Eyebrow>
                <h1 className="mt-1.5 font-display text-[32px] font-semibold leading-none tracking-tight text-ink">
                  {data.entity_name}
                </h1>
                {data.industry_label && (
                  <Body className="mt-2">{data.industry_label}</Body>
                )}
              </div>
              {data.broker_name && (
                <div className="text-right">
                  <Micro>Broker of record</Micro>
                  <p className="mt-1 text-[14px] font-semibold text-ink">
                    {data.broker_name}
                  </p>
                </div>
              )}
            </div>

            <div className="grid gap-x-8 gap-y-3 border-t border-rule pt-5 md:grid-cols-2">
              {data.domain && (
                <DetailRow icon={Globe} label="Domain" value={data.domain} />
              )}
              {data.country && (
                <DetailRow icon={MapPin} label="Country" value={data.country} />
              )}
              {data.naics_code && (
                <DetailRow
                  icon={Hash}
                  label="NAICS code"
                  value={
                    <>
                      <span className="font-mono">{data.naics_code}</span>
                      {data.industry_code && data.industry_code !== data.naics_code && (
                        <span className="ml-2 text-ink-mute">· {data.industry_code}</span>
                      )}
                    </>
                  }
                />
              )}
              {data.revenue_band && (
                <DetailRow
                  icon={Banknote}
                  label="Revenue"
                  value={
                    <>
                      <span>{data.revenue_band}</span>
                      {data.revenue && (
                        <span className="ml-2 text-ink-mute">
                          · {formatCurrency(data.revenue)}
                        </span>
                      )}
                    </>
                  }
                />
              )}
              <DetailRow
                icon={ShieldCheck}
                label="Active coverages"
                value={`${data.active_coverage_count} polic${data.active_coverage_count === 1 ? "y" : "ies"}`}
              />
              {data.coverage_lines.length > 0 && (
                <DetailRow
                  icon={Building2}
                  label="Lines"
                  value={
                    <span className="flex flex-wrap gap-1.5">
                      {data.coverage_lines.map((l) => (
                        <Chip key={l} variant="mute" size="sm">
                          {l}
                        </Chip>
                      ))}
                    </span>
                  }
                />
              )}
            </div>
          </Card>

          {/* Signal apparatus */}
          <Card variant="info" pad="lg" className="space-y-5">
            <div className="flex items-end justify-between gap-6">
              <div>
                <Eyebrow>Signal apparatus</Eyebrow>
                <h2 className="mt-1 font-display text-[24px] font-semibold leading-tight text-ink">
                  {captured.length} of {total} signal categories captured
                </h2>
                <Body className="mt-1.5">
                  Each captured category strengthens your composite score and
                  unlocks finer-grained peer comparison.
                </Body>
              </div>
              <div className="text-right">
                <NumDisplay size="xl">
                  {Math.round(completion * 100)}%
                </NumDisplay>
                <Micro>complete</Micro>
              </div>
            </div>
            <div className="h-2 overflow-hidden rounded-full bg-info/15">
              <div
                className="h-full rounded-full bg-info"
                style={{ width: `${completion * 100}%` }}
              />
            </div>
          </Card>

          {/* Captured / Pending split */}
          <div className="grid gap-5 md:grid-cols-2">
            <SignalList
              title="Captured"
              accent="pos"
              items={captured}
              empty="No signal categories captured yet."
            />
            <SignalList
              title="Pending"
              accent="spot"
              items={pending}
              empty="All signal categories captured. 🎉"
            />
          </div>
        </div>
      </div>
    </>
  );
}

function DetailRow({
  icon: Icon,
  label,
  value,
}: {
  icon: typeof Building2;
  label: string;
  value: React.ReactNode;
}) {
  return (
    <div className="flex items-start gap-3">
      <Icon size={15} className="mt-0.5 shrink-0 text-ink-mute" />
      <div className="min-w-0 flex-1">
        <Micro className="block">{label}</Micro>
        <div className="mt-0.5 text-[13.5px] text-ink">{value}</div>
      </div>
    </div>
  );
}

function SignalList({
  title,
  accent,
  items,
  empty,
}: {
  title: string;
  accent: "pos" | "spot";
  items: string[];
  empty: string;
}) {
  return (
    <Card pad="md" className="space-y-3">
      <header className="flex items-center justify-between">
        <Eyebrow>{title}</Eyebrow>
        <span
          className={cn(
            "text-[13px] font-semibold tabular-nums",
            accent === "pos" ? "text-pos" : "text-spot",
          )}
        >
          {items.length}
        </span>
      </header>
      {items.length === 0 ? (
        <Body className="italic">{empty}</Body>
      ) : (
        <ul className="space-y-1.5">
          {items.map((c) => (
            <li
              key={c}
              className="flex items-center gap-2 text-[13.5px] text-ink"
            >
              {accent === "pos" ? (
                <CheckCircle2 size={14} className="shrink-0 text-pos" />
              ) : (
                <Circle size={14} className="shrink-0 text-spot" />
              )}
              <span>{formatText(c, "capitalize")}</span>
            </li>
          ))}
        </ul>
      )}
    </Card>
  );
}

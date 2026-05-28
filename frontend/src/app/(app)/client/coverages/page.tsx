"use client";

import Link from "next/link";
import { ChevronRight, ShieldCheck } from "lucide-react";
import { Topbar } from "@/components/chrome/topbar";
import { Card } from "@/components/ui/card";
import { Chip } from "@/components/ui/chip";
import { Eyebrow, NumDisplay, Body, Micro } from "@/components/ui/typography";
import { Button } from "@/components/ui/button";
import { ScoreBar } from "@/components/ui/score-bar";
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
  const meanScore =
    coverages.length > 0
      ? coverages.reduce((sum, c) => sum + (c.composite_score ?? 0), 0) /
        coverages.length
      : 0;
  const awaiting = coverages.filter(
    (c) => c.referral_state && /awaiting/i.test(c.referral_state),
  ).length;

  return (
    <>
      <Topbar
        crumbs={["Client Portal", "Coverages"]}
        entity={data.entity_name}
      />
      <div className="flex-1 overflow-y-auto px-9 py-7">
        <div className="mx-auto grid max-w-[1280px] gap-6">
          <header className="flex items-end justify-between gap-6">
            <div>
              <Eyebrow>Active coverages</Eyebrow>
              <h1 className="mt-1.5 font-display text-[32px] font-semibold leading-none tracking-tight text-ink">
                {coverages.length} polic{coverages.length === 1 ? "y" : "ies"} in force
              </h1>
            </div>
            <Link href="/client/request">
              <Button variant="primary">
                <ShieldCheck size={15} />
                Request coverage
              </Button>
            </Link>
          </header>

          <div className="grid gap-4 sm:grid-cols-3">
            <SummaryTile label="Total premium" emphasis>
              {formatCurrency(totalPremium)}
            </SummaryTile>
            <SummaryTile label="Mean composite score">
              {meanScore > 0 ? meanScore.toFixed(0) : "—"}
            </SummaryTile>
            <SummaryTile label="Awaiting action" emphasis={awaiting > 0}>
              {awaiting}
            </SummaryTile>
          </div>

          {coverages.length === 0 ? (
            <Card pad="lg">
              <Eyebrow>No active coverages</Eyebrow>
              <Body className="mt-2">
                Your broker hasn't placed any coverages on this portal yet.
              </Body>
            </Card>
          ) : (
            <Card pad="md" className="overflow-hidden p-0">
              <table className="w-full table-fixed text-[13px]">
                <thead>
                  <tr className="border-b border-rule bg-surface-sunken text-left">
                    <ColHead width="w-[24%]">Coverage</ColHead>
                    <ColHead width="w-[14%]">Score</ColHead>
                    <ColHead width="w-[18%]">Position</ColHead>
                    <ColHead width="w-[16%]">Premium</ColHead>
                    <ColHead width="w-[20%]">Status</ColHead>
                    <ColHead width="w-[8%]">{null}</ColHead>
                  </tr>
                </thead>
                <tbody>
                  {coverages.map((c) => (
                    <CoverageRow key={c.submission_code} entry={c} />
                  ))}
                </tbody>
              </table>
            </Card>
          )}
        </div>
      </div>
    </>
  );
}

function ColHead({
  width,
  children,
}: {
  width: string;
  children: React.ReactNode;
}) {
  return (
    <th
      className={`px-4 py-2.5 text-[11px] font-semibold uppercase tracking-[0.08em] text-ink-mute ${width}`}
    >
      {children}
    </th>
  );
}

function CoverageRow({ entry }: { entry: ClientCoverageEntry }) {
  const tone = tierStatus(entry.tier);
  const chipTone = portalToneToTone(tone.tone);
  const awaiting = entry.referral_state && /awaiting/i.test(entry.referral_state);

  return (
    <tr className="border-b border-rule last:border-0 hover:bg-surface-sunken/40">
      <td className="px-4 py-3.5">
        <Link
          href={`/client/submissions/${entry.submission_code}`}
          className="block"
        >
          <p className="font-semibold text-ink">{entry.coverage}</p>
          <Micro className="mt-0.5 block font-mono">
            {entry.submission_code}
          </Micro>
        </Link>
      </td>
      <td className="px-4 py-3.5">
        {entry.composite_score != null ? (
          <div className="space-y-1">
            <span className="font-semibold tabular-nums text-ink">
              {entry.composite_score.toFixed(0)}
            </span>
            <ScoreBar
              value={entry.composite_score}
              max={1000}
              showValue={false}
              thresholds={[
                { at: 400, tone: "neg" },
                { at: 650, tone: "warn" },
                { at: 800, tone: "info" },
                { at: 1000, tone: "pos" },
              ]}
            />
          </div>
        ) : (
          <span className="text-ink-mute">—</span>
        )}
      </td>
      <td className="px-4 py-3.5 text-ink-soft">
        {peerStanding(entry.peer_percentile_rank)}
      </td>
      <td className="px-4 py-3.5">
        <span className="font-semibold tabular-nums text-ink">
          {entry.recommended_premium != null
            ? formatCurrency(entry.recommended_premium)
            : "—"}
        </span>
      </td>
      <td className="px-4 py-3.5">
        <div className="flex items-center gap-2">
          <Chip variant={awaiting ? "spot" : chipTone} size="sm">
            {awaiting
              ? formatText(entry.referral_state, "capitalize")
              : tone.label}
          </Chip>
        </div>
      </td>
      <td className="px-4 py-3.5 text-right">
        <Link
          href={`/client/submissions/${entry.submission_code}`}
          className="inline-flex items-center text-ink-mute hover:text-ink"
          aria-label={`Open ${entry.coverage} detail`}
        >
          <ChevronRight size={16} />
        </Link>
      </td>
    </tr>
  );
}

function SummaryTile({
  label,
  children,
  emphasis,
}: {
  label: string;
  children: React.ReactNode;
  emphasis?: boolean;
}) {
  return (
    <Card pad="md" variant={emphasis ? "info" : "default"}>
      <Micro className="block">{label}</Micro>
      <div className="mt-2">
        <NumDisplay size={emphasis ? "lg" : "md"}>{children}</NumDisplay>
      </div>
    </Card>
  );
}

"use client";

import { Building2 } from "lucide-react";
import { WorkbenchTopbar } from "@/components/chrome/workbench-topbar";
import { Card } from "@/components/ui/card";
import { Chip } from "@/components/ui/chip";
import { Eyebrow, NumDisplay, Body, Micro } from "@/components/ui/typography";
import { PageLoading } from "@/components/base/pageStates";
import { useDsiStore } from "@/store/dsiStore";
import { formatCurrency, formatPercent } from "@/lib/format";

/**
 * Distribution — how the premium and risk are shared across the commercial
 * entity stack. Reads from activeCommercial.commercial_distribution
 * (an array of participants).
 */
export default function DistributionPage() {
  const ver = useDsiStore((s) => s.activeVersion);
  const commercial = useDsiStore((s) => s.activeCommercial);
  const sub = useDsiStore((s) => s.activeSubmission);

  if (!sub) {
    return (
      <>
        <WorkbenchTopbar activeTabLabel="Distribution" />
        <PageLoading message="Loading distribution…" />
      </>
    );
  }

  const totalPremium = Number(ver?.final_premium ?? sub.final_premium ?? 0);
  const participants =
    (commercial?.commercial_distribution as
      | Array<Record<string, unknown>>
      | undefined) ?? [];

  const totalShare = participants.reduce((s, p) => {
    const share = p.share_pct ?? (p.share != null ? Number(p.share) * 100 : 0);
    return s + Number(share);
  }, 0);
  const totalCommission = participants.reduce(
    (s, p) => s + Number(p.commission_pct ?? 0) * Number(p.premium ?? 0) / 100,
    0,
  );

  return (
    <>
      <WorkbenchTopbar activeTabLabel="Distribution" />
      <div className="flex-1 overflow-y-auto px-9 py-7">
        <div className="mx-auto grid max-w-[1280px] gap-6">
          <header>
            <Eyebrow>Commercial</Eyebrow>
            <h1 className="mt-1 font-display text-[28px] font-semibold leading-tight text-ink">
              Distribution
            </h1>
            <Body className="mt-2">
              Premium share across participants in the commercial stack — who
              keeps what, who fronts, who reinsures.
            </Body>
          </header>

          {participants.length === 0 ? (
            <Card pad="lg">
              <Body className="italic">
                No commercial distribution recorded for this submission.
              </Body>
            </Card>
          ) : (
            <>
              {/* Hero stats */}
              <div className="grid gap-4 md:grid-cols-3">
                <Stat label="Participants">{participants.length}</Stat>
                <Stat
                  label="Coverage of 100%"
                  tone={totalShare >= 99 && totalShare <= 101 ? "pos" : "warn"}
                >
                  {totalShare.toFixed(1)}%
                </Stat>
                <Stat label="Total commission" emphasis>
                  {formatCurrency(totalCommission)}
                </Stat>
              </div>

              {/* Stacked share bar */}
              <Card pad="md">
                <Eyebrow className="mb-3">Share stack</Eyebrow>
                <ShareStack participants={participants} />
              </Card>

              {/* Per-participant rows */}
              <Card pad="md" className="overflow-hidden p-0">
                <header className="border-b border-rule px-5 py-3.5">
                  <Eyebrow>Participants</Eyebrow>
                </header>
                <table className="w-full table-fixed text-[13px]">
                  <thead>
                    <tr className="border-b border-rule bg-surface-sunken/60 text-left">
                      <ColHead width="w-[26%]">Name</ColHead>
                      <ColHead width="w-[14%]">Role</ColHead>
                      <ColHead width="w-[12%]">Share</ColHead>
                      <ColHead width="w-[18%]">Premium</ColHead>
                      <ColHead width="w-[14%]">Commission</ColHead>
                      <ColHead width="w-[16%]">Layer / line</ColHead>
                    </tr>
                  </thead>
                  <tbody>
                    {participants.map((p, i) => {
                      const share = Number(
                        p.share_pct ??
                          (p.share != null ? Number(p.share) * 100 : 0),
                      );
                      const premium = Number(p.premium ?? 0);
                      return (
                        <tr
                          key={String(p.id ?? p.name ?? i)}
                          className="border-b border-rule last:border-0 hover:bg-surface-sunken/40"
                        >
                          <td className="px-5 py-2.5">
                            <div className="flex items-center gap-2">
                              <Building2 size={13} className="text-ink-mute" />
                              <span className="font-medium text-ink">
                                {String(p.name ?? p.carrier ?? "—")}
                              </span>
                            </div>
                          </td>
                          <td className="px-5 py-2.5">
                            <Chip variant="mute" size="sm">
                              {String(p.type ?? p.role ?? "Participant")}
                            </Chip>
                          </td>
                          <td className="px-5 py-2.5 tabular-nums text-ink">
                            {share.toFixed(1)}%
                          </td>
                          <td className="px-5 py-2.5 font-semibold tabular-nums text-ink">
                            {p.premium != null
                              ? formatCurrency(premium)
                              : totalPremium > 0
                                ? formatCurrency((share / 100) * totalPremium)
                                : "—"}
                          </td>
                          <td className="px-5 py-2.5 tabular-nums text-ink-soft">
                            {p.commission_pct != null
                              ? `${Number(p.commission_pct).toFixed(1)}%`
                              : "—"}
                          </td>
                          <td className="px-5 py-2.5 text-ink-soft">
                            {String(p.layer ?? p.line ?? "—")}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </Card>
            </>
          )}
        </div>
      </div>
    </>
  );
}

function ShareStack({
  participants,
}: {
  participants: Array<Record<string, unknown>>;
}) {
  const colors = [
    "var(--color-info)",
    "var(--color-pos)",
    "var(--color-aux)",
    "var(--color-warn)",
    "var(--color-spot)",
    "var(--color-ink-soft)",
  ];
  return (
    <>
      <div className="flex h-4 w-full overflow-hidden rounded-full bg-surface-sunken">
        {participants.map((p, i) => {
          const share = Number(
            p.share_pct ?? (p.share != null ? Number(p.share) * 100 : 0),
          );
          return (
            <div
              key={i}
              style={{
                width: `${share}%`,
                background: colors[i % colors.length],
              }}
              title={`${String(p.name ?? p.carrier ?? "—")} — ${share.toFixed(1)}%`}
            />
          );
        })}
      </div>
      <ul className="mt-3 grid grid-cols-2 gap-x-4 gap-y-1 text-[12px]">
        {participants.map((p, i) => {
          const share = Number(
            p.share_pct ?? (p.share != null ? Number(p.share) * 100 : 0),
          );
          return (
            <li key={i} className="flex items-center gap-2">
              <span
                className="inline-block h-2 w-2 rounded-full"
                style={{ background: colors[i % colors.length] }}
              />
              <span className="flex-1 text-ink-soft">
                {String(p.name ?? p.carrier ?? "—")}
              </span>
              <span className="font-semibold tabular-nums text-ink">
                {share.toFixed(1)}%
              </span>
            </li>
          );
        })}
      </ul>
    </>
  );
}

function Stat({
  label,
  tone,
  emphasis,
  children,
}: {
  label: string;
  tone?: "pos" | "warn";
  emphasis?: boolean;
  children: React.ReactNode;
}) {
  return (
    <Card pad="md" variant={emphasis ? "info" : tone === "warn" ? "warn" : "default"}>
      <Micro
        className={
          tone === "pos"
            ? "text-pos"
            : tone === "warn"
              ? "text-warn"
              : emphasis
                ? "text-info-deep dark:text-info"
                : ""
        }
      >
        {label}
      </Micro>
      <NumDisplay size={emphasis ? "lg" : "md"} className="mt-2 block">
        {children}
      </NumDisplay>
    </Card>
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
      className={`px-5 py-2.5 text-[11px] font-semibold uppercase tracking-[0.08em] text-ink-mute ${width}`}
    >
      {children}
    </th>
  );
}

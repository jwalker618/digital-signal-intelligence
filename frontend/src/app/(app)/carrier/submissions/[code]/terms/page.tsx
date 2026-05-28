"use client";

import { Building2 } from "lucide-react";
import { WorkbenchTopbar } from "@/components/chrome/workbench-topbar";
import { Card } from "@/components/ui/card";
import { Eyebrow, Body, Micro } from "@/components/ui/typography";
import { LabelRow } from "@/components/ui/label-row";
import { LooseRecordCard } from "@/components/base/loose-record";
import { PageLoading } from "@/components/base/pageStates";
import { useDsiStore } from "@/store/dsiStore";
import { formatCurrency, formatDate } from "@/lib/format";

/**
 * Terms Overview — high-level commercial terms (limit, retention, premium,
 * effective dates, commercial entity stack). Reads from `activeCommercial`
 * which is the response of /api/v1/commercialterms/{version_code}.
 */
export default function TermsOverviewPage() {
  const sub = useDsiStore((s) => s.activeSubmission);
  const ver = useDsiStore((s) => s.activeVersion);
  const commercial = useDsiStore((s) => s.activeCommercial);

  if (!sub) {
    return (
      <>
        <WorkbenchTopbar activeTabLabel="Terms Overview" />
        <PageLoading message="Loading commercial terms…" />
      </>
    );
  }

  const fpd = (ver?.final_premium_detail ?? {}) as Record<string, unknown>;
  const limit = fpd.limit ?? commercial?.limit ?? ver?.recommended_limit;
  const deductible = fpd.deductible ?? commercial?.deductible;
  const aggregate = fpd.aggregate ?? commercial?.aggregate_limit;
  const finalPremium = ver?.final_premium ?? sub.final_premium ?? null;
  const basePremium = ver?.base_premium ?? null;
  const effectiveFrom = commercial?.effective_from ?? ver?.effective_from;
  const effectiveTo = commercial?.effective_to ?? ver?.effective_to;
  const participants =
    (commercial?.commercial_distribution as
      | Array<Record<string, unknown>>
      | undefined) ?? [];

  return (
    <>
      <WorkbenchTopbar activeTabLabel="Terms Overview" />
      <div className="flex-1 overflow-y-auto px-9 py-7">
        <div className="mx-auto grid max-w-[1280px] gap-6">
          <header>
            <Eyebrow>Commercial</Eyebrow>
            <h1 className="mt-1 font-display text-[28px] font-semibold leading-tight text-ink">
              Terms overview
            </h1>
            <Body className="mt-2">
              What's actually being offered — limits, retentions, premium,
              dates, and the commercial entity stack.
            </Body>
          </header>

          {/* Coverage card */}
          <Card variant="info" pad="lg" className="space-y-3">
            <Eyebrow className="text-info-deep dark:text-info">Coverage</Eyebrow>
            <div className="grid gap-2 md:grid-cols-2">
              <LabelRow
                label="Coverage"
                value={sub.coverage ?? "—"}
              />
              <LabelRow
                label="Limit (per occurrence)"
                value={
                  limit != null ? formatCurrency(Number(limit)) : "—"
                }
              />
              <LabelRow
                label="Aggregate limit"
                value={
                  aggregate != null
                    ? formatCurrency(Number(aggregate))
                    : limit != null
                      ? formatCurrency(Number(limit))
                      : "—"
                }
              />
              <LabelRow
                label="Deductible / retention"
                value={
                  deductible != null ? formatCurrency(Number(deductible)) : "—"
                }
              />
              <LabelRow
                label="Effective from"
                value={
                  effectiveFrom
                    ? formatDate(String(effectiveFrom))
                    : "—"
                }
              />
              <LabelRow
                label="Effective to"
                value={
                  effectiveTo ? formatDate(String(effectiveTo)) : "—"
                }
              />
            </div>
          </Card>

          {/* Premium card */}
          <Card pad="md" className="space-y-2">
            <Eyebrow>Premium</Eyebrow>
            <div className="grid gap-2 md:grid-cols-2">
              <LabelRow
                label="Base premium"
                value={
                  basePremium != null ? formatCurrency(Number(basePremium)) : "—"
                }
              />
              <LabelRow
                label="Final premium"
                value={
                  finalPremium != null
                    ? formatCurrency(Number(finalPremium))
                    : "—"
                }
              />
            </div>
          </Card>

          {/* Commercial distribution */}
          {participants.length > 0 ? (
            <Card pad="md" className="overflow-hidden p-0">
              <header className="border-b border-rule px-5 py-3.5">
                <Eyebrow>Commercial stack ({participants.length})</Eyebrow>
              </header>
              <table className="w-full table-fixed text-[13px]">
                <thead>
                  <tr className="border-b border-rule bg-surface-sunken/60 text-left">
                    <ColHead width="w-[28%]">Participant</ColHead>
                    <ColHead width="w-[14%]">Type</ColHead>
                    <ColHead width="w-[14%]">Share</ColHead>
                    <ColHead width="w-[16%]">Premium</ColHead>
                    <ColHead width="w-[14%]">Commission</ColHead>
                    <ColHead width="w-[14%]">Layer</ColHead>
                  </tr>
                </thead>
                <tbody>
                  {participants.map((p, i) => (
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
                      <td className="px-5 py-2.5 text-ink-soft">
                        {String(p.type ?? p.role ?? "—")}
                      </td>
                      <td className="px-5 py-2.5 tabular-nums text-ink">
                        {p.share_pct != null
                          ? `${Number(p.share_pct).toFixed(1)}%`
                          : p.share != null
                            ? `${(Number(p.share) * 100).toFixed(1)}%`
                            : "—"}
                      </td>
                      <td className="px-5 py-2.5 tabular-nums text-ink">
                        {p.premium != null
                          ? formatCurrency(Number(p.premium))
                          : "—"}
                      </td>
                      <td className="px-5 py-2.5 tabular-nums text-ink-soft">
                        {p.commission_pct != null
                          ? `${Number(p.commission_pct).toFixed(1)}%`
                          : "—"}
                      </td>
                      <td className="px-5 py-2.5 text-ink-soft">
                        {String(p.layer ?? "—")}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </Card>
          ) : (
            <LooseRecordCard
              title="Commercial entity"
              data={commercial as Record<string, unknown> | null}
              fields={[
                { key: "lead_carrier", label: "Lead carrier" },
                { key: "broker", label: "Broker" },
                { key: "syndicate", label: "Syndicate" },
                { key: "mga", label: "MGA" },
                { key: "fronting_carrier", label: "Fronting carrier" },
              ]}
              showRest
              emptyMessage="No commercial entity data attached to this quote."
            />
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
      className={`px-5 py-2.5 text-[11px] font-semibold uppercase tracking-[0.08em] text-ink-mute ${width}`}
    >
      {children}
    </th>
  );
}

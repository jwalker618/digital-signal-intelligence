"use client";

import { CheckCircle2, FileCheck, ShieldOff } from "lucide-react";
import { WorkbenchTopbar } from "@/components/chrome/workbench-topbar";
import { Card } from "@/components/ui/card";
import { Chip } from "@/components/ui/chip";
import { Eyebrow, Body, Micro } from "@/components/ui/typography";
import { MiniKpi } from "@/components/ui/mini-kpi";
import { PageLoading } from "@/components/base/pageStates";
import { LooseRecordCard } from "@/components/base/loose-record";
import { useDsiStore } from "@/store/dsiStore";
import { formatCurrency, formatText } from "@/lib/format";

export default function CoverageTermsPage() {
  const risk = useDsiStore((s) => s.activeRisk);
  const sub = useDsiStore((s) => s.activeSubmission);
  const ver = useDsiStore((s) => s.activeVersion);

  if (!sub) {
    return (
      <>
        <WorkbenchTopbar activeTabLabel="Coverage Terms" />
        <PageLoading message="Loading coverage terms…" />
      </>
    );
  }

  const fpd = (ver?.final_premium_detail ?? {}) as Record<string, unknown>;
  const limit = Number(fpd.limit ?? risk?.limit ?? 0);
  const aggregate = Number(fpd.aggregate ?? risk?.aggregate_limit ?? limit);

  const coveragesIn =
    (risk?.coverages_included as Array<unknown> | undefined) ??
    (risk?.included as Array<unknown> | undefined) ??
    [];
  const coveragesOut =
    (risk?.coverages_excluded as Array<unknown> | undefined) ??
    (risk?.excluded as Array<unknown> | undefined) ??
    [];
  const subLimits =
    (risk?.sub_limits as Array<Record<string, unknown>> | undefined) ?? [];
  const endorsements =
    (risk?.endorsements as Array<Record<string, unknown>> | undefined) ?? [];
  const structureMode = String(
    risk?.structure ?? risk?.limit_structure ?? "BUNDLED",
  );

  return (
    <>
      <WorkbenchTopbar activeTabLabel="Coverage Terms" />
      <div className="flex-1 overflow-y-auto px-9 py-7">
        <div className="mx-auto grid max-w-[1280px] gap-6">
          {/* Coverage overview */}
          <Card header="Coverage overview" icon={FileCheck} pad="md">
            <div className="grid grid-cols-2 gap-6 sm:grid-cols-4">
              <MiniKpi
                label="Territory"
                value={
                  risk?.territory
                    ? formatText(String(risk.territory), "capitalize")
                    : "—"
                }
              />
              <MiniKpi
                label="Trigger"
                value={
                  risk?.coverage_trigger
                    ? formatText(String(risk.coverage_trigger), "capitalize")
                    : "—"
                }
              />
              <MiniKpi label="Included" value={coveragesIn.length} />
              <MiniKpi label="Excluded" value={coveragesOut.length} />
            </div>
          </Card>

          {/* Headline structure */}
          <Card variant="info" pad="lg" className="grid gap-6 sm:grid-cols-3">
            <div>
              <Eyebrow className="text-info-deep dark:text-info">Limit</Eyebrow>
              <p className="mt-2 font-display text-[24px] font-semibold tabular-nums text-ink">
                {limit > 0 ? formatCurrency(limit) : "—"}
              </p>
              <Micro className="mt-1 block">per occurrence</Micro>
            </div>
            <div>
              <Eyebrow>Aggregate</Eyebrow>
              <p className="mt-2 font-display text-[24px] font-semibold tabular-nums text-ink">
                {aggregate > 0 ? formatCurrency(aggregate) : "—"}
              </p>
              <Micro className="mt-1 block">annual cap</Micro>
            </div>
            <div>
              <Eyebrow>Structure</Eyebrow>
              <p className="mt-2 text-[18px] font-semibold text-ink">
                {formatText(structureMode, "capitalize")}
              </p>
              <Micro className="mt-1 block">
                {structureMode.toLowerCase().includes("decoup")
                  ? "limits ring-fenced per coverage"
                  : "single limit shared across coverages"}
              </Micro>
            </div>
          </Card>

          {/* Included / Excluded */}
          <div className="grid gap-5 md:grid-cols-2">
            <CoverageList
              title="Included"
              icon={<CheckCircle2 size={14} className="text-pos" />}
              items={coveragesIn}
              tone="pos"
              empty="No specific coverages listed — assume default bundle."
            />
            <CoverageList
              title="Excluded"
              icon={<ShieldOff size={14} className="text-neg" />}
              items={coveragesOut}
              tone="neg"
              empty="No exclusions recorded."
            />
          </div>

          {/* Sub-limits */}
          {subLimits.length > 0 && (
            <Card
              header={`Sub-limits · ${subLimits.length}`}
              icon={FileCheck}
              pad="none"
              className="overflow-hidden"
            >
              <table className="w-full table-fixed text-[13px]">
                <thead>
                  <tr className="border-b border-rule bg-surface-sunken/60 text-left">
                    <ColHead width="w-[40%]">Coverage element</ColHead>
                    <ColHead width="w-[24%]">Sub-limit</ColHead>
                    <ColHead width="w-[36%]">Notes</ColHead>
                  </tr>
                </thead>
                <tbody>
                  {subLimits.map((s, i) => (
                    <tr
                      key={i}
                      className="border-b border-rule last:border-0 hover:bg-surface-sunken/40"
                    >
                      <td className="px-5 py-2.5 text-ink">
                        {String(s.name ?? s.coverage ?? "—")}
                      </td>
                      <td className="px-5 py-2.5 font-semibold tabular-nums text-ink">
                        {s.limit != null
                          ? formatCurrency(Number(s.limit))
                          : "—"}
                      </td>
                      <td className="px-5 py-2.5 text-[12.5px] text-ink-soft">
                        {String(s.note ?? s.basis ?? "")}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </Card>
          )}

          {/* Endorsements */}
          {endorsements.length > 0 && (
            <Card header={`Endorsements · ${endorsements.length}`} icon={CheckCircle2} pad="md">
              <ul className="divide-y divide-rule">
                {endorsements.map((e, i) => (
                  <li key={i} className="flex items-start gap-3 py-2.5">
                    <Chip
                      variant={
                        String(e.kind ?? "").toLowerCase() === "exclusion"
                          ? "neg"
                          : "info"
                      }
                      size="sm"
                    >
                      {formatText(String(e.kind ?? "Rider"), "capitalize")}
                    </Chip>
                    <div className="min-w-0 flex-1">
                      <p className="text-[13.5px] font-medium text-ink">
                        {String(e.name ?? e.title ?? "—")}
                      </p>
                      {e.description && (
                        <Body className="mt-0.5 text-[12.5px]">
                          {String(e.description)}
                        </Body>
                      )}
                    </div>
                  </li>
                ))}
              </ul>
            </Card>
          )}

          {/* Generic fallback for any other risk-terms fields the backend ships */}
          {subLimits.length === 0 &&
            endorsements.length === 0 &&
            coveragesIn.length === 0 && (
              <LooseRecordCard
                title="Risk terms detail"
                data={risk as Record<string, unknown> | null}
                fields={[
                  { key: "currency", label: "Currency" },
                  { key: "territory", label: "Territory" },
                  { key: "retroactive_date", label: "Retro date", kind: "date" },
                  { key: "discovery_period_months", label: "Discovery period (months)" },
                ]}
                showRest
              />
            )}
        </div>
      </div>
    </>
  );
}

function CoverageList({
  title,
  icon,
  items,
  tone,
  empty,
}: {
  title: string;
  icon: React.ReactNode;
  items: Array<unknown>;
  tone: "pos" | "neg";
  empty: string;
}) {
  return (
    <Card pad="md" variant={tone === "pos" ? "pos" : "default"}>
      <header className="flex items-center gap-2">
        {icon}
        <Eyebrow className={tone === "pos" ? "text-pos" : "text-neg"}>
          {title} ({items.length})
        </Eyebrow>
      </header>
      {items.length === 0 ? (
        <Body className="mt-2 italic">{empty}</Body>
      ) : (
        <ul className="mt-3 space-y-1.5">
          {items.map((c, i) => {
            const label =
              typeof c === "string"
                ? c
                : typeof c === "object" && c !== null
                  ? String((c as Record<string, unknown>).name ??
                      (c as Record<string, unknown>).coverage ??
                      "—")
                  : String(c);
            return (
              <li key={i} className="flex items-start gap-2 text-[13px] text-ink">
                <span
                  className={
                    "mt-2 inline-block h-1.5 w-1.5 shrink-0 rounded-full " +
                    (tone === "pos" ? "bg-pos" : "bg-neg")
                  }
                />
                {label}
              </li>
            );
          })}
        </ul>
      )}
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

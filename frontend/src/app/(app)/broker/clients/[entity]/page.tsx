"use client";

import { Building2, GitBranch, Layers, ListChecks, ShieldCheck } from "lucide-react";
import { Card } from "@/components/ui/card";
import { Chip } from "@/components/ui/chip";
import { WorkArea } from "@/components/ui/work-area";
import { Eyebrow, Micro, Body } from "@/components/ui/typography";
import { KpiSnug } from "@/components/ui/kpi-snug";
import { LabelRow } from "@/components/ui/label-row";
import { formatCurrency } from "@/lib/format";
import { fmtRelative } from "@/lib/utils";
import { useClientWorkbench } from "./_lib/context";
import { kFmt, tierTone, TIER_BG, BAR_BG, DOT_BG, NUM_TEXT } from "./_lib/helpers";

export default function ClientSummaryPage() {
  const cw = useClientWorkbench();
  if (!cw) return null;

  const initials = cw.entity_name
    .split(/\s+/)
    .slice(0, 2)
    .map((w) => w[0])
    .join("")
    .toUpperCase();

  const tiers = [1, 2, 3, 4, 5].map((t) => ({
    t,
    n: cw.coverages.filter((c) => c.tier === t).length,
  }));
  const maxTier = Math.max(...tiers.map((x) => x.n), 1);
  const stateMix = [
    { label: "Bound", n: cw.coverages.filter((c) => c.status_tone === "pos").length, tone: "pos" },
    { label: "Referred", n: cw.coverages.filter((c) => c.decision === "refer").length, tone: "spot" },
    { label: "Declined", n: cw.coverages.filter((c) => c.decision === "decline").length, tone: "neg" },
  ];

  return (
    <WorkArea>
      {/* identity + KPI strip */}
      <div className="grid gap-3.5 lg:grid-cols-[1.5fr_2.5fr]">
        <Card header="Client" icon={Building2} pad="md">
          <div className="mb-3.5 flex items-center gap-3.5">
            <div className="flex h-[52px] w-[52px] shrink-0 items-center justify-center rounded-xl bg-info-soft text-[18px] font-bold text-info-deep dark:text-info">
              {initials}
            </div>
            <div className="min-w-0">
              <div className="text-[16px] font-bold">{cw.entity_name}</div>
              {cw.domain && (
                <a
                  href={`https://${cw.domain}`}
                  target="_blank"
                  rel="noreferrer"
                  className="font-mono text-[12px] text-info hover:underline"
                >
                  {cw.domain}
                </a>
              )}
            </div>
          </div>
          <LabelRow label="Industry" value={cw.industry ?? "—"} />
          <LabelRow label="NAICS" value={cw.naics ? <span className="font-mono">{cw.naics}</span> : "—"} />
          <LabelRow label="Revenue band" value={cw.revenue_band ?? "—"} />
          <LabelRow
            label="Locations"
            value={[cw.country, cw.locations].filter(Boolean).join(" · ") || "—"}
          />
          <LabelRow label="Employees" value={cw.employees ?? "—"} />
          <LabelRow label="Broker" value={cw.broker ?? "—"} />
          <LabelRow
            label="Relationship"
            value={
              cw.first_seen
                ? `${fmtRelative(cw.first_seen)} → ${cw.last_seen ? fmtRelative(cw.last_seen) : "now"}`
                : "—"
            }
          />
        </Card>

        <div className="flex flex-col gap-3.5">
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
            <Card pad="sm">
              <KpiSnug label="Total premium" value={kFmt(cw.total_premium)} tone="info" />
              <Micro className="mt-0.5 block">annual, across coverages</Micro>
            </Card>
            <Card pad="sm">
              <KpiSnug label="Active coverages" value={cw.coverages.length} />
              <Micro className="mt-0.5 block">
                {cw.coverages.map((c) => c.line).join(" · ")}
              </Micro>
            </Card>
            <Card pad="sm">
              <KpiSnug label="Avg signal score" value={cw.avg_score ?? "—"} />
              <Micro className="mt-0.5 block">weighted across lines</Micro>
            </Card>
            <Card pad="sm">
              <KpiSnug label="Engagement" value={cw.engagement ?? "—"} tone="pos" />
              <Micro className="mt-0.5 block">{cw.engagement_label ?? "—"}</Micro>
            </Card>
          </div>
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
            <Card pad="sm">
              <KpiSnug label="Open queries" value={cw.open_queries} tone="spot" />
              <Micro className="mt-0.5 block">awaiting action</Micro>
            </Card>
            <Card pad="sm">
              <KpiSnug
                label="Avg response"
                value={cw.avg_response_hours != null ? `${cw.avg_response_hours}h` : "—"}
              />
              <Micro className="mt-0.5 block">client replies</Micro>
            </Card>
            <Card pad="sm">
              <KpiSnug
                label="Next renewal"
                value={cw.next_renewal_days != null ? `${cw.next_renewal_days}d` : "—"}
                tone="warn"
              />
              <Micro className="mt-0.5 block">earliest coverage</Micro>
            </Card>
            <Card pad="sm">
              <KpiSnug label="Last message" value={cw.last_message ?? "—"} />
              <Micro className="mt-0.5 block">most recent thread</Micro>
            </Card>
          </div>
        </div>
      </div>

      {/* active coverages */}
      <Card
        header="Active coverages"
        icon={ShieldCheck}
        pad="md"
        headerRight={<Chip variant="default" size="sm">{cw.coverages.length} in force</Chip>}
      >
        <div className="grid grid-cols-[1fr_1.4fr_80px_70px_90px_110px_130px] border-b border-rule pb-2 text-[10.5px] uppercase tracking-wider text-ink-mute">
          {["Line", "Carrier", "Score", "Tier", "Percentile", "Premium", "Status"].map((h) => (
            <span key={h}>{h}</span>
          ))}
        </div>
        {cw.coverages.map((c, i) => (
          <div
            key={c.code}
            className={`grid grid-cols-[1fr_1.4fr_80px_70px_90px_110px_130px] items-center py-2.5 text-[13px] ${
              i < cw.coverages.length - 1 ? "border-b border-rule" : ""
            }`}
          >
            <span className="font-semibold">{c.line}</span>
            <span className="text-ink-soft">{c.carrier ?? "—"}</span>
            <span className="font-bold tabular-nums text-info">
              {c.score != null ? c.score.toFixed(0) : "—"}
            </span>
            <span>
              {c.tier != null ? (
                <span
                  className={`inline-flex h-6 w-6 items-center justify-center rounded-md text-[12px] font-bold ${TIER_BG[tierTone(c.tier)]}`}
                >
                  {c.tier}
                </span>
              ) : (
                "—"
              )}
            </span>
            <span className="tabular-nums">
              {c.percentile != null ? `${Math.round(c.percentile * 100)}th` : "—"}
            </span>
            <span className="font-semibold tabular-nums">{kFmt(c.premium)}</span>
            <span>
              <Chip variant={c.status_tone as "pos" | "spot" | "neg" | "mute"} size="sm">
                {c.status}
              </Chip>
            </span>
          </div>
        ))}
      </Card>

      {/* aggregates */}
      <div className="grid gap-3.5 lg:grid-cols-3">
        <Card header="Tier mix" icon={Layers} pad="md">
          <div className="mt-1 flex h-[92px] items-end gap-3">
            {tiers.map(({ t, n }) => (
              <div key={t} className="flex flex-1 flex-col items-center gap-1.5">
                <span className={`text-[14px] font-semibold tabular-nums ${NUM_TEXT[tierTone(t)]}`}>
                  {n}
                </span>
                <div
                  className={`w-full rounded-t ${BAR_BG[tierTone(t)]}`}
                  style={{ height: `${Math.max(4, (n / maxTier) * 72)}px` }}
                />
                <Micro className="text-[10px]">T{t}</Micro>
              </div>
            ))}
          </div>
        </Card>

        <Card header="Pipeline state" icon={GitBranch} pad="md">
          <div className="mt-0.5 flex flex-col gap-2.5">
            {stateMix.map((s) => (
              <div key={s.label} className="flex items-center gap-2.5">
                <span className={`h-2 w-2 shrink-0 rounded-full ${DOT_BG[s.tone]}`} />
                <span className="flex-1 text-[13px]">{s.label}</span>
                <span className={`text-[15px] font-bold tabular-nums ${NUM_TEXT[s.tone]}`}>{s.n}</span>
              </div>
            ))}
          </div>
        </Card>

        <Card header="Coverage lines" icon={ListChecks} pad="md">
          <div className="mt-0.5 flex flex-col gap-2">
            {cw.coverages.map((c) => (
              <div key={c.code} className="flex items-center gap-2.5">
                <ShieldCheck size={14} className="text-info" />
                <span className="flex-1 text-[13px] font-semibold">{c.line}</span>
                <Micro>{c.carrier ?? "—"}</Micro>
              </div>
            ))}
          </div>
          {cw.coverages.length === 0 && <Body className="italic">No coverages.</Body>}
        </Card>
      </div>
    </WorkArea>
  );
}

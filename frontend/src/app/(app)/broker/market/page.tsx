"use client";

import { Leaf } from "lucide-react";
import { Topbar } from "@/components/chrome/topbar";
import {
  Body,
  Card,
  Caption,
  Chip,
  Eyebrow,
  KpiSnug,
  Micro,
} from "@/components/ui";
import { PageError, PageLoading, RoleGate } from "@/components/base/pageStates";
import { useRoleScopedFetch } from "@/lib/useRoleScopedFetch";
import { fetchMarketPulse } from "@/lib/portalApi";
import { useAuthStore } from "@/store/authStore";
import { formatDate, formatText } from "@/lib/format";
import { cn } from "@/lib/utils";
import type {
  LossEventEntry,
  MarketLineSummary,
  MarketPulseResponse,
} from "@/types/portal";

export default function BrokerMarketPage() {
  const accessToken = useAuthStore((s) => s.accessToken);
  const user = useAuthStore((s) => s.user);
  const enabled = !!accessToken && user?.role === "BROKER";

  const { data, error, loading } = useRoleScopedFetch<MarketPulseResponse>({
    fetcher: () => fetchMarketPulse(accessToken),
    enabled,
    deps: [accessToken],
  });

  if (!user) return <PageLoading message="Signing in…" />;
  if (user.role && user.role !== "BROKER") return <RoleGate expected="broker" />;
  if (loading) return <PageLoading />;
  if (error) return <PageError message={error} />;
  if (!data) return <PageLoading />;

  return <PulseBody data={data} />;
}

function isHardening(c: string): boolean {
  return /hard/i.test(c);
}

function isSoftening(c: string): boolean {
  return /soft/i.test(c);
}

function cycleTone(c: string): "warn" | "pos" | "info" {
  if (isHardening(c)) return "warn";
  if (isSoftening(c)) return "pos";
  return "info";
}

function PulseBody({ data }: { data: MarketPulseResponse }) {
  const hardening = data.lines.filter((l) => isHardening(l.cycle_position)).length;
  const softening = data.lines.filter((l) => isSoftening(l.cycle_position)).length;
  const overallTone = cycleTone(data.cycle_overall);

  return (
    <>
      <Topbar crumbs={["Broker Portal", "Market Pulse"]} />
      <div className="flex-1 overflow-y-auto px-9 py-7">
        <div className="grid gap-4">
          {/* Title + KPIs */}
          <header className="flex flex-wrap items-end justify-between gap-6">
            <div>
              <h1 className="mt-1.5 font-display text-[32px] font-semibold leading-tight tracking-tight text-ink">
                By-line market intelligence
              </h1>
              <Body className="mt-1.5">
                Cycle position, capacity, loss trends, and the climate overlay shaping placement
                decisions.
              </Body>
            </div>
            <div className="flex flex-wrap gap-7">
              <KpiSnug
                label="Cycle overall"
                value={formatText(data.cycle_overall, "capitalize")}
                tone={overallTone}
              />
              <KpiSnug label="Hardening" value={hardening} tone="warn" />
              <KpiSnug label="Softening" value={softening} tone="pos" />
              <KpiSnug label="Lines watched" value={data.lines.length} />
            </div>
          </header>

          {/* Climate pulse */}
          {data.climate_pulse_summary && (
            <Card variant="pos" pad="lg">
              <div className="grid items-start gap-4 md:grid-cols-[40px_1fr]">
                <div className="flex h-10 w-10 items-center justify-center rounded-md bg-pos-soft text-pos">
                  <Leaf size={20} />
                </div>
                <div>
                  <Eyebrow className="text-pos">
                    Climate pulse — the active market force
                  </Eyebrow>
                  <Body className="mt-2 text-[14px] leading-relaxed text-ink">
                    {data.climate_pulse_summary}
                  </Body>
                </div>
              </div>
            </Card>
          )}

          {/* By-line dashboards */}
          <section>
            <div className="mb-2.5 flex items-baseline justify-between">
              <h2 className="text-[17px] font-semibold text-ink">By-line dashboards</h2>
              <Caption>Click a line for full carrier and loss-event detail</Caption>
            </div>
            <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
              {data.lines.map((line) => (
                <LineCard key={line.slug} line={line} />
              ))}
            </div>
          </section>

          {/* Loss events */}
          {data.recent_loss_events.length > 0 && (
            <Card pad="lg">
              <div className="mb-3 flex items-baseline justify-between">
                <div>
                  <Eyebrow>Recent loss events</Eyebrow>
                  <h2 className="mt-1.5 text-[17px] font-semibold leading-tight text-ink">
                    Events shaping market direction
                  </h2>
                </div>
                <Caption>Last 12 months</Caption>
              </div>
              <div className="flex flex-col gap-2.5">
                {data.recent_loss_events.map((e, i) => (
                  <LossEventRow key={i} event={e} />
                ))}
              </div>
            </Card>
          )}
        </div>
      </div>
    </>
  );
}

function LineCard({ line }: { line: MarketLineSummary }) {
  const tone = cycleTone(line.cycle_position);
  const borderClass =
    tone === "warn" ? "border-t-warn" : tone === "pos" ? "border-t-pos" : "border-t-info";
  const cycleChipTone = tone;
  const rateColor =
    line.rate_change_yoy_pct > 5
      ? "text-warn"
      : line.rate_change_yoy_pct < -3
        ? "text-pos"
        : "text-ink-soft";
  const lossColor = /deter|worsen/i.test(line.loss_trend)
    ? "text-neg"
    : /improv/i.test(line.loss_trend)
      ? "text-pos"
      : "text-ink-soft";

  return (
    <Card pad="md" className={cn("border-t-[3px]", borderClass)}>
      <div className="mb-3 flex items-baseline justify-between">
        <span className="text-[14px] font-bold text-ink">{line.name}</span>
        <Chip variant={cycleChipTone} size="sm">
          {formatText(line.cycle_position, "capitalize")}
        </Chip>
      </div>
      <div className="mb-2.5 grid grid-cols-2 gap-2">
        <div>
          <Micro className="block">Rate YoY</Micro>
          <div className={cn("text-[20px] font-semibold tabular-nums", rateColor)}>
            {line.rate_change_yoy_pct > 0 ? "+" : ""}
            {line.rate_change_yoy_pct.toFixed(1)}%
          </div>
        </div>
        <div>
          <Micro className="block">Capacity</Micro>
          <div className="text-[14px] font-semibold text-ink">
            {formatText(line.capacity_state, "capitalize")}
          </div>
          <Micro className="block">
            {formatText(line.capacity_trend, "capitalize")}
          </Micro>
        </div>
      </div>
      <div className="mb-2.5 text-[12px]">
        <Micro>Loss trend: </Micro>
        <span className={cn("font-semibold", lossColor)}>
          {formatText(line.loss_trend, "capitalize")}
        </span>
      </div>
      {line.esg_overlay && (
        <div className="border-t border-rule pt-2.5">
          <Micro className="mb-1 flex items-center gap-1">
            <Leaf size={11} /> ESG overlay
          </Micro>
          <Caption className="text-[11.5px] leading-snug">{line.esg_overlay}</Caption>
        </div>
      )}
    </Card>
  );
}

function LossEventRow({ event }: { event: LossEventEntry }) {
  return (
    <div className="grid items-start gap-4 rounded-card border border-rule bg-surface-elev px-3.5 py-3 sm:grid-cols-[90px_1fr_auto]">
      <div>
        <Chip variant="mute" size="sm">
          {event.line}
        </Chip>
        <Micro className="mt-1 block">{formatDate(event.date)}</Micro>
      </div>
      <div>
        <div className="text-[13.5px] font-semibold text-ink">{event.headline}</div>
        <Caption className="mt-1 block italic leading-snug">
          {event.implication}
        </Caption>
      </div>
      <div className="text-right">
        <Micro className="block">industry loss</Micro>
        <span className="text-[16px] font-bold tabular-nums text-neg">
          ${event.estimated_industry_loss_usd_bn.toFixed(1)}B
        </span>
      </div>
    </div>
  );
}

"use client";

import { AlertOctagon, ArrowDownRight, ArrowUpRight, Cloud, Leaf } from "lucide-react";
import { Topbar } from "@/components/chrome/topbar";
import { Card } from "@/components/ui/card";
import { Chip } from "@/components/ui/chip";
import { Eyebrow, NumDisplay, Body, Micro } from "@/components/ui/typography";
import { PageError, PageLoading, RoleGate } from "@/components/base/pageStates";
import { useRoleScopedFetch } from "@/lib/useRoleScopedFetch";
import { fetchMarketPulse } from "@/lib/portalApi";
import { useAuthStore } from "@/store/authStore";
import { formatDate, formatText, formatPercent } from "@/lib/format";
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

function PulseBody({ data }: { data: MarketPulseResponse }) {
  return (
    <>
      <Topbar crumbs={["Broker Portal", "Market Pulse"]} />
      <div className="flex-1 overflow-y-auto px-9 py-7">
        <div className="mx-auto grid max-w-[1400px] gap-6">
          <header>
            <Eyebrow>Markets</Eyebrow>
            <h1 className="mt-1 font-display text-[32px] font-semibold leading-none tracking-tight text-ink">
              Market Pulse
            </h1>
          </header>

          {/* Hero: cycle */}
          <Card variant="info" pad="lg" className="space-y-3">
            <Eyebrow className="text-info-deep dark:text-info">Cycle</Eyebrow>
            <p className="font-display text-[22px] font-semibold leading-snug text-ink">
              {data.cycle_overall}
            </p>
            {data.climate_pulse_summary && (
              <div className="flex items-start gap-2 border-t border-info/30 pt-3">
                <Cloud size={15} className="mt-0.5 shrink-0 text-info" />
                <Body className="text-ink">{data.climate_pulse_summary}</Body>
              </div>
            )}
          </Card>

          {/* Line cards */}
          <section>
            <Eyebrow className="mb-3">By line</Eyebrow>
            <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
              {data.lines.map((line) => (
                <LineCard key={line.slug} line={line} />
              ))}
            </div>
          </section>

          {/* Recent loss events */}
          {data.recent_loss_events.length > 0 && (
            <section>
              <Eyebrow className="mb-3">Recent industry losses</Eyebrow>
              <div className="space-y-3">
                {data.recent_loss_events.map((e, i) => (
                  <LossEventRow key={i} event={e} />
                ))}
              </div>
            </section>
          )}
        </div>
      </div>
    </>
  );
}

function LineCard({ line }: { line: MarketLineSummary }) {
  const tone =
    line.cycle_position === "soft"
      ? "pos"
      : line.cycle_position === "hard"
        ? "neg"
        : line.cycle_position === "stable"
          ? "info"
          : "warn";
  return (
    <Card pad="md" className="space-y-3">
      <header className="flex items-start justify-between gap-3">
        <div>
          <h3 className="text-[16px] font-semibold text-ink">{line.name}</h3>
          <Micro className="mt-0.5 block">{line.slug}</Micro>
        </div>
        <Chip variant={tone} size="sm">
          {formatText(line.cycle_position, "capitalize")}
        </Chip>
      </header>

      <div className="flex items-baseline gap-2">
        <span
          className={cn(
            "font-display text-[22px] font-semibold tabular-nums",
            line.rate_change_yoy_pct >= 0 ? "text-neg" : "text-pos",
          )}
        >
          {line.rate_change_yoy_pct >= 0 ? "+" : ""}
          {line.rate_change_yoy_pct.toFixed(1)}%
        </span>
        <Micro>rate YoY</Micro>
      </div>

      <div className="grid grid-cols-2 gap-3 border-t border-rule pt-3 text-[12.5px]">
        <Stat
          label="Capacity"
          value={`${formatText(line.capacity_state, "capitalize")} · ${formatText(line.capacity_trend, "capitalize")}`}
        />
        <Stat
          label="Loss trend"
          value={formatText(line.loss_trend, "capitalize")}
          icon={
            /down|easing|improv/i.test(line.loss_trend) ? (
              <ArrowDownRight size={12} className="text-pos" />
            ) : /up|rising|worsen/i.test(line.loss_trend) ? (
              <ArrowUpRight size={12} className="text-neg" />
            ) : null
          }
        />
        {line.esg_overlay && (
          <Stat
            label="ESG"
            value={line.esg_overlay}
            icon={<Leaf size={12} className="text-pos" />}
          />
        )}
      </div>
    </Card>
  );
}

function LossEventRow({ event }: { event: LossEventEntry }) {
  return (
    <Card pad="md" className="grid gap-3 md:grid-cols-[1.4fr_120px_1fr]">
      <div>
        <div className="flex items-start gap-2">
          <AlertOctagon size={15} className="mt-0.5 shrink-0 text-neg" />
          <h3 className="text-[14.5px] font-semibold text-ink">
            {event.headline}
          </h3>
        </div>
        <Micro className="mt-1 block">
          {event.line} · {formatDate(event.date)}
        </Micro>
      </div>
      <div>
        <Micro>Est. industry loss</Micro>
        <p className="font-semibold tabular-nums text-ink">
          ${event.estimated_industry_loss_usd_bn.toFixed(1)}B
        </p>
      </div>
      <div>
        <Micro>Implication</Micro>
        <Body className="text-[13px]">{event.implication}</Body>
      </div>
    </Card>
  );
}

function Stat({
  label,
  value,
  icon,
}: {
  label: string;
  value: string;
  icon?: React.ReactNode;
}) {
  return (
    <div>
      <Micro className="block">{label}</Micro>
      <p className="flex items-center gap-1 font-semibold text-ink">
        {icon}
        {value}
      </p>
    </div>
  );
}

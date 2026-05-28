"use client";

import { useMemo, useState } from "react";
import { Building2, Leaf, Search, TrendingDown, TrendingUp } from "lucide-react";
import { Topbar } from "@/components/chrome/topbar";
import { Card } from "@/components/ui/card";
import { Chip } from "@/components/ui/chip";
import { Eyebrow, Body, Micro } from "@/components/ui/typography";
import { PageError, PageLoading, RoleGate } from "@/components/base/pageStates";
import { useRoleScopedFetch } from "@/lib/useRoleScopedFetch";
import { fetchCarriers } from "@/lib/portalApi";
import { useAuthStore } from "@/store/authStore";
import { formatPercent } from "@/lib/format";
import { cn } from "@/lib/utils";
import type {
  AppetiteStance,
  CarrierRosterResponse,
  CarrierSummary,
  PricingPosition,
  EsgStance,
} from "@/types/portal";

export default function BrokerCarriersPage() {
  const accessToken = useAuthStore((s) => s.accessToken);
  const user = useAuthStore((s) => s.user);
  const enabled = !!accessToken && user?.role === "BROKER";

  const { data, error, loading } = useRoleScopedFetch<CarrierRosterResponse>({
    fetcher: () => fetchCarriers(accessToken),
    enabled,
    deps: [accessToken],
  });

  if (!user) return <PageLoading message="Signing in…" />;
  if (user.role && user.role !== "BROKER") return <RoleGate expected="broker" />;
  if (loading) return <PageLoading />;
  if (error) return <PageError message={error} />;
  if (!data) return <PageLoading />;

  return <RosterBody data={data} />;
}

function RosterBody({ data }: { data: CarrierRosterResponse }) {
  const [query, setQuery] = useState("");
  const filtered = useMemo(
    () =>
      data.carriers.filter(
        (c) =>
          !query ||
          c.name.toLowerCase().includes(query.toLowerCase()) ||
          c.specialties.some((s) =>
            s.toLowerCase().includes(query.toLowerCase()),
          ),
      ),
    [data.carriers, query],
  );

  return (
    <>
      <Topbar crumbs={["Broker Portal", "Carrier Intelligence"]} />
      <div className="flex-1 overflow-y-auto px-9 py-7">
        <div className="mx-auto grid max-w-[1400px] gap-6">
          <header className="flex items-end justify-between gap-6">
            <div>
              <Eyebrow>Markets</Eyebrow>
              <h1 className="mt-1 font-display text-[32px] font-semibold leading-none tracking-tight text-ink">
                Carrier Intelligence
              </h1>
              <Body className="mt-2">
                Carrier appetite, pricing position, ESG stance, and your win
                rate. Filter by specialty.
              </Body>
            </div>
            <div className="flex items-center gap-2 rounded-btn border border-rule-strong bg-surface px-3">
              <Search size={15} className="text-ink-mute" />
              <input
                type="search"
                placeholder="Carrier or specialty…"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                className="h-10 w-64 border-0 bg-transparent text-[13.5px] text-ink placeholder:text-ink-mute focus:outline-none"
              />
            </div>
          </header>

          <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
            {filtered.map((c) => (
              <CarrierCard key={c.slug} carrier={c} />
            ))}
          </div>

          {filtered.length === 0 && (
            <Card pad="lg">
              <Body className="italic">No carriers match "{query}".</Body>
            </Card>
          )}
        </div>
      </div>
    </>
  );
}

function CarrierCard({ carrier }: { carrier: CarrierSummary }) {
  return (
    <Card pad="md" className="space-y-3">
      <header className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <div className="flex items-center gap-2">
            <Building2 size={15} className="text-ink-mute" />
            <h3 className="truncate text-[16px] font-semibold text-ink">
              {carrier.name}
            </h3>
          </div>
          <Micro className="mt-0.5 block">
            {carrier.type} · {carrier.headquarters}
          </Micro>
        </div>
        <PricingChip position={carrier.pricing_position} />
      </header>

      <div className="grid grid-cols-2 gap-3 border-t border-rule pt-3 text-[12.5px]">
        <Stat label="Win rate">
          <span className="font-semibold tabular-nums text-ink">
            {formatPercent(carrier.win_rate, 0)}
          </span>
        </Stat>
        <Stat label="Capacity">
          <span className="font-semibold text-ink">{carrier.capacity_band}</span>
        </Stat>
        <Stat label="Commission">
          <span className="font-semibold tabular-nums text-ink">
            {formatPercent(carrier.typical_commission_pct / 100, 1)}
          </span>
        </Stat>
        <Stat label="ESG">
          <span className="flex items-center gap-1">
            <Leaf size={11} className={esgColor(carrier.esg_stance)} />
            <span className="font-semibold text-ink">
              {esgLabel(carrier.esg_stance)}
            </span>
          </span>
        </Stat>
      </div>

      <div className="space-y-1.5">
        <Micro>Specialties</Micro>
        <div className="flex flex-wrap gap-1.5">
          {carrier.specialties.slice(0, 6).map((s) => (
            <Chip key={s} variant="mute" size="sm">
              {s}
            </Chip>
          ))}
        </div>
      </div>

      {Object.keys(carrier.appetite_summary).length > 0 && (
        <div className="space-y-1.5">
          <Micro>Appetite</Micro>
          <div className="flex flex-wrap gap-1.5">
            {Object.entries(carrier.appetite_summary)
              .slice(0, 5)
              .map(([line, stance]) => (
                <AppetiteChip key={line} line={line} stance={stance} />
              ))}
          </div>
        </div>
      )}

      {carrier.movement_note && (
        <div className="border-t border-rule pt-3">
          <Micro className="block">Movement</Micro>
          <Body className="text-[12.5px]">{carrier.movement_note}</Body>
        </div>
      )}
    </Card>
  );
}

function Stat({
  label,
  children,
}: {
  label: string;
  children: React.ReactNode;
}) {
  return (
    <div>
      <Micro className="block">{label}</Micro>
      <div className="mt-0.5">{children}</div>
    </div>
  );
}

function PricingChip({ position }: { position: PricingPosition }) {
  const variant: "pos" | "warn" | "mute" =
    position === "light" ? "pos" : position === "tight" ? "warn" : "mute";
  const icon =
    position === "light" ? (
      <TrendingDown size={11} />
    ) : position === "tight" ? (
      <TrendingUp size={11} />
    ) : null;
  return (
    <Chip variant={variant} size="sm">
      {icon}
      {position === "light"
        ? "Light"
        : position === "tight"
          ? "Tight"
          : "Median"}
    </Chip>
  );
}

function AppetiteChip({
  line,
  stance,
}: {
  line: string;
  stance: AppetiteStance;
}) {
  const variant =
    stance === "leaning_in"
      ? "pos"
      : stance === "leaning_out"
        ? "neg"
        : stance === "selective"
          ? "warn"
          : "mute";
  const label =
    stance === "leaning_in"
      ? "Leaning in"
      : stance === "leaning_out"
        ? "Leaning out"
        : stance === "selective"
          ? "Selective"
          : "Neutral";
  return (
    <Chip variant={variant} size="sm">
      <span className="font-mono text-[10.5px]">{line}</span>
      <span className="text-ink-mute">·</span>
      {label}
    </Chip>
  );
}

function esgLabel(s: EsgStance): string {
  return s === "leader"
    ? "Leader"
    : s === "progressive"
      ? "Progressive"
      : s === "restrictive"
        ? "Restrictive"
        : "Neutral";
}
function esgColor(s: EsgStance): string {
  return s === "leader"
    ? "text-pos"
    : s === "progressive"
      ? "text-info"
      : s === "restrictive"
        ? "text-neg"
        : "text-ink-mute";
}

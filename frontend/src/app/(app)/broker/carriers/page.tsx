"use client";

import { useMemo, useState } from "react";
import { Leaf } from "lucide-react";
import { Topbar } from "@/components/chrome/topbar";
import {
  AdminTable,
  Body,
  Card,
  Caption,
  Chip,
  Eyebrow,
  KpiSnug,
  Micro,
} from "@/components/ui";
import type { AdminTableCol, AdminTableRow } from "@/components/ui";
import { PageError, PageLoading, RoleGate } from "@/components/base/pageStates";
import { useRoleScopedFetch } from "@/lib/useRoleScopedFetch";
import { fetchCarriers } from "@/lib/portalApi";
import { useAuthStore } from "@/store/authStore";
import { cn } from "@/lib/utils";
import type {
  AppetiteStance,
  CarrierRosterResponse,
  EsgStance,
  PricingPosition,
} from "@/types/portal";

type EsgFilter = "all" | EsgStance;
type PricingFilter = "all" | PricingPosition;

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
  const [esg, setEsg] = useState<EsgFilter>("all");
  const [pricing, setPricing] = useState<PricingFilter>("all");

  const carriers = data.carriers;
  const leaders = carriers.filter((c) => c.esg_stance === "leader").length;
  const tight = carriers.filter((c) => c.pricing_position === "tight").length;
  const avgCmsn = carriers.length
    ? (carriers.reduce((s, c) => s + c.typical_commission_pct, 0) / carriers.length).toFixed(1)
    : "—";
  const avgWin = carriers.length
    ? Math.round(
        (carriers.reduce((s, c) => s + c.win_rate, 0) / carriers.length) * 100,
      )
    : 0;

  const filtered = useMemo(() => {
    return [...carriers]
      .filter((c) => esg === "all" || c.esg_stance === esg)
      .filter((c) => pricing === "all" || c.pricing_position === pricing)
      .sort((a, b) => b.win_rate - a.win_rate);
  }, [carriers, esg, pricing]);

  const cols: AdminTableCol[] = [
    { key: "carrier", label: "Carrier", width: "1.8fr" },
    { key: "type", label: "Type", width: "1fr" },
    { key: "cmsn", label: "Cmsn", align: "right", width: "90px" },
    { key: "pricing", label: "Pricing", width: "100px" },
    { key: "win", label: "Win rate", align: "right", width: "100px" },
    { key: "esg", label: "ESG", width: "120px" },
    { key: "capacity", label: "Capacity", width: "110px" },
    { key: "appetite", label: "Appetite", width: "1fr" },
  ];

  const rows: AdminTableRow[] = filtered.map((c) => ({
    carrier: (
      <div>
        <div className="font-semibold text-ink">{c.name}</div>
        <Micro className="mt-0.5 block">
          {c.specialties.slice(0, 2).join(" · ")}
        </Micro>
      </div>
    ),
    type: <Caption>{c.type}</Caption>,
    cmsn: (
      <span className="font-semibold tabular-nums text-ink">
        {c.typical_commission_pct.toFixed(1)}%
      </span>
    ),
    pricing: (
      <span
        className={cn(
          "font-semibold capitalize",
          c.pricing_position === "tight"
            ? "text-pos"
            : c.pricing_position === "light"
              ? "text-neg"
              : "text-ink-soft",
        )}
      >
        {c.pricing_position}
      </span>
    ),
    win: (
      <span className="font-bold tabular-nums text-ink">
        {Math.round(c.win_rate * 100)}%
      </span>
    ),
    esg: <EsgCell stance={c.esg_stance} />,
    capacity: <Caption>{c.capacity_band}</Caption>,
    appetite: <AppetiteStrip stances={Object.values(c.appetite_summary)} />,
  }));

  return (
    <>
      <Topbar crumbs={["Broker Portal", "Carrier Intelligence"]} />
      <div className="flex-1 overflow-y-auto px-9 py-7">
        <div className="mx-auto grid max-w-[1400px] gap-4">
          {/* Title + KPIs */}
          <header className="flex flex-wrap items-end justify-between gap-6">
            <div>
              <Eyebrow>Carrier intelligence</Eyebrow>
              <h1 className="mt-1.5 font-display text-[32px] font-semibold leading-tight tracking-tight text-ink">
                The market universe you place into
              </h1>
              <Body className="mt-1.5">
                Appetite, capacity, pricing, ESG stance, and your hit rate per carrier.
              </Body>
            </div>
            <div className="flex flex-wrap gap-7">
              <KpiSnug label="Carriers" value={carriers.length} />
              <KpiSnug label="ESG leaders" value={leaders} tone="pos" />
              <KpiSnug label="Tight pricing" value={tight} />
              <KpiSnug label="Avg cmsn" value={`${avgCmsn}%`} />
              <KpiSnug label="Avg win rate" value={`${avgWin}%`} />
            </div>
          </header>

          {/* Filters */}
          <div className="flex flex-wrap items-center gap-2">
            <Micro className="mr-1">ESG:</Micro>
            <FilterChip label="All" active={esg === "all"} onClick={() => setEsg("all")} />
            <FilterChip
              label="Leader"
              active={esg === "leader"}
              onClick={() => setEsg("leader")}
            />
            <FilterChip
              label="Progressive"
              active={esg === "progressive"}
              onClick={() => setEsg("progressive")}
            />
            <FilterChip
              label="Neutral"
              active={esg === "neutral"}
              onClick={() => setEsg("neutral")}
            />
            <FilterChip
              label="Restrictive"
              active={esg === "restrictive"}
              onClick={() => setEsg("restrictive")}
            />
            <span className="mx-2 h-4 w-px bg-rule" />
            <Micro className="mr-1">Pricing:</Micro>
            <FilterChip
              label="All"
              active={pricing === "all"}
              onClick={() => setPricing("all")}
            />
            <FilterChip
              label="Tight"
              active={pricing === "tight"}
              onClick={() => setPricing("tight")}
            />
            <FilterChip
              label="Median"
              active={pricing === "median"}
              onClick={() => setPricing("median")}
            />
            <FilterChip
              label="Light"
              active={pricing === "light"}
              onClick={() => setPricing("light")}
            />
            <span className="ml-auto">
              <Caption>Sort: by win rate ↓</Caption>
            </span>
          </div>

          {/* Table */}
          <Card pad="none">
            <AdminTable cols={cols} rows={rows} getRowKey={(_, i) => filtered[i]!.slug} />
            {filtered.length === 0 && (
              <div className="px-5 py-8 text-center">
                <Body className="italic">No carriers match the filters.</Body>
              </div>
            )}
          </Card>
        </div>
      </div>
    </>
  );
}

function FilterChip({
  label,
  active,
  onClick,
}: {
  label: string;
  active: boolean;
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={cn(
        "rounded-chip border px-2.5 py-1 text-[11.5px] font-medium transition",
        active
          ? "border-ink bg-ink text-canvas"
          : "border-rule-strong bg-surface text-ink-soft hover:bg-surface-sunken",
      )}
    >
      {label}
    </button>
  );
}

function EsgCell({ stance }: { stance: EsgStance }) {
  const cls =
    stance === "leader"
      ? "text-pos"
      : stance === "progressive"
        ? "text-info"
        : stance === "restrictive"
          ? "text-warn"
          : "text-ink-soft";
  return (
    <span className={cn("flex items-center gap-1.5 font-semibold capitalize", cls)}>
      <Leaf size={12} />
      {stance}
    </span>
  );
}

function AppetiteStrip({ stances }: { stances: AppetiteStance[] }) {
  const display = stances.slice(0, 5);
  return (
    <div
      className="flex gap-1"
      title={`Appetite breadth across ${display.length} lines`}
    >
      {display.map((s, i) => (
        <span
          key={i}
          className={cn(
            "h-3.5 w-2 rounded-sm",
            s === "leaning_in"
              ? "bg-pos"
              : s === "neutral"
                ? "bg-info"
                : s === "selective"
                  ? "bg-warn"
                  : "bg-neg",
          )}
        />
      ))}
      {display.length === 0 && <Micro>—</Micro>}
    </div>
  );
}


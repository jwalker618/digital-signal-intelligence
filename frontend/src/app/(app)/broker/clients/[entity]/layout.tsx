"use client";

import { use, type ReactNode } from "react";
import { usePathname } from "next/navigation";
import {
  CalendarClock,
  Calculator,
  ChartNoAxesGantt,
  Gauge,
  Globe,
  Lightbulb,
  ListChecks,
  MessagesSquare,
  Scale,
  ShieldAlert,
  ShieldCheck,
  TrendingUpDown,
} from "lucide-react";
import { Chip } from "@/components/ui/chip";
import {
  WorkbenchShell,
  type WbNavItem,
} from "@/components/chrome/workbench-shell";
import { PageLoading, PageError } from "@/components/base/pageStates";
import { useRoleScopedFetch } from "@/lib/useRoleScopedFetch";
import { fetchClientWorkbench } from "@/lib/portalApi";
import { useAuthStore } from "@/store/authStore";
import { formatCurrency } from "@/lib/format";
import { ClientWorkbenchContext } from "./_lib/context";

function buildNav(base: string): WbNavItem[] {
  return [
    { kind: "leaf", name: "Summary", icon: Gauge, href: base },
    {
      kind: "group",
      name: "Coverages",
      icon: ShieldCheck,
      children: [
        { name: "Coverage List", icon: ListChecks, href: `${base}/coverages` },
        { name: "Premium Build-up", icon: Calculator, href: `${base}/premium` },
        { name: "Risk Terms", icon: Scale, href: `${base}/terms` },
      ],
    },
    {
      kind: "group",
      name: "Risk Signals",
      icon: ChartNoAxesGantt,
      children: [
        { name: "Score & Cohort", icon: TrendingUpDown, href: `${base}/score` },
        { name: "Loss Profile", icon: ShieldAlert, href: `${base}/loss` },
        { name: "Exposure Profile", icon: Globe, href: `${base}/exposure` },
      ],
    },
    {
      kind: "group",
      name: "Engagement",
      icon: MessagesSquare,
      children: [
        { name: "Communications", icon: MessagesSquare, href: `${base}/comms` },
        { name: "Opportunities & Risks", icon: Lightbulb, href: `${base}/opportunities` },
      ],
    },
    {
      kind: "leaf",
      name: "Pipeline & Renewals",
      icon: CalendarClock,
      href: `${base}/pipeline`,
    },
  ];
}

const SLUG_TO_TAB: Record<string, string> = {
  coverages: "Coverage List",
  premium: "Premium Build-up",
  terms: "Risk Terms",
  score: "Score & Cohort",
  loss: "Loss Profile",
  exposure: "Exposure Profile",
  comms: "Communications",
  opportunities: "Opportunities & Risks",
  pipeline: "Pipeline & Renewals",
};

export default function ClientWorkbenchLayout({
  children,
  params,
}: {
  children: ReactNode;
  params: Promise<{ entity: string }>;
}) {
  const { entity } = use(params);
  const decodedEntity = decodeURIComponent(entity);
  const pathname = usePathname();
  const accessToken = useAuthStore((s) => s.accessToken);

  const base = `/broker/clients/${entity}`;
  const lastSeg = pathname.replace(base, "").replace(/^\//, "").split("/")[0] ?? "";
  const active = lastSeg === "" ? "Summary" : SLUG_TO_TAB[lastSeg] ?? "Summary";

  const { data, error, loading } = useRoleScopedFetch<ClientWorkbenchResponse>({
    fetcher: () => fetchClientWorkbench(accessToken, decodedEntity),
    enabled: !!accessToken,
    deps: [accessToken, decodedEntity],
  });

  const entityName = data?.entity_name ?? decodedEntity;
  const lead = (
    <>
      <span className="text-ink-mute">/</span>
      <div className="flex min-w-0 items-center gap-2">
        <span className="text-[14px] font-bold text-ink">{entityName}</span>
        {data?.industry && (
          <Chip variant="default" size="sm">
            {data.industry}
          </Chip>
        )}
        {data && (
          <Chip variant="info" size="sm">
            {data.coverages.length} coverages
          </Chip>
        )}
      </div>
    </>
  );

  return (
    <WorkbenchShell
      nav={buildNav(base)}
      active={active}
      backLabel="Book"
      backHref="/broker"
      account={{
        initials: "SA",
        name: "Sasha Alvarez",
        email: "sasha.alvarez@marsh.com",
      }}
      scope={{
        label: "Client",
        lines: [
          entityName,
          data
            ? `${data.coverages.length} coverages · ${formatCurrency(data.total_premium)} premium`
            : "",
        ],
      }}
      lead={lead}
      contextStats={[
        {
          label: "Total premium",
          value: data ? formatCurrency(data.total_premium) : "—",
          tone: "info",
        },
        { label: "Avg score", value: data?.avg_score ?? "—" },
        { label: "Engagement", value: data?.engagement_label ?? "—" },
      ]}
    >
      <ClientWorkbenchContext.Provider value={data ?? null}>
        {loading && !data ? (
          <PageLoading message="Loading client…" />
        ) : error ? (
          <PageError message={error} />
        ) : (
          children
        )}
      </ClientWorkbenchContext.Provider>
    </WorkbenchShell>
  );
}

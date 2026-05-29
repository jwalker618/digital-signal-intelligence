"use client";

import { use, useEffect, type ReactNode } from "react";
import { usePathname } from "next/navigation";
import {
  Building2,
  Calculator,
  ChartNoAxesGantt,
  Clock,
  FileCheck,
  FileStack,
  FileText,
  FlaskConical,
  Gauge,
  Glasses,
  Globe,
  Layers,
  Network,
  RefreshCw,
  Scale,
  ShieldAlert,
  TrendingUpDown,
  UserStar,
} from "lucide-react";
import { Chip } from "@/components/ui/chip";
import {
  WorkbenchShell,
  type WbNavItem,
} from "@/components/chrome/workbench-shell";
import { useDsiStore } from "@/store/dsiStore";
import { formatCurrency } from "@/lib/format";

/* Carrier submission workbench — drill-down nav mirrors the revised
 * design pack's DRILL_NAV (reim_carrier_workbench_shell.jsx). */
function buildNav(base: string): WbNavItem[] {
  return [
    { kind: "leaf", name: "Summary", icon: Gauge, href: base },
    {
      kind: "group",
      name: "Commercial Terms",
      icon: Building2,
      children: [
        { name: "Terms Overview", icon: FileText, href: `${base}/terms` },
        { name: "Premium Assembly", icon: Calculator, href: `${base}/premium` },
        { name: "Distribution", icon: Network, href: `${base}/distribution` },
      ],
    },
    {
      kind: "group",
      name: "Risk Terms",
      icon: Scale,
      children: [
        { name: "Deductible Structure", icon: Layers, href: `${base}/deductible` },
        { name: "Coverage Terms", icon: FileCheck, href: `${base}/coverage` },
        { name: "SIR & Waiting Periods", icon: Clock, href: `${base}/sir` },
        { name: "Aggregate & Reinstatement", icon: RefreshCw, href: `${base}/aggregate` },
      ],
    },
    {
      kind: "group",
      name: "Technical Assessment",
      icon: ChartNoAxesGantt,
      children: [
        { name: "Pricing Anatomy", icon: Calculator, href: `${base}/pricing` },
        { name: "Risk Assessment", icon: Glasses, href: `${base}/risk` },
        { name: "Loss Assessment", icon: ShieldAlert, href: `${base}/loss` },
        { name: "Exposure Assessment", icon: Globe, href: `${base}/exposure` },
        { name: "Scenarios", icon: FlaskConical, href: `${base}/scenarios` },
        { name: "Referral Actions", icon: UserStar, href: `${base}/referral` },
        { name: "Model Versions", icon: FileStack, href: `${base}/versions` },
      ],
    },
  ];
}

// Last-path-segment → tab display name. Summary when on the base.
const SLUG_TO_TAB: Record<string, string> = {
  terms: "Terms Overview",
  premium: "Premium Assembly",
  distribution: "Distribution",
  deductible: "Deductible Structure",
  coverage: "Coverage Terms",
  sir: "SIR & Waiting Periods",
  aggregate: "Aggregate & Reinstatement",
  pricing: "Pricing Anatomy",
  risk: "Risk Assessment",
  loss: "Loss Assessment",
  exposure: "Exposure Assessment",
  scenarios: "Scenarios",
  referral: "Referral Actions",
  versions: "Model Versions",
};

export default function WorkbenchLayout({
  children,
  params,
}: {
  children: ReactNode;
  params: Promise<{ code: string }>;
}) {
  const { code } = use(params);
  const pathname = usePathname();
  const submissions = useDsiStore((s) => s.submissions);
  const activeCode = useDsiStore(
    (s) => s.activeSubmission?.submission_code as string | undefined,
  );
  const sub = useDsiStore((s) => s.activeSubmission);
  const ver = useDsiStore((s) => s.activeVersion);
  const fetchSubmissions = useDsiStore((s) => s.fetchSubmissions);
  const fetchCore = useDsiStore((s) => s.fetchCoreSubmissionDetail);
  const prefetchTabs = useDsiStore((s) => s.prefetchWorkbenchTabs);

  const base = `/carrier/submissions/${code}`;
  const lastSeg = pathname.replace(`${base}`, "").replace(/^\//, "").split("/")[0] ?? "";
  const active = lastSeg === "" ? "Summary" : SLUG_TO_TAB[lastSeg] ?? "Summary";

  // Load the pipeline, activate this submission, then fan out a
  // fire-and-forget preload of every tab's data (perf retention).
  useEffect(() => {
    if (activeCode === code) return;
    let cancelled = false;
    (async () => {
      let pool = submissions;
      if (pool.length === 0) {
        try {
          await fetchSubmissions();
          pool = useDsiStore.getState().submissions;
        } catch {
          return;
        }
      }
      if (cancelled) return;
      const row = pool.find((s) => s.submission_code === code);
      if (row) {
        try {
          await fetchCore(row);
        } catch {
          /* tab pages render their own empty/error state */
        }
        if (!cancelled) prefetchTabs().catch(() => undefined);
      }
    })();
    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [code]);

  const entity = (sub?.entity_name as string | undefined) ?? "Loading…";
  const coverage = sub?.coverage as string | undefined;
  const decision = String(ver?.decision ?? sub?.decision ?? "").toUpperCase();
  const broker = (sub?.broker_name as string | undefined) ?? "Marsh";
  const score = ver?.final_composite_score ?? ver?.pure_composite_score ?? null;
  const tier = ver?.final_tier ?? null;
  const premium = ver?.final_premium ?? sub?.final_premium ?? sub?.recommended_premium ?? null;

  const lead = (
    <>
      <span className="text-ink-mute">/</span>
      <code className="text-[12px] text-ink-mute">{code}</code>
      <span className="text-ink-mute">·</span>
      <div className="flex min-w-0 items-center gap-2">
        <span className="text-[14px] font-bold text-ink">{entity}</span>
        {coverage && (
          <Chip variant="default" size="sm">
            {coverage}
          </Chip>
        )}
        {active !== "Summary" && decision && (
          <Chip variant="spot" size="sm">
            {decision}
          </Chip>
        )}
        <span className="ml-0.5 text-[11px] text-ink-mute">via {broker}</span>
      </div>
    </>
  );

  return (
    <WorkbenchShell
      nav={buildNav(base)}
      active={active}
      backLabel="Pipeline"
      backHref="/carrier"
      account={{
        initials: "JR",
        name: "Jordan Reyes",
        email: "jordan.reyes@hartfordmutual.com",
      }}
      scope={{ label: "Submission", lines: [`${code} · ${entity}`] }}
      lead={lead}
      contextStats={[
        {
          label: "Score",
          value: score != null ? Number(score).toFixed(0) : "—",
          tone: "info",
        },
        { label: "Tier", value: tier != null ? `T${tier}` : "—" },
        {
          label: "Premium",
          value: premium != null ? formatCurrency(Number(premium)) : "—",
        },
      ]}
    >
      {children}
    </WorkbenchShell>
  );
}

"use client";

import { useEffect, useMemo, useState } from "react";
import { Activity, Bot, ShieldCheck, ShieldX, ShieldQuestion } from "lucide-react";
import { Topbar } from "@/components/chrome/topbar";
import { Card } from "@/components/ui/card";
import { Eyebrow, NumDisplay, Body, Micro } from "@/components/ui/typography";
import { PageError, PageLoading, RoleGate } from "@/components/base/pageStates";
import { CarrierShell } from "@/components/chrome/carrier-shell";
import { isCarrierRole } from "@/lib/portalPaths";
import { useAuthStore } from "@/store/authStore";
import { useDsiStore } from "@/store/dsiStore";
import { formatCurrency, formatPercent } from "@/lib/format";

export default function CarrierMetricsPage() {
  const user = useAuthStore((s) => s.user);
  const submissions = useDsiStore((s) => s.submissions);
  const fetchSubmissions = useDsiStore((s) => s.fetchSubmissions);
  const [state, setState] = useState<"loading" | "ok" | "error">(
    submissions.length > 0 ? "ok" : "loading",
  );
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    fetchSubmissions()
      .then(() => !cancelled && setState("ok"))
      .catch((e) => {
        if (cancelled) return;
        setErr(e instanceof Error ? e.message : String(e));
        setState("error");
      });
    return () => {
      cancelled = true;
    };
  }, [fetchSubmissions]);

  const inner =
    !user ? (
      <PageLoading message="Signing in…" />
    ) : user.role && !isCarrierRole(user.role) ? (
      <RoleGate expected="carrier" />
    ) : state === "loading" ? (
      <PageLoading />
    ) : state === "error" ? (
      <PageError message={err ?? "Unknown error"} />
    ) : (
      <MetricsBody submissions={submissions} />
    );

  return <CarrierShell>{inner}</CarrierShell>;
}

function MetricsBody({ submissions }: { submissions: Record<string, unknown>[] }) {
  const stats = useMemo(() => {
    const total = submissions.length;
    let approve = 0,
      refer = 0,
      decline = 0,
      pending = 0;
    let premiumApproved = 0,
      premiumReferred = 0;
    let scoreSum = 0,
      scoreCount = 0;
    const byCoverage = new Map<string, number>();
    for (const s of submissions) {
      const dec = String(s.decision ?? "").toLowerCase();
      if (dec === "approve") approve++;
      else if (dec === "decline") decline++;
      else if (dec === "refer") refer++;
      else pending++;
      const prem = Number(s.final_premium ?? s.recommended_premium ?? 0);
      if (dec === "approve") premiumApproved += prem;
      else if (dec === "refer") premiumReferred += prem;
      const sc = s.composite_score;
      if (typeof sc === "number") {
        scoreSum += sc;
        scoreCount++;
      }
      const cov = String(s.coverage ?? "Unknown");
      byCoverage.set(cov, (byCoverage.get(cov) ?? 0) + 1);
    }
    const auto = total > 0 ? approve / total : 0;
    const referRate = total > 0 ? refer / total : 0;
    const meanScore = scoreCount > 0 ? scoreSum / scoreCount : 0;
    return {
      total,
      approve,
      refer,
      decline,
      pending,
      premiumApproved,
      premiumReferred,
      auto,
      referRate,
      meanScore,
      byCoverage: [...byCoverage.entries()].sort((a, b) => b[1] - a[1]),
    };
  }, [submissions]);

  return (
    <>
      <Topbar crumbs={["Carrier Portal", "Performance Metrics"]} />
      <div className="flex-1 overflow-y-auto px-9 py-7">
        <div className="mx-auto grid max-w-[1400px] gap-6">
          <header>
            <Eyebrow>Underwriting</Eyebrow>
            <h1 className="mt-1 font-display text-[32px] font-semibold leading-none tracking-tight text-ink">
              Performance Metrics
            </h1>
            <Body className="mt-2">
              Engine throughput, decision mix, and premium under management.
            </Body>
          </header>

          {/* Hero KPIs */}
          <div className="grid gap-4 md:grid-cols-4">
            <Stat variant="info" icon={Activity} label="Submissions in pipeline">
              {stats.total}
            </Stat>
            <Stat variant="pos" icon={ShieldCheck} label="Auto-approve rate">
              {formatPercent(stats.auto, 0)}
            </Stat>
            <Stat variant="warn" icon={ShieldQuestion} label="Referral rate">
              {formatPercent(stats.referRate, 0)}
            </Stat>
            <Stat variant="default" icon={Bot} label="Mean composite score">
              {stats.meanScore > 0 ? stats.meanScore.toFixed(0) : "—"}
            </Stat>
          </div>

          {/* Decision mix */}
          <Card pad="lg" className="space-y-4">
            <Eyebrow>Decision mix</Eyebrow>
            <div className="grid grid-cols-2 gap-6 md:grid-cols-4">
              <DecisionTile
                tone="pos"
                icon={ShieldCheck}
                label="Approve"
                count={stats.approve}
                total={stats.total}
              />
              <DecisionTile
                tone="warn"
                icon={ShieldQuestion}
                label="Refer"
                count={stats.refer}
                total={stats.total}
              />
              <DecisionTile
                tone="neg"
                icon={ShieldX}
                label="Decline"
                count={stats.decline}
                total={stats.total}
              />
              <DecisionTile
                tone="mute"
                icon={Activity}
                label="Pending"
                count={stats.pending}
                total={stats.total}
              />
            </div>
          </Card>

          {/* Premium */}
          <Card pad="lg" className="grid gap-6 md:grid-cols-2">
            <div>
              <Eyebrow className="text-pos">Premium approved</Eyebrow>
              <NumDisplay size="xl" className="mt-2 block text-pos">
                {formatCurrency(stats.premiumApproved)}
              </NumDisplay>
              <Micro className="mt-1 block">across {stats.approve} submissions</Micro>
            </div>
            <div>
              <Eyebrow className="text-warn">Premium under review</Eyebrow>
              <NumDisplay size="xl" className="mt-2 block text-warn">
                {formatCurrency(stats.premiumReferred)}
              </NumDisplay>
              <Micro className="mt-1 block">across {stats.refer} referrals</Micro>
            </div>
          </Card>

          {/* Coverage mix */}
          <Card pad="lg">
            <Eyebrow className="mb-3">Coverage mix</Eyebrow>
            <ul className="space-y-2">
              {stats.byCoverage.slice(0, 10).map(([name, count]) => (
                <li key={name}>
                  <div className="flex items-baseline justify-between text-[13px]">
                    <span className="font-medium text-ink">{name}</span>
                    <span className="font-semibold tabular-nums text-ink">
                      {count}
                    </span>
                  </div>
                  <div className="mt-1 h-1.5 overflow-hidden rounded-full bg-surface-sunken">
                    <div
                      className="h-full bg-info"
                      style={{ width: `${(count / stats.total) * 100}%` }}
                    />
                  </div>
                </li>
              ))}
            </ul>
          </Card>
        </div>
      </div>
    </>
  );
}

function Stat({
  variant,
  icon: Icon,
  label,
  children,
}: {
  variant: "info" | "pos" | "warn" | "default";
  icon: typeof Activity;
  label: string;
  children: React.ReactNode;
}) {
  return (
    <Card pad="md" variant={variant}>
      <div className="flex items-center gap-2">
        <Icon
          size={14}
          className={
            variant === "info"
              ? "text-info-deep dark:text-info"
              : variant === "pos"
                ? "text-pos"
                : variant === "warn"
                  ? "text-warn"
                  : "text-ink-mute"
          }
        />
        <Micro>{label}</Micro>
      </div>
      <NumDisplay size="lg" className="mt-2 block">
        {children}
      </NumDisplay>
    </Card>
  );
}

function DecisionTile({
  tone,
  icon: Icon,
  label,
  count,
  total,
}: {
  tone: "pos" | "warn" | "neg" | "mute";
  icon: typeof Activity;
  label: string;
  count: number;
  total: number;
}) {
  const pct = total > 0 ? count / total : 0;
  return (
    <div>
      <div
        className={`flex items-center gap-2 ${
          tone === "pos"
            ? "text-pos"
            : tone === "warn"
              ? "text-warn"
              : tone === "neg"
                ? "text-neg"
                : "text-ink-mute"
        }`}
      >
        <Icon size={14} />
        <Micro>{label}</Micro>
      </div>
      <div className="mt-1 flex items-baseline gap-2">
        <span className="font-display text-[26px] font-semibold tabular-nums text-ink">
          {count}
        </span>
        <span className="text-[12.5px] text-ink-mute tabular-nums">
          {formatPercent(pct, 0)}
        </span>
      </div>
    </div>
  );
}

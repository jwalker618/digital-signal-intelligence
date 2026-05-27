"use client";

// v8.2 Book Health — /portal/portfolio
//
// Rebuilt from the v8.1 portfolio metrics page into a richer broker-
// health view: retention, lines-per-client, cross-sell, tenure,
// commission yield, plus the concentration breakdowns. The "Risk
// Aggregation" page goes deeper on peril exposure; this one is the
// business health view.

import { useEffect, useState } from "react";
import {
  AlertTriangle,
  ChartPie,
  HeartPulse,
  Layers,
  ShieldCheck,
  TrendingUp,
  Users,
} from "lucide-react";

import ViewCanvas from "@/components/ViewCanvas";
import VerticalFilter from "@/components/portal/VerticalFilter";
import {
  CardGrid,
  StandardCard,
  SubmissionHeaderCard,
} from "@/components/base/cards";
import {
  InfoPanel,
  KpiTile,
  LabelValueList,
  NoData,
  ScoreBar,
  StatsGrid,
} from "@/components/base/content/primatives";

import { useAuthStore } from "@/store/authStore";
import { useDsiStore } from "@/store/dsiStore";
import { fetchBookHealth, fetchVerticals } from "@/lib/portalApi";
import { formatCurrency, formatNumber } from "@/lib/format";
import type {
  BookHealthResponse,
  VerticalSummary,
} from "@/types/portal";


export default function BookHealthPage() {
  const accessToken = useAuthStore((s) => s.accessToken);
  const userRole = useAuthStore((s) => s.user?.role ?? null);
  const setActiveMenu = useDsiStore((s) => s.setActiveMenu);

  const [data, setData] = useState<BookHealthResponse | null>(null);
  const [verticals, setVerticals] = useState<VerticalSummary[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => { setActiveMenu("Book Health"); }, [setActiveMenu]);

  useEffect(() => {
    let cancelled = false;
    async function load() {
      try {
        const [book, verts] = await Promise.all([
          fetchBookHealth(accessToken),
          fetchVerticals(accessToken),
        ]);
        if (cancelled) return;
        setData(book);
        setVerticals(verts.verticals);
      } catch (e) {
        if (!cancelled) setError(e instanceof Error ? e.message : String(e));
      }
    }
    if (accessToken && userRole === "BROKER") load();
    return () => { cancelled = true; };
  }, [accessToken, userRole]);

  if (userRole !== "BROKER") return <BrokerOnly />;
  if (error) return <ErrShell msg={error} />;
  if (!data) return <LoadShell />;

  const verticalLookup: Record<string, VerticalSummary> = Object.fromEntries(
    verticals.map((v) => [v.slug, v]),
  );

  return (
    <ViewCanvas>
      <CardGrid cols="grid-cols-1" className="gap-4">

        <SubmissionHeaderCard
          decision="approve"
          title={`Book Health — ${data.broker_name}`}
          subtitle="Retention, depth of relationship, profitability"
          lucideIcon={HeartPulse}
        >
          <StatsGrid
            columns={[
              { label: "Clients",         value: data.client_count, align: "center" },
              { label: "Policies",        value: data.policy_count, align: "center" },
              { label: "Total premium",   value: formatCurrency(data.total_premium_usd, 0), align: "center" },
              { label: "Est. commission", value: formatCurrency(data.total_estimated_commission_usd, 0), align: "center" },
              { label: "Commission yield", value: `${data.commission_yield_pct.toFixed(1)}%`, align: "center" },
            ]}
          />
        </SubmissionHeaderCard>

        <VerticalFilter />

        <CardGrid cols="grid-cols-1 lg:grid-cols-3" className="gap-4">
          <StandardCard title="Retention" lucideIcon={TrendingUp}>
            <div className="space-y-3 py-2">
              <KpiTile
                label="Annual retention rate"
                value={`${data.retention_rate_pct.toFixed(1)}%`}
                variant="emphasis"
                subtext="Indicative — production wires actual renewals"
              />
              <ScoreBar
                value={data.retention_rate_pct}
                min={70}
                max={100}
                decimals={1}
                thresholds={[
                  { at: 80, color: "var(--color-generate-text-maybe)" },
                  { at: 90, color: "var(--color-generate-text-comment)" },
                  { at: Infinity, color: "var(--color-generate-text-good)" },
                ]}
              />
              <KpiTile
                label="Average tenure"
                value={`${formatNumber(data.avg_tenure_months, 0)} mo`}
                subtext={`~${formatNumber(data.avg_tenure_months / 12, 1)} yrs`}
              />
            </div>
          </StandardCard>

          <StandardCard title="Depth of relationship" lucideIcon={Layers}>
            <div className="space-y-3 py-2">
              <KpiTile
                label="Avg lines per client"
                value={data.avg_lines_per_client.toFixed(2)}
                variant="emphasis"
              />
              <KpiTile
                label="Cross-sell ratio (≥3 lines)"
                value={`${data.cross_sell_ratio_pct.toFixed(0)}%`}
                subtext="Share of clients holding 3+ lines"
              />
              <KpiTile
                label="Avg premium / client"
                value={formatCurrency(data.avg_premium_per_client, 0)}
              />
            </div>
          </StandardCard>

          <StandardCard title="Profitability" lucideIcon={ChartPie}>
            <div className="space-y-3 py-2">
              <KpiTile
                label="Commission yield"
                value={`${data.commission_yield_pct.toFixed(1)}%`}
                variant="emphasis"
                subtext="Book-weighted average"
              />
              <KpiTile
                label="Total estimated commission"
                value={formatCurrency(data.total_estimated_commission_usd, 0)}
              />
              <p className="text-xs text-generate-text-placeholder">
                Production wires actual broker remuneration including
                contingent commissions and override agreements.
              </p>
            </div>
          </StandardCard>
        </CardGrid>

        <CardGrid cols="grid-cols-1 lg:grid-cols-2" className="gap-4">
          <StandardCard title="Premium by vertical" lucideIcon={Users}>
            <VerticalBreakdown
              counts={data.vertical_concentration}
              total={data.policy_count}
              verticals={verticalLookup}
            />
          </StandardCard>

          <StandardCard title="Premium by coverage line" lucideIcon={ShieldCheck}>
            <LineBreakdown
              counts={data.lines_concentration}
              total={data.policy_count}
            />
          </StandardCard>
        </CardGrid>

        <InfoPanel label="What's driving the book" aside="v8.2 demo">
          <p className="text-xs">
            Retention and tenure metrics are synthesised for the demo;
            production wires actual renewal history. Commission yield
            and per-line / per-vertical breakdowns are computed live
            from the broker's actual book of placed policies. Use
            Risk Aggregation for peril-level concentration narratives.
          </p>
        </InfoPanel>

      </CardGrid>
    </ViewCanvas>
  );
}


function VerticalBreakdown({
  counts, total, verticals,
}: {
  counts: Record<string, number>;
  total: number;
  verticals: Record<string, VerticalSummary>;
}) {
  const rows = Object.entries(counts)
    .filter(([, c]) => c > 0)
    .sort(([, a], [, b]) => b - a);

  if (rows.length === 0) {
    return <NoData message="No policies in any vertical yet." />;
  }

  return (
    <div className="space-y-2 py-2">
      {rows.map(([slug, count]) => {
        const v = verticals[slug];
        const sharePct = total ? (count / total) * 100 : 0;
        return (
          <div
            key={slug}
            className="grid items-center gap-3"
            style={{ gridTemplateColumns: "1.5fr 1fr 60px" }}
          >
            <div>
              <div className="text-sm font-bold">{v?.name ?? slug}</div>
              {v?.summary && (
                <div className="text-[10px] text-generate-text-placeholder">
                  {v.summary}
                </div>
              )}
            </div>
            <ScoreBar
              value={sharePct}
              min={0}
              max={100}
              decimals={0}
              hideValue
              thresholds={[
                { at: 25, color: "var(--color-generate-text-good)" },
                { at: 50, color: "var(--color-generate-text-comment)" },
                { at: Infinity, color: "var(--color-generate-text-maybe)" },
              ]}
            />
            <div className="text-right text-sm">
              <span className="font-bold">{count}</span>
              <span className="text-xs text-generate-text-placeholder ml-1">
                ({sharePct.toFixed(0)}%)
              </span>
            </div>
          </div>
        );
      })}
    </div>
  );
}


function LineBreakdown({
  counts, total,
}: {
  counts: Record<string, number>;
  total: number;
}) {
  const rows = Object.entries(counts).sort(([, a], [, b]) => b - a);

  if (rows.length === 0) {
    return <NoData message="No policies placed yet." />;
  }

  return (
    <div className="space-y-2 py-2">
      {rows.map(([line, count]) => {
        const sharePct = total ? (count / total) * 100 : 0;
        return (
          <div
            key={line}
            className="grid items-center gap-3"
            style={{ gridTemplateColumns: "1fr 1fr 60px" }}
          >
            <span className="text-sm font-bold capitalize">{line}</span>
            <ScoreBar
              value={sharePct}
              min={0}
              max={100}
              decimals={0}
              hideValue
              thresholds={[
                { at: 25, color: "var(--color-generate-text-good)" },
                { at: 50, color: "var(--color-generate-text-comment)" },
                { at: Infinity, color: "var(--color-generate-text-maybe)" },
              ]}
            />
            <div className="text-right text-sm">
              <span className="font-bold">{count}</span>
              <span className="text-xs text-generate-text-placeholder ml-1">
                ({sharePct.toFixed(0)}%)
              </span>
            </div>
          </div>
        );
      })}
    </div>
  );
}


function LoadShell() {
  return (
    <ViewCanvas>
      <CardGrid cols="grid-cols-1">
        <StandardCard title="Loading" lucideIcon={HeartPulse}>
          <NoData message="Loading book health…" />
        </StandardCard>
      </CardGrid>
    </ViewCanvas>
  );
}

function ErrShell({ msg }: { msg: string }) {
  return (
    <ViewCanvas>
      <CardGrid cols="grid-cols-1">
        <StandardCard title="Unable to load" lucideIcon={AlertTriangle}>
          <NoData message={msg} />
        </StandardCard>
      </CardGrid>
    </ViewCanvas>
  );
}

function BrokerOnly() {
  return (
    <ViewCanvas>
      <CardGrid cols="grid-cols-1">
        <StandardCard title="Broker-only" lucideIcon={AlertTriangle}>
          <NoData message="Book Health is for broker users only." />
        </StandardCard>
      </CardGrid>
    </ViewCanvas>
  );
}

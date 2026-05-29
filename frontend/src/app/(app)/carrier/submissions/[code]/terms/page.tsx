"use client";

import { Building2, Calendar, HandCoins, Layers } from "lucide-react";
import { Card } from "@/components/ui/card";
import { WorkArea } from "@/components/ui/work-area";
import { Eyebrow, Micro } from "@/components/ui/typography";
import { LabelRow } from "@/components/ui/label-row";
import { PageLoading } from "@/components/base/pageStates";
import { useDsiStore, type ApiRecord } from "@/store/dsiStore";
import { formatCurrency, formatDate, formatText } from "@/lib/format";
import { numOrNull, strOrNull, pctOrNull } from "@/lib/coerce";

/* ============================================================
 * Terms Overview — mirrors reim_wb_c.jsx WbCommercial.
 *
 * Four stacked rows:
 *   1. Hero info-tone card: Offered premium (44px) + net / gross /
 *      technical stats
 *   2. Two-col: Insured entity + Policy period (2-col DefLists each)
 *   3. Two-col: Premium ladder + Commission structure
 *      (Premium ladder is the compact build-up: technical → commission →
 *       net → taxes → gross → discretion → offered)
 * ============================================================ */

type Rung = {
  label: string;
  value: number | null;
  rate?: string;
  tone: "muted" | "neg" | "warn" | "sub" | "final";
};

export default function TermsOverviewPage() {
  const sub = useDsiStore((s) => s.activeSubmission) as ApiRecord | null;
  const ver = useDsiStore((s) => s.activeVersion) as ApiRecord | null;
  const commercial = useDsiStore((s) => s.activeCommercial) as ApiRecord | null;
  const quote = useDsiStore((s) => s.activeQuote) as ApiRecord | null;

  if (!commercial) {
    return (
      <>
        <PageLoading />
      </>
    );
  }

  const technicalPremium = numOrNull(
    commercial.technical_premium_usd ??
      commercial.technical_premium_local ??
      ver?.final_premium,
  );
  const netPremium = numOrNull(commercial.net_premium);
  const grossPremium = numOrNull(commercial.gross_premium);
  const offeredPremium = numOrNull(commercial.offered_premium);
  const discretionPct = pctOrNull(commercial.offered_premium_discretion);
  const totalCommission = numOrNull(commercial.total_commission);
  const totalTaxes = numOrNull(commercial.total_taxes);

  const entityName = strOrNull(sub?.entity_name);
  const entityId = strOrNull(sub?.entity_id ?? sub?.id);
  const market = strOrNull(sub?.country) ?? strOrNull(commercial.base_currency_market);
  const baseCurrency = strOrNull(commercial.base_currency) ?? "USD";

  const writtenDate = strOrNull(quote?.created_at ?? quote?.valid_from);
  const earnedStart = strOrNull(commercial.earned_start ?? quote?.valid_from);
  const earnedEnd = strOrNull(commercial.earned_end ?? quote?.valid_until);
  const earningMethod = strOrNull(commercial.earning_method ?? "straight_line");

  const deductions = (commercial.deductions as Record<string, ApiRecord> | undefined) ?? {};
  const brokerageRate = pctOrNull(deductions.brokerage?.rate);
  const overriderRate = pctOrNull(deductions.overrider?.rate);
  const profitCommissionRate = pctOrNull(deductions.profit_commission?.rate);

  const rungs: Rung[] = [
    { label: "Technical premium", value: technicalPremium, tone: "muted" },
    {
      label: "Total commission",
      value: totalCommission != null ? -totalCommission : null,
      tone: "neg",
    },
    { label: "Net premium", value: netPremium, tone: "sub" },
    {
      label: "Taxes & levies",
      value: totalTaxes != null ? totalTaxes : null,
      tone: "warn",
    },
    { label: "Gross premium", value: grossPremium, tone: "sub" },
    {
      label: "Discretion",
      value:
        discretionPct != null && grossPremium != null
          ? grossPremium * (discretionPct / 100)
          : 0,
      rate: discretionPct != null ? `${discretionPct.toFixed(1)}%` : "—",
      tone: "muted",
    },
    { label: "Offered premium", value: offeredPremium, tone: "final" },
  ];

  return (
    <>
      <WorkArea>
        {/* ─── 1. Hero ──────────────────────────────────────── */}
        <Card variant="info" pad="lg">
          <div className="grid grid-cols-1 items-center gap-8 lg:grid-cols-[1fr_auto_auto_auto]">
            <div>
              <Eyebrow className="text-info-deep dark:text-info">
                Offered premium
              </Eyebrow>
              <div className="mt-1.5 font-display text-[44px] font-semibold leading-none text-info-deep dark:text-info">
                {offeredPremium != null ? formatCurrency(offeredPremium) : "—"}
              </div>
              <Micro className="mt-2 block">
                at gross ·{" "}
                {discretionPct != null
                  ? `${discretionPct.toFixed(1)}% discretion applied`
                  : "no discretion recorded"}
              </Micro>
            </div>
            <HeroStat label="Net" value={netPremium} />
            <HeroStat label="Gross" value={grossPremium} />
            <HeroStat label="Technical" value={technicalPremium} muted />
          </div>
        </Card>

        {/* ─── 2. Entity + Period ──────────────────────────── */}
        <div className="grid gap-3.5 lg:grid-cols-[1.4fr_1fr]">
          <Card header="Insured entity" icon={Building2} pad="md">
            <div className="grid grid-cols-1 gap-x-6 md:grid-cols-2">
              <LabelRow label="Entity name" value={entityName ?? "—"} />
              <LabelRow
                label="Entity ID"
                value={
                  entityId ? <span className="font-mono">{entityId}</span> : "—"
                }
              />
              <LabelRow
                label="Market"
                value={market ? formatText(market, "capitalize") : "—"}
              />
              <LabelRow label="Base currency" value={baseCurrency} />
            </div>
          </Card>
          <Card header="Policy period" icon={Calendar} pad="md">
            <div className="grid grid-cols-1 gap-x-6 md:grid-cols-2">
              <LabelRow
                label="Written date"
                value={writtenDate ? formatDate(writtenDate) : "—"}
              />
              <LabelRow
                label="Earned start"
                value={earnedStart ? formatDate(earnedStart) : "—"}
              />
              <LabelRow
                label="Earned end"
                value={earnedEnd ? formatDate(earnedEnd) : "—"}
              />
              <LabelRow
                label="Method"
                value={
                  earningMethod
                    ? formatText(earningMethod.replace(/_/g, " "), "capitalize")
                    : "—"
                }
              />
            </div>
          </Card>
        </div>

        {/* ─── 3. Premium ladder + Commission ──────────────── */}
        <div className="grid gap-3.5 lg:grid-cols-[1.4fr_1fr]">
          <Card header="Premium ladder" icon={Layers} pad="md">
            <PremiumLadder rungs={rungs} />
          </Card>
          <Card header="Commission structure" icon={HandCoins} pad="md">
            <div className="grid grid-cols-1 gap-x-6 md:grid-cols-2">
              <LabelRow
                label="Brokerage"
                value={brokerageRate != null ? `${brokerageRate.toFixed(1)}%` : "—"}
              />
              <LabelRow
                label="Overrider"
                value={overriderRate != null ? `${overriderRate.toFixed(1)}%` : "—"}
              />
              <LabelRow
                label="Profit commission"
                value={
                  profitCommissionRate != null
                    ? `${profitCommissionRate.toFixed(1)}%`
                    : "—"
                }
              />
            </div>
            <div className="mt-3.5 flex items-baseline justify-between border-t border-ink-soft pt-3.5">
              <span className="text-[13px] font-bold">Total commission</span>
              <span className="font-mono text-[17px] font-bold tabular-nums">
                {totalCommission != null ? formatCurrency(totalCommission) : "—"}
              </span>
            </div>
            <Micro className="mt-2 block">
              Earned on net premium · paid to the broker on placement.
            </Micro>
          </Card>
        </div>
      </WorkArea>
    </>
  );
}

function HeroStat({
  label,
  value,
  muted,
}: {
  label: string;
  value: number | null;
  muted?: boolean;
}) {
  return (
    <div>
      <Micro>{label}</Micro>
      <div
        className={`mt-1 font-mono text-[22px] font-semibold tabular-nums ${
          muted ? "text-ink-soft" : "text-ink"
        }`}
      >
        {value != null ? formatCurrency(value) : "—"}
      </div>
    </div>
  );
}

function PremiumLadder({ rungs }: { rungs: Rung[] }) {
  return (
    <div>
      {rungs.map((r, i) => {
        const isSub = r.tone === "sub";
        const isFinal = r.tone === "final";
        const isLast = i === rungs.length - 1;
        const labelTone = r.tone === "muted" ? "text-ink-soft" : "text-ink";
        const valueTone =
          r.tone === "muted"
            ? "text-ink-soft"
            : r.tone === "neg"
              ? "text-neg"
              : r.tone === "warn"
                ? "text-warn"
                : r.tone === "final"
                  ? "text-info-deep dark:text-info"
                  : "text-ink";
        const valueSize =
          r.tone === "final" ? "text-[22px]" : isSub ? "text-[16px]" : "text-[13px]";
        const padding = isFinal ? "py-3.5" : isSub ? "py-2.5" : "py-1.5";
        const border = isSub
          ? "border-t border-ink-soft mt-1"
          : isFinal
            ? "border-t-2 border-ink mt-1"
            : !isLast
              ? "border-b border-rule"
              : "";
        return (
          <div
            key={r.label}
            className={`flex items-baseline justify-between px-1 ${padding} ${border}`}
          >
            <span
              className={`${labelTone} ${
                isFinal
                  ? "text-[14px] font-bold uppercase tracking-wider"
                  : isSub
                    ? "text-[13px] font-bold"
                    : "text-[13px] font-medium"
              }`}
            >
              {r.label}
              {r.rate && r.tone === "muted" && (
                <Micro className="ml-2 inline">{r.rate}</Micro>
              )}
            </span>
            <span
              className={`font-mono font-bold tabular-nums ${valueSize} ${valueTone}`}
            >
              {r.value != null
                ? r.value === 0
                  ? r.rate ?? "—"
                  : `${r.value < 0 ? "−" : r.tone === "warn" ? "+" : ""}${formatCurrency(Math.abs(r.value))}`
                : "—"}
            </span>
          </div>
        );
      })}
    </div>
  );
}




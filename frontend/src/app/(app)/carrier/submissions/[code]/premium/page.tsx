"use client";

import { AlertTriangle, Calculator, SlidersHorizontal } from "lucide-react";
import { Card } from "@/components/ui/card";
import { WorkArea } from "@/components/ui/work-area";
import { Eyebrow, Micro } from "@/components/ui/typography";
import { KpiSnug } from "@/components/ui/kpi-snug";
import { PageLoading } from "@/components/base/pageStates";
import { useDsiStore, type ApiRecord } from "@/store/dsiStore";
import { formatCurrency } from "@/lib/format";

/* ============================================================
 * Premium Assembly — mirrors reim_wb_b.jsx WbPremium (section 05).
 *
 * Three rows via WorkArea:
 *   1. Hero — offered premium info-tone card with side-by-side net /
 *      gross / technical
 *   2. Premium build-up ledger (technical → deductions → net → taxes →
 *      gross → discretion → offered)
 *   3. Two-col footer: Minimum premium check + Discretion analysis
 * ============================================================ */

type JsonbDed = { rate?: number; amount?: number };
type Deductions = Record<string, JsonbDed>;
type Taxes = Record<string, JsonbDed>;

export default function PremiumAssemblyPage() {
  const ver = useDsiStore((s) => s.activeVersion) as ApiRecord | null;
  const commercial = useDsiStore((s) => s.activeCommercial) as ApiRecord | null;

  if (!ver) {
    return (
      <>
        <PageLoading message="Loading premium build-up…" />
      </>
    );
  }

  const technicalPremium = numOrNull(ver.final_premium ?? ver.premium_after_modifiers);
  const netPremium = numOrNull(commercial?.net_premium);
  const grossPremium = numOrNull(commercial?.gross_premium);
  const offeredPremium = numOrNull(commercial?.offered_premium);
  const discretionPct = pctOrNull(commercial?.offered_premium_discretion);
  const discretionRationale = strOrNull(commercial?.offered_premium_rationale);
  const totalTaxes = numOrNull(commercial?.total_taxes);
  const minimumPremium = numOrNull(commercial?.minimum_premium ?? commercial?.minimum_gross);
  const atMinimum = boolOrNull(commercial?.at_minimum_premium);
  const maxDiscretion = pctOrNull(commercial?.max_discretion ?? commercial?.discretion_cap);

  const deductions = (commercial?.deductions as Deductions | undefined) ?? {};
  const taxes = (commercial?.taxes_and_levies as Taxes | undefined) ?? {};

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
                {discretionPct != null
                  ? `${discretionPct === 0 ? "0%" : `${discretionPct.toFixed(1)}%`} discretion applied`
                  : "no discretion recorded"}
                {grossPremium != null ? " · at gross premium" : ""}
              </Micro>
            </div>
            <HeroStat label="Net premium" value={netPremium} />
            <HeroStat label="Gross premium" value={grossPremium} />
            <HeroStat
              label="Technical premium"
              value={technicalPremium}
              muted
            />
          </div>
        </Card>

        {/* ─── 2. Build-up ledger ──────────────────────────── */}
        <Card header="Premium build-up" icon={Calculator} pad="md">
          <Ledger
            opening={{
              label: "Technical premium",
              value: technicalPremium,
              sub: "as priced from base × signal modifiers",
            }}
            sections={[
              {
                title: "Deductions",
                items: jsonbToLedgerItems(deductions, "deduction"),
                subtotalLabel: "Net premium",
                subtotalValue: netPremium,
              },
              {
                title: "Taxes & levies",
                items: jsonbToLedgerItems(taxes, "tax"),
                subtotalLabel: "Gross premium",
                subtotalValue: grossPremium,
              },
              {
                title: "Discretion",
                items: [
                  {
                    label: "Applied",
                    rate:
                      discretionPct != null
                        ? `${discretionPct > 0 ? "+" : ""}${discretionPct.toFixed(1)}%`
                        : "—",
                    delta:
                      discretionPct != null && grossPremium != null
                        ? grossPremium * (discretionPct / 100)
                        : 0,
                  },
                ],
              },
            ]}
            final={{ label: "Offered premium", value: offeredPremium }}
          />
        </Card>

        {/* ─── 3. Footer — minimum + discretion analysis ───── */}
        <div className="grid gap-3.5 md:grid-cols-2">
          <Card header="Minimum premium check" icon={AlertTriangle} pad="md">
            <div className="grid grid-cols-3 gap-3">
              <KpiSnug
                label="Minimum gross"
                value={minimumPremium != null ? formatCurrency(minimumPremium) : "—"}
              />
              <KpiSnug
                label="At minimum?"
                value={atMinimum != null ? (atMinimum ? "Yes" : "No") : "—"}
                tone={atMinimum === false ? "pos" : atMinimum === true ? "warn" : "default"}
              />
              <KpiSnug
                label="Max discretion"
                value={maxDiscretion != null ? `±${maxDiscretion.toFixed(0)}%` : "—"}
              />
            </div>
            {minimumPremium != null && offeredPremium != null && (
              <Micro className="mt-3 block border-t border-rule pt-3 text-[11.5px]">
                Offered premium {offeredPremium >= minimumPremium ? "clears" : "is below"}{" "}
                the carrier minimum by{" "}
                <strong
                  className={
                    offeredPremium >= minimumPremium ? "text-pos" : "text-neg"
                  }
                >
                  {formatCurrency(Math.abs(offeredPremium - minimumPremium))}
                </strong>
                .
              </Micro>
            )}
          </Card>

          <Card header="Discretion analysis" icon={SlidersHorizontal} pad="md">
            <div className="grid grid-cols-2 gap-3">
              <KpiSnug
                label="From gross"
                value={discretionPct != null ? `${discretionPct.toFixed(1)}%` : "—"}
              />
              <KpiSnug
                label="Direction"
                value={
                  discretionPct == null
                    ? "—"
                    : discretionPct > 0
                      ? "Loaded"
                      : discretionPct < 0
                        ? "Discounted"
                        : "Flat"
                }
              />
              <KpiSnug
                label="Rationale"
                value={discretionRationale ?? "None recorded"}
              />
              <KpiSnug
                label="Approver"
                value={strOrNull(commercial?.offered_premium_set_by) ?? "—"}
              />
            </div>
            {totalTaxes != null && (
              <Micro className="mt-3 block border-t border-rule pt-3 text-[11.5px]">
                Taxes total <strong>{formatCurrency(totalTaxes)}</strong>.
              </Micro>
            )}
          </Card>
        </div>
      </WorkArea>
    </>
  );
}

/* ──────────────────── sub-components ──────────────────── */

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

type LedgerItem = { label: string; rate?: string; delta: number };

function Ledger({
  opening,
  sections,
  final,
}: {
  opening?: { label: string; value: number | null; sub?: string };
  sections: Array<{
    title: string;
    items: LedgerItem[];
    subtotalLabel?: string;
    subtotalValue?: number | null;
  }>;
  final?: { label: string; value: number | null };
}) {
  return (
    <div>
      {opening && (
        <div className="flex items-baseline justify-between px-1 pt-2 pb-3.5">
          <div>
            <div className="text-[13.5px] font-semibold">{opening.label}</div>
            {opening.sub && <Micro className="mt-0.5 block">{opening.sub}</Micro>}
          </div>
          <span className="font-mono text-[16px] font-bold text-ink-soft tabular-nums">
            {opening.value != null ? formatCurrency(opening.value) : "—"}
          </span>
        </div>
      )}
      {sections.map((s, i) => (
        <div key={s.title} className={i === 0 ? "" : "mt-3"}>
          <Eyebrow className="block border-t border-rule px-1 pt-2 pb-1.5">
            {s.title}
          </Eyebrow>
          {s.items.length === 0 ? (
            <Micro className="px-1 py-2 italic">no entries</Micro>
          ) : (
            s.items.map((it, j) => (
              <div
                key={j}
                className="grid grid-cols-[1fr_80px_130px] px-1 py-1.5 text-[13px] text-ink-soft"
              >
                <span>{it.label}</span>
                <span className="text-right font-mono tabular-nums text-ink-mute">
                  {it.rate ?? "—"}
                </span>
                <span
                  className={`text-right font-mono font-semibold tabular-nums ${
                    it.delta < 0
                      ? "text-neg"
                      : it.delta > 0
                        ? "text-warn"
                        : "text-ink-mute"
                  }`}
                >
                  {it.delta === 0
                    ? "—"
                    : `${it.delta > 0 ? "+" : "-"}${formatCurrency(Math.abs(it.delta))}`}
                </span>
              </div>
            ))
          )}
          {s.subtotalLabel && (
            <div className="mt-1 flex items-baseline justify-between border-t border-ink-soft px-1 pt-2.5 pb-1.5">
              <span className="text-[13.5px] font-bold">{s.subtotalLabel}</span>
              <span className="font-mono text-[17px] font-bold tabular-nums">
                {s.subtotalValue != null ? formatCurrency(s.subtotalValue) : "—"}
              </span>
            </div>
          )}
        </div>
      ))}
      {final && (
        <div className="mt-2.5 flex items-baseline justify-between border-t-2 border-ink px-1 pt-3.5 pb-1">
          <span className="text-[15px] font-bold uppercase tracking-wider">
            {final.label}
          </span>
          <span className="font-mono text-[26px] font-bold text-info-deep dark:text-info tabular-nums">
            {final.value != null ? formatCurrency(final.value) : "—"}
          </span>
        </div>
      )}
    </div>
  );
}

/* ──────────────────── helpers ──────────────────── */

function jsonbToLedgerItems(j: Deductions | Taxes, kind: "deduction" | "tax"): LedgerItem[] {
  // Deductions are subtracted from technical → negative delta.
  // Taxes are added on top → positive delta (in the ledger they show as
  // warn-tone, matching the template's color logic where >0 is a loading).
  const sign = kind === "deduction" ? -1 : 1;
  return Object.entries(j).map(([key, raw]) => {
    const rate = numOrNull(raw?.rate);
    const amount = numOrNull(raw?.amount);
    return {
      label: humanise(key),
      rate: rate != null ? `${(rate * 100).toFixed(1)}%` : undefined,
      delta: amount != null ? sign * amount : 0,
    };
  });
}

function humanise(key: string): string {
  return key
    .split(/[_\s]+/)
    .filter(Boolean)
    .map((w) => w[0]!.toUpperCase() + w.slice(1))
    .join(" ");
}

function numOrNull(v: unknown): number | null {
  if (v == null) return null;
  const n = Number(v);
  return Number.isFinite(n) ? n : null;
}

function strOrNull(v: unknown): string | null {
  if (v == null) return null;
  const s = String(v).trim();
  return s.length > 0 ? s : null;
}

function boolOrNull(v: unknown): boolean | null {
  if (v == null) return null;
  return Boolean(v);
}

function pctOrNull(v: unknown): number | null {
  const n = numOrNull(v);
  return n == null ? null : n * 100;
}

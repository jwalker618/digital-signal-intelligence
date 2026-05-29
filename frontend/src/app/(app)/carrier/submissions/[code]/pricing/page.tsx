"use client";

import { ArrowRightToLine, Calculator, ChevronDown, CircleEllipsis } from "lucide-react";
import { Card } from "@/components/ui/card";
import { Chip } from "@/components/ui/chip";
import { WorkArea } from "@/components/ui/work-area";
import { Eyebrow, Micro } from "@/components/ui/typography";
import { PageLoading } from "@/components/base/pageStates";
import { useDsiStore, type ApiRecord } from "@/store/dsiStore";
import { formatCurrency } from "@/lib/format";
import { numOrNull, strOrNull, compactCurrency } from "@/lib/coerce";

/* ============================================================
 * Pricing Anatomy — mirrors reim_wb_a.jsx WbPricing.
 *
 * Layout: 2-col grid 1.6fr / 1fr.
 *   Left:  base → 5 modifier groups (collapsible-style bins) → final block
 *   Right: 3 limit options (Upper / Recommended / Lower) with ROL detail
 * ============================================================ */

const MODIFIER_GROUPS: Array<{ key: string; title: string; sources: string[] }> = [
  { key: "categorical", title: "Categorical", sources: ["categorical"] },
  {
    key: "signal",
    title: "Signal-based",
    sources: ["signal", "signal_feature", "signal_group", "evidence_grade"],
  },
  { key: "direct", title: "Direct queries", sources: ["direct_query", "query"] },
  { key: "loss", title: "Loss analysis", sources: ["loss", "experience", "loss_modifier"] },
  { key: "exposure", title: "Exposure analysis", sources: ["exposure", "exposure_modifier"] },
];

type Modifier = {
  source?: string;
  source_id?: string;
  name?: string;
  factor?: number;
  premium_before?: number;
  premium_after?: number;
};

export default function PricingAnatomyPage() {
  const ver = useDsiStore((s) => s.activeVersion) as ApiRecord | null;

  if (!ver) {
    return (
      <>
        <PageLoading message="Loading pricing data…" />
      </>
    );
  }

  const base = numOrNull(ver.base_premium);
  const finalPremium = numOrNull(ver.final_premium);
  const loadedPremium = numOrNull(ver.premium_after_modifiers ?? ver.loaded_premium);
  const ilfFactor = numOrNull(ver.ilf_factor);
  const recommendedLimit = numOrNull(ver.recommended_limit);
  const tier = (ver.final_tier as number | null | undefined) ?? null;
  const method = strOrNull(ver.base_premium_method);
  const baseDerivation = (ver.base_premium_derivation as ApiRecord | undefined) ?? {};
  const baseBasis = strOrNull(baseDerivation.basis_label ?? baseDerivation.basis);
  const baseBasisValue = numOrNull(baseDerivation.basis_value);
  const baseRate = numOrNull(baseDerivation.rate);

  const fpd = (ver.final_premium_detail as ApiRecord | undefined) ?? {};
  const deductibleFactor = numOrNull(fpd.deductible_factor);

  const modifiers: Modifier[] = Array.isArray(ver.modifiers_applied)
    ? (ver.modifiers_applied as Modifier[])
    : [];

  // Bucket by source → template's 5 groups.
  const grouped = MODIFIER_GROUPS.map((g) => {
    const items = modifiers.filter((m) =>
      g.sources.includes(String(m.source ?? "").toLowerCase()),
    );
    const total = items.reduce((sum, m) => {
      if (m.premium_before == null || m.premium_after == null) return sum;
      return sum + (Number(m.premium_after) - Number(m.premium_before));
    }, 0);
    return { ...g, items, total };
  });

  // Anything that didn't bucket goes in an "Other" group so nothing is lost.
  const knownSources = new Set(MODIFIER_GROUPS.flatMap((g) => g.sources));
  const otherItems = modifiers.filter(
    (m) => !knownSources.has(String(m.source ?? "").toLowerCase()),
  );
  if (otherItems.length > 0) {
    const total = otherItems.reduce((s, m) => {
      if (m.premium_before == null || m.premium_after == null) return s;
      return s + (Number(m.premium_after) - Number(m.premium_before));
    }, 0);
    grouped.push({
      key: "other",
      title: "Other",
      sources: [],
      items: otherItems,
      total,
    });
  }

  let running = base ?? 0;

  // Limit options (Upper / Recommended / Lower)
  const limitOptions = [
    {
      label: "Upper",
      limit: numOrNull(ver.rol_upper_limit),
      premium: numOrNull(ver.rol_upper_premium),
      rol: numOrNull(ver.rol_upper_rol),
      rationale: strOrNull(ver.rol_upper_rationale),
      selected: false,
    },
    {
      label: "Recommended",
      limit: recommendedLimit,
      premium: finalPremium,
      rol:
        finalPremium != null && recommendedLimit != null && recommendedLimit > 0
          ? finalPremium / recommendedLimit
          : null,
      rationale: strOrNull(ver.recommendation_rationale ?? null),
      selected: true,
    },
    {
      label: "Lower",
      limit: numOrNull(ver.rol_lower_limit),
      premium: numOrNull(ver.rol_lower_premium),
      rol: numOrNull(ver.rol_lower_rol),
      rationale: strOrNull(ver.rol_lower_rationale),
      selected: false,
    },
  ];

  return (
    <>
      <WorkArea className="lg:grid-cols-[1.6fr_1fr]">
        {/* ─── Left: pricing anatomy ─────────────────────────── */}
        <Card header="Pricing Anatomy" icon={Calculator} pad="md">
          <div className="mb-3.5 flex flex-wrap items-center gap-2.5 text-[13px] text-ink">
            <ArrowRightToLine size={14} className="text-ink-soft" />
            <span>
              Tier <strong>{tier ?? "—"}</strong> base premium using
            </span>
            <Chip variant="default" size="sm">
              <span className="font-mono text-[11px]">{method ?? "—"}</span>
            </Chip>
            <span>methodology</span>
          </div>

          {/* Base premium block */}
          <div className="mb-3.5 rounded-card bg-surface-elev px-3.5 py-2.5">
            <div className="grid grid-cols-[1fr_auto] gap-y-1.5 text-[13px]">
              <span>Basis</span>
              <span className="font-mono font-semibold">
                {baseBasis ?? "—"}
                {baseBasisValue != null ? ` @ ${formatCurrency(baseBasisValue)}` : ""}
              </span>
              <span>Rate</span>
              <span className="font-mono font-semibold">
                {baseRate != null ? baseRate.toFixed(6) : "—"}
              </span>
              <div className="col-span-2 mt-1 flex items-center justify-between border-t border-rule pt-2">
                <strong>Base premium</strong>
                <strong className="font-mono text-info">
                  {base != null ? formatCurrency(base) : "—"}
                </strong>
              </div>
            </div>
          </div>

          {/* Modifier groups */}
          {grouped.map((g) => {
            running += g.total;
            return (
              <div
                key={g.key}
                className="mb-2 overflow-hidden rounded-card border border-rule"
              >
                <div className="grid grid-cols-[1fr_100px_110px_110px] items-center bg-surface-sunken px-3.5 py-2.5 text-[12.5px] font-semibold">
                  <span className="flex items-center gap-1.5">
                    <ChevronDown size={12} /> {g.title}
                    <Micro className="ml-1">({g.items.length})</Micro>
                  </span>
                  <Micro className="text-center">—</Micro>
                  <span
                    className={`text-right font-mono font-bold tabular-nums ${
                      g.total > 0 ? "text-neg" : g.total < 0 ? "text-pos" : "text-ink-soft"
                    }`}
                  >
                    {g.total > 0 ? "+" : ""}
                    {formatCurrency(g.total)}
                  </span>
                  <span className="text-right font-mono font-bold tabular-nums">
                    {formatCurrency(running)}
                  </span>
                </div>
                {g.items.map((m, i) => {
                  const delta =
                    m.premium_before != null && m.premium_after != null
                      ? Number(m.premium_after) - Number(m.premium_before)
                      : 0;
                  return (
                    <div
                      key={`${m.source_id}-${i}`}
                      className="grid grid-cols-[1fr_100px_110px_110px] border-t border-rule px-3.5 py-2 pl-8 text-[12.5px]"
                    >
                      <span className="text-ink-soft">{m.name ?? m.source_id ?? "—"}</span>
                      <span className="text-center font-mono font-semibold tabular-nums">
                        {m.factor != null ? `${Number(m.factor).toFixed(2)}x` : "—"}
                      </span>
                      <span
                        className={`text-right font-mono tabular-nums ${
                          delta > 0 ? "text-neg" : delta < 0 ? "text-pos" : "text-ink-soft"
                        }`}
                      >
                        {delta > 0 ? "+" : delta < 0 ? "-" : ""}
                        {formatCurrency(Math.abs(delta))}
                      </span>
                      <Micro>—</Micro>
                    </div>
                  );
                })}
              </div>
            );
          })}

          {/* Final premium build-up */}
          <div className="mt-4 rounded-card border border-info bg-info-soft px-4 py-3.5">
            <Eyebrow className="mb-2.5 text-info-deep dark:text-info">
              Final premium
            </Eyebrow>
            <div className="grid grid-cols-[1fr_auto] gap-y-1.5 text-[13px]">
              <span>Loaded premium</span>
              <span className="font-mono">
                {loadedPremium != null ? formatCurrency(loadedPremium) : "—"}
              </span>
              <span>
                ILF factor
                {recommendedLimit != null
                  ? ` (limit ${compactCurrency(recommendedLimit)})`
                  : ""}
              </span>
              <span className="font-mono">
                {ilfFactor != null ? `${ilfFactor.toFixed(3)}x` : "—"}
              </span>
              <span>Deductible factor</span>
              <span className="font-mono">
                {deductibleFactor != null ? `${deductibleFactor.toFixed(3)}x` : "—"}
              </span>
              <div className="col-span-2 mt-1.5 flex items-center justify-between border-t border-info pt-2">
                <strong className="text-[15px]">Recommended premium</strong>
                <strong className="font-mono text-[18px] text-info-deep dark:text-info">
                  {finalPremium != null ? formatCurrency(finalPremium) : "—"}
                </strong>
              </div>
            </div>
          </div>
        </Card>

        {/* ─── Right: Recommended Quote + Limit Options ──────── */}
        <Card header="Recommended Quote + Limit Options" icon={CircleEllipsis} pad="md">
          {limitOptions.map((o) => (
            <div
              key={o.label}
              className={`mb-2.5 rounded-card border p-3.5 ${
                o.selected
                  ? "border-info bg-info-soft"
                  : "border-rule bg-surface-elev"
              }`}
            >
              <div className="mb-2 flex items-baseline justify-between">
                <span className="text-[13px] font-bold">{o.label}</span>
                {o.selected && (
                  <Chip variant="info" size="sm">
                    CURRENT
                  </Chip>
                )}
              </div>
              <PRow
                k="Technical limit"
                v={o.limit != null ? compactCurrency(o.limit) : "—"}
              />
              <PRow
                k="Technical premium"
                v={o.premium != null ? formatCurrency(o.premium) : "—"}
                bold
              />
              <PRow
                k="RoL"
                v={o.rol != null ? `${(o.rol * 100).toFixed(2)}%` : "—"}
              />
              {o.rationale && (
                <Micro className="mt-2 block text-[11.5px] leading-relaxed">
                  {o.rationale}
                </Micro>
              )}
            </div>
          ))}
        </Card>
      </WorkArea>
    </>
  );
}

function PRow({ k, v, bold }: { k: string; v: string; bold?: boolean }) {
  return (
    <div className="flex items-baseline justify-between border-b border-rule/60 py-1.5 text-[12.5px] last:border-b-0">
      <span className="text-ink-soft">{k}</span>
      <span className={`font-mono tabular-nums ${bold ? "font-semibold text-ink" : "text-ink"}`}>
        {v}
      </span>
    </div>
  );
}




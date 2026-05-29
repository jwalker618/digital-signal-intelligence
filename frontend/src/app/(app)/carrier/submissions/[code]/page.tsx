"use client";

import { use } from "react";
import {
  AlertCircle,
  Building2,
  ExternalLink,
  Layers,
  Scale,
  Search,
  User,
} from "lucide-react";
import { Card } from "@/components/ui/card";
import { Eyebrow, Micro } from "@/components/ui/typography";
import { LabelRow } from "@/components/ui/label-row";
import { KpiSnug } from "@/components/ui/kpi-snug";
import { WorkArea } from "@/components/ui/work-area";
import { PageLoading } from "@/components/base/pageStates";
import { useDsiStore, type ApiRecord } from "@/store/dsiStore";
import { formatCurrency, formatText } from "@/lib/format";
import type { Tone } from "@/lib/design-tokens";

/* ============================================================
 * Carrier Submission Workbench — Summary tab.
 * Mirrors reim_wb_a.jsx WbSummary section.
 * ============================================================ */

export default function WorkbenchSummaryPage(props: {
  params: Promise<{ code: string }>;
}) {
  use(props.params);
  const sub = useDsiStore((s) => s.activeSubmission);
  const ver = useDsiStore((s) => s.activeVersion) as ApiRecord | null;
  const commercial = useDsiStore((s) => s.activeCommercial) as ApiRecord | null;
  const risk = useDsiStore((s) => s.activeRisk) as ApiRecord | null;

  if (!sub) {
    return (
      <>
        <PageLoading message="Loading submission…" />
      </>
    );
  }

  const composite = numOrNull(ver?.final_composite_score ?? ver?.pure_composite_score);
  const decision = String(ver?.decision ?? sub.decision ?? "").toLowerCase();
  const tier = (ver?.final_tier as number | null | undefined) ?? sub.final_tier ?? null;
  const tierLabel = (ver?.tier_label as string | null | undefined) ?? null;
  const finalPremium = numOrNull(
    ver?.final_premium ?? sub.final_premium ?? sub.recommended_premium,
  );
  const limit = numOrNull(ver?.recommended_limit ?? null);
  const confidence = numOrNull(ver?.confidence);
  const signalCoverage = numOrNull(ver?.signal_coverage);
  const referralReasons: string[] = Array.isArray(ver?.referral_reasons)
    ? (ver?.referral_reasons as string[])
    : [];

  // Three Pillar Assessment.
  // Risk pillar = pure_composite_score — the score from signal-group rollup
  // BEFORE signal-condition / pricing modifiers (i.e. the "base" score, by
  // symmetry with base_premium). Loss + Exposure come straight off the MV row.
  const pureScore = numOrNull(ver?.pure_composite_score);
  const pillars: Pillar[] = [
    {
      name: "Risk",
      score: pureScore != null ? Math.round(pureScore / 10) : null,
      label: pillarLabel(pureScore != null ? pureScore / 10 : null, "risk"),
      tone: "info",
      bullets: pillarBullets("risk", ver),
    },
    {
      name: "Loss",
      score: numOrNull(ver?.loss_propensity_score),
      label:
        (ver?.loss_propensity_band as string | null | undefined)
          ? formatText(String(ver?.loss_propensity_band), "capitalize") +
            " propensity"
          : pillarLabel(numOrNull(ver?.loss_propensity_score), "loss"),
      tone: "pos",
      bullets: pillarBullets("loss", ver),
    },
    {
      name: "Exposure",
      score: numOrNull(ver?.exposure_size_score),
      label:
        (ver?.exposure_band_label as string | null | undefined) ??
        pillarLabel(numOrNull(ver?.exposure_size_score), "exposure"),
      tone: "aux",
      bullets: pillarBullets("exposure", ver),
    },
  ];

  // submission_data JSONB may carry these. Render only what's present.
  const sd: ApiRecord = (sub.submission_data as ApiRecord | undefined) ?? {};
  const industry = strOrNull(sd.industry_label ?? sd.naics_label);
  const naics = strOrNull(sd.naics_code ?? sd.naics);
  const revenueBand = strOrNull(sd.revenue_band);
  const country = strOrNull(sd.country);
  const locations = strOrNull(sd.locations);
  const employees = strOrNull(sd.employees);

  // Discovery items — pulled from submission_data when present; rendered
  // with the template's tone vocabulary so positive findings highlight pos
  // and missing/risky findings highlight spot/neg.
  const discovery = (sd.discovery as ApiRecord | undefined) ?? {};
  const mfaVerified = strOrNull(discovery.mfa_verified);
  const soc2 = strOrNull(discovery.soc2_status);
  const edrCoverage = strOrNull(discovery.edr_coverage);
  const publicRdp = strOrNull(discovery.public_rdp);

  // Commercial JSONBs
  const deductions = (commercial?.deductions as ApiRecord | undefined) ?? {};
  const taxes = (commercial?.taxes_and_levies as ApiRecord | undefined) ?? {};
  const brokeragePct = pctOrNull(
    (deductions.brokerage as ApiRecord | undefined)?.rate,
  );
  const totalTaxes = numOrNull(commercial?.total_taxes);
  const netPremium = numOrNull(commercial?.net_premium);
  const grossPremium = numOrNull(commercial?.gross_premium);
  const offeredPremium = numOrNull(commercial?.offered_premium);
  const discretionPct = pctOrNull(commercial?.offered_premium_discretion);
  const atMinimum = boolOrNull(commercial?.at_minimum_premium);
  const currency = strOrNull(commercial?.base_currency) ?? "USD";

  // Risk-terms JSONBs
  const coverageTerms = (risk?.coverage_terms as ApiRecord | undefined) ?? {};
  const extensionsList = Array.isArray(coverageTerms.extensions)
    ? (coverageTerms.extensions as unknown[])
    : [];
  const exclusionsList = Array.isArray(coverageTerms.exclusions)
    ? (coverageTerms.exclusions as unknown[])
    : [];
  const subLimitsList = Array.isArray(risk?.sub_limits)
    ? (risk?.sub_limits as ApiRecord[])
    : [];
  const subLimitsLabel =
    subLimitsList.length > 0
      ? subLimitsList
          .slice(0, 2)
          .map((s) => {
            const peril = strOrNull(s.peril);
            const sl = numOrNull(s.sub_limit);
            return peril && sl != null
              ? `${formatText(peril, "capitalize")} ${formatCurrencyShort(sl)}`
              : peril ?? null;
          })
          .filter(Boolean)
          .join(" · ") || null
      : null;
  const waitingHours = numOrNull(risk?.waiting_period_hours);

  const referText = decision === "refer" ? "Refer" : formatText(decision, "capitalize");

  return (
    <>
      <WorkArea>
          {/* ─── Decision banner ─────────────────────────────── */}
          <Card variant="spot" pad="lg">
            <div className="grid grid-cols-1 items-center gap-5 lg:grid-cols-[1fr_auto]">
              <div>
                <Eyebrow className="text-spot-deep dark:text-spot">
                  Decision
                </Eyebrow>
                <div className="mt-1 flex flex-wrap items-baseline gap-3.5">
                  <span className="font-display text-[28px] font-semibold text-spot-deep dark:text-spot">
                    {decision ? referText : "—"}
                  </span>
                  {referralReasons.length > 0 && (
                    <Micro>
                      awaiting underwriter audit · {referralReasons.length}{" "}
                      flagged signal{referralReasons.length === 1 ? "" : "s"}
                    </Micro>
                  )}
                </div>
              </div>
              <div className="grid grid-cols-3 gap-6 sm:grid-cols-6">
                <KpiSnug
                  label="Score"
                  value={composite != null ? composite.toFixed(0) : "—"}
                  tone="info"
                />
                <KpiSnug
                  label="Tier"
                  value={
                    tier != null
                      ? `T${tier}${tierLabel ? ` · ${tierLabel}` : ""}`
                      : "—"
                  }
                />
                <KpiSnug
                  label="Premium"
                  value={
                    finalPremium != null ? formatCurrencyShort(finalPremium) : "—"
                  }
                />
                <KpiSnug
                  label="Limit"
                  value={limit != null ? formatCurrencyShort(limit) : "—"}
                />
                <KpiSnug
                  label="Confidence"
                  value={
                    confidence != null
                      ? `${(confidence * 100).toFixed(0)}%`
                      : "—"
                  }
                  tone="pos"
                />
                <KpiSnug
                  label="Signal coverage"
                  value={
                    signalCoverage != null
                      ? `${(signalCoverage * 100).toFixed(0)}%`
                      : "—"
                  }
                />
              </div>
            </div>

            {referralReasons.length > 0 && (
              <div className="mt-5 rounded-card border border-spot/30 bg-surface px-4 py-3">
                <Eyebrow className="mb-2">Referral reasons</Eyebrow>
                <ul className="space-y-1">
                  {referralReasons.map((r, i) => (
                    <li
                      key={i}
                      className="flex items-start gap-2 text-[13px] text-ink"
                    >
                      <AlertCircle
                        size={12}
                        className="mt-1 shrink-0 text-warn"
                      />
                      {r}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </Card>

          {/* ─── Three Pillar Assessment ─────────────────────── */}
          <Card header="Three Pillar Assessment" icon={Layers} pad="md">
            <div className="grid gap-3.5 md:grid-cols-3">
              {pillars.map((p) => (
                <PillarCell key={p.name} pillar={p} />
              ))}
            </div>
          </Card>

          {/* ─── Bottom 3-col: identity+discovery · commercial · risk terms */}
          <div className="grid gap-3.5 lg:grid-cols-[0.9fr_1.4fr_1.4fr]">
            <div className="flex flex-col gap-3.5">
              <Card header="Who are they?" icon={User} pad="md" className="space-y-1">
                <LabelRow label="Industry" value={industry ?? "—"} />
                <LabelRow label="NAICS" value={naics ? <span className="font-mono">{naics}</span> : "—"} />
                <LabelRow label="Revenue band" value={revenueBand ?? "—"} />
                <LabelRow label="Country" value={country ?? "—"} />
                <LabelRow label="Locations" value={locations ?? "—"} />
                <LabelRow label="Employees" value={employees ?? "—"} />
              </Card>
              <Card header="Discovery" icon={Search} pad="md" className="space-y-1">
                <LabelRow
                  label="Domain"
                  value={
                    sub.discovered_domain ? (
                      <a
                        href={`https://${sub.discovered_domain}`}
                        target="_blank"
                        rel="noreferrer"
                        className="inline-flex items-center gap-1 font-mono text-info hover:underline"
                      >
                        {sub.discovered_domain}
                        <ExternalLink size={11} />
                      </a>
                    ) : "—"
                  }
                />
                <LabelRow label="MFA verified" value={mfaVerified ?? "—"} />
                <LabelRow label="SOC 2 Type II" value={soc2 ?? "—"} />
                <LabelRow label="EDR coverage" value={edrCoverage ?? "—"} />
                <LabelRow label="Public RDP" value={publicRdp ?? "—"} />
              </Card>
            </div>

            <Card header="Commercial Summary" icon={Building2} pad="md" className="space-y-1">
              <LabelRow
                label="Technical premium"
                value={
                  finalPremium != null ? (
                    <span className="font-mono font-semibold">{formatCurrency(finalPremium)}</span>
                  ) : "—"
                }
              />
              <LabelRow
                label="Brokerage"
                value={brokeragePct != null ? `${brokeragePct.toFixed(1)}%` : "—"}
              />
              <LabelRow
                label="Net premium"
                value={
                  netPremium != null ? (
                    <span className="font-mono">{formatCurrency(netPremium)}</span>
                  ) : "—"
                }
              />
              <LabelRow
                label="Taxes + levies"
                value={
                  totalTaxes != null ? (
                    <span className="font-mono">{formatCurrency(totalTaxes)}</span>
                  ) : Object.keys(taxes).length > 0 ? (
                    <span className="font-mono">
                      {formatCurrency(sumJsonbAmounts(taxes))}
                    </span>
                  ) : "—"
                }
              />
              <LabelRow
                label="Gross premium"
                value={
                  grossPremium != null ? (
                    <span className="font-mono font-semibold">{formatCurrency(grossPremium)}</span>
                  ) : "—"
                }
              />
              <LabelRow
                label="Offered premium"
                value={
                  offeredPremium != null ? (
                    <span className="font-mono font-semibold text-info">
                      {formatCurrency(offeredPremium)}
                    </span>
                  ) : "—"
                }
              />
              <LabelRow
                label="Discretion"
                value={
                  discretionPct != null ? `${discretionPct >= 0 ? "+" : ""}${discretionPct.toFixed(1)}%` : "—"
                }
              />
              <LabelRow
                label="At minimum?"
                value={atMinimum != null ? (atMinimum ? "Yes" : "No") : "—"}
              />
              <LabelRow label="Currency" value={currency} />
            </Card>

            <Card header="Risk Terms Summary" icon={Scale} pad="md" className="space-y-1">
              <LabelRow
                label="Deductible"
                value={
                  numOrNull(risk?.deductible_amount) != null
                    ? deductibleLabel(risk!)
                    : "—"
                }
              />
              <LabelRow
                label="SIR applies"
                value={
                  risk?.sir_applies != null ? (risk?.sir_applies ? "Yes" : "No") : "—"
                }
              />
              <LabelRow
                label="Waiting period"
                value={waitingHours != null ? `${waitingHours} hours` : "—"}
              />
              <LabelRow
                label="Aggregate"
                value={
                  numOrNull(risk?.aggregate_limit) != null ? (
                    <span className="font-mono">{formatCurrency(Number(risk!.aggregate_limit))}</span>
                  ) : "—"
                }
              />
              <LabelRow
                label="Reinstatements"
                value={reinstatementsLabel(risk)}
              />
              <LabelRow
                label="Coverage"
                value={strOrNull(coverageTerms.trigger) ?? "—"}
              />
              <LabelRow
                label="Extensions"
                value={extensionsList.length > 0 ? String(extensionsList.length) : "—"}
              />
              <LabelRow
                label="Exclusions"
                value={exclusionsList.length > 0 ? String(exclusionsList.length) : "—"}
              />
              <LabelRow
                label="Sub-limits"
                value={subLimitsLabel ? <span className="font-mono">{subLimitsLabel}</span> : "—"}
              />
            </Card>
          </div>
      </WorkArea>
    </>
  );
}

/* ─────────────────────────── helpers ─────────────────────────── */

type Pillar = {
  name: string;
  score: number | null;
  label: string;
  tone: Tone;
  bullets: string[];
};

function PillarCell({ pillar }: { pillar: Pillar }) {
  const toneTextClass =
    pillar.tone === "info"
      ? "text-info"
      : pillar.tone === "pos"
        ? "text-pos"
        : pillar.tone === "aux"
          ? "text-aux"
          : "text-ink";
  const toneBgClass =
    pillar.tone === "info"
      ? "bg-info"
      : pillar.tone === "pos"
        ? "bg-pos"
        : pillar.tone === "aux"
          ? "bg-aux"
          : "bg-rule";
  const pct = pillar.score != null ? Math.max(0, Math.min(100, pillar.score)) : 0;
  return (
    <div className="rounded-card border border-rule bg-surface-elev p-4">
      <Eyebrow>{pillar.name}</Eyebrow>
      <div className="mt-1.5 flex items-baseline gap-2">
        <span className={`font-mono text-[26px] font-semibold tabular-nums ${toneTextClass}`}>
          {pillar.score != null ? pillar.score : "—"}
        </span>
        <Micro>{pillar.label}</Micro>
      </div>
      <div className="mt-2 h-1 overflow-hidden rounded-sm bg-rule">
        <div className={`h-full ${toneBgClass}`} style={{ width: `${pct}%` }} />
      </div>
      {pillar.bullets.length > 0 && (
        <ul className="mt-2.5 list-disc space-y-0.5 pl-4 text-[12px] leading-relaxed text-ink-soft">
          {pillar.bullets.map((b) => (
            <li key={b}>{b}</li>
          ))}
        </ul>
      )}
    </div>
  );
}

function pillarLabel(score: number | null, kind: "risk" | "loss" | "exposure"): string {
  if (score == null) return "—";
  if (kind === "loss") {
    return score >= 70 ? "High propensity" : score >= 40 ? "Moderate propensity" : "Low propensity";
  }
  if (kind === "exposure") {
    return score >= 70 ? "Large" : score >= 40 ? "Mid-market" : "Small";
  }
  return score >= 70 ? "Strong" : score >= 40 ? "Acceptable" : "Watch";
}

function pillarBullets(
  kind: "risk" | "loss" | "exposure",
  ver: ApiRecord | null | undefined,
): string[] {
  // Real data-driven bullets where we can; otherwise empty (no fake mock copy).
  if (!ver) return [];
  if (kind === "loss") {
    const out: string[] = [];
    const trend = strOrNull(ver.loss_trend_direction);
    if (trend) out.push(`Frequency trend ${trend}`);
    const sev = numOrNull(ver.severity_propensity_score);
    if (sev != null) out.push(`Severity score ${Math.round(sev)}/100`);
    return out;
  }
  if (kind === "exposure") {
    const out: string[] = [];
    const ev = numOrNull(ver.exposure_value);
    if (ev != null) out.push(`${formatCurrencyShort(ev)} exposure value`);
    const cplx = numOrNull(ver.exposure_complexity_score);
    if (cplx != null) out.push(`Complexity ${Math.round(cplx)}/100`);
    return out;
  }
  // risk pillar: prefer cohort framing
  const out: string[] = [];
  const median = numOrNull(ver.peer_cohort_median_score);
  const composite = numOrNull(ver.final_composite_score);
  if (composite != null && median != null) {
    const delta = composite - median;
    out.push(`${delta >= 0 ? "Above" : "Below"} cohort median (${Math.abs(delta).toFixed(0)} pts)`);
  }
  const conf = numOrNull(ver.confidence);
  if (conf != null) out.push(`Confidence ${(conf * 100).toFixed(0)}%`);
  return out;
}

function deductibleLabel(risk: ApiRecord): React.ReactNode {
  const amt = Number(risk.deductible_amount);
  const basis = strOrNull(risk.deductible_basis ?? risk.deductible_type);
  return (
    <span className="font-mono">
      {formatCurrency(amt)}
      {basis ? ` · ${formatText(basis.replace(/_/g, " "), "capitalize")}` : ""}
    </span>
  );
}

function reinstatementsLabel(risk: ApiRecord | null | undefined): string {
  if (!risk || risk.reinstatements == null) return "—";
  const n = Number(risk.reinstatements);
  const rate = numOrNull(risk.reinstatement_rate);
  if (n <= 0) return "None";
  return `${n}${rate != null ? ` · ${Math.round(rate * 100)}% of premium` : ""}`;
}

function sumJsonbAmounts(j: ApiRecord): number {
  let total = 0;
  for (const v of Object.values(j)) {
    if (v && typeof v === "object" && "amount" in (v as ApiRecord)) {
      const a = Number((v as ApiRecord).amount);
      if (Number.isFinite(a)) total += a;
    }
  }
  return total;
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
  // Stored as a fraction (0.125 = 12.5%) per the JSONB schema comments.
  const n = numOrNull(v);
  return n == null ? null : n * 100;
}

function formatCurrencyShort(n: number): string {
  const abs = Math.abs(n);
  if (abs >= 1_000_000) return `${n < 0 ? "-" : ""}$${(abs / 1_000_000).toFixed(abs >= 10_000_000 ? 0 : 1)}M`;
  if (abs >= 1_000) return `${n < 0 ? "-" : ""}$${(abs / 1_000).toFixed(0)}k`;
  return formatCurrency(n);
}

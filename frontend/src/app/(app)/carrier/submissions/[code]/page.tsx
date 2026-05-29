"use client";

import Link from "next/link";
import { use } from "react";
import {
  AlertCircle,
  Building2,
  ExternalLink,
  FileText,
  Layers,
  Scale,
  Search,
} from "lucide-react";
import { WorkbenchTopbar } from "@/components/chrome/workbench-topbar";
import { Card } from "@/components/ui/card";
import { Chip } from "@/components/ui/chip";
import { Eyebrow, NumDisplay, Body, Micro } from "@/components/ui/typography";
import { LabelRow } from "@/components/ui/label-row";
import { ScoreBar } from "@/components/ui/score-bar";
import { KpiSnug } from "@/components/ui/kpi-snug";
import { PageLoading } from "@/components/base/pageStates";
import { useDsiStore } from "@/store/dsiStore";
import { formatCurrency, formatText, formatDate } from "@/lib/format";
import { fmtRelative } from "@/lib/utils";

export default function WorkbenchSummaryPage(props: {
  params: Promise<{ code: string }>;
}) {
  use(props.params);
  const sub = useDsiStore((s) => s.activeSubmission);
  const ver = useDsiStore((s) => s.activeVersion);
  const quote = useDsiStore((s) => s.activeQuote);
  const referral = useDsiStore((s) => s.activeReferral);
  const commercial = useDsiStore((s) => s.activeCommercial);
  const risk = useDsiStore((s) => s.activeRisk);

  if (!sub) {
    return (
      <>
        <WorkbenchTopbar activeTabLabel="Summary" />
        <PageLoading message="Loading submission…" />
      </>
    );
  }

  const composite = ver?.composite_score ?? sub.composite_score ?? null;
  const decision = String(ver?.decision ?? sub.decision ?? "").toLowerCase();
  const tier = ver?.final_tier ?? sub.final_tier ?? null;
  const tierLabel = ver?.tier_label ?? null;
  const finalPremium =
    ver?.final_premium ?? sub.final_premium ?? sub.recommended_premium ?? null;
  const basePremium = ver?.base_premium ?? null;
  const confidence = ver?.confidence ?? null;
  const referralReasons: string[] = ver?.referral_reasons ?? [];
  const referralAwaiting = referral?.awaiting_party ?? null;
  const referralState = referral?.referral_state ?? sub.referral_state ?? null;

  const decisionTone =
    decision === "approve"
      ? "pos"
      : decision === "decline"
        ? "neg"
        : decision === "refer"
          ? "warn"
          : "mute";

  const netPremium = commercial?.net_premium ?? null;
  const grossPremium = commercial?.gross_premium ?? null;
  const offeredPremium = commercial?.offered_premium ?? null;
  const brokerage = commercial?.brokerage_pct ?? null;

  return (
    <>
      <WorkbenchTopbar activeTabLabel="Summary" />
      <div className="flex-1 overflow-y-auto px-9 py-7">
        <div className="mx-auto grid max-w-[1280px] gap-6">
          {/* Decision banner */}
          <Card
            variant={decision === "refer" ? "spot" : "info"}
            pad="lg"
            className="space-y-5"
          >
            <header className="flex flex-wrap items-start justify-between gap-6">
              <div>
                <Eyebrow
                  className={
                    decision === "refer"
                      ? "text-spot-deep dark:text-spot"
                      : "text-info-deep dark:text-info"
                  }
                >
                  Decision
                </Eyebrow>
                <div className="mt-1 flex items-baseline gap-3">
                  <span className="font-display text-[28px] font-semibold capitalize text-ink">
                    {decision ? formatText(decision, "capitalize") : "—"}
                  </span>
                  {referralReasons.length > 0 && (
                    <Micro>
                      awaiting underwriter audit · {referralReasons.length}{" "}
                      flagged signal{referralReasons.length === 1 ? "" : "s"}
                    </Micro>
                  )}
                </div>
                {composite != null && (
                  <ScoreBar
                    value={Number(composite)}
                    max={1000}
                    className="mt-3 max-w-[360px]"
                    showValue={false}
                    thresholds={[
                      { at: 400, tone: "neg" },
                      { at: 650, tone: "warn" },
                      { at: 800, tone: "info" },
                      { at: 1000, tone: "pos" },
                    ]}
                  />
                )}
              </div>
              <div className="grid grid-cols-3 gap-6 sm:grid-cols-5">
                <KpiSnug
                  label="Score"
                  value={composite != null ? Number(composite).toFixed(0) : "—"}
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
                    finalPremium != null ? formatCurrency(finalPremium) : "—"
                  }
                />
                <KpiSnug
                  label="Confidence"
                  value={
                    confidence != null
                      ? `${(Number(confidence) * 100).toFixed(0)}%`
                      : "—"
                  }
                  tone="pos"
                />
                <KpiSnug
                  label="Decision"
                  value={
                    decision ? (
                      <Chip variant={decisionTone} size="sm">
                        {formatText(decision, "capitalize")}
                      </Chip>
                    ) : (
                      "—"
                    )
                  }
                />
              </div>
            </header>

            {referralReasons.length > 0 && (
              <div className="rounded-card border border-spot/30 bg-surface px-4 py-3">
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

          {/* Premium summary */}
          <div className="grid gap-4 md:grid-cols-3">
            <PremiumStat label="Base premium" value={basePremium} />
            <PremiumStat label="Final premium" value={finalPremium} emphasis />
            <PremiumStat
              label="Δ from base"
              value={
                basePremium != null && finalPremium != null
                  ? Number(finalPremium) - Number(basePremium)
                  : null
              }
              signed
            />
          </div>

          {/* Who / discovery / commercial / risk terms */}
          <div className="grid gap-5 lg:grid-cols-3">
            <Card header="Who are they?" icon={Building2} pad="md" className="space-y-1">
              <LabelRow label="Entity" value={sub.entity_name ?? "—"} />
              <LabelRow label="Coverage" value={sub.coverage ?? "—"} />
              <LabelRow
                label="Pipeline status"
                value={
                  sub.status ? formatText(sub.status, "capitalize") : "—"
                }
              />
              {sub.discovered_domain ? (
                <LabelRow
                  label="Domain"
                  value={
                    <a
                      href={`https://${sub.discovered_domain}`}
                      target="_blank"
                      rel="noreferrer"
                      className="inline-flex items-center gap-1 text-info hover:underline"
                    >
                      {sub.discovered_domain}
                      <ExternalLink size={11} />
                    </a>
                  }
                />
              ) : (
                <LabelRow label="Domain" value="—" />
              )}
              <LabelRow
                label="Submitted"
                value={
                  sub.created_at
                    ? `${formatDate(sub.created_at)} · ${fmtRelative(sub.created_at)}`
                    : "—"
                }
              />
            </Card>

            <Card
              header="Commercial summary"
              icon={Search}
              pad="md"
              className="space-y-1"
            >
              <LabelRow
                label="Technical premium"
                value={finalPremium != null ? formatCurrency(finalPremium) : "—"}
              />
              <LabelRow
                label="Brokerage"
                value={
                  brokerage != null
                    ? `${(Number(brokerage) * 100).toFixed(1)}%`
                    : "—"
                }
              />
              <LabelRow
                label="Net premium"
                value={netPremium != null ? formatCurrency(netPremium) : "—"}
              />
              <LabelRow
                label="Gross premium"
                value={
                  grossPremium != null ? formatCurrency(grossPremium) : "—"
                }
              />
              <LabelRow
                label="Offered premium"
                value={
                  offeredPremium != null ? formatCurrency(offeredPremium) : "—"
                }
              />
            </Card>

            <Card
              header="Risk terms summary"
              icon={Scale}
              pad="md"
              className="space-y-1"
            >
              <LabelRow
                label="Deductible"
                value={
                  risk?.deductible_amount != null
                    ? formatCurrency(risk.deductible_amount)
                    : "—"
                }
              />
              <LabelRow
                label="SIR applies"
                value={risk?.sir_applies != null ? (risk.sir_applies ? "Yes" : "No") : "—"}
              />
              <LabelRow
                label="Aggregate"
                value={
                  risk?.aggregate_limit != null
                    ? formatCurrency(risk.aggregate_limit)
                    : "—"
                }
              />
              <LabelRow
                label="Reinstatements"
                value={risk?.reinstatements ?? "—"}
              />
              <LabelRow
                label="Coverage trigger"
                value={
                  risk?.coverage_trigger
                    ? formatText(risk.coverage_trigger, "capitalize")
                    : "—"
                }
              />
            </Card>
          </div>

          {/* Referral + quote */}
          <div className="grid gap-5 md:grid-cols-2">
            <Card
              header="Referral"
              icon={Layers}
              pad="md"
              variant={referralState ? "spot" : "default"}
              className="space-y-2"
            >
              {referral ? (
                <>
                  {referral.referral_code && (
                    <LabelRow
                      label="Code"
                      value={
                        <span className="font-mono">
                          {referral.referral_code}
                        </span>
                      }
                    />
                  )}
                  {referralState && (
                    <LabelRow
                      label="State"
                      value={formatText(referralState, "capitalize")}
                    />
                  )}
                  {referralAwaiting && (
                    <LabelRow
                      label="Awaiting"
                      value={formatText(referralAwaiting, "capitalize")}
                    />
                  )}
                  {referral.opened_at && (
                    <LabelRow
                      label="Opened"
                      value={fmtRelative(referral.opened_at)}
                    />
                  )}
                  {referral.referral_code && (
                    <Link
                      href={`/carrier/submissions/${sub.submission_code}/referral`}
                      className="mt-2 inline-flex items-center gap-1.5 text-[13px] font-semibold text-spot-deep dark:text-spot hover:underline"
                    >
                      <FileText size={13} />
                      Referral actions →
                    </Link>
                  )}
                </>
              ) : (
                <Body className="italic">No referral on this submission.</Body>
              )}
            </Card>

            {quote && (
              <Card header="Current quote" icon={FileText} pad="md" className="space-y-1">
                {quote.quote_code && (
                  <LabelRow
                    label="Code"
                    value={
                      <span className="font-mono">{quote.quote_code}</span>
                    }
                  />
                )}
                {quote.version_number != null && (
                  <LabelRow label="Version" value={`v${quote.version_number}`} />
                )}
                {quote.created_at && (
                  <LabelRow
                    label="Created"
                    value={formatDate(quote.created_at)}
                  />
                )}
              </Card>
            )}
          </div>
        </div>
      </div>
    </>
  );
}

function PremiumStat({
  label,
  value,
  emphasis,
  signed,
}: {
  label: string;
  value: number | null;
  emphasis?: boolean;
  signed?: boolean;
}) {
  const tone =
    signed && value != null
      ? value > 0
        ? "text-neg"
        : value < 0
          ? "text-pos"
          : "text-ink"
      : "text-ink";
  return (
    <Card pad="md" variant={emphasis ? "info" : "default"}>
      <Micro className={emphasis ? "text-info-deep dark:text-info" : "block"}>
        {label}
      </Micro>
      <NumDisplay size={emphasis ? "lg" : "md"} className={`mt-2 block ${tone}`}>
        {value == null
          ? "—"
          : `${signed && value > 0 ? "+" : ""}${formatCurrency(value)}`}
      </NumDisplay>
    </Card>
  );
}

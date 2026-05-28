"use client";

import Link from "next/link";
import { use } from "react";
import { AlertCircle, ExternalLink, FileText } from "lucide-react";
import { WorkbenchTopbar } from "@/components/chrome/workbench-topbar";
import { Card } from "@/components/ui/card";
import { Chip } from "@/components/ui/chip";
import { Eyebrow, NumDisplay, Body, Micro } from "@/components/ui/typography";
import { LabelRow } from "@/components/ui/label-row";
import { ScoreBar } from "@/components/ui/score-bar";
import { PageLoading } from "@/components/base/pageStates";
import { useDsiStore } from "@/store/dsiStore";
import { formatCurrency, formatText, formatDate } from "@/lib/format";
import { fmtRelative } from "@/lib/utils";

export default function WorkbenchSummaryPage(props: {
  params: Promise<{ code: string }>;
}) {
  // params is unwrapped only to keep the file consistent with sibling tabs.
  use(props.params);
  const sub = useDsiStore((s) => s.activeSubmission);
  const ver = useDsiStore((s) => s.activeVersion);
  const quote = useDsiStore((s) => s.activeQuote);
  const referral = useDsiStore((s) => s.activeReferral);

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
  const referralReasons: string[] = ver?.referral_reasons ?? [];
  const referralAwaiting = referral?.awaiting_party ?? null;
  const referralState = referral?.referral_state ?? sub.referral_state ?? null;

  return (
    <>
      <WorkbenchTopbar activeTabLabel="Summary" />
      <div className="flex-1 overflow-y-auto px-9 py-7">
        <div className="mx-auto grid max-w-[1280px] gap-6">
          {/* Hero — composite + decision */}
          <Card variant="info" pad="lg" className="space-y-5">
            <header className="flex items-start justify-between gap-6">
              <div>
                <Eyebrow className="text-info-deep dark:text-info">
                  Composite score
                </Eyebrow>
                <NumDisplay size="xl" className="mt-2 block">
                  {composite != null ? Number(composite).toFixed(0) : "—"}
                </NumDisplay>
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
                {ver?.confidence != null && (
                  <Micro className="mt-2 block">
                    confidence {(Number(ver.confidence) * 100).toFixed(0)}%
                  </Micro>
                )}
              </div>
              <div className="space-y-2 text-right">
                {decision && (
                  <Chip
                    variant={
                      decision === "approve"
                        ? "pos"
                        : decision === "decline"
                          ? "neg"
                          : decision === "refer"
                            ? "warn"
                            : "mute"
                    }
                  >
                    {formatText(decision, "capitalize")}
                  </Chip>
                )}
                {tier != null && (
                  <div>
                    <Micro className="block">Tier</Micro>
                    <p className="text-[20px] font-semibold tabular-nums text-ink">
                      {tier}
                      {tierLabel && (
                        <span className="ml-2 text-[12px] font-medium text-ink-soft">
                          {tierLabel}
                        </span>
                      )}
                    </p>
                  </div>
                )}
                {ver?.auto_approve != null && (
                  <Chip
                    variant={ver.auto_approve ? "pos" : "mute"}
                    size="sm"
                  >
                    {ver.auto_approve ? "Auto-approved" : "Manual review"}
                  </Chip>
                )}
              </div>
            </header>

            {referralReasons.length > 0 && (
              <div className="rounded-card border border-info/30 bg-surface px-4 py-3">
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
            <PremiumStat
              label="Final premium"
              value={finalPremium}
              emphasis
            />
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

          {/* Entity + referral context */}
          <div className="grid gap-5 md:grid-cols-2">
            <Card pad="md" className="space-y-2">
              <Eyebrow>Entity</Eyebrow>
              <LabelRow label="Name" value={sub.entity_name ?? "—"} />
              {sub.discovered_domain && (
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
              )}
              {sub.coverage && (
                <LabelRow label="Coverage" value={sub.coverage} />
              )}
              {sub.created_at && (
                <LabelRow
                  label="Submitted"
                  value={`${formatDate(sub.created_at)} · ${fmtRelative(sub.created_at)}`}
                />
              )}
              {sub.status && (
                <LabelRow
                  label="Pipeline status"
                  value={formatText(sub.status, "capitalize")}
                />
              )}
            </Card>

            <Card
              pad="md"
              variant={referralState ? "spot" : "default"}
              className="space-y-2"
            >
              <Eyebrow
                className={
                  referralState ? "text-spot-deep dark:text-spot" : ""
                }
              >
                Referral
              </Eyebrow>
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
          </div>

          {/* Quote */}
          {quote && (
            <Card pad="md" className="space-y-2">
              <Eyebrow>Current quote</Eyebrow>
              <div className="grid gap-2 md:grid-cols-3">
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
              </div>
            </Card>
          )}
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
      <Micro
        className={emphasis ? "text-info-deep dark:text-info" : "block"}
      >
        {label}
      </Micro>
      <NumDisplay
        size={emphasis ? "lg" : "md"}
        className={`mt-2 block ${tone}`}
      >
        {value == null
          ? "—"
          : `${signed && value > 0 ? "+" : ""}${formatCurrency(value)}`}
      </NumDisplay>
    </Card>
  );
}

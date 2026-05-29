"use client";

import { useState } from "react";
import { useEnsureFetched } from "@/store/useEnsureFetched";
import {
  Check,
  Flame,
  Layers,
  PenLine,
  ShieldAlert,
  X,
} from "lucide-react";
import { Card } from "@/components/ui/card";
import { Chip } from "@/components/ui/chip";
import { WorkArea } from "@/components/ui/work-area";
import { Eyebrow, Body, Micro } from "@/components/ui/typography";
import { KpiSnug } from "@/components/ui/kpi-snug";
import { PageLoading } from "@/components/base/pageStates";
import { useDsiStore, type ApiRecord } from "@/store/dsiStore";
import { fmtRelative } from "@/lib/utils";
import { numOrNull, strOrNull } from "@/lib/coerce";

/* ============================================================
 * Referral Actions — mirrors reim_wb_b.jsx WbReferral (section 07).
 *
 * Four stacked rows:
 *   1. Spot-tone header — "Referred — pending underwriter audit" with
 *      trigger summary + Flagged/Audited/Total KPIs on the right
 *   2. Referral context — triggering conditions list with refer chips
 *   3. Signal audit matrix — wide 8-col table, override-aware rows
 *      (warn left border for flagged-unaudited; pos border for audited;
 *      flame icon for high-impact)
 *   4. Final decision — summary + Decline / Approve & bind buttons
 * ============================================================ */

type SignalAudit = {
  signal_code?: string;
  signal_id?: string;
  score?: number;
  confidence?: number;
  weight?: number;
  contribution?: number;
  flagged?: boolean;
  override?: boolean;
  audited_value?: number;
  rationale?: string;
};

export default function ReferralActionsPage() {
  const referral = useDsiStore((s) => s.activeReferral) as ApiRecord | null;
  const sub = useDsiStore((s) => s.activeSubmission) as ApiRecord | null;
  const referralSignals = useDsiStore((s) => s.referralSignals);
  const fetchReferralSignals = useDsiStore((s) => s.fetchReferralSignals);
  const submitOverride = useDsiStore((s) => s.submitSignalOverride);

  const submissionCode = sub?.submission_code as string | undefined;
  useEnsureFetched(submissionCode, fetchReferralSignals);
  const [overrideOpen, setOverrideOpen] = useState<string | null>(null);

  if (!referral || !sub) {
    return (
      <>
        <PageLoading message="Loading referral…" />
      </>
    );
  }

  const signals: SignalAudit[] = Array.isArray(referralSignals)
    ? (referralSignals as SignalAudit[])
    : [];

  const flagged = signals.filter((s) => s.flagged && !s.override);
  const audited = signals.filter((s) => s.override);

  const reasons = Array.isArray(referral.reasons)
    ? (referral.reasons as string[])
    : Array.isArray(referral.referral_reasons)
      ? (referral.referral_reasons as string[])
      : [];
  const priority = numOrNull(referral.priority) ?? (flagged.length >= 3 ? 1 : flagged.length >= 2 ? 2 : 3);
  const created = strOrNull(referral.created_at);
  const assignee = strOrNull(referral.assignee ?? referral.assigned_to);

  return (
    <>
      <WorkArea>
        {/* ─── 1. Referral header ─────────────────────────── */}
        <Card variant="spot" pad="lg">
          <div className="grid grid-cols-[auto_1fr_auto] items-center gap-5">
            <ShieldAlert size={32} className="text-spot" />
            <div>
              <Eyebrow className="text-spot-deep dark:text-spot">
                Referred — pending underwriter audit
              </Eyebrow>
              <h3 className="mt-1.5 font-display text-[17px] font-semibold leading-tight">
                Priority {priority} · auto-referred by {flagged.length}{" "}
                condition{flagged.length === 1 ? "" : "s"}
              </h3>
              <Micro className="mt-1 block">
                {reasons.length > 0
                  ? `Triggers: ${reasons.slice(0, 2).join(" · ")}.`
                  : "No referral reasons recorded."}
                {created ? ` Created ${fmtRelative(created)}.` : ""}
                {assignee ? ` Assigned to ${assignee}.` : ""}
              </Micro>
            </div>
            <div className="flex gap-3.5">
              <KpiSnug label="Flagged" value={String(flagged.length)} tone="warn" />
              <KpiSnug label="Audited" value={String(audited.length)} tone="pos" />
              <KpiSnug label="Total" value={String(signals.length)} />
            </div>
          </div>
        </Card>

        {/* ─── 2. Referral context — triggering conditions ─── */}
        <Card header="Referral context" icon={ShieldAlert} pad="md">
          <Eyebrow className="mb-2 block">Triggering conditions</Eyebrow>
          {reasons.length === 0 ? (
            <Body className="italic">No triggering conditions recorded.</Body>
          ) : (
            reasons.map((r, i) => (
              <div
                key={`${r}-${i}`}
                className="flex justify-between border-t border-rule py-2.5"
              >
                <div>
                  <span className="text-[13px]">{r}</span>
                  <Micro className="mt-0.5 block">signal_condition · refer</Micro>
                </div>
                <Chip variant="spot" size="sm">
                  refer
                </Chip>
              </div>
            ))
          )}
        </Card>

        {/* ─── 3. Signal audit matrix ────────────────────── */}
        <Card
          header="Signal audit matrix"
          icon={Layers}
          pad="md"
          headerRight={<Micro>{signals.length} signals</Micro>}
        >
          {signals.length === 0 ? (
            <Body className="italic">No signals to audit.</Body>
          ) : (
            <>
              <div className="grid grid-cols-[1.6fr_70px_70px_70px_90px_90px_1.4fr_60px] border-b border-rule py-1.5 text-[10.5px] uppercase tracking-wider text-ink-mute">
                {[
                  "Signal",
                  "Score",
                  "Conf",
                  "Weight",
                  "Contrib",
                  "Audited",
                  "Rationale",
                  "",
                ].map((h) => (
                  <span key={h}>{h}</span>
                ))}
              </div>
              {signals.map((s) => (
                <SignalRow
                  key={s.signal_code ?? s.signal_id}
                  signal={s}
                  onEdit={() =>
                    setOverrideOpen(
                      String(s.signal_code ?? s.signal_id ?? ""),
                    )
                  }
                />
              ))}
            </>
          )}
        </Card>

        {/* ─── 4. Final decision ───────────────────────────── */}
        <Card pad="md">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <Eyebrow>Final decision</Eyebrow>
              <h3 className="mt-1.5 font-display text-[15px] font-semibold leading-tight">
                {audited.length} signal{audited.length === 1 ? "" : "s"} audited ·{" "}
                {flagged.length} flagged signal{flagged.length === 1 ? "" : "s"} still
                pending audit
              </h3>
              <Micro className="mt-1 block">
                Audit or override the remaining flagged signals before binding.
              </Micro>
            </div>
            <div className="flex gap-2">
              <button
                type="button"
                className="inline-flex items-center gap-1.5 rounded-md border border-rule bg-surface px-3 py-1.5 text-[12px] text-neg hover:bg-surface-sunken"
              >
                <X size={13} /> Decline risk
              </button>
              <button
                type="button"
                className="inline-flex items-center gap-1.5 rounded-md bg-pos px-3 py-1.5 text-[12px] font-semibold text-canvas hover:opacity-90"
              >
                <Check size={13} /> Approve & bind
              </button>
            </div>
          </div>
        </Card>

        {/* Lightweight override sheet — rendered inline so the audit row
            stays visible while editing. */}
        {overrideOpen && (
          <OverrideSheet
            signalCode={overrideOpen}
            onClose={() => setOverrideOpen(null)}
            onSubmit={async (value, rationale) => {
              const quoteCode = sub.quote_code as string | undefined;
              if (!quoteCode) return;
              await submitOverride(quoteCode, overrideOpen, value, rationale);
              setOverrideOpen(null);
            }}
          />
        )}
      </WorkArea>
    </>
  );
}

/* ──────────────────── sub-components ──────────────────── */

function SignalRow({
  signal,
  onEdit,
}: {
  signal: SignalAudit;
  onEdit: () => void;
}) {
  const score = numOrNull(signal.score);
  const conf = numOrNull(signal.confidence);
  const weight = numOrNull(signal.weight);
  const contrib = numOrNull(signal.contribution);
  const highImpact = contrib != null && Math.abs(contrib) > 10;
  const overridden = !!signal.override;
  const flaggedUnaudited = !!signal.flagged && !overridden;
  const auditedValue = numOrNull(signal.audited_value);
  const rationale = strOrNull(signal.rationale);
  const lowConf = conf != null && conf < 0.7;

  const borderClass = flaggedUnaudited
    ? "border-l-[3px] border-l-warn"
    : overridden
      ? "border-l-[3px] border-l-pos"
      : "border-l-[3px] border-l-transparent";

  return (
    <div
      className={`grid grid-cols-[1.6fr_70px_70px_70px_90px_90px_1.4fr_60px] items-center border-b border-rule py-2.5 pl-2.5 text-[12.5px] ${borderClass}`}
    >
      <span className="flex items-center gap-1.5">
        {highImpact && <Flame size={12} className="text-warn" />}
        {overridden && <Check size={12} className="text-pos" />}
        <span
          className={`font-mono ${highImpact ? "font-bold" : "font-medium"}`}
        >
          {signal.signal_code ?? signal.signal_id ?? "—"}
        </span>
      </span>
      <span
        className={`tabular-nums ${overridden ? "font-bold text-pos" : ""}`}
      >
        {score != null ? score.toFixed(1) : "—"}
      </span>
      <span
        className={`tabular-nums ${lowConf ? "font-bold text-warn" : "text-ink-soft"}`}
      >
        {conf != null ? `${Math.round(conf * 100)}%` : "—"}
      </span>
      <span className="tabular-nums text-ink-soft">
        {weight != null ? weight.toFixed(2) : "—"}
      </span>
      <span
        className={`tabular-nums ${highImpact ? "font-bold text-warn" : ""}`}
      >
        {contrib != null ? contrib.toFixed(1) : "—"}
      </span>
      <span
        className={`tabular-nums font-semibold ${overridden ? "text-pos" : "text-ink-mute"}`}
      >
        {auditedValue != null ? auditedValue.toFixed(1) : "—"}
      </span>
      <Micro className="overflow-hidden text-ellipsis whitespace-nowrap text-[11px]">
        {rationale ?? "—"}
      </Micro>
      <button
        type="button"
        onClick={onEdit}
        aria-label="Audit signal"
        className="flex h-6 w-6 items-center justify-center justify-self-start rounded-md text-ink-mute hover:bg-surface-sunken hover:text-ink"
      >
        <PenLine size={14} />
      </button>
    </div>
  );
}

function OverrideSheet({
  signalCode,
  onClose,
  onSubmit,
}: {
  signalCode: string;
  onClose: () => void;
  onSubmit: (value: number | string, rationale: string) => Promise<void>;
}) {
  const [value, setValue] = useState("");
  const [rationale, setRationale] = useState("");
  const [submitting, setSubmitting] = useState(false);
  return (
    <Card pad="md">
      <div className="flex items-baseline justify-between">
        <Eyebrow>Audit signal</Eyebrow>
        <button
          type="button"
          onClick={onClose}
          className="text-[12px] text-ink-mute hover:text-ink"
        >
          Cancel
        </button>
      </div>
      <p className="mt-1.5 font-mono text-[13px]">{signalCode}</p>
      <div className="mt-3 grid gap-2.5 sm:grid-cols-[1fr_2fr_auto]">
        <input
          type="text"
          placeholder="Audited value"
          value={value}
          onChange={(e) => setValue(e.target.value)}
          className="rounded-md border border-rule bg-surface px-2.5 py-1.5 text-[13px]"
        />
        <input
          type="text"
          placeholder="Rationale"
          value={rationale}
          onChange={(e) => setRationale(e.target.value)}
          className="rounded-md border border-rule bg-surface px-2.5 py-1.5 text-[13px]"
        />
        <button
          type="button"
          disabled={!value || !rationale || submitting}
          onClick={async () => {
            setSubmitting(true);
            try {
              const v = Number(value);
              await onSubmit(Number.isFinite(v) ? v : value, rationale);
            } finally {
              setSubmitting(false);
            }
          }}
          className="rounded-md bg-info px-3 py-1.5 text-[12px] font-semibold text-canvas hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-50"
        >
          {submitting ? "Saving…" : "Submit override"}
        </button>
      </div>
    </Card>
  );
}

/* ──────────────────── helpers ──────────────────── */



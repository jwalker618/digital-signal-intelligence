"use client";

import { useEffect, useMemo, useState } from "react";
import { ArrowRight, FlaskConical, RotateCcw, ShieldAlert } from "lucide-react";
import { WorkbenchTopbar } from "@/components/chrome/workbench-topbar";
import { Card } from "@/components/ui/card";
import { Chip } from "@/components/ui/chip";
import { Button } from "@/components/ui/button";
import { Eyebrow, NumDisplay, Body, Micro } from "@/components/ui/typography";
import { PageError, PageLoading } from "@/components/base/pageStates";
import { useDsiStore, type ApiRecord } from "@/store/dsiStore";
import { formatCurrency } from "@/lib/format";
import {
  runFullCascade,
  type ScenarioOverrides,
  type ScenarioResult,
} from "@/lib/scenarioEngine";
import { cn } from "@/lib/utils";

/**
 * Workbench Scenarios — pick a few signal overrides + limit / deductible
 * adjustments, see the recalculated composite / tier / premium with
 * guardrails. Runs entirely client-side via scenarioEngine.runFullCascade.
 */
export default function WorkbenchScenariosPage() {
  const sub = useDsiStore((s) => s.activeSubmission);
  const ver = useDsiStore((s) => s.activeVersion);
  const signals = useDsiStore((s) => s.riskSignals);
  const fetchRiskSignals = useDsiStore((s) => s.fetchRiskSignals);

  const versionCode = ver?.version_code as string | undefined;
  const [signalsState, setSignalsState] = useState<"loading" | "ok" | "error">(
    signals.length > 0 ? "ok" : "loading",
  );
  const [signalsErr, setSignalsErr] = useState<string | null>(null);

  useEffect(() => {
    if (!versionCode) return;
    if (signals.length > 0) {
      setSignalsState("ok");
      return;
    }
    setSignalsState("loading");
    fetchRiskSignals(versionCode)
      .then(() => setSignalsState("ok"))
      .catch((e) => {
        setSignalsErr(e instanceof Error ? e.message : String(e));
        setSignalsState("error");
      });
  }, [versionCode, fetchRiskSignals, signals.length]);

  if (!sub || !ver) {
    return (
      <>
        <WorkbenchTopbar activeTabLabel="Scenarios" />
        <PageLoading message="Loading submission…" />
      </>
    );
  }
  if (signalsState === "loading")
    return (
      <>
        <WorkbenchTopbar activeTabLabel="Scenarios" />
        <PageLoading message="Loading signals…" />
      </>
    );
  if (signalsState === "error")
    return (
      <>
        <WorkbenchTopbar activeTabLabel="Scenarios" />
        <PageError message={signalsErr ?? "Unknown error"} />
      </>
    );

  return <ScenariosBody activeVersion={ver} signals={signals} />;
}

function ScenariosBody({
  activeVersion,
  signals,
}: {
  activeVersion: ApiRecord;
  signals: ApiRecord[];
}) {
  const fpd = (activeVersion.final_premium_detail ?? {}) as Record<string, unknown>;
  const baseLimit = Number(fpd.limit ?? activeVersion.recommended_limit ?? 0);
  const baseDeductible = Number(fpd.deductible ?? 0);

  // Overrides
  const [signalOverrides, setSignalOverrides] = useState<Record<string, number>>(
    {},
  );
  const [limitOverride, setLimitOverride] = useState<number | null>(null);
  const [deductibleOverride, setDeductibleOverride] = useState<number | null>(
    null,
  );

  const overrides: ScenarioOverrides = useMemo(
    () => ({
      signalOverrides,
      lossModifierOverride: null,
      exposureModifierOverride: null,
      limitOverride,
      deductibleOverride,
    }),
    [signalOverrides, limitOverride, deductibleOverride],
  );

  const result = useMemo<ScenarioResult | null>(() => {
    try {
      return runFullCascade(signals, activeVersion, overrides);
    } catch {
      return null;
    }
  }, [signals, activeVersion, overrides]);

  const dirty =
    Object.keys(signalOverrides).length > 0 ||
    limitOverride !== null ||
    deductibleOverride !== null;

  function reset() {
    setSignalOverrides({});
    setLimitOverride(null);
    setDeductibleOverride(null);
  }

  return (
    <>
      <WorkbenchTopbar activeTabLabel="Scenarios" />
      <div className="flex-1 overflow-y-auto px-9 py-7">
        <div className="mx-auto grid max-w-[1400px] gap-6 lg:grid-cols-[1.4fr_1fr]">
          {/* LEFT: live result */}
          <div className="space-y-6">
            <header>
              <Eyebrow>What-if cascade</Eyebrow>
              <h1 className="mt-1 flex items-center gap-3 font-display text-[28px] font-semibold leading-tight text-ink">
                <FlaskConical size={22} className="text-info" />
                Scenarios
              </h1>
              <Body className="mt-2">
                Override signals and structural terms to see how composite,
                tier, and premium would change. Guardrails enforced.
              </Body>
            </header>

            {result ? (
              <ResultCard result={result} dirty={dirty} onReset={reset} />
            ) : (
              <Card pad="lg" variant="warn">
                <Eyebrow className="text-warn">Cascade error</Eyebrow>
                <Body className="mt-1">
                  Couldn't compute the cascade — likely a missing field on the
                  active version. Try adjusting overrides.
                </Body>
              </Card>
            )}

            {result?.guardrails && (
              <GuardrailCard result={result} />
            )}
          </div>

          {/* RIGHT: controls */}
          <div className="space-y-6">
            <Card header="Structural overrides" icon={FlaskConical} pad="md" className="space-y-4">
              <NumericOverride
                label="Limit"
                base={baseLimit}
                value={limitOverride}
                onChange={setLimitOverride}
                step={1_000_000}
                format="currency"
              />
              <NumericOverride
                label="Deductible"
                base={baseDeductible}
                value={deductibleOverride}
                onChange={setDeductibleOverride}
                step={25_000}
                format="currency"
              />
            </Card>

            <Card
              header={`Signal overrides · ${signals.length}`}
              icon={FlaskConical}
              headerRight={
                Object.keys(signalOverrides).length > 0 ? (
                  <Button
                    type="button"
                    variant="ghost"
                    size="sm"
                    onClick={() => setSignalOverrides({})}
                  >
                    <RotateCcw size={11} />
                    Reset signals
                  </Button>
                ) : undefined
              }
              pad="md"
              className="space-y-3"
            >
              {signals.length === 0 ? (
                <Body className="italic">
                  No signals attached. Nothing to override.
                </Body>
              ) : (
                <ul className="max-h-[640px] space-y-2 overflow-y-auto pr-1">
                  {signals.slice(0, 30).map((s) => (
                    <SignalOverride
                      key={String(s.signal_id ?? s.signal_code)}
                      signal={s}
                      value={signalOverrides[String(s.signal_id ?? s.signal_code)]}
                      onChange={(v) => {
                        const key = String(s.signal_id ?? s.signal_code);
                        setSignalOverrides((prev) => {
                          if (v == null) {
                            const next = { ...prev };
                            delete next[key];
                            return next;
                          }
                          return { ...prev, [key]: v };
                        });
                      }}
                    />
                  ))}
                  {signals.length > 30 && (
                    <li>
                      <Micro>+{signals.length - 30} more not shown</Micro>
                    </li>
                  )}
                </ul>
              )}
            </Card>
          </div>
        </div>
      </div>
    </>
  );
}

function ResultCard({
  result,
  dirty,
  onReset,
}: {
  result: ScenarioResult;
  dirty: boolean;
  onReset: () => void;
}) {
  const compDelta = result.composite_score - result.original_composite;
  const premDelta = result.final_premium - result.original_final_premium;
  const tierDelta =
    (result.tier?.tier_id ?? result.original_tier) - result.original_tier;

  return (
    <Card variant="info" pad="lg" className="space-y-5">
      <header className="flex items-baseline justify-between">
        <Eyebrow className="text-info-deep dark:text-info">
          {dirty ? "Scenario result" : "Baseline (no overrides)"}
        </Eyebrow>
        {dirty && (
          <Button type="button" variant="ghost" size="sm" onClick={onReset}>
            <RotateCcw size={12} />
            Reset all
          </Button>
        )}
      </header>

      <div className="grid gap-6 sm:grid-cols-3">
        <DeltaStat
          label="Composite"
          before={result.original_composite}
          after={result.composite_score}
          delta={compDelta}
          tone={compDelta > 0 ? "pos" : compDelta < 0 ? "neg" : "mute"}
          fmt={(v) => v.toFixed(0)}
        />
        <DeltaStat
          label="Tier"
          before={result.original_tier}
          after={result.tier?.tier_id ?? result.original_tier}
          delta={tierDelta}
          tone={tierDelta < 0 ? "pos" : tierDelta > 0 ? "neg" : "mute"}
          fmt={(v) => v.toFixed(0)}
        />
        <DeltaStat
          label="Final premium"
          before={result.original_final_premium}
          after={result.final_premium}
          delta={premDelta}
          tone={premDelta < 0 ? "pos" : premDelta > 0 ? "neg" : "mute"}
          fmt={formatCurrency}
          emphasis
        />
      </div>

      <div className="grid gap-2 border-t border-info/30 pt-4 md:grid-cols-2">
        <FactorRow
          label="Loss combined"
          before={result.original_loss_combined}
          after={result.scenario_loss_combined}
        />
        <FactorRow
          label="Exposure modifier"
          before={result.original_exposure_modifier}
          after={result.scenario_exposure_modifier}
        />
        <FactorRow
          label="ILF"
          before={result.original_ilf_factor}
          after={result.ilf_factor}
        />
        <FactorRow
          label="Deductible factor"
          before={result.original_deductible_factor}
          after={result.deductible_factor}
        />
      </div>
    </Card>
  );
}

function GuardrailCard({ result }: { result: ScenarioResult }) {
  const g = result.guardrails as Record<string, unknown>;
  const triggered = !!(g.triggered ?? g.capped);
  const messages = (g.messages as string[]) ?? [];
  if (!triggered && messages.length === 0) return null;
  return (
    <Card variant="warn" pad="md" className="flex items-start gap-3">
      <ShieldAlert size={18} className="mt-0.5 shrink-0 text-warn" />
      <div>
        <Eyebrow className="text-warn">Guardrails active</Eyebrow>
        {messages.length > 0 ? (
          <ul className="mt-1.5 space-y-1">
            {messages.map((m, i) => (
              <li key={i} className="text-[13px] text-ink">
                {m}
              </li>
            ))}
          </ul>
        ) : (
          <Body className="mt-1">
            The cascade hit a guardrail and the premium was capped from{" "}
            <strong>{formatCurrency(result.final_premium * 1.5)}</strong> to{" "}
            <strong>{formatCurrency(result.final_premium)}</strong>.
          </Body>
        )}
      </div>
    </Card>
  );
}

function DeltaStat({
  label,
  before,
  after,
  delta,
  tone,
  fmt,
  emphasis,
}: {
  label: string;
  before: number;
  after: number;
  delta: number;
  tone: "pos" | "neg" | "mute";
  fmt: (v: number) => string;
  emphasis?: boolean;
}) {
  return (
    <div>
      <Micro className="block">{label}</Micro>
      <div className="mt-1 flex items-baseline gap-2">
        <NumDisplay size={emphasis ? "lg" : "md"}>{fmt(after)}</NumDisplay>
      </div>
      <div className="mt-1 flex items-center gap-1 text-[12px]">
        <span className="text-ink-mute tabular-nums">{fmt(before)}</span>
        <ArrowRight size={10} className="text-ink-mute" />
        <span
          className={cn(
            "tabular-nums",
            tone === "pos"
              ? "text-pos"
              : tone === "neg"
                ? "text-neg"
                : "text-ink-mute",
          )}
        >
          {delta > 0 ? "+" : ""}
          {fmt(delta)}
        </span>
      </div>
    </div>
  );
}

function FactorRow({
  label,
  before,
  after,
}: {
  label: string;
  before: number;
  after: number;
}) {
  const changed = Math.abs(before - after) > 0.0001;
  return (
    <div
      className={cn(
        "flex items-baseline justify-between text-[13px]",
        changed && "font-semibold",
      )}
    >
      <span className="text-ink-soft">{label}</span>
      <span className="tabular-nums text-ink">
        ×{before.toFixed(3)}
        {changed && (
          <>
            <ArrowRight size={10} className="mx-1 inline text-ink-mute" />×
            {after.toFixed(3)}
          </>
        )}
      </span>
    </div>
  );
}

function NumericOverride({
  label,
  base,
  value,
  onChange,
  step,
  format,
}: {
  label: string;
  base: number;
  value: number | null;
  onChange: (v: number | null) => void;
  step: number;
  format: "currency" | "number";
}) {
  const effective = value ?? base;
  const fmt = format === "currency" ? formatCurrency : (v: number) => v.toLocaleString();
  return (
    <div>
      <div className="mb-1.5 flex items-baseline justify-between">
        <label className="text-[12.5px] font-medium text-ink-soft">{label}</label>
        <span className="text-[12px] text-ink-mute">
          base {fmt(base)}
        </span>
      </div>
      <div className="flex items-center gap-2">
        <input
          type="number"
          value={effective}
          step={step}
          onChange={(e) => {
            const v = Number(e.target.value);
            onChange(Number.isFinite(v) && v !== base ? v : null);
          }}
          className="h-9 flex-1 rounded-btn border border-rule-strong bg-surface px-2.5 text-[13px] tabular-nums text-ink focus:border-info focus:outline-none focus:ring-2 focus:ring-info/30"
        />
        {value !== null && (
          <Button
            type="button"
            variant="ghost"
            size="sm"
            onClick={() => onChange(null)}
            aria-label={`Reset ${label}`}
          >
            <RotateCcw size={12} />
          </Button>
        )}
      </div>
    </div>
  );
}

function SignalOverride({
  signal,
  value,
  onChange,
}: {
  signal: ApiRecord;
  value: number | undefined;
  onChange: (v: number | null) => void;
}) {
  const baseMod = Number(signal.applied_modifier ?? 1);
  const effective = value ?? baseMod;
  const action = String(signal.action ?? "").toLowerCase();
  const tone =
    action === "approve"
      ? "pos"
      : action === "refer"
        ? "warn"
        : action === "decline"
          ? "neg"
          : "info";
  return (
    <li className="space-y-1 border-b border-rule pb-2 last:border-0">
      <div className="flex items-center gap-2">
        <Chip variant={tone} size="sm">
          {signal.action ?? "—"}
        </Chip>
        <span className="flex-1 truncate font-mono text-[11.5px] text-ink">
          {String(signal.signal_id ?? signal.signal_code ?? "—")}
        </span>
        {value !== undefined && (
          <button
            type="button"
            onClick={() => onChange(null)}
            className="text-ink-mute hover:text-ink"
            aria-label="Reset signal"
          >
            <RotateCcw size={11} />
          </button>
        )}
      </div>
      <div className="flex items-center gap-2">
        <input
          type="range"
          min={0.5}
          max={1.5}
          step={0.01}
          value={effective}
          onChange={(e) => {
            const v = Number(e.target.value);
            onChange(Math.abs(v - baseMod) < 0.005 ? null : v);
          }}
          className="flex-1 accent-info"
        />
        <span className="w-12 text-right text-[11.5px] tabular-nums text-ink">
          ×{effective.toFixed(2)}
        </span>
      </div>
    </li>
  );
}

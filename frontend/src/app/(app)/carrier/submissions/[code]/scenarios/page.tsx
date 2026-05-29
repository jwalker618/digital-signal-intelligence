"use client";

import { useMemo, useState } from "react";
import { useEnsureFetched } from "@/store/useEnsureFetched";
import { FlaskConical, Layers, Shield, TrendingDown } from "lucide-react";
import { Card } from "@/components/ui/card";
import { Chip } from "@/components/ui/chip";
import { WorkArea } from "@/components/ui/work-area";
import { Body, Micro } from "@/components/ui/typography";
import { PageLoading } from "@/components/base/pageStates";
import { useDsiStore, type ApiRecord } from "@/store/dsiStore";
import { formatCurrency } from "@/lib/format";
import { numOrNull, strOrNull } from "@/lib/coerce";
import {
  runFullCascade,
  type ScenarioOverrides,
  type ScenarioResult,
} from "@/lib/scenarioEngine";

/* ============================================================
 * Scenarios — mirrors reim_wb_c.jsx WbScenarios.
 *
 * Three stacked rows:
 *   1. Signal overrides — original vs scenario composite at the top,
 *      then a 6-col table where the Scenario column is editable
 *   2. Two-col: Loss modifier compare + Exposure & scaling compare
 *   3. Pricing cascade — original vs scenario row-by-row, capped by
 *      a heavy Final premium row with the dollar/% delta beneath
 * ============================================================ */

type SignalRow = {
  signal_id?: string;
  signal_code?: string;
  signal_name?: string;
  score?: number;
  weight?: number;
  contribution?: number;
};

export default function ScenariosPage() {
  const sub = useDsiStore((s) => s.activeSubmission) as ApiRecord | null;
  const ver = useDsiStore((s) => s.activeVersion) as ApiRecord | null;
  const signals = useDsiStore((s) => s.riskSignals) as SignalRow[];
  const fetchSignals = useDsiStore((s) => s.fetchRiskSignals);

  const versionCode = ver?.version_code as string | undefined;
  useEnsureFetched(
    signals.length === 0 ? versionCode : undefined,
    fetchSignals,
  );

  const [signalOverrides, setSignalOverrides] = useState<Record<string, number>>({});

  const overrides: ScenarioOverrides = useMemo(
    () => ({ signal_overrides: signalOverrides }),
    [signalOverrides],
  );

  const result = useMemo<ScenarioResult | null>(() => {
    if (!ver || !sub) return null;
    try {
      return runFullCascade(ver, sub, overrides);
    } catch {
      return null;
    }
  }, [ver, sub, overrides]);

  if (!ver || !sub) {
    return (
      <>
        <PageLoading message="Loading scenario engine…" />
      </>
    );
  }
  if (!result) {
    return (
      <>
        <Body className="mx-auto max-w-[600px] py-12 text-center italic">
          Scenario cascade unavailable for this version.
        </Body>
      </>
    );
  }

  const modifiedCount = Object.keys(signalOverrides).length;
  const compositeDelta = result.composite_score - result.original_composite;
  const tierChanged =
    result.tier != null && Number(result.tier.tier) !== result.original_tier;

  return (
    <>
      <WorkArea>
        {/* ─── 1. Signal overrides ─────────────────────────── */}
        <Card
          header="Signal overrides"
          icon={FlaskConical}
          pad="md"
          headerRight={
            modifiedCount > 0 ? (
              <Chip variant="info" size="sm">
                {modifiedCount} modified
              </Chip>
            ) : undefined
          }
        >
          <div className="mb-3.5 grid grid-cols-2 gap-4">
            <div>
              <Micro>Original composite</Micro>
              <div className="mt-0.5 flex items-baseline gap-2">
                <span className="font-mono text-[22px] font-bold tabular-nums">
                  {result.original_composite.toFixed(0)}
                </span>
                <Micro>Tier {result.original_tier}</Micro>
              </div>
            </div>
            <div>
              <Micro className="text-info">Scenario composite</Micro>
              <div className="mt-0.5 flex items-baseline gap-2">
                <span className="font-mono text-[26px] font-bold text-info tabular-nums">
                  {result.composite_score.toFixed(0)}
                </span>
                {compositeDelta !== 0 && (
                  <span
                    className={`text-[11px] font-bold ${
                      compositeDelta > 0 ? "text-pos" : "text-warn"
                    }`}
                  >
                    {compositeDelta > 0 ? "+" : ""}
                    {compositeDelta.toFixed(0)}
                  </span>
                )}
                <Micro>
                  Tier {result.tier?.tier ?? "—"} ·{" "}
                  {tierChanged ? "changed" : "stays"}
                </Micro>
              </div>
            </div>
          </div>

          <div className="grid grid-cols-[1.6fr_70px_70px_90px_90px_90px] border-y border-rule py-2 text-[10.5px] uppercase tracking-wider text-ink-mute">
            {[
              "Signal",
              "Original",
              "Weight",
              "Contribution",
              "Scenario",
              "New contrib",
            ].map((h) => (
              <span key={h}>{h}</span>
            ))}
          </div>
          {signals.length === 0 ? (
            <Micro className="block py-4 italic">No signals loaded.</Micro>
          ) : (
            signals.map((s) => {
              const code = String(s.signal_code ?? s.signal_id ?? "");
              const original = numOrNull(s.score);
              const weight = numOrNull(s.weight);
              const contribution = numOrNull(s.contribution);
              const scenarioValue = signalOverrides[code] ?? original ?? 0;
              const newContrib =
                weight != null ? scenarioValue * weight : null;
              const changed =
                signalOverrides[code] != null &&
                original != null &&
                signalOverrides[code] !== original;
              return (
                <div
                  key={code}
                  className="grid grid-cols-[1.6fr_70px_70px_90px_90px_90px] items-center border-b border-rule py-2.5 text-[13px]"
                >
                  <code className="text-[12px]">{code}</code>
                  <span className="tabular-nums">
                    {original != null ? original.toFixed(0) : "—"}
                  </span>
                  <span className="tabular-nums text-ink-soft">
                    {weight != null ? weight.toFixed(2) : "—"}
                  </span>
                  <span className="tabular-nums">
                    {contribution != null ? contribution.toFixed(1) : "—"}
                  </span>
                  <input
                    type="number"
                    min={0}
                    max={100}
                    value={scenarioValue}
                    onChange={(e) => {
                      const v = Number(e.target.value);
                      setSignalOverrides((prev) => {
                        const next = { ...prev };
                        if (
                          Number.isFinite(v) &&
                          original != null &&
                          v !== original
                        ) {
                          next[code] = v;
                        } else {
                          delete next[code];
                        }
                        return next;
                      });
                    }}
                    className={`w-16 rounded-md border px-2 py-1 text-center font-bold tabular-nums ${
                      changed
                        ? "border-info bg-info-soft text-info"
                        : "border-rule bg-surface"
                    }`}
                  />
                  <span
                    className={`font-bold tabular-nums ${changed ? "text-info" : ""}`}
                  >
                    {newContrib != null ? newContrib.toFixed(1) : "—"}
                  </span>
                </div>
              );
            })
          )}
        </Card>

        {/* ─── 2. Loss + Exposure compare ──────────────────── */}
        <div className="grid gap-3.5 md:grid-cols-2">
          <Card header="Loss modifier" icon={Shield} pad="md">
            <CompareRow
              k="Combined modifier"
              o={`${result.original_loss_combined.toFixed(2)}x`}
              s={`${result.scenario_loss_combined.toFixed(2)}x`}
              bold
            />
            {result.loss_modifier && (
              <>
                <CompareRow
                  k="Frequency multiplier"
                  o={`${(result.loss_modifier.original_frequency ?? 1).toFixed(2)}x`}
                  s={`${result.loss_modifier.frequency_multiplier.toFixed(2)}x`}
                />
                <CompareRow
                  k="Severity multiplier"
                  o={`${(result.loss_modifier.original_severity ?? 1).toFixed(2)}x`}
                  s={`${result.loss_modifier.severity_multiplier.toFixed(2)}x`}
                />
              </>
            )}
          </Card>
          <Card header="Exposure & scaling" icon={Layers} pad="md">
            <CompareRow
              k="Exposure modifier"
              o={`${result.original_exposure_modifier.toFixed(2)}x`}
              s={`${result.scenario_exposure_modifier.toFixed(2)}x`}
              bold
            />
            <CompareRow
              k="Exposure band"
              o={strOrNull(ver.exposure_band_label) ?? "—"}
              s={result.scenario_exposure_band || "—"}
            />
            <CompareRow
              k="ILF factor"
              o={`${result.original_ilf_factor.toFixed(3)}x`}
              s={`${result.ilf_factor.toFixed(3)}x`}
            />
            <CompareRow
              k="Deductible factor"
              o={`${result.original_deductible_factor.toFixed(3)}x`}
              s={`${result.deductible_factor.toFixed(3)}x`}
            />
          </Card>
        </div>

        {/* ─── 3. Pricing cascade ──────────────────────────── */}
        <Card
          header="Pricing cascade · original vs scenario"
          icon={TrendingDown}
          pad="md"
        >
          <div className="grid grid-cols-[50%_25%_25%] border-b border-rule py-2 text-[10.5px] uppercase tracking-wider text-ink-mute">
            <span>Step</span>
            <span className="text-right">Original</span>
            <span className="text-right text-info">Scenario</span>
          </div>
          <CascadeRow
            step="Tier assignment"
            o={`Tier ${result.original_tier}`}
            s={`Tier ${result.tier?.tier ?? "—"}`}
          />
          <CascadeRow
            step="Base premium"
            o={formatCurrency(result.original_base_premium)}
            s={formatCurrency(result.base_premium)}
          />
          {result.waterfall.map((step, i) => (
            <CascadeRow
              key={`${step.label}-${i}`}
              step={`After ${step.label.toLowerCase()}`}
              o={formatCurrency(step.original ?? step.value)}
              s={formatCurrency(step.value)}
            />
          ))}
          <div className="mt-1 grid grid-cols-[50%_25%_25%] border-t-2 border-ink px-1 py-3.5 text-[17px] font-bold">
            <span>Final premium</span>
            <span className="text-right font-mono tabular-nums">
              {formatCurrency(result.original_final_premium)}
            </span>
            <span className="text-right font-mono text-pos tabular-nums">
              {formatCurrency(result.final_premium)}
            </span>
          </div>
          {result.final_premium !== result.original_final_premium && (
            <Micro className="mt-1 block text-right text-[13px] font-bold text-pos">
              {result.final_premium < result.original_final_premium ? "−" : "+"}
              {formatCurrency(
                Math.abs(result.final_premium - result.original_final_premium),
              )}{" "}
              (
              {(
                ((result.final_premium - result.original_final_premium) /
                  result.original_final_premium) *
                100
              ).toFixed(1)}
              %) vs original
            </Micro>
          )}
        </Card>
      </WorkArea>
    </>
  );
}

function CompareRow({
  k,
  o,
  s,
  bold,
}: {
  k: string;
  o: string;
  s: string;
  bold?: boolean;
}) {
  const changed = o !== s;
  return (
    <div
      className={`grid grid-cols-[1fr_80px_30px_80px] items-baseline border-b border-rule py-2 text-[13px] ${
        bold ? "font-bold" : ""
      }`}
    >
      <span className="text-ink-soft">{k}</span>
      <span className="text-right font-mono tabular-nums">{o}</span>
      <span className="text-center text-ink-mute">→</span>
      <span
        className={`text-right font-mono tabular-nums ${
          changed ? "font-semibold text-info" : ""
        }`}
      >
        {s}
      </span>
    </div>
  );
}

function CascadeRow({ step, o, s }: { step: string; o: string; s: string }) {
  const changed = o !== s;
  return (
    <div className="grid grid-cols-[50%_25%_25%] border-b border-rule py-2 text-[13px]">
      <span>{step}</span>
      <span className="text-right font-mono tabular-nums">{o}</span>
      <span
        className={`text-right font-mono tabular-nums ${
          changed ? "font-bold text-info" : ""
        }`}
      >
        {s}
      </span>
    </div>
  );
}



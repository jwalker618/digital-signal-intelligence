"use client";

import { Calculator, Layers, ShieldAlert } from "lucide-react";
import { WorkbenchTopbar } from "@/components/chrome/workbench-topbar";
import { Card } from "@/components/ui/card";
import { Chip } from "@/components/ui/chip";
import { NumDisplay, Body, Micro } from "@/components/ui/typography";
import { LabelRow } from "@/components/ui/label-row";
import { Waterfall } from "@/components/charts/waterfall";
import { PageLoading } from "@/components/base/pageStates";
import { useDsiStore } from "@/store/dsiStore";
import { formatCurrency, formatPercent } from "@/lib/format";

/**
 * Pricing anatomy — base → modifier chain → final. Reads from
 * `activeVersion` which carries the full pricing object.
 */
export default function PricingAnatomyPage() {
  const ver = useDsiStore((s) => s.activeVersion);

  if (!ver) {
    return (
      <>
        <WorkbenchTopbar activeTabLabel="Pricing Anatomy" />
        <PageLoading message="Loading pricing data…" />
      </>
    );
  }

  const base = Number(ver.base_premium ?? 0);
  const final = Number(ver.final_premium ?? base);
  const lossMod = Number(ver.loss_combined_modifier ?? 1);
  const expMod = Number(ver.exposure_modifier ?? 1);
  const ilf = Number(ver.ilf_factor ?? 1);
  const fpd = ver.final_premium_detail ?? {};
  const dedFactor = Number(fpd.deductible_factor ?? 1);
  const signalConditions: Array<{
    signal_id?: string;
    action?: string;
    note?: string;
    applied_modifier?: number;
  }> = ver.signal_conditions ?? [];

  const modifierImpactPct = base > 0 ? (final - base) / base : 0;
  const lossDelta = base * (lossMod - 1);
  const expDelta = base * lossMod * (expMod - 1);
  const ilfDelta = base * lossMod * expMod * (ilf - 1);
  const dedDelta = base * lossMod * expMod * ilf * (dedFactor - 1);

  return (
    <>
      <WorkbenchTopbar activeTabLabel="Pricing Anatomy" />
      <div className="flex-1 overflow-y-auto px-9 py-7">
        <div className="mx-auto grid max-w-[1280px] gap-6">
          {/* Hero numbers */}
          <div className="grid gap-4 md:grid-cols-3">
            <Stat label="Base premium">{formatCurrency(base)}</Stat>
            <Stat
              label="Net modifier"
              tone={modifierImpactPct >= 0 ? "neg" : "pos"}
            >
              {modifierImpactPct >= 0 ? "+" : ""}
              {formatPercent(modifierImpactPct, 1)}
            </Stat>
            <Stat label="Final premium" emphasis>
              {formatCurrency(final)}
            </Stat>
          </div>

          {/* Modifier chain */}
          <Card header="Pricing anatomy" icon={Calculator} pad="lg">
            <Waterfall
              items={[
                { id: "base", label: "Base", value: base, type: "base" },
                { id: "loss", label: "Loss", value: lossDelta, type: lossDelta < 0 ? "pos" : "opp" },
                { id: "exp", label: "Exposure", value: expDelta, type: expDelta < 0 ? "pos" : "opp" },
                { id: "ilf", label: "ILF", value: ilfDelta, type: ilfDelta < 0 ? "pos" : "opp" },
                { id: "ded", label: "Deductible", value: dedDelta, type: dedDelta < 0 ? "pos" : "opp" },
                { id: "final", label: "Final", value: final, type: "final" },
              ]}
            />
          </Card>

          {/* Detail */}
          <Card header="Factors" icon={Layers} pad="md" className="grid gap-2 md:grid-cols-2">
            <LabelRow
              label="Loss combined modifier"
              value={`×${lossMod.toFixed(3)}`}
            />
            <LabelRow
              label="Exposure modifier"
              value={`×${expMod.toFixed(3)}`}
            />
            <LabelRow label="ILF" value={`×${ilf.toFixed(3)}`} />
            <LabelRow
              label="Deductible factor"
              value={`×${dedFactor.toFixed(3)}`}
            />
          </Card>

          {/* Signal conditions */}
          {signalConditions.length > 0 && (
            <Card
              header={`Active conditions · ${signalConditions.length}`}
              icon={ShieldAlert}
              pad="md"
            >
              <ul className="divide-y divide-rule">
                {signalConditions.map((c, i) => {
                  const action = (c.action ?? "").toLowerCase();
                  const tone =
                    action === "approve"
                      ? "pos"
                      : action === "decline"
                        ? "neg"
                        : action === "refer"
                          ? "warn"
                          : "info";
                  return (
                    <li
                      key={`${c.signal_id}-${i}`}
                      className="flex items-start gap-3 py-2.5"
                    >
                      <Chip variant={tone} size="sm">
                        {c.action ?? "—"}
                      </Chip>
                      <div className="min-w-0 flex-1">
                        <p className="font-mono text-[12.5px] text-ink">
                          {c.signal_id ?? "—"}
                        </p>
                        {c.note && (
                          <Body className="mt-0.5 text-[12.5px]">{c.note}</Body>
                        )}
                      </div>
                      {c.applied_modifier != null && (
                        <span className="font-semibold tabular-nums text-ink">
                          ×{Number(c.applied_modifier).toFixed(3)}
                        </span>
                      )}
                    </li>
                  );
                })}
              </ul>
            </Card>
          )}
        </div>
      </div>
    </>
  );
}

function Stat({
  label,
  tone,
  emphasis,
  children,
}: {
  label: string;
  tone?: "pos" | "neg";
  emphasis?: boolean;
  children: React.ReactNode;
}) {
  return (
    <Card pad="md" variant={emphasis ? "info" : "default"}>
      <Micro
        className={
          emphasis
            ? "text-info-deep dark:text-info"
            : tone === "pos"
              ? "text-pos"
              : tone === "neg"
                ? "text-neg"
                : ""
        }
      >
        {label}
      </Micro>
      <NumDisplay
        size={emphasis ? "lg" : "md"}
        className={`mt-2 block ${
          tone === "pos" ? "text-pos" : tone === "neg" ? "text-neg" : ""
        }`}
      >
        {children}
      </NumDisplay>
    </Card>
  );
}

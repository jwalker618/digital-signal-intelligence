"use client";

import { use, useEffect, useState } from "react";
import { Glasses, Layers } from "lucide-react";
import { WorkbenchTopbar } from "@/components/chrome/workbench-topbar";
import { Card } from "@/components/ui/card";
import { Chip } from "@/components/ui/chip";
import { Eyebrow, Body, Micro } from "@/components/ui/typography";
import { KpiSnug } from "@/components/ui/kpi-snug";
import { PageError, PageLoading } from "@/components/base/pageStates";
import { useDsiStore } from "@/store/dsiStore";

/**
 * Risk assessment — the signal-by-signal view of why this submission got
 * the score it did. Reads from activeVersion.signal_conditions; falls back
 * to fetchRiskSignals if the version doesn't carry them yet.
 */
export default function RiskAssessmentPage(props: {
  params: Promise<{ code: string }>;
}) {
  use(props.params);
  const ver = useDsiStore((s) => s.activeVersion);
  const fetchRiskSignals = useDsiStore((s) => s.fetchRiskSignals);
  const [state, setState] = useState<"ok" | "loading" | "error">("ok");
  const [err, setErr] = useState<string | null>(null);

  const versionCode = ver?.version_code as string | undefined;

  useEffect(() => {
    if (!versionCode) return;
    if (ver?.signal_conditions?.length) return;
    setState("loading");
    fetchRiskSignals(versionCode)
      .then(() => setState("ok"))
      .catch((e) => {
        setErr(e instanceof Error ? e.message : String(e));
        setState("error");
      });
  }, [versionCode, fetchRiskSignals, ver?.signal_conditions]);

  if (!ver)
    return (
      <>
        <WorkbenchTopbar activeTabLabel="Risk Assessment" />
        <PageLoading />
      </>
    );
  if (state === "loading")
    return (
      <>
        <WorkbenchTopbar activeTabLabel="Risk Assessment" />
        <PageLoading message="Loading signal evaluation…" />
      </>
    );
  if (state === "error")
    return (
      <>
        <WorkbenchTopbar activeTabLabel="Risk Assessment" />
        <PageError message={err ?? "Unknown error"} />
      </>
    );

  const conditions: Array<{
    signal_id?: string;
    action?: string;
    note?: string;
    applied_modifier?: number;
  }> = ver.signal_conditions ?? [];

  // Group by action.
  const approve = conditions.filter(
    (c) => (c.action ?? "").toLowerCase() === "approve",
  );
  const refer = conditions.filter(
    (c) => (c.action ?? "").toLowerCase() === "refer",
  );
  const decline = conditions.filter(
    (c) => (c.action ?? "").toLowerCase() === "decline",
  );
  const modifier = conditions.filter(
    (c) => (c.action ?? "").toLowerCase() === "modifier",
  );

  const composite = ver.final_composite_score ?? ver.pure_composite_score ?? null;
  const confidence = ver.confidence ?? null;
  const coverage = ver.signal_coverage ?? null;
  const tier = ver.final_tier ?? null;
  const tierLabel = ver.tier_label ?? null;

  return (
    <>
      <WorkbenchTopbar activeTabLabel="Risk Assessment" />
      <div className="flex-1 overflow-y-auto px-9 py-7">
        <div className="mx-auto grid max-w-[1280px] gap-6">
          {/* Results */}
          <Card header="Results" icon={Glasses} pad="md">
            <div className="grid grid-cols-2 gap-6 sm:grid-cols-4">
              <KpiSnug
                label="Composite"
                value={composite != null ? Number(composite).toFixed(0) : "—"}
                tone="info"
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
                label="Signal coverage"
                value={
                  coverage != null
                    ? `${(Number(coverage) * 100).toFixed(0)}%`
                    : "—"
                }
                tone="pos"
              />
              <KpiSnug
                label="Final tier"
                value={
                  tier != null
                    ? `T${tier}${tierLabel ? ` · ${tierLabel}` : ""}`
                    : "—"
                }
                tone="info"
              />
            </div>
          </Card>

          <Card header="Action breakdown" icon={Layers} pad="md">
            <div className="grid gap-4 sm:grid-cols-4">
            <Bucket label="Approve" count={approve.length} tone="pos" />
            <Bucket label="Refer" count={refer.length} tone="warn" />
            <Bucket label="Decline" count={decline.length} tone="neg" />
            <Bucket label="Modifier" count={modifier.length} tone="info" />
            </div>
          </Card>

          {refer.length > 0 && (
            <SignalSection title="Referred" tone="warn" items={refer} />
          )}
          {decline.length > 0 && (
            <SignalSection title="Decline triggers" tone="neg" items={decline} />
          )}
          {modifier.length > 0 && (
            <SignalSection title="Modifier signals" tone="info" items={modifier} />
          )}
          {approve.length > 0 && (
            <SignalSection title="Approve signals" tone="pos" items={approve} />
          )}

          {conditions.length === 0 && (
            <Card pad="lg">
              <Body className="italic">
                No signal conditions are attached to this version yet.
              </Body>
            </Card>
          )}
        </div>
      </div>
    </>
  );
}

function Bucket({
  label,
  count,
  tone,
}: {
  label: string;
  count: number;
  tone: "pos" | "warn" | "neg" | "info";
}) {
  return (
    <Card pad="md" variant={tone}>
      <Micro
        className={
          tone === "pos"
            ? "text-pos"
            : tone === "warn"
              ? "text-warn"
              : tone === "neg"
                ? "text-neg"
                : "text-info-deep dark:text-info"
        }
      >
        {label}
      </Micro>
      <p className="mt-2 font-display text-[28px] font-semibold tabular-nums text-ink">
        {count}
      </p>
    </Card>
  );
}

function SignalSection({
  title,
  tone,
  items,
}: {
  title: string;
  tone: "pos" | "warn" | "neg" | "info";
  items: Array<{
    signal_id?: string;
    action?: string;
    note?: string;
    applied_modifier?: number;
  }>;
}) {
  return (
    <section>
      <Eyebrow className="mb-3">
        {title} ({items.length})
      </Eyebrow>
      <Card pad="md" className="overflow-hidden p-0">
        <ul className="divide-y divide-rule">
          {items.map((s, i) => (
            <li
              key={`${s.signal_id}-${i}`}
              className="flex items-start gap-3 px-4 py-2.5"
            >
              <Chip variant={tone} size="sm">
                {s.action ?? "—"}
              </Chip>
              <div className="min-w-0 flex-1">
                <p className="font-mono text-[12.5px] text-ink">
                  {s.signal_id ?? "—"}
                </p>
                {s.note && (
                  <Body className="mt-0.5 text-[12.5px]">{s.note}</Body>
                )}
              </div>
              {s.applied_modifier != null && (
                <span className="shrink-0 font-semibold tabular-nums text-ink">
                  ×{Number(s.applied_modifier).toFixed(3)}
                </span>
              )}
            </li>
          ))}
        </ul>
      </Card>
    </section>
  );
}

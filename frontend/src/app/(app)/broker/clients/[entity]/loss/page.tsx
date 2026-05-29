"use client";

import { CheckCircle2, Minus, ShieldAlert, SlidersHorizontal, TrendingDown, TrendingUp } from "lucide-react";
import { Card } from "@/components/ui/card";
import { Chip } from "@/components/ui/chip";
import { WorkArea } from "@/components/ui/work-area";
import { Body, Micro } from "@/components/ui/typography";
import { KpiSnug } from "@/components/ui/kpi-snug";
import { LabelRow } from "@/components/ui/label-row";
import { formatCurrency, formatText } from "@/lib/format";
import { fmtRelative } from "@/lib/utils";
import { useClientWorkbench } from "../_lib/context";
import { kFmt } from "../_lib/helpers";

export default function LossProfilePage() {
  const cw = useClientWorkbench();
  if (!cw) return null;
  const c = cw.coverages[0];

  const band = c?.loss_propensity_band ?? null;
  const combined = c?.loss_combined_modifier ?? null;
  const freq = c?.loss_frequency_multiplier ?? null;
  const sev = c?.loss_severity_multiplier ?? null;
  const freqVel = c?.loss_frequency_velocity ?? null;
  const sevVel = c?.loss_severity_velocity ?? null;
  const combinedVel =
    freqVel != null && sevVel != null ? (freqVel + sevVel) / 2 : freqVel ?? sevVel;

  return (
    <WorkArea>
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4 lg:grid-cols-7">
        <Card pad="sm">
          <KpiSnug
            label="Propensity"
            value={band ? band.toUpperCase() : "—"}
            tone={band && /low/i.test(band) ? "pos" : "default"}
          />
        </Card>
        <Card pad="sm">
          <KpiSnug label="Band" value={band ? formatText(band, "capitalize") : "—"} />
        </Card>
        <Card pad="sm">
          <KpiSnug
            label="Combined mod"
            value={combined != null ? `${combined.toFixed(2)}x` : "—"}
            tone={combined != null && combined < 1 ? "pos" : "default"}
          />
        </Card>
        <Card pad="sm">
          <KpiSnug label="Freq mult" value={freq != null ? `${freq.toFixed(2)}x` : "—"} />
        </Card>
        <Card pad="sm">
          <KpiSnug label="Sev mult" value={sev != null ? `${sev.toFixed(2)}x` : "—"} />
        </Card>
        <Card pad="sm">
          <KpiSnug
            label="Confidence"
            value={c?.loss_confidence != null ? `${Math.round(c.loss_confidence * 100)}%` : "—"}
          />
        </Card>
        <Card pad="sm">
          <KpiSnug label="Cohort" value={c?.loss_cohort_name ?? "—"} />
        </Card>
      </div>

      <div className="grid gap-3.5 lg:grid-cols-2">
        <Card header="Loss trajectory" icon={TrendingUp} pad="md">
          <TrajectoryRow
            label="Overall"
            trend={c?.loss_trend_direction ?? velocityTrend(combinedVel)}
            delta={combinedVel}
          />
          <TrajectoryRow label="Frequency" trend={velocityTrend(freqVel)} delta={freqVel} />
          <TrajectoryRow label="Severity" trend={velocityTrend(sevVel)} delta={sevVel} />
          <Micro className="mt-2 block">
            Velocity is points/month; negative reads as improving.
          </Micro>
        </Card>

        <Card header="Modifiers" icon={SlidersHorizontal} pad="md">
          <LabelRow label="Frequency multiplier" value={freq != null ? `${freq.toFixed(2)}x` : "—"} />
          <LabelRow label="Severity multiplier" value={sev != null ? `${sev.toFixed(2)}x` : "—"} />
          <LabelRow label="Combined modifier" value={combined != null ? `${combined.toFixed(2)}x` : "—"} />
          <LabelRow label="Loss cohort" value={c?.loss_cohort_name ?? "—"} />
          <LabelRow
            label="Model confidence"
            value={c?.loss_confidence != null ? `${Math.round(c.loss_confidence * 100)}%` : "—"}
          />
        </Card>
      </div>

      <Card
        header="Loss event history"
        icon={ShieldAlert}
        pad="md"
        headerRight={
          <Chip variant="default" size="sm">
            {cw.loss_events.length} on record
          </Chip>
        }
      >
        {cw.loss_events.length === 0 ? (
          <div className="flex items-center gap-2">
            <CheckCircle2 size={15} className="text-pos" />
            <Body className="text-ink-soft">No losses on record for this client.</Body>
          </div>
        ) : (
          <>
            <div className="grid grid-cols-[90px_70px_110px_110px_1fr_90px] border-b border-rule pb-2 text-[10.5px] uppercase tracking-wider text-ink-mute">
              {["Date", "Line", "Incurred", "Paid", "Cause", "Status"].map((h) => (
                <span key={h}>{h}</span>
              ))}
            </div>
            {cw.loss_events.map((e, i) => (
              <div
                key={i}
                className={`grid grid-cols-[90px_70px_110px_110px_1fr_90px] items-center py-2.5 text-[13px] ${
                  i < cw.loss_events.length - 1 ? "border-b border-rule" : ""
                }`}
              >
                <Micro>{e.date ? fmtRelative(e.date) : "—"}</Micro>
                <span className="font-semibold">{e.line}</span>
                <span className="tabular-nums">{kFmt(e.incurred)}</span>
                <span className="tabular-nums">{kFmt(e.paid)}</span>
                <span className="text-[12.5px] text-ink-soft">{e.cause ?? "—"}</span>
                <Chip
                  variant={(e.status ?? "").toUpperCase() === "CLOSED" ? "pos" : "warn"}
                  size="sm"
                >
                  {e.status ? formatText(e.status, "capitalize") : "—"}
                </Chip>
              </div>
            ))}
          </>
        )}
      </Card>
    </WorkArea>
  );
}

function velocityTrend(v: number | null | undefined): string {
  if (v == null) return "—";
  if (v < -0.5) return "Improving";
  if (v > 0.5) return "Deteriorating";
  return "Stable";
}

function TrajectoryRow({
  label,
  trend,
  delta,
}: {
  label: string;
  trend: string;
  delta: number | null | undefined;
}) {
  const tone =
    delta == null
      ? "text-ink-soft"
      : delta < 0
        ? "text-pos"
        : delta > 0
          ? "text-warn"
          : "text-ink-soft";
  const Icon = delta == null || Math.abs(delta) <= 0.5 ? Minus : delta < 0 ? TrendingDown : TrendingUp;
  return (
    <div className="grid grid-cols-[1fr_auto] items-center gap-3 border-b border-rule py-2.5 last:border-b-0">
      <span className="text-[13px] font-semibold capitalize">{label}</span>
      <span className={`flex items-center gap-1.5 text-[12px] font-bold ${tone}`}>
        <Icon size={13} />
        <span className="capitalize">{trend}</span>
        {delta != null && (
          <span className="tabular-nums">
            {delta > 0 ? "+" : ""}
            {delta.toFixed(1)}
          </span>
        )}
      </span>
    </div>
  );
}

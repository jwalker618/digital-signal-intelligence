"use client";

import { CheckCircle2, ShieldAlert, SlidersHorizontal } from "lucide-react";
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

  return (
    <WorkArea>
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-6">
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
          <KpiSnug label="Events on record" value={cw.loss_events.length} />
        </Card>
      </div>

      <Card header="Modifiers" icon={SlidersHorizontal} pad="md">
        <div className="grid gap-x-8 md:grid-cols-2">
          <LabelRow label="Frequency multiplier" value={freq != null ? `${freq.toFixed(2)}x` : "—"} />
          <LabelRow label="Severity multiplier" value={sev != null ? `${sev.toFixed(2)}x` : "—"} />
          <LabelRow label="Combined modifier" value={combined != null ? `${combined.toFixed(2)}x` : "—"} />
          <LabelRow label="Propensity band" value={band ? formatText(band, "capitalize") : "—"} />
        </div>
      </Card>

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

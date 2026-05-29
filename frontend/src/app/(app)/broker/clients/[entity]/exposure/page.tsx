"use client";

import { Gauge, Layers } from "lucide-react";
import { Card } from "@/components/ui/card";
import { WorkArea } from "@/components/ui/work-area";
import { Body, Micro } from "@/components/ui/typography";
import { KpiSnug } from "@/components/ui/kpi-snug";
import { useClientWorkbench } from "../_lib/context";
import { kFmt } from "../_lib/helpers";

export default function ExposureProfilePage() {
  const cw = useClientWorkbench();
  if (!cw) return null;
  const c = cw.coverages[0];
  if (!c) {
    return (
      <WorkArea>
        <Card pad="lg">
          <Body className="italic">No coverage exposure to show.</Body>
        </Card>
      </WorkArea>
    );
  }

  const value = c.exposure_value;
  const size = c.exposure_size_score;
  const band = c.exposure_band_label;
  // Band position derived from size score (0–100) when present.
  const bandPct = size != null ? Math.max(0, Math.min(100, size)) : null;
  const prior = c.exposure_value_prior ?? null;
  const yoy =
    value != null && prior != null && prior !== 0
      ? ((value - prior) / prior) * 100
      : null;
  // Active band boundary (from endpoint) for floor/ceiling derivations.
  const activeBand = (c.exposure_bands ?? []).find((b) => b.active) ?? null;
  const floor = activeBand?.min_value ?? null;
  const ceiling = activeBand?.max_value ?? null;

  return (
    <WorkArea>
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-6">
        <Card pad="sm">
          <KpiSnug label="Exposure value" value={kFmt(value)} tone="info" />
        </Card>
        <Card pad="sm">
          <KpiSnug label="Band" value={band ?? "—"} />
        </Card>
        <Card pad="sm">
          <KpiSnug label="Size score" value={size != null ? size.toFixed(0) : "—"} />
        </Card>
        <Card pad="sm">
          <KpiSnug
            label="Complexity"
            value={c.exposure_complexity_score != null ? c.exposure_complexity_score.toFixed(0) : "—"}
          />
        </Card>
        <Card pad="sm">
          <KpiSnug
            label="Modifier"
            value={c.exposure_modifier != null ? `${c.exposure_modifier.toFixed(2)}x` : "—"}
          />
        </Card>
        <Card pad="sm">
          <KpiSnug
            label="YoY"
            value={yoy != null ? `${yoy >= 0 ? "+" : ""}${yoy.toFixed(1)}%` : "—"}
            tone={yoy != null && yoy >= 0 ? "warn" : "default"}
            delta={prior != null ? <Micro>from {kFmt(prior)}</Micro> : undefined}
          />
        </Card>
      </div>

      <div className="grid gap-3.5 lg:grid-cols-2">
        <Card header="Band position" icon={Gauge} pad="md">
          <Micro className="mb-3.5 block">
            Where {cw.entity_name} sits within the{" "}
            {band ? band.toLowerCase() : "exposure"} band.
          </Micro>
          <div className="relative h-9">
            <div className="absolute inset-x-0 top-3.5 h-2 rounded-sm border border-rule bg-surface-sunken" />
            {bandPct != null && (
              <>
                <div
                  className="absolute top-0 bottom-0 w-0.5 -translate-x-1/2 bg-info"
                  style={{ left: `${bandPct}%` }}
                />
                <div
                  className="absolute -top-5 -translate-x-1/2 whitespace-nowrap text-[11px] font-bold text-info"
                  style={{ left: `${bandPct}%` }}
                >
                  {kFmt(value)}
                </div>
              </>
            )}
          </div>
          <div className="mt-2 flex justify-between text-[11px] text-ink-mute">
            <span>{floor != null ? `${kFmt(floor)} floor` : "Small"}</span>
            <span>{ceiling != null ? `${kFmt(ceiling)} ceiling` : "Large"}</span>
          </div>
          <div className="mt-4 grid grid-cols-3 gap-3 border-t border-rule pt-3.5">
            <KpiSnug
              label="Band percentile"
              value={bandPct != null ? `${bandPct.toFixed(0)}%` : "—"}
            />
            <KpiSnug
              label="Below ceiling"
              value={value != null && ceiling != null ? kFmt(ceiling - value) : "—"}
            />
            <KpiSnug
              label="Above floor"
              value={value != null && floor != null ? kFmt(value - floor) : "—"}
            />
          </div>
        </Card>

        <Card header="Band boundaries" icon={Layers} pad="md">
          {c.exposure_bands && c.exposure_bands.length > 0 ? (
            <>
              <div className="grid grid-cols-[1fr_1.4fr_80px] border-b border-rule pb-2 text-[10.5px] uppercase tracking-wider text-ink-mute">
                {["Band", "Range", "Modifier"].map((h) => (
                  <span key={h}>{h}</span>
                ))}
              </div>
              {c.exposure_bands.map((b, i) => (
                <div
                  key={b.label}
                  className={`grid grid-cols-[1fr_1.4fr_80px] items-center py-3 text-[13px] ${
                    i < c.exposure_bands!.length - 1 ? "border-b border-rule" : ""
                  } ${b.active ? "-mx-2 rounded-md bg-info-soft px-2" : ""}`}
                >
                  <span className={b.active ? "font-bold text-info-deep dark:text-info" : "font-medium"}>
                    {b.label}
                    {b.active ? " · you" : ""}
                  </span>
                  <span className="text-[12.5px] tabular-nums text-ink-soft">
                    {b.min_value != null ? kFmt(b.min_value) : "—"} –{" "}
                    {b.max_value != null ? kFmt(b.max_value) : "—"}
                  </span>
                  <span className="font-semibold tabular-nums">
                    {b.modifier != null ? `${b.modifier.toFixed(2)}x` : "—"}
                  </span>
                </div>
              ))}
            </>
          ) : (
            <Body className="italic">Band boundary detail not available.</Body>
          )}
        </Card>
      </div>
    </WorkArea>
  );
}

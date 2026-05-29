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
          <KpiSnug label="Line" value={c.line} />
        </Card>
      </div>

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
          <span>Small</span>
          <span>Mid-market</span>
          <span>Large</span>
        </div>
      </Card>

      <Card header="Exposure detail" icon={Layers} pad="md">
        <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
          <KpiSnug label="Size score" value={size != null ? size.toFixed(0) : "—"} />
          <KpiSnug
            label="Complexity score"
            value={c.exposure_complexity_score != null ? c.exposure_complexity_score.toFixed(0) : "—"}
          />
          <KpiSnug
            label="Exposure modifier"
            value={c.exposure_modifier != null ? `${c.exposure_modifier.toFixed(2)}x` : "—"}
          />
          <KpiSnug label="Band" value={band ?? "—"} />
        </div>
      </Card>
    </WorkArea>
  );
}

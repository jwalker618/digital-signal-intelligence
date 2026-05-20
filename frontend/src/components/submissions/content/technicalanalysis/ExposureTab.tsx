"use client";

import { useEffect, useMemo } from "react";
import { useDsiStore } from "@/store/dsiStore";
import {
  Target, Activity, BarChart3, Layers, ScatterChart as ScatterIcon,
  Puzzle, Gauge, AlertTriangle, ShieldAlert
} from "lucide-react";
import { formatNumber, formatCurrency } from "@/lib/format";
import {
  KpiTile,
  InfoPanel,
} from "@/components/base/content/primatives";
import { StandardCard } from "@/components/base/cards";
import {
  PeerScatterChart,
  BenchmarkBarChart,
} from "@/components/base/charts/primatives";

export default function ExposureTab() {
  const {
    activeSubmission,
    activeVersion,
    activeQuote,
    exposureBandBenchmarks,
    exposureTierDistribution,
    exposureScatterData,
    isFetchingExposureAnalytics,
    fetchExposureAnalytics
  } = useDsiStore();

  useEffect(() => {
    if (activeSubmission?.coverage) {
      fetchExposureAnalytics(activeSubmission.coverage, 365);
    }
  }, [activeSubmission?.coverage, fetchExposureAnalytics]);

  if (!activeSubmission || !activeVersion) return null;

  const activePoint = [{
    x_magnitude: activeVersion.exposure_size_score || 0,
    y_composite: activeVersion.pure_composite_score || 0,
    name: "Current Submission"
  }];

  // Subject values for reference lines
  const subjectModifier = activeVersion.exposure_modifier || 1.0;
  const subjectMagnitude = activeVersion.exposure_size_score || 0;

  // Band boundaries for position gauge
  const bandBounds = activeVersion.exposure_band_boundaries || {};
  const bandMin = bandBounds.min_value ?? bandBounds.lower ?? null;
  const bandMax = bandBounds.max_value ?? bandBounds.upper ?? null;
  const exposureValue = activeVersion.exposure_value || 0;
  const hasBandPosition = bandMin != null && bandMax != null && bandMax > bandMin;
  const bandPct = hasBandPosition ? Math.max(0, Math.min(1, (exposureValue - bandMin) / (bandMax - bandMin))) : null;

  // Components breakdown — structured as {size: {score, band_label, modifier, weight}, complexity: {...}, combined_modifier}
  const components = activeVersion.exposure_components || {};
  const sizeComp = components.size || null;
  const complexityComp = components.complexity || null;
  const combinedModifier = components.combined_modifier;
  const hasComponents = sizeComp || complexityComp;

  // Exposure-relevant signal conditions
  // Exposure groups come from exposure_components.group_weights (moved from group_scores)
  const expGroupWeights = (activeVersion.exposure_components || {} as any).group_weights || {};
  const exposureGroupKeys = useMemo(() => {
    const keys = new Set<string>();
    for (const [key, val] of Object.entries(expGroupWeights)) {
      if ((val as number) > 0) keys.add(key);
    }
    return keys;
  }, [expGroupWeights]);

  const signalConditions = activeVersion?.signal_conditions || [];
  const queryConditions = activeVersion?.query_conditions || [];
  const allConditions = [...signalConditions, ...queryConditions];
  const exposureConditions = useMemo(() => {
    if (exposureGroupKeys.size === 0) return [];
    return allConditions.filter((c: any) => {
      if (c.source_type === 'signal_group' && exposureGroupKeys.has(c.source_id)) return true;
      if (c.group_code && exposureGroupKeys.has(c.group_code)) return true;
      return false;
    });
  }, [allConditions, exposureGroupKeys]);

  return (
    <div className="w-full no-scrollbar pb-12 pt-generate-pad"
      >
  
      {/* =======================================================================
          COMPONENT A: SUBJECT PROFILE — expanded with all exposure fields
          ======================================================================= */}
      <div className="pt-2 pb-2">
        <StandardCard title="Active Submission: Exposure Profile" lucideIcon={Target}>
        <div className="py-2">
          {/* Row 1: Primary KPIs — expanded */}
          <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-7 gap-4 pl-generate-pad pr-generate-pad">
            <KpiTile
              label="Exposure Value (TIV/Rev)"
              value={formatCurrency(activeVersion.exposure_value || 0)}
              variant="emphasis"
            />
            <KpiTile
              label="Exposure Band"
              value={(activeVersion.exposure_band_label || "N/A").toUpperCase()}
              subtext={
                hasBandPosition
                  ? `${formatCurrency(Number(bandMin))} – ${formatCurrency(Number(bandMax))}`
                  : undefined
              }
            />
            <KpiTile label="Size Score"       value={formatNumber(activeVersion.exposure_size_score, 1, "0.0")} />
            <KpiTile label="Complexity Score" value={formatNumber(activeVersion.exposure_complexity_score, 1, "N/A")} />
            <KpiTile label="Calculated Modifier" value={`${formatNumber(activeVersion.exposure_modifier, 3, "1.000")}x`} />
            <KpiTile label="Assessment Method" value={(activeVersion.exposure_assessment_method?.replace(/_/g, ' ') || "N/A").toUpperCase()} />
            <KpiTile
              label="Final Tier"
              value={`Tier ${activeVersion.final_tier || "–"}`}
              variant="emphasis"
            />
          </div>
        </div>
        </StandardCard>
      </div>

      {/* =======================================================================
          BAND POSITION & COMPONENTS ROW
          ======================================================================= */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-2 pt-2 pb-2">

        {/* BAND POSITION GAUGE */}
        <StandardCard title="Band Position" lucideIcon={Gauge}>
          <div className="py-2">
            {hasBandPosition ? (
              <div className="pl-generate-pad pr-generate-pad space-y-4">
                {/* Band bar */}
                <div>
                  <div className="flex justify-between text-xs opacity-60 mb-1">
                    <span>Band floor</span>
                    <span className="font-bold uppercase">{activeVersion.exposure_band_label}</span>
                    <span>Band ceiling</span>
                  </div>
                  <div className="relative h-6 bg-generate-background rounded-full overflow-hidden border border-generate-outline/20">
                    <div
                      className="absolute inset-y-0 left-0 bg-gradient-to-r from-generate-approve/30 via-generate-muted/30 to-generate-refer/30 rounded-full"
                      style={{ width: '100%' }}
                    />
                    {/* Position marker */}
                    <div
                      className="absolute top-0 bottom-0 w-0.5 bg-generate-selected z-10"
                      style={{ left: `${Math.max(2, Math.min(98, (bandPct || 0) * 100))}%` }}
                    >
                      <div className="absolute -top-5 left-1/2 -translate-x-1/2 text-[10px] font-bold text-generate-selected whitespace-nowrap">
                        {formatCurrency(exposureValue)}
                      </div>
                    </div>
                  </div>
                  <div className="flex justify-between text-xs mt-1 opacity-50">
                    <span>{formatCurrency(Number(bandMin))}</span>
                    <span>{formatCurrency(Number(bandMax))}</span>
                  </div>
                </div>

                {/* Position metrics */}
                <div className="grid grid-cols-3 gap-4 text-wrap">
                  <InfoPanel label="Band Percentile">
                    <span className="font-bold text-lg">{formatNumber((bandPct || 0) * 100, 0)}%</span>
                    <span className="text-xs opacity-50 block">from band floor</span>
                  </InfoPanel>
                  <InfoPanel label="Below Ceiling">
                    <span className="font-bold text-lg">{formatCurrency(bandMax - exposureValue)}</span>
                  </InfoPanel>
                  <InfoPanel label="Above Floor">
                    <span className="font-bold text-lg">{formatCurrency(exposureValue - bandMin)}</span>
                  </InfoPanel>
                </div>
              </div>
            ) : (
              <div className="flex items-center justify-center h-24 opacity-50 text-sm italic">
                Band boundary data not available.
              </div>
            )}
          </div>
        </StandardCard>

        {/* EXPOSURE COMPONENTS BREAKDOWN — structured rendering */}
        <StandardCard title="Exposure Components" lucideIcon={Puzzle}>
          <div className="overflow-y-auto">
            {hasComponents ? (
              <div className="pl-generate-pad pr-generate-pad space-y-3">
                {/* Size component */}
                {sizeComp && (
                  <InfoPanel
                    label="Size Component"
                    aside={`Weight: ${formatNumber(sizeComp.weight, 2)}`}
                  >
                    <div className="grid grid-cols-3 gap-3 text-wrap">
                      <div>
                        <span className="text-[10px] opacity-50 block">Score</span>
                        <span className="text-sm font-bold">{formatNumber(sizeComp.score, 1)}</span>
                      </div>
                      <div>
                        <span className="text-[10px] opacity-50 block">Band</span>
                        <span className="text-sm font-bold uppercase">{sizeComp.band_label || '-'}</span>
                      </div>
                      <div>
                        <span className="text-[10px] opacity-50 block">Modifier</span>
                        <span className="text-sm font-bold">{formatNumber(sizeComp.modifier, 3)}x</span>
                      </div>
                    </div>
                  </InfoPanel>
                )}

                {/* Complexity component */}
                {complexityComp && (
                  <InfoPanel
                    label="Complexity Component"
                    aside={`Weight: ${formatNumber(complexityComp.weight, 2)}`}
                  >
                    <div className="grid grid-cols-3 gap-3 text-wrap">
                      <div>
                        <span className="text-[10px] opacity-50 block">Score</span>
                        <span className="text-sm font-bold">{formatNumber(complexityComp.score, 1)}</span>
                      </div>
                      <div>
                        <span className="text-[10px] opacity-50 block">Band</span>
                        <span className="text-sm font-bold uppercase">{complexityComp.band_label || '-'}</span>
                      </div>
                      <div>
                        <span className="text-[10px] opacity-50 block">Modifier</span>
                        <span className="text-sm font-bold">{formatNumber(complexityComp.modifier, 3)}x</span>
                      </div>
                    </div>
                  </InfoPanel>
                )}

                {/* Combined modifier */}
                {combinedModifier != null && (
                  <div className="border-t border-generate-outline/20 pt-3 flex items-center justify-between">
                    <span className="text-xs opacity-60">Combined Modifier</span>
                    <span className="font-bold text-lg">{formatNumber(combinedModifier, 3)}x</span>
                  </div>
                )}
              </div>
            ) : (
              <div className="flex items-center justify-center h-24 opacity-50 text-sm italic">
                No component breakdown available.
              </div>
            )}
          </div>
        </StandardCard>

      </div>

      {isFetchingExposureAnalytics ? (
        <div className="flex flex-col items-center justify-center py-20 opacity-50 space-y-4">
          <Activity className="w-8 h-8 animate-spin" />
          <p className="text-sm tracking-widest uppercase">Calculating Benchmarks...</p>
        </div>
      ) : (
        <>
          {/* =======================================================================
              CHART ROW 1: SCATTER MATRIX (decision-colored)
              ======================================================================= */}
          <div className="pt-2 pb-2">
            <StandardCard title="Exposure Magnitude vs. Overall Risk" lucideIcon={ScatterIcon}>
              <div className="py-2">
                <PeerScatterChart
                  points={exposureScatterData.map((p: any) => ({ x: p.x_magnitude, y: p.y_composite, decision: p.decision }))}
                  subject={{
                    x: activeVersion.exposure_size_score || 0,
                    y: activeVersion.pure_composite_score || 0,
                  }}
                  xLabel="Exposure Magnitude Score (0-100)"
                  yLabel="Pure Composite Score (0-1000)"
                  xName="Magnitude Score"
                  yName="Risk Score"
                />
              </div>
            </StandardCard>
          </div>

          {/* =======================================================================
              CHART ROW 2: BAND & TIER BENCHMARKING
              ======================================================================= */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-2 pt-2 pb-2">

            {/* COMPONENT C: BAND BENCHMARKING */}
            <StandardCard title="Band Benchmarking" lucideIcon={BarChart3}>
              <div className="py-2">
                <p className="text-sm mb-4 opacity-70 text-wrap">Average Exposure Modifier across book bands. Subject modifier shown as reference line ({formatNumber(subjectModifier, 3)}x).</p>
                <BenchmarkBarChart
                  data={exposureBandBenchmarks}
                  categoryKey="band_label"
                  valueKey="avg_modifier"
                  subjectCategory={activeVersion.exposure_band_label}
                  subjectValue={subjectModifier}
                  peerCountKey="peer_count"
                  valueName="Avg Modifier"
                  emptyMessage="No band data available."
                />
              </div>
            </StandardCard>

            {/* COMPONENT D: TIER DISTRIBUTION */}
            <StandardCard title="Exposure by Final Tier" lucideIcon={Layers}>
              <div className="py-2">
                <p className="text-sm mb-4 opacity-70 text-wrap">Average Exposure Magnitude Score within each Final Tier. Subject magnitude shown as reference line ({formatNumber(subjectMagnitude, 1)}).</p>
                <BenchmarkBarChart
                  data={exposureTierDistribution}
                  categoryKey="tier"
                  valueKey="avg_magnitude"
                  subjectCategory={`Tier ${activeVersion.final_tier}`}
                  subjectValue={subjectMagnitude}
                  subjectValueDecimals={1}
                  peerCountKey="peer_count"
                  valueName="Avg Magnitude"
                  formatValue={(v) => formatNumber(v, 1)}
                  yDomain={[0, 100]}
                  emptyMessage="No tier data available."
                />
              </div>
            </StandardCard>

          </div>

          {/* =======================================================================
              EXPOSURE-RELEVANT SIGNAL CONDITIONS
              ======================================================================= */}
          {exposureConditions.length > 0 && (
            <div className="pt-2 pb-2">
              <StandardCard
                title="Exposure Signal Conditions"
                lucideIcon={AlertTriangle}
                headerRight={<span className="text-[10px] opacity-40">({exposureConditions.length})</span>}
              >
              <div className="overflow-y-auto max-h-[280px]">
                <div className="space-y-0">
                  {exposureConditions.map((cond: any, idx: number) => {
                    const actionKey = typeof cond.action === 'string' ? cond.action.toLowerCase() : (cond.action?.value || 'note');
                    const isModifier = actionKey === 'modifier';
                    const isReferral = actionKey === 'referral' || actionKey === 'refer';
                    const isTierOverride = actionKey === 'tier_override';
                    const tagColor = isModifier ? 'bg-generate-info/15 text-generate-info' :
                                     isReferral ? 'bg-generate-refer/15 text-generate-refer' :
                                     isTierOverride ? 'bg-generate-decline/15 text-generate-decline' :
                                     'bg-generate-muted/15 text-generate-muted';
                    return (
                      <div key={idx} className="flex items-center justify-between px-generate-pad py-2 border-b border-generate-outline/10 hover:bg-generate-background/20 transition-colors">
                        <div className="flex items-center gap-3 min-w-0">
                          <ShieldAlert className={`w-3.5 h-3.5 shrink-0 ${isReferral ? 'text-generate-refer' : isModifier ? 'text-generate-info' : 'text-generate-muted'}`} />
                          <div className="min-w-0">
                            <span className="text-sm block truncate">{cond.note || cond.source_name || 'Condition'}</span>
                            <span className="text-[10px] opacity-40 block">{cond.source_type}: {cond.source_id}</span>
                          </div>
                        </div>
                        <div className="flex items-center gap-2 shrink-0 ml-2">
                          <span className={`text-[10px] font-bold uppercase px-2 py-0.5 rounded ${tagColor}`}>
                            {actionKey.replace('_', ' ')}
                          </span>
                          {cond.action_value != null && typeof cond.action_value === 'number' && (
                            <span className="text-xs font-bold opacity-70 w-16 text-right">
                              {isModifier ? `${formatNumber(cond.action_value * 100, 0)}%` :
                               isTierOverride ? `→ T${cond.action_value}` :
                               cond.action_value}
                            </span>
                          )}
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
              </StandardCard>
            </div>
          )}
        </>
      )}

    </div>
  );
}

"use client";

import { useEffect, useMemo } from "react";
import { useDsiStore } from "@/store/dsiStore";
import {
  TrendingUp, TrendingDown, Activity, Target, ShieldAlert, BarChart3,
  Minus, Clock, GitBranch, Layers, AlertTriangle
} from "lucide-react";
import { StandardCard } from "@/components/base/cards";
import KeyDetailsBar from "@/components/base/keyDetailsBar";
import {
  formatNumber, formatPercent, formatCurrency
} from "@/lib/format";
import {
  KpiTile,
  ScoreBar,
} from "@/components/base/content/primatives";
import {
  PeerScatterChart,
  BenchmarkBarChart,
} from "@/components/base/charts/primatives";

export default function LossTab() {
  const {
    activeSubmission,
    activeVersion,
    activeQuote,
    lossCohortBenchmarks,
    lossTrendDistribution,
    lossScatterData,
    isFetchingLossAnalytics,
    fetchLossAnalytics
  } = useDsiStore();

  useEffect(() => {
    if (activeSubmission?.coverage) {
      fetchLossAnalytics(activeSubmission.coverage, 365);
    }
  }, [activeSubmission?.coverage, fetchLossAnalytics]);

  if (!activeSubmission || !activeVersion) return null;

  const activePoint = [{
    x_propensity: activeVersion.loss_propensity_score || 0,
    y_severity: activeVersion.severity_propensity_score || 0,
    name: "Current Submission"
  }];

  // Subject's modifier for reference line on cohort chart
  const subjectModifier = activeVersion.loss_combined_modifier || 1.0;

  // Velocity helpers
  const scoreVelocity = activeVersion.loss_score_velocity || 0;
  const freqVelocity = activeVersion.loss_frequency_velocity || 0;
  const sevVelocity = activeVersion.loss_severity_velocity || 0;
  const trendDirection = activeVersion.loss_trend_direction || 'stable';
  const freqTrend = activeVersion.loss_frequency_trend_direction || 'stable';
  const sevTrend = activeVersion.loss_severity_trend_direction || 'stable';

  // Previous scores for delta display
  const prevScore = activeVersion.loss_previous_score;
  const prevFreqScore = activeVersion.loss_previous_frequency_score;
  const prevSevScore = activeVersion.loss_previous_severity_score;

  // Group scores breakdown — each entry is {frequency_score, severity_score, confidence}
  const groupScores = activeVersion.loss_group_scores || {};
  const groupEntries = Object.entries(groupScores).sort(([, a]: any, [, b]: any) => {
    const aScore = (a?.frequency_score || 0) + (a?.severity_score || 0);
    const bScore = (b?.frequency_score || 0) + (b?.severity_score || 0);
    return bScore - aScore;
  });

  // Loss-relevant signal conditions: filter conditions whose source group is in loss_group_scores
  const lossGroupKeys = new Set(Object.keys(groupScores));
  const signalConditions = activeVersion?.signal_conditions || [];
  const queryConditions = activeVersion?.query_conditions || [];
  const allConditions = [...signalConditions, ...queryConditions];
  const lossConditions = useMemo(() => {
    if (lossGroupKeys.size === 0) return allConditions.filter((c: any) => c.action?.toLowerCase?.() === 'modifier');
    return allConditions.filter((c: any) => {
      // Group-level conditions that match a loss group
      if (c.source_type === 'signal_group' && lossGroupKeys.has(c.source_id)) return true;
      // Signal-level conditions where the group_code is in loss groups
      if (c.group_code && lossGroupKeys.has(c.group_code)) return true;
      return false;
    });
  }, [allConditions, lossGroupKeys]);

  // Compute book-wide trend totals for context line
  const trendTotal = lossTrendDistribution.reduce((acc: number, d: any) => acc + d.count, 0);
  const getTrendCount = (keyword: string) => {
    const match = lossTrendDistribution.find((d: any) => d.trend?.toLowerCase().includes(keyword));
    return match?.count || 0;
  };

  const getTrendIcon = (trend: string) => {
    const t = trend?.toLowerCase() || '';
    if (t.includes('improv')) return <TrendingDown className="w-4 h-4 text-dsi-positive" />;
    if (t.includes('deter') || t.includes('worsen')) return <TrendingUp className="w-4 h-4 text-dsi-negative" />;
    return <Minus className="w-4 h-4 opacity-50" />;
  };

  const getTrendLabel = (trend: string) => {
    const t = trend?.toLowerCase() || '';
    if (t.includes('improv')) return 'Improving';
    if (t.includes('deter') || t.includes('worsen')) return 'Deteriorating';
    return 'Stable';
  };

  const getVelocityColor = (v: number) => v > 0 ? 'text-dsi-negative' : v < 0 ? 'text-dsi-positive' : 'opacity-50';

  return (
    <div className="
      w-full no-scrollbar
      animate-in fade-in duration-500 pb-12"
      >
      <KeyDetailsBar
        status={activeQuote?.status}
        validFrom={activeQuote?.valid_from}
        validUntil={activeQuote?.valid_until}
        boundAt={activeQuote?.bound_at}
        policyNumber={activeQuote?.policy_number}
        submissionCode={activeSubmission?.submission_code}
        quoteCode={activeQuote?.quote_code}
      />

      {/* =======================================================================
          COMPONENT A: SUBJECT PROFILE — expanded with all loss fields
          ======================================================================= */}
      <div className="flex flex-col pt-2 pb-2">
        <div className="dsi-section-header overflow-x-hidden whitespace-nowrap border-collapse">
          <Target className="icon"/><span className="text-sm">Active Submission: Loss Profile</span>
        </div>
        <div className="dsi-section-analysis overflow-x-hidden whitespace-nowrap border-collapse pt-4 pb-4">
          {/* Row 1: Primary KPIs */}
          <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-8 gap-4 pl-dsi-pad pr-dsi-pad">
            <KpiTile
              label="Propensity Band"
              value={(activeVersion.loss_propensity_band?.replace(/_/g, ' ') || "N/A").toUpperCase()}
              variant="emphasis"
            />
            <KpiTile
              label="Severity Band"
              value={(activeVersion.severity_propensity_band?.replace(/_/g, ' ') || "N/A").toUpperCase()}
            />
            <KpiTile
              label="Combined Modifier"
              value={`${activeVersion.loss_combined_modifier != null ? formatNumber(activeVersion.loss_combined_modifier, 3) : "1.000"}x`}
            />
            <KpiTile
              label="Freq Multiplier"
              value={`${activeVersion.loss_frequency_multiplier != null ? formatNumber(activeVersion.loss_frequency_multiplier, 3) : "1.000"}x`}
            />
            <KpiTile
              label="Sev Multiplier"
              value={`${activeVersion.loss_severity_multiplier != null ? formatNumber(activeVersion.loss_severity_multiplier, 3) : "1.000"}x`}
            />
            <KpiTile
              label="Model Confidence"
              value={activeVersion.loss_confidence != null ? formatPercent(activeVersion.loss_confidence, 0) : "N/A"}
            />
            <KpiTile
              label="Cohort"
              value={activeVersion.loss_cohort_name || "Unknown"}
              subtext={activeVersion.loss_cohort_confidence != null ? `${formatPercent(activeVersion.loss_cohort_confidence, 0)} conf` : undefined}
            />
            <KpiTile
              label="Score Velocity"
              value={
                <span className={activeVersion.loss_score_velocity > 0 ? 'text-dsi-negative' : 'text-dsi-positive'}>
                  {activeVersion.loss_score_velocity > 0 ? '+' : ''}{activeVersion.loss_score_velocity || "0.0"}
                </span>
              }
            />
          </div>

          {/* Row 2: Meta line */}
          <div className="flex items-center gap-4 pl-dsi-pad pr-dsi-pad mt-3 pt-3 border-t border-dsi-outline/10 text-xs opacity-40">
            {activeVersion.loss_last_refresh && (
              <span className="flex items-center gap-1">
                <Clock className="w-3 h-3" />
                Last refresh: {new Date(activeVersion.loss_last_refresh).toLocaleDateString()}
              </span>
            )}
            {activeVersion.correlation_matrix_version && (
              <span className="flex items-center gap-1">
                <GitBranch className="w-3 h-3" />
                Matrix: {activeVersion.correlation_matrix_version}
              </span>
            )}
          </div>
        </div>
      </div>

      {isFetchingLossAnalytics ? (
        <div className="flex flex-col items-center justify-center py-20 opacity-50 space-y-4">
          <Activity className="w-8 h-8 animate-spin" />
          <p className="text-sm tracking-widest uppercase">Calculating Benchmarks...</p>
        </div>
      ) : (
        <>
          {/* =======================================================================
              CHART ROW 1: SCATTER & VELOCITY PANEL
              ======================================================================= */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-2 pt-2 pb-2">

            {/* COMPONENT B: SCATTER MATRIX (decision-colored) */}
            <div className="lg:col-span-2 flex flex-col">
              <div className="dsi-section-header overflow-x-hidden whitespace-nowrap border-collapse">
                <ShieldAlert className="icon"/><span className="text-sm">Frequency vs. Severity Matrix</span>
              </div>
              <div className="dsi-section-analysis overflow-x-hidden whitespace-nowrap border-collapse pt-4 pb-4">
                <PeerScatterChart
                  points={lossScatterData.map((p: any) => ({ x: p.x_propensity, y: p.y_severity, decision: p.decision }))}
                  subject={{
                    x: activeVersion.loss_propensity_score || 0,
                    y: activeVersion.severity_propensity_score || 0,
                  }}
                  xLabel="Loss Propensity Score"
                  yLabel="Severity Score"
                  xName="Frequency (Propensity)"
                  yName="Severity"
                />
              </div>
            </div>

            {/* COMPONENT D: SUBJECT VELOCITY PANEL with previous scores */}
            <div className="flex flex-col">
              <div className="dsi-section-header overflow-x-hidden whitespace-nowrap border-collapse">
                <TrendingUp className="icon"/><span className="text-sm">Loss Trajectory</span>
              </div>
              <div className="dsi-section-analysis overflow-x-hidden whitespace-nowrap border-collapse pt-4 pb-4">
                <div className="pl-dsi-pad pr-dsi-pad space-y-3">

                  {/* Overall trend */}
                  <div className="border border-dsi-outline/20 rounded-lg p-3">
                    <span className="text-xs opacity-70 block mb-2">Overall Trend</span>
                    <div className="flex items-center gap-2">
                      {getTrendIcon(trendDirection)}
                      <span className="font-bold text-lg">{getTrendLabel(trendDirection)}</span>
                    </div>
                    <div className="flex items-baseline gap-1 mt-1">
                      <span className={`font-bold text-sm ${getVelocityColor(scoreVelocity)}`}>
                        {scoreVelocity > 0 ? '+' : ''}{formatNumber(scoreVelocity, 1)}
                      </span>
                      <span className="text-xs opacity-50">pts/period</span>
                    </div>
                    {prevScore != null && (
                      <div className="text-[10px] opacity-40 mt-1">
                        Previous: {formatNumber(prevScore, 1)} → Current: {formatNumber(activeVersion.loss_propensity_score, 1)}
                      </div>
                    )}
                  </div>

                  {/* Frequency breakdown */}
                  <div className="border border-dsi-outline/20 rounded-lg p-3">
                    <span className="text-xs opacity-70 block mb-2">Frequency Component</span>
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        {getTrendIcon(freqTrend)}
                        <span className="font-bold">{getTrendLabel(freqTrend)}</span>
                      </div>
                      <span className={`font-bold text-sm ${getVelocityColor(freqVelocity)}`}>
                        {freqVelocity > 0 ? '+' : ''}{formatNumber(freqVelocity, 1)}
                      </span>
                    </div>
                    {prevFreqScore != null && (
                      <div className="text-[10px] opacity-40 mt-1">
                        Previous: {formatNumber(prevFreqScore, 1)} → Current: {formatNumber(activeVersion.loss_propensity_score, 1)}
                      </div>
                    )}
                  </div>

                  {/* Severity breakdown */}
                  <div className="border border-dsi-outline/20 rounded-lg p-3">
                    <span className="text-xs opacity-70 block mb-2">Severity Component</span>
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        {getTrendIcon(sevTrend)}
                        <span className="font-bold">{getTrendLabel(sevTrend)}</span>
                      </div>
                      <span className={`font-bold text-sm ${getVelocityColor(sevVelocity)}`}>
                        {sevVelocity > 0 ? '+' : ''}{formatNumber(sevVelocity, 1)}
                      </span>
                    </div>
                    {prevSevScore != null && (
                      <div className="text-[10px] opacity-40 mt-1">
                        Previous: {formatNumber(prevSevScore, 1)} → Current: {formatNumber(activeVersion.severity_propensity_score, 1)}
                      </div>
                    )}
                  </div>

                  {/* Book-wide context */}
                  {trendTotal > 0 && (
                    <div className="border-t border-dsi-outline/20 pt-3">
                      <span className="text-xs opacity-70 block mb-2">Book-wide Trend ({trendTotal} peers)</span>
                      <div className="flex gap-3 text-xs">
                        <span className="flex items-center gap-1">
                          <span className="inline-block w-2 h-2 rounded-full bg-dsi-approve"></span>
                          {getTrendCount('improv')} improving
                        </span>
                        <span className="flex items-center gap-1">
                          <span className="inline-block w-2 h-2 rounded-full bg-dsi-muted"></span>
                          {getTrendCount('stable')} stable
                        </span>
                        <span className="flex items-center gap-1">
                          <span className="inline-block w-2 h-2 rounded-full bg-dsi-decline"></span>
                          {getTrendCount('deter')} deteriorating
                        </span>
                      </div>
                    </div>
                  )}

                </div>
              </div>
            </div>

          </div>

          {/* =======================================================================
              CHART ROW 2: COHORT BENCHMARKING + GROUP SCORES
              ======================================================================= */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-2 pt-2 pb-2">

            {/* COHORT BENCHMARKING (2/3 width) */}
            <div className="lg:col-span-2 flex flex-col">
              <div className="dsi-section-header overflow-x-hidden whitespace-nowrap border-collapse">
                <BarChart3 className="icon"/><span className="text-sm">Cohort Benchmarking</span>
              </div>
              <div className="dsi-section-analysis overflow-x-hidden whitespace-nowrap border-collapse pt-4 pb-4">
                <p className="pl-dsi-pad pr-dsi-pad text-sm mb-4 opacity-70 text-wrap">Average Combined Loss Modifier across all cohorts. Subject modifier shown as reference line ({formatNumber(subjectModifier, 3)}x).</p>
                <BenchmarkBarChart
                  data={lossCohortBenchmarks}
                  categoryKey="cohort_name"
                  valueKey="avg_modifier"
                  subjectCategory={activeVersion.loss_cohort_name}
                  subjectValue={subjectModifier}
                  peerCountKey="peer_count"
                  valueName="Avg Modifier"
                  emptyMessage="No cohort data available."
                />
              </div>
            </div>

            {/* LOSS GROUP SCORES BREAKDOWN (1/3 width) */}
            <div className="flex flex-col">
              <div className="dsi-section-header overflow-x-hidden whitespace-nowrap border-collapse">
                <Layers className="icon"/><span className="text-sm">Loss Group Scores</span>
              </div>
              <div className="dsi-section-analysis overflow-y-auto border-collapse no-scrollbar max-h-[400px]">
                {groupEntries.length > 0 ? (
                  <div className="space-y-0">
                    {groupEntries.map(([group, detail]: [string, any]) => {
                      const freqScore = detail?.frequency_score ?? 0;
                      const sevScore = detail?.severity_score ?? 0;
                      const confidence = detail?.confidence;
                      return (
                        <div key={group} className="px-dsi-pad py-2.5 border-b border-dsi-outline/10 hover:bg-dsi-background/20 transition-colors">
                          <div className="flex items-center justify-between mb-1.5">
                            <span className="text-xs font-semibold truncate max-w-[140px]" title={group}>{group}</span>
                            {confidence != null && (
                              <span className="text-[10px] opacity-40 ml-1">{formatPercent(confidence, 0)} conf</span>
                            )}
                          </div>
                          <div className="mb-1">
                            <ScoreBar label="Freq" value={freqScore} />
                          </div>
                          <ScoreBar label="Sev" value={sevScore} />
                        </div>
                      );
                    })}
                  </div>
                ) : (
                  <div className="flex items-center justify-center h-24 opacity-50 text-sm italic">
                    No group scores available.
                  </div>
                )}
              </div>
            </div>

          </div>

          {/* =======================================================================
              LOSS-RELEVANT SIGNAL CONDITIONS
              ======================================================================= */}
          {lossConditions.length > 0 && (
            <div className="flex flex-col pt-2 pb-2">
              <div className="dsi-section-header overflow-x-hidden whitespace-nowrap border-collapse">
                <AlertTriangle className="icon"/>
                <span className="text-sm">Loss Signal Conditions ({lossConditions.length})</span>
              </div>
              <div className="dsi-section-analysis overflow-y-auto border-collapse max-h-[280px]">
                <div className="space-y-0">
                  {lossConditions.map((cond: any, idx: number) => {
                    const actionKey = typeof cond.action === 'string' ? cond.action.toLowerCase() : (cond.action?.value || 'note');
                    const isModifier = actionKey === 'modifier';
                    const isReferral = actionKey === 'referral' || actionKey === 'refer';
                    const isTierOverride = actionKey === 'tier_override';
                    const tagColor = isModifier ? 'bg-dsi-info/15 text-dsi-info' :
                                     isReferral ? 'bg-dsi-warning/15 text-dsi-warning' :
                                     isTierOverride ? 'bg-dsi-negative/10 text-dsi-negative' :
                                     'bg-dsi-muted/15 text-dsi-muted';
                    return (
                      <div key={idx} className="flex items-center justify-between px-dsi-pad py-2 border-b border-dsi-outline/10 hover:bg-dsi-background/20 transition-colors">
                        <div className="flex items-center gap-3 min-w-0">
                          <ShieldAlert className={`w-3.5 h-3.5 shrink-0 ${isReferral ? 'text-dsi-warning' : isModifier ? 'text-dsi-info' : 'text-dsi-muted'}`} />
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
                              {isModifier ? formatPercent(cond.action_value, 0) :
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
            </div>
          )}
        </>
      )}

    </div>
  );
}

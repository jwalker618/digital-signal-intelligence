"use client";

import { useEffect, useMemo } from "react";
import { useDsiStore } from "@/store/dsiStore";
import {
  TrendingUp, TrendingDown, Activity, Target, ShieldAlert, BarChart3,
  Paperclip, Minus, Clock, GitBranch, Layers, AlertTriangle
} from "lucide-react";
import {
  ScatterChart, Scatter, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, ResponsiveContainer,
  BarChart, Bar, Cell, ReferenceLine, Label
} from "recharts";

const DECISION_COLORS: Record<string, string> = {
  approve: '#10b981',
  refer: '#f59e0b',
  decline: '#f43f5e',
};

const getDecisionColor = (decision: string | undefined) => {
  if (!decision) return '#475569';
  return DECISION_COLORS[decision.toLowerCase()] || '#475569';
};

const formatNum = (num: number | null | undefined, decimals = 1) =>
  num !== null && num !== undefined ? Number(num).toFixed(decimals) : "-";

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

  const tooltipStyle = {
    backgroundColor: '#0f172a',
    borderColor: '#334155',
    color: '#f8fafc',
    borderRadius: '8px',
    fontSize: '12px'
  };

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
    if (t.includes('improv')) return <TrendingDown className="w-4 h-4 text-emerald-400" />;
    if (t.includes('deter') || t.includes('worsen')) return <TrendingUp className="w-4 h-4 text-rose-400" />;
    return <Minus className="w-4 h-4 opacity-50" />;
  };

  const getTrendLabel = (trend: string) => {
    const t = trend?.toLowerCase() || '';
    if (t.includes('improv')) return 'Improving';
    if (t.includes('deter') || t.includes('worsen')) return 'Deteriorating';
    return 'Stable';
  };

  const getVelocityColor = (v: number) => v > 0 ? 'text-rose-400' : v < 0 ? 'text-emerald-400' : 'opacity-50';

  return (
    <div className="
      w-full no-scrollbar
      animate-in fade-in duration-500 pb-12"
      >
      {/* STICKY WRAPPER */}
      <div className="
        sticky top-0 z-20
        bg-dsi-background
        pt-3 pb-2"
        >

        {/* SECTION HEADER */}
        <div className="
          flex gap-dsi-pad
          rounded-t-xl
          border-b-1 border-dsi-outline/50
          overflow-x-hidden whitespace-nowrap border-collapse
          bg-dsi-analysis/60
          pl-dsi-pad
          pt-2 pb-2
        "
        >
          <Paperclip className="icon"/><span className="text-sm">Key Details</span>
        </div>

        {/* KEY INFORMATION CARD */}
        <div className="
          grid grid-cols-[10%_35%_55%] grid-rows-1
          border-b-3 border-dsi-contrast-background
          overflow-x-hidden whitespace-nowrap border-collapse
          rounded-b-xl
          bg-dsi-analysis shadow-sm
          pt-2 pb-2"
        >
          <div className="text-left pl-dsi-pad pr-dsi-pad border-r-1 border-dsi-outline/50 overflow-x-hidden">
            <span className="text-sm">Status:</span><span className="pl-2 uppercase font-bold">{activeQuote.status}</span>
          </div>

          <div className="text-center pl-dsi-pad pr-dsi-pad border-r-1 border-dsi-outline/50 overflow-x-hidden">
            {(activeQuote.status === 'draft' || activeQuote.status === 'ready') && (
              <span className="">
                <span className="text-sm">Quote Valid From:</span><span className="pl-2 uppercase font-bold">{new Date(activeQuote.valid_from).toLocaleDateString()};</span>
                <span className="pl-2 pr-2"> </span>
                <span className="text-sm">Until:</span><span className="pl-2 uppercase font-bold">{new Date(activeQuote.valid_until).toLocaleDateString()}</span>
              </span>
            )}
            {activeQuote.status === 'bound' && (
              <span className="">
                  <span className="text-sm">Bound Date:</span><span className="pl-2 uppercase font-bold">{activeQuote.bound_at ? new Date(activeQuote.bound_at).toLocaleDateString() : 'N/A'}</span>
                  <span className="text-sm">Policy Reference:</span><span className="pl-2 uppercase font-bold">{activeQuote.policy_number || 'Pending'}</span>
              </span>
            )}
          </div>

          <div className="text-center pl-dsi-pad pr-dsi-pad overflow-x-hidden">
            <span className="text-sm">Submission Code: </span><span className="pl-2 uppercase font-bold">{activeSubmission.submission_code}</span>
            <span className="pl-6 pr-6">||</span>
            <span className="text-sm">Quote Code: </span><span className="pl-2 uppercase font-bold">{activeQuote.quote_code}</span>
          </div>

        </div>
      </div>

      {/* =======================================================================
          COMPONENT A: SUBJECT PROFILE — expanded with all loss fields
          ======================================================================= */}
      <div className="flex flex-col pt-2 pb-2">
        <div className="
          flex gap-dsi-pad
          rounded-t-xl
          border-b-1 border-dsi-outline/50
          overflow-x-hidden whitespace-nowrap border-collapse
          bg-dsi-analysis/60
          pl-dsi-pad
          pt-2 pb-2
        ">
          <Target className="icon"/><span className="text-sm">Active Submission: Loss Profile</span>
        </div>
        <div className="
          flex flex-col flex-1
          border-b-3 border-dsi-contrast-background
          overflow-x-hidden whitespace-nowrap border-collapse
          rounded-b-xl
          bg-dsi-analysis shadow-sm
          pt-4 pb-4
        ">
          {/* Row 1: Primary KPIs */}
          <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-8 gap-4 pl-dsi-pad pr-dsi-pad">
            <div>
              <span className="opacity-70 block text-xs mb-1">Propensity Band</span>
              <span className="font-bold text-lg text-dsi-selected uppercase">
                {activeVersion.loss_propensity_band?.replace(/_/g, ' ') || "N/A"}
              </span>
            </div>
            <div>
              <span className="opacity-70 block text-xs mb-1">Severity Band</span>
              <span className="font-bold text-lg uppercase">
                {activeVersion.severity_propensity_band?.replace(/_/g, ' ') || "N/A"}
              </span>
            </div>
            <div>
              <span className="opacity-70 block text-xs mb-1">Combined Modifier</span>
              <span className="font-bold text-lg">
                {activeVersion.loss_combined_modifier?.toFixed(3) || "1.000"}x
              </span>
            </div>
            <div>
              <span className="opacity-70 block text-xs mb-1">Freq Multiplier</span>
              <span className="font-bold text-lg">
                {activeVersion.loss_frequency_multiplier?.toFixed(3) || "1.000"}x
              </span>
            </div>
            <div>
              <span className="opacity-70 block text-xs mb-1">Sev Multiplier</span>
              <span className="font-bold text-lg">
                {activeVersion.loss_severity_multiplier?.toFixed(3) || "1.000"}x
              </span>
            </div>
            <div>
              <span className="opacity-70 block text-xs mb-1">Model Confidence</span>
              <span className="font-bold text-lg">
                {activeVersion.loss_confidence != null ? `${(activeVersion.loss_confidence * 100).toFixed(0)}%` : "N/A"}
              </span>
            </div>
            <div>
              <span className="opacity-70 block text-xs mb-1">Cohort</span>
              <span className="font-bold text-sm leading-tight block">
                {activeVersion.loss_cohort_name || "Unknown"}
              </span>
              <span className="text-[10px] opacity-40">
                {activeVersion.loss_cohort_confidence != null ? `${(activeVersion.loss_cohort_confidence * 100).toFixed(0)}% conf` : ''}
              </span>
            </div>
            <div>
              <span className="opacity-70 block text-xs mb-1">Score Velocity</span>
              <span className={`font-bold text-lg ${activeVersion.loss_score_velocity > 0 ? 'text-rose-400' : 'text-emerald-400'}`}>
                {activeVersion.loss_score_velocity > 0 ? '+' : ''}{activeVersion.loss_score_velocity || "0.0"}
              </span>
            </div>
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
              <div className="
                flex gap-dsi-pad
                rounded-t-xl
                border-b-1 border-dsi-outline/50
                overflow-x-hidden whitespace-nowrap border-collapse
                bg-dsi-analysis/60
                pl-dsi-pad
                pt-2 pb-2
              ">
                <ShieldAlert className="icon"/><span className="text-sm">Frequency vs. Severity Matrix</span>
              </div>
              <div className="
                flex flex-col flex-1
                border-b-3 border-dsi-contrast-background
                overflow-x-hidden whitespace-nowrap border-collapse
                rounded-b-xl
                bg-dsi-analysis shadow-sm
                pt-4 pb-4
              ">
                <div className="pl-dsi-pad pr-dsi-pad flex gap-4 mb-2 text-[10px] uppercase tracking-wider">
                  <span className="flex items-center gap-1"><span className="inline-block w-2 h-2 rounded-full bg-emerald-500"></span> Approve</span>
                  <span className="flex items-center gap-1"><span className="inline-block w-2 h-2 rounded-full bg-amber-500"></span> Refer</span>
                  <span className="flex items-center gap-1"><span className="inline-block w-2 h-2 rounded-full bg-rose-500"></span> Decline</span>
                  <span className="flex items-center gap-1"><span className="inline-block w-2 h-2 rounded-full bg-slate-500"></span> Unknown</span>
                </div>
                <div className="pl-dsi-pad pr-dsi-pad h-[400px] w-full relative">
                  <ResponsiveContainer width="100%" height="100%">
                    <ScatterChart margin={{ top: 10, right: 30, bottom: 20, left: 0 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#334155" opacity={0.5} />
                      <XAxis
                        type="number"
                        dataKey="x_propensity"
                        name="Frequency (Propensity)"
                        stroke="#94a3b8"
                        tick={{ fill: '#94a3b8', fontSize: 12 }}
                        label={{ value: 'Loss Propensity Score', position: 'insideBottom', offset: -15, fill: '#94a3b8', fontSize: 12 }}
                      />
                      <YAxis
                        type="number"
                        dataKey="y_severity"
                        name="Severity"
                        stroke="#94a3b8"
                        tick={{ fill: '#94a3b8', fontSize: 12 }}
                        label={{ value: 'Severity Score', angle: -90, position: 'insideLeft', fill: '#94a3b8', fontSize: 12 }}
                      />
                      <RechartsTooltip
                        cursor={{ strokeDasharray: '3 3' }}
                        contentStyle={tooltipStyle}
                        formatter={(value: any, name: string) => [Number(value).toFixed(1), name]}
                      />
                      {/* Subject crosshair reference lines */}
                      <ReferenceLine
                        x={activeVersion.loss_propensity_score || 0}
                        stroke="#3b82f6"
                        strokeDasharray="4 4"
                        strokeOpacity={0.6}
                      />
                      <ReferenceLine
                        y={activeVersion.severity_propensity_score || 0}
                        stroke="#3b82f6"
                        strokeDasharray="4 4"
                        strokeOpacity={0.6}
                      />
                      {/* Peer dots colored by decision */}
                      {lossScatterData.map((point: any, idx: number) => (
                        <Scatter
                          key={`peer-${idx}`}
                          data={[point]}
                          fill={getDecisionColor(point.decision)}
                          fillOpacity={0.5}
                          isAnimationActive={false}
                        />
                      ))}
                      <Scatter name="Active Submission" data={activePoint} fill="#3b82f6" shape="star" />
                    </ScatterChart>
                  </ResponsiveContainer>
                </div>
              </div>
            </div>

            {/* COMPONENT D: SUBJECT VELOCITY PANEL with previous scores */}
            <div className="flex flex-col">
              <div className="
                flex gap-dsi-pad
                rounded-t-xl
                border-b-1 border-dsi-outline/50
                overflow-x-hidden whitespace-nowrap border-collapse
                bg-dsi-analysis/60
                pl-dsi-pad
                pt-2 pb-2
              ">
                <TrendingUp className="icon"/><span className="text-sm">Loss Trajectory</span>
              </div>
              <div className="
                flex flex-col flex-1
                border-b-3 border-dsi-contrast-background
                overflow-x-hidden whitespace-nowrap border-collapse
                rounded-b-xl
                bg-dsi-analysis shadow-sm
                pt-4 pb-4
              ">
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
                        {scoreVelocity > 0 ? '+' : ''}{scoreVelocity.toFixed(1)}
                      </span>
                      <span className="text-xs opacity-50">pts/period</span>
                    </div>
                    {prevScore != null && (
                      <div className="text-[10px] opacity-40 mt-1">
                        Previous: {formatNum(prevScore, 1)} → Current: {formatNum(activeVersion.loss_propensity_score, 1)}
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
                        {freqVelocity > 0 ? '+' : ''}{freqVelocity.toFixed(1)}
                      </span>
                    </div>
                    {prevFreqScore != null && (
                      <div className="text-[10px] opacity-40 mt-1">
                        Previous: {formatNum(prevFreqScore, 1)} → Current: {formatNum(activeVersion.loss_propensity_score, 1)}
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
                        {sevVelocity > 0 ? '+' : ''}{sevVelocity.toFixed(1)}
                      </span>
                    </div>
                    {prevSevScore != null && (
                      <div className="text-[10px] opacity-40 mt-1">
                        Previous: {formatNum(prevSevScore, 1)} → Current: {formatNum(activeVersion.severity_propensity_score, 1)}
                      </div>
                    )}
                  </div>

                  {/* Book-wide context */}
                  {trendTotal > 0 && (
                    <div className="border-t border-dsi-outline/20 pt-3">
                      <span className="text-xs opacity-70 block mb-2">Book-wide Trend ({trendTotal} peers)</span>
                      <div className="flex gap-3 text-xs">
                        <span className="flex items-center gap-1">
                          <span className="inline-block w-2 h-2 rounded-full bg-emerald-500"></span>
                          {getTrendCount('improv')} improving
                        </span>
                        <span className="flex items-center gap-1">
                          <span className="inline-block w-2 h-2 rounded-full bg-slate-500"></span>
                          {getTrendCount('stable')} stable
                        </span>
                        <span className="flex items-center gap-1">
                          <span className="inline-block w-2 h-2 rounded-full bg-rose-500"></span>
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
              <div className="
                flex gap-dsi-pad
                rounded-t-xl
                border-b-1 border-dsi-outline/50
                overflow-x-hidden whitespace-nowrap border-collapse
                bg-dsi-analysis/60
                pl-dsi-pad
                pt-2 pb-2
              ">
                <BarChart3 className="icon"/><span className="text-sm">Cohort Benchmarking</span>
              </div>
              <div className="
                flex flex-col flex-1
                border-b-3 border-dsi-contrast-background
                overflow-x-hidden whitespace-nowrap border-collapse
                rounded-b-xl
                bg-dsi-analysis shadow-sm
                pt-4 pb-4
              ">
                <p className="pl-dsi-pad pr-dsi-pad text-sm mb-4 opacity-70 text-wrap">Average Combined Loss Modifier across all cohorts. Subject modifier shown as reference line ({subjectModifier.toFixed(3)}x).</p>
                <div className="pl-dsi-pad pr-dsi-pad h-[300px] w-full">
                  {lossCohortBenchmarks.length > 0 ? (
                    <ResponsiveContainer width="100%" height="100%">
                      <BarChart data={lossCohortBenchmarks} margin={{ top: 0, right: 0, bottom: 20, left: -20 }}>
                        <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#334155" opacity={0.5} />
                        <XAxis
                          dataKey="cohort_name"
                          stroke="#94a3b8"
                          tick={{ fill: '#94a3b8', fontSize: 11 }}
                          interval={0}
                          tickFormatter={(val) => val.length > 15 ? val.substring(0, 15) + '...' : val}
                        />
                        <YAxis
                          stroke="#94a3b8"
                          tick={{ fill: '#94a3b8', fontSize: 12 }}
                          domain={['auto', 'auto']}
                        />
                        <RechartsTooltip
                          contentStyle={tooltipStyle}
                          cursor={{ fill: '#1e293b', opacity: 0.4 }}
                          formatter={(value: any, name: string) => {
                            if (name === 'avg_modifier') return [`${Number(value).toFixed(3)}x`, 'Avg Modifier'];
                            return [value, name];
                          }}
                          labelFormatter={(label) => {
                            const match = lossCohortBenchmarks.find((d: any) => d.cohort_name === label);
                            return match ? `${label} (n=${match.peer_count})` : label;
                          }}
                        />
                        {/* Subject modifier reference line */}
                        <ReferenceLine
                          y={subjectModifier}
                          stroke="#3b82f6"
                          strokeDasharray="6 3"
                          strokeWidth={2}
                        >
                          <Label value={`Subject ${subjectModifier.toFixed(3)}x`} position="right" fill="#3b82f6" fontSize={11} />
                        </ReferenceLine>
                        <Bar dataKey="avg_modifier" radius={[4, 4, 0, 0]}
                          label={({ x, y, width, index }: any) => {
                            const entry = lossCohortBenchmarks[index];
                            return (
                              <text x={x + width / 2} y={y - 6} textAnchor="middle" fill="#94a3b8" fontSize={10}>
                                n={entry?.peer_count}
                              </text>
                            );
                          }}
                        >
                          {lossCohortBenchmarks.map((entry: any, index: number) => (
                            <Cell
                              key={`cell-${index}`}
                              fill={entry.cohort_name === activeVersion.loss_cohort_name ? '#3b82f6' : '#475569'}
                            />
                          ))}
                        </Bar>
                      </BarChart>
                    </ResponsiveContainer>
                  ) : (
                    <div className="flex h-full items-center justify-center opacity-50 italic text-sm">No cohort data available.</div>
                  )}
                </div>
              </div>
            </div>

            {/* LOSS GROUP SCORES BREAKDOWN (1/3 width) */}
            <div className="flex flex-col">
              <div className="
                flex gap-dsi-pad
                rounded-t-xl
                border-b-1 border-dsi-outline/50
                overflow-x-hidden whitespace-nowrap border-collapse
                bg-dsi-analysis/60
                pl-dsi-pad
                pt-2 pb-2
              ">
                <Layers className="icon"/><span className="text-sm">Loss Group Scores</span>
              </div>
              <div className="
                flex flex-col flex-1
                border-b-3 border-dsi-contrast-background
                overflow-y-auto border-collapse
                rounded-b-xl
                bg-dsi-analysis shadow-sm
                pt-2 pb-2
                max-h-[400px]
              ">
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
                              <span className="text-[10px] opacity-40 ml-1">{(confidence * 100).toFixed(0)}% conf</span>
                            )}
                          </div>
                          {/* Frequency bar */}
                          <div className="flex items-center gap-2 mb-1">
                            <span className="text-[10px] opacity-50 w-10 shrink-0">Freq</span>
                            <div className="flex-1 h-1.5 bg-dsi-background rounded-full overflow-hidden">
                              <div
                                className="h-full rounded-full transition-all"
                                style={{
                                  width: `${Math.min(100, Math.max(2, freqScore))}%`,
                                  backgroundColor: freqScore > 70 ? '#f43f5e' : freqScore > 40 ? '#f59e0b' : '#10b981'
                                }}
                              />
                            </div>
                            <span className="text-[10px] font-bold w-8 text-right">{formatNum(freqScore, 1)}</span>
                          </div>
                          {/* Severity bar */}
                          <div className="flex items-center gap-2">
                            <span className="text-[10px] opacity-50 w-10 shrink-0">Sev</span>
                            <div className="flex-1 h-1.5 bg-dsi-background rounded-full overflow-hidden">
                              <div
                                className="h-full rounded-full transition-all"
                                style={{
                                  width: `${Math.min(100, Math.max(2, sevScore))}%`,
                                  backgroundColor: sevScore > 70 ? '#f43f5e' : sevScore > 40 ? '#f59e0b' : '#10b981'
                                }}
                              />
                            </div>
                            <span className="text-[10px] font-bold w-8 text-right">{formatNum(sevScore, 1)}</span>
                          </div>
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
              <div className="
                flex gap-dsi-pad
                rounded-t-xl
                border-b-1 border-dsi-outline/50
                overflow-x-hidden whitespace-nowrap border-collapse
                bg-dsi-analysis/60
                pl-dsi-pad
                pt-2 pb-2
              ">
                <AlertTriangle className="icon"/>
                <span className="text-sm">Loss Signal Conditions ({lossConditions.length})</span>
              </div>
              <div className="
                flex flex-col flex-1
                border-b-3 border-dsi-contrast-background
                overflow-y-auto border-collapse
                rounded-b-xl
                bg-dsi-analysis shadow-sm
                pt-2 pb-2
                max-h-[280px]
              ">
                <div className="space-y-0">
                  {lossConditions.map((cond: any, idx: number) => {
                    const actionKey = typeof cond.action === 'string' ? cond.action.toLowerCase() : (cond.action?.value || 'note');
                    const isModifier = actionKey === 'modifier';
                    const isReferral = actionKey === 'referral' || actionKey === 'refer';
                    const isTierOverride = actionKey === 'tier_override';
                    const tagColor = isModifier ? 'bg-blue-500/15 text-blue-400' :
                                     isReferral ? 'bg-amber-500/15 text-amber-400' :
                                     isTierOverride ? 'bg-rose-500/15 text-rose-400' :
                                     'bg-slate-500/15 text-slate-400';
                    return (
                      <div key={idx} className="flex items-center justify-between px-dsi-pad py-2 border-b border-dsi-outline/10 hover:bg-dsi-background/20 transition-colors">
                        <div className="flex items-center gap-3 min-w-0">
                          <ShieldAlert className={`w-3.5 h-3.5 shrink-0 ${isReferral ? 'text-amber-400' : isModifier ? 'text-blue-400' : 'text-slate-400'}`} />
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
                              {isModifier ? `${(cond.action_value * 100).toFixed(0)}%` :
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

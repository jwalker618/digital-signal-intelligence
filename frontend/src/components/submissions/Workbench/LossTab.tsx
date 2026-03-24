"use client";

import { useEffect } from "react";
import { useDsiStore } from "@/store/dsiStore";
import { TrendingUp, TrendingDown, Activity, Target, ShieldAlert, BarChart3, Paperclip, Minus } from "lucide-react";
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
          COMPONENT A: SUBJECT PROFILE
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
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-6 pl-dsi-pad pr-dsi-pad">
            <div>
              <span className="opacity-70 block text-xs mb-1">Propensity Band</span>
              <span className="font-bold text-lg text-dsi-selected uppercase">
                {activeVersion.loss_propensity_band?.replace(/_/g, ' ') || "N/A"}
              </span>
            </div>
            <div>
              <span className="opacity-70 block text-xs mb-1">Combined Modifier</span>
              <span className="font-bold text-lg">
                {activeVersion.loss_combined_modifier?.toFixed(3) || "1.000"}x
              </span>
            </div>
            <div>
              <span className="opacity-70 block text-xs mb-1">Severity Score</span>
              <span className="font-bold text-lg">
                {activeVersion.severity_propensity_score?.toFixed(1) || "0.0"}
              </span>
            </div>
            <div>
              <span className="opacity-70 block text-xs mb-1">Score Velocity</span>
              <span className={`font-bold text-lg ${activeVersion.loss_score_velocity > 0 ? 'text-rose-400' : 'text-emerald-400'}`}>
                {activeVersion.loss_score_velocity > 0 ? '+' : ''}{activeVersion.loss_score_velocity || "0.0"}
              </span>
            </div>
            <div>
              <span className="opacity-70 block text-xs mb-1">Cohort Assignment</span>
              <span className="font-bold text-sm leading-tight block">
                {activeVersion.loss_cohort_name || "Unknown"}
              </span>
            </div>
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

            {/* COMPONENT D: SUBJECT VELOCITY PANEL (replaces pie chart) */}
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
                <div className="pl-dsi-pad pr-dsi-pad space-y-4">

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
                  </div>

                  {/* Book-wide context */}
                  {trendTotal > 0 && (
                    <div className="border-t border-dsi-outline/20 pt-3 mt-3">
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
              CHART ROW 2: COHORT BENCHMARKING
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
        </>
      )}

    </div>
  );
}

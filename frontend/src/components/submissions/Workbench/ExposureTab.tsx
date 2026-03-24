"use client";

import { useEffect } from "react";
import { useDsiStore } from "@/store/dsiStore";
import { Target, Activity, BarChart3, Layers, ScatterChart as ScatterIcon, Paperclip } from "lucide-react";
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

  const tooltipStyle = {
    backgroundColor: '#0f172a',
    borderColor: '#334155',
    color: '#f8fafc',
    borderRadius: '8px',
    fontSize: '12px'
  };

  // Subject values for reference lines
  const subjectModifier = activeVersion.exposure_modifier || 1.0;
  const subjectMagnitude = activeVersion.exposure_size_score || 0;

  return (
    <div className="
      w-full no-scrollbar
      animate-in fade-in duration-500 pb-12"
      >
      {/* STICKY WRAPPER: Acts as a solid curtain to hide scrolling content */}
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
          COMPONENT A: SUBJECT PROFILE (HERO KPIs)
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
          <Target className="icon"/><span className="text-sm">Active Submission: Exposure Profile</span>
        </div>
        <div className="
          flex flex-col flex-1
          border-b-3 border-dsi-contrast-background
          overflow-x-hidden whitespace-nowrap border-collapse
          rounded-b-xl
          bg-dsi-analysis shadow-sm
          pt-4 pb-4
        ">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-6 pl-dsi-pad pr-dsi-pad">
            <div>
              <span className="opacity-70 block text-xs mb-1">Exposure Value (TIV/Rev)</span>
              <span className="font-bold text-lg text-dsi-selected">
                ${(activeVersion.exposure_value || 0).toLocaleString()}
              </span>
            </div>
            <div>
              <span className="opacity-70 block text-xs mb-1">Exposure Band</span>
              <span className="font-bold text-lg uppercase">
                {activeVersion.exposure_band_label || "N/A"}
              </span>
            </div>
            <div>
              <span className="opacity-70 block text-xs mb-1">Magnitude Score</span>
              <span className="font-bold text-lg">
                {activeVersion.exposure_size_score?.toFixed(1) || "0.0"}
              </span>
            </div>
            <div>
              <span className="opacity-70 block text-xs mb-1">Calculated Modifier</span>
              <span className="font-bold text-lg">
                {activeVersion.exposure_modifier?.toFixed(3) || "1.000"}x
              </span>
            </div>
          </div>
        </div>
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
              <ScatterIcon className="icon"/><span className="text-sm">Exposure Magnitude vs. Overall Risk</span>
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
                      dataKey="x_magnitude"
                      name="Magnitude Score"
                      stroke="#94a3b8"
                      tick={{ fill: '#94a3b8', fontSize: 12 }}
                      label={{ value: 'Exposure Magnitude Score (0-100)', position: 'insideBottom', offset: -15, fill: '#94a3b8', fontSize: 12 }}
                    />
                    <YAxis
                      type="number"
                      dataKey="y_composite"
                      name="Risk Score"
                      stroke="#94a3b8"
                      tick={{ fill: '#94a3b8', fontSize: 12 }}
                      label={{ value: 'Pure Composite Score (0-1000)', angle: -90, position: 'insideLeft', fill: '#94a3b8', fontSize: 12 }}
                    />
                    <RechartsTooltip
                      cursor={{ strokeDasharray: '3 3' }}
                      contentStyle={tooltipStyle}
                      formatter={(value: any, name: string) => [Number(value).toFixed(1), name]}
                    />
                    {/* Subject crosshair reference lines */}
                    <ReferenceLine
                      x={activeVersion.exposure_size_score || 0}
                      stroke="#3b82f6"
                      strokeDasharray="4 4"
                      strokeOpacity={0.6}
                    />
                    <ReferenceLine
                      y={activeVersion.pure_composite_score || 0}
                      stroke="#3b82f6"
                      strokeDasharray="4 4"
                      strokeOpacity={0.6}
                    />
                    {/* Peer dots colored by decision */}
                    {exposureScatterData.map((point: any, idx: number) => (
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

          {/* =======================================================================
              CHART ROW 2: BAND & TIER BENCHMARKING
              ======================================================================= */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-2 pt-2 pb-2">

            {/* COMPONENT C: BAND BENCHMARKING */}
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
                <BarChart3 className="icon"/><span className="text-sm">Band Benchmarking</span>
              </div>
              <div className="
                flex flex-col flex-1
                border-b-3 border-dsi-contrast-background
                overflow-x-hidden whitespace-nowrap border-collapse
                rounded-b-xl
                bg-dsi-analysis shadow-sm
                pt-4 pb-4
              ">
                <p className="pl-dsi-pad pr-dsi-pad text-sm mb-4 opacity-70 text-wrap">Average Exposure Modifier across book bands. Subject modifier shown as reference line ({subjectModifier.toFixed(3)}x).</p>
                <div className="pl-dsi-pad pr-dsi-pad h-[300px] w-full">
                  {exposureBandBenchmarks.length > 0 ? (
                    <ResponsiveContainer width="100%" height="100%">
                      <BarChart data={exposureBandBenchmarks} margin={{ top: 0, right: 0, bottom: 20, left: -20 }}>
                        <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#334155" opacity={0.5} />
                        <XAxis dataKey="band_label" stroke="#94a3b8" tick={{ fill: '#94a3b8', fontSize: 11 }} />
                        <YAxis stroke="#94a3b8" tick={{ fill: '#94a3b8', fontSize: 12 }} domain={['auto', 'auto']} />
                        <RechartsTooltip
                          contentStyle={tooltipStyle}
                          cursor={{ fill: '#1e293b', opacity: 0.4 }}
                          formatter={(value: any, name: string) => {
                            if (name === 'avg_modifier') return [`${Number(value).toFixed(3)}x`, 'Avg Modifier'];
                            return [value, name];
                          }}
                          labelFormatter={(label) => {
                            const match = exposureBandBenchmarks.find((d: any) => d.band_label === label);
                            if (!match) return label;
                            return `${label} (n=${match.peer_count}, avg value $${Number(match.avg_exposure_value || 0).toLocaleString(undefined, { maximumFractionDigits: 0 })})`;
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
                            const entry = exposureBandBenchmarks[index];
                            return (
                              <text x={x + width / 2} y={y - 6} textAnchor="middle" fill="#94a3b8" fontSize={10}>
                                n={entry?.peer_count}
                              </text>
                            );
                          }}
                        >
                          {exposureBandBenchmarks.map((entry: any, index: number) => (
                            <Cell
                              key={`cell-${index}`}
                              fill={entry.band_label === activeVersion.exposure_band_label ? '#3b82f6' : '#475569'}
                            />
                          ))}
                        </Bar>
                      </BarChart>
                    </ResponsiveContainer>
                  ) : (
                    <div className="flex h-full items-center justify-center opacity-50 italic text-sm">No band data available.</div>
                  )}
                </div>
              </div>
            </div>

            {/* COMPONENT D: TIER DISTRIBUTION */}
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
                <Layers className="icon"/><span className="text-sm">Exposure by Final Tier</span>
              </div>
              <div className="
                flex flex-col flex-1
                border-b-3 border-dsi-contrast-background
                overflow-x-hidden whitespace-nowrap border-collapse
                rounded-b-xl
                bg-dsi-analysis shadow-sm
                pt-4 pb-4
              ">
                <p className="pl-dsi-pad pr-dsi-pad text-sm mb-4 opacity-70 text-wrap">Average Exposure Magnitude Score within each Final Tier. Subject magnitude shown as reference line ({subjectMagnitude.toFixed(1)}).</p>
                <div className="pl-dsi-pad pr-dsi-pad h-[300px] w-full">
                  {exposureTierDistribution.length > 0 ? (
                    <ResponsiveContainer width="100%" height="100%">
                      <BarChart data={exposureTierDistribution} margin={{ top: 0, right: 0, bottom: 20, left: -20 }}>
                        <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#334155" opacity={0.5} />
                        <XAxis dataKey="tier" stroke="#94a3b8" tick={{ fill: '#94a3b8', fontSize: 11 }} />
                        <YAxis stroke="#94a3b8" tick={{ fill: '#94a3b8', fontSize: 12 }} domain={[0, 100]} />
                        <RechartsTooltip
                          contentStyle={tooltipStyle}
                          cursor={{ fill: '#1e293b', opacity: 0.4 }}
                          formatter={(value: any, name: string) => [Number(value).toFixed(1), name === 'avg_magnitude' ? 'Avg Magnitude' : name]}
                          labelFormatter={(label) => {
                            const match = exposureTierDistribution.find((d: any) => d.tier === label);
                            return match ? `${label} (n=${match.peer_count})` : label;
                          }}
                        />
                        {/* Subject magnitude reference line */}
                        <ReferenceLine
                          y={subjectMagnitude}
                          stroke="#3b82f6"
                          strokeDasharray="6 3"
                          strokeWidth={2}
                        >
                          <Label value={`Subject ${subjectMagnitude.toFixed(1)}`} position="right" fill="#3b82f6" fontSize={11} />
                        </ReferenceLine>
                        <Bar dataKey="avg_magnitude" fill="#64748b" radius={[4, 4, 0, 0]}
                          label={({ x, y, width, index }: any) => {
                            const entry = exposureTierDistribution[index];
                            return (
                              <text x={x + width / 2} y={y - 6} textAnchor="middle" fill="#94a3b8" fontSize={10}>
                                n={entry?.peer_count}
                              </text>
                            );
                          }}
                        >
                           {exposureTierDistribution.map((entry: any, index: number) => (
                            <Cell
                              key={`cell-${index}`}
                              fill={entry.tier === `Tier ${activeVersion.final_tier}` ? '#3b82f6' : '#475569'}
                            />
                          ))}
                        </Bar>
                      </BarChart>
                    </ResponsiveContainer>
                  ) : (
                    <div className="flex h-full items-center justify-center opacity-50 italic text-sm">No tier data available.</div>
                  )}
                </div>
              </div>
            </div>

          </div>
        </>
      )}

    </div>
  );
}

"use client";

import { useEffect } from "react";
import { useDsiStore } from "@/store/dsiStore";
import { Target, Activity, BarChart3, Layers, ScatterChart as ScatterIcon, Paperclip } from "lucide-react";
import { 
  ScatterChart, Scatter, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, ResponsiveContainer,
  BarChart, Bar, Cell, LineChart, Line
} from "recharts";

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

  // Highlight the active submission in the scatter plot
  const activePoint = [{
    x_magnitude: activeVersion.exposure_magnitude_score || 0,
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
      <div className="border border-dsi-outline/20 rounded-xl p-5 bg-dsi-analysis shadow-sm">
        <h3 className="text-sm font-bold tracking-wide flex items-center gap-2 mb-4 border-b border-dsi-outline/10 pb-2">
          <Target className="w-4 h-4 text-dsi-selected" /> Active Submission: Exposure Profile
        </h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
          <div>
            <span className="opacity-50 block text-xs mb-1">Exposure Value (TIV/Rev)</span>
            <span className="font-mono font-bold text-lg text-dsi-selected">
              ${(activeVersion.exposure_value || 0).toLocaleString()}
            </span>
          </div>
          <div>
            <span className="opacity-50 block text-xs mb-1">Exposure Band</span>
            <span className="font-mono font-bold text-lg uppercase">
              {activeVersion.exposure_band_label || "N/A"}
            </span>
          </div>
          <div>
            <span className="opacity-50 block text-xs mb-1">Magnitude Score</span>
            <span className="font-mono font-bold text-lg">
              {activeVersion.exposure_magnitude_score?.toFixed(1) || "0.0"}
            </span>
          </div>
          <div>
            <span className="opacity-50 block text-xs mb-1">Calculated Modifier</span>
            <span className="font-mono font-bold text-lg">
              {activeVersion.exposure_modifier?.toFixed(3) || "1.000"}x
            </span>
          </div>
        </div>
      </div>

      {isFetchingExposureAnalytics ? (
        <div className="flex flex-col items-center justify-center py-20 opacity-50 space-y-4">
          <Activity className="w-8 h-8 animate-spin" />
          <p className="font-mono text-sm tracking-widest uppercase">Calculating Exposure Benchmarks...</p>
        </div>
      ) : (
        <>
          {/* =======================================================================
              CHART ROW 1: SCATTER MATRIX
              ======================================================================= */}
          <div className="border border-dsi-outline/20 rounded-xl p-5 bg-dsi-analysis shadow-sm flex flex-col min-h-[400px]">
            <h3 className="text-sm font-bold tracking-wide flex items-center gap-2 mb-6">
              <ScatterIcon className="w-4 h-4 text-dsi-selected" /> Exposure Magnitude vs. Overall Risk
            </h3>
            <div className="flex-1 w-full relative">
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
                  {/* Background Peers */}
                  <Scatter name="Peer Group" data={exposureScatterData} fill="#475569" fillOpacity={0.6} />
                  {/* Active Submission Highlight */}
                  <Scatter name="Active Submission" data={activePoint} fill="#3b82f6" shape="star" />
                </ScatterChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* =======================================================================
              CHART ROW 2: BAND & TIER BENCHMARKING
              ======================================================================= */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 h-[400px]">
            
            {/* COMPONENT C: BAND BENCHMARKING */}
            <div className="border border-dsi-outline/20 rounded-xl p-5 bg-dsi-analysis shadow-sm flex flex-col">
              <h3 className="text-sm font-bold tracking-wide flex items-center gap-2 mb-2">
                <BarChart3 className="w-4 h-4 text-dsi-selected" /> Band Benchmarking
              </h3>
              <p className="text-xs opacity-50 mb-6">Average Exposure Modifier across book bands.</p>
              <div className="flex-1 w-full">
                {exposureBandBenchmarks.length > 0 ? (
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={exposureBandBenchmarks} margin={{ top: 0, right: 0, bottom: 20, left: -20 }}>
                      <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#334155" opacity={0.5} />
                      <XAxis dataKey="band_label" stroke="#94a3b8" tick={{ fill: '#94a3b8', fontSize: 11 }} />
                      <YAxis stroke="#94a3b8" tick={{ fill: '#94a3b8', fontSize: 12 }} domain={['auto', 'auto']} />
                      <RechartsTooltip 
                        contentStyle={tooltipStyle}
                        cursor={{ fill: '#1e293b', opacity: 0.4 }}
                        formatter={(value: any, name: string) => [name === 'avg_modifier' ? `${Number(value).toFixed(3)}x` : value, name === 'avg_modifier' ? 'Avg Modifier' : 'Avg Value']}
                      />
                      <Bar dataKey="avg_modifier" radius={[4, 4, 0, 0]}>
                        {exposureBandBenchmarks.map((entry, index) => (
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

            {/* COMPONENT D: TIER DISTRIBUTION */}
            <div className="border border-dsi-outline/20 rounded-xl p-5 bg-dsi-analysis shadow-sm flex flex-col">
              <h3 className="text-sm font-bold tracking-wide flex items-center gap-2 mb-2">
                <Layers className="w-4 h-4 text-dsi-selected" /> Exposure by Final Tier
              </h3>
              <p className="text-xs opacity-50 mb-6">Average Exposure Magnitude Score within each Final Tier.</p>
              <div className="flex-1 w-full">
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
                      />
                      <Bar dataKey="avg_magnitude" fill="#64748b" radius={[4, 4, 0, 0]}>
                         {exposureTierDistribution.map((entry, index) => (
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
        </>
      )}

    </div>
  );
}
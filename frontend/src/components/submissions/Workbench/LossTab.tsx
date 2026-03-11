"use client";

import { useEffect } from "react";
import { useDsiStore } from "@/store/dsiStore";
import { TrendingUp, Activity, Target, ShieldAlert, BarChart3 } from "lucide-react";
import { 
  ScatterChart, Scatter, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, ResponsiveContainer,
  BarChart, Bar, Cell,
  PieChart, Pie, Legend
} from "recharts";

export default function LossTab() {
  const { 
    activeSubmission, 
    activeVersion,
    lossCohortBenchmarks,
    lossTrendDistribution,
    lossScatterData,
    isFetchingLossAnalytics,
    fetchLossAnalytics
  } = useDsiStore();

  // 1. Fetch comparative data on mount
  useEffect(() => {
    if (activeSubmission?.coverage) {
      fetchLossAnalytics(activeSubmission.coverage, 365);
    }
  }, [activeSubmission?.coverage, fetchLossAnalytics]);

  if (!activeSubmission || !activeVersion) return null;

  // --- CHART HELPERS & DATA PREP ---
  
  // Isolate the active submission for the Scatter Plot so we can highlight it
  const activePoint = [{
    x_propensity: activeVersion.loss_propensity_score || 0,
    y_severity: activeVersion.severity_propensity_score || 0,
    name: "Current Submission"
  }];

  // Map Trend colors (Improving = Green, Stable = Slate, Worsening = Rose)
  const getTrendColor = (trend: string) => {
    const t = trend?.toLowerCase() || '';
    if (t.includes('improve')) return '#10b981'; // emerald-500
    if (t.includes('worsen')) return '#f43f5e';  // rose-500
    return '#64748b';                            // slate-500
  };

  // Standardize tooltip styling for dark mode
  const tooltipStyle = {
    backgroundColor: '#0f172a', // slate-900
    borderColor: '#334155',     // slate-700
    color: '#f8fafc',           // slate-50
    borderRadius: '8px',
    fontSize: '12px'
  };

  return (
    <div className="w-full max-w-[1400px] mx-auto space-y-6 animate-in fade-in duration-500 pb-12 pt-4">
      
      {/* =======================================================================
          COMPONENT A: SUBJECT PROFILE (HERO KPIs)
          ======================================================================= */}
      <div className="border border-dsi-outline/20 rounded-xl p-5 bg-dsi-analysis shadow-sm">
        <h3 className="text-sm font-bold tracking-wide flex items-center gap-2 mb-4 border-b border-dsi-outline/10 pb-2">
          <Target className="w-4 h-4 text-dsi-selected" /> Active Submission: Loss Profile
        </h3>
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-6">
          <div>
            <span className="opacity-50 block text-xs mb-1">Propensity Band</span>
            <span className="font-mono font-bold text-lg text-dsi-selected uppercase">
              {activeVersion.loss_propensity_band?.replace(/_/g, ' ') || "N/A"}
            </span>
          </div>
          <div>
            <span className="opacity-50 block text-xs mb-1">Combined Modifier</span>
            <span className="font-mono font-bold text-lg">
              {activeVersion.loss_combined_modifier?.toFixed(3) || "1.000"}x
            </span>
          </div>
          <div>
            <span className="opacity-50 block text-xs mb-1">Severity Score</span>
            <span className="font-mono font-bold text-lg">
              {activeVersion.severity_propensity_score?.toFixed(1) || "0.0"}
            </span>
          </div>
          <div>
            <span className="opacity-50 block text-xs mb-1">Score Velocity</span>
            <span className={`font-mono font-bold text-lg ${activeVersion.loss_score_velocity > 0 ? 'text-rose-400' : 'text-emerald-400'}`}>
              {activeVersion.loss_score_velocity > 0 ? '+' : ''}{activeVersion.loss_score_velocity || "0.0"}
            </span>
          </div>
          <div>
            <span className="opacity-50 block text-xs mb-1">Cohort Assignment</span>
            <span className="font-mono font-bold text-sm leading-tight block">
              {activeVersion.loss_cohort_name || "Unknown"}
            </span>
          </div>
        </div>
      </div>

      {isFetchingLossAnalytics ? (
        <div className="flex flex-col items-center justify-center py-20 opacity-50 space-y-4">
          <Activity className="w-8 h-8 animate-spin" />
          <p className="font-mono text-sm tracking-widest uppercase">Calculating Peer Benchmarks...</p>
        </div>
      ) : (
        <>
          {/* =======================================================================
              CHART ROW 1: SCATTER & DONUT
              ======================================================================= */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            
            {/* COMPONENT B: FREQUENCY VS SEVERITY MATRIX */}
            <div className="lg:col-span-2 border border-dsi-outline/20 rounded-xl p-5 bg-dsi-analysis shadow-sm flex flex-col min-h-[400px]">
              <h3 className="text-sm font-bold tracking-wide flex items-center gap-2 mb-6">
                <ShieldAlert className="w-4 h-4 text-dsi-selected" /> Frequency vs. Severity Matrix
              </h3>
              <div className="flex-1 w-full relative">
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
                    {/* Background Peers */}
                    <Scatter name="Peer Group" data={lossScatterData} fill="#475569" fillOpacity={0.6} />
                    {/* Active Submission Highlight */}
                    <Scatter name="Active Submission" data={activePoint} fill="#3b82f6" shape="star" />
                  </ScatterChart>
                </ResponsiveContainer>
              </div>
            </div>

            {/* COMPONENT D: TREND DISTRIBUTION */}
            <div className="border border-dsi-outline/20 rounded-xl p-5 bg-dsi-analysis shadow-sm flex flex-col min-h-[400px]">
              <h3 className="text-sm font-bold tracking-wide flex items-center gap-2 mb-2">
                <TrendingUp className="w-4 h-4 text-dsi-selected" /> Trend Distribution
              </h3>
              <p className="text-xs opacity-50 mb-4">Peer velocity trajectory over the last year.</p>
              <div className="flex-1 w-full">
                {lossTrendDistribution.length > 0 ? (
                  <ResponsiveContainer width="100%" height="100%">
                    <PieChart>
                      <Pie
                        data={lossTrendDistribution}
                        dataKey="count"
                        nameKey="trend"
                        cx="50%"
                        cy="50%"
                        innerRadius={60}
                        outerRadius={90}
                        paddingAngle={5}
                      >
                        {lossTrendDistribution.map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={getTrendColor(entry.trend)} />
                        ))}
                      </Pie>
                      <RechartsTooltip contentStyle={tooltipStyle} />
                      <Legend 
                        verticalAlign="bottom" 
                        height={36} 
                        formatter={(value) => <span className="text-xs uppercase tracking-wider text-slate-300">{value}</span>}
                      />
                    </PieChart>
                  </ResponsiveContainer>
                ) : (
                  <div className="flex h-full items-center justify-center opacity-50 italic text-sm">No trend data available.</div>
                )}
              </div>
            </div>

          </div>

          {/* =======================================================================
              CHART ROW 2: COHORT BENCHMARKING
              ======================================================================= */}
          <div className="border border-dsi-outline/20 rounded-xl p-5 bg-dsi-analysis shadow-sm flex flex-col h-[400px]">
            <h3 className="text-sm font-bold tracking-wide flex items-center gap-2 mb-2">
              <BarChart3 className="w-4 h-4 text-dsi-selected" /> Cohort Benchmarking
            </h3>
            <p className="text-xs opacity-50 mb-6">Average Combined Loss Modifier across all cohorts (Active cohort highlighted).</p>
            <div className="flex-1 w-full">
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
                      formatter={(value: any, name: string) => [
                        name === 'avg_modifier' ? `${Number(value).toFixed(3)}x` : value, 
                        name === 'avg_modifier' ? 'Avg Modifier' : 'Peer Count'
                      ]}
                    />
                    <Bar dataKey="avg_modifier" radius={[4, 4, 0, 0]}>
                      {lossCohortBenchmarks.map((entry, index) => (
                        <Cell 
                          key={`cell-${index}`} 
                          // Highlight the cohort that matches the active submission's cohort
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
        </>
      )}

    </div>
  );
}
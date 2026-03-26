"use client";

import { useState, useMemo, useEffect } from "react";
import { useDsiStore } from "@/store/dsiStore";
import ViewCanvas from "@/components/ViewCanvas";
import {
  Orbit, Target, Layers, Zap, BarChart3,
  TrendingDown, AlertTriangle, ArrowRight, RotateCcw, ChevronDown
} from "lucide-react";
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip,
  ResponsiveContainer, Cell, ScatterChart, Scatter
} from "recharts";
import { SHOCK_SCENARIOS, applyShock, ShockResult } from "@/lib/shockEngine";
import { formatNum } from "@/lib/format";

const TIER_COLORS = ['var(--dsi-positive)', 'var(--dsi-info)', 'var(--dsi-warning)', 'var(--dsi-negative)', 'var(--dsi-negative)'];
const DECISION_DOT: Record<string, string> = { approve: 'var(--dsi-approve)', refer: 'var(--dsi-refer)', decline: 'var(--dsi-decline)' };

export default function WorldEngineView() {
  const { submissions, fetchSubmissions, fetchCoreSubmissionDetail, setHasPageActions } = useDsiStore();

  const [selectedScenario, setSelectedScenario] = useState(SHOCK_SCENARIOS[0].id);
  const [scope, setScope] = useState('all');
  const [magnitude, setMagnitude] = useState(SHOCK_SCENARIOS[0].magnitude);
  const [shockApplied, setShockApplied] = useState(false);

  useEffect(() => {
    setHasPageActions(false);
    if (submissions.length === 0) fetchSubmissions();
  }, []);

  // Sync magnitude when scenario changes
  const scenario = SHOCK_SCENARIOS.find(s => s.id === selectedScenario) || SHOCK_SCENARIOS[0];
  useEffect(() => { setMagnitude(scenario.magnitude); setShockApplied(false); }, [scenario]);

  // Unique coverages for scope selector
  const coverages = useMemo(() => {
    const set = new Set<string>();
    submissions.forEach((s: any) => {
      const cov = (s.coverage_configuration || '').split(' / ')[0];
      if (cov) set.add(cov);
    });
    return Array.from(set).sort();
  }, [submissions]);

  // Portfolio aggregates
  const portfolio = useMemo(() => {
    const totalPremium = submissions.reduce((s: number, sub: any) => s + (sub.recommended_premium || 0), 0);
    const avgScore = submissions.length > 0 ? submissions.reduce((s: number, sub: any) => s + (sub.pure_composite_score || 0), 0) / submissions.length : 0;
    const tierDist: Record<number, number> = {};
    const covDist: Record<string, number> = {};
    const decDist: Record<string, number> = {};
    submissions.forEach((sub: any) => {
      const tier = sub.final_tier || 0;
      tierDist[tier] = (tierDist[tier] || 0) + 1;
      const cov = (sub.coverage_configuration || 'Unknown').split(' / ')[0];
      covDist[cov] = (covDist[cov] || 0) + 1;
      const dec = (sub.decision || 'unknown').toLowerCase();
      decDist[dec] = (decDist[dec] || 0) + 1;
    });
    return { totalPremium, avgScore, tierDist, covDist, decDist, count: submissions.length };
  }, [submissions]);

  const tierChartData = Object.entries(portfolio.tierDist).map(([tier, count]) => ({ tier: `Tier ${tier}`, count, tierNum: Number(tier) })).sort((a, b) => a.tierNum - b.tierNum);
  const covChartData = Object.entries(portfolio.covDist).map(([cov, count]) => ({ coverage: cov, count, pct: ((count / (portfolio.count || 1)) * 100).toFixed(0) })).sort((a, b) => b.count - a.count);

  // Shock result
  const shockResult: ShockResult | null = useMemo(() => {
    if (!shockApplied) return null;
    return applyShock(submissions, scenario, scope, magnitude);
  }, [shockApplied, submissions, scenario, scope, magnitude]);

  // Tier migration data for after chart
  const afterTierData = shockResult ? Object.entries(shockResult.tier_dist_after).map(([tier, count]) => ({ tier: `Tier ${tier}`, count, tierNum: Number(tier) })).sort((a, b) => a.tierNum - b.tierNum) : [];

  const tooltipStyle = { backgroundColor: 'var(--dsi-chart-tooltip-bg)', borderColor: 'var(--dsi-chart-tooltip-border)', color: '#f8fafc', borderRadius: '8px', fontSize: '12px' };

  return (
    <ViewCanvas unstyledMain={true}>
      <div className="w-full h-full overflow-y-auto no-scrollbar bg-dsi-background text-dsi-contrast-background p-dsi-pad animate-in fade-in duration-500 pb-12">

        {/* HERO HEADER */}
        <div className="flex items-center gap-4 mb-6">
          <Orbit className="w-8 h-8 text-dsi-selected" />
          <div>
            <h1 className="text-2xl font-black tracking-wide">World Engine</h1>
            <p className="text-xs opacity-50">Portfolio intelligence &bull; Shock simulation &bull; Impact analysis</p>
          </div>
        </div>

        {/* ═══════════════════════════════════════════════════════════════
            PORTFOLIO OVERVIEW
            ═══════════════════════════════════════════════════════════════ */}
        <div className="flex flex-col mb-4">
          <div className="flex gap-dsi-pad rounded-t-xl border-b-1 border-dsi-outline/50 overflow-x-hidden whitespace-nowrap border-collapse bg-dsi-analysis/60 pl-dsi-pad pt-2 pb-2">
            <Target className="icon"/><span className="text-sm">Portfolio Overview</span>
            <span className="text-[10px] opacity-40 ml-2">{portfolio.count} submissions</span>
          </div>
          <div className="border-b-3 border-dsi-contrast-background rounded-b-xl bg-dsi-analysis shadow-sm pt-4 pb-4 px-dsi-pad">

            {/* Key Metrics */}
            <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-6">
              <div className="border border-dsi-outline/20 rounded-lg p-3">
                <span className="text-xs opacity-60 block mb-1">Total Submissions</span>
                <span className="text-xl font-black text-dsi-selected">{portfolio.count}</span>
              </div>
              <div className="border border-dsi-outline/20 rounded-lg p-3">
                <span className="text-xs opacity-60 block mb-1">Aggregate Premium</span>
                <span className="text-xl font-black text-dsi-selected">${(portfolio.totalPremium / 1000000).toFixed(1)}M</span>
              </div>
              <div className="border border-dsi-outline/20 rounded-lg p-3">
                <span className="text-xs opacity-60 block mb-1">Average Score</span>
                <span className="text-xl font-black text-dsi-selected">{formatNum(portfolio.avgScore, 0)}</span>
              </div>
              <div className="border border-dsi-outline/20 rounded-lg p-3">
                <span className="text-xs opacity-60 block mb-1">Approval Rate</span>
                <span className="text-xl font-black text-dsi-positive">
                  {portfolio.count > 0 ? ((portfolio.decDist['approve'] || 0) / portfolio.count * 100).toFixed(0) : 0}%
                </span>
              </div>
              <div className="border border-dsi-outline/20 rounded-lg p-3">
                <span className="text-xs opacity-60 block mb-1">Referral Rate</span>
                <span className="text-xl font-black text-dsi-warning">
                  {portfolio.count > 0 ? ((portfolio.decDist['refer'] || 0) / portfolio.count * 100).toFixed(0) : 0}%
                </span>
              </div>
            </div>

            {/* Charts */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Tier Distribution */}
              <div>
                <span className="text-xs opacity-60 block mb-2">Tier Distribution</span>
                <div className="h-[200px]">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={tierChartData} margin={{ top: 5, right: 10, bottom: 5, left: -20 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke="var(--dsi-chart-grid)" opacity={0.3} />
                      <XAxis dataKey="tier" stroke="var(--dsi-chart-axis)" tick={{ fill: 'var(--dsi-chart-axis)', fontSize: 11 }} />
                      <YAxis stroke="var(--dsi-chart-axis)" tick={{ fill: 'var(--dsi-chart-axis)', fontSize: 11 }} />
                      <RechartsTooltip contentStyle={tooltipStyle} />
                      <Bar dataKey="count" radius={[4, 4, 0, 0]}>
                        {tierChartData.map((entry, idx) => (
                          <Cell key={idx} fill={TIER_COLORS[entry.tierNum - 1] || 'var(--dsi-chart-peer)'} />
                        ))}
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </div>

              {/* Sector Concentration */}
              <div>
                <span className="text-xs opacity-60 block mb-2">Sector Concentration</span>
                <div className="space-y-2">
                  {covChartData.slice(0, 6).map((entry) => (
                    <div key={entry.coverage} className="flex items-center gap-3">
                      <span className="text-xs w-24 truncate opacity-70" title={entry.coverage}>{entry.coverage}</span>
                      <div className="flex-1 h-4 bg-dsi-background rounded-full overflow-hidden">
                        <div className="h-full rounded-full bg-dsi-selected/40" style={{ width: `${entry.pct}%` }} />
                      </div>
                      <span className="text-xs font-bold w-12 text-right">{entry.count} ({entry.pct}%)</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* ═══════════════════════════════════════════════════════════════
            SHOCK SIMULATOR
            ═══════════════════════════════════════════════════════════════ */}
        <div className="flex flex-col mb-4">
          <div className="flex gap-dsi-pad rounded-t-xl border-b-1 border-dsi-outline/50 overflow-x-hidden whitespace-nowrap border-collapse bg-dsi-analysis/60 pl-dsi-pad pt-2 pb-2">
            <Zap className="icon"/><span className="text-sm">Shock Simulator</span>
            {shockApplied && (
              <button onClick={() => setShockApplied(false)} className="ml-auto mr-dsi-pad flex items-center gap-1 text-xs text-dsi-selected hover:opacity-70">
                <RotateCcw className="w-3 h-3" /> Reset
              </button>
            )}
          </div>
          <div className="border-b-3 border-dsi-contrast-background rounded-b-xl bg-dsi-analysis shadow-sm pt-4 pb-4 px-dsi-pad">

            {/* Controls */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-4">
              {/* Scenario */}
              <div>
                <span className="text-xs opacity-60 block mb-1">Scenario</span>
                <select
                  value={selectedScenario}
                  onChange={(e) => setSelectedScenario(e.target.value)}
                  className="w-full bg-dsi-background border border-dsi-outline/30 rounded px-3 py-2 text-sm outline-none focus:border-dsi-selected"
                >
                  {SHOCK_SCENARIOS.map(s => (
                    <option key={s.id} value={s.id}>{s.name}</option>
                  ))}
                </select>
              </div>

              {/* Scope */}
              <div>
                <span className="text-xs opacity-60 block mb-1">Scope</span>
                <select
                  value={scope}
                  onChange={(e) => { setScope(e.target.value); setShockApplied(false); }}
                  className="w-full bg-dsi-background border border-dsi-outline/30 rounded px-3 py-2 text-sm outline-none focus:border-dsi-selected"
                >
                  <option value="all">All Submissions</option>
                  {coverages.map(c => (
                    <option key={c} value={c}>{c}</option>
                  ))}
                </select>
              </div>

              {/* Magnitude */}
              <div>
                <span className="text-xs opacity-60 block mb-1">Magnitude: {magnitude} pts</span>
                <input
                  type="range" min="5" max="50" step="1"
                  value={magnitude}
                  onChange={(e) => { setMagnitude(Number(e.target.value)); setShockApplied(false); }}
                  className="w-full"
                />
              </div>

              {/* Apply */}
              <div className="flex items-end">
                <button
                  onClick={() => setShockApplied(true)}
                  className="w-full bg-dsi-selected text-dsi-background px-4 py-2 rounded font-bold text-sm hover:opacity-90 transition-opacity flex items-center justify-center gap-2"
                >
                  <Zap className="w-4 h-4" /> Apply Shock
                </button>
              </div>
            </div>

            {/* Scenario description */}
            <p className="text-xs opacity-50 text-wrap">{scenario.description}</p>
          </div>
        </div>

        {/* ═══════════════════════════════════════════════════════════════
            IMPACT DASHBOARD (shown after shock applied)
            ═══════════════════════════════════════════════════════════════ */}
        {shockResult && (
          <div className="flex flex-col mb-4">
            <div className="flex gap-dsi-pad rounded-t-xl border-b-1 border-dsi-outline/50 overflow-x-hidden whitespace-nowrap border-collapse bg-dsi-analysis/60 pl-dsi-pad pt-2 pb-2">
              <AlertTriangle className="icon text-dsi-warning"/>
              <span className="text-sm">Impact Analysis — {scenario.name}</span>
              <span className="text-[10px] opacity-40 ml-2">{shockResult.total_affected} of {submissions.length} affected</span>
            </div>
            <div className="border-b-3 border-dsi-contrast-background rounded-b-xl bg-dsi-analysis shadow-sm pt-4 pb-4 px-dsi-pad">

              {/* Impact KPIs */}
              <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-6">
                <div className="border border-dsi-outline/20 rounded-lg p-3">
                  <span className="text-xs opacity-60 block mb-1">Risks Affected</span>
                  <span className="text-xl font-black text-dsi-warning">{shockResult.total_affected}</span>
                </div>
                <div className="border border-dsi-outline/20 rounded-lg p-3">
                  <span className="text-xs opacity-60 block mb-1">Tier Migrations</span>
                  <span className="text-xl font-black text-dsi-negative">{shockResult.tier_migrations}</span>
                </div>
                <div className="border border-dsi-outline/20 rounded-lg p-3">
                  <span className="text-xs opacity-60 block mb-1">Decision Changes</span>
                  <span className="text-xl font-black text-dsi-negative">{shockResult.decision_changes}</span>
                </div>
                <div className="border border-dsi-outline/20 rounded-lg p-3">
                  <span className="text-xs opacity-60 block mb-1">Premium Impact</span>
                  <span className={`text-xl font-black ${shockResult.premium_delta > 0 ? 'text-dsi-negative' : 'text-dsi-positive'}`}>
                    {shockResult.premium_delta > 0 ? '+' : ''}${(shockResult.premium_delta / 1000).toFixed(0)}K
                  </span>
                </div>
                <div className="border border-dsi-outline/20 rounded-lg p-3">
                  <span className="text-xs opacity-60 block mb-1">Premium Change</span>
                  <span className={`text-xl font-black ${shockResult.premium_delta > 0 ? 'text-dsi-negative' : 'text-dsi-positive'}`}>
                    {shockResult.aggregate_premium_before > 0
                      ? `${shockResult.premium_delta > 0 ? '+' : ''}${((shockResult.premium_delta / shockResult.aggregate_premium_before) * 100).toFixed(1)}%`
                      : 'N/A'}
                  </span>
                </div>
              </div>

              {/* Tier Distribution Before/After */}
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
                <div>
                  <span className="text-xs opacity-60 block mb-2">Tier Distribution — Before</span>
                  <div className="h-[180px]">
                    <ResponsiveContainer width="100%" height="100%">
                      <BarChart data={tierChartData} margin={{ top: 5, right: 10, bottom: 5, left: -20 }}>
                        <CartesianGrid strokeDasharray="3 3" stroke="var(--dsi-chart-grid)" opacity={0.3} />
                        <XAxis dataKey="tier" stroke="var(--dsi-chart-axis)" tick={{ fill: 'var(--dsi-chart-axis)', fontSize: 11 }} />
                        <YAxis stroke="var(--dsi-chart-axis)" tick={{ fill: 'var(--dsi-chart-axis)', fontSize: 11 }} />
                        <RechartsTooltip contentStyle={tooltipStyle} />
                        <Bar dataKey="count" radius={[4, 4, 0, 0]}>
                          {tierChartData.map((entry, idx) => (
                            <Cell key={idx} fill={TIER_COLORS[entry.tierNum - 1] || 'var(--dsi-chart-peer)'} />
                          ))}
                        </Bar>
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                </div>
                <div>
                  <span className="text-xs opacity-60 block mb-2">Tier Distribution — After Shock</span>
                  <div className="h-[180px]">
                    <ResponsiveContainer width="100%" height="100%">
                      <BarChart data={afterTierData} margin={{ top: 5, right: 10, bottom: 5, left: -20 }}>
                        <CartesianGrid strokeDasharray="3 3" stroke="var(--dsi-chart-grid)" opacity={0.3} />
                        <XAxis dataKey="tier" stroke="var(--dsi-chart-axis)" tick={{ fill: 'var(--dsi-chart-axis)', fontSize: 11 }} />
                        <YAxis stroke="var(--dsi-chart-axis)" tick={{ fill: 'var(--dsi-chart-axis)', fontSize: 11 }} />
                        <RechartsTooltip contentStyle={tooltipStyle} />
                        <Bar dataKey="count" radius={[4, 4, 0, 0]}>
                          {afterTierData.map((entry, idx) => (
                            <Cell key={idx} fill={TIER_COLORS[entry.tierNum - 1] || 'var(--dsi-chart-peer)'} />
                          ))}
                        </Bar>
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                </div>
              </div>

              {/* Most Affected Table */}
              <div>
                <span className="text-xs opacity-60 block mb-2">Most Affected Submissions</span>
                <div className="overflow-x-auto">
                  <table className="w-full text-sm text-left whitespace-nowrap">
                    <thead>
                      <tr className="text-xs underline opacity-70">
                        <th className="py-2 pr-2">Entity</th>
                        <th className="py-2 px-2 text-right">Score Before</th>
                        <th className="py-2 px-2 text-center"><ArrowRight className="w-3 h-3 inline" /></th>
                        <th className="py-2 px-2 text-right">Score After</th>
                        <th className="py-2 px-2 text-right">Delta</th>
                        <th className="py-2 px-2 text-center">Tier</th>
                        <th className="py-2 px-2 text-center">Decision</th>
                        <th className="py-2 px-2 text-right">Premium Impact</th>
                      </tr>
                    </thead>
                    <tbody>
                      {shockResult.affected.slice(0, 15).map((item, idx) => (
                        <tr
                          key={idx}
                          onClick={() => fetchCoreSubmissionDetail(item.original)}
                          className={`border-b border-dsi-outline/5 cursor-pointer hover:bg-dsi-background/20 transition-colors ${item.tier_changed ? 'bg-dsi-negative/5' : ''}`}
                        >
                          <td className="py-2 pr-2 font-semibold">{item.original.entity_name}</td>
                          <td className="py-2 px-2 text-right">{formatNum(item.original_score, 0)}</td>
                          <td className="py-2 px-2 text-center opacity-30">→</td>
                          <td className="py-2 px-2 text-right text-dsi-negative font-bold">{formatNum(item.shocked_score, 0)}</td>
                          <td className="py-2 px-2 text-right text-dsi-negative">{item.score_delta}</td>
                          <td className="py-2 px-2 text-center">
                            {item.tier_changed ? (
                              <span className="text-dsi-negative font-bold">T{item.original_tier}→T{item.shocked_tier}</span>
                            ) : (
                              <span className="opacity-50">T{item.original_tier}</span>
                            )}
                          </td>
                          <td className="py-2 px-2 text-center">
                            {item.decision_changed ? (
                              <span className="text-dsi-negative font-bold">{item.original_decision}→{item.shocked_decision}</span>
                            ) : (
                              <span className="opacity-50">{item.original_decision}</span>
                            )}
                          </td>
                          <td className="py-2 px-2 text-right">
                            {item.premium_delta !== 0 ? (
                              <span className={item.premium_delta > 0 ? 'text-dsi-negative' : 'text-dsi-positive'}>
                                {item.premium_delta > 0 ? '+' : ''}${item.premium_delta.toLocaleString()}
                              </span>
                            ) : (
                              <span className="opacity-30">—</span>
                            )}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                  {shockResult.affected.length > 15 && (
                    <p className="text-xs opacity-40 mt-2">Showing top 15 of {shockResult.affected.length} affected submissions.</p>
                  )}
                </div>
              </div>
            </div>
          </div>
        )}

      </div>
    </ViewCanvas>
  );
}

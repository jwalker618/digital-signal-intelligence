"use client";

import { useState, useMemo, useEffect } from "react";
import { useDsiStore } from "@/store/dsiStore";
import ViewCanvas from "@/components/ViewCanvas";
import {
  Orbit, Target, Zap, AlertTriangle, ArrowRight, RotateCcw,
  Plus, X, Radio,
  Sparkles, TrendingDown, Network as NetworkIcon,
} from "lucide-react";
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip,
  ResponsiveContainer, Cell
} from "recharts";
import { SHOCK_SCENARIOS, ActiveShock, applyMultipleShocks, generateEmergingScenarios, ShockResult } from "@/lib/shockEngine";
import { formatNumber, formatCurrency, formatPercent } from "@/lib/format";
import { tooltipStyle } from "@/lib/chartConfig";
import { api, fmtDate, fmtRelative } from "@/lib/api";
import { StatusBadge } from "@/components/shared/StatusBadge";
import type {
  DiscoveredRelationship,
  DriftAlert,
  MaturityState,
  WorldEngineStats,
} from "@/types/worldEngine";

const TIER_COLORS = ['var(--dsi-positive)', 'var(--dsi-info)', 'var(--dsi-warning)', 'var(--dsi-negative)', 'var(--dsi-negative)'];

const LIKELIHOOD_COLOR: Record<string, string> = {
  'High': 'text-dsi-negative',
  'Elevated': 'text-dsi-warning',
  'Moderate': 'text-dsi-warning',
  'Low-Moderate': 'text-dsi-muted',
  'Low': 'text-dsi-muted',
};

export default function WorldEngineView() {
  const { submissions, fetchSubmissions, fetchCoreSubmissionDetail, setHasPageActions } = useDsiStore();

  // Multi-shock state
  const [activeShocks, setActiveShocks] = useState<ActiveShock[]>([]);
  const [pendingScenario, setPendingScenario] = useState(SHOCK_SCENARIOS[0].id);
  const [pendingScope, setPendingScope] = useState('all');
  const [pendingMagnitude, setPendingMagnitude] = useState(SHOCK_SCENARIOS[0].magnitude);

  // Backend world-model state (/api/v1/world-engine/*)
  const [maturity, setMaturity] = useState<MaturityState | null>(null);
  const [weStats, setWeStats] = useState<WorldEngineStats | null>(null);
  const [alerts, setAlerts] = useState<DriftAlert[]>([]);
  const [rels, setRels] = useState<DiscoveredRelationship[]>([]);
  const [ackBusy, setAckBusy] = useState<string | null>(null);

  async function loadWorldModel() {
    const [m, s, a, r] = await Promise.all([
      api.get<MaturityState>("/api/v1/world-engine/maturity").catch(() => null),
      api.get<WorldEngineStats>("/api/v1/world-engine/stats").catch(() => null),
      api
        .get<{ alerts: DriftAlert[] }>("/api/v1/world-engine/drift-alerts?unacknowledged_only=true")
        .catch(() => ({ alerts: [] as DriftAlert[] })),
      api
        .get<{ relationships: DiscoveredRelationship[] }>("/api/v1/world-engine/relationships?limit=50")
        .catch(() => ({ relationships: [] as DiscoveredRelationship[] })),
    ]);
    setMaturity(m);
    setWeStats(s);
    setAlerts(a.alerts ?? []);
    setRels(r.relationships ?? []);
  }

  async function acknowledgeAlert(alertId: string) {
    setAckBusy(alertId);
    try {
      await api.post(`/api/v1/world-engine/drift-alerts/${alertId}/acknowledge`);
      await loadWorldModel();
    } finally {
      setAckBusy(null);
    }
  }

  useEffect(() => {
    setHasPageActions(false);
    if (submissions.length === 0) fetchSubmissions();
    void loadWorldModel();
  }, []);

  // Sync magnitude when pending scenario changes
  useEffect(() => {
    const s = SHOCK_SCENARIOS.find(s => s.id === pendingScenario);
    if (s) setPendingMagnitude(s.magnitude);
  }, [pendingScenario]);

  // Coverages for scope selector
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
      tierDist[sub.final_tier || 0] = (tierDist[sub.final_tier || 0] || 0) + 1;
      const cov = (sub.coverage_configuration || 'Unknown').split(' / ')[0];
      covDist[cov] = (covDist[cov] || 0) + 1;
      decDist[(sub.decision || 'unknown').toLowerCase()] = (decDist[(sub.decision || 'unknown').toLowerCase()] || 0) + 1;
    });
    return { totalPremium, avgScore, tierDist, covDist, decDist, count: submissions.length };
  }, [submissions]);

  const tierChartData = Object.entries(portfolio.tierDist).map(([t, c]) => ({ tier: `Tier ${t}`, count: c, tierNum: Number(t) })).sort((a, b) => a.tierNum - b.tierNum);
  const covChartData = Object.entries(portfolio.covDist).map(([c, n]) => ({ coverage: c, count: n, pct: formatNumber((n / (portfolio.count || 1)) * 100) })).sort((a, b) => b.count - a.count);

  // Shock result — recalculates when active shocks change
  const shockResult: ShockResult | null = useMemo(() => {
    if (activeShocks.length === 0) return null;
    return applyMultipleShocks(submissions, activeShocks);
  }, [activeShocks, submissions]);

  const afterTierData = shockResult ? Object.entries(shockResult.tier_dist_after).map(([t, c]) => ({ tier: `Tier ${t}`, count: c, tierNum: Number(t) })).sort((a, b) => a.tierNum - b.tierNum) : [];

  // Emerging scenarios — generated from portfolio composition
  const emergingScenarios = useMemo(() => generateEmergingScenarios(submissions), [submissions]);

  // Add a shock
  const addShock = () => {
    const scenario = SHOCK_SCENARIOS.find(s => s.id === pendingScenario);
    if (!scenario) return;
    setActiveShocks(prev => [...prev, { scenario, scope: pendingScope, magnitude: pendingMagnitude }]);
  };

  const removeShock = (idx: number) => {
    setActiveShocks(prev => prev.filter((_, i) => i !== idx));
  };

  // Apply emerging scenario as a shock
  const applyEmerging = (e: any) => {
    const scenario: any = { id: e.id, name: e.name, description: e.description, magnitude: e.estimated_magnitude };
    setActiveShocks(prev => [...prev, { scenario, scope: e.affected_scope, magnitude: e.estimated_magnitude }]);
  };

  return (
    <ViewCanvas unstyledMain={true}>
      <div className="w-full h-full overflow-y-auto no-scrollbar bg-dsi-background text-dsi-contrast-background p-dsi-pad animate-in fade-in duration-500 pb-12">

        {/* HERO */}
        <div className="flex items-center gap-4 mb-6">
          <Orbit className="w-8 h-8 text-dsi-selected" />
          <div>
            <h1 className="text-2xl font-black tracking-wide">World Engine</h1>
            <p className="text-xs opacity-50">World model &bull; Portfolio intelligence &bull; Shock simulation &bull; Emerging risk analysis</p>
          </div>
        </div>

        {/* ═══ WORLD MODEL ═══ */}
        <div className="flex flex-col mb-4">
          <div className="flex gap-dsi-pad rounded-t-xl border-b-1 border-dsi-outline/50 bg-dsi-analysis/60 pl-dsi-pad pt-2 pb-2">
            <Sparkles className="icon"/><span className="text-sm">World Model</span>
            <span className="text-[10px] opacity-40 ml-2">
              {maturity ? `${maturity.assessed_entity_count} entities` : "No data"}
            </span>
          </div>
          <div className="border-b-3 border-dsi-contrast-background rounded-b-xl bg-dsi-analysis shadow-sm pt-4 pb-4 px-dsi-pad">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="border border-dsi-outline/20 rounded-lg p-3">
                <span className="text-xs opacity-60 block mb-1">Maturity Stage</span>
                <span className="text-xl font-black text-dsi-selected uppercase">
                  {maturity?.stage ?? "—"}
                </span>
                {maturity && (
                  <span className="block text-[10px] opacity-60 mt-1">
                    {formatNumber(maturity.time_depth_months, 1)} months of data
                  </span>
                )}
              </div>
              <div className="border border-dsi-outline/20 rounded-lg p-3">
                <span className="text-xs opacity-60 block mb-1">Active Relationships</span>
                <span className="text-xl font-black text-dsi-selected">
                  {weStats?.relationships_by_state?.active ?? maturity?.active_relationships ?? "—"}
                </span>
                {maturity && (
                  <span className="block text-[10px] opacity-60 mt-1">
                    {maturity.provisional_relationships} provisional &middot; {maturity.candidate_relationships} candidate
                  </span>
                )}
              </div>
              <div className="border border-dsi-outline/20 rounded-lg p-3">
                <span className="text-xs opacity-60 block mb-1">Open Drift Alerts</span>
                <span className={`text-xl font-black ${weStats && weStats.drift_alerts_unacknowledged > 0 ? "text-dsi-warning" : "text-dsi-selected"}`}>
                  {weStats?.drift_alerts_unacknowledged ?? "—"}
                </span>
              </div>
              <div className="border border-dsi-outline/20 rounded-lg p-3">
                <span className="text-xs opacity-60 block mb-1">Assessed Entities</span>
                <span className="text-xl font-black text-dsi-selected">
                  {maturity?.assessed_entity_count ?? "—"}
                </span>
                {maturity && (
                  <span className="block text-[10px] opacity-60 mt-1">
                    {maturity.entities_with_temporal_data} with history
                  </span>
                )}
              </div>
            </div>
          </div>
        </div>

        {/* ═══ OPEN DRIFT ALERTS ═══ */}
        <div className="flex flex-col mb-4">
          <div className="flex gap-dsi-pad rounded-t-xl border-b-1 border-dsi-outline/50 bg-dsi-analysis/60 pl-dsi-pad pt-2 pb-2">
            <TrendingDown className="icon text-dsi-warning"/><span className="text-sm">Open Drift Alerts</span>
            <span className="text-[10px] opacity-40 ml-2">{alerts.length} open</span>
          </div>
          <div className="border-b-3 border-dsi-contrast-background rounded-b-xl bg-dsi-analysis shadow-sm pt-2 pb-2 overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-xs underline opacity-70 text-left">
                  <th className="py-2 px-dsi-pad">Signal</th>
                  <th className="py-2 px-2">Severity</th>
                  <th className="py-2 px-2">Type</th>
                  <th className="py-2 px-2">Detected</th>
                  <th className="py-2 px-2">Summary</th>
                  <th className="py-2 px-dsi-pad"></th>
                </tr>
              </thead>
              <tbody>
                {alerts.map((a) => (
                  <tr key={a.id} className="border-t border-dsi-outline/10">
                    <td className="py-2 px-dsi-pad font-mono text-xs">{a.source_signal ?? "—"}</td>
                    <td className="py-2 px-2"><StatusBadge status={a.severity} /></td>
                    <td className="py-2 px-2 text-xs">{a.alert_type}</td>
                    <td className="py-2 px-2 text-xs">{fmtRelative(a.detected_at)}</td>
                    <td className="py-2 px-2 opacity-80">{a.description}</td>
                    <td className="py-2 px-dsi-pad">
                      <button
                        onClick={() => void acknowledgeAlert(a.id)}
                        disabled={ackBusy === a.id}
                        className="text-xs text-dsi-selected hover:underline disabled:opacity-50"
                      >
                        Acknowledge
                      </button>
                    </td>
                  </tr>
                ))}
                {alerts.length === 0 && (
                  <tr>
                    <td colSpan={6} className="py-4 px-dsi-pad opacity-60 text-center text-xs">
                      No open alerts.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>

        {/* ═══ DISCOVERED RELATIONSHIPS ═══ */}
        <div className="flex flex-col mb-4">
          <div className="flex gap-dsi-pad rounded-t-xl border-b-1 border-dsi-outline/50 bg-dsi-analysis/60 pl-dsi-pad pt-2 pb-2">
            <NetworkIcon className="icon"/><span className="text-sm">Discovered Relationships</span>
            <span className="text-[10px] opacity-40 ml-2">{rels.length} recent</span>
          </div>
          <div className="border-b-3 border-dsi-contrast-background rounded-b-xl bg-dsi-analysis shadow-sm pt-2 pb-2 overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-xs underline opacity-70 text-left">
                  <th className="py-2 px-dsi-pad">Source signal</th>
                  <th className="py-2 px-2">→ Target signal</th>
                  <th className="py-2 px-2">Direction</th>
                  <th className="py-2 px-2 text-right">Correlation</th>
                  <th className="py-2 px-2 text-right">Influence</th>
                  <th className="py-2 px-2 text-right">Population</th>
                  <th className="py-2 px-2">Lifecycle</th>
                  <th className="py-2 px-dsi-pad">Discovered</th>
                </tr>
              </thead>
              <tbody>
                {rels.map((r) => (
                  <tr key={r.id} className="border-t border-dsi-outline/10">
                    <td className="py-2 px-dsi-pad font-mono text-xs">{r.source_signal}</td>
                    <td className="py-2 px-2 font-mono text-xs">{r.target_signal}</td>
                    <td className="py-2 px-2 text-xs">{r.direction.replaceAll("_", " ")}</td>
                    <td className="py-2 px-2 text-right tabular-nums">{formatNumber(r.correlation_rho, 2)}</td>
                    <td className="py-2 px-2 text-right tabular-nums">{formatPercent(r.influence_weight)}</td>
                    <td className="py-2 px-2 text-right tabular-nums">{r.population_size}</td>
                    <td className="py-2 px-2"><StatusBadge status={r.lifecycle_state} /></td>
                    <td className="py-2 px-dsi-pad text-xs opacity-70">{fmtDate(r.created_at)}</td>
                  </tr>
                ))}
                {rels.length === 0 && (
                  <tr>
                    <td colSpan={8} className="py-4 px-dsi-pad opacity-60 text-center text-xs">
                      No relationships discovered yet.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>

        {/* ═══ PORTFOLIO OVERVIEW ═══ */}
        <div className="flex flex-col mb-4">
          <div className="flex gap-dsi-pad rounded-t-xl border-b-1 border-dsi-outline/50 bg-dsi-analysis/60 pl-dsi-pad pt-2 pb-2">
            <Target className="icon"/><span className="text-sm">Portfolio Overview</span>
            <span className="text-[10px] opacity-40 ml-2">{portfolio.count} submissions</span>
          </div>
          <div className="border-b-3 border-dsi-contrast-background rounded-b-xl bg-dsi-analysis shadow-sm pt-4 pb-4 px-dsi-pad">
            <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-6">
              <div className="border border-dsi-outline/20 rounded-lg p-3"><span className="text-xs opacity-60 block mb-1">Total Submissions</span><span className="text-xl font-black text-dsi-selected">{portfolio.count}</span></div>
              <div className="border border-dsi-outline/20 rounded-lg p-3"><span className="text-xs opacity-60 block mb-1">Aggregate Premium</span><span className="text-xl font-black text-dsi-selected">{`${formatNumber(portfolio.totalPremium / 1000000, 1)}M`}</span></div>
              <div className="border border-dsi-outline/20 rounded-lg p-3"><span className="text-xs opacity-60 block mb-1">Average Score</span><span className="text-xl font-black text-dsi-selected">{formatNumber(portfolio.avgScore)}</span></div>
              <div className="border border-dsi-outline/20 rounded-lg p-3"><span className="text-xs opacity-60 block mb-1">Approval Rate</span><span className="text-xl font-black text-dsi-positive">{portfolio.count > 0 ? formatPercent((portfolio.decDist['approve'] || 0) / portfolio.count) : "0%"}</span></div>
              <div className="border border-dsi-outline/20 rounded-lg p-3"><span className="text-xs opacity-60 block mb-1">Referral Rate</span><span className="text-xl font-black text-dsi-warning">{portfolio.count > 0 ? formatPercent((portfolio.decDist['refer'] || 0) / portfolio.count) : "0%"}</span></div>
            </div>
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
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
                        {tierChartData.map((e, i) => <Cell key={i} fill={TIER_COLORS[e.tierNum - 1] || 'var(--dsi-chart-peer)'} />)}
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </div>
              <div>
                <span className="text-xs opacity-60 block mb-2">Sector Concentration</span>
                <div className="space-y-2">
                  {covChartData.slice(0, 6).map((e) => (
                    <div key={e.coverage} className="flex items-center gap-3">
                      <span className="text-xs w-24 truncate opacity-70" title={e.coverage}>{e.coverage}</span>
                      <div className="flex-1 h-4 bg-dsi-background rounded-full overflow-hidden">
                        <div className="h-full rounded-full bg-dsi-selected/40" style={{ width: `${e.pct}%` }} />
                      </div>
                      <span className="text-xs font-bold w-12 text-right">{e.count} ({e.pct}%)</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* ═══ EMERGING SCENARIOS ═══ */}
        <div className="flex flex-col mb-4">
          <div className="flex gap-dsi-pad rounded-t-xl border-b-1 border-dsi-outline/50 bg-dsi-analysis/60 pl-dsi-pad pt-2 pb-2">
            <Radio className="icon text-dsi-warning"/><span className="text-sm">Emerging Scenarios</span>
            <span className="text-[10px] opacity-40 ml-2">Continuously monitored</span>
          </div>
          <div className="border-b-3 border-dsi-contrast-background rounded-b-xl bg-dsi-analysis shadow-sm pt-3 pb-3">
            {emergingScenarios.map((es) => (
              <div key={es.id} className="flex items-center justify-between px-dsi-pad py-2.5 border-b border-dsi-outline/10 hover:bg-dsi-background/20 transition-colors">
                <div className="flex-1 min-w-0 text-wrap">
                  <div className="flex items-center gap-2 mb-0.5">
                    <span className="text-sm font-bold">{es.name}</span>
                    <span className={`text-[10px] font-bold ${LIKELIHOOD_COLOR[es.likelihood_label] || 'opacity-50'}`}>
                      {formatPercent(es.likelihood)} {es.likelihood_label}
                    </span>
                  </div>
                  <p className="text-xs opacity-60 line-clamp-1">{es.description}</p>
                  <div className="flex items-center gap-3 mt-1 text-[10px] opacity-40">
                    <span>Scope: {es.affected_scope}</span>
                    <span>Magnitude: ~{es.estimated_magnitude} pts</span>
                    <span>Horizon: {es.time_horizon}</span>
                    <span>Source: {es.source}</span>
                  </div>
                </div>
                <button
                  onClick={() => applyEmerging(es)}
                  className="shrink-0 ml-4 text-xs text-dsi-selected hover:opacity-70 flex items-center gap-1 border border-dsi-outline/20 px-2 py-1 rounded"
                  title="Simulate this scenario"
                >
                  <Zap className="w-3 h-3" /> Simulate
                </button>
              </div>
            ))}
          </div>
        </div>

        {/* ═══ SHOCK SIMULATOR — multi-shock ═══ */}
        <div className="flex flex-col mb-4">
          <div className="flex justify-between items-center gap-dsi-pad rounded-t-xl border-b-1 border-dsi-outline/50 bg-dsi-analysis/60 pl-dsi-pad pr-dsi-pad pt-2 pb-2">
            <div className="flex items-center gap-dsi-pad">
              <Zap className="icon"/><span className="text-sm">Shock Simulator</span>
              {activeShocks.length > 0 && (
                <span className="text-[10px] bg-dsi-negative/15 text-dsi-negative px-2 py-0.5 rounded font-bold">
                  {activeShocks.length} active
                </span>
              )}
            </div>
            {activeShocks.length > 0 && (
              <button onClick={() => setActiveShocks([])} className="flex items-center gap-1 text-xs text-dsi-selected hover:opacity-70">
                <RotateCcw className="w-3 h-3" /> Clear All
              </button>
            )}
          </div>
          <div className="border-b-3 border-dsi-contrast-background rounded-b-xl bg-dsi-analysis shadow-sm pt-4 pb-4 px-dsi-pad">
            {/* Add shock controls */}
            <div className="grid grid-cols-1 md:grid-cols-5 gap-3 mb-4">
              <div>
                <span className="text-xs opacity-60 block mb-1">Scenario</span>
                <select value={pendingScenario} onChange={(e) => setPendingScenario(e.target.value)} className="w-full bg-dsi-background border border-dsi-outline/30 rounded px-2 py-2 text-sm outline-none focus:border-dsi-selected">
                  {SHOCK_SCENARIOS.map(s => <option key={s.id} value={s.id}>{s.name}</option>)}
                </select>
              </div>
              <div>
                <span className="text-xs opacity-60 block mb-1">Scope</span>
                <select value={pendingScope} onChange={(e) => setPendingScope(e.target.value)} className="w-full bg-dsi-background border border-dsi-outline/30 rounded px-2 py-2 text-sm outline-none focus:border-dsi-selected">
                  <option value="all">All Submissions</option>
                  {coverages.map(c => <option key={c} value={c}>{c}</option>)}
                </select>
              </div>
              <div>
                <span className="text-xs opacity-60 block mb-1">Magnitude: {pendingMagnitude} pts</span>
                <input type="range" min="5" max="50" step="1" value={pendingMagnitude} onChange={(e) => setPendingMagnitude(Number(e.target.value))} className="w-full mt-1" />
              </div>
              <div className="flex items-end">
                <button onClick={addShock} className="w-full bg-dsi-selected text-dsi-background px-3 py-2 rounded font-bold text-sm hover:opacity-90 flex items-center justify-center gap-2">
                  <Plus className="w-4 h-4" /> Add Shock
                </button>
              </div>
              <div className="flex items-end">
                <span className="text-[10px] opacity-40 text-wrap">{SHOCK_SCENARIOS.find(s => s.id === pendingScenario)?.description}</span>
              </div>
            </div>

            {/* Active shocks list */}
            {activeShocks.length > 0 && (
              <div className="flex flex-wrap gap-2 mt-2">
                {activeShocks.map((shock, idx) => (
                  <div key={idx} className="flex items-center gap-2 bg-dsi-negative/10 border border-dsi-negative/20 rounded px-3 py-1.5 text-sm">
                    <Zap className="w-3 h-3 text-dsi-negative" />
                    <span className="font-semibold">{shock.scenario.name}</span>
                    <span className="opacity-50 text-xs">({shock.scope}, -{shock.magnitude}pts)</span>
                    <button onClick={() => removeShock(idx)} className="ml-1 hover:text-dsi-negative"><X className="w-3 h-3" /></button>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* ═══ IMPACT DASHBOARD ═══ */}
        {shockResult && (
          <div className="flex flex-col mb-4">
            <div className="flex gap-dsi-pad rounded-t-xl border-b-1 border-dsi-outline/50 bg-dsi-analysis/60 pl-dsi-pad pt-2 pb-2">
              <AlertTriangle className="icon text-dsi-warning"/>
              <span className="text-sm">Impact Analysis — {shockResult.shocks.length} shock{shockResult.shocks.length !== 1 ? 's' : ''} applied</span>
              <span className="text-[10px] opacity-40 ml-2">{shockResult.total_affected} of {submissions.length} affected</span>
            </div>
            <div className="border-b-3 border-dsi-contrast-background rounded-b-xl bg-dsi-analysis shadow-sm pt-4 pb-4 px-dsi-pad">
              {/* Impact KPIs */}
              <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-6">
                <div className="border border-dsi-outline/20 rounded-lg p-3"><span className="text-xs opacity-60 block mb-1">Risks Affected</span><span className="text-xl font-black text-dsi-warning">{shockResult.total_affected}</span></div>
                <div className="border border-dsi-outline/20 rounded-lg p-3"><span className="text-xs opacity-60 block mb-1">Tier Migrations</span><span className="text-xl font-black text-dsi-negative">{shockResult.tier_migrations}</span></div>
                <div className="border border-dsi-outline/20 rounded-lg p-3"><span className="text-xs opacity-60 block mb-1">Decision Changes</span><span className="text-xl font-black text-dsi-negative">{shockResult.decision_changes}</span></div>
                <div className="border border-dsi-outline/20 rounded-lg p-3"><span className="text-xs opacity-60 block mb-1">Premium Impact</span><span className={`text-xl font-black ${shockResult.premium_delta > 0 ? 'text-dsi-negative' : 'text-dsi-positive'}`}>{`${shockResult.premium_delta > 0 ? '+' : ''}${formatNumber(shockResult.premium_delta / 1000)}K`}</span></div>
                <div className="border border-dsi-outline/20 rounded-lg p-3"><span className="text-xs opacity-60 block mb-1">Premium Change</span><span className={`text-xl font-black ${shockResult.premium_delta > 0 ? 'text-dsi-negative' : 'text-dsi-positive'}`}>{shockResult.aggregate_premium_before > 0 ? `${shockResult.premium_delta > 0 ? '+' : ''}${formatPercent(shockResult.premium_delta / shockResult.aggregate_premium_before, 1)}` : 'N/A'}</span></div>
              </div>

              {/* Before/After charts */}
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
                          {tierChartData.map((e, i) => <Cell key={i} fill={TIER_COLORS[e.tierNum - 1] || 'var(--dsi-chart-peer)'} />)}
                        </Bar>
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                </div>
                <div>
                  <span className="text-xs opacity-60 block mb-2">Tier Distribution — After {shockResult.shocks.length} Shock{shockResult.shocks.length !== 1 ? 's' : ''}</span>
                  <div className="h-[180px]">
                    <ResponsiveContainer width="100%" height="100%">
                      <BarChart data={afterTierData} margin={{ top: 5, right: 10, bottom: 5, left: -20 }}>
                        <CartesianGrid strokeDasharray="3 3" stroke="var(--dsi-chart-grid)" opacity={0.3} />
                        <XAxis dataKey="tier" stroke="var(--dsi-chart-axis)" tick={{ fill: 'var(--dsi-chart-axis)', fontSize: 11 }} />
                        <YAxis stroke="var(--dsi-chart-axis)" tick={{ fill: 'var(--dsi-chart-axis)', fontSize: 11 }} />
                        <RechartsTooltip contentStyle={tooltipStyle} />
                        <Bar dataKey="count" radius={[4, 4, 0, 0]}>
                          {afterTierData.map((e, i) => <Cell key={i} fill={TIER_COLORS[e.tierNum - 1] || 'var(--dsi-chart-peer)'} />)}
                        </Bar>
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                </div>
              </div>

              {/* Most Affected */}
              <span className="text-xs opacity-60 block mb-2">Most Affected Submissions</span>
              <div className="overflow-x-auto">
                <table className="w-full text-sm text-left whitespace-nowrap">
                  <thead>
                    <tr className="text-xs underline opacity-70">
                      <th className="py-2 pr-2">Entity</th>
                      <th className="py-2 px-2 text-right">Before</th>
                      <th className="py-2 px-2 text-center"><ArrowRight className="w-3 h-3 inline" /></th>
                      <th className="py-2 px-2 text-right">After</th>
                      <th className="py-2 px-2 text-right">Delta</th>
                      <th className="py-2 px-2 text-center">Tier</th>
                      <th className="py-2 px-2 text-center">Decision</th>
                      <th className="py-2 px-2 text-right">Premium</th>
                      <th className="py-2 px-2">Shocks</th>
                    </tr>
                  </thead>
                  <tbody>
                    {shockResult.affected.slice(0, 15).map((item, idx) => (
                      <tr key={idx} onClick={() => fetchCoreSubmissionDetail(item.original)} className={`border-b border-dsi-outline/5 cursor-pointer hover:bg-dsi-background/20 ${item.tier_changed ? 'bg-dsi-negative/5' : ''}`}>
                        <td className="py-2 pr-2 font-semibold">{item.original.entity_name}</td>
                        <td className="py-2 px-2 text-right">{formatNumber(item.original_score, 0)}</td>
                        <td className="py-2 px-2 text-center opacity-30">→</td>
                        <td className="py-2 px-2 text-right text-dsi-negative font-bold">{formatNumber(item.shocked_score, 0)}</td>
                        <td className="py-2 px-2 text-right text-dsi-negative">{item.score_delta}</td>
                        <td className="py-2 px-2 text-center">
                          {item.tier_changed
                            ? <span className="text-dsi-negative font-bold">T{item.original_tier}→T{item.shocked_tier}</span>
                            : <span className="opacity-50">T{item.original_tier}</span>}
                        </td>
                        <td className="py-2 px-2 text-center">
                          {item.decision_changed
                            ? <span className="text-dsi-negative font-bold">{item.original_decision}→{item.shocked_decision}</span>
                            : <span className="opacity-50">{item.original_decision}</span>}
                        </td>
                        <td className="py-2 px-2 text-right">
                          {item.premium_delta !== 0
                            ? <span className={item.premium_delta > 0 ? 'text-dsi-negative' : 'text-dsi-positive'}>{item.premium_delta > 0 ? '+' : ''}{formatCurrency(item.premium_delta)}</span>
                            : <span className="opacity-30">—</span>}
                        </td>
                        <td className="py-2 px-2 text-xs opacity-50 truncate max-w-[150px]" title={item.shocks_applied.join(', ')}>
                          {item.shocks_applied.length}×
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
                {shockResult.affected.length > 15 && (
                  <p className="text-xs opacity-40 mt-2">Showing top 15 of {shockResult.affected.length} affected.</p>
                )}
              </div>
            </div>
          </div>
        )}

      </div>
    </ViewCanvas>
  );
}

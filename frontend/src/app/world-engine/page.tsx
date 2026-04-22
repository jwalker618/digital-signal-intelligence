"use client";

import { useState, useMemo, useEffect } from "react";
import { useDsiStore } from "@/store/dsiStore";
import ViewCanvas from "@/components/ViewCanvas";
import { 
  CardGrid, 
  StandardCard } from "@/components/base/cards";

import {
  Orbit, Zap, AlertTriangle,
  Plus, X, Radio, Link, ChartCandlestick, Eye,
} from "lucide-react";

import { SHOCK_SCENARIOS, ActiveShock, applyMultipleShocks, generateEmergingScenarios, ShockResult } from "@/lib/shockEngine";
import { formatNumber, formatCurrency, formatPercent, formatText, formatTimeRelative, formatDate } from "@/lib/format";

import { api, } from "@/lib/api";
import { StatusBadge } from "@/components/shared/StatusBadge";
import {
  DistributionBarChart,
  HorizontalBarList,
} from "@/components/base/charts/primatives";

import type {
  DiscoveredRelationship,
  DriftAlert,
  MaturityState,
  WorldEngineStats,
} from "@/types/worldEngine";

const TIER_COLORS = ['var(--dsi-approve)', 'var(--dsi-info)', 'var(--dsi-refer)', 'var(--dsi-decline)', 'var(--dsi-decline)'];

const LIKELIHOOD_COLOR: Record<string, string> = {
  'High': 'text-dsi-decline',
  'Elevated': 'text-dsi-refer',
  'Moderate': 'text-dsi-refer',
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
      <CardGrid cols="grid-cols-1" className="w-full no-scrollbar animate-in fade-in duration-500 pb-12 pt-dsi-pad">

        {/* ═══ WORLD MODEL ═══ */}
        <StandardCard
          title="World Engine"
          lucideIcon={Orbit}
          headerRight={
            <span className="text-xs content-center">
              ({maturity ? `${maturity.assessed_entity_count} entities` : "No data"})
            </span>
          }
        >
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            
            <div className="dsi-contentbox flex flex-col">

              <span className="dsi-analysis-description text-center">Maturity Stage</span>
              <span className="dsi-analysis-item text-center text-xl">{maturity?.stage ?? "—"}</span>
              
              {maturity && (
                <span className="dsi-analysis-item text-xs font-normal text-center">
                  {formatNumber(maturity.time_depth_months, 1)} months of data
                </span>
              )}
            </div>

            <div className="dsi-contentbox flex flex-col">

              <span className="dsi-analysis-description text-center">Active Relationships</span>
              <span className="dsi-analysis-item text-center text-xl">{weStats?.relationships_by_state?.active ?? maturity?.active_relationships ?? "—"}
              </span>
              {maturity && (
                <span className="dsi-analysis-item text-xs font-normal text-center">
                  {maturity.provisional_relationships} provisional &middot; {maturity.candidate_relationships} candidate
                </span>
              )}
            </div>
            
            <div className="dsi-contentbox flex flex-col">

              <span className="dsi-analysis-description text-center">Open Drift Alerts</span>
              <span className={`dsi-analysis-item text-center text-xl ${weStats && weStats.drift_alerts_unacknowledged > 0 ? "text-dsi-decline" : "text-dsi-contrast-background"}`}>
                {weStats?.drift_alerts_unacknowledged ?? "—"}
              </span>
            </div>
            
            <div className="dsi-contentbox flex flex-col">

              <span className="dsi-analysis-description text-center">Assessed Entities</span>
              <span className="dsi-analysis-item text-center text-xl">{maturity?.assessed_entity_count ?? "—"}</span>
              {maturity && (
                <span className="dsi-analysis-item text-xs font-normal text-center">
                  {maturity.entities_with_temporal_data} with history
                </span>
              )}
            </div>
          </div>
        </StandardCard>

        {/* ═══ OPEN DRIFT ALERTS ═══ */}
        <StandardCard
          title="Open Drift Alerts"
          lucideIcon={Eye}
          headerRight={<span className="text-xs content-center">{alerts.length} open</span>}
        >
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="dsi-grid-table-header text-dsi-contrast-background text-wrap">
                  <th className="p-1.5 text-left">Signal</th>
                  <th className="p-1.5 text-left">Severity</th>
                  <th className="p-1.5 text-left">Type</th>
                  <th className="p-1.5 text-center">Detected</th>
                  <th className="p-1.5 text-left">Summary</th>
                  <th className="p-1.5 text-right"></th>
                </tr>
              </thead>
              <tbody>
                {alerts.map((a) => (
                  <tr key={a.id} className="cursor-pointer text-dsi-contrast-background hover:text-dsi-selected">
                    <td className="p-1.5 text-left">{formatText(a.source_signal ?? "—","capitalize")}</td>
                    <td className="p-1.5 text-left"><StatusBadge status={formatText(a.severity,"capitalize")} /></td>
                    <td className="p-1.5 text-left">{formatText(a.alert_type,"capitalize")}</td>
                    <td className="p-1.5 text-center">{formatTimeRelative(a.detected_at)}</td>
                    <td className="p-1.5 text-left">{formatText(a.description,"capitalize")}</td>
                    <td className="p-1.5 text-right">
                      
                      <button
                        onClick={() => void acknowledgeAlert(a.id)}
                        disabled={ackBusy === a.id}
                        className="dsi-actionbutton content-end"
                      >
                        Acknowledge
                      </button>

                    </td>
                  </tr>
                ))}
                {alerts.length === 0 && (
                  <tr>
                    <td colSpan={6} className="dsi-user-message">
                      No open alerts.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </StandardCard>

        {/* ═══ DISCOVERED RELATIONSHIPS ═══ */}
        <StandardCard
          title="Discovered Relationships"
          lucideIcon={Link}
          headerRight={<span className="text-xs content-center">{rels.length} recent</span>}
        >
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="dsi-grid-table-header text-dsi-contrast-background text-wrap">
                  <th className="p-1.5 text-left">Source signal</th>
                  <th className="p-1.5 text-left">Target signal</th>
                  <th className="p-1.5 text-left">Direction</th>
                  <th className="p-1.5 text-center">Correlation</th>
                  <th className="p-1.5 text-center">Influence</th>
                  <th className="p-1.5 text-center">Population</th>
                  <th className="p-1.5 text-left">Lifecycle</th>
                  <th className="p-1.5 text-center">Discovered</th>
                </tr>
              </thead>
              <tbody>
                {rels.map((r) => (
                  <tr key={r.id} className="cursor-pointer text-dsi-contrast-background hover:text-dsi-selected">
                    <td className="p-1.5 text-left">{formatText(r.source_signal,"capitalize")}</td>
                    <td className="p-1.5 text-left">{formatText(r.target_signal,"capitalize")}</td>
                    <td className="p-1.5 text-left">{formatText(r.direction.replaceAll("_", " "),"capitalize")}</td>
                    <td className="p-1.5 text-center tabular-nums">{formatNumber(r.correlation_rho, 2)}</td>
                    <td className="p-1.5 text-center tabular-nums">{formatPercent(r.influence_weight)}</td>
                    <td className="p-1.5 text-center tabular-nums">{r.population_size}</td>
                    <td className="p-1.5 text-left"><StatusBadge status={formatText(r.lifecycle_state,"capitalize")} /></td>
                    <td className="p-1.5 text-center">{formatDate(r.created_at)}</td>
                  </tr>
                ))}
                {rels.length === 0 && (
                  <tr>
                    <td colSpan={8} className="dsi-user-message">
                      No relationships discovered yet.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </StandardCard>

        {/* ═══ PORTFOLIO OVERVIEW ═══ */}
        <StandardCard
          title="Portfolio Overview"
          lucideIcon={ChartCandlestick}
          headerRight={<span className="text-xs content-center">{portfolio.count} submissions</span>}
        >
          <div>
            <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-6">
              <div className="dsi-contentbox flex flex-col">
                <span className="dsi-analysis-description text-center">Total Submissions</span>
                <span className="dsi-analysis-item text-center text-xl">{formatNumber(portfolio.count)}</span>
                </div>
              <div className="dsi-contentbox flex flex-col">
                <span className="dsi-analysis-description text-center">Aggregate Premium</span>
                <span className="dsi-analysis-item text-center text-xl">{`${formatNumber(portfolio.totalPremium / 1000000, 1)}M`}</span>
                </div>
              <div className="dsi-contentbox flex flex-col">
                <span className="dsi-analysis-description text-center">Average Score</span>
                <span className="dsi-analysis-item text-center text-xl">{formatNumber(portfolio.avgScore)}</span>
                </div>
              <div className="dsi-contentbox flex flex-col">
                <span className="dsi-analysis-description text-center">Approval Rate</span>
                <span className="dsi-analysis-item text-center text-xl">{portfolio.count > 0 ? formatPercent((portfolio.decDist['approve'] || 0) / portfolio.count) : "0%"}</span>
                </div>
              <div className="dsi-contentbox flex flex-col">
                <span className="dsi-analysis-description text-center">Referral Rate</span>
                <span className="dsi-analysis-item text-center text-xl">{portfolio.count > 0 ? formatPercent((portfolio.decDist['refer'] || 0) / portfolio.count) : "0%"}</span>
                </div>
            </div>
            
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              
              <div>
                <span className="text-xs opacity-60 block mb-2">Tier Distribution</span>
                <DistributionBarChart
                  data={tierChartData}
                  categoryKey="tier"
                  valueKey="count"
                  colorFor={(e: any) => TIER_COLORS[e.tierNum - 1] || 'var(--dsi-analysis)'}
                  valueName="Count"
                  height={200}
                />
              </div>
              <div>

                <span className="text-xs opacity-60 block mb-2">Sector Concentration</span>
                <HorizontalBarList
                  limit={6}
                  rows={covChartData.map((e) => ({
                    label: e.coverage,
                    percent: Number(e.pct),
                    valueLabel: `${e.count} (${e.pct}%)`,
                  }))}
                />
              </div>
            </div>
          </div>
        </StandardCard>

        {/* ═══ EMERGING SCENARIOS ═══ */}
        <StandardCard
          title="Emerging Scenarios"
          lucideIcon={Radio}
          headerRight={<span className="text-xs content-center">Continuously monitored</span>}
        >
          <div>
            {emergingScenarios.map((es) => (
              
              <div key={es.id} className="flex items-center justify-between py-2.5 border-b border-dsi-outline/10 hover:text-dsi-selected">
                <div className="flex-1 min-w-0 text-wrap">
                  <div className="flex items-center gap-2 mb-0.5">
                    
                    <span className="text-sm font-bold">{formatText(es.name,"upper")}</span>
                    <span className={`dsi-notificationpill p-1 border-none shadow-none ${LIKELIHOOD_COLOR[es.likelihood_label] || ''}`}>
                      {formatPercent(es.likelihood)} {es.likelihood_label}
                    </span>

                  </div>
                  
                  <div className="flex items-center gap-3 mt-2 text-xs">
                    <span>Scope: {es.affected_scope}</span>
                    <span>Magnitude: ~{es.estimated_magnitude} pts</span>
                    <span>Horizon: {es.time_horizon}</span>
                    <span>Source: {es.source}</span>
                  </div>
                  
                </div>
                
                <button
                  onClick={() => applyEmerging(es)}
                  className="dsi-actionbutton flex gap-2"
                  title="Simulate this scenario"
                ><Zap className="icon" /> Simulate
                </button>

              </div>
            ))}
          </div>
        </StandardCard>

        {/* ═══ SHOCK SIMULATOR — multi-shock ═══ */}
        <StandardCard
          title="Shock Simulator"
          lucideIcon={Zap}
          headerRight={
            <div className="flex items-center gap-dsi-pad">
              {activeShocks.length > 0 && (
                <span className="text-xs content-center">
                  {activeShocks.length} active
                </span>
              )}
            </div>
          }
        >
          <div>
            {/* Add shock controls */}
            <div className="grid grid-cols-1 md:grid-cols-5 gap-3 mb-4">
              <div>
                
                <span className="dsi-analysis-description text-center">Scenario</span>
                
                <select 
                  value={pendingScenario} 
                  onChange={(e) => setPendingScenario(e.target.value)} 
                  className="
                    w-full 
                    bg-dsi-background mt-2
                    rounded-md p-1.5 text-sm">
                  {SHOCK_SCENARIOS.map(s => <option key={s.id} value={s.id}>{s.name}</option>)}
                </select>

              </div>
              <div>
                
                <span className="dsi-analysis-description text-center">Scope</span>

                <select 
                  value={pendingScope} 
                  onChange={(e) => setPendingScope(e.target.value)} 
                  className="
                    w-full 
                    bg-dsi-background mt-2
                    rounded-md p-1.5 text-sm">
                  <option value="all">All Submissions</option>
                  {coverages.map(c => <option key={c} value={c}>{c}</option>)}
                </select>

              </div>
              
              <div>
                <span className="dsi-analysis-description text-center">Magnitude: {pendingMagnitude} pts</span>
                <input 
                  type="range" min="5" max="50" step="1" 
                  value={pendingMagnitude} 
                  onChange={(e) => setPendingMagnitude(Number(e.target.value))} 
                  className="w-full mt-1 justify-center content-center items-center" />
              </div>

              <div className="flex items-end">
                <button onClick={addShock} className="w-full dsi-actionbutton">
                  <Plus className="icon" /> Add Shock
                </button>
              </div>

              <div className="flex items-end">
                <span className="text-xs text-wrap">{SHOCK_SCENARIOS.find(s => s.id === pendingScenario)?.description}</span>
              </div>

            </div>

            {/* Active shocks list */}
            {activeShocks.length > 0 && (
              <div className="flex flex-wrap gap-2 mt-2">
                {activeShocks.map((shock, idx) => (
                  <div key={idx} className="flex items-center gap-2 bg-dsi-decline/10 border border-dsi-decline/20 rounded px-3 py-1.5 text-sm">
                    <Zap className="w-3 h-3 text-dsi-decline" />
                    <span className="font-semibold">{shock.scenario.name}</span>
                    <span className="opacity-50 text-xs">({shock.scope}, -{shock.magnitude}pts)</span>
                    <button onClick={() => removeShock(idx)} className="ml-1 hover:text-dsi-decline"><X className="w-3 h-3" /></button>
                  </div>
                ))}
              </div>
            )}
          </div>
        </StandardCard>

        {/* ═══ IMPACT DASHBOARD ═══ */}
        {shockResult && (
          <StandardCard
            title={`Impact Analysis — ${shockResult.shocks.length} shock${shockResult.shocks.length !== 1 ? 's' : ''} applied`}
            lucideIcon={AlertTriangle}
            headerRight={
              <span className="text-xs content-center">
                {shockResult.total_affected} of {submissions.length} affected
              </span>
            }
          >
            <div>
              {/* Impact KPIs */}
              <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-6">
                
                <div className="dsi-contentbox flex flex-col">
                  <span className="dsi-analysis-description text-center">Risks Affected</span>
                  <span className="dsi-analysis-item text-center text-xl">{shockResult.total_affected}</span></div>
                
                <div className="dsi-contentbox flex flex-col">
                  <span className="dsi-analysis-description text-center">Tier Migrations</span>
                  <span className="dsi-analysis-item text-center text-xl">{shockResult.tier_migrations}</span></div>
                
                <div className="dsi-contentbox flex flex-col">
                  <span className="dsi-analysis-description text-center">Decision Changes</span>
                  <span className="dsi-analysis-item text-center text-xl">{shockResult.decision_changes}</span></div>
                
                <div className="dsi-contentbox flex flex-col">
                  <span className="dsi-analysis-description text-center">Premium Impact</span>
                  <span className="dsi-analysis-item text-center text-xl"> {shockResult.premium_delta > 0 ? '+' : ''}${formatNumber(shockResult.premium_delta / 1000)}K</span>
                </div>
                
                <div className="dsi-contentbox flex flex-col">
                  <span className="dsi-analysis-description text-center">Premium Change</span>
                  <span className="dsi-analysis-item text-center text-xl"> {shockResult.aggregate_premium_before > 0 ? `${shockResult.premium_delta > 0 ? '+' : ''}${formatPercent(shockResult.premium_delta / shockResult.aggregate_premium_before, 1)}` : 'N/A'}</span>
                </div>
              </div>

              {/* Before/After charts */}
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
                <div>
                  <span className="text-xs opacity-60 block mb-2">Tier Distribution — Before</span>
                  <DistributionBarChart
                    data={tierChartData}
                    categoryKey="tier"
                    valueKey="count"
                    colorFor={(e: any) => TIER_COLORS[e.tierNum - 1] || 'var(--dsi-analysis)'}
                    valueName="Count"
                    height={180}
                  />
                </div>
                <div>
                  <span className="text-xs opacity-60 block mb-2">Tier Distribution — After {shockResult.shocks.length} Shock{shockResult.shocks.length !== 1 ? 's' : ''}</span>
                  <DistributionBarChart
                    data={afterTierData}
                    categoryKey="tier"
                    valueKey="count"
                    colorFor={(e: any) => TIER_COLORS[e.tierNum - 1] || 'var(--dsi-analysis)'}
                    valueName="Count"
                    height={180}
                  />
                </div>
              </div>

              {/* Most Affected */}
              
              <span className="text-xs">Most Affected Submissions</span>
              <div className="overflow-x-auto">
                <table className="w-full text-sm text-left whitespace-nowrap">
                  <thead>
                    <tr className="dsi-grid-table-header text-dsi-contrast-background text-wrap">
                      <th className="p-1.5 text-left">Entity</th>
                      <th className="p-1.5 text-center">Before</th>
                      <th className="p-1.5 text-center">After</th>
                      <th className="p-1.5 text-center">Delta</th>
                      <th className="p-1.5 text-center">Tier</th>
                      <th className="p-1.5 text-center">Decision</th>
                      <th className="p-1.5 text-center">Premium</th>
                      <th className="p-1.5 text-center">Shocks</th>
                    </tr>
                  </thead>
                  <tbody>
                    {shockResult.affected.slice(0, 15).map((item, idx) => (
                      
                      <tr key={idx} onClick={() => fetchCoreSubmissionDetail(item.original)} className={`cursor-pointer text-dsi-contrast-background hover:text-dsi-selected ${item.tier_changed ? 'bg-dsi-decline/5' : ''}`}>
                        <td className="p-1.5 text-left">{formatText(item.original.entity_name,"upper")}</td>
                        <td className="p-1.5 text-center">{formatNumber(item.original_score, 0)}</td>
                        <td className="p-1.5 text-center">{formatNumber(item.shocked_score, 0)}</td>
                        <td className="p-1.5 text-center">{item.score_delta}</td>
                        <td className="p-1.5 text-center">
                          {item.tier_changed
                            ? <span className="font-bold">T{item.original_tier}→T{item.shocked_tier}</span>
                            : <span>T{item.original_tier}</span>}
                        </td>
                        <td className="p-1.5 text-center">
                          {item.decision_changed
                            ? <span className="font-bold">{formatText(item.original_decision,"upper")}→{formatText(item.shocked_decision,"upper")}</span>
                            : <span>{formatText(item.original_decision,"upper")}</span>}
                        </td>
                        <td className="p-1.5 text-right pr-dsi-pad">
                          {item.premium_delta !== 0
                            ? <span className="font-bold">{item.premium_delta > 0 ? '+' : ''}{formatCurrency(item.premium_delta)}</span>
                            : <span>—</span>}
                        </td>
                        <td className="p-1.5 text-center" title={item.shocks_applied.join(', ')}>
                          {item.shocks_applied.length}×
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
                {shockResult.affected.length > 15 && (
                  <p className="text-xs mt-dsi-pad">Showing top 15 of {shockResult.affected.length} affected.</p>
                )}
              </div>
            </div>
          </StandardCard>
        )}

      </CardGrid>
    </ViewCanvas>
  );
}

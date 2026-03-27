/**
 * shockEngine.ts — Pure functions for portfolio-level shock simulation.
 * Supports multiple simultaneous shocks and emerging scenario generation.
 */

export interface ShockScenario {
  id: string;
  name: string;
  description: string;
  magnitude: number;
}

export const SHOCK_SCENARIOS: ShockScenario[] = [
  { id: 'cve', name: 'Critical Vulnerability (CVE)', description: 'Zero-day affects primary cloud provider. Degrades technical infrastructure signals.', magnitude: 25 },
  { id: 'leadership', name: 'Key Personnel Departure', description: 'CISO or CTO resigns unexpectedly. Degrades corporate governance signals.', magnitude: 20 },
  { id: 'regulatory', name: 'Regulatory Action', description: 'New compliance requirement imposed with 90-day deadline.', magnitude: 30 },
  { id: 'supply_chain', name: 'Supply Chain Disruption', description: 'Key vendor experiences major outage or breach.', magnitude: 22 },
  { id: 'market', name: 'Market Downturn', description: 'Sector-wide financial stress reduces operational resilience.', magnitude: 15 },
  { id: 'peer_breach', name: 'Data Breach (Industry Peer)', description: 'Major competitor suffers high-profile data breach. Increased threat landscape.', magnitude: 18 },
];

export interface ActiveShock {
  scenario: ShockScenario;
  scope: string;
  magnitude: number;
}

export interface ShockedSubmission {
  original: any;
  shocked_score: number;
  original_score: number;
  score_delta: number;
  original_tier: number;
  shocked_tier: number;
  tier_changed: boolean;
  original_decision: string;
  shocked_decision: string;
  decision_changed: boolean;
  premium_delta: number;
  shocks_applied: string[]; // which shocks hit this submission
}

export interface ShockResult {
  shocks: ActiveShock[];
  affected: ShockedSubmission[];
  unaffected: any[];
  total_affected: number;
  total_unaffected: number;
  tier_migrations: number;
  decision_changes: number;
  aggregate_premium_before: number;
  aggregate_premium_after: number;
  premium_delta: number;
  tier_dist_before: Record<number, number>;
  tier_dist_after: Record<number, number>;
}

function tierFromScore(score: number): { tier: number; decision: string } {
  if (score >= 800) return { tier: 1, decision: 'approve' };
  if (score >= 650) return { tier: 2, decision: 'approve' };
  if (score >= 500) return { tier: 3, decision: 'refer' };
  if (score >= 350) return { tier: 4, decision: 'refer' };
  return { tier: 5, decision: 'decline' };
}

function premiumForTier(basePremium: number, originalTier: number, newTier: number): number {
  const tierMultipliers: Record<number, number> = { 1: 0.7, 2: 0.85, 3: 1.0, 4: 1.25, 5: 1.6 };
  const origMult = tierMultipliers[originalTier] || 1.0;
  const newMult = tierMultipliers[newTier] || 1.0;
  return basePremium * (newMult / origMult);
}

/**
 * Apply multiple shocks simultaneously. Each shock degrades scores
 * for submissions within its scope. Shocks stack additively.
 */
export function applyMultipleShocks(
  submissions: any[],
  shocks: ActiveShock[]
): ShockResult {
  const affected: ShockedSubmission[] = [];
  const unaffected: any[] = [];
  const tierDistBefore: Record<number, number> = {};
  const tierDistAfter: Record<number, number> = {};

  for (const sub of submissions) {
    const score = sub.pure_composite_score ?? 0;
    const tier = sub.final_tier ?? tierFromScore(score).tier;
    const premium = sub.recommended_premium ?? 0;
    const cov = (sub.coverage_configuration || '').toLowerCase();

    tierDistBefore[tier] = (tierDistBefore[tier] || 0) + 1;

    // Determine total degradation from all applicable shocks
    let totalDegradation = 0;
    const appliedShockNames: string[] = [];

    for (const shock of shocks) {
      const inScope = shock.scope === 'all' || cov.includes(shock.scope.toLowerCase());
      if (inScope) {
        totalDegradation += shock.magnitude;
        appliedShockNames.push(shock.scenario.name);
      }
    }

    if (totalDegradation === 0) {
      unaffected.push(sub);
      tierDistAfter[tier] = (tierDistAfter[tier] || 0) + 1;
      continue;
    }

    const shockedScore = Math.max(0, score - totalDegradation);
    const shockedResult = tierFromScore(shockedScore);
    const shockedPremium = premiumForTier(premium, tier, shockedResult.tier);

    tierDistAfter[shockedResult.tier] = (tierDistAfter[shockedResult.tier] || 0) + 1;

    affected.push({
      original: sub,
      shocked_score: Math.round(shockedScore * 10) / 10,
      original_score: score,
      score_delta: Math.round((shockedScore - score) * 10) / 10,
      original_tier: tier,
      shocked_tier: shockedResult.tier,
      tier_changed: shockedResult.tier !== tier,
      original_decision: (sub.decision || 'unknown').toLowerCase(),
      shocked_decision: shockedResult.decision,
      decision_changed: shockedResult.decision !== (sub.decision || 'unknown').toLowerCase(),
      premium_delta: Math.round(shockedPremium - premium),
      shocks_applied: appliedShockNames,
    });
  }

  const aggPremBefore = affected.reduce((s, a) => s + (a.original.recommended_premium || 0), 0);
  const aggPremAfter = affected.reduce((s, a) => s + (a.original.recommended_premium || 0) + a.premium_delta, 0);

  return {
    shocks,
    affected: affected.sort((a, b) => a.score_delta - b.score_delta),
    unaffected,
    total_affected: affected.length,
    total_unaffected: unaffected.length,
    tier_migrations: affected.filter(a => a.tier_changed).length,
    decision_changes: affected.filter(a => a.decision_changed).length,
    aggregate_premium_before: aggPremBefore,
    aggregate_premium_after: aggPremAfter,
    premium_delta: Math.round(aggPremAfter - aggPremBefore),
    tier_dist_before: tierDistBefore,
    tier_dist_after: tierDistAfter,
  };
}

// ─── Emerging Scenarios ──────────────────────────────────────────────────────

export interface EmergingScenario {
  id: string;
  name: string;
  description: string;
  likelihood: number; // 0-1
  likelihood_label: string;
  affected_scope: string;
  estimated_magnitude: number;
  time_horizon: string;
  source: string;
}

/**
 * Generate emerging scenarios based on portfolio composition.
 * These simulate what a continuous monitoring engine would surface.
 */
export function generateEmergingScenarios(submissions: any[]): EmergingScenario[] {
  const covCounts: Record<string, number> = {};
  const tierCounts: Record<number, number> = {};
  let totalPremium = 0;
  let avgScore = 0;

  for (const sub of submissions) {
    const cov = (sub.coverage_configuration || '').split(' / ')[0];
    covCounts[cov] = (covCounts[cov] || 0) + 1;
    const tier = sub.final_tier || 0;
    tierCounts[tier] = (tierCounts[tier] || 0) + 1;
    totalPremium += sub.recommended_premium || 0;
    avgScore += sub.pure_composite_score || 0;
  }
  avgScore = submissions.length > 0 ? avgScore / submissions.length : 0;

  const total = submissions.length || 1;
  const scenarios: EmergingScenario[] = [];

  // Find dominant coverage
  const sortedCovs = Object.entries(covCounts).sort((a, b) => b[1] - a[1]);
  const dominantCov = sortedCovs[0];

  if (dominantCov && dominantCov[1] / total > 0.25) {
    scenarios.push({
      id: 'concentration_risk',
      name: `${dominantCov[0]} Concentration Risk`,
      description: `${((dominantCov[1] / total) * 100).toFixed(0)}% of portfolio concentrated in ${dominantCov[0]}. A sector-wide event would disproportionately impact the book.`,
      likelihood: 0.35 + Math.random() * 0.3,
      likelihood_label: 'Moderate',
      affected_scope: dominantCov[0],
      estimated_magnitude: 20,
      time_horizon: '6-12 months',
      source: 'Concentration Analysis',
    });
  }

  // High tier 4/5 count
  const weakRisks = (tierCounts[4] || 0) + (tierCounts[5] || 0);
  if (weakRisks > total * 0.15) {
    scenarios.push({
      id: 'tail_risk_cluster',
      name: 'Tail Risk Cluster Deterioration',
      description: `${weakRisks} submissions (${((weakRisks / total) * 100).toFixed(0)}%) in Tier 4-5. Correlated deterioration could trigger multiple claims simultaneously.`,
      likelihood: 0.2 + Math.random() * 0.25,
      likelihood_label: 'Elevated',
      affected_scope: 'all',
      estimated_magnitude: 15,
      time_horizon: '3-6 months',
      source: 'Tail Risk Monitor',
    });
  }

  // Regulatory landscape
  scenarios.push({
    id: 'regulatory_tightening',
    name: 'Regulatory Tightening Wave',
    description: 'Emerging global regulatory frameworks (NIS2, SEC cyber rules, DORA) expected to increase compliance burdens across the portfolio.',
    likelihood: 0.6 + Math.random() * 0.2,
    likelihood_label: 'High',
    affected_scope: 'all',
    estimated_magnitude: 18,
    time_horizon: '3-9 months',
    source: 'Regulatory Intelligence',
  });

  // Technology supply chain
  if (covCounts['Cyber'] > 0 || covCounts['Technology'] > 0) {
    scenarios.push({
      id: 'cloud_provider_incident',
      name: 'Major Cloud Provider Incident',
      description: 'Elevated threat indicators suggest increased probability of significant cloud infrastructure disruption affecting multiple portfolio entities.',
      likelihood: 0.15 + Math.random() * 0.2,
      likelihood_label: 'Low-Moderate',
      affected_scope: sortedCovs.find(([c]) => c.includes('Cyber') || c.includes('Tech'))?.[0] || 'all',
      estimated_magnitude: 28,
      time_horizon: '1-3 months',
      source: 'Threat Intelligence',
    });
  }

  // AI disruption
  scenarios.push({
    id: 'ai_liability_emergence',
    name: 'AI Liability Claims Emergence',
    description: 'Growing adoption of AI tools creates new liability vectors. Early claims signals detected across professional indemnity and D&O exposures.',
    likelihood: 0.25 + Math.random() * 0.2,
    likelihood_label: 'Moderate',
    affected_scope: 'all',
    estimated_magnitude: 12,
    time_horizon: '6-18 months',
    source: 'Emerging Risk Analysis',
  });

  // Sort by likelihood descending
  return scenarios.sort((a, b) => b.likelihood - a.likelihood);
}

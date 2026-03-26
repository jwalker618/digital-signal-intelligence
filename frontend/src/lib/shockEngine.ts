/**
 * shockEngine.ts — Pure functions for portfolio-level shock simulation.
 *
 * Takes pipeline submissions, applies a shock scenario to a filtered scope,
 * and returns before/after comparison data.
 */

export interface ShockScenario {
  id: string;
  name: string;
  description: string;
  magnitude: number; // points to degrade composite score
}

export const SHOCK_SCENARIOS: ShockScenario[] = [
  { id: 'cve', name: 'Critical Vulnerability (CVE)', description: 'Zero-day affects primary cloud provider. Degrades technical infrastructure signals.', magnitude: 25 },
  { id: 'leadership', name: 'Key Personnel Departure', description: 'CISO or CTO resigns unexpectedly. Degrades corporate governance signals.', magnitude: 20 },
  { id: 'regulatory', name: 'Regulatory Action', description: 'New compliance requirement imposed with 90-day deadline.', magnitude: 30 },
  { id: 'supply_chain', name: 'Supply Chain Disruption', description: 'Key vendor experiences major outage or breach.', magnitude: 22 },
  { id: 'market', name: 'Market Downturn', description: 'Sector-wide financial stress reduces operational resilience.', magnitude: 15 },
  { id: 'peer_breach', name: 'Data Breach (Industry Peer)', description: 'Major competitor suffers high-profile data breach. Increased threat landscape.', magnitude: 18 },
];

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
}

export interface ShockResult {
  scenario: ShockScenario;
  scope: string;
  affected: ShockedSubmission[];
  unaffected: any[];
  // Aggregates
  total_affected: number;
  total_unaffected: number;
  tier_migrations: number;
  decision_changes: number;
  aggregate_premium_before: number;
  aggregate_premium_after: number;
  premium_delta: number;
  // Tier distribution before/after
  tier_dist_before: Record<number, number>;
  tier_dist_after: Record<number, number>;
}

/**
 * Simple tier lookup from score using common tier band ranges.
 * Uses the seeder's default tier structure.
 */
function tierFromScore(score: number): { tier: number; decision: string } {
  if (score >= 800) return { tier: 1, decision: 'approve' };
  if (score >= 650) return { tier: 2, decision: 'approve' };
  if (score >= 500) return { tier: 3, decision: 'refer' };
  if (score >= 350) return { tier: 4, decision: 'refer' };
  return { tier: 5, decision: 'decline' };
}

/**
 * Rough premium adjustment based on tier change.
 * Tier degradation increases premium, improvement decreases.
 */
function premiumForTier(basePremium: number, originalTier: number, newTier: number): number {
  const tierMultipliers: Record<number, number> = { 1: 0.7, 2: 0.85, 3: 1.0, 4: 1.25, 5: 1.6 };
  const origMult = tierMultipliers[originalTier] || 1.0;
  const newMult = tierMultipliers[newTier] || 1.0;
  return basePremium * (newMult / origMult);
}

export function applyShock(
  submissions: any[],
  scenario: ShockScenario,
  scope: string, // 'all' or a coverage type
  customMagnitude?: number
): ShockResult {
  const magnitude = customMagnitude ?? scenario.magnitude;

  const affected: ShockedSubmission[] = [];
  const unaffected: any[] = [];
  const tierDistBefore: Record<number, number> = {};
  const tierDistAfter: Record<number, number> = {};

  for (const sub of submissions) {
    const score = sub.pure_composite_score ?? 0;
    const tier = sub.final_tier ?? tierFromScore(score).tier;
    const premium = sub.recommended_premium ?? 0;

    // Count before distribution
    tierDistBefore[tier] = (tierDistBefore[tier] || 0) + 1;

    // Check if in scope
    const inScope = scope === 'all' ||
      (sub.coverage_configuration || '').toLowerCase().includes(scope.toLowerCase());

    if (!inScope) {
      unaffected.push(sub);
      tierDistAfter[tier] = (tierDistAfter[tier] || 0) + 1;
      continue;
    }

    // Apply shock — degrade score
    const shockedScore = Math.max(0, score - magnitude);
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
    });
  }

  const aggPremBefore = affected.reduce((s, a) => s + (a.original.recommended_premium || 0), 0);
  const aggPremAfter = affected.reduce((s, a) => s + (a.original.recommended_premium || 0) + a.premium_delta, 0);

  return {
    scenario,
    scope,
    affected: affected.sort((a, b) => a.score_delta - b.score_delta), // most degraded first
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

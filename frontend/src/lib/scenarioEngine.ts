/**
 * scenarioEngine.ts — Pure functions for full client-side pricing cascade.
 *
 * Chain: Signal Overrides → Composite Score → Tier → Base Premium
 *        → Loss Modifier → Exposure Modifier → Modifier Chain
 *        → ILF → Deductible Factor → Guardrails → Final Premium
 *
 * All functions are pure (no side effects, no store access).
 * Config snapshots come from activeVersion JSONB fields.
 */

// ─── Types ───────────────────────────────────────────────────────────────────

export interface TierResult {
  tier_id: number;
  label: string;
  action: string;
  application: { method: string; value?: number; applied?: number; basis?: string };
  band_min: number;
  band_max: number;
}

export interface LossModifierResult {
  propensity_score: number;
  severity_score: number;
  propensity_band: string;
  severity_band: string;
  frequency_multiplier: number;
  severity_multiplier: number;
  combined_modifier: number;
}

export interface WaterfallStep {
  source: string;
  name: string;
  original_factor: number;
  scenario_factor: number;
  premium_after: number;
}

export interface GuardrailResult {
  clamped_modifier: number;
  capped_premium: number;
  warnings: string[];
  was_capped: boolean;
}

export interface ScenarioResult {
  // Composite
  composite_score: number;
  original_composite: number;
  // Tier
  tier: TierResult | null;
  original_tier: number;
  // Base premium
  base_premium: number;
  original_base_premium: number;
  // Loss
  loss_modifier: LossModifierResult | null;
  scenario_loss_combined: number;
  original_loss_combined: number;
  // Exposure
  scenario_exposure_modifier: number;
  original_exposure_modifier: number;
  scenario_exposure_band: string;
  // Modifier chain
  waterfall: WaterfallStep[];
  premium_after_modifiers: number;
  total_modifier: number;
  // ILF
  ilf_factor: number;
  original_ilf_factor: number;
  // Deductible
  deductible_factor: number;
  original_deductible_factor: number;
  // Guardrails
  guardrails: GuardrailResult;
  // Final
  final_premium: number;
  original_final_premium: number;
}

// ─── A1: Composite Score ─────────────────────────────────────────────────────

export function recalcCompositeScore(
  signals: any[],
  overrides: Record<string, number>
): { composite: number; groupScores: Record<string, number> } {
  if (!signals || signals.length === 0) return { composite: 0, groupScores: {} };

  // Build group stats
  const groupStats: Record<string, { totalWeight: number; groupWeight: number }> = {};
  for (const sig of signals) {
    const group = sig.group_code || 'ungrouped';
    if (!groupStats[group]) {
      groupStats[group] = { totalWeight: 0, groupWeight: sig.group_weight || 0 };
    }
    groupStats[group].totalWeight += (sig.weight || 0);
  }

  const groupScores: Record<string, number> = {};
  for (const sig of signals) {
    const group = sig.group_code || 'ungrouped';
    const score = overrides[sig.code] !== undefined ? overrides[sig.code] : (sig.score || 0);
    const weight = sig.weight || 0;
    const totalGroupWeight = groupStats[group].totalWeight || 1;
    if (!groupScores[group]) groupScores[group] = 0;
    groupScores[group] += (score * weight) / totalGroupWeight;
  }

  let composite = 0;
  for (const group of Object.keys(groupScores)) {
    composite += groupScores[group] * groupStats[group].groupWeight * 10;
  }

  return { composite, groupScores };
}

// ─── A2: Tier Lookup ─────────────────────────────────────────────────────────

export function lookupTierFromScore(
  score: number,
  tierBandInterpretation: any
): TierResult | null {
  if (!tierBandInterpretation?.tiers) return null;

  const tiers = tierBandInterpretation.tiers;
  for (const t of tiers) {
    const min = t.bands?.min ?? 0;
    const max = t.bands?.max ?? 1000;
    if (score >= min && score <= max) {
      return {
        tier_id: t.tier_id,
        label: t.label,
        action: t.action,
        application: t.application || {},
        band_min: min,
        band_max: max,
      };
    }
  }
  // Default to last tier if no match
  const last = tiers[tiers.length - 1];
  if (last) {
    return {
      tier_id: last.tier_id,
      label: last.label,
      action: last.action,
      application: last.application || {},
      band_min: last.bands?.min ?? 0,
      band_max: last.bands?.max ?? 1000,
    };
  }
  return null;
}

// ─── A3: Base Premium ────────────────────────────────────────────────────────

export function recalcBasePremium(
  tierApplication: TierResult["application"] | null,
  basePremiumDerivation: any
): number {
  if (!tierApplication) {
    return basePremiumDerivation?.result || 0;
  }

  const method = tierApplication.method?.toUpperCase?.() || '';

  if (method === 'PREMIUM_BASE' || method === 'PREMIUM_BASED') {
    // Direct value from tier
    return tierApplication.value || basePremiumDerivation?.result || 0;
  }

  if (method === 'MULTIPLIER') {
    // Rate × basis value
    const basisValue = basePremiumDerivation?.basis_value || 0;
    const rate = tierApplication.applied || tierApplication.value || 0;
    return basisValue * rate;
  }

  // Fallback: use original
  return basePremiumDerivation?.result || 0;
}

// ─── A4: Loss Modifier ───────────────────────────────────────────────────────

export function recalcLossModifier(
  signals: any[],
  overrides: Record<string, number>,
  groupScoresData: Record<string, any>,
  lossCorrelationConfig: any
): LossModifierResult | null {
  if (!lossCorrelationConfig) return null;

  // Find loss-weighted groups
  const lossGroups: Record<string, number> = {};
  for (const [gid, gs] of Object.entries(groupScoresData || {})) {
    const lw = (gs as any)?.loss_weight;
    if (lw && lw > 0) lossGroups[gid] = lw;
  }
  if (Object.keys(lossGroups).length === 0) return null;

  // Build per-group average scores using overridden signal scores
  const groupStats: Record<string, { totalWeight: number }> = {};
  for (const sig of signals) {
    const group = sig.group_code || 'ungrouped';
    if (!lossGroups[group]) continue;
    if (!groupStats[group]) groupStats[group] = { totalWeight: 0 };
    groupStats[group].totalWeight += (sig.weight || 0);
  }

  let lossWeightedSum = 0;
  let lossWeightTotal = 0;
  const perGroupScores: Record<string, number> = {};

  for (const sig of signals) {
    const group = sig.group_code || 'ungrouped';
    if (!lossGroups[group]) continue;
    const score = overrides[sig.code] !== undefined ? overrides[sig.code] : (sig.score || 0);
    const weight = sig.weight || 0;
    const totalGW = groupStats[group]?.totalWeight || 1;
    if (!perGroupScores[group]) perGroupScores[group] = 0;
    perGroupScores[group] += (score * weight) / totalGW;
  }

  for (const [gid, groupScore] of Object.entries(perGroupScores)) {
    const lw = lossGroups[gid];
    lossWeightedSum += groupScore * lw;
    lossWeightTotal += lw;
  }

  const avgSignalScore = lossWeightTotal > 0 ? lossWeightedSum / lossWeightTotal : 50;
  const propensityScore = Math.max(0, Math.min(100, 100 - avgSignalScore));
  // Severity: slight offset (deterministic in scenario — use propensity directly)
  const severityScore = Math.max(0, Math.min(100, propensityScore));

  // Band lookups
  const propBands = lossCorrelationConfig.propensity_bands || [];
  const sevBands = lossCorrelationConfig.severity_bands || [];

  const propBand = propBands.find((b: any) => propensityScore >= b.min_score && propensityScore < b.max_score)
    || propBands[propBands.length - 1];
  const sevBand = sevBands.find((b: any) => severityScore >= b.min_score && severityScore < b.max_score)
    || sevBands[sevBands.length - 1];

  const freqMult = propBand?.frequency_multiplier ?? 1.0;
  const sevMult = sevBand?.severity_multiplier ?? 1.0;

  const freqWeight = lossCorrelationConfig.frequency_weight ?? 0.6;
  const sevWeight = lossCorrelationConfig.severity_weight ?? 0.4;
  const combined = freqMult * freqWeight + sevMult * sevWeight;

  return {
    propensity_score: Math.round(propensityScore * 100) / 100,
    severity_score: Math.round(severityScore * 100) / 100,
    propensity_band: propBand?.name || 'unknown',
    severity_band: sevBand?.name || 'unknown',
    frequency_multiplier: freqMult,
    severity_multiplier: sevMult,
    combined_modifier: Math.round(combined * 1000) / 1000,
  };
}

// ─── A5: Exposure Modifier (band lookup) ─────────────────────────────────────

export function recalcExposureModifier(
  exposureValue: number,
  exposureBandInterpretation: any
): { band_label: string; modifier: number } {
  if (!exposureBandInterpretation?.size?.bands) {
    return { band_label: 'N/A', modifier: 1.0 };
  }

  const sizeBands = exposureBandInterpretation.size.bands;
  for (const band of sizeBands) {
    const min = band.bands?.min ?? 0;
    const max = band.bands?.max ?? Infinity;
    if (exposureValue >= min && exposureValue <= max) {
      return { band_label: band.label || 'Unknown', modifier: band.modifier ?? 1.0 };
    }
  }

  // Default to last band
  const last = sizeBands[sizeBands.length - 1];
  return { band_label: last?.label || 'Unknown', modifier: last?.modifier ?? 1.0 };
}

// ─── A6: Modifier Chain ──────────────────────────────────────────────────────

export function applyModifierChain(
  basePremium: number,
  modifiersApplied: any[],
  scenarioLossModifier: number | null,
  scenarioExposureModifier: number | null
): { premium: number; totalModifier: number; waterfall: WaterfallStep[] } {
  const waterfall: WaterfallStep[] = [];
  let premium = basePremium;
  let totalModifier = 1.0;

  for (const mod of (modifiersApplied || [])) {
    const source = (mod.source || mod.source_id || '').toLowerCase();
    const name = mod.name || mod.note || source;
    const originalFactor = mod.factor ?? mod.applied ?? 1.0;

    let scenarioFactor = originalFactor;
    if (scenarioLossModifier !== null && (source.includes('loss') || name.includes('loss'))) {
      scenarioFactor = scenarioLossModifier;
    } else if (scenarioExposureModifier !== null && (source.includes('exposure') || name.includes('exposure'))) {
      scenarioFactor = scenarioExposureModifier;
    }

    premium *= scenarioFactor;
    totalModifier *= scenarioFactor;

    waterfall.push({
      source,
      name,
      original_factor: originalFactor,
      scenario_factor: scenarioFactor,
      premium_after: premium,
    });
  }

  return { premium, totalModifier, waterfall };
}

// ─── A7: ILF Recalculation ──────────────────────────────────────────────────

export function recalcILF(
  limit: number,
  ilfCurveConfig: any
): number {
  if (!ilfCurveConfig || !ilfCurveConfig.curve) return 1.0;

  const anchor = ilfCurveConfig.anchor_limit || 1000000;
  const params = ilfCurveConfig.params || {};
  const curveType = ilfCurveConfig.curve.toLowerCase();

  const rawAtLimit = evaluateCurve(curveType, limit, anchor, params);
  const rawAtAnchor = evaluateCurve(curveType, anchor, anchor, params);

  if (rawAtAnchor === 0) return 1.0;
  return rawAtLimit / rawAtAnchor;
}

function evaluateCurve(curve: string, L: number, anchor: number, params: any): number {
  switch (curve) {
    case 'power': {
      const alpha = params.alpha ?? 0.5;
      return Math.pow(L / anchor, alpha);
    }
    case 'iso_pareto': {
      const q = params.q ?? 2.5;
      const b = params.b ?? 50000;
      return 1 - Math.pow(b / (b + L), q - 1);
    }
    case 'bounded_exponential': {
      const maxIlf = params.max_ilf ?? 3.0;
      const k = params.k ?? 1.2;
      return 1 + (maxIlf - 1) * (1 - Math.exp(-k * L / anchor));
    }
    case 'logarithmic': {
      const a = params.a ?? 1.0;
      const bParam = params.b ?? 0.3;
      return a + bParam * Math.log(L / anchor + 1);
    }
    case 'pareto': {
      const alpha = params.alpha ?? 0.8;
      return Math.pow(L / anchor, alpha);
    }
    default:
      return L / anchor;
  }
}

// ─── A8: Deductible Factor ───────────────────────────────────────────────────

export function recalcDeductibleFactor(
  deductible: number,
  productType: string,
  deductibleFactorTable: any
): number {
  if (!deductibleFactorTable) return 1.0;

  const factors = deductibleFactorTable[productType] || Object.values(deductibleFactorTable)[0];
  if (!factors || !Array.isArray(factors)) return 1.0;

  const match = factors.find((f: any) => f.deductible === deductible);
  return match?.factor ?? 1.0;
}

// ─── A9: Guardrails ─────────────────────────────────────────────────────────

export function applyGuardrails(
  totalModifier: number,
  finalPremium: number,
  limit: number,
  revenue: number,
  guardrailsConfig: any
): GuardrailResult {
  const warnings: string[] = [];
  let clampedModifier = totalModifier;
  let cappedPremium = finalPremium;

  if (!guardrailsConfig) {
    return { clamped_modifier: totalModifier, capped_premium: finalPremium, warnings: [], was_capped: false };
  }

  const floor = guardrailsConfig.modifier_floor ?? 0.10;
  const cap = guardrailsConfig.modifier_cap ?? 2.50;
  const maxPTL = guardrailsConfig.max_premium_to_limit_ratio ?? 0.35;
  const maxPTR = guardrailsConfig.max_premium_to_revenue_ratio ?? 0.01;

  if (clampedModifier < floor) {
    warnings.push(`Total modifier clamped from ${clampedModifier.toFixed(3)} to floor ${floor}`);
    clampedModifier = floor;
  }
  if (clampedModifier > cap) {
    warnings.push(`Total modifier clamped from ${clampedModifier.toFixed(3)} to cap ${cap}`);
    clampedModifier = cap;
  }

  if (limit > 0) {
    const maxByLimit = limit * maxPTL;
    if (cappedPremium > maxByLimit) {
      warnings.push(`Premium capped at ${(maxPTL * 100).toFixed(0)}% of limit ($${maxByLimit.toLocaleString()})`);
      cappedPremium = maxByLimit;
    }
  }

  if (revenue > 0) {
    const maxByRevenue = revenue * maxPTR;
    if (cappedPremium > maxByRevenue) {
      warnings.push(`Premium capped at ${(maxPTR * 100).toFixed(1)}% of revenue ($${maxByRevenue.toLocaleString()})`);
      cappedPremium = maxByRevenue;
    }
  }

  return {
    clamped_modifier: clampedModifier,
    capped_premium: cappedPremium,
    warnings,
    was_capped: warnings.length > 0,
  };
}

// ─── A10: Full Cascade Orchestrator ──────────────────────────────────────────

export interface ScenarioOverrides {
  signalOverrides: Record<string, number>;
  lossModifierOverride: number | null;
  exposureModifierOverride: number | null;
  limitOverride: number | null;
  deductibleOverride: number | null;
}

export function runFullCascade(
  signals: any[],
  activeVersion: any,
  overrides: ScenarioOverrides
): ScenarioResult {
  const av = activeVersion;

  // ── Original values ──
  const originalComposite = av.pure_composite_score || 0;
  const originalTier = av.final_tier || av.score_based_tier || 1;
  const originalBasePremium = av.base_premium || 0;
  const originalLossCombined = av.loss_combined_modifier || 1.0;
  const originalExposureModifier = av.exposure_modifier || 1.0;
  const originalILF = av.ilf_factor || 1.0;
  const originalFinalPremium = av.final_premium || av.premium_after_modifiers || 0;

  // Determine original deductible factor from final_premium_detail
  const fpd = av.final_premium_detail || {};
  const originalDeductibleFactor = fpd.deductible_factor || 1.0;
  const currentLimit = overrides.limitOverride || fpd.limit || av.recommended_limit || 0;
  const currentDeductible = overrides.deductibleOverride || fpd.deductible || 0;
  const productType = av.submission_data?.product_type || av.coverage || '';
  const revenue = av.submission_data?.revenue || av.exposure_value || 0;

  // ── A1: Composite ──
  const { composite } = recalcCompositeScore(signals, overrides.signalOverrides);
  const hasSignalOverrides = Object.keys(overrides.signalOverrides).length > 0;
  const scenarioComposite = hasSignalOverrides ? composite : originalComposite;

  // ── A2: Tier ──
  const tier = lookupTierFromScore(scenarioComposite, av.tier_band_interpretation);

  // ── A3: Base Premium ──
  const scenarioBasePremium = tier
    ? recalcBasePremium(tier.application, av.base_premium_derivation)
    : originalBasePremium;

  // ── A4: Loss Modifier ──
  let scenarioLossCombined = originalLossCombined;
  let lossResult: LossModifierResult | null = null;
  if (overrides.lossModifierOverride !== null) {
    scenarioLossCombined = overrides.lossModifierOverride;
  } else if (hasSignalOverrides && av.loss_correlation_config) {
    lossResult = recalcLossModifier(
      signals, overrides.signalOverrides, av.group_scores, av.loss_correlation_config
    );
    if (lossResult) scenarioLossCombined = lossResult.combined_modifier;
  }

  // ── A5: Exposure Modifier ──
  let scenarioExposureMod = originalExposureModifier;
  let scenarioExposureBand = av.exposure_band_label || 'N/A';
  if (overrides.exposureModifierOverride !== null) {
    scenarioExposureMod = overrides.exposureModifierOverride;
  }

  // ── A6: Modifier Chain ──
  const lossOverrideForChain = scenarioLossCombined !== originalLossCombined ? scenarioLossCombined : null;
  const expOverrideForChain = scenarioExposureMod !== originalExposureModifier ? scenarioExposureMod : null;
  const { premium: premiumAfterMods, totalModifier, waterfall } = applyModifierChain(
    scenarioBasePremium, av.modifiers_applied, lossOverrideForChain, expOverrideForChain
  );

  // ── A7: ILF ──
  let scenarioILF = originalILF;
  if (overrides.limitOverride !== null && av.ilf_curve_config) {
    scenarioILF = recalcILF(overrides.limitOverride, av.ilf_curve_config);
  }

  // ── A8: Deductible ──
  let scenarioDeductibleFactor = originalDeductibleFactor;
  if (overrides.deductibleOverride !== null && av.deductible_factor_table) {
    scenarioDeductibleFactor = recalcDeductibleFactor(
      overrides.deductibleOverride, productType, av.deductible_factor_table
    );
  }

  // ── Pre-guardrail premium ──
  const preGuardrailPremium = premiumAfterMods * scenarioILF * scenarioDeductibleFactor;

  // ── A9: Guardrails ──
  const guardrails = applyGuardrails(
    totalModifier, preGuardrailPremium, currentLimit, revenue, av.guardrails_config
  );

  return {
    composite_score: scenarioComposite,
    original_composite: originalComposite,
    tier,
    original_tier: originalTier,
    base_premium: scenarioBasePremium,
    original_base_premium: originalBasePremium,
    loss_modifier: lossResult,
    scenario_loss_combined: scenarioLossCombined,
    original_loss_combined: originalLossCombined,
    scenario_exposure_modifier: scenarioExposureMod,
    original_exposure_modifier: originalExposureModifier,
    scenario_exposure_band: scenarioExposureBand,
    waterfall,
    premium_after_modifiers: premiumAfterMods,
    total_modifier: totalModifier,
    ilf_factor: scenarioILF,
    original_ilf_factor: originalILF,
    deductible_factor: scenarioDeductibleFactor,
    original_deductible_factor: originalDeductibleFactor,
    guardrails,
    final_premium: guardrails.capped_premium,
    original_final_premium: originalFinalPremium,
  };
}

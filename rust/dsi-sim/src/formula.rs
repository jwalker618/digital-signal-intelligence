//! DSI Core Pricing Formula
//!
//! Implements the deterministic pricing formula from the Vision Paper:
//!
//! P_final = (B × R) × ILF × D_fac × Mods
//!
//! Where:
//! - B = Base premium (from tier application)
//! - R = Risk multiplier (from composite score tier)
//! - ILF = Increased Limit Factor (from limit selection)
//! - D_fac = Deductible factor (from deductible selection)
//! - Mods = Product of all applicable modifiers

use crate::config::{CoverageConfig, ProductPricing};

/// Core pricing formula calculator
#[derive(Debug, Clone)]
pub struct PricingFormula {
    /// Base premium (B)
    pub base_premium: f64,
    /// Risk multiplier (R) - from tier
    pub risk_multiplier: f64,
    /// Increased Limit Factor (ILF)
    pub ilf: f64,
    /// Deductible factor (D_fac)
    pub deductible_factor: f64,
    /// Combined modifiers (Mods)
    pub modifiers: f64,
}

/// Result of pricing calculation
#[derive(Debug, Clone)]
pub struct PricingResult {
    /// Final calculated premium
    pub final_premium: f64,
    /// Premium before modifiers
    pub premium_before_modifiers: f64,
    /// Applied tier
    pub tier: u8,
    /// Tier label
    pub tier_label: String,
    /// Risk multiplier used
    pub risk_multiplier: f64,
    /// ILF applied
    pub ilf: f64,
    /// Deductible factor applied
    pub deductible_factor: f64,
    /// Total modifier factor
    pub total_modifiers: f64,
}

impl PricingFormula {
    /// Create a new pricing formula instance
    pub fn new(base_premium: f64) -> Self {
        PricingFormula {
            base_premium,
            risk_multiplier: 1.0,
            ilf: 1.0,
            deductible_factor: 1.0,
            modifiers: 1.0,
        }
    }

    /// Set risk multiplier from tier
    pub fn with_tier(mut self, tier: u8, config: &CoverageConfig) -> Self {
        self.risk_multiplier = config.get_tier_multiplier(tier);
        self
    }

    /// Set ILF from requested limit
    pub fn with_limit(mut self, limit: f64, product_pricing: Option<&ProductPricing>, base_limit: f64) -> Self {
        if let Some(pricing) = product_pricing {
            // Find the ILF for the requested limit
            // Linear interpolation between defined points
            self.ilf = interpolate_ilf(&pricing.ilf_curve.factors, limit, base_limit);
        }
        self
    }

    /// Set deductible factor from selected deductible
    pub fn with_deductible(mut self, deductible: f64, product_pricing: Option<&ProductPricing>, base_deductible: f64) -> Self {
        if let Some(pricing) = product_pricing {
            self.deductible_factor = interpolate_deductible(&pricing.deductible_factors, deductible, base_deductible);
        }
        self
    }

    /// Apply categorical modifiers
    pub fn with_modifiers(mut self, modifiers: &[f64]) -> Self {
        self.modifiers = modifiers.iter().product();
        self
    }

    /// Calculate final premium
    ///
    /// P_final = (B × R) × ILF × D_fac × Mods
    pub fn calculate(&self) -> f64 {
        let base_with_risk = self.base_premium * self.risk_multiplier;
        let with_ilf = base_with_risk * self.ilf;
        let with_deductible = with_ilf * self.deductible_factor;
        let final_premium = with_deductible * self.modifiers;
        final_premium
    }

    /// Calculate with full result details
    pub fn calculate_detailed(&self, tier: u8, tier_label: &str) -> PricingResult {
        let base_with_risk = self.base_premium * self.risk_multiplier;
        let with_ilf = base_with_risk * self.ilf;
        let premium_before_modifiers = with_ilf * self.deductible_factor;
        let final_premium = premium_before_modifiers * self.modifiers;

        PricingResult {
            final_premium,
            premium_before_modifiers,
            tier,
            tier_label: tier_label.to_string(),
            risk_multiplier: self.risk_multiplier,
            ilf: self.ilf,
            deductible_factor: self.deductible_factor,
            total_modifiers: self.modifiers,
        }
    }
}

/// Interpolate ILF for a given limit
fn interpolate_ilf(factors: &[(impl AsRef<LimitPoint>)], limit: f64, base_limit: f64) -> f64
where
    LimitPoint: From<(f64, f64)>,
{
    // Simple implementation: find bracketing factors and interpolate
    // In production, this would use proper curve interpolation

    // Convert to simple tuples for processing
    let points: Vec<(f64, f64)> = factors.iter()
        .filter_map(|f| {
            // This is a placeholder - actual implementation depends on factor structure
            None::<(f64, f64)>
        })
        .collect();

    // Default: return 1.0 for base limit, scale proportionally
    if limit <= base_limit {
        1.0
    } else {
        // Simple log-linear scaling (ILFs typically follow ISO curves)
        let ratio = (limit / base_limit).ln();
        1.0 + (ratio * 0.4) // Approximate ISO curve
    }
}

/// Interpolate deductible factor
fn interpolate_deductible(factors: &[crate::config::DeductibleFactor], deductible: f64, base_deductible: f64) -> f64 {
    // Find exact match or interpolate
    for factor in factors {
        if (factor.deductible - deductible).abs() < 0.01 {
            return factor.factor;
        }
    }

    // Default: higher deductible = lower factor (premium credit)
    if deductible > base_deductible {
        let ratio = deductible / base_deductible;
        1.0 - (0.05 * (ratio - 1.0).ln().max(0.0)) // ~5% credit per doubling
    } else {
        let ratio = base_deductible / deductible;
        1.0 + (0.08 * (ratio - 1.0).ln().max(0.0)) // ~8% surcharge per halving
    }
}

// Placeholder type for limit points
struct LimitPoint {
    limit: f64,
    factor: f64,
}

impl From<(f64, f64)> for LimitPoint {
    fn from((limit, factor): (f64, f64)) -> Self {
        LimitPoint { limit, factor }
    }
}

impl AsRef<LimitPoint> for crate::config::LimitFactor {
    fn as_ref(&self) -> &LimitPoint {
        // This is a workaround - in production we'd have proper type alignment
        unsafe { &*(self as *const _ as *const LimitPoint) }
    }
}

/// Calculate premium from composite score and config
pub fn calculate_premium_from_score(
    composite_score: f64,
    config: &CoverageConfig,
    product_type: &str,
    limit: f64,
    deductible: f64,
    modifiers: &[f64],
) -> PricingResult {
    let tier = config.get_tier_for_score(composite_score);
    let tier_label = config.risk_tier_bands.bands.iter()
        .find(|b| b.id == tier)
        .map(|b| b.label.clone())
        .unwrap_or_else(|| "UNKNOWN".to_string());

    let risk_multiplier = config.get_tier_multiplier(tier);
    let product_pricing = config.pricing.by_product_type.get(product_type);

    // Determine base premium from tier method
    let base_premium = config.risk_tier_bands.bands.iter()
        .find(|b| b.id == tier)
        .map(|b| {
            match b.interpretation.application.method.as_str() {
                "PREMIUM_BASE" => config.metadata.min_premium * b.interpretation.application.value,
                "MULTIPLIER" => config.metadata.min_premium, // Would need basis input
                _ => config.metadata.min_premium,
            }
        })
        .unwrap_or(config.metadata.min_premium);

    PricingFormula::new(base_premium)
        .with_tier(tier, config)
        .with_limit(limit, product_pricing, config.pricing.base_limit_reference)
        .with_deductible(deductible, product_pricing, config.pricing.base_deductible_reference)
        .with_modifiers(modifiers)
        .calculate_detailed(tier, &tier_label)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_basic_formula() {
        let formula = PricingFormula::new(10_000.0);
        assert_eq!(formula.calculate(), 10_000.0);
    }

    #[test]
    fn test_with_modifiers() {
        let formula = PricingFormula::new(10_000.0)
            .with_modifiers(&[0.9, 1.1, 0.95]);

        // 10000 * 0.9 * 1.1 * 0.95 = 9405
        let expected = 10_000.0 * 0.9 * 1.1 * 0.95;
        assert!((formula.calculate() - expected).abs() < 0.01);
    }

    #[test]
    fn test_full_formula() {
        let mut formula = PricingFormula::new(10_000.0);
        formula.risk_multiplier = 1.2;
        formula.ilf = 1.5;
        formula.deductible_factor = 0.95;
        formula.modifiers = 0.9;

        // P = 10000 * 1.2 * 1.5 * 0.95 * 0.9 = 15390
        let expected = 10_000.0 * 1.2 * 1.5 * 0.95 * 0.9;
        assert!((formula.calculate() - expected).abs() < 0.01);
    }
}

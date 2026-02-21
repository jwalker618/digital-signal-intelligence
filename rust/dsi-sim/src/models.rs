//! DSI Core Risk Models (Version 4 - Phase 3)
//!
//! Implements the core pricing formula as memory-safe Rust structs.
//! These models enable millisecond portfolio recalculation.
//!
//! # Formula
//!
//! P_final = (basis × base_rate) × limit_ilf × deductible_factor
//!           × risk_modifier × loss_modifier × exposure_modifier

use pyo3::prelude::*;
use rayon::prelude::*;
use serde::{Deserialize, Serialize};

/// Complete risk profile for premium calculation.
///
/// Captures all pricing factors needed to calculate technical premium.
/// Designed for zero-copy parallel processing across portfolios.
#[pyclass]
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RiskProfile {
    /// Entity identifier
    #[pyo3(get, set)]
    pub entity_id: String,

    /// Base rate from risk tier (0.001 = 0.1%)
    #[pyo3(get, set)]
    pub base_rate: f64,

    /// Increased Limit Factor (e.g., 1.0 for $1M, 3.5 for $5M)
    #[pyo3(get, set)]
    pub limit_ilf: f64,

    /// Deductible factor (e.g., 1.0 baseline, 0.85 for higher deductible)
    #[pyo3(get, set)]
    pub deductible_factor: f64,

    /// Risk tier modifier (composite score impact)
    #[pyo3(get, set)]
    pub risk_modifier: f64,

    /// Loss tier modifier (frequency × severity)
    #[pyo3(get, set)]
    pub loss_modifier: f64,

    /// Exposure modifier (size × complexity)
    #[pyo3(get, set)]
    pub exposure_modifier: f64,

    /// Categorical modifiers product
    #[pyo3(get, set)]
    pub categorical_modifier: f64,

    /// Original premium (for comparison)
    #[pyo3(get, set)]
    pub original_premium: f64,

    /// Industry classification
    #[pyo3(get, set)]
    pub industry: String,

    /// Current risk tier (1-5)
    #[pyo3(get, set)]
    pub tier: u8,
}

#[pymethods]
impl RiskProfile {
    #[new]
    fn new(entity_id: String, base_rate: f64) -> Self {
        RiskProfile {
            entity_id,
            base_rate,
            limit_ilf: 1.0,
            deductible_factor: 1.0,
            risk_modifier: 1.0,
            loss_modifier: 1.0,
            exposure_modifier: 1.0,
            categorical_modifier: 1.0,
            original_premium: 0.0,
            industry: String::new(),
            tier: 3,
        }
    }

    /// Calculate technical premium for this risk profile.
    ///
    /// Formula: P = (basis × base_rate) × ILF × D_fac × R × L × E × Cat
    pub fn calculate_technical_premium(&self, basis: f64) -> f64 {
        let base = basis * self.base_rate;
        let with_ilf = base * self.limit_ilf;
        let with_ded = with_ilf * self.deductible_factor;
        let with_risk = with_ded * self.risk_modifier;
        let with_loss = with_risk * self.loss_modifier;
        let with_exposure = with_loss * self.exposure_modifier;
        let final_premium = with_exposure * self.categorical_modifier;

        final_premium
    }

    /// Apply a shock to the risk modifier and recalculate.
    pub fn calculate_shocked_premium(&self, basis: f64, risk_shock: f64) -> f64 {
        let shocked_risk = self.risk_modifier * risk_shock;

        let base = basis * self.base_rate;
        let with_ilf = base * self.limit_ilf;
        let with_ded = with_ilf * self.deductible_factor;
        let with_risk = with_ded * shocked_risk;
        let with_loss = with_risk * self.loss_modifier;
        let with_exposure = with_loss * self.exposure_modifier;
        let final_premium = with_exposure * self.categorical_modifier;

        final_premium
    }

    /// Get combined modifier product (for analysis)
    pub fn combined_modifier(&self) -> f64 {
        self.limit_ilf
            * self.deductible_factor
            * self.risk_modifier
            * self.loss_modifier
            * self.exposure_modifier
            * self.categorical_modifier
    }
}

/// High-performance simulation engine for portfolio stress testing.
///
/// Uses Rayon for zero-cost parallel processing across CPU cores.
#[pyclass]
pub struct SimulationEngine {
    /// Portfolio of risk profiles
    profiles: Vec<RiskProfile>,
    /// Basis values for each profile (TIV, limit, revenue, etc.)
    basis_values: Vec<f64>,
}

#[pymethods]
impl SimulationEngine {
    /// Create a new simulation engine with portfolio data.
    #[new]
    fn new(profiles: Vec<RiskProfile>, basis_values: Vec<f64>) -> PyResult<Self> {
        if profiles.len() != basis_values.len() {
            return Err(PyErr::new::<pyo3::exceptions::PyValueError, _>(
                format!(
                    "Profile count ({}) must match basis count ({})",
                    profiles.len(),
                    basis_values.len()
                )
            ));
        }
        Ok(SimulationEngine { profiles, basis_values })
    }

    /// Create from JSON portfolio data.
    #[staticmethod]
    fn from_json(json_str: &str) -> PyResult<Self> {
        let data: PortfolioData = serde_json::from_str(json_str)
            .map_err(|e| PyErr::new::<pyo3::exceptions::PyValueError, _>(e.to_string()))?;

        Ok(SimulationEngine {
            profiles: data.profiles,
            basis_values: data.basis_values,
        })
    }

    /// Calculate baseline total premium (no shock applied).
    fn calculate_baseline(&self) -> f64 {
        self.profiles
            .par_iter()
            .zip(self.basis_values.par_iter())
            .map(|(profile, basis)| profile.calculate_technical_premium(*basis))
            .sum()
    }

    /// Run shock scenario where risk_modifier is multiplied by shock_factor.
    ///
    /// This is the core simulation method. It processes the entire portfolio
    /// in parallel, calculating what happens when all risk modifiers are
    /// scaled by the shock factor.
    ///
    /// Returns the new total premium after the shock.
    fn simulate_risk_shock(&self, shock_factor: f64) -> f64 {
        self.profiles
            .par_iter()
            .zip(self.basis_values.par_iter())
            .map(|(profile, basis)| profile.calculate_shocked_premium(*basis, shock_factor))
            .sum()
    }

    /// Simulate shock with industry filter.
    ///
    /// Only applies shock to entities in the specified industry.
    fn simulate_industry_shock(&self, industry: &str, shock_factor: f64) -> f64 {
        self.profiles
            .par_iter()
            .zip(self.basis_values.par_iter())
            .map(|(profile, basis)| {
                if profile.industry.to_lowercase().contains(&industry.to_lowercase()) {
                    profile.calculate_shocked_premium(*basis, shock_factor)
                } else {
                    profile.calculate_technical_premium(*basis)
                }
            })
            .sum()
    }

    /// Simulate shock with tier filter.
    ///
    /// Only applies shock to entities in the specified tier.
    fn simulate_tier_shock(&self, tier: u8, shock_factor: f64) -> f64 {
        self.profiles
            .par_iter()
            .zip(self.basis_values.par_iter())
            .map(|(profile, basis)| {
                if profile.tier == tier {
                    profile.calculate_shocked_premium(*basis, shock_factor)
                } else {
                    profile.calculate_technical_premium(*basis)
                }
            })
            .sum()
    }

    /// Run comprehensive shock analysis.
    ///
    /// Returns detailed metrics about the shock impact.
    fn analyze_shock(&self, shock_factor: f64) -> ShockAnalysis {
        let baseline = self.calculate_baseline();
        let shocked = self.simulate_risk_shock(shock_factor);

        // Calculate per-entity impacts
        let impacts: Vec<f64> = self.profiles
            .par_iter()
            .zip(self.basis_values.par_iter())
            .map(|(profile, basis)| {
                let original = profile.calculate_technical_premium(*basis);
                let shocked = profile.calculate_shocked_premium(*basis, shock_factor);
                shocked - original
            })
            .collect();

        // Statistics
        let total_impact: f64 = impacts.iter().sum();
        let mean_impact = total_impact / impacts.len() as f64;
        let variance: f64 = impacts.iter().map(|i| (i - mean_impact).powi(2)).sum::<f64>()
            / impacts.len() as f64;
        let std_impact = variance.sqrt();

        let entities_increased = impacts.iter().filter(|&&i| i > 0.0).count();
        let entities_decreased = impacts.iter().filter(|&&i| i < 0.0).count();
        let max_increase = impacts.iter().cloned().fold(f64::NEG_INFINITY, f64::max);
        let max_decrease = impacts.iter().cloned().fold(f64::INFINITY, f64::min);

        ShockAnalysis {
            baseline_premium: baseline,
            shocked_premium: shocked,
            total_impact,
            mean_impact,
            std_impact,
            entities_increased,
            entities_decreased,
            max_increase,
            max_decrease,
            adequacy_ratio: shocked / baseline,
        }
    }

    /// Get portfolio size.
    fn portfolio_size(&self) -> usize {
        self.profiles.len()
    }

    /// Get tier distribution.
    fn tier_distribution(&self) -> Vec<(u8, usize)> {
        let mut dist = [0usize; 5];
        for profile in &self.profiles {
            if profile.tier >= 1 && profile.tier <= 5 {
                dist[(profile.tier - 1) as usize] += 1;
            }
        }
        (1..=5).map(|t| (t as u8, dist[(t - 1) as usize])).collect()
    }

    /// Get industry distribution.
    fn industry_distribution(&self) -> Vec<(String, usize)> {
        use std::collections::HashMap;
        let mut dist: HashMap<String, usize> = HashMap::new();
        for profile in &self.profiles {
            *dist.entry(profile.industry.clone()).or_insert(0) += 1;
        }
        let mut vec: Vec<_> = dist.into_iter().collect();
        vec.sort_by(|a, b| b.1.cmp(&a.1));
        vec
    }
}

/// Shock analysis results.
#[pyclass]
#[derive(Debug, Clone)]
pub struct ShockAnalysis {
    #[pyo3(get)]
    pub baseline_premium: f64,
    #[pyo3(get)]
    pub shocked_premium: f64,
    #[pyo3(get)]
    pub total_impact: f64,
    #[pyo3(get)]
    pub mean_impact: f64,
    #[pyo3(get)]
    pub std_impact: f64,
    #[pyo3(get)]
    pub entities_increased: usize,
    #[pyo3(get)]
    pub entities_decreased: usize,
    #[pyo3(get)]
    pub max_increase: f64,
    #[pyo3(get)]
    pub max_decrease: f64,
    #[pyo3(get)]
    pub adequacy_ratio: f64,
}

/// Portfolio data for JSON deserialization.
#[derive(Debug, Serialize, Deserialize)]
struct PortfolioData {
    profiles: Vec<RiskProfile>,
    basis_values: Vec<f64>,
}

#[cfg(test)]
mod tests {
    use super::*;

    fn create_test_profiles() -> (Vec<RiskProfile>, Vec<f64>) {
        let profiles = vec![
            RiskProfile {
                entity_id: "entity_1".to_string(),
                base_rate: 0.001,
                limit_ilf: 1.0,
                deductible_factor: 1.0,
                risk_modifier: 1.0,
                loss_modifier: 1.0,
                exposure_modifier: 1.0,
                categorical_modifier: 1.0,
                original_premium: 10000.0,
                industry: "Technology".to_string(),
                tier: 2,
            },
            RiskProfile {
                entity_id: "entity_2".to_string(),
                base_rate: 0.002,
                limit_ilf: 1.5,
                deductible_factor: 0.9,
                risk_modifier: 1.2,
                loss_modifier: 1.1,
                exposure_modifier: 1.0,
                categorical_modifier: 1.0,
                original_premium: 25000.0,
                industry: "Healthcare".to_string(),
                tier: 3,
            },
        ];
        let basis_values = vec![10_000_000.0, 5_000_000.0];

        (profiles, basis_values)
    }

    #[test]
    fn test_premium_calculation() {
        let profile = RiskProfile {
            entity_id: "test".to_string(),
            base_rate: 0.001, // 0.1%
            limit_ilf: 1.0,
            deductible_factor: 1.0,
            risk_modifier: 1.0,
            loss_modifier: 1.0,
            exposure_modifier: 1.0,
            categorical_modifier: 1.0,
            original_premium: 0.0,
            industry: "Tech".to_string(),
            tier: 2,
        };

        let premium = profile.calculate_technical_premium(10_000_000.0);
        assert!((premium - 10_000.0).abs() < 0.01);
    }

    #[test]
    fn test_shock_simulation() {
        let (profiles, basis) = create_test_profiles();
        let engine = SimulationEngine::new(profiles, basis).unwrap();

        let baseline = engine.calculate_baseline();
        let shocked = engine.simulate_risk_shock(1.5); // 50% worse risk

        assert!(shocked > baseline);
        assert!((shocked / baseline - 1.5).abs() < 0.01);
    }

    #[test]
    fn test_industry_filter() {
        let (profiles, basis) = create_test_profiles();
        let engine = SimulationEngine::new(profiles, basis).unwrap();

        let baseline = engine.calculate_baseline();
        let tech_shocked = engine.simulate_industry_shock("Technology", 2.0);

        // Only Tech entity should be affected
        assert!(tech_shocked > baseline);
        assert!(tech_shocked < baseline * 2.0); // Not everything doubled
    }
}

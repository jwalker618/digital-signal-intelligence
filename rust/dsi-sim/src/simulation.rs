//! DSI Monte Carlo Simulation Engine
//!
//! Runs portfolio-wide simulations to assess impact of shocks.
//! Uses Rayon for parallel computation across entities.

use rayon::prelude::*;
use std::collections::HashMap;
use std::time::Instant;

use crate::config::CoverageConfig;
use crate::formula::calculate_premium_from_score;
use crate::portfolio::{Entity, PortfolioSnapshot};
use crate::shock::ShockParameter;

/// Main simulation engine
pub struct Simulator {
    /// Loaded coverage configurations by coverage name
    configs: HashMap<String, CoverageConfig>,
    /// Current portfolio snapshot
    portfolio: Option<PortfolioSnapshot>,
}

/// Result of a simulation run
#[derive(Debug, Clone)]
pub struct SimulationResult {
    /// Pre-shock vs post-shock premium ratio
    pub premium_adequacy: f64,
    /// Total premium impact (post - pre)
    pub total_premium_impact: f64,
    /// Number of entities affected by the shock
    pub entities_affected: usize,
    /// Tier migration summary: (from_tier, to_tier, count)
    pub tier_migrations: Vec<(u8, u8, usize)>,
    /// Detailed statistics
    pub stats: SimulationStats,
}

/// Detailed simulation statistics
#[derive(Debug, Clone)]
pub struct SimulationStats {
    /// Mean change in composite score
    pub mean_score_delta: f64,
    /// Standard deviation of score changes
    pub std_score_delta: f64,
    /// Entities that improved tier (lower number)
    pub entities_upgraded: usize,
    /// Entities that worsened tier (higher number)
    pub entities_downgraded: usize,
    /// Execution time in milliseconds
    pub execution_time_ms: f64,
}

/// Per-entity simulation result
#[derive(Debug, Clone)]
struct EntityResult {
    entity_id: String,
    pre_score: f64,
    post_score: f64,
    pre_tier: u8,
    post_tier: u8,
    pre_premium: f64,
    post_premium: f64,
    affected: bool,
}

impl Simulator {
    /// Create a new simulator
    pub fn new() -> Self {
        Simulator {
            configs: HashMap::new(),
            portfolio: None,
        }
    }

    /// Load a coverage configuration
    pub fn load_config(&mut self, path: &str) -> Result<(), SimulationError> {
        let config = CoverageConfig::from_file(path)
            .map_err(|e| SimulationError::ConfigError(e.to_string()))?;

        // Extract coverage name from config
        let coverage_name = config.metadata.name.split('_').next()
            .unwrap_or(&config.metadata.name)
            .to_string();

        self.configs.insert(coverage_name, config);
        Ok(())
    }

    /// Load multiple configurations
    pub fn load_configs(&mut self, paths: &[&str]) -> Result<(), SimulationError> {
        for path in paths {
            self.load_config(path)?;
        }
        Ok(())
    }

    /// Load portfolio snapshot
    pub fn load_portfolio(&mut self, snapshot: PortfolioSnapshot) {
        self.portfolio = Some(snapshot);
    }

    /// Get entity count
    pub fn entity_count(&self) -> usize {
        self.portfolio.as_ref().map(|p| p.entity_count()).unwrap_or(0)
    }

    /// Run simulation with given shock
    pub fn run_simulation(
        &self,
        shock: &ShockParameter,
        _iterations: usize, // Reserved for Monte Carlo sampling
    ) -> Result<SimulationResult, SimulationError> {
        let portfolio = self.portfolio.as_ref()
            .ok_or(SimulationError::NoPortfolio)?;

        let start = Instant::now();

        // Run simulation in parallel across entities
        let results: Vec<EntityResult> = portfolio.entities
            .par_iter()
            .map(|entity| self.simulate_entity(entity, shock))
            .collect();

        let execution_time_ms = start.elapsed().as_secs_f64() * 1000.0;

        // Aggregate results
        self.aggregate_results(results, execution_time_ms)
    }

    /// Run simulation with multiple shocks
    pub fn run_multi_shock_simulation(
        &self,
        shocks: &[ShockParameter],
    ) -> Result<SimulationResult, SimulationError> {
        let portfolio = self.portfolio.as_ref()
            .ok_or(SimulationError::NoPortfolio)?;

        let start = Instant::now();

        // Apply all shocks sequentially to each entity
        let results: Vec<EntityResult> = portfolio.entities
            .par_iter()
            .map(|entity| {
                let mut current_entity = entity.clone();

                for shock in shocks {
                    if shock.applies_to_entity(&current_entity) {
                        if let Some(signal) = current_entity.get_signal_mut(&shock.signal_id) {
                            signal.score = shock.apply_to_score(signal.score);
                        }
                    }
                }

                self.calculate_entity_result(entity, &current_entity)
            })
            .collect();

        let execution_time_ms = start.elapsed().as_secs_f64() * 1000.0;

        self.aggregate_results(results, execution_time_ms)
    }

    /// Simulate single entity
    fn simulate_entity(&self, entity: &Entity, shock: &ShockParameter) -> EntityResult {
        if !shock.applies_to_entity(entity) {
            // Entity not affected
            return EntityResult {
                entity_id: entity.entity_id.clone(),
                pre_score: entity.composite_score,
                post_score: entity.composite_score,
                pre_tier: entity.tier,
                post_tier: entity.tier,
                pre_premium: entity.premium,
                post_premium: entity.premium,
                affected: false,
            };
        }

        // Apply shock to entity
        let shocked_entity = match shock.shock_type {
            crate::shock::ShockType::Override(value) => {
                entity.with_signal_override(&shock.signal_id, value)
            }
            crate::shock::ShockType::Multiplier(factor) => {
                entity.with_signal_multiplier(&shock.signal_id, factor)
            }
            crate::shock::ShockType::Additive(delta) => {
                let current = entity.get_signal(&shock.signal_id)
                    .map(|s| s.score)
                    .unwrap_or(50.0);
                entity.with_signal_override(&shock.signal_id, current + delta)
            }
            crate::shock::ShockType::Percentile(pct) => {
                entity.with_signal_override(&shock.signal_id, pct)
            }
        };

        self.calculate_entity_result(entity, &shocked_entity)
    }

    /// Calculate result for entity before/after shock
    fn calculate_entity_result(&self, pre: &Entity, post: &Entity) -> EntityResult {
        // Recalculate composite scores
        let post_score = post.recalculate_composite();

        // Determine new tier based on score
        let post_tier = self.get_tier_for_entity(post, post_score);

        // Calculate new premium
        let post_premium = self.calculate_premium_for_entity(post, post_score, post_tier);

        EntityResult {
            entity_id: pre.entity_id.clone(),
            pre_score: pre.composite_score,
            post_score,
            pre_tier: pre.tier,
            post_tier,
            pre_premium: pre.premium,
            post_premium,
            affected: (post_score - pre.composite_score).abs() > 0.01,
        }
    }

    /// Get tier for entity based on score
    fn get_tier_for_entity(&self, entity: &Entity, score: f64) -> u8 {
        if let Some(config) = self.configs.get(&entity.coverage) {
            config.get_tier_for_score(score)
        } else {
            // Default tier calculation
            match score as u32 {
                800..=1000 => 1,
                650..=799 => 2,
                500..=649 => 3,
                350..=499 => 4,
                _ => 5,
            }
        }
    }

    /// Calculate premium for entity
    fn calculate_premium_for_entity(&self, entity: &Entity, score: f64, tier: u8) -> f64 {
        if let Some(config) = self.configs.get(&entity.coverage) {
            let modifiers: Vec<f64> = entity.modifiers.iter().map(|m| m.factor).collect();
            let result = calculate_premium_from_score(
                score,
                config,
                &entity.product_type,
                entity.limit,
                entity.deductible,
                &modifiers,
            );
            result.final_premium
        } else {
            // Estimate premium change based on tier movement
            let tier_multipliers = [0.85, 1.0, 1.15, 1.5, 2.0];
            let old_mult = tier_multipliers.get(entity.tier as usize - 1).unwrap_or(&1.0);
            let new_mult = tier_multipliers.get(tier as usize - 1).unwrap_or(&1.0);
            entity.premium * (new_mult / old_mult)
        }
    }

    /// Aggregate entity results into simulation result
    fn aggregate_results(
        &self,
        results: Vec<EntityResult>,
        execution_time_ms: f64,
    ) -> Result<SimulationResult, SimulationError> {
        if results.is_empty() {
            return Err(SimulationError::NoEntities);
        }

        // Calculate totals
        let total_pre_premium: f64 = results.iter().map(|r| r.pre_premium).sum();
        let total_post_premium: f64 = results.iter().map(|r| r.post_premium).sum();
        let entities_affected = results.iter().filter(|r| r.affected).count();

        // Calculate score deltas
        let score_deltas: Vec<f64> = results.iter()
            .map(|r| r.post_score - r.pre_score)
            .collect();

        let mean_delta = score_deltas.iter().sum::<f64>() / score_deltas.len() as f64;
        let variance = score_deltas.iter()
            .map(|d| (d - mean_delta).powi(2))
            .sum::<f64>() / score_deltas.len() as f64;
        let std_delta = variance.sqrt();

        // Tier migrations
        let mut migrations: HashMap<(u8, u8), usize> = HashMap::new();
        let mut upgraded = 0;
        let mut downgraded = 0;

        for r in &results {
            if r.pre_tier != r.post_tier {
                *migrations.entry((r.pre_tier, r.post_tier)).or_insert(0) += 1;
                if r.post_tier < r.pre_tier {
                    upgraded += 1;
                } else {
                    downgraded += 1;
                }
            }
        }

        let tier_migrations: Vec<(u8, u8, usize)> = migrations
            .into_iter()
            .map(|((from, to), count)| (from, to, count))
            .collect();

        Ok(SimulationResult {
            premium_adequacy: if total_pre_premium > 0.0 {
                total_post_premium / total_pre_premium
            } else {
                1.0
            },
            total_premium_impact: total_post_premium - total_pre_premium,
            entities_affected,
            tier_migrations,
            stats: SimulationStats {
                mean_score_delta: mean_delta,
                std_score_delta: std_delta,
                entities_upgraded: upgraded,
                entities_downgraded: downgraded,
                execution_time_ms,
            },
        })
    }
}

impl Default for Simulator {
    fn default() -> Self {
        Self::new()
    }
}

/// Simulation errors
#[derive(Debug)]
pub enum SimulationError {
    ConfigError(String),
    NoPortfolio,
    NoEntities,
    InvalidShock(String),
}

impl std::fmt::Display for SimulationError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            SimulationError::ConfigError(e) => write!(f, "Configuration error: {}", e),
            SimulationError::NoPortfolio => write!(f, "No portfolio loaded"),
            SimulationError::NoEntities => write!(f, "Portfolio has no entities"),
            SimulationError::InvalidShock(e) => write!(f, "Invalid shock: {}", e),
        }
    }
}

impl std::error::Error for SimulationError {}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::portfolio::Signal;

    fn create_test_portfolio() -> PortfolioSnapshot {
        let mut snapshot = PortfolioSnapshot::new();

        for i in 0..100 {
            snapshot.entities.push(Entity {
                entity_id: format!("entity_{}", i),
                entity_name: format!("Test Corp {}", i),
                coverage: "cyber".to_string(),
                configuration: "cyber_general".to_string(),
                industry: if i % 2 == 0 { "Technology" } else { "Healthcare" }.to_string(),
                country: "US".to_string(),
                composite_score: 500.0 + (i as f64 * 5.0),
                tier: ((i / 20) + 1).min(5) as u8,
                premium: 50_000.0 + (i as f64 * 1000.0),
                signals: vec![
                    Signal {
                        signal_id: "tls_configuration".to_string(),
                        score: 50.0 + (i as f64 * 0.5),
                        weight: 0.15,
                        group_id: "tech".to_string(),
                        confidence: 1.0,
                    },
                    Signal {
                        signal_id: "security_headers".to_string(),
                        score: 60.0 + (i as f64 * 0.3),
                        weight: 0.10,
                        group_id: "tech".to_string(),
                        confidence: 1.0,
                    },
                ],
                modifiers: vec![],
                limit: 1_000_000.0,
                deductible: 10_000.0,
                product_type: "standard".to_string(),
            });
        }

        snapshot.refresh_metadata();
        snapshot
    }

    #[test]
    fn test_simulation_basic() {
        let mut sim = Simulator::new();
        sim.load_portfolio(create_test_portfolio());

        let shock = ShockParameter::signal_override("tls_configuration", 20.0);
        let result = sim.run_simulation(&shock, 1).unwrap();

        assert!(result.entities_affected > 0);
        assert!(result.total_premium_impact != 0.0);
    }

    #[test]
    fn test_simulation_with_filter() {
        let mut sim = Simulator::new();
        sim.load_portfolio(create_test_portfolio());

        let mut shock = ShockParameter::signal_override("tls_configuration", 0.0);
        shock.filter_industry("Technology");

        let result = sim.run_simulation(&shock, 1).unwrap();

        // Only ~50% of entities are in Technology
        assert!(result.entities_affected > 0);
        assert!(result.entities_affected < 100);
    }

    #[test]
    fn test_multi_shock() {
        let mut sim = Simulator::new();
        sim.load_portfolio(create_test_portfolio());

        let shocks = vec![
            ShockParameter::signal_multiplier("tls_configuration", 0.5),
            ShockParameter::signal_multiplier("security_headers", 0.7),
        ];

        let result = sim.run_multi_shock_simulation(&shocks).unwrap();

        // All entities should be affected
        assert_eq!(result.entities_affected, 100);
        // Premium should increase (worse scores = higher premiums)
        assert!(result.total_premium_impact > 0.0);
    }
}

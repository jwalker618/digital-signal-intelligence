//! DSI Portfolio Snapshot
//!
//! Represents a point-in-time snapshot of all bound entities for simulation.

use serde::{Deserialize, Serialize};
use std::collections::HashMap;

/// Complete portfolio snapshot for simulation
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PortfolioSnapshot {
    /// Snapshot timestamp (ISO 8601)
    pub timestamp: String,
    /// All entities in the portfolio
    pub entities: Vec<Entity>,
    /// Portfolio-level metadata
    #[serde(default)]
    pub metadata: PortfolioMetadata,
}

/// Portfolio metadata
#[derive(Debug, Clone, Default, Serialize, Deserialize)]
pub struct PortfolioMetadata {
    /// Total bound premium
    pub total_premium: f64,
    /// Entity count by coverage
    #[serde(default)]
    pub by_coverage: HashMap<String, usize>,
    /// Entity count by tier
    #[serde(default)]
    pub by_tier: HashMap<u8, usize>,
}

/// Single entity in the portfolio
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Entity {
    /// Unique entity identifier
    pub entity_id: String,
    /// Entity name
    pub entity_name: String,
    /// Coverage type (e.g., "cyber", "fi", "do")
    pub coverage: String,
    /// Configuration used
    pub configuration: String,

    /// Industry classification
    #[serde(default)]
    pub industry: String,
    /// Country/region
    #[serde(default)]
    pub country: String,

    /// Current composite score (0-1000)
    pub composite_score: f64,
    /// Current risk tier (1-5)
    pub tier: u8,
    /// Current bound premium
    pub premium: f64,

    /// All signal values
    pub signals: Vec<Signal>,
    /// Applied modifiers
    #[serde(default)]
    pub modifiers: Vec<Modifier>,

    /// Policy details
    #[serde(default)]
    pub limit: f64,
    #[serde(default)]
    pub deductible: f64,
    #[serde(default)]
    pub product_type: String,
}

/// Individual signal value
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Signal {
    /// Signal identifier
    pub signal_id: String,
    /// Current score (0-100)
    pub score: f64,
    /// Signal weight in composite calculation
    pub weight: f64,
    /// Group this signal belongs to
    pub group_id: String,
    /// Confidence level
    #[serde(default = "default_confidence")]
    pub confidence: f64,
}

fn default_confidence() -> f64 {
    1.0
}

/// Applied modifier
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Modifier {
    /// Modifier source (categorical group ID)
    pub source: String,
    /// Applied factor
    pub factor: f64,
}

impl PortfolioSnapshot {
    /// Create empty snapshot
    pub fn new() -> Self {
        PortfolioSnapshot {
            timestamp: chrono_lite::now_utc(),
            entities: Vec::new(),
            metadata: PortfolioMetadata::default(),
        }
    }

    /// Get entity count
    pub fn entity_count(&self) -> usize {
        self.entities.len()
    }

    /// Get entities by coverage
    pub fn entities_by_coverage(&self, coverage: &str) -> Vec<&Entity> {
        self.entities.iter()
            .filter(|e| e.coverage == coverage)
            .collect()
    }

    /// Get entities by industry
    pub fn entities_by_industry(&self, industry: &str) -> Vec<&Entity> {
        self.entities.iter()
            .filter(|e| e.industry.to_lowercase().contains(&industry.to_lowercase()))
            .collect()
    }

    /// Get entities by tier
    pub fn entities_by_tier(&self, tier: u8) -> Vec<&Entity> {
        self.entities.iter()
            .filter(|e| e.tier == tier)
            .collect()
    }

    /// Calculate total premium
    pub fn total_premium(&self) -> f64 {
        self.entities.iter().map(|e| e.premium).sum()
    }

    /// Get tier distribution
    pub fn tier_distribution(&self) -> HashMap<u8, usize> {
        let mut dist = HashMap::new();
        for entity in &self.entities {
            *dist.entry(entity.tier).or_insert(0) += 1;
        }
        dist
    }

    /// Update metadata from entities
    pub fn refresh_metadata(&mut self) {
        self.metadata.total_premium = self.total_premium();
        self.metadata.by_tier = self.tier_distribution();

        let mut by_coverage: HashMap<String, usize> = HashMap::new();
        for entity in &self.entities {
            *by_coverage.entry(entity.coverage.clone()).or_insert(0) += 1;
        }
        self.metadata.by_coverage = by_coverage;
    }
}

impl Default for PortfolioSnapshot {
    fn default() -> Self {
        Self::new()
    }
}

impl Entity {
    /// Recalculate composite score from signals
    pub fn recalculate_composite(&self) -> f64 {
        let mut total_weighted = 0.0;
        let mut total_weight = 0.0;

        for signal in &self.signals {
            total_weighted += signal.score * signal.weight;
            total_weight += signal.weight;
        }

        if total_weight > 0.0 {
            // Score is on 0-100 scale, composite is 0-1000
            (total_weighted / total_weight) * 10.0
        } else {
            500.0 // Default to middle
        }
    }

    /// Get signal by ID
    pub fn get_signal(&self, signal_id: &str) -> Option<&Signal> {
        self.signals.iter().find(|s| s.signal_id == signal_id)
    }

    /// Get mutable signal by ID
    pub fn get_signal_mut(&mut self, signal_id: &str) -> Option<&mut Signal> {
        self.signals.iter_mut().find(|s| s.signal_id == signal_id)
    }

    /// Clone with modified signal value
    pub fn with_signal_override(&self, signal_id: &str, new_score: f64) -> Entity {
        let mut clone = self.clone();
        if let Some(signal) = clone.get_signal_mut(signal_id) {
            signal.score = new_score.clamp(0.0, 100.0);
        }
        clone
    }

    /// Apply modifier to all signal scores
    pub fn with_signal_multiplier(&self, signal_id: &str, multiplier: f64) -> Entity {
        let mut clone = self.clone();
        if let Some(signal) = clone.get_signal_mut(signal_id) {
            signal.score = (signal.score * multiplier).clamp(0.0, 100.0);
        }
        clone
    }
}

/// Simple chrono replacement for timestamps
mod chrono_lite {
    use std::time::{SystemTime, UNIX_EPOCH};

    pub fn now_utc() -> String {
        let duration = SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .unwrap_or_default();
        let secs = duration.as_secs();

        // Simple ISO 8601 format
        format!("{}", secs)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn create_test_entity() -> Entity {
        Entity {
            entity_id: "test_001".to_string(),
            entity_name: "Test Corp".to_string(),
            coverage: "cyber".to_string(),
            configuration: "cyber_general".to_string(),
            industry: "Technology".to_string(),
            country: "US".to_string(),
            composite_score: 650.0,
            tier: 2,
            premium: 50_000.0,
            signals: vec![
                Signal {
                    signal_id: "tls_configuration".to_string(),
                    score: 80.0,
                    weight: 0.15,
                    group_id: "technical_infrastructure".to_string(),
                    confidence: 0.95,
                },
                Signal {
                    signal_id: "security_headers".to_string(),
                    score: 60.0,
                    weight: 0.10,
                    group_id: "technical_infrastructure".to_string(),
                    confidence: 0.90,
                },
            ],
            modifiers: vec![],
            limit: 1_000_000.0,
            deductible: 10_000.0,
            product_type: "standard".to_string(),
        }
    }

    #[test]
    fn test_signal_override() {
        let entity = create_test_entity();
        let modified = entity.with_signal_override("tls_configuration", 20.0);

        assert_eq!(modified.get_signal("tls_configuration").unwrap().score, 20.0);
        // Original unchanged
        assert_eq!(entity.get_signal("tls_configuration").unwrap().score, 80.0);
    }

    #[test]
    fn test_composite_recalculation() {
        let entity = create_test_entity();
        let composite = entity.recalculate_composite();

        // (80 * 0.15 + 60 * 0.10) / (0.15 + 0.10) * 10 = 720
        let expected = ((80.0 * 0.15 + 60.0 * 0.10) / 0.25) * 10.0;
        assert!((composite - expected).abs() < 0.1);
    }
}

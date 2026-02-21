//! DSI Shock Parameters
//!
//! Defines shock scenarios for portfolio stress testing.
//! A shock represents a hypothetical event that affects signal values.

use serde::{Deserialize, Serialize};

/// Type of shock to apply
#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum ShockType {
    /// Override signal to specific value (e.g., tls_configuration = 0)
    Override(f64),
    /// Multiply signal by factor (e.g., all scores * 0.7)
    Multiplier(f64),
    /// Add/subtract from signal (e.g., -20 points)
    Additive(f64),
    /// Set to percentile of distribution (e.g., 10th percentile)
    Percentile(f64),
}

/// Shock parameter for simulation
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ShockParameter {
    /// Signal ID to shock
    pub signal_id: String,
    /// Type of shock to apply
    pub shock_type: ShockType,
    /// Optional industry filter
    pub industry_filter: Option<String>,
    /// Optional coverage filter
    pub coverage_filter: Option<String>,
    /// Optional tier filter
    pub tier_filter: Option<u8>,
    /// Optional country filter
    pub country_filter: Option<String>,
    /// Description of the shock scenario
    pub description: Option<String>,
}

impl ShockParameter {
    /// Create a signal override shock
    pub fn signal_override(signal_id: &str, new_value: f64) -> Self {
        ShockParameter {
            signal_id: signal_id.to_string(),
            shock_type: ShockType::Override(new_value),
            industry_filter: None,
            coverage_filter: None,
            tier_filter: None,
            country_filter: None,
            description: Some(format!("Override {} to {}", signal_id, new_value)),
        }
    }

    /// Create a signal multiplier shock
    pub fn signal_multiplier(signal_id: &str, multiplier: f64) -> Self {
        ShockParameter {
            signal_id: signal_id.to_string(),
            shock_type: ShockType::Multiplier(multiplier),
            industry_filter: None,
            coverage_filter: None,
            tier_filter: None,
            country_filter: None,
            description: Some(format!("Multiply {} by {}", signal_id, multiplier)),
        }
    }

    /// Create an additive shock
    pub fn signal_additive(signal_id: &str, delta: f64) -> Self {
        ShockParameter {
            signal_id: signal_id.to_string(),
            shock_type: ShockType::Additive(delta),
            industry_filter: None,
            coverage_filter: None,
            tier_filter: None,
            country_filter: None,
            description: Some(format!("Add {} to {}", delta, signal_id)),
        }
    }

    /// Filter shock to specific industry
    pub fn filter_industry(&mut self, industry: &str) {
        self.industry_filter = Some(industry.to_string());
    }

    /// Filter shock to specific coverage
    pub fn filter_coverage(&mut self, coverage: &str) {
        self.coverage_filter = Some(coverage.to_string());
    }

    /// Filter shock to specific tier
    pub fn filter_tier(&mut self, tier: u8) {
        self.tier_filter = Some(tier);
    }

    /// Filter shock to specific country
    pub fn filter_country(&mut self, country: &str) {
        self.country_filter = Some(country.to_string());
    }

    /// Set description
    pub fn with_description(mut self, description: &str) -> Self {
        self.description = Some(description.to_string());
        self
    }

    /// Check if entity matches filters
    pub fn matches_entity(&self, entity: &crate::portfolio::Entity) -> bool {
        // Check industry filter
        if let Some(ref industry) = self.industry_filter {
            if !entity.industry.to_lowercase().contains(&industry.to_lowercase()) {
                return false;
            }
        }

        // Check coverage filter
        if let Some(ref coverage) = self.coverage_filter {
            if entity.coverage != *coverage {
                return false;
            }
        }

        // Check tier filter
        if let Some(tier) = self.tier_filter {
            if entity.tier != tier {
                return false;
            }
        }

        // Check country filter
        if let Some(ref country) = self.country_filter {
            if !entity.country.to_lowercase().contains(&country.to_lowercase()) {
                return false;
            }
        }

        true
    }

    /// Check if entity has the target signal
    pub fn applies_to_entity(&self, entity: &crate::portfolio::Entity) -> bool {
        if !self.matches_entity(entity) {
            return false;
        }

        // Check if entity has the signal
        entity.signals.iter().any(|s| s.signal_id == self.signal_id)
    }

    /// Apply shock to a signal score
    pub fn apply_to_score(&self, current_score: f64) -> f64 {
        let new_score = match self.shock_type {
            ShockType::Override(value) => value,
            ShockType::Multiplier(factor) => current_score * factor,
            ShockType::Additive(delta) => current_score + delta,
            ShockType::Percentile(pct) => {
                // Percentile is approximated as percentage of 100
                pct
            }
        };

        // Clamp to valid range [0, 100]
        new_score.clamp(0.0, 100.0)
    }
}

/// Common shock scenarios
pub mod scenarios {
    use super::*;

    /// CrowdStrike-like outage affecting all tech companies
    pub fn crowdstrike_outage() -> ShockParameter {
        ShockParameter::signal_override("tls_configuration", 10.0)
            .with_description("Major security vendor outage - all TLS scores degraded")
    }

    /// Systemic cyber attack affecting security posture
    pub fn systemic_cyber_attack() -> Vec<ShockParameter> {
        vec![
            ShockParameter::signal_multiplier("tls_configuration", 0.5)
                .with_description("TLS infrastructure compromised"),
            ShockParameter::signal_multiplier("security_headers", 0.6)
                .with_description("Security headers bypassed"),
            ShockParameter::signal_multiplier("waf_presence", 0.4)
                .with_description("WAF ineffective"),
        ]
    }

    /// Economic downturn affecting financial stability
    pub fn economic_downturn() -> Vec<ShockParameter> {
        vec![
            ShockParameter::signal_multiplier("financial_stability", 0.7)
                .with_description("Broad financial stress"),
            ShockParameter::signal_multiplier("regulatory_compliance", 0.85)
                .with_description("Compliance lapses under pressure"),
        ]
    }

    /// Regional disaster affecting specific country
    pub fn regional_disaster(country: &str) -> ShockParameter {
        let mut shock = ShockParameter::signal_multiplier("business_continuity", 0.3)
            .with_description(&format!("Regional disaster in {}", country));
        shock.filter_country(country);
        shock
    }

    /// Industry-specific regulatory change
    pub fn regulatory_change(industry: &str, impact: f64) -> ShockParameter {
        let mut shock = ShockParameter::signal_multiplier("regulatory_compliance", impact)
            .with_description(&format!("Regulatory change affecting {}", industry));
        shock.filter_industry(industry);
        shock
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::portfolio::{Entity, Signal};

    fn create_test_entity() -> Entity {
        Entity {
            entity_id: "test".to_string(),
            entity_name: "Test Corp".to_string(),
            coverage: "cyber".to_string(),
            configuration: "cyber_general".to_string(),
            industry: "Technology".to_string(),
            country: "US".to_string(),
            composite_score: 650.0,
            tier: 2,
            premium: 50_000.0,
            signals: vec![Signal {
                signal_id: "tls_configuration".to_string(),
                score: 80.0,
                weight: 0.15,
                group_id: "tech".to_string(),
                confidence: 1.0,
            }],
            modifiers: vec![],
            limit: 1_000_000.0,
            deductible: 10_000.0,
            product_type: "standard".to_string(),
        }
    }

    #[test]
    fn test_shock_override() {
        let shock = ShockParameter::signal_override("tls_configuration", 20.0);
        assert_eq!(shock.apply_to_score(80.0), 20.0);
    }

    #[test]
    fn test_shock_multiplier() {
        let shock = ShockParameter::signal_multiplier("tls_configuration", 0.5);
        assert_eq!(shock.apply_to_score(80.0), 40.0);
    }

    #[test]
    fn test_shock_filter() {
        let entity = create_test_entity();

        let mut shock = ShockParameter::signal_override("tls_configuration", 0.0);
        assert!(shock.matches_entity(&entity));

        shock.filter_industry("Healthcare");
        assert!(!shock.matches_entity(&entity));

        shock.industry_filter = Some("Technology".to_string());
        assert!(shock.matches_entity(&entity));
    }

    #[test]
    fn test_score_clamping() {
        let shock = ShockParameter::signal_additive("test", 50.0);
        // 80 + 50 = 130, should clamp to 100
        assert_eq!(shock.apply_to_score(80.0), 100.0);

        let shock2 = ShockParameter::signal_additive("test", -100.0);
        // 80 - 100 = -20, should clamp to 0
        assert_eq!(shock2.apply_to_score(80.0), 0.0);
    }
}

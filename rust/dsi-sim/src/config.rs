//! DSI Configuration Parsing
//!
//! Parses Phase 5 config.yaml files into Rust structures for simulation.

use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use std::fs;
use std::path::Path;

/// Complete coverage configuration from config.yaml
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CoverageConfig {
    pub metadata: ConfigMetadata,
    pub signal_registry: Vec<SignalConfig>,
    pub groups: GroupsConfig,
    pub risk_tier_bands: TierBandConfig,
    pub loss_tier_bands: TierBandConfig,
    pub exposure: ExposureConfig,
    pub pricing: PricingConfig,
    #[serde(default)]
    pub limit_configuration: LimitConfig,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ConfigMetadata {
    pub name: String,
    pub version: String,
    #[serde(default)]
    pub product_types: Vec<String>,
    #[serde(default)]
    pub min_premium: f64,
    #[serde(default = "default_currency")]
    pub default_currency: String,
    #[serde(default)]
    pub model_specificity: u8,
}

fn default_currency() -> String {
    "USD".to_string()
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SignalConfig {
    pub id: String,
    #[serde(default)]
    pub inference_utility_function: Option<String>,
    #[serde(default)]
    pub proxy_tier: String,
    #[serde(default)]
    pub expectation_level: Option<String>,
    #[serde(default)]
    pub three_layer_assessment: Option<ThreeLayerAssessment>,
    #[serde(default)]
    pub categories: Option<CategoriesConfig>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ThreeLayerAssessment {
    pub group_id: String,
    #[serde(default)]
    pub risk: Option<DimensionConfig>,
    #[serde(default)]
    pub loss: Option<LossDimensionConfig>,
    #[serde(default)]
    pub exposure: Option<ExposureDimensionConfig>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DimensionConfig {
    #[serde(default = "default_positive")]
    pub correlation_direction: String,
    #[serde(default)]
    pub weight: f64,
}

fn default_positive() -> String {
    "positive".to_string()
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct LossDimensionConfig {
    #[serde(default)]
    pub severity: Option<DimensionConfig>,
    #[serde(default)]
    pub frequency: Option<DimensionConfig>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ExposureDimensionConfig {
    #[serde(default)]
    pub size: Option<DimensionConfig>,
    #[serde(default)]
    pub complexity: Option<DimensionConfig>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CategoriesConfig {
    pub group_id: String,
    #[serde(default)]
    pub features: Vec<CategoryFeature>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CategoryFeature {
    pub cat: String,
    #[serde(default)]
    pub label: String,
    #[serde(default)]
    pub applied: Option<f64>,
    #[serde(default)]
    pub value: Option<f64>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct GroupsConfig {
    #[serde(default)]
    pub three_layer_assessment: Vec<GroupConfig>,
    #[serde(default)]
    pub categories: Vec<CategoryGroupConfig>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct GroupConfig {
    pub id: String,
    pub name: String,
    #[serde(default)]
    pub risk: Option<GroupDimensionConfig>,
    #[serde(default)]
    pub loss: Option<GroupDimensionConfig>,
    #[serde(default)]
    pub exposure: Option<GroupDimensionConfig>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct GroupDimensionConfig {
    #[serde(default)]
    pub weight: f64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CategoryGroupConfig {
    pub id: String,
    pub name: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TierBandConfig {
    pub bands: Vec<TierBand>,
    #[serde(default)]
    pub constraints: TierConstraints,
}

/// Individual tier band definition
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TierBand {
    pub id: u8,
    pub label: String,
    #[serde(default)]
    pub interpretation: TierInterpretation,
}

#[derive(Debug, Clone, Default, Serialize, Deserialize)]
pub struct TierInterpretation {
    #[serde(default)]
    pub bands: ScoreBands,
    #[serde(default)]
    pub application: TierApplication,
}

#[derive(Debug, Clone, Default, Serialize, Deserialize)]
pub struct ScoreBands {
    #[serde(default)]
    pub min: f64,
    #[serde(default = "default_max_score")]
    pub max: f64,
}

fn default_max_score() -> f64 {
    1000.0
}

#[derive(Debug, Clone, Default, Serialize, Deserialize)]
pub struct TierApplication {
    #[serde(default)]
    pub method: String,
    #[serde(default)]
    pub value: f64,
    #[serde(default)]
    pub basis: Option<String>,
}

#[derive(Debug, Clone, Default, Serialize, Deserialize)]
pub struct TierConstraints {
    #[serde(default)]
    pub floor: f64,
    #[serde(default = "default_cap")]
    pub cap: f64,
}

fn default_cap() -> f64 {
    3.0
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ExposureConfig {
    #[serde(default)]
    pub size: ExposureDimension,
    #[serde(default)]
    pub complexity: ExposureDimension,
}

#[derive(Debug, Clone, Default, Serialize, Deserialize)]
pub struct ExposureDimension {
    #[serde(default)]
    pub bands: Vec<ExposureBand>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ExposureBand {
    pub id: u8,
    pub label: String,
    #[serde(default)]
    pub applied: f64,
}

/// Pricing configuration (Phase V5)
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PricingConfig {
    #[serde(default)]
    pub base_limit_reference: f64,
    #[serde(default)]
    pub base_deductible_reference: f64,
    #[serde(default)]
    pub by_product_type: HashMap<String, ProductPricing>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ProductPricing {
    #[serde(default)]
    pub ilf_curve: ILFCurve,
    #[serde(default)]
    pub deductible_factors: Vec<DeductibleFactor>,
}

#[derive(Debug, Clone, Default, Serialize, Deserialize)]
pub struct ILFCurve {
    #[serde(default)]
    pub factors: Vec<LimitFactor>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct LimitFactor {
    pub limit: f64,
    pub factor: f64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DeductibleFactor {
    pub deductible: f64,
    pub factor: f64,
}

#[derive(Debug, Clone, Default, Serialize, Deserialize)]
pub struct LimitConfig {
    #[serde(default)]
    pub mode: String,
    #[serde(default)]
    pub bundled_premium_method: String,
}

impl CoverageConfig {
    /// Load configuration from YAML file
    pub fn from_file<P: AsRef<Path>>(path: P) -> Result<Self, ConfigError> {
        let content = fs::read_to_string(path.as_ref())
            .map_err(|e| ConfigError::IoError(e.to_string()))?;

        Self::from_yaml(&content)
    }

    /// Parse configuration from YAML string
    pub fn from_yaml(yaml: &str) -> Result<Self, ConfigError> {
        // The YAML has a nested structure: {coverage: {config_name: {...}}}
        // We need to extract the inner config
        let root: serde_yaml::Value = serde_yaml::from_str(yaml)
            .map_err(|e| ConfigError::ParseError(e.to_string()))?;

        // Navigate to the actual config (first coverage, first config)
        let config_value = root
            .as_mapping()
            .and_then(|m| m.values().next())
            .and_then(|v| v.as_mapping())
            .and_then(|m| m.values().next())
            .ok_or_else(|| ConfigError::ParseError("Invalid config structure".to_string()))?;

        serde_yaml::from_value(config_value.clone())
            .map_err(|e| ConfigError::ParseError(e.to_string()))
    }

    /// Get signal weight by ID
    pub fn get_signal_weight(&self, signal_id: &str) -> Option<f64> {
        self.signal_registry.iter()
            .find(|s| s.id == signal_id)
            .and_then(|s| s.three_layer_assessment.as_ref())
            .and_then(|tla| tla.risk.as_ref())
            .map(|r| r.weight)
    }

    /// Get tier for a composite score
    pub fn get_tier_for_score(&self, score: f64) -> u8 {
        for band in &self.risk_tier_bands.bands {
            if score >= band.interpretation.bands.min && score <= band.interpretation.bands.max {
                return band.id;
            }
        }
        5 // Default to highest risk tier
    }

    /// Get tier multiplier/rate
    pub fn get_tier_multiplier(&self, tier: u8) -> f64 {
        self.risk_tier_bands.bands.iter()
            .find(|b| b.id == tier)
            .map(|b| b.interpretation.application.value)
            .unwrap_or(1.0)
    }
}

#[derive(Debug)]
pub enum ConfigError {
    IoError(String),
    ParseError(String),
}

impl std::fmt::Display for ConfigError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            ConfigError::IoError(e) => write!(f, "IO error: {}", e),
            ConfigError::ParseError(e) => write!(f, "Parse error: {}", e),
        }
    }
}

impl std::error::Error for ConfigError {}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_tier_lookup() {
        let config = CoverageConfig {
            metadata: ConfigMetadata {
                name: "test".to_string(),
                version: "2.2.0".to_string(),
                product_types: vec![],
                min_premium: 1000.0,
                default_currency: "USD".to_string(),
                model_specificity: 1,
            },
            signal_registry: vec![],
            groups: GroupsConfig {
                three_layer_assessment: vec![],
                categories: vec![],
            },
            risk_tier_bands: TierBandConfig {
                bands: vec![
                    TierBand {
                        id: 1,
                        label: "PREFERRED".to_string(),
                        interpretation: TierInterpretation {
                            bands: ScoreBands { min: 800.0, max: 1000.0 },
                            application: TierApplication { method: "PREMIUM_BASE".to_string(), value: 0.85, basis: None },
                        },
                    },
                    TierBand {
                        id: 5,
                        label: "HIGH_RISK".to_string(),
                        interpretation: TierInterpretation {
                            bands: ScoreBands { min: 0.0, max: 350.0 },
                            application: TierApplication { method: "PREMIUM_BASE".to_string(), value: 2.0, basis: None },
                        },
                    },
                ],
                constraints: TierConstraints::default(),
            },
            loss_tier_bands: TierBandConfig { bands: vec![], constraints: TierConstraints::default() },
            exposure: ExposureConfig { size: ExposureDimension::default(), complexity: ExposureDimension::default() },
            pricing: PricingConfig { base_limit_reference: 1_000_000.0, base_deductible_reference: 10_000.0, by_product_type: HashMap::new() },
            limit_configuration: LimitConfig::default(),
        };

        assert_eq!(config.get_tier_for_score(850.0), 1);
        assert_eq!(config.get_tier_for_score(100.0), 5);
    }
}

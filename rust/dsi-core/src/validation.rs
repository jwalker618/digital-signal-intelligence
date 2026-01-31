//! Configuration validation in Rust
//!
//! Validates v2.0 coverage YAML configurations at native speed.
//! Focuses on the computationally intensive checks:
//! - Score condition format validation
//! - Weight sum verification
//! - Structural compliance

use pyo3::prelude::*;
use pyo3::ToPyObject;
use serde_yaml::Value;
use std::collections::HashMap;

/// Validation issue
#[derive(Clone, Debug)]
struct Issue {
    severity: String, // "error", "warning", "info"
    category: String,
    message: String,
    path: String,
}

impl Issue {
    fn to_dict(&self) -> HashMap<String, String> {
        HashMap::from([
            ("severity".into(), self.severity.clone()),
            ("category".into(), self.category.clone()),
            ("message".into(), self.message.clone()),
            ("path".into(), self.path.clone()),
        ])
    }
}

/// Validate a YAML config string.
///
/// Returns a dict with:
///   valid: bool
///   errors: list of issue dicts
///   warnings: list of issue dicts
///   error_count: int
///   warning_count: int
#[pyfunction]
pub fn validate_config(yaml_content: &str) -> PyResult<HashMap<String, PyObject>> {
    let mut issues: Vec<Issue> = Vec::new();

    // Parse YAML
    let raw: Value = match serde_yaml::from_str(yaml_content) {
        Ok(v) => v,
        Err(e) => {
            issues.push(Issue {
                severity: "error".into(),
                category: "parse".into(),
                message: format!("Failed to parse YAML: {}", e),
                path: "".into(),
            });
            return build_result(&issues);
        }
    };

    // Root must be a mapping
    let root = match raw.as_mapping() {
        Some(m) => m,
        None => {
            issues.push(Issue {
                severity: "error".into(),
                category: "structure".into(),
                message: "Root must be a mapping".into(),
                path: "".into(),
            });
            return build_result(&issues);
        }
    };

    // Get first key (coverage name)
    let (_, coverage_val) = match root.iter().next() {
        Some(kv) => kv,
        None => {
            issues.push(Issue {
                severity: "error".into(),
                category: "structure".into(),
                message: "Empty root mapping".into(),
                path: "".into(),
            });
            return build_result(&issues);
        }
    };

    // Get config (nested under coverage)
    let coverage_map = match coverage_val.as_mapping() {
        Some(m) => m,
        None => {
            issues.push(Issue {
                severity: "error".into(),
                category: "structure".into(),
                message: "Coverage value must be a mapping".into(),
                path: "".into(),
            });
            return build_result(&issues);
        }
    };

    let (_, config_val) = match coverage_map.iter().next() {
        Some(kv) => kv,
        None => {
            issues.push(Issue {
                severity: "error".into(),
                category: "structure".into(),
                message: "Empty coverage mapping".into(),
                path: "".into(),
            });
            return build_result(&issues);
        }
    };

    let config = match config_val.as_mapping() {
        Some(m) => m,
        None => {
            issues.push(Issue {
                severity: "error".into(),
                category: "structure".into(),
                message: "Config must be a mapping".into(),
                path: "".into(),
            });
            return build_result(&issues);
        }
    };

    // Check required sections
    let has_groups = config.get(Value::String("signal_groups".into())).is_some();
    let has_registry = config.get(Value::String("signal_registry".into())).is_some();
    if !has_groups && !has_registry {
        issues.push(Issue {
            severity: "error".into(),
            category: "signal_groups".into(),
            message: "Missing signal_groups or signal_registry".into(),
            path: "".into(),
        });
    }

    let has_tiers = config.get(Value::String("tier_thresholds".into())).is_some();
    let has_risk_tiers = config.get(Value::String("risk_tier_bands".into())).is_some();
    if !has_tiers && !has_risk_tiers {
        issues.push(Issue {
            severity: "error".into(),
            category: "tiers".into(),
            message: "Missing tier_thresholds or risk_tier_bands".into(),
            path: "".into(),
        });
    }

    // Validate score_conditions format (no DECLINE, valid actions)
    validate_score_conditions_internal(config, &mut issues);

    // Validate weight sums
    validate_weights_internal(config, &mut issues);

    build_result(&issues)
}

fn validate_score_conditions_internal(config: &serde_yaml::Mapping, issues: &mut Vec<Issue>) {
    let valid_actions = ["FLAG", "MODIFIER", "REFER"];

    // Check signal_groups
    if let Some(groups) = config.get(Value::String("signal_groups".into())) {
        if let Some(groups_seq) = groups.as_sequence() {
            for group in groups_seq {
                let gid = group.get(Value::String("id".into()))
                    .and_then(|v| v.as_str())
                    .unwrap_or("?");

                if let Some(sc) = group.get(Value::String("score_conditions".into())) {
                    if sc.is_bool() {
                        issues.push(Issue {
                            severity: "error".into(),
                            category: "score_conditions".into(),
                            message: format!(
                                "Group '{}' uses boolean score_conditions (v1.0). Must be a list.",
                                gid
                            ),
                            path: format!("signal_groups.{}.score_conditions", gid),
                        });
                    } else if let Some(conds) = sc.as_sequence() {
                        check_conditions(conds, &format!("signal_groups.{}", gid), &valid_actions, issues);
                    }
                }
            }
        }
    }

    // Check signal_features
    if let Some(features) = config.get(Value::String("signal_features".into())) {
        if let Some(features_map) = features.as_mapping() {
            for (gid_val, feat_list) in features_map {
                let gid = gid_val.as_str().unwrap_or("?");
                if let Some(feats) = feat_list.as_sequence() {
                    for feat in feats {
                        let fid = feat.get(Value::String("id".into()))
                            .and_then(|v| v.as_str())
                            .unwrap_or("?");

                        if let Some(sc) = feat.get(Value::String("score_conditions".into())) {
                            if sc.is_bool() {
                                issues.push(Issue {
                                    severity: "error".into(),
                                    category: "score_conditions".into(),
                                    message: format!(
                                        "Feature '{}' uses boolean score_conditions (v1.0)",
                                        fid
                                    ),
                                    path: format!("signal_features.{}.{}", gid, fid),
                                });
                            } else if let Some(conds) = sc.as_sequence() {
                                check_conditions(
                                    conds,
                                    &format!("signal_features.{}.{}", gid, fid),
                                    &valid_actions,
                                    issues,
                                );
                            }
                        }
                    }
                }
            }
        }
    }
}

fn check_conditions(
    conditions: &serde_yaml::Sequence,
    path: &str,
    valid_actions: &[&str],
    issues: &mut Vec<Issue>,
) {
    for (i, cond) in conditions.iter().enumerate() {
        let cpath = format!("{}.score_conditions[{}]", path, i);
        let cond_map = match cond.as_mapping() {
            Some(m) => m,
            None => {
                issues.push(Issue {
                    severity: "error".into(),
                    category: "score_conditions".into(),
                    message: format!("Condition must be a mapping at {}", cpath),
                    path: cpath,
                });
                continue;
            }
        };

        if !cond_map.contains_key(Value::String("threshold".into())) {
            issues.push(Issue {
                severity: "error".into(),
                category: "score_conditions".into(),
                message: format!("Missing 'threshold' at {}", cpath),
                path: cpath.clone(),
            });
        }

        if let Some(action_val) = cond_map.get(Value::String("action".into())) {
            let action = action_val.as_str().unwrap_or("");
            if action == "DECLINE" {
                issues.push(Issue {
                    severity: "error".into(),
                    category: "score_conditions".into(),
                    message: format!(
                        "DECLINE in score_conditions at {}. DECLINE is tier-level only.",
                        cpath
                    ),
                    path: cpath.clone(),
                });
            } else if !valid_actions.contains(&action) {
                issues.push(Issue {
                    severity: "error".into(),
                    category: "score_conditions".into(),
                    message: format!("Invalid action '{}' at {}", action, cpath),
                    path: cpath.clone(),
                });
            }
        } else {
            issues.push(Issue {
                severity: "error".into(),
                category: "score_conditions".into(),
                message: format!("Missing 'action' at {}", cpath),
                path: cpath,
            });
        }
    }
}

fn validate_weights_internal(config: &serde_yaml::Mapping, issues: &mut Vec<Issue>) {
    if let Some(groups) = config.get(Value::String("signal_groups".into())) {
        if let Some(groups_seq) = groups.as_sequence() {
            let total: f64 = groups_seq.iter()
                .filter_map(|g| {
                    g.get(Value::String("weight".into()))
                        .and_then(|v| v.as_f64())
                })
                .sum();

            if (total - 1.0).abs() > 0.01 {
                issues.push(Issue {
                    severity: "error".into(),
                    category: "weights".into(),
                    message: format!(
                        "Signal group weights sum to {:.3}, expected ~1.0",
                        total
                    ),
                    path: "signal_groups".into(),
                });
            }
        }
    }
}

/// Validate score_conditions from a YAML string.
///
/// Returns list of issue dicts.
#[pyfunction]
pub fn validate_score_conditions(yaml_content: &str) -> PyResult<Vec<HashMap<String, String>>> {
    let raw: Value = serde_yaml::from_str(yaml_content)
        .map_err(|e| pyo3::exceptions::PyValueError::new_err(format!("YAML parse error: {}", e)))?;

    let root = raw.as_mapping()
        .ok_or_else(|| pyo3::exceptions::PyValueError::new_err("Root must be a mapping"))?;

    let (_, coverage_val) = root.iter().next()
        .ok_or_else(|| pyo3::exceptions::PyValueError::new_err("Empty root"))?;

    let coverage_map = coverage_val.as_mapping()
        .ok_or_else(|| pyo3::exceptions::PyValueError::new_err("Coverage must be a mapping"))?;

    let (_, config_val) = coverage_map.iter().next()
        .ok_or_else(|| pyo3::exceptions::PyValueError::new_err("Empty coverage"))?;

    let config = config_val.as_mapping()
        .ok_or_else(|| pyo3::exceptions::PyValueError::new_err("Config must be a mapping"))?;

    let mut issues: Vec<Issue> = Vec::new();
    validate_score_conditions_internal(config, &mut issues);

    Ok(issues.iter().map(|i| i.to_dict()).collect())
}

/// Validate weight sums from a YAML string.
///
/// Returns list of issue dicts.
#[pyfunction]
pub fn validate_weight_sums(yaml_content: &str) -> PyResult<Vec<HashMap<String, String>>> {
    let raw: Value = serde_yaml::from_str(yaml_content)
        .map_err(|e| pyo3::exceptions::PyValueError::new_err(format!("YAML parse error: {}", e)))?;

    let root = raw.as_mapping()
        .ok_or_else(|| pyo3::exceptions::PyValueError::new_err("Root must be a mapping"))?;

    let (_, coverage_val) = root.iter().next()
        .ok_or_else(|| pyo3::exceptions::PyValueError::new_err("Empty root"))?;

    let coverage_map = coverage_val.as_mapping()
        .ok_or_else(|| pyo3::exceptions::PyValueError::new_err("Coverage must be a mapping"))?;

    let (_, config_val) = coverage_map.iter().next()
        .ok_or_else(|| pyo3::exceptions::PyValueError::new_err("Empty coverage"))?;

    let config = config_val.as_mapping()
        .ok_or_else(|| pyo3::exceptions::PyValueError::new_err("Config must be a mapping"))?;

    let mut issues: Vec<Issue> = Vec::new();
    validate_weights_internal(config, &mut issues);

    Ok(issues.iter().map(|i| i.to_dict()).collect())
}

fn build_result(issues: &[Issue]) -> PyResult<HashMap<String, PyObject>> {
    Python::with_gil(|py| {
        let errors: Vec<HashMap<String, String>> = issues.iter()
            .filter(|i| i.severity == "error")
            .map(|i| i.to_dict())
            .collect();

        let warnings: Vec<HashMap<String, String>> = issues.iter()
            .filter(|i| i.severity == "warning")
            .map(|i| i.to_dict())
            .collect();

        let error_count = errors.len();
        let warning_count = warnings.len();

        let mut result = HashMap::new();
        result.insert("valid".into(), (error_count == 0).to_object(py));
        result.insert("errors".into(), errors.to_object(py));
        result.insert("warnings".into(), warnings.to_object(py));
        result.insert("error_count".into(), error_count.to_object(py));
        result.insert("warning_count".into(), warning_count.to_object(py));

        Ok(result)
    })
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_concentration_hhi() {
        let targets = vec!["a", "a", "b", "b"];
        let mut counts: HashMap<&str, usize> = HashMap::new();
        for t in &targets {
            *counts.entry(t).or_insert(0) += 1;
        }
        let total = targets.len() as f64;
        let hhi: f64 = counts.values()
            .map(|&c| { let s = c as f64 / total; s * s })
            .sum();
        assert_eq!(hhi, 0.5);
    }

    #[test]
    fn test_weight_check() {
        let yaml = r#"
coverage:
  config:
    signal_groups:
      - id: g1
        weight: 0.5
      - id: g2
        weight: 0.5
"#;
        let raw: Value = serde_yaml::from_str(yaml).unwrap();
        let root = raw.as_mapping().unwrap();
        let (_, cv) = root.iter().next().unwrap();
        let cm = cv.as_mapping().unwrap();
        let (_, config_val) = cm.iter().next().unwrap();
        let config = config_val.as_mapping().unwrap();

        let mut issues = Vec::new();
        validate_weights_internal(config, &mut issues);
        assert!(issues.is_empty()); // Weights sum to 1.0
    }
}

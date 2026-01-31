//! Behavioural derivative calculations in Rust
//!
//! Implements the five derivatives from schemas/organisational_graph.yaml:
//! - Entropy (control decay)
//! - Velocity (operational overload)
//! - Drift (peer divergence)
//! - Concentration (single-point-of-failure / HHI)
//! - Fragility (composite resilience)
//!
//! Target: 5-20x speedup over Python for large signal sets.

use pyo3::prelude::*;
use pyo3::ToPyObject;
use std::collections::HashMap;

/// Result of a derivative calculation
#[derive(Clone, Debug)]
struct DerivativeResult {
    name: String,
    value: f64,
    warning_threshold: f64,
    critical_threshold: f64,
    components: HashMap<String, f64>,
}

impl DerivativeResult {
    fn to_dict(&self) -> HashMap<String, PyObject> {
        Python::with_gil(|py| {
            let mut d = HashMap::new();
            d.insert("name".into(), self.name.to_object(py));
            d.insert("value".into(), self.value.to_object(py));
            d.insert("warning_threshold".into(), self.warning_threshold.to_object(py));
            d.insert("critical_threshold".into(), self.critical_threshold.to_object(py));
            d.insert("is_warning".into(), (self.value >= self.warning_threshold).to_object(py));
            d.insert("is_critical".into(), (self.value >= self.critical_threshold).to_object(py));

            let status = if self.value >= self.critical_threshold {
                "CRITICAL"
            } else if self.value >= self.warning_threshold {
                "WARNING"
            } else {
                "NORMAL"
            };
            d.insert("status".into(), status.to_object(py));
            d
        })
    }
}

/// Compute entropy: control decay indicator.
///
/// Args:
///   signal_values: List of signal values (from tech/corporate categories)
///
/// Returns dict with value, status, thresholds, components.
#[pyfunction]
pub fn compute_entropy(signal_values: Vec<f64>) -> PyResult<HashMap<String, PyObject>> {
    let result = entropy_internal(&signal_values);
    Ok(result.to_dict())
}

fn entropy_internal(signal_values: &[f64]) -> DerivativeResult {
    if signal_values.len() < 2 {
        return DerivativeResult {
            name: "entropy".into(),
            value: 0.0,
            warning_threshold: 0.15,
            critical_threshold: 0.30,
            components: HashMap::from([
                ("signal_count".into(), signal_values.len() as f64),
            ]),
        };
    }

    // Compute deltas
    let deltas: Vec<f64> = signal_values.windows(2)
        .map(|w| (w[1] - w[0]).abs())
        .collect();

    if deltas.is_empty() {
        return DerivativeResult {
            name: "entropy".into(),
            value: 0.0,
            warning_threshold: 0.15,
            critical_threshold: 0.30,
            components: HashMap::new(),
        };
    }

    let mean_delta: f64 = deltas.iter().sum::<f64>() / deltas.len() as f64;
    let variance: f64 = deltas.iter()
        .map(|d| (d - mean_delta).powi(2))
        .sum::<f64>() / deltas.len() as f64;
    let stddev = variance.sqrt();

    // Normalize to 0-1 scale (signal range is 0-100)
    let entropy_value = stddev / 100.0;

    DerivativeResult {
        name: "entropy".into(),
        value: entropy_value,
        warning_threshold: 0.15,
        critical_threshold: 0.30,
        components: HashMap::from([
            ("mean_delta".into(), mean_delta),
            ("stddev".into(), stddev),
            ("signal_count".into(), signal_values.len() as f64),
        ]),
    }
}

/// Compute velocity: operational overload indicator.
///
/// Args:
///   change_signals: Signal values indicating rapid change
///   governance_signals: Signal values indicating governance capacity
///
/// Returns dict with value, status, thresholds, components.
#[pyfunction]
pub fn compute_velocity(
    change_signals: Vec<f64>,
    governance_signals: Vec<f64>,
) -> PyResult<HashMap<String, PyObject>> {
    let result = velocity_internal(&change_signals, &governance_signals);
    Ok(result.to_dict())
}

fn velocity_internal(change_signals: &[f64], governance_signals: &[f64]) -> DerivativeResult {
    let change_rate = if change_signals.is_empty() {
        50.0
    } else {
        change_signals.iter().sum::<f64>() / change_signals.len() as f64
    };

    let governance_rate = if governance_signals.is_empty() {
        50.0
    } else {
        governance_signals.iter().sum::<f64>() / governance_signals.len() as f64
    };

    let velocity = change_rate / governance_rate.max(1.0);

    DerivativeResult {
        name: "velocity".into(),
        value: velocity,
        warning_threshold: 1.5,
        critical_threshold: 2.5,
        components: HashMap::from([
            ("change_rate".into(), change_rate),
            ("governance_rate".into(), governance_rate),
            ("change_signal_count".into(), change_signals.len() as f64),
            ("governance_signal_count".into(), governance_signals.len() as f64),
        ]),
    }
}

/// Compute drift: peer divergence indicator (Mahalanobis distance).
///
/// Args:
///   signal_values: Dict of signal_id → value
///   cohort_means: Dict of signal_id → cohort mean (optional)
///   cohort_stddevs: Dict of signal_id → cohort stddev (optional)
///
/// Returns dict with value, status, thresholds, components.
#[pyfunction]
#[pyo3(signature = (signal_values, cohort_means=None, cohort_stddevs=None))]
pub fn compute_drift(
    signal_values: HashMap<String, f64>,
    cohort_means: Option<HashMap<String, f64>>,
    cohort_stddevs: Option<HashMap<String, f64>>,
) -> PyResult<HashMap<String, PyObject>> {
    let result = drift_internal(&signal_values, &cohort_means, &cohort_stddevs);
    Ok(result.to_dict())
}

fn drift_internal(
    signal_values: &HashMap<String, f64>,
    cohort_means: &Option<HashMap<String, f64>>,
    cohort_stddevs: &Option<HashMap<String, f64>>,
) -> DerivativeResult {
    if signal_values.is_empty() {
        return DerivativeResult {
            name: "drift".into(),
            value: 0.0,
            warning_threshold: 2.0,
            critical_threshold: 3.0,
            components: HashMap::new(),
        };
    }

    let drift = if let (Some(means), Some(stddevs)) = (cohort_means, cohort_stddevs) {
        let z_scores: Vec<f64> = signal_values.iter()
            .filter_map(|(id, &val)| {
                let mean = means.get(id)?;
                let std = stddevs.get(id)?;
                if *std > 0.0 {
                    Some(((val - mean) / std).abs())
                } else {
                    None
                }
            })
            .collect();

        if z_scores.is_empty() {
            0.0
        } else {
            // Root mean square of z-scores
            (z_scores.iter().map(|z| z * z).sum::<f64>() / z_scores.len() as f64).sqrt()
        }
    } else {
        // Without cohort data: estimate from signal variance
        let values: Vec<f64> = signal_values.values().copied().collect();
        let mean = values.iter().sum::<f64>() / values.len() as f64;
        let variance = values.iter()
            .map(|v| (v - mean).powi(2))
            .sum::<f64>() / values.len() as f64;
        variance.sqrt() / mean.max(1.0)
    };

    DerivativeResult {
        name: "drift".into(),
        value: drift,
        warning_threshold: 2.0,
        critical_threshold: 3.0,
        components: HashMap::from([
            ("signal_count".into(), signal_values.len() as f64),
            ("cohort_available".into(), if cohort_means.is_some() { 1.0 } else { 0.0 }),
        ]),
    }
}

/// Compute concentration: single-point-of-failure indicator (HHI).
///
/// Args:
///   dependency_targets: List of target node IDs for dependency/data_flow edges
///
/// Returns dict with value, status, thresholds, components.
#[pyfunction]
pub fn compute_concentration(
    dependency_targets: Vec<String>,
) -> PyResult<HashMap<String, PyObject>> {
    let result = concentration_internal(&dependency_targets);
    Ok(result.to_dict())
}

fn concentration_internal(dependency_targets: &[String]) -> DerivativeResult {
    if dependency_targets.is_empty() {
        return DerivativeResult {
            name: "concentration".into(),
            value: 0.0,
            warning_threshold: 0.25,
            critical_threshold: 0.50,
            components: HashMap::from([("dependency_count".into(), 0.0)]),
        };
    }

    // Count occurrences of each target
    let mut counts: HashMap<&str, usize> = HashMap::new();
    for target in dependency_targets {
        *counts.entry(target.as_str()).or_insert(0) += 1;
    }

    let total = dependency_targets.len() as f64;
    let hhi: f64 = counts.values()
        .map(|&c| {
            let share = c as f64 / total;
            share * share
        })
        .sum();

    DerivativeResult {
        name: "concentration".into(),
        value: hhi,
        warning_threshold: 0.25,
        critical_threshold: 0.50,
        components: HashMap::from([
            ("dependency_count".into(), dependency_targets.len() as f64),
            ("unique_targets".into(), counts.len() as f64),
            ("hhi".into(), hhi),
        ]),
    }
}

/// Compute fragility: composite resilience indicator.
///
/// Args:
///   entropy_value: Entropy derivative value
///   velocity_value: Velocity derivative value
///   concentration_value: Concentration derivative value
///   infra_health: Average infrastructure signal score (0-100)
///
/// Returns dict with value, status, thresholds, components.
#[pyfunction]
#[pyo3(signature = (entropy_value, velocity_value, concentration_value, infra_health=50.0))]
pub fn compute_fragility(
    entropy_value: f64,
    velocity_value: f64,
    concentration_value: f64,
    infra_health: f64,
) -> PyResult<HashMap<String, PyObject>> {
    let result = fragility_internal(entropy_value, velocity_value, concentration_value, infra_health);
    Ok(result.to_dict())
}

fn fragility_internal(
    entropy_value: f64,
    velocity_value: f64,
    concentration_value: f64,
    infra_health: f64,
) -> DerivativeResult {
    // Normalize to 0-1
    let entropy_norm = (entropy_value / 0.30).min(1.0); // critical threshold
    let velocity_norm = (velocity_value / 2.5).min(1.0); // critical threshold
    let concentration_norm = concentration_value; // already 0-1
    let infra_fragility = 1.0 - (infra_health / 100.0).clamp(0.0, 1.0);

    let fragility = 0.30 * entropy_norm
        + 0.25 * velocity_norm
        + 0.25 * concentration_norm
        + 0.20 * infra_fragility;

    DerivativeResult {
        name: "fragility".into(),
        value: fragility,
        warning_threshold: 0.40,
        critical_threshold: 0.65,
        components: HashMap::from([
            ("entropy_contribution".into(), 0.30 * entropy_norm),
            ("velocity_contribution".into(), 0.25 * velocity_norm),
            ("concentration_contribution".into(), 0.25 * concentration_norm),
            ("infrastructure_contribution".into(), 0.20 * infra_fragility),
        ]),
    }
}

/// Compute all five derivatives at once.
///
/// Args:
///   signal_values: All signal values (ordered)
///   change_signals: Growth/expansion signals
///   governance_signals: Governance/compliance signals
///   signal_map: signal_id → value mapping
///   dependency_targets: List of dependency target IDs
///   infra_health: Average infrastructure score
///   cohort_means: Optional cohort means
///   cohort_stddevs: Optional cohort stddevs
///
/// Returns dict of derivative_name → result dict.
#[pyfunction]
#[pyo3(signature = (signal_values, change_signals, governance_signals, signal_map, dependency_targets, infra_health=50.0, cohort_means=None, cohort_stddevs=None))]
pub fn compute_all_derivatives(
    signal_values: Vec<f64>,
    change_signals: Vec<f64>,
    governance_signals: Vec<f64>,
    signal_map: HashMap<String, f64>,
    dependency_targets: Vec<String>,
    infra_health: f64,
    cohort_means: Option<HashMap<String, f64>>,
    cohort_stddevs: Option<HashMap<String, f64>>,
) -> PyResult<HashMap<String, HashMap<String, PyObject>>> {
    let entropy = entropy_internal(&signal_values);
    let velocity = velocity_internal(&change_signals, &governance_signals);
    let drift = drift_internal(&signal_map, &cohort_means, &cohort_stddevs);
    let concentration = concentration_internal(&dependency_targets);
    let fragility = fragility_internal(
        entropy.value,
        velocity.value,
        concentration.value,
        infra_health,
    );

    let mut results = HashMap::new();
    results.insert("entropy".into(), entropy.to_dict());
    results.insert("velocity".into(), velocity.to_dict());
    results.insert("drift".into(), drift.to_dict());
    results.insert("concentration".into(), concentration.to_dict());
    results.insert("fragility".into(), fragility.to_dict());

    Ok(results)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_entropy_stable() {
        let values = vec![50.0, 50.0, 50.0, 50.0];
        let result = entropy_internal(&values);
        assert_eq!(result.value, 0.0);
        assert_eq!(result.name, "entropy");
    }

    #[test]
    fn test_entropy_chaotic() {
        let values = vec![10.0, 90.0, 20.0, 80.0, 15.0, 85.0];
        let result = entropy_internal(&values);
        assert!(result.value > 0.0);
    }

    #[test]
    fn test_velocity_balanced() {
        let change = vec![50.0, 50.0];
        let governance = vec![50.0, 50.0];
        let result = velocity_internal(&change, &governance);
        assert!((result.value - 1.0).abs() < 0.001);
    }

    #[test]
    fn test_concentration_diverse() {
        let targets = vec!["a".into(), "b".into(), "c".into(), "d".into()];
        let result = concentration_internal(&targets);
        assert_eq!(result.value, 0.25); // 4 equal = HHI of 0.25
    }

    #[test]
    fn test_concentration_monopoly() {
        let targets = vec!["a".into(), "a".into(), "a".into()];
        let result = concentration_internal(&targets);
        assert_eq!(result.value, 1.0); // All same = HHI of 1.0
    }

    #[test]
    fn test_fragility_low() {
        let result = fragility_internal(0.0, 1.0, 0.0, 80.0);
        assert!(result.value < 0.40); // Should be NORMAL
    }
}

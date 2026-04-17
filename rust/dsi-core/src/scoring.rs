//! V6/E1 Stage 5.2 — Rust port of `layers/risk/_scoring_spec.py`.
//!
//! The algorithm here must match `compute_composite` in the Python
//! pure-function spec bit-for-bit (within the 1e-9 abs tolerance
//! documented in `_scoring_spec.py`). The parity CI job replays
//! golden fixtures through both implementations and fails on any
//! divergence exceeding that bound.
//!
//! Design rules inherited from the Python spec:
//! - Deterministic: no time, randomness, or HashMap iteration order
//!   dependence. We iterate over `group_weights` in caller-supplied
//!   order; within-group iteration follows input order.
//! - No I/O. Inputs are plain structs; output is a plain struct.
//! - Every branch maps 1:1 to the Python reference.

use pyo3::prelude::*;
use std::collections::HashMap;

/// Neutral score used when a group has no signals or zero total weight.
pub const DEFAULT_SCORE: f64 = 50.0;
/// Neutral confidence used when total expected signals is zero.
pub const DEFAULT_CONFIDENCE: f64 = 0.5;
/// Scales group scores into the 0..1000 composite window.
pub const COMPOSITE_SCALE: f64 = 10.0;


#[pyclass(get_all, set_all)]
#[derive(Clone)]
pub struct SignalInput {
    pub signal_id: String,
    pub group_id: String,
    pub raw_score: f64,
    pub weight: f64,
    pub confidence: f64,
    pub populated: bool,
}

#[pymethods]
impl SignalInput {
    #[new]
    fn new(
        signal_id: String,
        group_id: String,
        raw_score: f64,
        weight: f64,
        confidence: f64,
        populated: bool,
    ) -> Self {
        Self { signal_id, group_id, raw_score, weight, confidence, populated }
    }
}


#[pyclass(get_all, set_all)]
#[derive(Clone)]
pub struct GroupWeight {
    pub group_id: String,
    pub risk_weight: f64,
    pub expected_signal_count: u32,
}

#[pymethods]
impl GroupWeight {
    #[new]
    fn new(group_id: String, risk_weight: f64, expected_signal_count: u32) -> Self {
        Self { group_id, risk_weight, expected_signal_count }
    }
}


#[pyclass(get_all)]
#[derive(Clone)]
pub struct GroupScore {
    pub group_id: String,
    pub group_score: f64,
    pub risk_weight: f64,
    pub risk_contribution: f64,
    pub signal_count: u32,
    pub expected_signal_count: u32,
    pub coverage_ratio: f64,
}


#[pyclass(get_all)]
#[derive(Clone)]
pub struct CompositeResult {
    pub composite_score: f64,
    pub group_scores: Vec<GroupScore>,
    pub overall_confidence: f64,
    pub signal_coverage: f64,
}


/// Pure scoring function. Mirrors `_scoring_spec.compute_composite`.
#[pyfunction]
#[pyo3(signature = (signals, group_weights, default_score=DEFAULT_SCORE, default_confidence=DEFAULT_CONFIDENCE))]
pub fn compute_composite(
    signals: Vec<SignalInput>,
    group_weights: Vec<GroupWeight>,
    default_score: f64,
    default_confidence: f64,
) -> CompositeResult {
    // 1. Bucket signals by group_id. We collect indices into `signals`
    //    rather than cloning, so the relative within-group order is
    //    preserved.
    let mut buckets: HashMap<&str, Vec<&SignalInput>> = HashMap::new();
    for s in &signals {
        buckets.entry(s.group_id.as_str()).or_default().push(s);
    }

    let mut out_groups: Vec<GroupScore> = Vec::with_capacity(group_weights.len());
    let mut total_expected: u64 = 0;
    let mut total_populated: u64 = 0;
    let mut confidence_accumulator: f64 = 0.0;

    for gw in &group_weights {
        let bucket = buckets.get(gw.group_id.as_str());
        let actual_count = bucket.map(|b| b.len()).unwrap_or(0);
        total_expected += gw.expected_signal_count as u64;

        let (group_score, populated_in_group) = match bucket {
            Some(b) if !b.is_empty() => {
                let mut total_weighted = 0.0;
                let mut total_weight = 0.0;
                let mut conf_sum = 0.0;
                let mut populated = 0u64;
                for s in b {
                    total_weighted += s.raw_score * s.weight;
                    total_weight += s.weight;
                    conf_sum += s.confidence;
                    if s.populated {
                        populated += 1;
                    }
                }
                let gs = if total_weight > 0.0 {
                    total_weighted / total_weight
                } else {
                    default_score
                };
                let avg_conf = conf_sum / (actual_count as f64);
                confidence_accumulator += avg_conf * (actual_count as f64);
                total_populated += populated;
                (gs, populated)
            }
            _ => (default_score, 0u64),
        };

        let risk_contribution = group_score * gw.risk_weight * COMPOSITE_SCALE;
        let coverage_ratio = if gw.expected_signal_count > 0 {
            (populated_in_group as f64) / (gw.expected_signal_count as f64)
        } else {
            0.0
        };

        out_groups.push(GroupScore {
            group_id: gw.group_id.clone(),
            group_score,
            risk_weight: gw.risk_weight,
            risk_contribution,
            signal_count: actual_count as u32,
            expected_signal_count: gw.expected_signal_count,
            coverage_ratio,
        });
    }

    let composite: f64 = out_groups.iter().map(|g| g.risk_contribution).sum();

    let (overall_conf, coverage) = if total_expected > 0 {
        (
            confidence_accumulator / (total_expected as f64),
            (total_populated as f64) / (total_expected as f64),
        )
    } else {
        (default_confidence, 0.0)
    };

    CompositeResult {
        composite_score: composite,
        group_scores: out_groups,
        overall_confidence: overall_conf,
        signal_coverage: coverage,
    }
}


// Rust-side unit tests live in the parity test
// `tests/unit/test_scoring_parity.py` which drives the Rust
// implementation from Python (the PyO3 extension cannot be linked
// from `cargo test` without pulling in libpython).

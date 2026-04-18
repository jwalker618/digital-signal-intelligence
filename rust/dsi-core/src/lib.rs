//! DSI Core - Performance-critical components for Digital Signal Intelligence
//!
//! Provides Rust implementations of:
//! - Graph computations (PageRank, risk propagation)
//! - Behavioural derivative calculations (entropy, velocity, drift, concentration, fragility)
//! - Configuration validation
//!
//! Exposed to Python via PyO3 bindings.

use pyo3::prelude::*;

pub mod graph;
pub mod derivatives;
pub mod validation;
pub mod scoring;

/// DSI Core Python module
#[pymodule]
fn dsi_core(m: &Bound<'_, PyModule>) -> PyResult<()> {
    // Graph submodule
    let graph_module = PyModule::new_bound(m.py(), "graph")?;
    graph_module.add_class::<graph::PyGraph>()?;
    graph_module.add_class::<graph::PyNode>()?;
    graph_module.add_class::<graph::PyEdge>()?;
    graph_module.add_function(wrap_pyfunction!(graph::pagerank, &graph_module)?)?;
    graph_module.add_function(wrap_pyfunction!(graph::risk_propagation, &graph_module)?)?;
    graph_module.add_function(wrap_pyfunction!(graph::exposure_aggregation, &graph_module)?)?;
    m.add_submodule(&graph_module)?;

    // Derivatives submodule
    let deriv_module = PyModule::new_bound(m.py(), "derivatives")?;
    deriv_module.add_function(wrap_pyfunction!(derivatives::compute_entropy, &deriv_module)?)?;
    deriv_module.add_function(wrap_pyfunction!(derivatives::compute_velocity, &deriv_module)?)?;
    deriv_module.add_function(wrap_pyfunction!(derivatives::compute_drift, &deriv_module)?)?;
    deriv_module.add_function(wrap_pyfunction!(derivatives::compute_concentration, &deriv_module)?)?;
    deriv_module.add_function(wrap_pyfunction!(derivatives::compute_fragility, &deriv_module)?)?;
    deriv_module.add_function(wrap_pyfunction!(derivatives::compute_all_derivatives, &deriv_module)?)?;
    m.add_submodule(&deriv_module)?;

    // Validation submodule
    let valid_module = PyModule::new_bound(m.py(), "validation")?;
    valid_module.add_function(wrap_pyfunction!(validation::validate_config, &valid_module)?)?;
    valid_module.add_function(wrap_pyfunction!(validation::validate_score_conditions, &valid_module)?)?;
    valid_module.add_function(wrap_pyfunction!(validation::validate_weight_sums, &valid_module)?)?;
    m.add_submodule(&valid_module)?;

    // Scoring submodule (V6/E1 Stage 5.2+)
    let scoring_module = PyModule::new_bound(m.py(), "scoring")?;
    scoring_module.add_class::<scoring::SignalInput>()?;
    scoring_module.add_class::<scoring::GroupWeight>()?;
    scoring_module.add_class::<scoring::GroupScore>()?;
    scoring_module.add_class::<scoring::CompositeResult>()?;
    scoring_module.add_function(wrap_pyfunction!(scoring::compute_composite, &scoring_module)?)?;
    scoring_module.add("DEFAULT_SCORE", scoring::DEFAULT_SCORE)?;
    scoring_module.add("DEFAULT_CONFIDENCE", scoring::DEFAULT_CONFIDENCE)?;
    scoring_module.add("COMPOSITE_SCALE", scoring::COMPOSITE_SCALE)?;
    m.add_submodule(&scoring_module)?;

    Ok(())
}

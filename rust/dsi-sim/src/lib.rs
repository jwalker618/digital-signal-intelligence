//! DSI Monte Carlo Portfolio Simulation Engine
//!
//! Phase 11: Vision Paper Implementation
//!
//! This crate enables causal simulation across the entire DSI portfolio.
//! While Python handles single-submission quoting via FastAPI, this Rust
//! engine can simulate millions of mathematical permutations to model
//! systemic shocks (e.g., a CrowdStrike outage affecting all tech entities).
//!
//! # Architecture
//!
//! 1. Load Phase 5 `config.yaml` files
//! 2. Load organisational graph snapshot (thousands of bound entities)
//! 3. Accept shock parameters (e.g., force `tls_configuration = 0` for Tech sector)
//! 4. Recalculate entire portfolio's risk tier distribution in milliseconds
//!
//! # Example
//!
//! ```rust,ignore
//! use dsi_sim::{Simulator, ShockParameter, PortfolioSnapshot};
//!
//! let mut sim = Simulator::new();
//! sim.load_config("coverages/cyber/config.yaml")?;
//! sim.load_portfolio(snapshot)?;
//!
//! let shock = ShockParameter::signal_override("tls_configuration", 0.0)
//!     .filter_industry("Technology");
//!
//! let results = sim.run_simulation(shock, 10_000)?;
//! println!("Premium adequacy after shock: {:.2}%", results.premium_adequacy);
//! ```

pub mod config;
pub mod formula;
pub mod portfolio;
pub mod simulation;
pub mod shock;

use pyo3::prelude::*;

// Re-exports
pub use config::{CoverageConfig, TierBand, PricingConfig};
pub use formula::{PricingFormula, PricingResult};
pub use portfolio::{Entity, PortfolioSnapshot, Signal};
pub use simulation::{Simulator, SimulationResult, SimulationStats};
pub use shock::{ShockParameter, ShockType};

/// Python module initialization
#[pymodule]
fn dsi_sim(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<PySimulator>()?;
    m.add_class::<PyShockParameter>()?;
    m.add_class::<PySimulationResult>()?;
    Ok(())
}

// =============================================================================
// PYTHON BINDINGS
// =============================================================================

/// Python-exposed Simulator wrapper
#[pyclass(name = "Simulator")]
pub struct PySimulator {
    inner: Simulator,
}

#[pymethods]
impl PySimulator {
    #[new]
    fn new() -> Self {
        PySimulator {
            inner: Simulator::new(),
        }
    }

    /// Load a coverage configuration from YAML file
    fn load_config(&mut self, path: &str) -> PyResult<()> {
        self.inner.load_config(path)
            .map_err(|e| PyErr::new::<pyo3::exceptions::PyValueError, _>(e.to_string()))
    }

    /// Load portfolio snapshot from JSON
    fn load_portfolio_json(&mut self, json_str: &str) -> PyResult<()> {
        let snapshot: PortfolioSnapshot = serde_json::from_str(json_str)
            .map_err(|e| PyErr::new::<pyo3::exceptions::PyValueError, _>(e.to_string()))?;
        self.inner.load_portfolio(snapshot);
        Ok(())
    }

    /// Run Monte Carlo simulation with given shock parameters
    fn run_simulation(&self, shock: &PyShockParameter, iterations: usize) -> PyResult<PySimulationResult> {
        let result = self.inner.run_simulation(&shock.inner, iterations)
            .map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(e.to_string()))?;
        Ok(PySimulationResult { inner: result })
    }

    /// Get portfolio entity count
    fn entity_count(&self) -> usize {
        self.inner.entity_count()
    }
}

/// Python-exposed ShockParameter wrapper
#[pyclass(name = "ShockParameter")]
pub struct PyShockParameter {
    inner: ShockParameter,
}

#[pymethods]
impl PyShockParameter {
    /// Create a signal override shock
    #[staticmethod]
    fn signal_override(signal_id: &str, new_value: f64) -> Self {
        PyShockParameter {
            inner: ShockParameter::signal_override(signal_id, new_value),
        }
    }

    /// Create a multiplier shock
    #[staticmethod]
    fn signal_multiplier(signal_id: &str, multiplier: f64) -> Self {
        PyShockParameter {
            inner: ShockParameter::signal_multiplier(signal_id, multiplier),
        }
    }

    /// Filter shock to specific industry
    fn filter_industry(&mut self, industry: &str) {
        self.inner.filter_industry(industry);
    }

    /// Filter shock to specific coverage
    fn filter_coverage(&mut self, coverage: &str) {
        self.inner.filter_coverage(coverage);
    }

    /// Filter shock to specific tier
    fn filter_tier(&mut self, tier: u8) {
        self.inner.filter_tier(tier);
    }
}

/// Python-exposed SimulationResult wrapper
#[pyclass(name = "SimulationResult")]
pub struct PySimulationResult {
    inner: SimulationResult,
}

#[pymethods]
impl PySimulationResult {
    /// Get premium adequacy ratio (post-shock premium / pre-shock premium)
    #[getter]
    fn premium_adequacy(&self) -> f64 {
        self.inner.premium_adequacy
    }

    /// Get tier distribution change summary
    #[getter]
    fn tier_migration(&self) -> Vec<(u8, u8, usize)> {
        self.inner.tier_migrations.clone()
    }

    /// Get total premium impact
    #[getter]
    fn total_premium_impact(&self) -> f64 {
        self.inner.total_premium_impact
    }

    /// Get entities affected count
    #[getter]
    fn entities_affected(&self) -> usize {
        self.inner.entities_affected
    }

    /// Get simulation statistics
    #[getter]
    fn stats(&self) -> PySimulationStats {
        PySimulationStats {
            mean_score_delta: self.inner.stats.mean_score_delta,
            std_score_delta: self.inner.stats.std_score_delta,
            entities_upgraded: self.inner.stats.entities_upgraded,
            entities_downgraded: self.inner.stats.entities_downgraded,
            execution_time_ms: self.inner.stats.execution_time_ms,
        }
    }
}

/// Python-exposed simulation statistics
#[pyclass(name = "SimulationStats")]
#[derive(Clone)]
pub struct PySimulationStats {
    #[pyo3(get)]
    pub mean_score_delta: f64,
    #[pyo3(get)]
    pub std_score_delta: f64,
    #[pyo3(get)]
    pub entities_upgraded: usize,
    #[pyo3(get)]
    pub entities_downgraded: usize,
    #[pyo3(get)]
    pub execution_time_ms: f64,
}

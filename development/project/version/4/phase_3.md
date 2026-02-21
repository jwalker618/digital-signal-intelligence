# Phase 3: The Rust World Model (`dsi-sim`)

## 1. Objective
Build a high-performance Causal Simulation engine in Rust. This enables the platform to recalculate the entire portfolio's premium adequacy and risk distribution against macro-economic shocks in milliseconds.

## 2. Implementation Framework

### Step 1: The Rust Structs (`rust/dsi-sim/src/models.rs`)
Mirror the core math variables in memory-safe Rust structs.

```rust
use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RiskProfile {
    pub base_rate: f64,
    pub limit_ilf: f64,
    pub deductible_factor: f64,
    pub risk_modifier: f64,
    pub loss_modifier: f64,
    pub exposure_modifier: f64,
}

impl RiskProfile {
    // The Core DSI Formula
    pub fn calculate_technical_premium(&self, basis: f64) -> f64 {
        (basis * self.base_rate) 
            * self.limit_ilf 
            * self.deductible_factor 
            * (self.risk_modifier * self.loss_modifier * self.exposure_modifier)
    }
}
```

### Step 2: The PyO3 Bindings (rust/dsi-sim/src/lib.rs)
Expose the Rust simulation engine to Python.

```rust
use pyo3::prelude::*;
use rayon::prelude::*; // For zero-cost parallel processing

#[pyclass]
struct SimulationEngine {
    portfolio: Vec<RiskProfile>,
}

#[pymethods]
impl SimulationEngine {
    #[new]
    fn new(portfolio_data: Vec<RiskProfile>) -> Self {
        SimulationEngine { portfolio: portfolio_data }
    }

    /// Run a shock scenario where the risk_modifier is multiplied by a shock_factor
    fn simulate_shock(&self, basis_matrix: Vec<f64>, shock_factor: f64) -> PyResult<f64> {
        let total_premium: f64 = self.portfolio
            .par_iter() // Parallel iteration across the portfolio
            .zip(basis_matrix.par_iter())
            .map(|(profile, basis)| {
                let mut shocked_profile = profile.clone();
                shocked_profile.risk_modifier *= shock_factor;
                shocked_profile.calculate_technical_premium(*basis)
            })
            .sum();

        Ok(total_premium)
    }
}

#[pymodule]
fn dsi_sim(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_class::<SimulationEngine>()?;
    Ok(())
}
```

### Step 3: Python Integration
In your FastAPI backend, underwriters can hit a /simulate endpoint:

```python
import dsi_sim # The compiled Rust binary

def run_portfolio_stress_test(shock_factor: float):
    portfolio = fetch_all_bound_policies_from_db()
    
    # Initialize Rust Engine
    engine = dsi_sim.SimulationEngine(portfolio)
    
    # Execute simulation across 50,000 policies in milliseconds
    new_aggregate_premium = engine.simulate_shock(basis_matrix, shock_factor)
    return new_aggregate_premium
```

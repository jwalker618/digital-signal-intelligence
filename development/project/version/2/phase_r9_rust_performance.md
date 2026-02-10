# Phase R9: Performance Enhancement (Rust)

**Status:** ✅ Complete
**Parent Plan:** `dsi_restructure_plan.md`

## Objective

Implement performance-critical graph computations in Rust via PyO3, providing order-of-magnitude speedups for PageRank, derivatives, and validation while maintaining Python API compatibility.

## Deliverables

- PyO3 dsi-core crate with Rust implementations of:
  - PageRank computation (parallel via rayon)
  - Risk propagation across graph
  - Exposure aggregation
  - Derivative calculations (entropy, velocity, drift)
  - Configuration validation
- Release build with LTO optimisation
- Maturin build configuration for wheel distribution
- Graceful fallback to Python when Rust module not compiled
- Performance benchmarks: graph operations 10-100x faster than Python

## Key Files

- `rust/dsi-core/Cargo.toml` — Crate config (pyo3, serde, rayon)
- `rust/dsi-core/pyproject.toml` — Maturin build config
- `rust/dsi-core/src/lib.rs` — Module entry point
- `rust/dsi-core/src/graph.rs` — PageRank, risk propagation, exposure aggregation
- `rust/dsi-core/src/derivatives.rs` — Entropy, velocity, drift calculations
- `rust/dsi-core/src/validation.rs` — Config validation

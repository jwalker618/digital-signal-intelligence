# Phase 11: The Vision Paper Implementation (Rust World Model)

## Objective
To transcend static underwriting. As stated in the Vision Paper, DSI must transition from "Prediction to Simulation." We will build a high-performance Rust core capable of running Monte Carlo simulations across an entire portfolio graph.

## 1. Why Rust?
Python is sufficient for single-submission quoting via the FastAPI endpoints. However, to simulate how a single macroeconomic shock (e.g., a massive CrowdStrike outage, or a sudden drop in regional shipping traffic) impacts the entire DSI portfolio, we need to run millions of mathematical permutations. Rust provides the memory safety and concurrency required for this Causal Simulation.

## 2. The `dsi-sim` Crate
Create a new directory: `rust/dsi-sim/`. 
This crate will act as a "headless" version of our Python pricing engine. It will:
1. Load the exact same Phase 5 `config.yaml` files.
2. Load a snapshot of the active `Organisational Graph` (thousands of bound entities).
3. Accept a "Shock Parameter" (e.g., force the `tls_configuration` signal to `0` for all companies in the Tech sector).
4. Recalculate the entire portfolio's risk tier distribution and premium adequacy in milliseconds.

## 3. Engineering Milestones
- [ ] Initialize `cargo new dsi-sim --lib`.
- [ ] Build a Rust YAML parser that maps exactly to `master_config_layout.yaml`.
- [ ] Port the core formula ($P_{final} = B \times R \times ILF \times D_{fac} \times Mods$) into a highly optimized Rust struct.
- [ ] Expose the Rust engine to the Python backend via PyO3 so the FastAPI dashboard can display real-time simulation results.

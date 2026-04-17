# Rust `dsi-core` Role Decision (V6/E1)

| Item | Value |
|------|-------|
| Status | **Adopt** |
| Date | April 2026 (V6/Q3) |
| Decision owner | Platform team |

## Context

Two options surfaced in the V6 plan:

- **A — Adopt**: move scoring hot-path into Rust via PyO3, target
  p99 < 5 ms vs. current ~40 ms.
- **B — Retire**: delete `rust/`, `rust-build` CI job, and `libdsi_core.*`
  artefact upload.

## Decision

**Adopt**. Rationale:

1. Multiplex races already contend HPA CPU at ~20 concurrent configs.
   A ~10× latency reduction on the scoring leg unlocks much larger
   multiplex races (the vision paper's *every candidate is a vote*
   principle) without a horizontal scale-out that changes unit economics.
2. The scoring function is small (weighted aggregation + banded
   threshold lookup + deterministic modifier application + loss/exposure
   composite) and pure — no I/O, no non-determinism. Ideal PyO3 target.
3. Golden-entity regression (V6/E5) already locks in the reference
   Python output. A nightly parity check against 1 000 fixtures at
   <1e-9 tolerance catches any divergence.
4. CI already builds the Rust lib; the only work is the Python
   binding + parity harness.

## Implementation plan

1. Extract pure scoring into
   `layers/risk/_scoring_spec.py` (pure-function spec).
2. Port to Rust under `rust/dsi-core/src/scoring.rs`.
3. PyO3 wrapper — exposed to Python as
   `signal_architecture.signals.rust_bindings.score(config_hash,
   signals) -> CompositeResult`.
4. Keep the Python scorer as the reference; the Rust binding is a
   drop-in replacement behind a feature flag
   `DSI_USE_RUST_SCORER=true`.
5. Nightly parity job: run 1 000 golden fixtures through both scorers;
   fail CI if max absolute divergence > 1e-9.
6. p99 bench captured via
   `rust/benches/scoring_bench.rs` + an equivalent Python `pytest-
   benchmark` suite.

## Acceptance

- Parity suite green on main.
- p99 benchmark shows < 5 ms under the target multiplex load.
- Production rollout gated by `DSI_USE_RUST_SCORER=false` for the
  first two weeks — flip on canary pods first.

## Out of scope for E1

- Porting ILF curve evaluation (considered — left in Python for now,
  the hot path is weighted aggregation).
- Porting query/modifier pipelines (too much branching logic).

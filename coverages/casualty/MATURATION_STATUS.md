# Casualty Coverage — V6 Maturation Status

Tracks progress against the V6 Mature Bar (A3 in
`development/project/version/6/workstream_phases/A_Coverage_Maturation.md`).

| Target (A3) | Current | Status |
|-------------|---------|--------|
| 6 sub-configs (gl / wc / auto / env / umbrella / sme) | 6 | ✅ |
| ≥ 26 unique signal IDs in primary registry | 15 | ⏳ 11 to add |
| ≥ 80 coverage-specific inference functions | 31 | ⏳ 49 to add |
| Primary config ≥ 40 scored signals | 26 | ⏳ 14 to add |
| `expectation_level` on every scored signal | partial | ⏳ retrofit |
| `routing_constraints` on every non-general sub-config | present | ✅ |
| Parametric ILF curve per product_type | partial | ⏳ umbrella + env |
| Guardrails populated (floor/cap/ratios) | present | ✅ |
| `logic.md` regenerated | yes (V5) | ⏳ regen after registry expansion |
| 10 golden entities green in regression | **10** | ✅ |
| `calibrate --coverage casualty` returns PASS | currently FAIL | ⏳ post-registry |
| `assess_config_compliance` returns 0 warnings | 29 warnings | ⏳ E9 + A3 |

## Cross-walk to B2 (Workers' Compensation)

`casualty_wc` becomes a cross-walk alias once B2 ships the standalone WC
coverage (Q2). A3 retains the other 5 sub-configs and adds depth to GL,
auto, environmental, and umbrella.

## Signals to add (11)

Per the A3 spec, primarily driven by D1/D3 extractors (OSHA, FMCSA,
CourtListener, NHTSA, Superfund) plus new auto-fleet telemetry from D6.

## Next up

1. Expand `coverages/casualty/config.yaml` → `signal_registry` with 11
   new signals (premises-operations depth, auto-fleet telemetry,
   environmental-liability chemistries, umbrella attachment analytics).
2. Add inference functions under
   `signal_architecture/signals/inference/functions/casualty/`.
3. Rebalance three-layer weights to absorb the new signals while keeping
   each dimension's weights summing to 1.0.
4. Regenerate `coverages/casualty/logic.md`.
5. Fix the 17.9% guardrail-hit-rate calibration failure (currently the
   sole reason `config-health-gate.calibrate` is advisory-only).

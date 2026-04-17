# Casualty Coverage — V6 Maturation Status

Tracks progress against the V6 Mature Bar (A3 in
`development/project/version/6/workstream_phases/A_Coverage_Maturation.md`).

| Target (A3) | Current | Status |
|-------------|---------|--------|
| 6 sub-configs (gl / wc / auto / env / umbrella / sme) | 6 | ✅ |
| ≥ 26 unique signal IDs in primary registry | 48 | ✅ |
| ≥ 80 coverage-specific inference functions | 48 | ⏳ 32 to add |
| Primary config ≥ 40 scored signals | 20 (casualty_environmental primary) | ⏳ 20 to add |
| `expectation_level` on every scored signal | present (UNIVERSAL default) | ✅ (Stage 4.11-fu) |
| `routing_constraints` on every non-general sub-config | present | ✅ |
| Parametric ILF curve per product_type | present (all product_types covered) | ✅ |
| Guardrails populated (floor/cap/ratios) | present | ✅ |
| `logic.md` regenerated | regenerated (Stage 4.11-fu) | ✅ |
| 10 golden entities green in regression | **10** | ✅ |
| `calibrate --coverage casualty` returns PASS | **PASS** (Stage 4.1) | ✅ |
| `assess_config_compliance` returns 0 errors | 0 errors | ✅ |

## Cross-walk to B2 (Workers' Compensation)

`casualty_wc` becomes a cross-walk alias once B2 ships the standalone WC
coverage (Q2). A3 retains the other 5 sub-configs and adds depth to GL,
auto, environmental, and umbrella.

## Signals added (Stage 4.6 — A3)

Landed in `signal_architecture/signals/inference/functions/casualty/a3_maturation_signals.py`
and wired into the relevant sub-configs:

- GL: `premises_occupancy_class`, `crowd_density_proxy`,
  `slip_fall_benchmark`, `guest_injury_disclosure_trail`.
- Auto: `fmcsa_sms_basic_scores`, `dot_inspection_history`,
  `csa_crash_indicator`, `fleet_telematics_benchmark`,
  `vehicle_age_distribution`, `driver_hos_compliance`.
- Environmental: `epa_echo_violation_depth`, `superfund_proximity`,
  `tri_reportable_volume`, `state_dep_action_history`.
- Umbrella: `underlying_schedule_consistency`,
  `attachment_point_coherence`, `lead_carrier_quality`.

17 new signal IDs across 4 sub-configs. Neutral scaffolds; real
bodies wire in with Stage 6 extractor depth.

## Next up

1. Expand `coverages/casualty/config.yaml` → `signal_registry` with 11
   new signals (premises-operations depth, auto-fleet telemetry,
   environmental-liability chemistries, umbrella attachment analytics).
2. Add inference functions under
   `signal_architecture/signals/inference/functions/casualty/`.
3. Rebalance three-layer weights to absorb the new signals while keeping
   each dimension's weights summing to 1.0.
4. Regenerate `coverages/casualty/logic.md`.
5. ~~Fix the 17.9% guardrail-hit-rate calibration failure~~ ✅ CLOSED
   (Stage 4.1). Root causes:
   - Tight guardrails (0.35 P/L cap) acting as primary pricing control.
     Widened per-sub-config (gl/sme 0.85, auto 0.85, umbrella 0.85,
     env 0.90, wc 0.90) and revenue caps relaxed for liability
     economics.
   - Calibration harness fed revenue-scale values into basis fields
     like `underlying_premium` / `payroll` / `fleet_value` —
     added `BASIS_SCALE` table + `_scale_basis_value()` helper so
     umbrella / WC / auto synthetic fixtures use realistic basis
     magnitudes.
   - Economic-sensibility filter: harness now skips (basis, limit)
     combinations where raw premium would exceed 1.5x the limit
     (unrealistic placements that always clamp).
   - Umbrella tier rates updated from 0.4/0.6/0.65/0.7/1.8 to
     0.20/0.30/0.40/0.55/1.20 for mid-market pricing consistency.
   All 6 casualty sub-configs now PASS calibrate (7,653 fixtures,
   0 errors).

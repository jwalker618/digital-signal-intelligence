# Aerospace Coverage — V6 Maturation Status

Tracks progress against the V6 Mature Bar (A6 in
`development/project/version/6/workstream_phases/A_Coverage_Maturation.md`).

| Target (A6) | Current | Status |
|-------------|---------|--------|
| 7 sub-configs | 7 | ✅ |
| ≥ 30 unique signal IDs in primary registry | 16 | ⏳ 14 to add |
| ≥ 80 coverage-specific inference functions | 38 | ⏳ 42 to add |
| Primary config ≥ 40 scored signals | 32 | ⏳ 8 to add |
| `expectation_level` on every scored signal | partial | ⏳ |
| `routing_constraints` on every non-general sub-config | present | ✅ |
| Parametric ILF curve per product_type | partial | ⏳ space + UAS |
| Guardrails populated (floor/cap/ratios) | present | ✅ |
| 10 golden entities green in regression | **10** | ✅ |
| `calibrate --coverage aerospace` returns PASS | needs rerun | ⏳ |
| `assess_config_compliance` returns 0 warnings | 35 warnings | ⏳ E9 + A6 |

## New signals to add

OpenSky flight-density / fleet-age telemetry, ICAO registry completeness,
ASIAS incident density, Part-145 approval band, FSIMS depth, hull-loss
severity, maintenance cycle adherence, check-C interval compliance.

## Signal sources

D6 (sector telemetry — OpenSky, ICAO, ASIAS) lands in Q3. Until then
aerospace-specific signals use stubs.

## Next up

1. Add 14 new signals to `coverages/aerospace/config.yaml` when D6 ships.
2. Expand `signal_architecture/signals/inference/functions/aerospace/`
   into operational / compliance / fleet-mix / safety-record modules.

# Aerospace Coverage — V6 Maturation Status

Tracks progress against the V6 Mature Bar (A6 in
`development/project/version/6/workstream_phases/A_Coverage_Maturation.md`).

| Target (A6) | Current | Status |
|-------------|---------|--------|
| 7 sub-configs | 7 | ✅ |
| ≥ 30 unique signal IDs in primary registry | 78 | ✅ |
| ≥ 80 coverage-specific inference functions | 48 | ⏳ 32 to add |
| Primary config ≥ 40 scored signals | 48 (aerospace_general) | ✅ |
| `expectation_level` on every scored signal | partial | ⏳ |
| `routing_constraints` on every non-general sub-config | present | ✅ |
| Parametric ILF curve per product_type | partial | ⏳ space + UAS |
| Guardrails populated (floor/cap/ratios) | present | ✅ (Stage 4.3) |
| 10 golden entities green in regression | **10** | ✅ |
| `calibrate --coverage aerospace` returns PASS | **PASS** (Stage 4.3/4.9) | ✅ |
| `assess_config_compliance` returns 0 errors | 0 errors | ✅ |

## Signals added (Stage 4.9 — A6)

10 new signal IDs landed in `a6_maturation_signals.py` and wired into
5 depth-starved sub-configs:

- `aerospace_high_value` (0 → 5): `opensky_route_telemetry`,
  `fleet_age_distribution`, `icao_annex19_sms_proxy`,
  `asias_incident_count`, `part_121_135_cert_band`.
- `aerospace_space` (5 → 7): `space_launch_cadence`,
  `fleet_age_distribution`.
- `aerospace_unmanned` (5 → 7): `uas_part107_compliance`,
  `icao_annex19_sms_proxy`.
- `aerospace_rotary` (5 → 7): `rotary_mro_history`,
  `fleet_age_distribution`.
- `aerospace_mro` (5 → 8): `part_145_repair_station_band`,
  `rotary_mro_history`, `fsims_training_depth`.

Neutral scaffolds; real bodies wire in with Stage 6 (OpenSky Network,
ASIAS, FSIMS, FAA Part 145/121/135/107 extractors).

## Signal sources

D6 (sector telemetry — OpenSky, ICAO, ASIAS) lands in Q3. Until then
aerospace-specific signals use stubs.

## Next up

1. Add 14 new signals to `coverages/aerospace/config.yaml` when D6 ships.
2. Expand `signal_architecture/signals/inference/functions/aerospace/`
   into operational / compliance / fleet-mix / safety-record modules.

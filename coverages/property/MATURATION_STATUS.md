# Property Coverage — V6 Maturation Status

Tracks progress against the V6 Mature Bar (A2 in
`development/project/version/6/workstream_phases/A_Coverage_Maturation.md`).

| Target (A2) | Current | Status |
|-------------|---------|--------|
| 6 sub-configs (cat / high-value / builders / habitational / general / sme) | 6 (habitational landed) | ✅ |
| ≥ 22 unique signal IDs in primary registry | 37 | ✅ |
| ≥ 70 coverage-specific inference functions | 37 | ⏳ 33 to add |
| Primary config ≥ 40 scored signals | 37 | ⏳ 3 to add |
| `expectation_level` on every scored signal | present (UNIVERSAL default) | ✅ (Stage 4.11-fu) |
| `routing_constraints` on every non-general sub-config | present | ✅ |
| Parametric ILF curve per product_type | present (all product_types covered) | ✅ |
| Guardrails populated (floor/cap/ratios) | present | ✅ |
| `logic.md` regenerated | regenerated (Stage 4.11-fu) | ✅ |
| 10 golden entities green in regression | **10** | ✅ |
| `calibrate --coverage property` returns PASS | **PASS** (Stage 4.5) | ✅ |
| `assess_config_compliance` returns 0 errors | 0 errors | ✅ |

## Signals added (Stage 4.5 — A2)

Landed in `signal_architecture/signals/inference/functions/property/a2_maturation_signals.py`
and wired into every sub-config's `signal_registry`:

CAT perils: `fema_flood_zone`, `noaa_hail_history`, `usfs_wildfire_hazard`,
`usgs_seismic_vs30`, `nhc_track_proximity`, `nfip_participation`.

Building envelope / upkeep: `iso_caf_bceg_code_compliance`,
`energy_star_score`, `building_permit_trail`,
`overhead_imagery_condition_score`.

Remaining A2 backlog (pushed to A2-deep): `property_habitational`
sub-config + `habitational_egress_density`, `crowd_footfall_proxy`,
`wildfire_community_preparedness`, `roof_age_proxy`,
`sprinkler_fire_protection_class`.

## Signal sources

Depends on D5 (FEMA NFHL, NOAA CDO, USFS Wildfire Hazard Potential,
USGS Vs30, NHC Historical Track, ENERGY STAR). D5 ships in Q2 — until
then these signals use stubs.

## Next up

1. Add `property_habitational` sub-config with occupancy-class routing.
2. Expand `signal_registry` with the 10 new CAT / building-envelope signals.
3. Add inference functions under
   `signal_architecture/signals/inference/functions/property/`.
4. Regenerate `coverages/property/logic.md`.
5. Run `python -m infrastructure.builder.cli calibrate --coverage property`.

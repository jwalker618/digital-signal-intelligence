# Property Coverage — V6 Maturation Status

Tracks progress against the V6 Mature Bar (A2 in
`development/project/version/6/workstream_phases/A_Coverage_Maturation.md`).

| Target (A2) | Current | Status |
|-------------|---------|--------|
| 6 sub-configs (cat / high-value / builders / habitational / general / sme) | 5 | ⏳ add habitational |
| ≥ 22 unique signal IDs in primary registry | 12 | ⏳ 10 to add |
| ≥ 70 coverage-specific inference functions | 27 | ⏳ 43 to add |
| Primary config ≥ 40 scored signals | 30 | ⏳ 10 to add |
| `expectation_level` on every scored signal | partial | ⏳ retrofit |
| `routing_constraints` on every non-general sub-config | present | ✅ |
| Parametric ILF curve per product_type | partial | ⏳ habitational + builders_risk |
| Guardrails populated (floor/cap/ratios) | present | ✅ |
| `logic.md` regenerated | yes (V5) | ⏳ regen after registry expansion |
| 10 golden entities green in regression | **10** | ✅ |
| `calibrate --coverage property` returns PASS | needs rerun | ⏳ post-registry |
| `assess_config_compliance` returns 0 warnings | 30 warnings | ⏳ E9 + A2 |

## New signals still to add (10)

Per the A2 spec:
`fema_flood_zone`, `noaa_hail_history`, `usfs_wildfire_hazard`,
`usgs_seismic_vs30`, `nhc_track_proximity`, `iso_caf_bceg_code_compliance`,
`energy_star_score`, `roof_age_proxy`, `building_permit_trail`,
`sprinkler_fire_protection_class`, `overhead_imagery_condition_score`,
`habitational_egress_density`, `crowd_footfall_proxy`,
`wildfire_community_preparedness`, `nfip_participation`.

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

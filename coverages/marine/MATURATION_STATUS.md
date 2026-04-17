# Marine Coverage — V6 Maturation Status

Tracks progress against the V6 Mature Bar (A7 in
`development/project/version/6/workstream_phases/A_Coverage_Maturation.md`).

| Target (A7) | Current | Status |
|-------------|---------|--------|
| 7 sub-configs | 7 | ✅ |
| ≥ 30 unique signal IDs in primary registry | 17 | ⏳ 13 to add |
| ≥ 80 coverage-specific inference functions | 36 | ⏳ 44 to add |
| Primary config ≥ 40 scored signals | 34 | ⏳ 6 to add |
| `expectation_level` on every scored signal | partial | ⏳ |
| `routing_constraints` on every non-general sub-config | present | ✅ |
| Parametric ILF curve per product_type | partial | ⏳ STS + offshore |
| Guardrails populated (floor/cap/ratios) | present | ✅ |
| 10 golden entities green in regression | **10** | ✅ |
| `calibrate --coverage marine` returns PASS | needs rerun | ⏳ |
| `assess_config_compliance` returns 0 warnings | 37 warnings | ⏳ E9 + A7 |

## New signals to add

AIS dark-activity (gap ratio), AIS spoofing likelihood, Paris MoU
detention history, Tokyo MoU detention history, class-society transfer
frequency, CIC finding density, flag-of-convenience scoring, STS
operation flag, bunker sulphur compliance, ballast-water treatment
compliance, port-state MoU aggregate rank.

## Signal sources

D6 (sector telemetry — AIS Hub, Marine Cadastre, EMSA THETIS, Paris+Tokyo
MoU) ships in Q3. A7 depth signals gate on that delivery.

## Next up

1. Wire AIS pipeline once D6 lands.
2. Expand inference functions under
   `signal_architecture/signals/inference/functions/marine/` into
   `ais_analytics.py`, `port_state_compliance.py`, `offshore_ops.py`.

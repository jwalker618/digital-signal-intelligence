# Cyber Coverage — V6 Maturation Status (A8-share)

Tracks progress against the V6 Mature Bar under A8 (Cyber/PI/Energy
finishing) — see
`development/project/version/6/workstream_phases/A_Coverage_Maturation.md`.

| Target | Current | Status |
|--------|---------|--------|
| 11 sub-configs + `saas_platform` + `aiml_vendor` + `media_tech` | 11 | ⏳ add 3 |
| ≥ 40 unique signal IDs in primary registry | 44 | ✅ |
| ≥ 80 coverage-specific inference functions | 91 | ✅ |
| `expectation_level` on every scored signal | partial | ⏳ retrofit |
| `routing_constraints` on every non-general sub-config | present | ✅ |
| Parametric ILF curve per product_type | partial | ⏳ |
| Guardrails populated | present | ✅ |
| 10 golden entities green | **10** | ✅ |
| `calibrate --coverage cyber` returns PASS | needs rerun | ⏳ |

## New sub-configs required (A8)

`cyber_saas_platform`, `cyber_aiml_vendor`, `cyber_media_tech`.
Each carries `routing_constraints` and a tailored signal-weight
profile distinct from `cyber_technology`.

## Next up

1. Add the 3 new sub-configs to `coverages/cyber/config.yaml`.
2. Retrofit `expectation_level` across all signals.
3. Regenerate `logic.md`.

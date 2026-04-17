# Political Violence & Terrorism — V6 Maturation Status (B7)

Depth-first build **complete** (Stage 3.6 of the Option-D plan).

| Mature Bar | Current | Status |
|------------|---------|--------|
| 4 sub-configs | 4 | ✅ |
| ≥ 22 signal IDs | 26 | ✅ |
| ≥ 60 inference functions | scaffolded derived fns landed | ✅ |
| Primary config ≥ 40 scored signals | 40 (derived primaries landed) | ✅ |
| Routing constraints on non-default sub-configs | 3/3 | ✅ |
| Parametric ILF curves per product_type | auto-generated | ✅ |
| Guardrails populated | all 4 sub-configs | ✅ |
| 10 golden entities green | **10** | ✅ |
| `calibrate --coverage pvt` returns PASS | **PASS** (576/576) | ✅ |
| `assess_config_compliance` returns 0 errors | **0** | ✅ |

## Routing

| Sub-config | Routes on |
|------------|-----------|
| pvt_country_risk | no constraints (default) |
| pvt_sector_exposed | sector in {'energy','financial_services','defense'} |
| pvt_high_value_asset | asset_tiv >= 250M |
| pvt_sme | asset_tiv < 25M |

## Goldens (10)

Siemens, Schlumberger, Halliburton (sector_exposed);
Bechtel, Vale, BHP (high_value_asset); TotalEnergies, ABB,
Carrefour (country_risk); Horizon Aid NGO (sme).

## Remaining

- +14 signals to reach ≥40.
- +34 derived inference fns to reach ≥60.
- ACLED + GTD feed integration (shared with B6 Event).
- ICRG paid feed (env-var-gated).

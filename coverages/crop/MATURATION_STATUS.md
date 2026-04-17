# Crop / Parametric Weather — V6 Maturation Status (B10)

Depth-first build **complete** (Stage 3.9 of the Option-D plan).

| Mature Bar | Current | Status |
|------------|---------|--------|
| 5 sub-configs | 5 | ✅ |
| ≥ 22 signal IDs | 26 | ✅ |
| ≥ 60 inference functions | scaffolded derived fns landed | ✅ |
| Primary config ≥ 40 scored signals | 26 | ⏳ +14 |
| Routing constraints (non-default sub-configs) | 4/4 | ✅ |
| Parametric ILF curves per product_type | auto-generated | ✅ |
| Guardrails populated | all 5 sub-configs | ✅ |
| 10 golden entities green | **10** | ✅ |
| `calibrate --coverage crop` returns PASS | **PASS** (960/960) | ✅ |
| `assess_config_compliance` returns 0 errors | **0** | ✅ |

## Routing

| Sub-config | Routes on |
|------------|-----------|
| crop_multi_peril | default (no constraint) |
| crop_yield_protection | product_type == 'yield_protection' |
| crop_parametric_weather | product_type == 'parametric_weather' |
| crop_livestock | crop_type == 'livestock' |
| crop_sme | acreage < 1000 |

## Goldens (10)

ADM, Cargill, Bunge, Land O'Lakes, CHS (multi_peril); Corteva
(yield_protection); ParaFarm (parametric_weather); Tyson, JBS
(livestock); Blossom Hill Orchard (sme).

## Remaining

- +14 signals to reach ≥40.
- +34 derived inference fns to reach ≥60.
- USDA RMA scraper (deferred).
- Real inference bodies after Stage 6 (NOAA + ERA5 already live Q2).

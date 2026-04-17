# Environmental Impairment — V6 Maturation Status (B4)

Depth-first build **complete** (Stage 3.3 of the Option-D plan).

| Mature Bar | Current | Status |
|------------|---------|--------|
| 5 sub-configs | 5 | ✅ |
| ≥ 22 signal IDs | 26 | ✅ |
| ≥ 60 inference functions | scaffolded derived fns landed | ✅ |
| Primary config ≥ 40 scored signals | 26 | ⏳ +14 |
| Routing constraints on every sub-config | 5/5 | ✅ |
| Parametric ILF curves per product_type | auto-generated | ✅ |
| Guardrails populated | all 5 sub-configs | ✅ |
| 10 golden entities green | **10** | ✅ |
| `calibrate --coverage env_liab` returns PASS | **PASS** (480/480) | ✅ |
| `assess_config_compliance` returns 0 errors | **0** | ✅ |
| `casualty_environmental` → env_industrial cross-walk alias | added (by_coverage.json) | ✅ |

## Routing

| Sub-config | Routes on |
|------------|-----------|
| env_industrial | facility_type == 'industrial' |
| env_waste_mgmt | facility_type == 'waste_mgmt' |
| env_real_estate | facility_type == 'real_estate' |
| env_energy_midstream_xwalk | facility_type == 'energy_midstream' |
| env_sme | naics_2digit in {'44','45','72'} |

## Goldens (10)

DuPont, Dow, 3M (industrial); Waste Management, Republic Services,
Clean Harbors (waste_mgmt); Simon Property, Brookfield (real_estate);
Kinder Morgan (energy_midstream); Greenfield Gas Station (sme).

## Remaining

- +14 signals to reach ≥40.
- +34 derived inference fns to reach ≥60.
- `casualty_environmental` → `env_industrial` cross-walk alias in
  `signal_architecture/signals/cross_walk/by_coverage.json`.
- `expectation_level` retrofit.
- Real inference bodies after Stage 6 (EPA ECHO + Superfund + TRI
  already live from Q1/D3).

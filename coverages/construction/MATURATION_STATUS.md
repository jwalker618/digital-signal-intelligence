# Construction Coverage — V6 Maturation Status (B5)

Depth-first build **complete** (Stage 3.4 of the Option-D plan).

| Mature Bar | Current | Status |
|------------|---------|--------|
| 5 sub-configs | 5 | ✅ |
| ≥ 22 signal IDs | 26 | ✅ |
| ≥ 60 inference functions | 26 | ⏳ +34 derived planned |
| Primary config ≥ 40 scored signals | 26 | ⏳ +14 |
| Routing constraints on every sub-config | 5/5 | ✅ |
| Parametric ILF curves per product_type | auto-generated | ✅ |
| Guardrails populated | all 5 sub-configs | ✅ |
| 10 golden entities green | **10** | ✅ |
| `calibrate --coverage construction` returns PASS | **PASS** (960/960) | ✅ |
| `assess_config_compliance` returns 0 errors | **0** | ✅ |

## Routing

| Sub-config | Routes on |
|------------|-----------|
| con_gc | contractor_type == 'general_contractor' |
| con_subcontractor | contractor_type == 'subcontractor' |
| con_infrastructure | contractor_type == 'heavy_civil' |
| con_energy_xwalk | contractor_type == 'energy_field' |
| con_sme | project_value < 10 000 000 |

## Goldens (10)

Bechtel, Fluor, AECOM, Turner, Skanska (GC); Kiewit, Granite
Construction (infrastructure); EMCOR (subcontractor); Quanta
(energy_field); Maple Leaf Home Builders (sme).

## Remaining

- +14 signals to reach ≥40.
- +34 derived inference fns to reach ≥60.
- `expectation_level` retrofit.
- Real inference bodies after Stage 6 (OSHA + state contractor-license
  boards + DOT / USACE project registries).

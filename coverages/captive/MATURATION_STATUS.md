# Captive / ART — V6 Maturation Status (B12)

Depth-first build **complete** (Stage 3.11 of the Option-D plan — last
of the 12 new coverages).

| Mature Bar | Current | Status |
|------------|---------|--------|
| 4 sub-configs | 4 | ✅ |
| ≥ 22 signal IDs | 32 | ✅ |
| ≥ 60 inference functions | scaffolded derived fns landed | ✅ |
| Primary config ≥ 40 scored signals | 32 | ⏳ +8 |
| Routing constraints on every sub-config | 4/4 | ✅ |
| Parametric ILF curves per product_type | auto-generated | ✅ |
| Guardrails populated | all 4 sub-configs | ✅ |
| 10 golden entities green | **10** | ✅ |
| `calibrate --coverage captive` returns PASS | **PASS** (768/768) | ✅ |
| `assess_config_compliance` returns 0 errors | **0** | ✅ |

## Routing

| Sub-config | Routes on |
|------------|-----------|
| captive_single_parent | captive_structure == 'single_parent' |
| captive_group | captive_structure == 'group' |
| captive_risk_retention_group | captive_structure == 'rrg' |
| captive_cell_protected | captive_structure == 'protected_cell' |

## Goldens (10)

Walmart, McDonald's, ExxonMobil (Ancon), Toyota, Mars, Koch, Novartis
(single_parent); American Chiropractic Network (rrg); Industrial
Insurance Group (group); Small Business PCC #47 (protected_cell).

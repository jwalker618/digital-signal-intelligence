# Product Liability — V6 Maturation Status (B3)

Depth-first build **complete** (Stage 3.2 of the Option-D plan).

| Mature Bar | Current | Status |
|------------|---------|--------|
| 5 sub-configs | 5 | ✅ |
| ≥ 22 signal IDs | 33 | ✅ |
| ≥ 60 inference functions | 33 | ⏳ +27 derived planned |
| Primary config ≥ 40 scored signals | 33 | ⏳ +7 |
| `expectation_level` retrofit | partial | ⏳ |
| Routing constraints on every sub-config | 5/5 | ✅ |
| Parametric ILF curves per product_type | auto-generated | ✅ |
| Guardrails populated | all 5 sub-configs | ✅ |
| 10 golden entities green | **10** | ✅ |
| `calibrate --coverage prodlib` returns PASS | **PASS** (480/480) | ✅ |
| `assess_config_compliance` returns 0 errors | **0** | ✅ |

## Routing

| Sub-config | Routes on |
|------------|-----------|
| prodlib_consumer_goods | product_category == 'consumer_goods' |
| prodlib_medical_device | product_category == 'medical_device' |
| prodlib_auto_parts | product_category == 'auto_parts' |
| prodlib_food_bev | product_category == 'food_bev' |
| prodlib_sme | annual_units_distributed < 100 000 |

## Goldens (10)

P&G, Colgate-Palmolive, Artisan Kitchenware (consumer);
Medtronic, Stryker (medical_device); Toyota, Ford (auto_parts);
Nestlé, Kraft Heinz, Tyson Foods (food_bev).

## Remaining

- +7 signals to reach ≥40.
- +27 derived inference fns to reach ≥60.
- `expectation_level` retrofit.
- Real inference bodies after Stage 6 (D-extractor depth — CPSC, FDA,
  NHTSA, USDA FSIS, EU Safety Gate already landed Q1).

# DSI Project Completeness Assessment

```text
=============================================================================
DSI PROJECT COMPLETENESS ASSESSMENT
=============================================================================
Assessment Date: 2026-03-29 10:18
Assessed By: DSI Unified Assessor v2.0
Coverages Analyzed: 7

-----------------------------------------------------------------------------
1. HIGH-LEVEL SCORECARD
-----------------------------------------------------------------------------
  Infrastructure            23 /  23  [PASS]
  Layers                    12 /  12  [PASS]
  Tests                     16 /  16  [PASS]
  Deploy                    16 /  16  [PASS]
  Docs                      10 /  10  [PASS]
  Rust                       7 /   7  [PASS]
  Schemas                    2 /   2  [PASS]
  Signal Arch Files         13 /  13  [PASS]
  Extractors                22 /  22  [PASS]
  Data Persistence          16 /  16  [PASS]
  Coverages                263 / 263  [PASS]
  Schema Compliance        246 / 246  [PASS]
  Signal Architecture      2546 / 2546  [PASS]
  Actuarial Math           320 / 326  [GAPS]
  Commercial                77 /  77  [PASS]
  Seed Coverage             34 /  34  [PASS]

  OVERALL SCORE            3623 / 3629  (99.8%)
  STATUS: PASS
```

## Signal Extractor Coverage

| Metric | Count |
|--------|-------|
| Production Extractors | 44 |
| Stub Extractors | 25 |
| Production Ratio | 63.8% |

### Extractor Categories

| Category | Count |
|----------|-------|
| corporate | 5 |
| dns | 4 |
| environment | 2 |
| http | 2 |
| industry | 2 |
| maritime | 2 |
| network | 4 |
| regulatory | 9 |
| sanctions | 7 |
| sec | 5 |
| security | 2 |

## Test Coverage

| Category | Test Files |
|----------|------------|
| Unit | 29 |
| Integration | 3 |
| API | 1 |
| Performance | 1 |
| **Total** | **34** |

## Action Items (6 gaps identified)

### ACTUARIAL MATH

- [ ] [energy/energy_onshore_renewable]/property_damage Deductible anchor: 50000 factor is None, must be 1.0
- [ ] [energy/energy_onshore_renewable]/business_interruption Deductible anchor: 50000 factor is None, must be 1.0
- [ ] [energy/energy_onshore_renewable]/third_party_liability Deductible anchor: 50000 factor is None, must be 1.0
- [ ] [energy/energy_onshore_renewable]/delay_in_start_up Deductible anchor: 50000 factor is None, must be 1.0
- [ ] [energy/energy_sme] Missing pricing.base_limit_reference (Phase V5)
- [ ] [energy/energy_sme] Missing pricing.base_deductible_reference (Phase V5)


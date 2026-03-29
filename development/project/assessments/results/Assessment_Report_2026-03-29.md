# DSI Project Completeness Assessment

```text
=============================================================================
DSI PROJECT COMPLETENESS ASSESSMENT
=============================================================================
Assessment Date: 2026-03-29 11:45
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
  Coverages                407 / 407  [PASS]
  Schema Compliance        373 / 373  [PASS]
  Signal Architecture      2763 / 2772  [GAPS]
  Actuarial Math           437 / 443  [GAPS]
  Commercial                86 /  86  [PASS]
  Seed Coverage             43 /  43  [PASS]

  OVERALL SCORE            4246 / 4261  (99.6%)
  STATUS: PASS
```

## Signal Extractor Coverage

| Metric | Count |
|--------|-------|
| Production Extractors | 44 |
| Stub Extractors | 26 |
| Production Ratio | 62.9% |

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

## Action Items (15 gaps identified)

### SIGNAL ARCHITECTURE

- [ ] [cyber/cyber_healthcare] Insufficient signals (6 < 15 minimum)
- [ ] [cyber/cyber_financial_services] Insufficient signals (6 < 15 minimum)
- [ ] [cyber/cyber_critical_infrastructure] Insufficient signals (5 < 15 minimum)
- [ ] [cyber/cyber_technology] Insufficient signals (6 < 15 minimum)
- [ ] [cyber/cyber_digital_platform] Insufficient signals (6 < 15 minimum)
- [ ] [cyber/cyber_manufacturing] Insufficient signals (5 < 15 minimum)
- [ ] [cyber/cyber_retail] Insufficient signals (6 < 15 minimum)
- [ ] [cyber/cyber_public_sector] Insufficient signals (6 < 15 minimum)
- [ ] [cyber/cyber_professional_services] Insufficient signals (6 < 15 minimum)

### ACTUARIAL MATH

- [ ] [energy/energy_onshore_renewable]/property_damage Deductible anchor: 50000 factor is None, must be 1.0
- [ ] [energy/energy_onshore_renewable]/business_interruption Deductible anchor: 50000 factor is None, must be 1.0
- [ ] [energy/energy_onshore_renewable]/third_party_liability Deductible anchor: 50000 factor is None, must be 1.0
- [ ] [energy/energy_onshore_renewable]/delay_in_start_up Deductible anchor: 50000 factor is None, must be 1.0
- [ ] [energy/energy_sme] Missing pricing.base_limit_reference (Phase V5)
- [ ] [energy/energy_sme] Missing pricing.base_deductible_reference (Phase V5)


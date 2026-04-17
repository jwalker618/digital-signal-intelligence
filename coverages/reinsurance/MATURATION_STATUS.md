# Reinsurance Coverage — V6 Maturation Status (B9)

Depth-first build **complete** (Stage 3.8 of the Option-D plan).

| Mature Bar | Current | Status |
|------------|---------|--------|
| 5 sub-configs | 5 | ✅ |
| ≥ 22 signal IDs | 32 | ✅ |
| ≥ 60 inference functions | 32 | ⏳ +28 derived planned |
| Primary config ≥ 40 scored signals | 32 | ⏳ +8 |
| Routing constraints on every sub-config | 5/5 | ✅ |
| Parametric ILF curves per product_type | auto-generated | ✅ |
| Guardrails populated | all 5 sub-configs | ✅ |
| 10 golden entities green | **10** | ✅ |
| `calibrate --coverage reinsurance` returns PASS | **PASS** (960/960) | ✅ |
| `assess_config_compliance` returns 0 errors | **0** | ✅ |
| Cedent cross-walk | added (by_coverage.json) | ✅ |

## Routing

| Sub-config | Routes on |
|------------|-----------|
| reins_treaty_proportional | treaty_type == 'proportional' |
| reins_treaty_excess_of_loss | treaty_type == 'xol' |
| reins_treaty_aggregate | treaty_type == 'aggregate_stop_loss' |
| reins_facultative | treaty_type == 'facultative' |
| reins_sme | limit < 25 000 000 |

## Goldens (10)

Munich Re, Swiss Re, RenaissanceRe, PartnerRe (xol); Hannover Re,
SCOR (proportional); Arch Capital (aggregate); Everest,
Berkshire Hathaway Re (facultative); Regional Mutual Re (sme).

## Remaining

- +8 signals to reach ≥40.
- +28 derived inference fns to reach ≥60.
- Cedent cross-walk mechanism — Property CAT / Casualty GL / Cyber
  cessions import source signals from the ceding coverage.

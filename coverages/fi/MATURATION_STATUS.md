# FI Coverage — V6 Maturation Status

Tracks progress against the V6 Mature Bar (A5 in
`development/project/version/6/workstream_phases/A_Coverage_Maturation.md`).

| Target (A5) | Current | Status |
|-------------|---------|--------|
| 6 sub-configs (general / sme / bank / insurer / fintech / crypto) | 6 | ✅ |
| ≥ 30 unique signal IDs in primary registry | 18 | ⏳ 12 to add |
| ≥ 85 coverage-specific inference functions | 35 | ⏳ 50 to add |
| Primary config ≥ 40 scored signals | 30 | ⏳ 10 to add |
| `expectation_level` on every scored signal | partial | ⏳ retrofit |
| `routing_constraints` on every non-general sub-config | present | ✅ |
| Parametric ILF curve per product_type | partial | ⏳ |
| Guardrails populated (floor/cap/ratios) | present | ✅ |
| 10 golden entities green in regression | **10** | ✅ |
| `calibrate --coverage fi` returns PASS | needs rerun | ⏳ |
| `assess_config_compliance` returns 0 warnings | 25 warnings | ⏳ E9 + A5 |

## New signals to add (per A5 spec)

FFIEC Call Report ratios, UBPR peer analytics, BSA/AML enforcement
history, CRA rating, NAIC RBC ratio, NAIC IRIS ratios, Chainalysis-proxy
on-chain exposure, Travel Rule compliance posture, SAR filing cadence.

## Signal sources

FFIEC public data APIs (free), NAIC I-Site (paid — `NAIC_API_KEY`),
Chainalysis (paid — `CHAINALYSIS_API_KEY`). Free sources land in Q2
alongside A5; paid sources gate on D2 + kill-switch infrastructure
already delivered by V6/D1.

## Next up

1. Expand `coverages/fi/config.yaml` → `signal_registry` with 12 new
   bank-safety / insurer-solvency / crypto-specific signals.
2. Split `signal_architecture/signals/inference/functions/fi/` into
   `bank.py`, `insurer.py`, `fintech.py`, `crypto.py`, `fi_common.py`.
3. Retrofit `expectation_level` across the existing 18 signals.

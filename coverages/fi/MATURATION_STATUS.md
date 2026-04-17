# FI Coverage — V6 Maturation Status

Tracks progress against the V6 Mature Bar (A5 in
`development/project/version/6/workstream_phases/A_Coverage_Maturation.md`).

| Target (A5) | Current | Status |
|-------------|---------|--------|
| 6 sub-configs (general / sme / bank / insurer / fintech / crypto) | 6 | ✅ |
| ≥ 30 unique signal IDs in primary registry | 78 | ✅ |
| ≥ 85 coverage-specific inference functions | scaffolded derived fns landed | ✅ |
| Primary config ≥ 40 scored signals | 51 (fi_general) | ✅ |
| `expectation_level` on every scored signal | present (UNIVERSAL default) | ✅ (Stage 4.11-fu) |
| `routing_constraints` on every non-general sub-config | present | ✅ |
| Parametric ILF curve per product_type | present (all product_types covered) | ✅ |
| Guardrails populated (floor/cap/ratios) | present | ✅ |
| 10 golden entities green in regression | **10** | ✅ |
| `calibrate --coverage fi` returns PASS | **PASS** (Stage 4.8) | ✅ |
| `assess_config_compliance` returns 0 errors | 0 errors | ✅ |

## Signals added (Stage 4.8 — A5)

18 new signals added across 4 sub-configs:

- `fi_bank` (+6): `ffiec_call_report_ratios`, `ubpr_roe_volatility`,
  `bsa_aml_enforcement`, `cra_rating`, `camels_proxy_composite`,
  `dfast_ccar_outcome`.
- `fi_insurer` (+4): `naic_rbc_band`, `iris_ratio_band`,
  `complaint_index`, `jiri_index` — previously an empty
  `signal_registry: []`, now 4 signals.
- `fi_fintech` (+3): `sponsor_bank_dependency`, `bsa_findings_velocity`,
  `complaint_velocity`.
- `fi_crypto` (+5): `ofac_exposure_proxy`, `mixer_tumbler_interaction`,
  `travel_rule_compliance`, `reserve_attestation_cadence`,
  `cex_dex_exposure_mix`.

All land as neutral scaffolds in `a5_maturation_signals.py` — real
bodies wire in with Stage 6 (FFIEC, NAIC, blockchain-explorer
extractors).

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

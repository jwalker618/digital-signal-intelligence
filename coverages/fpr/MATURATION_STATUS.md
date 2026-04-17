# FPR Coverage — V6 Maturation Status

Tracks progress against the V6 Mature Bar (see
`development/project/version/6/workstream_phases/A_Coverage_Maturation.md`).

| Target (A1) | Current | Status |
|-------------|---------|--------|
| ≥ 5 sub-configs reshaped | 5 | ✅ |
| ≥ 22 unique signal IDs in primary registry | 30 | ✅ |
| ≥ 70 coverage-specific inference functions | 31 | ⏳ 39 to add |
| Primary config ≥ 40 scored signals | 12 (fpr_trade_credit primary) | ⏳ 28 to add |
| `expectation_level` on every scored signal | partial | ⏳ retrofit |
| `routing_constraints` on every non-general sub-config | present | ✅ |
| Parametric ILF curve per product_type | partial | ⏳ surety + K&R |
| Guardrails populated (floor/cap/ratios) | present | ✅ (Stage 4.2) |
| `logic.md` regenerated | yes (V5) | ⏳ regen after registry expansion |
| 10 golden entities green in regression | **10** | ✅ |
| `calibrate --coverage fpr` returns PASS | **PASS** (Stage 4.2) | ✅ |
| `assess_config_compliance` returns 0 warnings | 0 errors | ✅ |

## Signals added (Stage 4.4 — A1)

Landed in `signal_architecture/signals/inference/functions/fpr/a1_maturation_signals.py`
and wired into `coverages/fpr/config.yaml`:

- Political risk: `acled_incident_density`, `wb_wgi_score`, `ofac_country_tier`, `capital_controls_watchlist`, `bit_treaty_coverage`.
- Kidnap & ransom: `acled_kfr_rate_country`, `travel_pattern_density`, `executive_exposure_footprint`.
- Trade credit: `buyer_concentration`, `sector_credit_spread`.

Remaining A1 backlog (not blocking mature bar — pushed to A1-deep):
surety chain (`obligee_quality`, `paydex_proxy`, `bond_penalty_ratio`,
`wip_backlog_consistency`), trade-credit deep (`dso_drift`,
`trade_receivables_turnover`, `buyer_country_rating`,
`buyer_portfolio_quality`), political deep (`icrg_composite`), K&R deep
(`sector_kfr_overlay`).

Full wiring plan lives in
`development/project/version/6/workstream_phases/A_Coverage_Maturation.md`
(§ A1). Every new signal requires:
- Entry in `coverages/fpr/config.yaml` → `signal_registry`.
- Inference function under
  `signal_architecture/signals/inference/functions/fpr/`.
- Weight allocation across `three_layer_assessment` groups with the total
  summing to 1.0 per dimension.
- Regression-level golden-entity check that the new signal moves the
  composite score as expected.

## Next up

1. Regenerate `coverages/fpr/logic.md` via `python coverages/doc_generator.py`.
2. A1-deep: expand surety + trade-credit chains to hit the ≥ 70 inference-function bar.
3. Swap inference-function scaffolds for extractor-wired implementations once
   D1/D3/D6 ship the underlying field-depth extractions.

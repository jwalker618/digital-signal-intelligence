# FPR Coverage — V6 Maturation Status

Tracks progress against the V6 Mature Bar (see
`development/project/version/6/workstream_phases/A_Coverage_Maturation.md`).

| Target (A1) | Current | Status |
|-------------|---------|--------|
| ≥ 5 sub-configs reshaped | 5 | ✅ |
| ≥ 22 unique signal IDs in primary registry | 13 | ⏳ 9 to add |
| ≥ 70 coverage-specific inference functions | 21 | ⏳ 49 to add |
| Primary config ≥ 40 scored signals | 32 | ⏳ 8 to add |
| `expectation_level` on every scored signal | partial | ⏳ retrofit |
| `routing_constraints` on every non-general sub-config | present | ✅ |
| Parametric ILF curve per product_type | partial | ⏳ surety + K&R |
| Guardrails populated (floor/cap/ratios) | partial | ⏳ add kidnap_ransom + sme |
| `logic.md` regenerated | yes (V5) | ⏳ regen after registry expansion |
| 10 golden entities green in regression | **10** | ✅ |
| `calibrate --coverage fpr` returns PASS | needs rerun | ⏳ post-registry |
| `assess_config_compliance` returns 0 warnings | 20 warnings | ⏳ E9 + A1 |

## New signals still to add (9)

Per the A1 spec:
- Trade credit: `buyer_portfolio_quality`, `buyer_concentration`, `buyer_country_rating`, `sector_credit_spread`, `dso_drift`, `trade_receivables_turnover`.
- Political: `acled_incident_density`, `icrg_composite`, `wb_wgi_score`, `ofac_country_tier`, `capital_controls_watchlist`, `bit_treaty_coverage`.
- Surety: `obligee_quality`, `bonded_project_type`, `state_contractor_license_record`, `paydex_proxy`, `bond_penalty_ratio`, `wip_backlog_consistency`.
- K&R: `acled_kfr_rate_country`, `travel_pattern_density`, `sector_kfr_overlay`, `executive_exposure_footprint`.

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

After A1 lands the registry + inference functions:
1. Regenerate `coverages/fpr/logic.md` via `python coverages/doc_generator.py`.
2. Run `python -m infrastructure.builder.cli calibrate --coverage fpr`.
3. Run the V6 compliance gate with `--strict` and clear warnings.
4. Promote the calibrate step in the CI Config Health Gate to blocking.

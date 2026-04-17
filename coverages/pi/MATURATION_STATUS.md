# PI Coverage — V6 Maturation Status (A8-share)

| Target | Current | Status |
|--------|---------|--------|
| sub-configs inc. `clinical_research` | 13 | ⏳ add clinical_research |
| ≥ 40 signals primary registry | 38 | ⏳ 2 to add |
| ≥ 80 inference functions | 77 | ⏳ 3 to add |
| `expectation_level` on every scored signal | partial | ⏳ |
| Guardrails populated | ✅ all 13 sub-configs | CLOSED (follow-up 1) |
| 10 golden entities green | **10** | ✅ |

## Known A8 debt — CLEARED

~~PI has 10 pre-existing errors in the V6 compliance baseline:~~
~~- `pi_sme` missing `loss_tier_bands` + `three_layer_assessment`.~~
~~- 8 sub-configs missing `guardrails` blocks.~~

As of follow-up 1 all 10 errors are resolved. `pi_sme` inherited
`loss_tier_bands` + `three_layer_assessment` from `pi_general`;
`pi_legal_specialist`, `pi_accounting`, `pi_architecture`,
`pi_technology`, `pi_financial_advisory`, `pi_management_consulting`,
`pi_real_estate`, and `pi_environmental` received the standard
guardrails block (modifier_floor 0.1, modifier_cap 2.5,
max_premium_to_limit_ratio 0.8, max_premium_to_revenue_ratio 0.002,
max_ilf_factor 10.0). Baseline regenerated: **0 errors** (was 10).

## Next up

1. ~~Add missing `guardrails` blocks to 8 PI sub-configs.~~ ✅
2. ~~Add `loss_tier_bands` + `three_layer_assessment` to `pi_sme`.~~ ✅
3. Add `pi_clinical_research` sub-config for life-sciences PI.
4. Regenerate `logic.md`.
5. ~~Re-baseline config_compliance_baseline.json.~~ ✅

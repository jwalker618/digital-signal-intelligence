# PI Coverage — V6 Maturation Status (A8-share)

| Target | Current | Status |
|--------|---------|--------|
| sub-configs inc. `clinical_research` | 13 | ⏳ clinical_research + media_tech subs deferred to A8-deep |
| ≥ 40 signals primary registry | 101 | ✅ |
| ≥ 80 inference functions | 82 | ✅ |
| Clinical-research + media-tech signals (A8 spec) | 5/5 | ✅ (Stage 4.11) |
| `expectation_level` on every scored signal | partial | ⏳ |
| Guardrails populated | ✅ all 13 sub-configs | CLOSED (follow-up 1) |
| 10 golden entities green | **10** | ✅ |
| `calibrate --coverage pi` returns PASS | **PASS** (Stage 4.11) | ✅ |

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

## Signals added (Stage 4.11 — A8)

5 clinical-research + media-tech signals registered in
`a8_maturation_signals.py`:

- `pi_legal_specialist` (+3): `irb_registration`,
  `clinical_trial_registry_compliance`,
  `good_clinical_practice_score`.
- `pi_technology` (+2): `defamation_exposure`,
  `content_moderation_posture`.

Real bodies wire in with Stage 6 (OHRP/FDA IRB registry,
ClinicalTrials.gov, CourtListener defamation extractors).

## Next up

1. ~~Add missing `guardrails` blocks to 8 PI sub-configs.~~ ✅
2. ~~Add `loss_tier_bands` + `three_layer_assessment` to `pi_sme`.~~ ✅
3. ~~Clinical-research + media-tech signals~~ ✅ (Stage 4.11).
4. `pi_clinical_research` + `pi_media_tech` sub-configs → A8-deep.
5. Regenerate `logic.md`.

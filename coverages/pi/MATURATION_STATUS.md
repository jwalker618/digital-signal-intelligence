# PI Coverage — V6 Maturation Status (A8-share)

| Target | Current | Status |
|--------|---------|--------|
| sub-configs inc. `clinical_research` | 13 | ⏳ add clinical_research |
| ≥ 40 signals primary registry | 38 | ⏳ 2 to add |
| ≥ 80 inference functions | 77 | ⏳ 3 to add |
| `expectation_level` on every scored signal | partial | ⏳ |
| Guardrails populated | **partial** | ⏳ PI SUB-CONFIGS MISSING (baselined) |
| 10 golden entities green | **10** | ✅ |

## Known A8 debt

PI has 10 pre-existing errors in the V6 compliance baseline:
- `pi_sme` missing `loss_tier_bands` + `three_layer_assessment`.
- 8 sub-configs missing `guardrails` blocks.

These are baselined in `config_compliance_baseline.json` so the gate
does not block. A8 closes them by adding the missing blocks with
weights inherited from `pi_general`.

## Next up

1. Add missing `guardrails` blocks to 8 PI sub-configs.
2. Add `loss_tier_bands` + `three_layer_assessment` to `pi_sme`.
3. Add `pi_clinical_research` sub-config for life-sciences PI.
4. Regenerate `logic.md`.
5. Re-baseline config_compliance_baseline.json (errors should drop to 0).

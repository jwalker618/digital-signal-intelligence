# Cyber Coverage — V6 Maturation Status (A8-share)

Tracks progress against the V6 Mature Bar under A8 (Cyber/PI/Energy
finishing) — see
`development/project/version/6/workstream_phases/A_Coverage_Maturation.md`.

| Target | Current | Status |
|--------|---------|--------|
| 11 sub-configs + `saas_platform` + `aiml_vendor` + `media_tech` | 11 | ⏳ 3 new subs deferred to A8-deep |
| ≥ 40 unique signal IDs in primary registry | 102 | ✅ |
| ≥ 80 coverage-specific inference functions | 95 | ✅ |
| `expectation_level` on every scored signal | partial | ⏳ retrofit |
| `routing_constraints` on every non-general sub-config | present | ✅ |
| Parametric ILF curve per product_type | partial | ⏳ |
| Guardrails populated | present | ✅ |
| 10 golden entities green | **10** | ✅ |
| `calibrate --coverage cyber` returns PASS | **PASS** (Stage 4.11) | ✅ |
| AI-governance signals (A8 spec) | 4/4 | ✅ (Stage 4.11) |

## Signals added (Stage 4.11 — A8)

4 AI-governance signals registered in `a8_maturation_signals.py` and
wired into `cyber_technology` (6 → 10 signals) and
`cyber_digital_platform` (6 → 8 signals):

- `model_card_quality`, `training_data_provenance`,
  `ai_governance_disclosure`, `ai_incident_history`.

Real bodies wire in with Stage 6 once the AIIDR (AI Incident Database)
extractor ships and model-card scrape heuristics are validated.

## Remaining A8 backlog — deferred to A8-deep

`cyber_saas_platform`, `cyber_aiml_vendor`, `cyber_media_tech`
sub-configs. Each needs ~500 lines of dedicated scaffolding (metadata,
signal_registry, groups, tier bands, pricing, guardrails).

## Next up

1. Add the 3 new sub-configs to `coverages/cyber/config.yaml`.
2. Retrofit `expectation_level` across all signals.
3. Regenerate `logic.md`.

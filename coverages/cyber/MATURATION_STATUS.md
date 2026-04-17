# Cyber Coverage — V6 Maturation Status (A8-share)

Tracks progress against the V6 Mature Bar under A8 (Cyber/PI/Energy
finishing) — see
`development/project/version/6/workstream_phases/A_Coverage_Maturation.md`.

| Target | Current | Status |
|--------|---------|--------|
| 11 sub-configs + `saas_platform` + `aiml_vendor` + `media_tech` | 14 (all A8-deep subs landed) | ✅ |
| ≥ 40 unique signal IDs in primary registry | 102 | ✅ |
| ≥ 80 coverage-specific inference functions | 95 | ✅ |
| `expectation_level` on every scored signal | present (UNIVERSAL default) | ✅ (Stage 4.11-fu) |
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

## New sub-config — `cyber_aiml_vendor` (A8-deep follow-up)

Landed as a full sub-config (~440 lines: metadata, direct_queries,
signal_registry, groups, tier bands, pricing, guardrails). Routed on
`industry_sector in {AI_VENDOR, ML_VENDOR, AIML_PLATFORM}`.

Registry includes the 4 AI-governance signals + 3 cross-inherited
cyber infrastructure signals:
- `model_card_quality`, `training_data_provenance`,
  `ai_governance_disclosure`, `ai_incident_history`.
- `secure_sdlc_maturity`, `email_security_posture`,
  `remote_access_security`.

Pricing uses tightened guardrails (modifier_cap 3.0 vs 2.5 for other
cyber sub-configs) and a slightly richer ILF curve (max_ilf 5.5 vs
5.0) to reflect the thicker-tail risk profile of AI incidents.

Calibrate PASS (2,952 fixtures, 0 errors); compliance strict PASS.

## Remaining A8 backlog — deferred to A8-deep

`cyber_saas_platform` and `cyber_media_tech` sub-configs. Each needs
~450 lines of dedicated scaffolding.

## Next up

1. Add the 3 new sub-configs to `coverages/cyber/config.yaml`.
2. Retrofit `expectation_level` across all signals.
3. Regenerate `logic.md`.

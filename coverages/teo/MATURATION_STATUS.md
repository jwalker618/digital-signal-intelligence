# Tech E&O — V6 Maturation Status (B8)

Depth-first build **complete** (Stage 3.7 of the Option-D plan).

| Mature Bar | Current | Status |
|------------|---------|--------|
| 5 sub-configs | 5 | ✅ |
| ≥ 22 signal IDs | 34 | ✅ |
| ≥ 60 inference functions | scaffolded derived fns landed | ✅ |
| Primary config ≥ 40 scored signals | 34 | ⏳ +6 |
| Routing constraints on every sub-config | 5/5 | ✅ |
| Parametric ILF curves per product_type | auto-generated | ✅ |
| Guardrails populated | all 5 sub-configs | ✅ |
| 10 golden entities green | **10** | ✅ |
| `calibrate --coverage teo` returns PASS | **PASS** (720/720) | ✅ |
| `assess_config_compliance` returns 0 errors | **0** | ✅ |

## Routing

| Sub-config | Routes on |
|------------|-----------|
| teo_saas | business_model == 'saas' |
| teo_aiml_vendor | business_model == 'aiml_vendor' |
| teo_systems_integrator | business_model == 'systems_integrator' |
| teo_managed_service_provider | business_model == 'managed_services' |
| teo_sme | revenue < 25 000 000 |

## Goldens (10)

Salesforce, ServiceNow, Snowflake, Datadog (saas); OpenAI, Anthropic
(aiml_vendor); Accenture, Infosys (systems_integrator); CDW (msp);
RapidFlow Analytics (sme).

## Remaining

- +6 signals to reach ≥40.
- +26 derived inference fns to reach ≥60.
- Real inference bodies after Stage 6 (GitHub org + SOC2 attestation
  + BuiltWith extractors).

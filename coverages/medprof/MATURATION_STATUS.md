# MedProf Coverage — V6 Maturation Status (B1)

V6/B1 depth-first build **complete**. Most Mature Bar items landed in
the initial build; remaining items tracked below.

| Mature Bar | Current | Status |
|------------|---------|--------|
| 5 sub-configs (hospital / physician_group / nursing_home / telehealth / sme) | 5 | ✅ |
| ≥ 22 unique signal IDs in primary registry | 32 | ✅ |
| ≥ 60 coverage-specific inference functions | 32 | ⏳ +28 derived functions planned |
| Primary config ≥ 40 scored signals | 32 | ⏳ +8 to reach 40 |
| `expectation_level` on every scored signal | partial | ⏳ retrofit |
| `routing_constraints` on every non-general sub-config | 5/5 | ✅ |
| Parametric ILF curves per product_type | auto-generated | ✅ |
| Guardrails populated (floor/cap/ratios) | all 5 sub-configs | ✅ |
| 10 golden entities green | **10** | ✅ |
| `calibrate --coverage medprof` returns PASS | **PASS** | ✅ |
| `assess_config_compliance` returns 0 errors | **0** | ✅ |
| `logic.md` regenerated | yes | ✅ |

## Goldens (10)

HCA Healthcare, Ascension, Tenet, Kaiser Permanente, Northwell,
Cleveland Clinic (hospital); Teladoc Health (telehealth); Brookdale
Senior Living, Genesis Healthcare (nursing home); Pediatrix Medical
Group (physician group).

## What's shipped

- `coverages/medprof/config.yaml` — 5 sub-configs with
  `routing_constraints` (employee_count + facility_type + product_type),
  32 signals in each sub-config's signal_registry, four canonical
  three_layer_assessment groups (public_record / technical_infrastructure
  / structured_data / corporate_footprint), guardrails, ILF curves per
  product_type.
- `signal_architecture/signals/inference/functions/medprof/` —
  `mpl_signals.py` registers 32 inference functions mapped to the
  config's `inference_utility_function` names. Each returns a neutral
  (score=500) SignalResult with proxy-tier-scaled confidence.
- `tests/fixtures/golden_entities/medprof/` — 10 snapshot fixtures
  covering hospital / physician / LTC / telehealth sub-configs.
- `coverages/medprof/logic.md` — generated.

## Remaining (Stage 2 closure)

1. Add 8 more signals to the primary config to hit the ≥ 40 bar
   (candidates: npdb_proxy_signal, cms_value_based_payment_participation,
   quality_measure_trend, sentinel_event_disclosure,
   peer_review_process_depth, staffing_ratio_benchmark,
   infection_control_score, credentialing_process_maturity).
2. Author 28 derived inference functions (rolling aggregations,
   specialty-mix composites) to hit the ≥ 60 bar.
3. Retrofit `expectation_level` annotation on every scored signal.
4. Replace the neutral-body inference functions with real logic once
   Stage 6 (D-extractor depth) wires CMS Hospital Compare, Joint
   Commission, and NPDB extractors to return meaningful fields.

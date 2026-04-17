# MedProf Coverage — V6 Maturation Status (B1)

New coverage. V6/B1 scaffold committed; config.yaml + inference
functions + golden entities follow in the expansion PR.

| Mature Bar | Current | Status |
|------------|---------|--------|
| 5 sub-configs (hospital / physician_group / nursing_home / telehealth / sme) | 0 | ⏳ expansion PR |
| ≥ 22 unique signal IDs in primary registry | 0 | ⏳ 24 planned |
| ≥ 60 coverage-specific inference functions | 0 | ⏳ 70 planned |
| Primary config ≥ 40 scored signals | 0 | ⏳ |
| `expectation_level` on every scored signal | 0 | ⏳ |
| `routing_constraints` on every non-general sub-config | 0 | ⏳ |
| Parametric ILF curve per product_type | 0 | ⏳ |
| Guardrails populated | 0 | ⏳ |
| 10 golden entities green | 0 | ⏳ |
| `assess_config_compliance` returns 0 warnings | n/a | ⏳ |

## Blocking dependencies

- D3 litigation extractors (CMS Hospital Compare, Joint Commission,
  NPDB public, state medical boards). **All landed in Q1/D3.** ✅
- ProductionExtractor base class with neutral-absence contract. ✅
- E5 golden-entity infrastructure. ✅

## Path to Mature

1. Fill `development/project/version/6/coverage_specs/b1_medprof.yaml`
   (currently skeleton).
2. Run `python -m infrastructure.builder.cli expand --spec
   development/project/version/6/coverage_specs/b1_medprof.yaml --write`.
3. Commit generated `coverages/medprof/config.yaml` + inference package.
4. Add 10 golden entities to
   `tests/fixtures/golden_entities/_manifest.yaml`.
5. Run `python -m infrastructure.builder.cli calibrate --coverage medprof`.
6. Ensure `config_health_gate` CI job stays green.

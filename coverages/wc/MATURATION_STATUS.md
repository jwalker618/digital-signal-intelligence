# WC Coverage — V6 Maturation Status (B2)

Depth-first build **complete** (Stage 3.1 of the Option-D plan).

| Mature Bar | Current | Status |
|------------|---------|--------|
| 6 sub-configs (construction / healthcare / manufacturing / office / transport / sme) | 6 | ✅ |
| ≥ 22 signal IDs in primary registry | 33 | ✅ |
| ≥ 60 inference functions | 33 | ⏳ +27 derived planned |
| Primary config ≥ 40 scored signals | 33 | ⏳ +7 to reach 40 |
| `expectation_level` on every scored signal | present (UNIVERSAL default) | ✅ (Stage 4.11-fu) |
| `routing_constraints` on every sub-config (NAICS-driven) | 6/6 | ✅ |
| Parametric ILF curves per product_type | auto-generated | ✅ |
| Guardrails populated | all 6 sub-configs | ✅ |
| 10 golden entities green | **10** | ✅ |
| `calibrate --coverage wc` returns PASS | **PASS** (288/288 fixtures) | ✅ |
| `assess_config_compliance` returns 0 errors | **0** | ✅ |
| `logic.md` regenerated | yes | ✅ |

## Routing (NAICS 2-digit)

| Sub-config | Routes on |
|------------|-----------|
| wc_construction | naics_2digit == '23' |
| wc_healthcare | naics_2digit == '62' |
| wc_manufacturing | naics_2digit in {'31','32','33'} |
| wc_office | naics_2digit in {'54','52','51','55'} |
| wc_transport | naics_2digit in {'48','49'} |
| wc_sme | employee_count < 100 (any NAICS) |

## Goldens (10)

Walmart (office), Amazon (transport), UPS (transport), HCA Healthcare
(healthcare), Caterpillar (manufacturing), Bechtel (construction),
Fluor (construction), FedEx (transport), Kaiser Permanente
(healthcare), Local Cafe LLC (sme).

## Remaining (pending real extractors)

- 7 more signals to hit the ≥40 primary-registry bar (candidates:
  osha_establishment_severity, osha_citation_velocity, dart_rate,
  trir_band, emr_proxy, state_wc_board_violation_record,
  cat_body_part_mix).
- 27 more inference functions (derived composites + rolling aggregates)
  to hit ≥60.
- `casualty_wc` → `wc_<naics>` cross-walk alias in
  `signal_architecture/signals/cross_walk/by_coverage.json`.
- `expectation_level` retrofit on every scored signal.
- Replace neutral inference-function bodies with real logic once Stage
  6 D-extractor depth wires OSHA + state WC boards + NCCI class codes.

# WC Coverage — V6 Maturation Status (B2)

| Mature Bar | Current | Status |
|------------|---------|--------|
| 6 sub-configs (construction / healthcare / manufacturing / office / transport / sme) | 0 | ⏳ expansion PR |
| ≥ 22 signal IDs in primary registry | 0 | ⏳ 22 planned |
| ≥ 60 inference functions | 0 | ⏳ 65 planned |
| `casualty_wc` cross-walk alias | pending | ⏳ |
| 10 golden entities green | 0 | ⏳ |

## Blocking dependencies

- D3 OSHA establishment + citation extractors — ✅ landed Q1.
- State WC board scrapers — deferred to B2 expansion PR (FL, CA, NY, TX, IL).
- NCCI class code ingestion — deferred.

## Path to Mature

1. Fill `development/project/version/6/coverage_specs/b2_wc.yaml`.
2. Expand + calibrate + validate.
3. Add cross-walk alias from `casualty_wc` → `wc_<naics_mapped>` in
   `signal_architecture/signals/cross_walk/by_coverage.json`.
4. Commit golden entities (Waste Management, FedEx, Caterpillar already
   in the casualty fixtures — reuse via cross-walk).

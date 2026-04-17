# Environmental Impairment — V6 Maturation Status (B4)

| Mature Bar | Current | Status |
|------------|---------|--------|
| 5 sub-configs | 0 | ⏳ |
| ≥ 22 signal IDs | 0 | ⏳ 22 planned |
| ≥ 60 inference functions | 0 | ⏳ 65 planned |
| 10 golden entities | 0 | ⏳ |
| `casualty_environmental` cross-walk alias | pending | ⏳ |

## Dependencies

- D3 regulatory extractors (EPA, TRI, Superfund, NRC) — ✅ Q1.
- D5 climate extractors (TRI, Superfund, NRC, MSHA, Copernicus) — ✅ Q2.
- MSHA scraper — gated on B4 expansion PR.

## Path to Mature

1. Fill `development/project/version/6/coverage_specs/b4_env_liab.yaml`.
2. Expand → calibrate → validate.
3. Add cross-walk alias: `casualty_environmental` → `env_industrial`
   in `signal_architecture/signals/cross_walk/by_coverage.json`.
4. 10 goldens (Waste Management, DuPont, Chevron — reuse from casualty;
   add 3M, Dow, Veolia, Clean Harbors, Republic Services, Orsted,
   Cargill).

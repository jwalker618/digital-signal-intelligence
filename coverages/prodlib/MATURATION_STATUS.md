# Product Liability — V6 Maturation Status (B3)

| Mature Bar | Current | Status |
|------------|---------|--------|
| 5 sub-configs | 0 | ⏳ |
| ≥ 22 signal IDs | 0 | ⏳ 24 planned |
| ≥ 60 inference functions | 0 | ⏳ 70 planned |
| 10 golden entities | 0 | ⏳ |

## Dependencies

- D3 recalls extractors (CPSC, FDA, NHTSA, FSIS, EU Safety Gate) — ✅ Q1.
- D4 USPTO (patent-litigation density) — ⏳ Q3.

## Path to Mature

1. Fill `development/project/version/6/coverage_specs/b3_prodlib.yaml`.
2. Expand → calibrate → validate.
3. 10 goldens (Procter & Gamble, Johnson & Johnson, Toyota, Ford,
   Medtronic, Stryker, Nestlé, Kraft Heinz, Colgate-Palmolive, 3M).

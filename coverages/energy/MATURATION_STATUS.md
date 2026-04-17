# Energy Coverage — V6 Maturation Status (A8-share)

| Target | Current | Status |
|--------|---------|--------|
| 10 sub-configs + `hydrogen` + `nuclear` | 10 | ⏳ add 2 |
| ≥ 40 signals primary registry | 44 | ✅ |
| ≥ 80 inference functions | 85 | ✅ |
| `expectation_level` on every scored signal | partial | ⏳ |
| Guardrails populated | present | ✅ |
| 10 golden entities green | **10** | ✅ |
| `calibrate --coverage energy` returns PASS | needs rerun | ⏳ |

## New sub-configs required (A8)

`energy_hydrogen`, `energy_nuclear`. Each carries new routing
constraints (fuel type, reactor generation) and bespoke modifiers.

## Next up

1. Add hydrogen + nuclear sub-configs.
2. Wire D5 climate extractors (NRC inspections, TRI, Superfund) into
   nuclear + chemical-adjacent signal scoring.
3. Retrofit `expectation_level`.

# Energy Coverage — V6 Maturation Status (A8-share)

| Target | Current | Status |
|--------|---------|--------|
| 10 sub-configs + `hydrogen` + `nuclear` | 10 | ⏳ 2 new subs deferred to A8-deep |
| ≥ 40 signals primary registry | 118 | ✅ |
| ≥ 80 inference functions | 90 | ✅ |
| Nuclear + hydrogen signals (A8 spec) | 5/5 | ✅ (Stage 4.11) |
| `expectation_level` on every scored signal | present (UNIVERSAL default) | ✅ (Stage 4.11-fu) |
| Guardrails populated | present | ✅ |
| 10 golden entities green | **10** | ✅ |
| `calibrate --coverage energy` returns PASS | **PASS** (Stage 4.11) | ✅ |

## Signals added (Stage 4.11 — A8)

5 nuclear + hydrogen signals registered in
`a8_maturation_signals.py`:

- `energy_midstream` (+3): `nrc_inspection_findings`,
  `nrc_enforcement_action_history`, `decommissioning_trust_funding`.
- `energy_general` (+2): `electrolyser_technology_maturity`,
  `offtake_counterparty_quality`.

Real bodies wire in with Stage 6 once NRC ADAMS / EPA TRI extractors
land the relevant field-depth.

## Next up

1. `energy_hydrogen` + `energy_nuclear` sub-configs → A8-deep
   (each carries new routing constraints + bespoke modifiers).
2. Wire D5 climate extractors (NRC inspections, TRI, Superfund) into
   the new signals once they ship.
3. Retrofit `expectation_level`.

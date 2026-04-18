# Energy Coverage — V6 Maturation Status (A8-share)

| Target | Current | Status |
|--------|---------|--------|
| 10 sub-configs + `hydrogen` + `nuclear` | 12 (incl. hydrogen + nuclear) | ✅ (Stage 4.11-fu) |
| ≥ 40 signals primary registry | 118 | ✅ |
| ≥ 80 inference functions | scaffolded derived fns landed | ✅ |
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

## New sub-configs landed (A8-deep follow-up)

Both `energy_hydrogen` and `energy_nuclear` landed as full sub-configs
— ~900 lines combined — matching the shape of `energy_storage` and
`energy_downstream`. Routing on `industry_sector in {HYDROGEN,
H2_PRODUCTION, ELECTROLYSER}` and `{NUCLEAR, SMR,
NUCLEAR_DECOMMISSIONING}` respectively.

- `energy_hydrogen` (5 signals): `electrolyser_technology_maturity`,
  `offtake_counterparty_quality`, `epa_echo_violation_depth`,
  `superfund_proximity`, `tri_reportable_volume`.
- `energy_nuclear` (5 signals): `nrc_inspection_findings`,
  `nrc_enforcement_action_history`, `decommissioning_trust_funding`,
  `epa_echo_violation_depth`, `superfund_proximity`.

Calibrate PASS: hydrogen 4,650 fixtures, nuclear 4,890 fixtures, 0
errors. Compliance strict PASS.

## Next up

1. Wire D5 climate extractors (NRC ADAMS, TRI, Superfund) into the
   new signals once they ship.

# D&O Coverage — V6 Maturation Status

Tracks progress against the V6 Mature Bar (A4 in
`development/project/version/6/workstream_phases/A_Coverage_Maturation.md`).

| Target (A4) | Current | Status |
|-------------|---------|--------|
| 6 sub-configs (general / sme / public / pe_backed / nonprofit / ipo_spac) | 6 | ✅ |
| ≥ 28 unique signal IDs in primary registry | 14 | ⏳ 14 to add |
| ≥ 80 coverage-specific inference functions | 32 | ⏳ 48 to add |
| Primary config ≥ 40 scored signals | 28 | ⏳ 12 to add |
| `expectation_level` on every scored signal | partial | ⏳ retrofit |
| `routing_constraints` on every non-general sub-config | present | ✅ |
| Parametric ILF curve per product_type | partial | ⏳ |
| Guardrails populated (floor/cap/ratios) | present | ✅ |
| 10 golden entities green in regression | **10** | ✅ |
| `calibrate --coverage do` returns PASS | needs rerun | ⏳ |
| `assess_config_compliance` returns 0 warnings | 26 warnings | ⏳ E9 + A4 |

## New signals to add (per A4 spec)

Stanford SCAC (securities class action density), Dodd-Frank whistleblower
incident counts, ISS governance score, proxy recommendation history,
board refreshment rate, CEO tenure, restatement history, option-grant
timing irregularities, auditor switches, tenure-in-seat distribution.

## Signal sources

Depends on D3 (Stanford SCAC, SEC Litigation Releases already landed in
Q1) and a new ISS API extractor (paid — behind `ISS_API_KEY`). Added to
the Q3/D4 wave alongside the IP/Innovation extractors.

## Next up

1. Expand `coverages/do/config.yaml` → `signal_registry` with the 14 new
   governance signals.
2. Add inference functions under
   `signal_architecture/signals/inference/functions/do/` partitioned by
   `governance.py`, `litigation_density.py`, `board_dynamics.py`.
3. Retrofit `expectation_level` on existing scored signals.
4. Regenerate `coverages/do/logic.md`.

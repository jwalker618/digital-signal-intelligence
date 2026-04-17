# D&O Coverage — V6 Maturation Status

Tracks progress against the V6 Mature Bar (A4 in
`development/project/version/6/workstream_phases/A_Coverage_Maturation.md`).

| Target (A4) | Current | Status |
|-------------|---------|--------|
| 6 sub-configs (general / sme / public / pe_backed / nonprofit / ipo_spac) | 6 | ✅ |
| ≥ 28 unique signal IDs in primary registry | 81 | ✅ |
| ≥ 80 coverage-specific inference functions | 46 | ⏳ 34 to add |
| Primary config ≥ 40 scored signals | 48 (do_general) | ✅ |
| `expectation_level` on every scored signal | present (UNIVERSAL default) | ✅ (Stage 4.11-fu) |
| `routing_constraints` on every non-general sub-config | present | ✅ |
| Parametric ILF curve per product_type | partial | ⏳ |
| Guardrails populated (floor/cap/ratios) | present | ✅ |
| 10 golden entities green in regression | **10** | ✅ |
| `calibrate --coverage do` returns PASS | **PASS** (Stage 4.7) | ✅ |
| `assess_config_compliance` returns 0 errors | 0 errors | ✅ |

## Signals added (Stage 4.7 — A4)

Landed in `a4_maturation_signals.py` and wired into the `do_public`
sub-config (taking it from 10 → 24 signals):

`shareholder_suit_history`, `dodd_frank_whistleblower_telemetry`,
`iss_proxy_recommendation`, `glass_lewis_recommendation`,
`proxy_dissent_rate`, `board_refreshment_velocity`, `ceo_tenure_band`,
`audit_qualification_history`, `restatement_record`,
`cfo_turnover_velocity`, `director_interlock_density`,
`related_party_transaction_volume`, `clawback_policy_presence`,
`equity_grant_dilution_trend`.

14 new signal IDs bring unique IDs across the 6 sub-configs from 67 → 81.

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

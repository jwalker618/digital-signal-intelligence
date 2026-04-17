# Marine Coverage — V6 Maturation Status

Tracks progress against the V6 Mature Bar (A7 in
`development/project/version/6/workstream_phases/A_Coverage_Maturation.md`).

| Target (A7) | Current | Status |
|-------------|---------|--------|
| 7 sub-configs | 7 | ✅ |
| ≥ 30 unique signal IDs in primary registry | 81 | ✅ |
| ≥ 80 coverage-specific inference functions | 46 | ⏳ 34 to add |
| Primary config ≥ 40 scored signals | 50 (marine_general) | ✅ |
| `expectation_level` on every scored signal | present (UNIVERSAL default) | ✅ (Stage 4.11-fu) |
| `routing_constraints` on every non-general sub-config | present | ✅ |
| Parametric ILF curve per product_type | partial | ⏳ STS + offshore |
| Guardrails populated (floor/cap/ratios) | present | ✅ |
| 10 golden entities green in regression | **10** | ✅ |
| `calibrate --coverage marine` returns PASS | **PASS** (Stage 4.10) | ✅ |
| `assess_config_compliance` returns 0 errors | 0 errors | ✅ |

## Signals added (Stage 4.10 — A7)

10 new signal IDs landed in `a7_maturation_signals.py` and wired into
5 depth-starved sub-configs (each now 8-15 signals):

- `marine_tanker` (+4): `ais_dark_activity_rate`,
  `ais_spoofing_signal`, `paris_mou_detention_history`,
  `sts_transfer_density`.
- `marine_cargo` (+4): `paris_mou_detention_history`,
  `tokyo_mou_detention_history`, `flag_of_convenience_proxy`,
  `vessel_age_profile_curve`.
- `marine_offshore` (+3): `class_society_transfer_frequency`,
  `imo_cic_campaign_results`, `vessel_age_profile_curve`.
- `marine_war_risk` (+3): `piracy_corridor_exposure`,
  `ais_dark_activity_rate`, `flag_of_convenience_proxy`.
- `marine_high_value` (+4): `paris_mou_detention_history`,
  `tokyo_mou_detention_history`, `vessel_age_profile_curve`,
  `class_society_transfer_frequency`.

Neutral scaffolds; real bodies wire in with Stage 6 (AIS Hub, Marine
Cadastre, EMSA THETIS, Paris MoU, Tokyo MoU, IMO GISIS deep, IMB).

## Signal sources

D6 (sector telemetry — AIS Hub, Marine Cadastre, EMSA THETIS, Paris+Tokyo
MoU) ships in Q3. A7 depth signals gate on that delivery.

## Next up

1. Wire AIS pipeline once D6 lands.
2. Expand inference functions under
   `signal_architecture/signals/inference/functions/marine/` into
   `ais_analytics.py`, `port_state_compliance.py`, `offshore_ops.py`.

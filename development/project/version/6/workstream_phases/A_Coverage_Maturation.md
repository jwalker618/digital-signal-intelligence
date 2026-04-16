# Workstream A — Coverage Maturation

| Item | Value |
|------|-------|
| Version | 1.0 |
| Depends on | E2 (Config Health Gate), E5 (Golden Entities), D1/D3 (free signal sources) |
| Phases | A1–A8 |

---

## Maturity Bar (applies to every phase in this workstream)

- ≥ 6 sub-configs covering the material market segments for that line.
- ≥ 22 unique signal IDs in the signal registry for the primary config.
- ≥ 60 coverage-specific inference functions under `signal_architecture/signals/inference/functions/{coverage}/`.
- Primary config: ≥ 40 scored signals.
- Every scored signal carries `expectation_level` (UNIVERSAL / ENTERPRISE / CORPORATE / SME / MICRO).
- Every non-general sub-config carries multiplexer `routing_constraints`.
- `limit_configuration` is `DECOUPLED` (except SME sub-configs which may be `BUNDLED`).
- A parametric ILF curve per `product_type` with `anchor_limit == base_limit_reference`.
- Guardrails populated: `modifier_floor`, `modifier_cap`, `max_premium_to_limit_ratio`, `max_premium_to_revenue_ratio`, `max_ilf_factor`.
- `logic.md` regenerated via `python coverages/doc_generator.py`.
- Regression harness: `tests/integration/test_{coverage}_regression.py` pricing 10 golden entities within tolerance.
- `python -m infrastructure.builder.cli calibrate --coverage {name}` returns PASS.
- `python development/project/assessments/scripts/assess_config_compliance.py coverages/{name}/config.yaml` returns 0 warnings.

---

## A1 — FPR Maturation (weakest today → Mature)

**Current**: 5 sub-configs, 13 signal IDs, 21 inference fns.
**Target**: 5 sub-configs (retained but rebuilt), 22 signal IDs, 70+ inference fns.

### Sub-configs (reshape, don't add)
| Sub-config | Focus | Key `routing_constraints` |
|------------|-------|---------------------------|
| `fpr_trade_credit` | Buyer-credit, receivables | `product_type == "trade_credit"` |
| `fpr_political_risk` | Country / sector political exposure | `product_type == "political_risk"` |
| `fpr_surety` | Contract + commercial surety | `product_type == "surety_bond"` |
| `fpr_kidnap_ransom` | Executive / travel K&R | `product_type == "kidnap_ransom"` |
| `fpr_sme` | Streamlined SME | `revenue < 25_000_000` |

### New signal IDs (minimum 22 total)
Trade credit: `buyer_portfolio_quality`, `buyer_concentration`, `buyer_country_rating`, `sector_credit_spread`, `dso_drift`, `trade_receivables_turnover`.
Political: `acled_incident_density`, `icrg_composite`, `wb_wgi_score`, `ofac_country_tier`, `capital_controls_watchlist`, `bit_treaty_coverage`.
Surety: `obligee_quality`, `bonded_project_type`, `state_contractor_license_record`, `paydex_proxy`, `bond_penalty_ratio`, `wip_backlog_consistency`.
K&R: `acled_kfr_rate_country`, `travel_pattern_density`, `sector_kfr_overlay`, `executive_exposure_footprint`.

### Inference functions
New package: `signal_architecture/signals/inference/functions/fpr/`. Split by domain:
- `trade_credit.py` (12 fns), `political.py` (14 fns), `surety.py` (16 fns), `kidnap_ransom.py` (12 fns), `fpr_common.py` (cross-shared — 16 fns).

### Signal sources required (from D1/D3)
ACLED, World Bank WGI, ICRG (paid — behind env var), OFAC country lists, GLEIF LEI, OpenCorporates, state contractor-license boards, FRED credit spreads, Dun & Bradstreet (paid, env-var-gated).

### Expected deliverables
1. `coverages/fpr/config.yaml` rebuilt against the new signal registry.
2. `coverages/fpr/logic.md` regenerated.
3. `signal_architecture/signals/inference/functions/fpr/` with 70+ fns and tests.
4. 10 golden entities under `tests/fixtures/golden_entities/fpr/`.
5. Regression suite green.

---

## A2 — Property Maturation

**Current**: 5 sub-configs, 12 signal IDs, 27 inference fns.
**Target**: 6 sub-configs, 22 signal IDs, 70+ inference fns.

### Sub-configs
| Sub-config | Focus | `routing_constraints` |
|------------|-------|----------------------|
| `property_cat_exposed` | CAT (wind/flood/EQ/wildfire/hail) | `cat_exposed == true` |
| `property_high_value` | HNW residential + commercial HV | `tiv > 25_000_000` |
| `property_builders_risk` | Construction-phase | `product_type == "builders_risk"` |
| `property_habitational` | Apartments / hotels / senior living | `occupancy_class == "habitational"` |
| `property_general` | Default corporate | — |
| `property_sme` | SME SR | `revenue < 25_000_000` |

### New signal IDs
`fema_flood_zone`, `noaa_hail_history`, `usfs_wildfire_hazard`, `usgs_seismic_vs30`, `nhc_track_proximity`, `iso_caf_bceg_code_compliance`, `energy_star_score`, `roof_age_proxy`, `building_permit_trail`, `sprinkler_fire_protection_class`, `overhead_imagery_condition_score`, `habitational_egress_density`, `crowd_footfall_proxy`, `wildfire_community_preparedness`, `nfip_participation`.

### Inference functions
`signal_architecture/signals/inference/functions/property/` expanded to 70+ fns across `cat_perils.py`, `building_envelope.py`, `occupancy.py`, `habitational.py`, `builders_risk.py`, `property_common.py`.

### Signal sources required (from D5)
FEMA NFHL, NOAA CDO / SPC Storm Events, USFS Wildfire Hazard Potential, USGS Vs30, NHC Historical Track, ENERGY STAR, Bing Maps / Mapbox overhead imagery, ISO CAF/BCEG, Google Places footfall (affordable proxy).

---

## A3 — Casualty Maturation

**Current**: 6 sub-configs, 15 signal IDs, 31 inference fns.
**Target**: 6 sub-configs (casualty_wc becomes a cross-walk alias after B2 ships), 26 signal IDs, 80+ inference fns.

### Sub-configs (rebalanced)
| Sub-config | Focus | `routing_constraints` |
|------------|-------|----------------------|
| `casualty_gl` | Premises + operations GL | `product_type == "general_liability"` |
| `casualty_auto` | Commercial auto / fleet | `product_type == "commercial_auto"` |
| `casualty_environmental` | Pollution legal liability | superseded by B4 on cross-walk |
| `casualty_umbrella` | Umbrella / excess | `product_type == "umbrella"` |
| `casualty_general` | Default multiline | — |
| `casualty_sme` | Streamlined SME | `revenue < 25_000_000` |

(`casualty_wc` retired once B2 Workers' Compensation standalone ships.)

### New signal IDs
GL: `premises_occupancy_class`, `crowd_density_proxy`, `slip_fall_benchmark`, `guest_injury_disclosure_trail`.
Auto: `fmcsa_sms_basic_scores`, `dot_inspection_history`, `csa_crash_indicator`, `fleet_telematics_benchmark`, `vehicle_age_distribution`, `driver_hos_compliance`.
Environmental: `epa_echo_violation_depth`, `superfund_proximity`, `tri_reportable_volume`, `state_dep_action_history`.
Umbrella: `underlying_schedule_consistency`, `attachment_point_coherence`, `lead_carrier_quality`.

### Inference functions
`signal_architecture/signals/inference/functions/casualty/` expanded to 80+ fns.

### Signal sources required
OSHA establishment severity, FMCSA SMS, CSA, DOT inspection, EPA ECHO (already wired, deeper use), TRI, Superfund NPL, state DEQ/DEP.

---

## A4 — D&O Maturation

**Current**: 6 sub-configs, 21 signal IDs, 60 inference fns.
**Target**: 6 sub-configs, 28 signal IDs, 80+ inference fns.

### Sub-configs (retain)
`do_public`, `do_pe_backed`, `do_nonprofit`, `do_ipo_spac`, `do_general`, `do_sme`.

### New signal IDs
`shareholder_suit_history` (Stanford SCAC), `dodd_frank_whistleblower_telemetry`, `iss_proxy_recommendation`, `glass_lewis_recommendation`, `proxy_dissent_rate`, `board_refreshment_velocity`, `ceo_tenure_band`, `audit_qualification_history`, `restatement_record` (SEC 4.02), `cfo_turnover_velocity`, `director_interlock_density`, `related_party_transaction_volume`, `clawback_policy_presence`, `equity_grant_dilution_trend`.

### Signal sources required
Stanford SCAC, SEC EDGAR (already wired — deeper DEF 14A parsing), ISS / Glass Lewis (paid, env-var-gated), Boardex-like proxies (free via CrossRef + OpenAlex).

---

## A5 — FI Maturation

**Current**: 6 sub-configs, 21 signal IDs, 60 inference fns.
**Target**: 6 sub-configs, 30 signal IDs, 85+ inference fns.

### Sub-configs (retain + enrich)
`fi_bank`, `fi_insurer`, `fi_fintech`, `fi_crypto`, `fi_general`, `fi_sme`.

### New signal IDs
Bank: `ffiec_call_report_ratios`, `ubpr_roe_volatility`, `bsa_aml_enforcement`, `cra_rating`, `camels_proxy_composite`, `dfast_ccar_outcome`.
Insurer: `naic_rbc_band`, `iris_ratio_band`, `complaint_index`, `jiri_index`.
Fintech: `sponsor_bank_dependency`, `bsa_findings_velocity`, `complaint_velocity`.
Crypto: `ofac_exposure_proxy`, `mixer_tumbler_interaction`, `travel_rule_compliance`, `reserve_attestation_cadence`, `cex_dex_exposure_mix`.
Universal: `s&p_fitch_moodys_rating_band`, `cds_spread_volatility` (FRED).

### Signal sources required
FFIEC (free), NAIC (free — state DOI feeds), Chainalysis-style proxies (free blockchain explorers), Travel Rule Protocol directory.

---

## A6 — Aerospace Maturation

**Current**: 7 sub-configs, 24 signal IDs, 68 inference fns.
**Target**: 7 sub-configs, 30 signal IDs, 80+ inference fns.

### Sub-configs (retain)
`aerospace_general`, `aerospace_sme`, `aerospace_high_value`, `aerospace_mro`, `aerospace_rotary`, `aerospace_space`, `aerospace_unmanned`.

### New signal IDs
`opensky_route_telemetry`, `fleet_age_distribution`, `icao_annex19_sms_proxy`, `asias_incident_count`, `fsims_training_depth`, `part_145_repair_station_band`, `part_121_135_cert_band`, `rotary_mro_history`, `space_launch_cadence`, `uas_part107_compliance`.

### Signal sources required
OpenSky Network (free), ICAO Annex 19 proxy via AICC directories, ASIAS reports (free), FSIMS public data, FAA Part 145 + Part 121 + Part 135 certificate lookups.

---

## A7 — Marine Maturation

**Current**: 7 sub-configs, 23 signal IDs, 70 inference fns.
**Target**: 7 sub-configs, 30 signal IDs, 80+ inference fns.

### Sub-configs (retain)
`marine_cargo`, `marine_tanker`, `marine_offshore`, `marine_war_risk`, `marine_high_value`, `marine_general`, `marine_sme`.

### New signal IDs
`ais_dark_activity_rate`, `ais_spoofing_signal`, `paris_mou_detention_history`, `tokyo_mou_detention_history`, `class_society_transfer_frequency`, `imo_cic_campaign_results`, `flag_of_convenience_proxy`, `sts_transfer_density`, `piracy_corridor_exposure`, `vessel_age_profile_curve`.

### Signal sources required
AIS Hub, Marine Cadastre, EMSA THETIS, Paris MoU, Tokyo MoU, IMO GISIS (already wired — deeper use), classification society registries (Lloyd's Register, DNV, ABS, BV public pages).

---

## A8 — Cyber / PI / Energy Finishing

Already at "Mature" on signal-count criterion; this phase closes the three remaining items:

### A8.1 — Cyber sub-config additions
Add `cyber_saas_platform` and `cyber_aiml_vendor` as new sub-configs (total: 13). `cyber_aiml_vendor` introduces four new signal IDs: `model_card_quality`, `training_data_provenance`, `ai_governance_disclosure`, `ai_incident_history` (from AIIDR — AI Incident Database).

### A8.2 — PI sub-config additions
Add `pi_clinical_research` and `pi_media_tech` (total: 15). `pi_clinical_research` adds `irb_registration`, `clinical_trial_registry_compliance`, `good_clinical_practice_score`. `pi_media_tech` adds `defamation_exposure`, `content_moderation_posture`.

### A8.3 — Energy sub-config additions
Add `energy_hydrogen` and `energy_nuclear` (total: 12). `energy_nuclear` adds `nrc_inspection_findings`, `nrc_enforcement_action_history`, `decommissioning_trust_funding`; `energy_hydrogen` adds `electrolyser_technology_maturity`, `offtake_counterparty_quality`.

### A8.4 — Cross-retrofit
- Add `expectation_level` to every scored signal currently lacking it across cyber / pi / energy.
- Add `routing_constraints` to every non-general sub-config in these three coverages.
- Lock `guardrails.max_ilf_factor` based on the Q1 calibration-harness output.

---

## Acceptance for Workstream A

- Every existing coverage meets the Maturity Bar.
- `development/project/assessments/results/A-exit-{timestamp}.json` shows PASS across all 10 coverages.
- `tests/integration/test_*_regression.py` green on 100 golden entities (10 per coverage).
- `python -m infrastructure.builder.cli calibrate` returns PASS across every coverage × sub-config combination.
- `logic.md` regenerated for every coverage.
- Zero FIXME comments remaining in `coverages/*/config.yaml`.

# Workstream B — New Coverages

| Item | Value |
|------|-------|
| Version | 1.0 |
| Depends on | Workstream A (signal library & inference packages extended), D1/D3/D5/D6 (signal sources) |
| Phases | B1–B12 |

---

## Delivery Mechanism

Every new coverage ships via the **Coverage Expansion Pipeline**:

```
python -m infrastructure.builder.cli expand --spec development/project/version/6/coverage_specs/{phase}.yaml --write
python coverages/doc_generator.py
python -m infrastructure.builder.cli calibrate --coverage {name}
```

Each coverage must hit the same **Maturity Bar** defined in `A_Coverage_Maturation.md` — this is non-negotiable at ship.

**Coverage spec YAML** (one per phase under `development/project/version/6/coverage_specs/`) contains:
- Metadata (name, description, market, product types).
- Sub-configs with `routing_constraints` and `model_specificity`.
- Signal registry (minimum 22 IDs).
- Three-layer assessment group weights (risk/loss/exposure summing to 1.0).
- Proxy-tier distribution target (≥ 50% DIRECT_OBSERVABLE).
- Pricing anchors + ILF curves per product type.
- Guardrails.

**Pre-merge CI gate**: `config_health_gate` (E2) must pass before merge.

---

## Wave 1 (Q2) — Highest-Yield Coverages

### B1 — Medical Professional Liability

**Path**: `coverages/medprof/config.yaml`
**Sub-configs (5)**:
| Sub-config | Focus | `routing_constraints` |
|------------|-------|----------------------|
| `medprof_hospital` | Acute-care / teaching hospitals | `employee_count >= 500` |
| `medprof_physician_group` | Multi-specialty groups | `500 > employee_count >= 20` |
| `medprof_nursing_home` | LTC / SNF / assisted living | `facility_type == "ltc"` |
| `medprof_telehealth` | Telehealth / digital-first | `product_type == "telehealth"` |
| `medprof_sme` | Solo + small-group practice | `employee_count < 20` |

**New signal IDs (24)**:
`cms_star_rating`, `hospital_compare_mortality`, `hospital_compare_readmission`, `hhs_oig_leie_exposure`, `joint_commission_accreditation`, `state_medical_board_actions`, `cms_hospital_cost_report_margin`, `malpractice_claim_density_proxy`, `residency_training_program_quality`, `credentialing_process_maturity`, `ehr_interoperability_band`, `hipaa_breach_record`, `cms_adverse_event_reporting`, `specialty_mix_risk`, `bed_utilisation_band`, `telehealth_platform_quality`, `cross_state_licensure_compliance`, `npdb_proxy_signal`, `cms_value_based_payment_participation`, `quality_measure_trend`, `sentinel_event_disclosure`, `peer_review_process_depth`, `staffing_ratio_benchmark`, `infection_control_score`.

**Inference package**: `signal_architecture/signals/inference/functions/medprof/` (70+ fns).

**Sources (all free)**: CMS Hospital Compare, CMS Cost Reports, HHS OIG LEIE, Joint Commission, state medical boards, OCR HIPAA Breach Portal (already wired), NPDB public summary.

**Golden entities**: 10 public health systems + physician groups.

---

### B2 — Workers' Compensation (standalone)

**Path**: `coverages/wc/config.yaml`
**Sub-configs (6)**:
`wc_construction`, `wc_healthcare`, `wc_manufacturing`, `wc_office`, `wc_transport`, `wc_sme`.

**`routing_constraints`**: `naics_2digit IN (...)` per sub-config; `wc_sme` routes on `employee_count < 100`.

**New signal IDs (22)**:
`osha_establishment_severity`, `osha_citation_velocity`, `naics_exposure_band`, `dart_rate`, `trir_band`, `emr_proxy`, `state_wc_board_violation_record`, `class_code_exposure_mix`, `ergonomic_program_disclosure`, `return_to_work_program_band`, `cat_body_part_mix`, `dot_auto_overlap` (for transport), `hospital_worker_injury_trend` (for healthcare), `construction_fatality_proximity`, `heat_illness_exposure`, `manufacturing_cumulative_trauma_score`, `night_shift_exposure_band`, `safety_training_cadence`, `near_miss_reporting_culture`, `contractor_intensity`, `immigrant_worker_exposure_band`, `rural_ambulance_access`.

**Inference package**: `signal_architecture/signals/inference/functions/wc/` (65+ fns).

**Sources (all free)**: OSHA establishment + citations, state WC boards (varies — FL, CA, NY, TX, IL first), NCCI class code files (open), NAICS BLS injury statistics.

**Migration**: `casualty_wc` sub-config deprecated; cross-walk alias added so existing quotes still route.

---

### B3 — Product Liability / Recall

**Path**: `coverages/prodlib/config.yaml`
**Sub-configs (5)**:
`prodlib_consumer_goods`, `prodlib_medical_device`, `prodlib_auto_parts`, `prodlib_food_bev`, `prodlib_sme`.

**New signal IDs (24)**:
`cpsc_recall_history`, `fda_maude_device_adverse_events`, `fda_recall_history`, `nhtsa_recall_history`, `usda_fsis_recall_history`, `eu_rapex_notification_history`, `supplier_concentration`, `manufacturing_country_risk_mix`, `quality_management_certification_band`, `iso_9001_maturity`, `gmp_cgmp_compliance_proxy`, `warning_letter_fda_history`, `class_action_density`, `retailer_distribution_breadth`, `labelling_compliance_track_record`, `ingredient_source_transparency`, `product_lifecycle_stage`, `first_generation_product_exposure`, `white_label_dependency`, `amazon_marketplace_complaint_velocity`, `recall_response_maturity`, `product_insurance_exposure_breadth`, `r_and_d_investment_trend`, `patent_litigation_density`.

**Inference package**: `signal_architecture/signals/inference/functions/prodlib/` (70+ fns).

**Sources (all free)**: CPSC, FDA MAUDE + recalls + warning letters, NHTSA, USDA FSIS, EU Safety Gate (RAPEX), USPTO (patents).

---

### B4 — Environmental Impairment (standalone)

**Path**: `coverages/env_liab/config.yaml`
**Sub-configs (5)**:
`env_industrial`, `env_waste_mgmt`, `env_real_estate`, `env_energy_midstream_xwalk` (cross-walks to energy_midstream), `env_sme`.

**New signal IDs (22)**:
`epa_echo_violation_depth`, `tri_reportable_volume`, `tri_chemical_mix`, `superfund_npl_proximity`, `cerclis_site_exposure`, `state_deq_action_history`, `spill_reporting_cadence`, `rcra_compliance_band`, `npdes_permit_compliance`, `cercla_pra_band`, `agency_consent_decree_history`, `brownfield_redevelopment_exposure`, `air_permit_title_v_compliance`, `pfas_exposure_band`, `asbestos_lead_mgmt_proxy`, `underground_storage_tank_registry`, `nrc_material_license`, `mine_safety_mshza_record`, `environmental_justice_proximity`, `epa_ghg_reporter_band`, `tsca_inventory_exposure`, `climate_related_disclosure_maturity`.

**Inference package**: `signal_architecture/signals/inference/functions/env_liab/` (65+ fns).

**Sources (all free)**: EPA ECHO (already wired — deeper), TRI, Superfund NPL, CERCLIS, state DEQ/DEP, NRC, MSHA.

**Migration**: `casualty_environmental` remains as a cross-walk alias (routing preserved).

---

## Wave 2 (Q3)

### B5 — Construction / CAR / OCIP

**Path**: `coverages/construction/config.yaml`
**Sub-configs (5)**:
`con_gc` (general contractor), `con_subcontractor`, `con_infrastructure` (DOT / USACE heavy civil), `con_energy_xwalk` (cross-walks to energy configs for field construction), `con_sme`.

**New signal IDs (23)**:
`enr_top400_benchmark`, `state_contractor_license_board_record`, `osha_construction_sic_severity`, `dot_project_registry_history`, `usace_project_portfolio_track_record`, `contractor_fatality_history`, `scaffolding_fall_protection_exposure`, `wrap_program_experience`, `bid_backlog_wip_ratio`, `bonding_capacity_band`, `lien_history`, `change_order_velocity_proxy`, `contractor_workforce_stability`, `site_safety_training_cadence`, `crane_erection_license_band`, `demolition_asbestos_handling_cert`, `building_code_ibc_compliance`, `leed_certification_mix`, `prevailing_wage_compliance`, `union_density_proxy`, `subcontractor_quality_mix`, `bim_adoption_band`, `weather_exposure_profile`.

**Inference package**: `signal_architecture/signals/inference/functions/construction/` (65+ fns).

**Sources (all free except ENR)**: state contractor licensing boards, OSHA, DOT project registries, USACE public records, USPTO (patents), LEED (public), SAM.gov (federal contractor exclusions).

---

### B6 — Event Cancellation / Contingency

**Path**: `coverages/event/config.yaml`
**Sub-configs (5)**:
`event_sports`, `event_concert`, `event_conference`, `event_broadcast`, `event_sme`.

**New signal IDs (22)**:
`venue_weather_history`, `venue_seismic_exposure`, `acled_civil_unrest_proximity`, `google_trends_demand_proxy`, `ticketing_platform_quality`, `artist_promoter_track_record`, `event_scale_band`, `insurance_stacking_complexity`, `sponsor_quality_band`, `cancellation_history_proxy`, `regulatory_permit_trail`, `pandemic_clause_exposure`, `comms_backup_infrastructure`, `broadcast_rights_concentration`, `force_majeure_clause_maturity`, `talent_key_person_exposure`, `travel_dependency`, `catering_vendor_quality`, `security_contractor_quality`, `covid_variant_sensitivity`, `alcohol_service_exposure`, `crowd_capacity_band`.

**Inference package**: `signal_architecture/signals/inference/functions/event/` (60+ fns).

**Sources (all free)**: NOAA CDO, ACLED, Google Trends, venue public filings, SEC (for public broadcasters), state liquor boards.

---

### B7 — Political Violence & Terrorism (standalone)

**Path**: `coverages/pvt/config.yaml`
**Sub-configs (4)**:
`pvt_country_risk`, `pvt_sector_exposed`, `pvt_high_value_asset`, `pvt_sme`.

**New signal IDs (22)**:
`acled_incident_density_country`, `acled_incident_density_city`, `gtd_historical_incidents`, `gdelt_media_conflict_score`, `icrg_political_risk`, `state_osac_threat_level`, `fcdo_travel_advisory`, `sector_specific_acled_overlay`, `asset_class_pvt_exposure`, `country_sovereign_rating_band`, `wb_wgi_political_stability`, `capital_controls_watchlist`, `expropriation_history_country`, `terrorism_tria_layer_exposure`, `kidnap_ransom_regional_overlay`, `civil_war_risk_score`, `coup_risk_score`, `election_risk_proximity`, `protest_density_trend`, `ethnic_tension_overlay`, `border_dispute_exposure`, `cybersecurity_attribution_pvt_overlap`.

**Inference package**: `signal_architecture/signals/inference/functions/pvt/` (55+ fns).

**Sources**: ACLED (free), GTD (free), GDELT (free), World Bank WGI, State Dept OSAC, UK FCDO, ICRG (paid, env-gated).

---

### B8 — Tech E&O (standalone, split from PI + Cyber)

**Path**: `coverages/teo/config.yaml`
**Sub-configs (5)**:
`teo_saas`, `teo_managed_service`, `teo_custom_dev`, `teo_hardware`, `teo_sme`.

**New signal IDs (22)**:
`github_org_telemetry`, `builtwith_stack_depth`, `sla_documentation_quality`, `customer_ticker_quality`, `soc2_iso27001_attestation`, `release_cadence_velocity`, `dependency_cve_exposure`, `open_source_license_risk`, `cloud_provider_dependency_band`, `pen_test_disclosure`, `bug_bounty_maturity`, `vendor_risk_program_depth`, `sla_breach_history_proxy`, `customer_concentration_logo_mix`, `pricing_disclosure_transparency`, `ai_feature_disclosure`, `data_residency_commitment`, `gdpr_dpa_maturity`, `api_versioning_maturity`, `sdk_support_matrix`, `developer_ecosystem_breadth`, `open_source_contribution_index`.

**Inference package**: `signal_architecture/signals/inference/functions/teo/` (65+ fns).

**Sources**: GitHub (free), BuiltWith (paid, env-gated), Wappalyzer (OSS), HackerOne / Bugcrowd (public directories), urlscan.io.

---

## Wave 3 (Q4)

### B9 — Reinsurance (Treaty & Fac)

**Path**: `coverages/reinsurance/config.yaml`
**Sub-configs (5)**:
`re_prop_cat`, `re_casualty`, `re_specialty`, `re_retro`, `re_quota_share`.

**Cross-walk**: every direct DSI coverage config emits a cession-friendly summary used by `re_*` configs — a cedent entity's signal profile flows through without re-extraction. Implemented as `signal_architecture/orchestration/cession_aggregator.py`.

**New signal IDs (22)**:
`cedent_composite_dsi_score`, `portfolio_cat_concentration`, `portfolio_line_mix`, `cedent_financial_strength`, `cedent_retention_band`, `cedent_u/w_discipline_history`, `cedent_reserve_adequacy_proxy`, `treaty_wording_maturity`, `contract_certainty_band`, `cedent_claim_handling_quality`, `cedent_technology_maturity`, `reinstatement_terms_coherence`, `sliding_scale_commission_exposure`, `loss_corridor_exposure`, `annual_aggregate_deductible`, `per_risk_xl_pricing_band`, `cat_bond_alternative_capacity_exposure`, `ils_competitor_density`, `retrocession_chain_depth`, `cedent_external_rating_band`, `follow_the_fortunes_clause_maturity`, `loss_development_volatility`.

**Inference package**: `signal_architecture/signals/inference/functions/reinsurance/` (60+ fns).

**Sources**: AM Best (paid, env-gated), SERFF (free), state DOI filings, SEC filings (re insurers), Lloyd's Syndicate returns (free).

---

### B10 — Crop / Parametric Weather

**Path**: `coverages/crop/config.yaml`
**Sub-configs (5)**:
`crop_multi_peril` (MPCI), `crop_hail`, `crop_parametric_weather`, `crop_livestock`, `crop_sme`.

**New signal IDs (22)**:
`usda_rma_sob_historical`, `noaa_drought_monitor`, `noaa_precip_history`, `ecmwf_era5_temperature`, `copernicus_sentinel_ndvi`, `usda_nass_yield_history`, `frost_risk_window_overlay`, `hail_swath_history`, `soil_quality_index`, `irrigation_infrastructure_band`, `commodity_basis_risk`, `grain_elevator_proximity`, `farm_program_participation`, `livestock_density_exposure`, `avian_influenza_proximity`, `foot_and_mouth_proximity`, `parametric_trigger_basis_risk`, `index_insurance_correlation`, `reinsurance_program_exposure`, `agricultural_lender_concentration`, `farm_size_percentile`, `multi_year_yield_volatility`.

**Inference package**: `signal_architecture/signals/inference/functions/crop/` (60+ fns).

**Sources (all free)**: USDA RMA SOB, NASS, NOAA CDO + Drought Monitor, ECMWF ERA5, Copernicus Sentinel, USDA APHIS (livestock disease).

---

### B11 — Specie / Fine Art

**Path**: `coverages/specie/config.yaml`
**Sub-configs (4)**:
`specie_fine_art`, `specie_cash_transit`, `specie_jewellery`, `specie_wine_collect`.

**New signal IDs (20)**:
`auction_provenance_history` (Sotheby's / Christie's public), `interpol_stolen_works_match`, `artist_market_liquidity_band`, `freeport_operator_quality`, `transit_carrier_quality`, `armored_vehicle_fleet_quality`, `storage_facility_security_band`, `humidity_climate_control_cert`, `alarm_certification_band`, `category_market_volatility`, `restoration_history_disclosure`, `authenticity_certification_trail`, `loan_exhibition_exposure`, `auction_house_settlement_risk`, `export_cites_compliance`, `jewellery_grading_lab_quality`, `wine_vintage_authenticity`, `cellar_conditions_proxy`, `cash_in_transit_route_risk`, `cit_crew_vetting_cadence`.

**Inference package**: `signal_architecture/signals/inference/functions/specie/` (50+ fns).

**Sources**: Interpol stolen works (free), auction-house public records, CITES trade database (free), GIA/HRD/IGI (public directories).

---

### B12 — Captive / ART

**Path**: `coverages/captive/config.yaml`
**Sub-configs (4)**:
`captive_single_parent`, `captive_group`, `captive_ric` (risk retention group), `captive_cell`.

**New signal IDs (20)**:
`parent_company_dsi_composite`, `captive_domicile_regulator_quality`, `captive_capitalization_band`, `actuarial_rate_adequacy_proxy`, `fronting_carrier_quality`, `reinsurance_program_depth`, `loss_corridor_funding_band`, `discount_rate_coherence`, `tax_shelter_fidelity`, `irs_section_831b_compliance`, `domicile_regulatory_history`, `captive_manager_quality`, `risk_distribution_band`, `premium_tax_treatment_band`, `accounting_treatment_coherence`, `parent_financial_strength_overlay`, `claims_handling_tpa_quality`, `asset_investment_policy_conservatism`, `solvency_margin_band`, `captive_age_maturity_band`.

**Inference package**: `signal_architecture/signals/inference/functions/captive/` (50+ fns).

**Sources (all free)**: Vermont / Bermuda / Cayman / Guernsey captive registries; SEC filings of parent; state DOI filings.

---

## Acceptance for Workstream B

- 12 new coverages live under `coverages/{name}/config.yaml`, each passing the Maturity Bar.
- `python -m infrastructure.builder.cli calibrate --coverage {name}` PASS for all 12.
- 120 new golden entities (10 per coverage) committed under `tests/fixtures/golden_entities/`.
- `coverages/registry.py` lists all 22 coverages; feature flags removed after Q4 sign-off.
- `docs/overview/Commercial_Entity_Schema.md` updated with any new commercial-term fields required by new coverages (especially reinsurance and captive).
- Cross-walks between `casualty_wc` → `wc_*`, `casualty_environmental` → `env_liab_*`, and `pi`/`cyber` → `teo_*` are live and tested.

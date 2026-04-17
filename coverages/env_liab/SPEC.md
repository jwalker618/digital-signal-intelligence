# B4 — Environmental Impairment (standalone)

## Path
`coverages/env_liab/config.yaml`

## Sub-configs (5)

`env_industrial`, `env_waste_mgmt`, `env_real_estate`,
`env_energy_midstream_xwalk` (cross-walks to `energy_midstream`),
`env_sme`.

## New signal IDs (22)

`epa_echo_violation_depth`, `tri_reportable_volume`, `tri_chemical_mix`,
`superfund_npl_proximity`, `cerclis_site_exposure`,
`state_deq_action_history`, `spill_reporting_cadence`,
`rcra_compliance_band`, `npdes_permit_compliance`, `cercla_pra_band`,
`agency_consent_decree_history`, `brownfield_redevelopment_exposure`,
`air_permit_title_v_compliance`, `pfas_exposure_band`,
`asbestos_lead_mgmt_proxy`, `underground_storage_tank_registry`,
`nrc_material_license`, `mine_safety_mshza_record`,
`environmental_justice_proximity`, `epa_ghg_reporter_band`,
`tsca_inventory_exposure`, `climate_related_disclosure_maturity`.

## Inference package

`signal_architecture/signals/inference/functions/env_liab/` — 65+ fns.

## Sources (all free)

EPA ECHO (already wired — deeper ingestion required), TRI, Superfund
NPL, CERCLIS, state DEQ/DEP, NRC, MSHA. All landed as D3/D5 in Q1-Q2.

## Migration

`casualty_environmental` remains as a cross-walk alias (routing
preserved). Alias deprecation window is Q4 (C4-final).

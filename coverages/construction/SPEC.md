# B5 — Construction / CAR / OCIP

## Path
`coverages/construction/config.yaml`

## Sub-configs (5)

`con_gc` (general contractor), `con_subcontractor`,
`con_infrastructure` (DOT / USACE heavy civil),
`con_energy_xwalk` (cross-walk to energy configs for field construction),
`con_sme`.

## New signal IDs (23)

`enr_top400_benchmark`, `state_contractor_license_board_record`,
`osha_construction_sic_severity`, `dot_project_registry_history`,
`usace_project_portfolio_track_record`, `contractor_fatality_history`,
`scaffolding_fall_protection_exposure`, `wrap_program_experience`,
`bid_backlog_wip_ratio`, `bonding_capacity_band`, `lien_history`,
`change_order_velocity_proxy`, `contractor_workforce_stability`,
`site_safety_training_cadence`, `crane_erection_license_band`,
`demolition_asbestos_handling_cert`, `building_code_ibc_compliance`,
`leed_certification_mix`, `prevailing_wage_compliance`,
`union_density_proxy`, `subcontractor_quality_mix`, `bim_adoption_band`,
`weather_exposure_profile`.

## Inference package
`signal_architecture/signals/inference/functions/construction/` — 65+ fns.

## Sources (free, mostly landed D3/D5/D6)
State contractor licensing boards, OSHA, DOT project registries,
USACE records, USPTO (patents via D4), LEED public, SAM.gov
(federal exclusions).

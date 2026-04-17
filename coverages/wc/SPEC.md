# B2 — Workers' Compensation (standalone)

Copied from `development/project/version/6/workstream_phases/B_New_Coverages.md`.

## Path
`coverages/wc/config.yaml`

## Sub-configs (6)

`wc_construction`, `wc_healthcare`, `wc_manufacturing`, `wc_office`,
`wc_transport`, `wc_sme`.

## Routing constraints

`naics_2digit IN (...)` per sub-config; `wc_sme` on `employee_count < 100`.

## New signal IDs (22)

`osha_establishment_severity`, `osha_citation_velocity`,
`naics_exposure_band`, `dart_rate`, `trir_band`, `emr_proxy`,
`state_wc_board_violation_record`, `class_code_exposure_mix`,
`ergonomic_program_disclosure`, `return_to_work_program_band`,
`cat_body_part_mix`, `dot_auto_overlap`, `hospital_worker_injury_trend`,
`construction_fatality_proximity`, `heat_illness_exposure`,
`manufacturing_cumulative_trauma_score`, `night_shift_exposure_band`,
`safety_training_cadence`, `near_miss_reporting_culture`,
`contractor_intensity`, `immigrant_worker_exposure_band`,
`rural_ambulance_access`.

## Inference package

`signal_architecture/signals/inference/functions/wc/` — 65+ fns.

## Sources (all free, all landed in D3)

OSHA establishment + citations, state WC boards (FL, CA, NY, TX, IL
first), NCCI class code files, NAICS BLS injury statistics.

## Migration

`casualty_wc` sub-config deprecated once B2 ships. A cross-walk alias
keeps existing quotes routing correctly; the alias is removed in
C4-final (Q4).

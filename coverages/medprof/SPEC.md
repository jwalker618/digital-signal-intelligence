# B1 — Medical Professional Liability

Copied from `development/project/version/6/workstream_phases/B_New_Coverages.md`
for convenience.

## Path
`coverages/medprof/config.yaml`

## Sub-configs (5)

| Sub-config | Focus | `routing_constraints` |
|------------|-------|----------------------|
| `medprof_hospital` | Acute-care / teaching hospitals | `employee_count >= 500` |
| `medprof_physician_group` | Multi-specialty groups | `500 > employee_count >= 20` |
| `medprof_nursing_home` | LTC / SNF / assisted living | `facility_type == "ltc"` |
| `medprof_telehealth` | Telehealth / digital-first | `product_type == "telehealth"` |
| `medprof_sme` | Solo + small-group practice | `employee_count < 20` |

## New signal IDs (24)

`cms_star_rating`, `hospital_compare_mortality`, `hospital_compare_readmission`,
`hhs_oig_leie_exposure`, `joint_commission_accreditation`,
`state_medical_board_actions`, `cms_hospital_cost_report_margin`,
`malpractice_claim_density_proxy`, `residency_training_program_quality`,
`credentialing_process_maturity`, `ehr_interoperability_band`,
`hipaa_breach_record`, `cms_adverse_event_reporting`, `specialty_mix_risk`,
`bed_utilisation_band`, `telehealth_platform_quality`,
`cross_state_licensure_compliance`, `npdb_proxy_signal`,
`cms_value_based_payment_participation`, `quality_measure_trend`,
`sentinel_event_disclosure`, `peer_review_process_depth`,
`staffing_ratio_benchmark`, `infection_control_score`.

## Inference package

`signal_architecture/signals/inference/functions/medprof/` — 70+ fns.

## Sources (all free)

CMS Hospital Compare, CMS Cost Reports, HHS OIG LEIE, Joint Commission,
state medical boards, OCR HIPAA Breach Portal (already wired), NPDB
public summary. All available via D3 extractors landed in Q1.

## Golden entities (target 10)

10 public health systems + physician groups.

## Acceptance

- `python -m infrastructure.builder.cli calibrate --coverage medprof`
  returns PASS.
- `assess_config_compliance --config coverages/medprof/config.yaml`
  returns 0 warnings.
- 10 golden entities green.
- Maturity Bar (see `A_Coverage_Maturation.md`) satisfied.

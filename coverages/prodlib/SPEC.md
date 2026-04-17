# B3 — Product Liability / Recall

## Path
`coverages/prodlib/config.yaml`

## Sub-configs (5)

`prodlib_consumer_goods`, `prodlib_medical_device`, `prodlib_auto_parts`,
`prodlib_food_bev`, `prodlib_sme`.

## New signal IDs (24)

`cpsc_recall_history`, `fda_maude_device_adverse_events`,
`fda_recall_history`, `nhtsa_recall_history`, `usda_fsis_recall_history`,
`eu_rapex_notification_history`, `supplier_concentration`,
`manufacturing_country_risk_mix`, `quality_management_certification_band`,
`iso_9001_maturity`, `gmp_cgmp_compliance_proxy`,
`warning_letter_fda_history`, `class_action_density`,
`retailer_distribution_breadth`, `labelling_compliance_track_record`,
`ingredient_source_transparency`, `product_lifecycle_stage`,
`first_generation_product_exposure`, `white_label_dependency`,
`amazon_marketplace_complaint_velocity`, `recall_response_maturity`,
`product_insurance_exposure_breadth`, `r_and_d_investment_trend`,
`patent_litigation_density`.

## Inference package

`signal_architecture/signals/inference/functions/prodlib/` — 70+ fns.

## Sources (all free, all landed in D3)

CPSC, FDA MAUDE + recalls + warning letters, NHTSA, USDA FSIS, EU
Safety Gate (RAPEX), USPTO (patents — lands D4 in Q3).

# DSI Regulatory Artefact Kit (V6/C6)

Eight templates that regulators, insurance departments, and internal
model-risk committees can read. Each file carries:

1. A one-sentence summary.
2. A mapping table from regulatory requirement → DSI artefact / code
   path.
3. Gaps with owner + due date.

Not prose-for-prose's-sake — these are operational documents that must
survive cross-examination.

## Contents

| File | Purpose |
|------|---------|
| `lloyds_model_use_and_governance.md` | Lloyd's MU&G compliance statement |
| `naic_model_risk_management.md` | NAIC MRM alignment (inventory, validation, change control) |
| `fca_fg21_3_algorithmic_pricing.md` | FCA FG21/3 algorithmic-pricing + fairness |
| `gdpr_dpia.md` | Article 35 DPIA template |
| `eu_ai_act_risk_classification.md` | Annex III risk classification |
| `us_state_doi_rate_filing_template.md` | SERFF filing template (IL/CA/TX first) |
| `noaic_data_lineage_statement.md` | Chain-of-custody narrative |
| `fairness_testing_report_template.md` | Disparate-impact test template |

## Review cadence

- Initial internal review each quarter by Compliance.
- External counsel review scheduled separately (tracked in
  `docs/ops/reports/external_counsel.md`).
- CI job verifies every internal link resolves (`docs/check_links.py`,
  added with the regulatory CI gate).

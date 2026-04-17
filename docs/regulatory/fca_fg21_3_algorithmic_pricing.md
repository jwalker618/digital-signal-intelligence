# FCA FG21/3 — Algorithmic Pricing Alignment

**Summary.** DSI aligns with the UK FCA's FG21/3 guidance on
algorithmic pricing, with explicit fairness testing and price-walking
prohibitions built into the config health gate.

## FG21/3 requirement → DSI control

| FG21/3 requirement | DSI control |
|--------------------|-------------|
| No unfair price-walking | Config version history + audit; renewal price derived from same config hash as prior term unless explicit PR |
| Customer-outcome testing | Golden-entity regression covering vulnerable customer segments |
| Fairness testing | `docs/regulatory/fairness_testing_report_template.md` |
| Customer vulnerability | SME / micro configs carry wider guardrails; flagged in sub-config `expectation_level` |
| Governance oversight | MU&G-aligned board-level oversight |
| Data & input transparency | Provenance chain (V6/E2) |
| Pricing-factor documentation | `coverages/<name>/logic.md` + Rate-Filing Kit |

## Gaps

| Gap | Owner | Due |
|-----|-------|-----|
| Six-monthly fairness test report | Compliance | 2026-Q4 |
| Vulnerable customer segmentation mapping | Actuarial | 2026-Q4 |
| Documented renewal pricing policy | UW | 2026-Q3 |

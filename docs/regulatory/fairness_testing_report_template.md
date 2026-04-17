# Disparate-Impact Fairness Testing Template

**Summary.** DSI prices *entities*, not *individuals*. Where an
assessment signal may correlate with protected-class attributes of
natural persons (e.g., board composition, geography), DSI applies the
disparate-impact testing framework documented here.

## Method

1. **Protected-class overlay.** Where a protected-class proxy is
   plausible (geography → ethnicity, industry → gender skew), we
   compute the premium distribution conditional on each overlay value.
2. **Disparate-impact ratio.** Premium(overlay=A) / Premium(overlay=B).
   Ratios outside [0.8, 1.25] trigger a FAIRNESS_FLAGGED referral.
3. **Explanation.** Every flagged quote is annotated with the signal(s)
   driving the disparity. Non-actuarially-justified disparities block
   the quote.

## Quarterly report

| Section | Content |
|---------|---------|
| Entity cohort | Size + industry + geography counts |
| Protected-class overlays evaluated | List + coverage |
| Disparate-impact ratios | Table, per (coverage, overlay, segment) |
| Flagged quotes | Count + referral resolution outcome |
| Signal drivers | Top-N signals explaining flagged cohorts |
| Remediation actions | Config / weight changes made this quarter |

## Cadence

Quarterly. Report stored at
`docs/ops/reports/fairness_report_{YYYY_QX}.md` and reviewed by the
MRM committee.

## Gaps

| Gap | Owner | Due |
|-----|-------|-----|
| Protected-class overlay library | DPO + Legal | 2026-Q4 |
| First quarterly report | Compliance | 2026-Q4 |
| Automated regression when ratio drifts > 5% | Platform + Compliance | 2027-Q1 |

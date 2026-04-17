# EU AI Act — Risk Classification for DSI

**Summary.** DSI is classified as a **high-risk AI system** under the
EU AI Act Annex III (creditworthiness-adjacent decision-making for
financial services). This document enumerates the compliance
obligations that flow from that classification.

## Article 6 classification

DSI processes digital-signal intelligence to produce an insurance
pricing decision. Annex III paragraph 5(b) extends to creditworthiness
and insurance pricing systems. Classification: **HIGH RISK**.

## Article 9+ obligations

| Obligation | DSI control |
|------------|-------------|
| Risk management system | MU&G-aligned governance |
| Data governance | Provenance chain + absence-as-signal |
| Technical documentation | `coverages/<name>/logic.md` + ADR archive |
| Record-keeping | Model version audit table + provenance chain |
| Transparency to users | `logic.md` + customer-facing rationale at quote time |
| Human oversight | Referral queue — every DECLINE / REFER routed to underwriter |
| Accuracy & robustness | Golden-entity regression + calibration harness |
| Cybersecurity | SOC2 Type II controls + External Secrets Operator |
| Quality management system | ISO 9001-aligned change control |

## Gaps

| Gap | Owner | Due |
|-----|-------|-----|
| Notified body engagement | Compliance | 2026-Q4 |
| CE marking submission | Compliance + Legal | 2027-Q1 |
| Post-market monitoring plan | Platform + MRM | 2026-Q4 |
| Incident reporting channel registered with authorities | DPO | 2026-Q3 |

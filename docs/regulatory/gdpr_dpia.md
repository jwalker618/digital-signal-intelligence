# GDPR Article 35 — Data Protection Impact Assessment Template

**Summary.** DSI performs entity-level risk assessments on corporate
entities (not natural persons by default). Where assessments touch
natural-person data (e.g., director-and-officer board lists), DSI
processes only publicly-disclosed information and records the legal
basis on every processing event.

## DPIA template

### 1. Systematic description
DSI ingests public and licensed corporate signals to produce an
insurance-premium assessment for a commercial entity. Data sources are
enumerated in `development/project/version/6/workstream_phases/D_Signal_Sources.md`.

### 2. Necessity & proportionality
Entity-level processing; natural-person data limited to public board
disclosures. Minimum necessary data principle enforced by the signal
registry schema (no PII fields).

### 3. Risk assessment
| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|-----------|
| Director NPI exposure | Low | Medium | Public-record only; provenance chain |
| Cross-border transfer | Medium | Medium | All EU data processed in EU region |
| Profiling | Low (entity, not individual) | Low | No individual profiling |

### 4. Measures
- Encryption at rest + in transit.
- Per-tenant overlays so tenants can exclude specific data classes.
- Retention policy: raw signals purged after 90 days; quotes retained
  10 years (regulatory).

### 5. Consultation
DPO consulted at design time; ongoing quarterly review.

## Gaps

| Gap | Owner | Due |
|-----|-------|-----|
| ROPA entry for every extractor | DPO | 2026-Q3 |
| Board approval log | Legal | 2026-Q4 |

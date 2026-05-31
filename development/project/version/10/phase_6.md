# V10 Phase 6 — Client Portal: Evidence Confidence & Defensible "Why"

**Status:** Planning
**Depends on:** Phase 1 (portal evidence projection + primitives)
**Audience:** client
**Backend precondition:** none beyond Phase 1's `/portal/submissions/{code}/evidence` (curated).

The client portal already shows scores, peers, and an action plan — but it never tells the client *how solid* any of it is. This phase layers evidence confidence over the existing client surfaces, in plain language, with zero adversarial internals.

---

## A. What has been built (backend)
- Phase 1's curated projection: `GET /portal/submissions/{code}/evidence -> PortalEvidenceResponse` (grade, basis, confidence, absence_sub_type, composite rollup — **no** sources/pro/counter/cluster/validator).
- Already-wired client data: `/portal/submissions/{code}/score` (composite, tier, impact breakdown), `/peers` (cohort), `/actions` (remediation), `/profile`.

## A.1 Existing client surfaces to enhance (verified)
```
frontend/src/app/(app)/client/
  drivers/      Risk Insights (signal drivers)
  coverages/    coverage list
  peers/        Industry Benchmarks (bell-curve)
  actions/      Action Plan (remediation)
  scenarios/    what-if
  profile/      entity profile (signal categories observed/pending)
  submissions/[code]/  coverage detail (score, impact, quote history)
```

---

## B. What it augments & why
**Drivers** and **coverages** present findings as fact; **actions** lists remediation; **peers** benchmarks. None convey *evidential strength*. A client told "we rated you down on MFA" reacts very differently when shown "and this is **Inferred** (lowest confidence) — give us an attestation and it becomes **Attested**, improving your score." Evidence confidence is what makes the client portal **fair, trustworthy, and action-driving** rather than an opaque verdict.

The absence sub-type is especially important here: "Couldn't verify" (`absence_failed_fetch`) invites the client to supply data; "Verified clear" (`absence_authoritative_empty`) is reassurance. Collapsing both to "N/A" is a trust failure.

---

## C. Frontend implementation (client)

### C.1 API + types
`lib/portalApi.ts`: `fetchSubmissionEvidence(code)` (Phase 1). Merge its `signals[]` (by `signal_id`/`signal_label`) into the existing drivers/coverages view-models in `types/portal.ts`.

### C.2 Surface-by-surface
- **`client/drivers`**: add an `<EvidenceGradeBadge audience="client">` (label-only) + a one-line `evidence_basis` to each driver row. Add an "evidence strength" filter (e.g. "show low-confidence findings"). Render `<AbsenceTag>` for absent signals.
- **`client/coverages`**: per coverage card, add a `<CompositeGradeRollup composite />` ("how well-evidenced is this assessment") using the curated composite. A single glance: strong vs thin evidence.
- **`client/submissions/[code]`**: in the existing impact-breakdown card, annotate each strength/drag with its grade badge; add an "evidence confidence" `kpi-snug` (the composite weighted-mean grade).
- **`client/peers`**: annotate each signal strength/weakness (already shown via z-scores) with its grade badge — "you're weak here, and the finding is well-evidenced" vs "weak, but only inferred."
- **`client/actions`**: the most important link-up. Each remediation action already shows premium delta + effort; add **current grade → projected grade** ("Inferred → Attested") so the client sees the *evidence* improvement, not just the price. Where an action targets an `absence_failed_fetch` signal, lead with "we couldn't verify this — provide X."
- **`<DecisionSummary code />`** (new, client) — when a submission carries `grade_referral_reasons`/decline, render a plain-language summary built from the curated subset (basis + remediation), **replacing** any need for the raw disclosure packet (which stays carrier/broker-only).

### C.3 Strictly excluded for client
No `evidence_sources`, `evidence_pro/counter/tie_breaker`, `reproducibility`, `primitive_type`, `cluster_id`, validator axes, calibration, mechanisms, commitments. Enforced server-side by Phase 1's projection; the UI simply has nothing to render.

### C.4 Per-audience matrix
| | Client | Broker | Carrier |
|---|---|---|---|
| grade badge (plain) + basis | ✅ | ✅ (Phase 7) | ✅ (Phase 2) |
| composite rollup | ✅ | ✅ | ✅ |
| grade→projected on actions | ✅ | ✅ | ✅ |
| any internal field | ❌ | partial | ✅ |

---

## D. States
- Curated evidence unavailable: degrade silently to the current (pre-V10) view; no broken layout.
- Absent grade: `<AbsenceTag>`, never blank.

## E. Definition of done
- `client/drivers`, `coverages`, `submissions/[code]`, `peers`, `actions` all show plain-language grades + basis sourced from the curated endpoint.
- `actions` shows current→projected grade alongside the existing premium delta.
- `<DecisionSummary>` renders for referred/declined submissions.
- Negative test: client DOM contains no source ids, pro/counter, cluster ids, or validator data.

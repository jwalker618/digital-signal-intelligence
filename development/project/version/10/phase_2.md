# V10 Phase 2 — Evidence Grades in the Carrier Workbench

**Status:** Planning
**Depends on:** Phase 1 (primitives, carrier evidence fetchers)
**Audience:** carrier
**Backend precondition:** none (carrier evidence endpoints are live)

Puts the V7 evidence layer into the surface that needs it most: the underwriter's submission workbench. Every signal gains a grade, and the full argument behind it becomes one click away.

---

## A. What has been built (backend)
Carrier evidence endpoints (auth `assessment:read`), keyed by `model_version_id`:
```
GET /api/v1/model-versions/{mv}/evidence              -> CompositeEvidenceDTO   (composite rollup + per_group + per_primitive + grade_referral_reasons)
GET /api/v1/model-versions/{mv}/signals/{sig}         -> SignalEvidenceDTO      (full: grade, basis, sources[], pro/counter/tie_breaker, absence_sub_type, primitive_type, reproducibility, variant_of, cluster_id)
GET /api/v1/model-versions/{mv}/signals/{sig}/history -> SignalHistoryRowDTO[]  (grade/score over versions)
```
The model version in scope for a submission is already resolved by the carrier workbench (`store/dsiStore.ts` loads `modelversion/{code}/all`); the `mv` id is in hand.

---

## B. What it augments & why
Augments the carrier submission workbench, specifically:
- `frontend/src/app/(app)/carrier/submissions/[code]/risk/page.tsx` — the group/signal breakdown table (score / weight / contribution / coverage). This is the per-signal surface (there is no separate `signals` tab; the breakdown lives here).
- `…/page.tsx` (Summary) — the headline composite + three-pillar block.

Today a signal shows a score and weight but no indication of **how much to trust it**. A `0.8` inferred from one weak proxy and a `0.8` behaviourally validated across three sources are visually identical. Grades + basis + pro/counter/tie-breaker turn the model from a black box into an **auditable argument** — the prerequisite for a defensible underwriting decision (and for the disclosure packet in Phase 5).

---

## C. Frontend implementation (carrier)

### C.1 Data wiring
Extend `store/dsiStore.ts`: on workbench load, fetch `fetchEvidence(mvId)` (composite + per-signal grade map) alongside the existing signal fetch. Lazy-fetch `fetchSignalEvidence(mvId, sigId)` when the drawer opens (the list view only needs grade + absence; the deep fields load on demand).

### C.2 Components (new `frontend/src/components/evidence/` for carrier-rich views)
- **`<EvidenceCell signal />`** — slots into the existing risk breakdown rows: an `<EvidenceGradeBadge audience="carrier">` + an "ⓘ" trigger. Add as a column in the risk table.
- **`<EvidenceDrawer mvId signalId />`** — a side panel (build on `ui/work-area` + `ui/card`) showing, from `SignalEvidenceDTO`:
  - grade badge + `evidence_basis`;
  - **Pro / Counter / Tie-breaker** three-panel;
  - `reproducibility` chip (Phase 3 enriches), `primitive_type` chip, `<ClusterChip cluster_id>` (Phase 9), `variant_of` link;
  - **Sources** list (`evidence_sources`: kind, ref/url, fetched_at, response_hash) — the provenance trail;
  - a "History" mini-tab rendering `…/history` as a `charts/score-history` sparkline of grade over versions.
- **`<ClusterChip cluster_id />`** — filters the table to the cluster (full behaviour in Phase 9; here just the chip).

### C.3 Wiring into surfaces
- **risk page**: add the evidence column + drawer; sort/filter by grade; a "lowest-evidence first" toggle (surfaces the signals worth scrutinising).
- **Summary page**: add `<CompositeGradeRollup composite />` next to the composite score; render `grade_referral_reasons[]` as a callout when present (these are *why the grade triggered a referral*).
- **risk page (full table mode)**: an expanded evidence view within the risk tab (grade, basis, reproducibility, primitive, sources count) for underwriters who want the dense table rather than per-row drawers.

### C.4 Per-audience matrix
| | Client | Broker | Carrier |
|---|---|---|---|
| anything in this phase | ❌ (Phase 6) | ❌ (Phase 7) | ✅ full |

---

## D. States
- `evidence_grade === null`: render `<AbsenceTag>` if `absence_sub_type` set, else muted "ungraded".
- Empty composite (evidence not computed for this version): "Evidence grades unavailable for this model version."
- Drawer load error: inline error in the drawer, table unaffected.

## E. Definition of done
- Carrier risk table shows a grade badge per signal from `/evidence`; drawer opens with basis + pro/counter/tie-breaker + sources + reproducibility + history.
- Summary shows the composite rollup and any `grade_referral_reasons`.
- "Lowest-evidence first" sort works.
- No client/broker surface touched.

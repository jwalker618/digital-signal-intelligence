# V10 Phase 1 — Foundation: Evidence Design Primitives & Portal-Scoped Evidence Access

**Status:** Planning
**Depends on:** nothing (first phase)
**Audience:** all three (foundation)
**Backend precondition (this phase adds it):** a portal-scoped evidence projection endpoint, because the client/broker portals cannot call the carrier-permissioned V7 evidence endpoints.

This phase builds the two things every later phase reuses: (1) the shared evidence UI primitives + grade palette, and (2) the backend projection that lets the client/broker portals receive a *curated* evidence subset. No audience-specific screens yet — this is the spine.

---

## A. What has been built (backend)

### A.1 The taxonomy & grades (carrier-permissioned)
`signal_architecture/signals/evidence.py` — `EvidenceGrade = Literal["inferred","observed","corroborated","structured_attested","behaviourally_validated"]`, 5-rung rank dict, `bump_evidence` (monotonic), `EvidenceSource`.

Carrier endpoints (`infrastructure/api/routes/evidence.py`, auth `assessment:read`):
```
GET /api/v1/model-versions/{mv}/evidence              -> CompositeEvidenceDTO
GET /api/v1/model-versions/{mv}/signals/{sig}         -> SignalEvidenceDTO
GET /api/v1/model-versions/{mv}/signals/{sig}/history -> SignalHistoryRowDTO[]
```
`CompositeEvidenceDTO` (`schemas/evidence.py`): `{ composite:{min_grade, weighted_mean_grade, distribution{}}, per_group{}, per_primitive{}, grade_referral_reasons[] }`.
`SignalEvidenceDTO`: `{ signal_id, score, category, confidence, evidence_grade, evidence_basis, evidence_sources[{source_id,kind,ref,fetched_at,response_hash,notes}], evidence_pro, evidence_counter, evidence_tie_breaker, absence_sub_type, primitive_type, reproducibility, variant_of, cluster_id }`.

### A.2 The gap these don't fill
They are **carrier-only**. The portals work in `submission_code` and authenticate as `portal:client:read` / `portal:broker:read`. There is no portal endpoint that returns evidence. **This phase adds one.**

---

## A′. Backend work in this phase

Add a portal-scoped projection under the existing portal package (`infrastructure/api/routes/portal/`). It resolves `submission_code → latest model_version_id`, calls the same evidence services the carrier route uses, and returns an **audience-curated** subset.

```
GET /api/v1/portal/submissions/{submission_code}/evidence   -> PortalEvidenceResponse
```
- Auth: `portal:client:read` (client sees own; broker sees own-book — reuse `routes/portal/dependencies.py:scoped_submission`).
- `PortalEvidenceResponse` (new `schemas` entry in `routes/portal/schemas.py`):
```jsonc
{
  "submission_code": "SUB-123",
  "coverage": "cyber",
  "composite": { "min_grade":"observed", "weighted_mean_grade":"corroborated",
                 "distribution": {"inferred":2,"observed":5,"corroborated":7,"structured_attested":3,"behaviourally_validated":1} },
  "signals": [
    { "signal_id":"mfa_coverage", "signal_label":"MFA coverage",
      "evidence_grade":"structured_attested",
      "evidence_basis":"Attestation cross-checked against config export",   // plain-language, audience-safe
      "confidence":0.86,
      "absence_sub_type":null,
      "has_provenance":true }    // boolean, NOT the raw sources — see curation rules
  ]
}
```
**Curation rules (enforced server-side, not just hidden in UI):**
- Always include: `evidence_grade`, `evidence_basis`, `confidence`, `absence_sub_type`, composite rollup.
- **Never** include for client: `evidence_sources` (raw provenance), `evidence_pro/counter/tie_breaker`, `reproducibility`, `primitive_type`, `cluster_id`, `variant_of`, validator internals.
- For broker (own client): may include `evidence_sources` summarised + `has_provenance`; still no validator internals.
- Add a `?detail=broker` toggle gated by `portal:broker:read` for the broker superset.

Test: a client JWT gets the curated subset; assert the response JSON contains **no** `evidence_pro`, `cluster_id`, or `evidence_sources` keys (negative test). Mirror the carrier evidence-store fixtures.

---

## B. What it augments & why

Augments **nothing visible yet** — it builds the shared layer. The rationale is leverage: every later phase renders grades. Defining the badge, the palette, the absence semantics, and the portal projection **once** keeps eight downstream surfaces consistent and keeps the FE/BE authorization model in lockstep (the curation is server-enforced, so a UI bug can't leak adversarial internals to a client).

---

## C. Frontend implementation

### C.1 Grade palette (single source of truth)
New `frontend/src/lib/gradePalette.ts` (sits beside `lib/design-tokens.ts` / `lib/portalTone.ts`):
```ts
import type { Tone } from "./portalTone";   // existing tone vocab: pos|neg|spot|info|aux|warn
export const GRADE_ORDER = ["inferred","observed","corroborated","structured_attested","behaviourally_validated"] as const;
export type EvidenceGrade = typeof GRADE_ORDER[number];
export const GRADE_META: Record<EvidenceGrade,{label:string;short:string;tone:Tone;rank:number}> = {
  inferred:                {label:"Inferred",               short:"INF", tone:"neg",  rank:1},
  observed:                {label:"Observed",               short:"OBS", tone:"warn", rank:2},
  corroborated:            {label:"Corroborated",           short:"COR", tone:"info", rank:3},
  structured_attested:     {label:"Attested",               short:"ATT", tone:"pos",  rank:4},
  behaviourally_validated: {label:"Validated",              short:"VAL", tone:"pos",  rank:5},
};
export function gradeRankLabel(g: EvidenceGrade){ return `${GRADE_META[g].rank}/5`; }
```
Mirrors the rank dict in `signal_architecture/signals/evidence.py`. These five strings are the contract — never invent others.

### C.2 Primitives (new files in `frontend/src/components/ui/`)
- **`evidence-grade.tsx` → `<EvidenceGradeBadge grade audience />`** — wraps `ui/chip.tsx` with `GRADE_META[grade].tone`. Carrier/broker show `short` + tooltip `rank/5`; client shows `label` only.
- **`evidence-meter.tsx` → `<EvidenceMeter distribution />`** — a stacked bar (reuse the visual idiom of `ui/score-bar.tsx`) rendering `composite.distribution`; one segment per grade in `GRADE_ORDER`, coloured by tone. Used in summaries.
- **`absence-tag.tsx` → `<AbsenceTag subType />`** — `chip` variant: `absence_failed_fetch` → "Couldn't verify" (warn); `absence_authoritative_empty` → "Verified clear" (info). Never a generic "N/A".
- **`grade-rollup.tsx` → `<CompositeGradeRollup composite />`** — a `kpi-snug`/`label-row` cluster: min grade badge, weighted-mean grade badge, and the `<EvidenceMeter>`.

### C.3 API + types
- `frontend/src/types/portal.ts`: add `EvidenceGrade`, `PortalEvidenceSignal`, `PortalEvidenceResponse` (mirror A′).
- `frontend/src/lib/portalApi.ts`: add `fetchSubmissionEvidence(code)` → `PortalEvidenceResponse`; path via `lib/portalPaths.ts`.
- `frontend/src/lib/api.ts` consumers / `store/dsiStore.ts`: add carrier raw-evidence fetchers `fetchEvidence(mvId)` and `fetchSignalEvidence(mvId, sigId)` (used by Phase 2). Keep these out of the portal store.

### C.4 Per-audience summary
| | Client | Broker | Carrier |
|---|---|---|---|
| data source | `/portal/.../evidence` (curated) | `/portal/.../evidence?detail=broker` | raw `/model-versions/{mv}/...` |
| grade badge style | label only | short+tooltip | short+tooltip |
| internal fields | none (server-stripped) | provenance summary | full |

---

## D. Definition of done
- `/portal/submissions/{code}/evidence` returns the curated subset; negative test confirms no `evidence_pro`/`cluster_id`/`evidence_sources` for a client JWT; broker `detail=broker` adds provenance summary only.
- `gradePalette.ts` + `<EvidenceGradeBadge>`, `<EvidenceMeter>`, `<AbsenceTag>`, `<CompositeGradeRollup>` render for all 5 grades + 2 absence subtypes (visual check).
- `fetchSubmissionEvidence`, `fetchEvidence`, `fetchSignalEvidence` wired and typed; no portal surface imports a carrier-permissioned fetch.
- No regression to existing portal pages.

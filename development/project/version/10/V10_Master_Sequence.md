# Version 10 — Master Sequence: Surfacing the Evidence Engine across Client, Broker & Carrier

**Status:** Planning
**Owner:** Platform / Frontend Engineering
**Predecessors (all merged to `main`):**
- **V7** — the **evidence-grade reasoning engine**: evidence taxonomy + grades, adversarial validator, triple-source calibration, stability/reproducibility, primitive classification, root-cause clusters, variant amplification, mechanism memory, delta re-extraction (SEC/Companies House/OFAC webhooks), disclosure packets, SHA3-224 commitments. **Built end-to-end on the backend with live API endpoints — but consumed by *zero* frontend surfaces.**
- **V8** — the **stakeholder portal**: client + broker portal APIs (`routes/portal/` package), cohort benchmarking (`layers/cohort/`), impact breakdown, remediation, reassessment-with-override.
- **V9** — the **portal frontends themselves** plus the mobile companion (`/m`) and template-fidelity passes. This is where the `client/`, `broker/`, and `carrier/` React surfaces were actually built.

---

## 0. The single most important fact

**The three audiences already have working portals.** Do not "build a client portal" or "build a broker portal" — they exist:

```
frontend/src/app/(app)/
  client/    actions, biz, coverages, drivers, peers, profile, request, scenarios, submissions/[code]
  broker/    aggregation, book-health, carriers, client-health, clients, communications,
             coverages, market, placement, recommendations, scenarios
  carrier/   pipeline, metrics, world-engine,
             submissions/[code]/{summary,terms,premium,distribution,deductible,coverage,sir,
                                 aggregate,pricing,risk,loss,exposure,scenarios,referral,
                                 versions,signals,peers,contacts,history,audit,conditions}
```

These portals already consume the **V8 portal API** (`lib/portalApi.ts`, 23 endpoints): overview, score, peers, actions, communications, queries, broker-intel, etc.

**What none of them surface is the V7 evidence engine.** A signal's *score* is everywhere; its *evidence grade, the argument behind it, the validator's second opinion, its reproducibility, its provenance, the disclosure packet, the reassessment history* — all built, all live on the API, all invisible.

**V10 is the integration layer that surfaces the V7 evidence intelligence into the three existing portals, optimally per audience** — plus the small backend work needed to expose evidence to the client/broker portals safely (they cannot call the carrier-permissioned V7 endpoints directly).

---

## 1. What has been built (capability → endpoint → who can call it → FE today)

"Backend" = built, tested, merged. Auth column matters: V7 endpoints are **carrier** permissions (`assessment:*`); portal endpoints are **portal** permissions (`portal:*`).

| # | Capability | Backend | Live endpoint | Auth | FE today |
|---|---|---|---|---|---|
| 1 | Evidence grade + basis + pro/counter/tie-breaker + sources (per signal) | `signals/evidence.py`, `schemas/evidence.py` | `GET /model-versions/{mv}/signals/{sig}` | `assessment:read` (carrier) | **absent** |
| 2 | Composite/group/primitive grade rollup | `aggregators/grade_rollup.py`, `scorer.py` | `GET /model-versions/{mv}/evidence` | `assessment:read` | **absent** |
| 3 | Signal evidence history (longitudinal) | evidence store | `GET /model-versions/{mv}/signals/{sig}/history` | `assessment:read` | **absent** |
| 4 | Adversarial validator (4-axis) | `validation/`, `schemas/validator.py` | ⚠️ DTO exists; **no GET route yet** | (new) | **absent** |
| 5 | Stability / reproducibility | `signals/stability.py` | inline on SignalEvidenceDTO (`reproducibility`) | `assessment:read` | **absent** |
| 6 | Triple-source calibration | `validation/sampler.py`, `grade_calibration_store.py` | `GET /calibration/pending`, `POST /calibration/decision`, `GET /calibration/stats` | `assessment:refer` | **absent** |
| 7 | Primitive classification (12) | `signals/primitive_classification.py` | inline (`primitive_type`) + `per_primitive` rollup | `assessment:read` | **absent** |
| 8 | Root-cause clusters | `signals/routing/root_cause_cluster.py` | inline (`cluster_id`) + disclosure grouping | `assessment:read` | **absent** |
| 9 | Variant amplification | `variants/` | inline (`variant_of`) | `assessment:read` | **absent** |
| 10 | Mechanism memory + recall | `mechanism/` | `GET /mechanisms`, `GET /model-versions/{mv}/signals/{sig}/mechanisms` | `assessment:read` | **absent** |
| 11 | Delta events + recompute | `recompute/`, `routes/events.py` | `POST /events/external/{src}` (HMAC), `POST /recompute`, `GET /submissions/{sub}/entity-events` | HMAC / `assessment:refer` / `assessment:read` | **absent** |
| 12 | Disclosure packet + commitment | `disclosure/packet.py`, `commitment_store.py` | `POST /model-versions/{mv}/disclosure-packet`, `POST /model-versions/{mv}/verify-commitment` | `assessment:read` | **absent** |
| 13 | Cohort benchmarking | `layers/cohort/` | `GET /portal/submissions/{code}/peers` | `portal:client:read` | **present** (`client/peers`, `bell-curve`) |
| 14 | Impact breakdown | `risk/impact_breakdown.py` | `GET /portal/submissions/{code}/score` | `portal:client:read` | **present** (`client/submissions`) |
| 15 | Remediation plan | `risk/remediation.py` | `GET /portal/submissions/{code}/actions` | `portal:client:read` | **present** (`client/actions`) |
| 16 | Reassessment-with-override | `risk/reassessment.py` | via `POST /portal/.../reply` (`triggered_reassessment`) | `portal:broker:reply` | **trigger only** (no timeline) |

**The pattern:** rows 13–16 (V8) are already wired into the portals. Rows 1–12 (V7) are the unsurfaced backlog. **V10 surfaces rows 1–12.**

---

## 2. The architectural gap: V7 endpoints are carrier-only

The V7 evidence endpoints require `assessment:read` / `assessment:refer` — carrier roles. The **client** (`portal:client:*`) and **broker** (`portal:broker:*`) portals literally cannot call them. So:

- **Carrier** surfaces (Phases 2–5, 8–9) consume the **raw V7 endpoints** directly (keyed by `model_version_id`, via `lib/api.ts` + `store/dsiStore.ts`).
- **Client / broker** surfaces (Phases 6–7) consume **new portal-scoped projection endpoints** that V10 adds under `/portal/...` — these resolve `submission_code → latest model_version_id`, call the evidence services internally, and return a **curated, audience-appropriate subset** (no internal-only fields). This keeps the FE/BE authorization model intact and prevents leaking adversarial internals to outside parties.

Every phase that needs a new portal endpoint declares it in its **§A.backend-precondition**.

---

## 3. Phase map

Each phase doc follows: **(A) What has been built**, **(B) What it augments & why**, **(C) Frontend implementation per audience**.

| Phase | Title | Audience(s) | Headline |
|---|---|---|---|
| **1** | Foundation: evidence design primitives + portal-scoped evidence access | all | `<EvidenceGradeBadge>`/`<EvidenceMeter>`/`<AbsenceTag>`, `GRADE_PALETTE`, new `/portal/.../evidence` projection endpoint, `portalApi`/`api`/types additions |
| **2** | Evidence grades in the carrier workbench | carrier | Grade column + evidence drawer in `carrier/.../risk`, `/signals`, summary |
| **3** | Carrier assurance: validator · stability · calibration · commitments | carrier | Validator panel, stability badges, calibration console, integrity verify |
| **4** | Carrier ops: mechanism memory · delta events · recompute | carrier | Mechanism recall, entity-event feed (`history`/`audit` tabs), manual recompute |
| **5** | Disclosure packet & defensible export | carrier → broker | Packet viewer/download on `referral` tab + commitment digest |
| **6** | Client portal: evidence confidence & defensible "why" | client | Grade confidence on `client/drivers`, `coverages`, `submissions`, `peers`, `actions` |
| **7** | Broker portal: evidence-aware book & client workbench | broker | Grade confidence per client + book-level evidence rollup + broker disclosure |
| **8** | Reassessment timeline (continuous-improvement loop) | all | Before/after diff + timeline on carrier `versions`, broker workbench, client submission |
| **9** | Root-cause clusters & primitive lenses | carrier (full) → client/broker (themes) | Cluster grouping + primitive lens views |
| **10** | Demo, end-to-end walkthrough & cutover | all | Evidence-aware three-audience demo, smoke tests, cutover checklist |

**Execution order:** 1 → 2 → (3,4,5 carrier, independent) → 6 → 7 → 8 → 9 → 10. Phase 1 is a hard prerequisite for all. Phases 6–7 depend on Phase 1's portal-projection endpoint.

---

## 4. Shared frontend conventions (established in Phase 1)

**Design system — reuse the real primitives** (`frontend/src/components/`):
- `ui/`: `card.tsx`, `chip.tsx`, `button.tsx`, `kpi-pill.tsx`, `kpi-snug.tsx`, `kpi-tile.tsx`, `mini-kpi.tsx`, `score-bar.tsx`, `label-row.tsx`, `typography.tsx` (`Eyebrow/Body/Micro/Caption/NumDisplay`), `work-area.tsx`, `loading.tsx`, `divider.tsx`, `icon.tsx`, `avatar.tsx`.
- `charts/`: `bell-curve.tsx`, `cohort-bar.tsx`, `waterfall.tsx`, `score-history.tsx`, `sparkline.tsx`, `subject-marker.tsx`, `premium-breakdown.tsx`.
- `chrome/`: `topbar.tsx`, `persona-sidebar.tsx`, `workbench-shell.tsx`, `carrier-shell.tsx`.
- `shared/`: `PermissionGate.tsx`, `NotificationToast.tsx`, `admin-table.tsx`.
- `base/pageStates.tsx`: loading/error/`RoleGate` empty states.
- **New** evidence primitives live in `components/ui/` (grade badge/meter) so every portal can import them — see Phase 1.

**Tokens / tone:** colours come from `lib/design-tokens.ts` and `lib/portalTone.ts` (existing tone vocabulary: `pos/neg/spot/info/aux/warn`). The 5 grades map onto this vocabulary once, in Phase 1's `GRADE_PALETTE`. Do not introduce a parallel colour set.

**API layer:**
- Carrier raw-V7 calls: extend `lib/api.ts` consumers and `store/dsiStore.ts` (the carrier workbench data store).
- Client/broker portal calls: extend `lib/portalApi.ts` (+ `lib/portalPaths.ts`) and `types/portal.ts`.
- Never call a carrier-permissioned endpoint from a client/broker surface — use the Phase 1 portal projection.

**Persona / permission gating:** persona comes from `store/authStore.ts` (`user.role`) and `navConfig.ts` (`PORTAL_{CLIENT,BROKER,CARRIER}_CHILDREN`). Gate evidence UI with the existing `<PermissionGate>` and `<RoleGate>`; new permissions (e.g. validator read) are added to `types/auth.ts` + backend in the relevant phase.

**States:** every data surface specifies loading / empty / error via `base/pageStates.tsx`. The **absence sub-type distinction** (`absence_failed_fetch` = "couldn't check" vs `absence_authoritative_empty` = "checked, nothing found") must never collapse to a generic "N/A" — it is a first-class evidence concept for all audiences.

---

## 5. Definition of done (whole version)

- A **carrier** sees, for any model version: per-signal grades + basis + pro/counter/tie-breaker + sources; validator verdicts; stability; calibration console; mechanism recall; entity-event feed + manual recompute; disclosure packet export + integrity verify; reassessment timeline; cluster/primitive lenses.
- A **client** sees a plain-language evidence-confidence layer over their existing drivers/coverages/peers/actions, and a read-only improvement timeline — with **no** adversarial internals (no raw pro/counter, no source ids, no validator axes, no cluster ids).
- A **broker** sees, per client and across the book, which findings are solid vs soft, can pull a client's disclosure packet, and can track reassessment outcomes.
- New portal-scoped evidence endpoints exist with negative tests proving a client/broker JWT cannot reach carrier-only data.
- The evidence-aware demo runs end to end across all three audiences (Phase 10).

---

## 6. Accuracy note

This sequence was written against `main` after the V7/V8/V9 merges, and verified directly in the tree: the portal route **package** is `infrastructure/api/routes/portal/` (mounted at `/api/v1/portal`); the V7 routes are `routes/{evidence,disclosure,mechanism,commitments,grade_calibration,events,recompute,entity_events}.py`; the frontend personas are `app/(app)/{client,broker,carrier}`; the design system is `components/{ui,charts,chrome,shared}`; the API layer is `lib/{api,portalApi,portalPaths}.ts` + `store/{authStore,dsiStore}.ts`. Where a capability lacks an endpoint today (notably **validator-verdict GET**, item #4), the consuming phase declares it as a backend precondition.

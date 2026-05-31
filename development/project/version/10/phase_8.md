# V10 Phase 8 — Reassessment Timeline (Continuous-Improvement Loop)

**Status:** Planning
**Depends on:** Phase 1, Phase 6 (client), Phase 7 (broker)
**Audience:** all three
**Backend precondition:** add a **reassessment-diff/history endpoint** (the trigger + lineage exist; a structured before/after view does not).

V8 already *triggers* reassessment (a broker reply with a signal value update re-runs the workflow and produces a new model version). What no surface shows is the **story**: what changed, by how much, and why. This phase closes the loop visually for all three audiences.

---

## A. What has been built (backend)

### A.1 The trigger (live)
`layers/risk/reassessment.py:reassess_with_signal_override` + `merge_direct_query_responses`. Invoked from the broker reply path; a reply carries `signal_value_update`, sets `triggered_reassessment=true`, and yields `new_quote_id` (see `CommunicationThreadMessage` in `schemas`/`types/portal.ts`). A new `ModelVersionRecord` is persisted.

### A.2 What's missing
There is no endpoint that returns a **structured diff** between the prior and new model version, nor a list of reassessment runs. The data exists (model-version lineage + per-signal `signal_history` + quote history) but isn't shaped for a timeline. **Add:**
```
GET /api/v1/portal/submissions/{code}/reassessment-history -> ReassessmentRun[]
GET /api/v1/portal/submissions/{code}/reassessment/{run_id}/diff -> ReassessmentDiff   (or fold diff into the run)
```
`ReassessmentRun`: `{ run_id, triggered_at, triggered_by, trigger_reason, prior_mv_id, new_mv_id, composite_before, composite_after, composite_delta, tier_before, tier_after, decision_before, decision_after, net_premium_delta }`.
`ReassessmentDiff`: `{ improved[], regressed[], new[], dropped[] }` where each entry is `{ signal_id, signal_label, grade_before, grade_after, score_delta }`. Build it by diffing `signal_history` between `prior_mv_id` and `new_mv_id` (deterministic; reuses the evidence store). Curate per audience like Phase 1 (client: no internal fields). Carrier may also use the raw model-version lineage already in `store/dsiStore.ts`.

---

## B. What it augments & why
Augments the **carrier `versions` tab** (`carrier/submissions/[code]/versions`, today a flat lineage), the **broker client workbench**, and the **client submission detail** (today a bare quote-history table). A reassessment is the moment the platform proves it responds to new evidence; showing the before/after is what converts a one-off score into a **relationship of continuous improvement** — the core client-retention and broker-value narrative.

Why per audience: **client** — "you supplied MFA evidence, your score went 685→745, premium −12%" (reinforces Phase 6 actions); **broker** — track which replies moved the needle and by how much; **carrier** — review the diff and decide whether the new version supersedes for binding.

---

## C. Frontend implementation

### C.1 API + types
- Client/broker: `lib/portalApi.ts` `fetchReassessmentHistory(code)`, `fetchReassessmentDiff(code, runId)`. `types/portal.ts`: `ReassessmentRun`, `ReassessmentDiff`.
- Carrier: reuse `store/dsiStore.ts` lineage; add diff fetch if not derivable client-side.

### C.2 Components (new `frontend/src/components/reassessment/`)
- **`<ReassessmentTimeline runs />`** — vertical timeline (reuse the version-history idiom + `charts/score-history`): one node per run with date, `composite_delta` (signed, toned), tier/decision change flags. Click expands the diff.
- **`<ReassessmentDiff diff before after audience />`** — before|after columns (composite via `kpi-tile`, tier via `lib/tier.ts` pill, decision); then collapsible **Improved / Regressed / New / Dropped** lists, each row `grade_before → grade_after` (+ score delta). `net_premium_delta` headline chip. Client audience: simplified (no regressed-internal detail, plain grades).

### C.3 Wiring per audience
- **Carrier** (`versions` tab): timeline at top; when a run changed tier/decision, banner on Summary. (Trigger itself stays in the existing carrier/broker reply flow — no new trigger UI here.)
- **Broker** (client workbench / comms): timeline + per-reply outcome ("your reply moved composite +X"); book view can flag clients with a pending recommended reassessment (remediation supplied but not yet re-run).
- **Client** (`submissions/[code]`): a read-only **"Your progress"** timeline replacing/augmenting the plain quote-history table; no trigger control (a client requests a re-run via the existing communications path).

### C.4 Per-audience matrix
| | Client | Broker | Carrier |
|---|---|---|---|
| timeline (own/book) | ✅ read-only | ✅ | ✅ |
| before/after diff | ✅ simplified | ✅ | ✅ full |
| regressed/dropped detail | summarised | ✅ | ✅ |
| trigger reassessment | request only | ✅ (existing reply) | ✅ (existing) |

---

## D. States
- No reassessments: "No reassessments yet — supply evidence to improve your score."
- In-flight (async re-run): optimistic "running…" node; poll history for the new run.
- Tier/decision changed: highlight node + Summary banner (carrier).

## E. Definition of done
- `reassessment-history` + diff endpoint added + tested (diff is deterministic from `signal_history`).
- Carrier `versions`, broker workbench, client submission all render the timeline; diff expands with grade transitions.
- Client timeline is read-only and contains no internal fields.

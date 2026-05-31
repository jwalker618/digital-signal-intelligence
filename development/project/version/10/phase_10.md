# V10 Phase 10 — Demo, End-to-End Walkthrough & Cutover

**Status:** Planning
**Depends on:** Phases 1–9
**Audience:** all three
**Backend precondition:** none (reuses the V8 demo seed `seed/demo_reset.py`).

The closing phase: prove the evidence engine is now visible and coherent across all three audiences, lock in regression coverage, and cut over.

---

## A. What has been built (backend)
- `seed/demo_reset.py` (V8 Phase 7) — deterministic three-persona demo state, resettable in <5s. The V8 storyboard (client → carrier referral → broker reply → reassessment → premium drop → client visibility) already runs; V10 enriches every act with the now-visible evidence layer.

---

## B. What it augments & why
Augments the **demo narrative** and the **test suite**. V8's demo proved the closed loop; V10's demo proves the loop is now *evidenced* — at every act the audience can see grades, the argument, the validator's view (carrier), the disclosure packet, and the reassessment diff. This is the difference between "the number changed" and "here is exactly why, and how strong the evidence is."

---

## C. Implementation

### C.1 Evidence-aware demo script (extends the V8 storyboard)
| Act | Persona | Surface | V10 addition |
|---|---|---|---|
| 1 | Client | `client/drivers` + `peers` | Each bottom driver now shows its **grade** + plain-language basis; "MFA absent — Couldn't verify" (`absence_failed_fetch`). |
| 2 | Client | `client/actions` | Remediation shows **Inferred → Attested** alongside the £ saving. |
| 3 | Carrier | `carrier/.../risk` + evidence drawer | Underwriter opens the drawer: pro/counter/tie-breaker, **validator** verdict, **stability**, sources, **mechanism recall**. |
| 4 | Carrier | `carrier/.../referral` | Generates the **disclosure packet** (with commitment digest) backing the referral. |
| 5 | Broker | `broker/clients/...` | Broker sees the soft-but-material MFA finding + provenance; replies with MFA evidence. |
| 6 | Carrier | `carrier/.../versions` | **Reassessment timeline**: composite 685→745, tier up, premium −12%, diff shows MFA Inferred→Attested. |
| 7 | Client | `client/submissions/[code]` | "Your progress" timeline shows the improvement and its evidence. |

Reset via the existing `python -m seed demo-reset`.

### C.2 Smoke / E2E tests
- Per-audience render tests: each enhanced page mounts with seeded data and shows the evidence layer (grades present, absence tags correct).
- **Authorization negative tests** (critical): a client JWT and a broker JWT cannot reach any carrier-only V7 endpoint or field; the portal projections strip internal fields (assert at the API and DOM level).
- Determinism: disclosure packet + reassessment diff are byte-stable for fixed seed state.

### C.3 Cutover checklist
- All new portal endpoints (`/portal/.../evidence`, `/disclosure`, `/reassessment-history`, validator-verdict GET) added, tested, and documented in the OpenAPI surface.
- New permissions (validator read, if introduced) seeded into roles + `types/auth.ts`.
- Feature-flag the evidence layer per portal if a staged rollout is wanted (env or config gate read in `navConfig.ts`/page level).
- `pytest tests/ -v` green; frontend typecheck + build green.
- Mobile (`/m`) parity check: decide whether the evidence layer surfaces in the mobile feed (recommend: grade badge on the signal hero + movers only; full evidence stays desktop — track as V10.1 if deferred).

### C.4 Per-audience definition of done
| | Client | Broker | Carrier |
|---|---|---|---|
| evidence visible end-to-end | ✅ plain | ✅ +provenance/disclosure | ✅ full incl. validator/calibration/mechanism |
| reassessment loop visible | ✅ | ✅ | ✅ |
| no internal leakage | ✅ (tested) | ✅ (tested) | n/a |

---

## D. Definition of done (version close)
- The evidence-aware demo runs all seven acts across three personas from a single reset.
- Authorization negative tests pass for client + broker.
- Determinism tests pass for packet + diff.
- Cutover checklist complete; suite + build green.

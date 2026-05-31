# V10 Phase 5 — Disclosure Packet & Defensible Export

**Status:** Planning
**Depends on:** Phase 1, Phase 2 (evidence), Phase 3 (commitment)
**Audience:** carrier (primary) → broker (own client's packet)
**Backend precondition:** add a **portal-scoped disclosure endpoint** for broker access (carrier endpoint is live).

A disclosure packet is the deterministic, defensible artefact a carrier produces when a decision is challenged: every grade-driven referral reason, grouped by root cause, with pro/counter/tie-breaker per finding, evidence sources, recalled mechanisms, and a SHA3-224 commitment digest. This phase makes it viewable and downloadable.

---

## A. What has been built (backend)

### A.1 Generator + endpoint (carrier, live)
`signal_architecture/disclosure/packet.py` (`build_packet`, `PacketSection`, deterministic Jinja2 → Markdown + canonical JSON). Cached on `referrals.disclosure_packet` when a grade referral fires.
```
POST /api/v1/model-versions/{mv}/disclosure-packet?format=json   -> DisclosureResponse { markdown, payload }   (auth assessment:read)
POST /api/v1/model-versions/{mv}/disclosure-packet?format=md     -> text/markdown
```
`payload`: `{ generated_at, model_version_id, composite_min_grade, composite_distribution{}, referral_reasons[], sections:[ { title, signal_id, grade, pro, counter, tie_breaker, sources[], cluster_symptoms[], recalled_mechanisms[], commitment_digest, reproducibility } ] }`.

### A.2 What's missing for the broker
The broker portal (`portal:broker:read`) can't call the carrier endpoint. **Add:**
```
GET /api/v1/portal/submissions/{code}/disclosure   -> DisclosureResponse   (portal:broker:read, own-book via scoped_submission)
```
Resolve `code → latest mv`, call `build_packet`, return the same structure (brokers may see the full packet for their own client — they are the client's representative). **Client: excluded** (gets a plain-language decision summary instead — Phase 6).

---

## B. What it augments & why
Augments the carrier `referral` tab (`carrier/submissions/[code]/referral`), which today lists referral reasons + an override modal but produces nothing exportable. And the broker `communications`/client workbench, where a broker explains/appeals a decision.

Why: **carrier** — regulatory/dispute defensibility in one click, with an integrity digest; **broker** — pull the packet to explain a decline/refer to their client or support an appeal; **client** — the adversarial pro/counter framing is internal, so clients get the derived plain-language summary, not the raw packet.

---

## C. Frontend implementation

### C.1 API + types
- Carrier: `lib/api.ts` `fetchDisclosurePacket(mvId)` (+ a `format=md` URL builder for download).
- Broker: `lib/portalApi.ts` `fetchSubmissionDisclosure(code)`.
- `types/portal.ts`: `DisclosurePacket`, `PacketSection`.

### C.2 Components (new `frontend/src/components/disclosure/`)
- **`<DisclosurePacketViewer packet />`** — render the **structured `payload`** (not a raw markdown dump) in the design system: header (model version, `generated_at`, `composite_min_grade`, **commitment digest** with copy), then one `<PacketSectionCard>` per `sections[]` grouped by `cluster_symptoms` — title, grade badge, pro/counter/tie-breaker columns, sources, recalled mechanisms, reproducibility.
- **Download actions** — "Download .md" (link to `?format=md`) and "Download .json" (blob of `payload`). Filename `disclosure-{mv}.md`.
- **`<IntegrityDigest value />`** — short SHA3-224 with copy (shared with Phase 3).

### C.3 Wiring per audience
- **Carrier** (`referral` tab): a "Disclosure packet" section with the viewer + downloads, shown whenever a referral exists; also surface per-version on the `versions` tab.
- **Broker** (`broker/clients/.../comms` or client workbench): a "Get disclosure packet" action for the active submission (own client; server-scoped).
- **Client**: **no raw packet** — Phase 6 renders a `<DecisionSummary>` from the public subset.

### C.4 Per-audience matrix
| | Client | Broker | Carrier |
|---|---|---|---|
| raw packet viewer | ❌ | ✅ (own client) | ✅ |
| .md / .json download | ❌ | ✅ | ✅ |
| commitment digest | ❌ | ✅ | ✅ |
| plain-language summary | ✅ (Phase 6) | ✅ | ✅ |

---

## D. States
- No referral / no packet: "No disclosure packet — this version did not trigger a referral."
- Cached vs fresh: show `generated_at`; carrier "regenerate" re-POSTs.
- Large packet: virtualise the section list.

## E. Definition of done
- Carrier `referral` tab renders `<DisclosurePacketViewer>` from `payload`; .md + .json downloads work; digest shown + copyable.
- `/portal/submissions/{code}/disclosure` added + tested; broker pulls own-client packet; cross-client attempt 404s.
- Negative test: client shell exposes no pro/counter strings.

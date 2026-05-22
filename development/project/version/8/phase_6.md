# Version 8 Phase 6: Portal API Surface

## Overview

Consolidate the services from Phases 2–5 into a coherent **portal API** mounted under `/api/v1/portal/*`. Apply role-based access control (`BROKER` vs `CLIENT`) and ensure brokers only see their own clients, clients only see themselves.

This phase adds **no new business logic**. It is pure plumbing: route definitions, request/response schemas, permission decorators, broker–client scoping logic.

## Rationale

Phases 2–5 each built backend services but deliberately did **not** expose endpoints. This was intentional — exposing endpoints piecemeal would have led to inconsistent auth, scoping, and shape per phase. Phase 6 consolidates them under one router with one set of conventions.

The frontend (Phase 8) calls only `/api/v1/portal/*` endpoints. The carrier UI continues to call existing endpoints. Two surfaces, one backend.

## Decisions (locked, do not relitigate)

| Decision | Choice | Implication |
|-|-|-|
| Route prefix | `/api/v1/portal` | Clear separation from carrier API |
| Auth pattern | Same FastAPI dependency the existing API uses, but routes also enforce role + scope | No new auth machinery |
| Broker scoping | Broker can access entities where `entity.broker_id == user.broker_id` | Single FK check; rejected at dependency level |
| Client scoping | Client can access only their own entity — entity belongs to the same tenant as the user | Tenant-based scoping for clients |
| Pagination | Cursor-based via `?cursor=` param on list endpoints | Consistent with any existing list patterns; confirm |
| Endpoint shape | RESTful, plural collection paths | Standard |
| No business logic in routes | Routes call into Phase 2–5 services; no per-route reshaping | Keeps routes thin |

## Current State

- Phases 1–5 complete.
- `infrastructure/api/routes/` contains the existing route modules.
- `infrastructure/api/main.py` mounts routers.
- Authentication dependency (likely `get_current_user`) exists; confirm exact name during discovery.
- No portal routes exist yet.

## Target State

### Module layout

```
infrastructure/api/routes/portal/
    __init__.py
    overview.py         # GET /portal/overview (role-aware)
    score.py            # GET /portal/entities/{id}/score
    peers.py            # GET /portal/entities/{id}/peers
    actions.py          # GET /portal/entities/{id}/actions
    submissions.py      # GET/POST /portal/entities/{id}/submissions
    queries.py          # GET /portal/queries (broker inbox)
    dependencies.py     # role + scope dependency functions
```

### Dependency: scope-checking

```python
# infrastructure/api/routes/portal/dependencies.py

async def require_portal_user(current_user: User = Depends(get_current_user)) -> User:
    """User must have BROKER or CLIENT role."""
    if current_user.role not in (Role.BROKER, Role.CLIENT):
        raise HTTPException(403, "Portal access requires BROKER or CLIENT role")
    return current_user

async def scoped_entity(
    entity_id: int,
    current_user: User = Depends(require_portal_user),
    session: Session = Depends(get_session),
) -> Entity:
    """Resolve entity and assert the user is allowed to see it."""
    entity = session.get(Entity, entity_id)
    if entity is None:
        raise HTTPException(404, "Entity not found")
    if current_user.role == Role.BROKER:
        if entity.broker_id != current_user.broker_id:
            raise HTTPException(403, "Entity not in your book")
    elif current_user.role == Role.CLIENT:
        if entity.tenant_id != current_user.tenant_id:
            raise HTTPException(403, "Entity not in your tenant")
    return entity
```

Every portal endpoint that operates on a specific entity uses `Depends(scoped_entity)`.

### Endpoints

#### `GET /api/v1/portal/overview`

Role-aware overview.

**Broker response** (`role == BROKER`):
```json
{
  "role": "BROKER",
  "broker": {"id": 1, "name": "Marsh", "slug": "marsh"},
  "clients": [
    {
      "entity_id": 101,
      "entity_name": "Acme Industries",
      "coverage_line": "cyber",
      "latest_quote": {
        "quote_id": 88,
        "composite_score": 745,
        "tier": 2,
        "percentile_rank": 73.4,
        "premium_usd": 124000,
        "renewal_date": "2026-09-15"
      },
      "open_queries_count": 1
    }
  ]
}
```

**Client response** (`role == CLIENT`):
```json
{
  "role": "CLIENT",
  "entity": {
    "entity_id": 101,
    "entity_name": "Acme Industries",
    "broker": {"id": 1, "name": "Marsh"}
  },
  "active_coverages": [
    {
      "coverage_line": "cyber",
      "latest_quote_id": 88,
      "composite_score": 745,
      "tier": 2,
      "percentile_rank": 73.4,
      "premium_usd": 124000
    }
  ],
  "open_queries_count": 0
}
```

#### `GET /api/v1/portal/entities/{entity_id}/score`

Returns the impact breakdown from Phase 3 plus headline numbers.

```json
{
  "entity_id": 101,
  "quote_id": 88,
  "coverage_line": "cyber",
  "composite_score": 745,
  "tier": 2,
  "base_premium": 145000,
  "final_premium": 124000,
  "impact_breakdown": { /* full ImpactBreakdown from Phase 3 */ }
}
```

Query param `coverage_line` optional — defaults to the entity's most-recently-assessed coverage.

#### `GET /api/v1/portal/entities/{entity_id}/peers`

Returns cohort stats and signal strengths/weaknesses from Phase 2.

```json
{
  "entity_id": 101,
  "quote_id": 88,
  "cohort_id": "cyber:51:50-250M",
  "cohort_size": 64,
  "percentile_rank": 73.4,
  "cohort_mean_score": 711,
  "cohort_median_score": 718,
  "entity_score": 745,
  "signal_ranking": { /* SignalRanking from Phase 2 */ }
}
```

If cohort_size < 10, response includes `"percentile_rank": null` and a `"note": "Insufficient peers"`.

#### `GET /api/v1/portal/entities/{entity_id}/actions`

Returns the remediation plan from Phase 4.

```json
{
  "entity_id": 101,
  "quote_id": 88,
  "remediation_plan": { /* full RemediationPlan from Phase 4 */ }
}
```

#### `GET /api/v1/portal/entities/{entity_id}/submissions`

List of submissions for the entity, with status and linked referrals.

```json
{
  "entity_id": 101,
  "submissions": [
    {
      "submission_id": 200,
      "coverage_line": "cyber",
      "status": "READY",
      "created_at": "2026-05-10T09:23:00Z",
      "quote_id": 88,
      "referral": {
        "referral_id": 17,
        "state": "AWAITING_BROKER",
        "awaiting_party": "broker",
        "open_query": {
          "message_id": 42,
          "body": "Please confirm MFA status...",
          "request_signal_evidence": "mfa_enabled",
          "created_at": "2026-05-15T11:00:00Z"
        }
      }
    }
  ]
}
```

#### `POST /api/v1/portal/entities/{entity_id}/submissions`

Initiate a renewal/new submission. **Requires `portal:client:submit`** (client only).

**Request:**
```json
{
  "coverage_line": "cyber",
  "renewal_of_submission_id": 199  // optional
}
```

**Behaviour:** thin wrapper over the existing `POST /api/v1/submissions` endpoint, with the entity_id pre-filled from the URL and tenant/broker context inherited from the user.

**Response:**
```json
{
  "submission_id": 201,
  "status": "PROCESSING"
}
```

#### `GET /api/v1/portal/queries`

Broker inbox. Lists open queries (referrals in `AWAITING_BROKER` state) across all of the broker's clients.

**Permissions**: `portal:broker:read`.

```json
{
  "broker": {"id": 1, "name": "Marsh"},
  "open_queries": [
    {
      "referral_id": 17,
      "entity_id": 101,
      "entity_name": "Acme Industries",
      "coverage_line": "cyber",
      "submission_id": 200,
      "quote_id": 88,
      "open_query": {
        "message_id": 42,
        "body": "Please confirm MFA status...",
        "request_signal_evidence": "mfa_enabled",
        "created_at": "2026-05-15T11:00:00Z"
      },
      "client_score": 685,
      "client_tier": 4
    }
  ]
}
```

Sorted by query age desc (oldest first — the broker should clear stale queries).

#### `POST /api/v1/portal/queries/{referral_id}/reply`

Convenience alias for Phase 5's `POST /api/v1/referrals/{referral_id}/messages/reply`. Same payload, same behaviour, but mounted under `/portal/*` for clean broker-side URL structure. Internally delegates to the Phase 5 handler.

This is the only "alias" endpoint in the portal surface — every other endpoint is genuinely new in Phase 6.

### Response schemas

All response shapes defined as Pydantic models in `infrastructure/api/routes/portal/schemas.py`. Models reuse Phase 2/3/4/5 Pydantic models where possible (import, don't redefine).

### Mounted in main.py

```python
# infrastructure/api/main.py
from infrastructure.api.routes.portal import router as portal_router
app.include_router(portal_router, prefix="/api/v1/portal", tags=["portal"])
```

Single new include. Phase 5's referral_messages router stays where it is — both surfaces coexist.

## Implementation Plan

### Step 1: Discovery

Confirm:
1. Exact name of the auth dependency (`get_current_user` or similar).
2. Where `Session` dependency comes from.
3. Existing submission creation endpoint signature (`POST /api/v1/submissions` per recon).
4. Whether existing endpoints already enforce tenant scoping at dependency level — Phase 6 should align with that pattern.

### Step 2: Create the portal package

Create `infrastructure/api/routes/portal/` with `__init__.py` exporting the consolidated `router: APIRouter`.

### Step 3: Dependencies

Implement `require_portal_user` and `scoped_entity` in `dependencies.py`.

### Step 4: Endpoint implementations

One file per endpoint group:

- `overview.py` — role-aware overview. Calls into helpers that resolve the broker's book or the client's coverages.
- `score.py` — fetch latest quote for entity, return its impact_breakdown.
- `peers.py` — fetch cohort stats via `layers/cohort/service.py`.
- `actions.py` — invoke `build_remediation_plan` from Phase 4.
- `submissions.py` — list + create (create delegates to existing submission endpoint logic).
- `queries.py` — broker inbox; reply alias to Phase 5.

Each file is a thin route module — under 100 lines. If a route exceeds that, it's doing too much. Push logic into the Phase 2–5 services.

### Step 5: Schemas

`schemas.py` with Pydantic models for each response shape. Import from Phase 2 (`CohortStats`, `SignalRanking`), Phase 3 (`ImpactBreakdown`), Phase 4 (`RemediationPlan`), Phase 5 (`ReferralMessage`). Compose into the response envelopes shown above.

### Step 6: Mount

Add the include line in `infrastructure/api/main.py`.

### Step 7: Tests

`tests/api/test_portal.py`:

**Scope tests:**
- Broker accessing entity in their book: 200.
- Broker accessing entity in someone else's book: 403.
- Client accessing their own entity: 200.
- Client accessing another tenant's entity: 403.
- User without BROKER or CLIENT role hitting any `/portal/*` endpoint: 403.

**Overview tests:**
- Broker `/overview`: returns clients list, includes `latest_quote` summary, `open_queries_count` accurate.
- Client `/overview`: returns own entity, active coverages.

**Score / peers / actions tests:**
- All three return Phase 2/3/4 data correctly shaped.
- Peers returns `null` percentile for cohort < 10.

**Submissions tests:**
- List returns expected shape.
- Create (as CLIENT) creates a submission.
- Create (as BROKER) rejected — `portal:client:submit` not held by broker.

**Queries tests:**
- Broker `/queries`: lists open queries for their clients only.
- Broker `/queries/{id}/reply`: delegates correctly, behaves identically to Phase 5 endpoint.

### Step 8: OpenAPI sanity check

Generate the OpenAPI schema (FastAPI's `/docs` route). Manually inspect: every `/portal/*` endpoint appears with correct request/response shapes, tagged `portal`. Confirm no schema collision with carrier endpoints.

## Constraints & Principles

1. **No business logic in routes.** Routes call into Phase 2–5 services. If a route has more than ~20 lines of logic, refactor into a service.
2. **Permission + scope at the dependency level.** Every entity-scoped route uses `Depends(scoped_entity)`. No per-route ad hoc scope checks.
3. **Reuse Pydantic models.** Phase 2/3/4/5 models are imported, not redefined.
4. **Carrier API untouched.** No changes to existing routes. Two surfaces, one backend.
5. **Single mount in main.py.** One include line for the portal router. Phase 5's referral_messages stays where it is.
6. **No new persistence.** Phase 6 reads from data populated by Phases 1–5.
7. **Cursor pagination** if any list grows large — for v8 demo data, lists are <100 items; pagination can be deferred but design the contract for it.

## Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| Existing carrier endpoints implicitly assume tenant scoping that breaks for portal users | Discovery confirms; if portal users need cross-tenant or scoped-differently logic, dependencies handle it before route is hit. |
| Submission create endpoint requires fields the portal can't reasonably provide | Submission create through portal is a thin wrapper — confirm minimum required fields during discovery; if extras needed, the Pydantic request model documents defaults. |
| Broker inbox query expensive across all clients | Index on `referrals.awaiting_party` (Phase 5 migration) + index on `entities.broker_id` (Phase 1) — both already in place. Query is fast. |
| Multiple coverage lines per entity confuse the score/peers/actions endpoints | Each endpoint accepts optional `coverage_line` query param; defaults to most-recently-assessed. Documented in OpenAPI. |
| Permission decorator drift between routes | Tests assert 403 for every route given a user with wrong role. Centralised dependencies prevent per-route drift. |

## Dependencies

- **Phases 1–5 complete.** Phase 6 consumes services from each.

## Success Criteria

1. `infrastructure/api/routes/portal/` package exists with the seven module files plus `dependencies.py` and `schemas.py`.
2. Eight endpoints live and tested:
   - `GET /portal/overview`
   - `GET /portal/entities/{id}/score`
   - `GET /portal/entities/{id}/peers`
   - `GET /portal/entities/{id}/actions`
   - `GET /portal/entities/{id}/submissions`
   - `POST /portal/entities/{id}/submissions`
   - `GET /portal/queries`
   - `POST /portal/queries/{id}/reply`
3. Scope enforced at dependency level for every entity-scoped route.
4. Broker can only see entities in their book; client can only see their tenant's entity.
5. Step 7 tests pass.
6. OpenAPI shows all eight endpoints under `portal` tag with correct schemas.
7. Carrier API endpoints unchanged.
8. Router mounted in `main.py` (single new include).
9. Full `pytest tests/ -v` green.
10. No frontend, no seed, no schema changes.

## Out of Scope (Phase 6)

- Frontend consumption — Phase 8.
- Seeding broker / client demo users — Phase 7.
- Multi-broker per entity — single broker assumption from Phase 1.
- API rate limiting — v8.1.
- WebSocket events for live updates — v8.1.
- Webhook subscriptions for external integrations — v8.1.
- Analytics on portal usage — v8.1.

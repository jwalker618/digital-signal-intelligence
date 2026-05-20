# Version 8 Phase 1: Data Model & Roles

## Overview

Add the foundational data shapes that every subsequent v8 phase depends on: a `Broker` model, a `broker_id` foreign key on `Entity`, and two new roles — `BROKER` and `CLIENT` — on the existing role enum, with their associated permission strings.

This is a **schema-only** phase. No endpoints, no UI, no logic that consumes the new shapes. Phase 1's job is to make the data model truthful so Phases 2–8 can build on stable ground.

## Rationale

The v7 codebase models only carrier-side users (`ADMIN`, `ACTUARIAL`, `SENIOR_UNDERWRITER`, `UNDERWRITER`, `READ_ONLY`). Brokers and clients are absent from the data model entirely. v8 cannot function without a first-class concept of "Broker" (Marsh) and "Client" (the insured), and the schema must permit a broker to be associated with many clients.

Per the v8 planning decision ("Real model" over "Demo shortcut"), we model brokers properly so the change survives past the Marsh demo into v8.1+.

## Decisions (locked, do not relitigate)

| Decision | Choice | Implication |
|-|-|-|
| Broker as separate table or tenant flag | Separate table | Survives multi-broker support; clean joins |
| Broker–Entity relationship | One broker per entity (FK on Entity, nullable) | Single-broker assumption; schema permits multi-broker via join table in future without rework |
| Client identity | A `User` with role `CLIENT`, scoped to a `Tenant` that represents the insured | Reuses existing tenant/user machinery; no new "Client" table |
| BROKER/CLIENT permissions | Separate permission strings, prefixed `portal:` | Keeps portal permissions distinct from underwriter permissions |
| `broker_id` nullability | NULL allowed | Existing entities pre-v8 have no broker; backfill is Phase 7's job |
| Frontend types | Update `frontend/src/types/auth.ts` role enum | Single-line type addition; not "frontend work" — it's a type contract update |

## Current State

### Existing files

- `infrastructure/db/models.py` — defines `Tenant`, `User`, `Role`, `Entity` and their relationships. **Confirm exact field names during implementation** — paths in this doc are illustrative.
- `infrastructure/db/migrations/` — Alembic migrations directory. **Confirm latest migration number** at the start of implementation; the new migration is `latest + 1`.
- `frontend/src/types/auth.ts` — TypeScript role enum mirror of the backend.
- `infrastructure/api/auth/` (or wherever permission strings are defined) — list of `portal:*`-style permission strings.

### Existing roles (per recon)

```
ADMIN
ACTUARIAL
SENIOR_UNDERWRITER
UNDERWRITER
READ_ONLY
```

### Existing permissions (per recon, illustrative — confirm in implementation)

```
assessment:read, assessment:write, assessment:refer
entity:read, entity:write
config:read, config:write, config:deploy
recalibration:view, recalibration:approve
portfolio:view, portfolio:simulate
world_engine:view
admin:system, admin:users, admin:audit
```

## Target State

### Data model additions

```python
# infrastructure/db/models.py

class Broker(Base):
    __tablename__ = "brokers"

    id: Mapped[int] = mapped_column(primary_key=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)  # e.g. "marsh"
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, nullable=False)

    tenant: Mapped["Tenant"] = relationship(back_populates="brokers")
    entities: Mapped[list["Entity"]] = relationship(back_populates="broker")

class Tenant(Base):
    # ... existing fields ...
    brokers: Mapped[list["Broker"]] = relationship(back_populates="tenant")

class Entity(Base):
    # ... existing fields ...
    broker_id: Mapped[int | None] = mapped_column(ForeignKey("brokers.id"), nullable=True, index=True)
    broker: Mapped["Broker | None"] = relationship(back_populates="entities")
```

**Why is `Broker` tenant-scoped?** Multi-tenancy is the existing isolation boundary. A broker belongs to one tenant. If the demo tenant `dsi-demo` contains Marsh as a broker, that broker can be linked to client entities that also live within `dsi-demo`. This keeps the existing tenant-scoping contract intact.

**Why nullable `broker_id` on Entity?** Existing entities have no broker. Backfill is Phase 7's job for demo entities; legacy entities stay null.

### Role enum additions

In whatever module declares roles (likely `infrastructure/db/models.py` or `infrastructure/api/auth/`):

```python
class Role(str, Enum):
    # ... existing values ...
    BROKER = "BROKER"
    CLIENT = "CLIENT"
```

### Permission strings

Add to the canonical permission string list:

```
portal:broker:read           # Broker can view their book of clients
portal:broker:reply          # Broker can reply to underwriter queries
portal:client:read           # Client can view their own score, peers, actions
portal:client:submit         # Client can initiate a renewal/submission
```

Wiring rules:

- Role `BROKER` is granted: `portal:broker:read`, `portal:broker:reply`, `portal:client:read` (a broker can see the client's view of their clients).
- Role `CLIENT` is granted: `portal:client:read`, `portal:client:submit`.
- No existing roles get the new `portal:*` permissions.

### TypeScript role enum

```ts
// frontend/src/types/auth.ts
export enum Role {
  // ... existing values ...
  BROKER = "BROKER",
  CLIENT = "CLIENT",
}
```

Single-line addition mirroring backend. No other frontend changes in this phase.

### Migration

Alembic migration number = current latest + 1.

**Up migration:**
1. Create `brokers` table with the columns above.
2. Add `broker_id` column to `entities` (nullable, FK to `brokers.id`, indexed).
3. If the role enum is a database enum type, add `BROKER` and `CLIENT` values. If it's a string column with check constraint, update the constraint. **Confirm the existing pattern** before writing the migration.
4. Insert no seed data — Phase 7 owns seeding.

**Down migration:**
1. Drop `broker_id` from `entities`.
2. Drop `brokers` table.
3. Revert the enum/constraint changes (or accept that PostgreSQL enum value removal requires a more careful path — document in the migration if so).

## Implementation Plan

### Step 1: Discovery (confirm before writing code)

Open and confirm:
1. `infrastructure/db/models.py` — exact class names for `Tenant`, `User`, `Role`, `Entity`. Confirm role storage (enum vs string column).
2. `infrastructure/db/migrations/versions/` — find latest migration number.
3. Where permission strings live. Confirm naming convention (`:` separated as recon suggests).
4. `frontend/src/types/auth.ts` — confirm `Role` enum location.

Document the confirmed paths inline in the migration file's docstring so it serves as the discovery record.

### Step 2: Add `Broker` model and `Entity.broker_id`

- Add the `Broker` SQLAlchemy model and back-references as shown.
- Add `broker_id` FK and `broker` relationship to `Entity`.
- No business logic. No service methods. Pure schema.

### Step 3: Add roles and permissions

- Add `BROKER` and `CLIENT` to the role enum.
- Add the four `portal:*` permission strings to the canonical list.
- Wire role → permissions mapping per the **Permission strings** section.

### Step 4: Migration

- Generate the Alembic migration. Manually verify it does only what it should — no spurious autogenerated drops or alters.
- Test `alembic upgrade head` then `alembic downgrade -1` cleanly on a local DB.

### Step 5: Frontend type mirror

- Add `BROKER` and `CLIENT` to `frontend/src/types/auth.ts` `Role` enum.
- No other frontend changes.

### Step 6: Tests

- `tests/db/test_models.py` (or wherever model tests live):
  - Create a `Broker`, assert it persists, assert `broker.tenant` and `broker.entities` relationships work.
  - Create an `Entity` with `broker_id=None`, assert it persists.
  - Create an `Entity` with `broker_id=<broker.id>`, assert it persists and `entity.broker` loads.
  - Assert `broker.slug` is unique (insert duplicate, assert IntegrityError).
- `tests/auth/test_roles.py` (or equivalent):
  - Assert `Role.BROKER` and `Role.CLIENT` exist.
  - Assert `BROKER` has `portal:broker:read`, `portal:broker:reply`, `portal:client:read`.
  - Assert `CLIENT` has `portal:client:read`, `portal:client:submit`.
  - Assert no existing role has any `portal:*` permission.
- Migration smoke test if one exists in the suite — add the v8 migration to it.

## Constraints & Principles

1. **No business logic in this phase.** Models, migration, role/permission registration only. Anyone reviewing this phase should see only schema work.
2. **Backward compatibility.** All existing models, migrations, tests, and API surfaces continue to function unchanged. `broker_id` is nullable for this reason.
3. **No multi-broker rework debt.** The current schema allows extending to many-to-many later via a join table without altering `Broker` or `Entity`. Do not add a join table in this phase — YAGNI.
4. **Permission strings are namespaced.** `portal:*` is the v8 namespace. Do not collide with existing strings.
5. **TypeScript enum stays in sync.** If the backend role enum changes, `frontend/src/types/auth.ts` updates in the same commit. No drift.

## Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| Postgres enum values cannot be removed in a down migration without complex workarounds | If the role storage is a Postgres enum, document the limitation in the down migration and accept it (most projects do). If a string + check constraint, no issue. |
| Permission wiring missed for one of the new permissions | Tests assert every new permission is bound to at least one role. |
| `broker_id` index missing causing slow lookups in Phase 2+ | Migration creates the index. Verified by `\d entities` showing the index. |
| `frontend/src/types/auth.ts` lives in a different conventional path | Discovery step 1 confirms. |
| Existing test fixtures break because they construct entities without `broker_id` | `broker_id` is nullable — no fixture changes required. |

## Dependencies

- v7 main branch is the working base.
- No dependency on v7 Phase 1 (Evidence Grade) — v8 Phase 1 touches different tables and fields.

## Success Criteria

1. `Broker` model present in `infrastructure/db/models.py` with `id`, `tenant_id`, `name`, `slug`, `created_at`.
2. `Entity.broker_id` nullable FK exists with index.
3. `Tenant.brokers` and `Broker.entities` relationships work bidirectionally in tests.
4. `Role.BROKER` and `Role.CLIENT` defined and usable.
5. Four `portal:*` permission strings defined.
6. `BROKER` role maps to `portal:broker:read`, `portal:broker:reply`, `portal:client:read`. `CLIENT` role maps to `portal:client:read`, `portal:client:submit`. No existing role gets `portal:*`.
7. Migration applies cleanly with `alembic upgrade head`, rolls back cleanly with `alembic downgrade -1`.
8. `frontend/src/types/auth.ts` `Role` enum has `BROKER` and `CLIENT`.
9. Full `pytest tests/ -v` passes.
10. No endpoints, no API logic, no UI changes (beyond the one type enum line) introduced.

## Out of Scope (Phase 1)

- Endpoints that filter by `broker_id` (Phase 6).
- Permission-checking middleware that gates routes by `portal:*` (Phase 6).
- Seeding any actual Marsh broker or client tenant (Phase 7).
- Frontend role-based redirect after login (Phase 8).
- Re-assigning existing entities to brokers (Phase 7 for demo data; manual otherwise).

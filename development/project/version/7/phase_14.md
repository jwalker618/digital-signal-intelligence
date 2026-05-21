# V7 Phase 14: API + Server-Side Disclosure Packets (Backend Only)

> **Frontend deferred**: every `frontend/**` change lives in Phase 15.
> This phase touches **no** frontend file. Safe to land while parallel UI work continues.

## Depends on
- Phases 1–13 complete. Every previous phase has landed its data — this phase exposes it via HTTP.

## Blocks
- Phase 15 (frontend consumes everything this phase ships).

## Scope

Backend-only exposure layer:

1. **API DTOs** — Pydantic models for every V7 field added in Phases 1–13. Existing endpoints' response models extended; new endpoints added for evidence, calibration, mechanism, entity events, commitment verification, manual recompute, and disclosure packet generation.
2. **Server-side disclosure packet generator** — Jinja-templated Markdown + structured JSON. Returned by the disclosure endpoint and (optionally) cached into `referrals.disclosure_packet`.
3. **Commitment verification endpoint** — accepts a candidate payload, returns whether its SHA3-224 matches a stored commitment.

Visual encoding decisions (which chip, which colour, which axis) all live in Phase 15.

## Decisions (locked)

| # | Decision | Choice |
|---|----------|--------|
| D1 | DTO style | Pydantic v2 `BaseModel`. Re-uses the `EvidenceGradeName` / `ReproducibilityClass` literals from previous phases |
| D2 | Endpoint shape | `/api/v1/model-versions/{mv_id}/evidence` returns composite + per-group + per-primitive in one payload. Per-signal detail is a separate endpoint to keep the composite payload small |
| D3 | Pagination | History endpoint is paginated (default 50, max 200). Composite endpoint is single-shot |
| D4 | Disclosure formats | `format=json` (default): `{markdown, payload}` JSON. `format=md`: `text/markdown` body. No other formats |
| D5 | Disclosure determinism | Same model_version_id + same backing rows → byte-identical Markdown + identical JSON payload (after sorting keys) |
| D6 | Disclosure persistence | When a grade-driven referral fires, the workflow stores the generated payload's JSON into a new `referrals.disclosure_packet` JSONB column (Alembic `029`). Subsequent GET requests prefer the stored payload |
| D7 | Commitment verify | Round-trips through `infrastructure/db/commitment_store.verify`. Returns `{ok, digest_computed}` so the caller can debug mismatches |
| D8 | Auth | Re-uses existing `current_user` dependency. Tenant scoping enforced on every read |
| D9 | Backward compat | Existing `ModelVersionDTO` and similar gain new fields as `Optional` — no caller breaks |
| D10 | No frontend changes | Hard rule for this phase. Phase 15 consumes |

## Files

### Create
- `alembic/versions/029_disclosure_packet.py`
- `infrastructure/api/schemas/evidence.py`
- `infrastructure/api/schemas/validator.py`
- `infrastructure/api/schemas/calibration.py`
- `infrastructure/api/schemas/mechanism.py`
- `infrastructure/api/schemas/disclosure.py`
- `infrastructure/api/routes/evidence.py`
- `infrastructure/api/routes/disclosure.py`
- `infrastructure/api/routes/mechanism.py`
- `infrastructure/api/routes/entity_events.py`
- `infrastructure/api/routes/commitments.py`
- `signal_architecture/disclosure/__init__.py`
- `signal_architecture/disclosure/packet.py`
- `signal_architecture/disclosure/templates.py`
- `tests/api/test_evidence_endpoints.py`
- `tests/api/test_disclosure_endpoint.py`
- `tests/api/test_commitments_endpoint.py`
- `tests/api/test_mechanism_endpoint.py`

### Modify
- `infrastructure/db/models.py` — `referrals.disclosure_packet` column (mirrored at ORM level)
- `infrastructure/api/types.py` — extend existing `ModelVersionDTO` / `SignalAuditRecordDTO` with V7 fields as `Optional`
- `infrastructure/api/main.py` — register the new routers
- `layers/risk/workflow.py` — when a grade referral fires, generate and persist the packet payload into `referrals.disclosure_packet`

### Explicitly NOT modified
- Anything under `frontend/`
- `frontend/src/types/dsi.ts`

## API DTOs

`infrastructure/api/schemas/evidence.py`:

```python
"""V7 Phase 14 — evidence Pydantic DTOs.

Each DTO maps to the ORM rows added in Phases 5/6/7/8/9.
"""
from __future__ import annotations

from datetime import datetime
from typing import List, Literal, Optional

from pydantic import BaseModel, Field

EvidenceGradeName = Literal[
    "inferred", "observed", "corroborated", "structured_attested", "behaviourally_validated",
]
ReproducibilityClass = Literal["stable", "flaky", "unstable", "unknown"]


class EvidenceSourceDTO(BaseModel):
    source_id: str
    kind: str
    ref: str
    fetched_at: datetime
    response_hash: Optional[str] = None
    notes: str = ""


class SignalEvidenceDTO(BaseModel):
    signal_id: str
    score: Optional[float] = None
    category: Optional[str] = None
    confidence: float
    evidence_grade: Optional[EvidenceGradeName] = None
    evidence_basis: Optional[str] = None
    evidence_sources: List[EvidenceSourceDTO] = Field(default_factory=list)
    evidence_pro: Optional[str] = None
    evidence_counter: Optional[str] = None
    evidence_tie_breaker: Optional[str] = None
    absence_sub_type: Optional[str] = None
    primitive_type: Optional[str] = None
    reproducibility: Optional[ReproducibilityClass] = None
    variant_of: Optional[str] = None
    cluster_id: Optional[str] = None


class GradeRollupDTO(BaseModel):
    min_grade: Optional[EvidenceGradeName] = None
    weighted_mean_grade: Optional[float] = None
    distribution: dict[EvidenceGradeName, float] = Field(default_factory=dict)


class CompositeEvidenceDTO(BaseModel):
    composite: GradeRollupDTO
    per_group: dict[str, GradeRollupDTO] = Field(default_factory=dict)
    per_primitive: dict[str, GradeRollupDTO] = Field(default_factory=dict)
    grade_referral_reasons: list[str] = Field(default_factory=list)


class SignalHistoryRowDTO(BaseModel):
    model_version_id: str
    recorded_at: datetime
    evidence_grade: Optional[EvidenceGradeName] = None
    score: Optional[float] = None
    category: Optional[str] = None
    evidence_basis: Optional[str] = None
```

`infrastructure/api/schemas/validator.py`:

```python
from __future__ import annotations
from datetime import datetime
from typing import Literal, Optional
from pydantic import BaseModel, Field

Axis = Literal["MATERIAL", "CORRECT_ENTITY", "OPERATIONALLY_PLAUSIBLE", "GENERALISES_AT_RENEWAL"]


class AxisResultDTO(BaseModel):
    axis: Axis
    passed: bool
    confidence: Literal["high", "medium", "low"]
    rationale: str


class ValidatorVerdictDTO(BaseModel):
    signal_id: str
    mode: Literal["quick_pass", "full_pass"]
    advance: bool
    grade_before: Optional[str] = None
    grade_after: Optional[str] = None
    axes: dict[Axis, AxisResultDTO] = Field(default_factory=dict)
    pro_argument: str
    counter_argument: str
    tie_breaker: str
    elapsed_seconds: Optional[float] = None
    decided_at: datetime
```

`infrastructure/api/schemas/calibration.py`:

```python
from __future__ import annotations
import uuid
from datetime import datetime
from typing import Literal, Optional
from pydantic import BaseModel, Field


class CalibrationSampleDTO(BaseModel):
    id: uuid.UUID
    submission_id: uuid.UUID
    coverage: str
    signal_id: str
    signal_weight: float
    extractor_grade: str
    validator_grade: Optional[str] = None
    sampling_reason: Literal["high_weight_referred", "stratified_random"]
    created_at: datetime
    expires_at: datetime
    state: Literal["pending", "decided", "expired"]


class CalibrationDecisionIn(BaseModel):
    sample_id: uuid.UUID
    human_grade: Literal["inferred", "observed", "corroborated", "structured_attested", "behaviourally_validated"]
    note: str = ""


class CalibrationStatsDTO(BaseModel):
    window_days: Optional[int] = None
    decided: int
    exact_match_extractor_rate: float
    exact_match_validator_rate: Optional[float] = None
    within_one_extractor_rate: float
```

`infrastructure/api/schemas/mechanism.py`:

```python
from __future__ import annotations
from pydantic import BaseModel, Field


class MechanismDTO(BaseModel):
    id: str
    summary: str
    primitive_type: str
    sector_tags: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    what_made_it_high_grade: str = ""
    recall_count: int = 0
```

`infrastructure/api/schemas/disclosure.py`:

```python
from __future__ import annotations
from typing import Any
from pydantic import BaseModel


class DisclosureResponse(BaseModel):
    markdown: str
    payload: dict[str, Any]
```

## Routes

`infrastructure/api/routes/evidence.py`:

```python
"""V7 Phase 14 — evidence read endpoints."""
from __future__ import annotations

import uuid
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query

from infrastructure.api.utils import current_user, get_db
from infrastructure.api.schemas.evidence import (
    CompositeEvidenceDTO, GradeRollupDTO,
    SignalEvidenceDTO, SignalHistoryRowDTO,
)

router = APIRouter(prefix="/api/v1/model-versions", tags=["evidence"])


@router.get("/{model_version_id}/evidence", response_model=CompositeEvidenceDTO)
def get_composite_evidence(model_version_id: uuid.UUID, db=Depends(get_db), user=Depends(current_user)):
    mv = _load_mv_or_404(db, model_version_id, user.tenant_id)
    return CompositeEvidenceDTO(
        composite=GradeRollupDTO(
            min_grade=mv.composite_min_grade,
            weighted_mean_grade=(float(mv.composite_weighted_mean_grade)
                                 if mv.composite_weighted_mean_grade is not None else None),
            distribution=mv.composite_grade_distribution or {},
        ),
        per_group=_load_group_rollups(db, model_version_id),
        per_primitive=_load_primitive_rollups(db, model_version_id),
        grade_referral_reasons=_load_grade_referral_reasons(db, model_version_id),
    )


@router.get("/{model_version_id}/signals/{signal_id}", response_model=SignalEvidenceDTO)
def get_signal_evidence(model_version_id: uuid.UUID, signal_id: str,
                        db=Depends(get_db), user=Depends(current_user)):
    row = _load_signal_or_404(db, model_version_id, signal_id, user.tenant_id)
    return SignalEvidenceDTO(
        signal_id=row.signal_id,
        score=row.score, category=row.category, confidence=row.confidence,
        evidence_grade=row.evidence_grade, evidence_basis=row.evidence_basis,
        evidence_sources=row.evidence_sources or [],
        evidence_pro=row.evidence_pro, evidence_counter=row.evidence_counter,
        evidence_tie_breaker=row.evidence_tie_breaker,
        absence_sub_type=row.absence_sub_type, primitive_type=row.primitive_type,
        variant_of=row.variant_of, cluster_id=(row.metadata or {}).get("cluster_id"),
    )


@router.get("/{model_version_id}/signals/{signal_id}/history",
            response_model=List[SignalHistoryRowDTO])
def get_signal_history(
    model_version_id: uuid.UUID, signal_id: str,
    limit: int = Query(default=50, ge=1, le=200),
    db=Depends(get_db), user=Depends(current_user),
):
    submission_id = _resolve_submission(db, model_version_id, user.tenant_id)
    rows = _load_signal_history(db, submission_id, signal_id, limit=limit)
    return [
        SignalHistoryRowDTO(
            model_version_id=str(r.model_version_id),
            recorded_at=r.recorded_at,
            evidence_grade=r.evidence_grade,
            score=r.score, category=r.category,
            evidence_basis=r.evidence_basis,
        )
        for r in rows
    ]
```

`infrastructure/api/routes/disclosure.py`:

```python
"""V7 Phase 14 — disclosure packet endpoint."""
from __future__ import annotations

import uuid
from fastapi import APIRouter, Depends, Response
from fastapi.responses import JSONResponse

from infrastructure.api.utils import current_user, get_db
from infrastructure.api.schemas.disclosure import DisclosureResponse
from signal_architecture.disclosure.packet import build_packet

router = APIRouter(prefix="/api/v1/model-versions", tags=["disclosure"])


@router.post("/{mv_id}/disclosure-packet")
def generate_packet(
    mv_id: uuid.UUID, format: str = "json",
    db=Depends(get_db), user=Depends(current_user),
):
    # Prefer the cached packet from referrals.disclosure_packet if present
    cached = _load_cached_packet(db, mv_id, user.tenant_id)
    if cached is None:
        sections = _build_sections(db, mv_id, user.tenant_id)
        md, payload = build_packet(
            model_version_id=mv_id,
            composite_min_grade=_load_min_grade(db, mv_id),
            composite_distribution=_load_distribution(db, mv_id),
            referral_reasons=_load_grade_referral_reasons(db, mv_id),
            sections=sections,
        )
    else:
        md = cached["markdown"]
        payload = cached["payload"]

    if format == "md":
        return Response(content=md, media_type="text/markdown")
    return JSONResponse(content=DisclosureResponse(markdown=md, payload=payload).model_dump())
```

`infrastructure/api/routes/mechanism.py`:

```python
"""V7 Phase 14 — mechanism inspection endpoints."""
from __future__ import annotations

import uuid
from typing import List

from fastapi import APIRouter, Depends, Query

from infrastructure.api.utils import current_user, get_db
from infrastructure.api.schemas.mechanism import MechanismDTO
from signal_architecture.mechanism.store import load_all
from signal_architecture.mechanism.recall import recall

router = APIRouter(prefix="/api/v1", tags=["mechanism"])


@router.get("/mechanisms", response_model=List[MechanismDTO])
def list_mechanisms(
    primitive_type: str | None = None,
    coverage: str | None = None,
    limit: int = Query(default=50, ge=1, le=200),
    db=Depends(get_db), user=Depends(current_user),
):
    rows = load_all(str(user.tenant_id))
    if primitive_type:
        rows = [m for m in rows if m.primitive_type == primitive_type]
    if coverage:
        rows = [m for m in rows if coverage in m.sector_tags]
    rows = rows[:limit]
    return [MechanismDTO(**{
        "id": m.id, "summary": m.summary, "primitive_type": m.primitive_type,
        "sector_tags": m.sector_tags, "tags": m.tags,
        "what_made_it_high_grade": m.what_made_it_high_grade,
        "recall_count": m.recall_count,
    }) for m in rows]


@router.get("/model-versions/{mv_id}/signals/{signal_id}/mechanisms",
            response_model=List[MechanismDTO])
def mechanisms_for_signal(
    mv_id: uuid.UUID, signal_id: str,
    db=Depends(get_db), user=Depends(current_user),
):
    sig = _load_signal_or_404(db, mv_id, signal_id, user.tenant_id)
    coverage = _coverage_for_mv(db, mv_id)
    return [
        MechanismDTO(
            id=m.id, summary=m.summary, primitive_type=m.primitive_type,
            sector_tags=m.sector_tags, tags=m.tags,
            what_made_it_high_grade=m.what_made_it_high_grade,
            recall_count=m.recall_count,
        )
        for m in recall(
            tenant_id=str(user.tenant_id),
            primitive_type=sig.primitive_type or "unknown",
            coverage=coverage,
            query_text=(sig.evidence_basis or ""),
            top_k=3,
        )
    ]
```

`infrastructure/api/routes/entity_events.py`:

```python
"""V7 Phase 14 — read endpoint for entity events (Phase 13 stores them)."""
from __future__ import annotations

import uuid
from typing import List

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from datetime import datetime

from infrastructure.api.utils import current_user, get_db

router = APIRouter(prefix="/api/v1/submissions", tags=["events"])


class EntityEventDTO(BaseModel):
    id: uuid.UUID
    event_type: str
    source_feed: str
    received_at: datetime
    dispatched_at: datetime | None
    blast_radius: list[str]
    resulting_model_version_id: uuid.UUID | None
    payload: dict


@router.get("/{submission_id}/entity-events", response_model=List[EntityEventDTO])
def list_events(
    submission_id: uuid.UUID,
    limit: int = Query(default=50, ge=1, le=200),
    db=Depends(get_db), user=Depends(current_user),
):
    rows = _load_events_for_submission(db, submission_id, user.tenant_id, limit)
    return [EntityEventDTO(
        id=r.id, event_type=r.event_type, source_feed=r.source_feed,
        received_at=r.received_at, dispatched_at=r.dispatched_at,
        blast_radius=r.blast_radius or [],
        resulting_model_version_id=r.resulting_model_version_id,
        payload=r.payload or {},
    ) for r in rows]
```

`infrastructure/api/routes/commitments.py`:

```python
"""V7 Phase 14 — commitment verification endpoint."""
from __future__ import annotations

import uuid
from typing import Optional, Any
from fastapi import APIRouter, Depends
from pydantic import BaseModel

from infrastructure.api.utils import current_user, get_db
from infrastructure.db.commitment_store import verify, sha3_224

router = APIRouter(prefix="/api/v1/model-versions", tags=["commitments"])


class VerifyIn(BaseModel):
    signal_id: Optional[str] = None
    scope: str
    candidate_payload: dict[str, Any]


class VerifyOut(BaseModel):
    ok: bool
    digest_computed: str


@router.post("/{mv_id}/verify-commitment", response_model=VerifyOut)
def verify_commitment(mv_id: uuid.UUID, body: VerifyIn,
                      db=Depends(get_db), user=Depends(current_user)):
    ok = verify(
        db, model_version_id=mv_id, signal_id=body.signal_id,
        scope=body.scope, candidate_payload=body.candidate_payload,
    )
    return VerifyOut(ok=ok, digest_computed=sha3_224(body.candidate_payload))
```

## Disclosure packet generator

`signal_architecture/disclosure/packet.py`:

```python
"""V7 Phase 14 — generate a templated underwriter disclosure packet.

Bundles signal + grade + pro/counter/tie-breaker + sources + commitment
digest + cluster symptoms + recalled mechanisms.

Determinism (D5): same backing rows → byte-identical Markdown + same JSON
payload (after canonical-key sorting).
"""
from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from jinja2 import Environment, BaseLoader

from .templates import MARKDOWN_TEMPLATE

_env = Environment(loader=BaseLoader(), autoescape=False, trim_blocks=True, lstrip_blocks=True)


@dataclass
class PacketSection:
    title: str
    signal_id: str
    grade: str
    grade_referral_reasons: list[str]
    pro: str
    counter: str
    tie_breaker: str
    sources: list[dict] = field(default_factory=list)
    cluster_symptoms: list[dict] = field(default_factory=list)
    recalled_mechanisms: list[dict] = field(default_factory=list)
    commitment_digest: str = ""
    reproducibility: str | None = None


def build_packet(
    *,
    model_version_id: uuid.UUID,
    composite_min_grade: str | None,
    composite_distribution: dict[str, float],
    referral_reasons: list[str],
    sections: list[PacketSection],
    generated_at: datetime | None = None,
) -> tuple[str, dict[str, Any]]:
    generated_at = generated_at or datetime.now(timezone.utc)
    payload: dict[str, Any] = {
        "generated_at": generated_at.isoformat(),
        "model_version_id": str(model_version_id),
        "composite_min_grade": composite_min_grade,
        "composite_distribution": composite_distribution,
        "referral_reasons": referral_reasons,
        "sections": [s.__dict__ for s in sections],
    }
    md = _env.from_string(MARKDOWN_TEMPLATE).render(p=payload)
    # Canonical JSON serialisation for determinism
    return md, json.loads(json.dumps(payload, sort_keys=True, default=str))
```

`signal_architecture/disclosure/templates.py`:

```python
MARKDOWN_TEMPLATE = """\
# Referral Disclosure Packet

**Generated**: {{ p.generated_at }}
**Model version**: `{{ p.model_version_id }}`
**Composite min grade**: `{{ p.composite_min_grade or "n/a" }}`

## Grade distribution
{% for g, w in p.composite_distribution.items() -%}
- {{ g }}: {{ (w * 100) | round(0) }}%
{% endfor %}

## Referral reasons
{% for r in p.referral_reasons -%}
- {{ r }}
{% endfor %}

---

{% for s in p.sections %}
## {{ s.title }}

- **Signal**: `{{ s.signal_id }}`
- **Grade**: `{{ s.grade }}`
- **Reproducibility**: `{{ s.reproducibility or "unknown" }}`
- **Commitment**: `{{ s.commitment_digest }}`

### Pro
{{ s.pro }}

### Counter
{{ s.counter }}

### Tie-breaker
{{ s.tie_breaker }}

### Sources
{% for src in s.sources -%}
- `{{ src.kind }}` · `{{ src.source_id }}` · {{ src.ref }} ({{ src.fetched_at }})
{% endfor %}

### Cluster symptoms
{% for sym in s.cluster_symptoms[:5] -%}
- `{{ sym | tojson }}`
{% endfor %}

### Recalled mechanisms
{% for m in s.recalled_mechanisms -%}
- {{ m.summary }}  ({{ m.tags | join(", ") }})
{% endfor %}

---
{% endfor %}
"""
```

## Migration `029`

```python
"""V7 Phase 14 — referrals.disclosure_packet column for cached packets.

Revision ID: 029
Revises: 028
"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision = "029"
down_revision = "028"


def upgrade():
    op.add_column("referrals", sa.Column("disclosure_packet", JSONB, nullable=True))


def downgrade():
    op.drop_column("referrals", "disclosure_packet")
```

## Workflow integration

`layers/risk/workflow.py` extension — at the point where a `Referral` row is created in response to a grade-driven `TriggeredCondition`:

```python
from signal_architecture.disclosure.packet import build_packet, PacketSection

def _generate_disclosure_for_referral(self, db, referral, mv_id, sections):
    md, payload = build_packet(
        model_version_id=mv_id,
        composite_min_grade=...,
        composite_distribution=...,
        referral_reasons=...,
        sections=sections,
    )
    referral.disclosure_packet = {"markdown": md, "payload": payload}
```

## Steps

### 14.1 — Migration
**File**: `alembic/versions/029_disclosure_packet.py`.
**Action**: Apply + round-trip.

### 14.2 — Pydantic schemas
**Files**: `infrastructure/api/schemas/{evidence,validator,calibration,mechanism,disclosure}.py`.
**Action**: Drop in code. Type-check.

### 14.3 — Routes
**Files**: `infrastructure/api/routes/{evidence,disclosure,mechanism,entity_events,commitments}.py`.
**Action**: Implement endpoints. Register in `infrastructure/api/main.py`.

### 14.4 — Disclosure packet generator
**Files**: `signal_architecture/disclosure/{packet,templates}.py`.
**Action**: Drop in code. Verify determinism: build twice with identical inputs → identical output.

### 14.5 — Wire cached packet into workflow
**File**: `layers/risk/workflow.py`.
**Action**: On grade-driven referral, persist packet into `referrals.disclosure_packet`. Read path in disclosure route prefers the cached payload.

### 14.6 — Extend existing DTOs additively
**File**: `infrastructure/api/types.py`.
**Action**: Add optional V7 fields to existing `ModelVersionDTO` / `SignalAuditRecordDTO` / referral DTOs. All `Optional` — existing consumers unaffected.

### 14.7 — Tests
**Files**:
- `tests/api/test_evidence_endpoints.py` — DTO shape matches ORM; auth required; tenant scoping; pagination.
- `tests/api/test_disclosure_endpoint.py` — determinism (build twice → identical), Markdown contains every required section, cached path returns the stored payload, `format=md` returns `text/markdown`.
- `tests/api/test_commitments_endpoint.py` — round-trip: build packet → commit → POST candidate → `ok=True`; tampered candidate → `ok=False`.
- `tests/api/test_mechanism_endpoint.py` — tenant scoping, filters by primitive_type and coverage.

## Test gates

```bash
alembic upgrade head
alembic downgrade -1
alembic upgrade head

pytest tests/api/test_evidence_endpoints.py \
        tests/api/test_disclosure_endpoint.py \
        tests/api/test_commitments_endpoint.py \
        tests/api/test_mechanism_endpoint.py -v

pytest tests/ -x -q

# Determinism smoke
python -c "
from signal_architecture.disclosure.packet import build_packet, PacketSection
import uuid, datetime
md1, p1 = build_packet(
    model_version_id=uuid.UUID(int=1),
    composite_min_grade='observed',
    composite_distribution={'observed': 1.0},
    referral_reasons=[],
    sections=[],
    generated_at=datetime.datetime(2026, 1, 1, tzinfo=datetime.timezone.utc),
)
md2, p2 = build_packet(
    model_version_id=uuid.UUID(int=1),
    composite_min_grade='observed',
    composite_distribution={'observed': 1.0},
    referral_reasons=[],
    sections=[],
    generated_at=datetime.datetime(2026, 1, 1, tzinfo=datetime.timezone.utc),
)
assert md1 == md2 and p1 == p2
print('disclosure deterministic ✓')
"

# Belt-and-braces: confirm no frontend file changed
git diff --name-only HEAD~1 HEAD | grep -E '^frontend/' && echo 'ERROR: frontend touched in Phase 14' && exit 1 || echo 'frontend untouched ✓'
```

## Done when

- [ ] Every V7 field reachable through a Pydantic DTO and an endpoint.
- [ ] Composite evidence endpoint returns composite + per-group + per-primitive in one payload.
- [ ] Disclosure packet generator is deterministic for identical inputs.
- [ ] Cached packet stored in `referrals.disclosure_packet` when a grade referral fires.
- [ ] Commitment verification endpoint round-trips correctly.
- [ ] All tests green.
- [ ] No file under `frontend/` modified by this phase's commits.

## Out of scope

- Any `frontend/**` change. → Phase 15.
- Visual encoding decisions (badge colours, chip styling, weighted-mean placement). → Phase 15.
- Bulk export of disclosure packets across portfolio. → V8.

## Invariants

1. No frontend file is touched by this phase.
2. Disclosure packet generation is deterministic.
3. All new DTO fields are `Optional` on existing endpoints — backward compatible.
4. Tenant scoping enforced on every read.

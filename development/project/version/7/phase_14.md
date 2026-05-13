# V7 Phase 14: API + Frontend + Disclosure Packets

## Depends on
- Phases 1–13 complete. Every previous phase has landed its data — this phase exposes it.

## Blocks
- Nothing in V7. V8 work depends on V7 phase 14 endpoints existing.

## Scope

Three workstreams, single phase because they share consumers:

1. **API exposure** — Pydantic DTOs for every new field. Endpoints for: grade rollup browsing, validator verdicts, calibration queue, mechanism inspection, entity event history, commitment verification, manual recompute, disclosure packet generation.
2. **Workbench UI** — new tabs and panels in `frontend/src/components/submissions/Workbench/`: Evidence column on the signal ledger, composite grade panel, primitive-rollup heatmap, validator pro/counter card, calibration queue, mechanism memory drawer.
3. **Disclosure packets** — server-side generation of a referral packet bundling: signal + grade + pro/counter/tie-breaker + sources + commitment digest + cluster symptoms + recalled mechanisms. Outputs Markdown + JSON. Drives the existing `referrals` table.

Visual discipline: grade and confidence are rendered as **distinct** indicators (different shapes, different positions). Reproducibility class is a third chip. The UI must communicate that these are three independent axes, not three views of the same number.

## Decisions (locked)

| # | Decision | Choice |
|---|----------|--------|
| D1 | Grade visual | Coloured badge: `inferred`=grey, `observed`=blue, `corroborated`=teal, `structured_attested`=green, `behaviourally_validated`=emerald. Label always shown |
| D2 | Confidence visual | Continuous 0–100% bar. **Never** the same colour ramp as grade |
| D3 | Reproducibility visual | Pill chip: `stable`=outline-green, `flaky`=outline-amber, `unstable`=outline-red, `unknown`=outline-grey |
| D4 | Composite panel | Composite min-grade prominently displayed; distribution bar showing weight share per grade; weighted-mean grade rendered in small print with a "display only" tooltip |
| D5 | Primitive heatmap | One row per `primitive_type` × one column per grade. Cell intensity = share of the entity's weight at that intersection |
| D6 | Pro/counter card | Side-by-side panels under the signal detail drawer: pro on left, counter on right, tie-breaker below |
| D7 | Calibration queue | Separate page `/calibration` listing pending samples scoped to user's coverage; one-click decision via radio + note |
| D8 | Mechanism drawer | Right-side drawer reachable from the validator card; shows recalled mechanisms with summary + tags |
| D9 | Disclosure packet | Generated on demand: button "Generate Packet" on a referred submission. Server returns Markdown + JSON; UI exposes both, copies digest to clipboard |
| D10 | Backward compat | Existing UI tabs/components untouched. Additive only |

## Files

### Create — Backend (Pydantic + routes)
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
- `signal_architecture/disclosure/packet.py` — Markdown+JSON generation
- `signal_architecture/disclosure/templates.py` — Jinja templates
- `tests/api/test_evidence_endpoints.py`
- `tests/api/test_disclosure_endpoint.py`

### Create — Frontend
- `frontend/src/types/evidence.ts`
- `frontend/src/components/submissions/Workbench/EvidenceTab.tsx`
- `frontend/src/components/submissions/Workbench/CompositeEvidencePanel.tsx`
- `frontend/src/components/submissions/Workbench/PrimitiveHeatmap.tsx`
- `frontend/src/components/submissions/Workbench/EvidenceBadge.tsx`
- `frontend/src/components/submissions/Workbench/ConfidenceBar.tsx`
- `frontend/src/components/submissions/Workbench/ReproducibilityChip.tsx`
- `frontend/src/components/submissions/Workbench/ProCounterCard.tsx`
- `frontend/src/components/submissions/Workbench/MechanismDrawer.tsx`
- `frontend/src/components/submissions/Workbench/DisclosurePacketButton.tsx`
- `frontend/src/app/calibration/page.tsx`
- `frontend/src/components/calibration/CalibrationQueue.tsx`
- `frontend/src/components/calibration/DecisionForm.tsx`

### Modify
- `frontend/src/types/dsi.ts` — extend `ModelVersion` and `SignalCondition` with V7 fields
- `frontend/src/components/submissions/Workbench/WorkbenchView.tsx` — wire the new tab + panel
- `infrastructure/api/types.py` — extend existing `ModelVersionDTO` etc with V7 fields
- `infrastructure/api/main.py` — register new routers

## API DTOs

`infrastructure/api/schemas/evidence.py`:

```python
"""V7 Phase 14 — evidence Pydantic DTOs.

Each DTO maps directly to the ORM rows added in Phases 5/6/7/8/9.
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
```

## Routes

`infrastructure/api/routes/evidence.py`:

```python
"""V7 Phase 14 — evidence read endpoints."""
from __future__ import annotations

import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException

from infrastructure.api.utils import current_user, get_db
from infrastructure.api.schemas.evidence import (
    CompositeEvidenceDTO, GradeRollupDTO, SignalEvidenceDTO,
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
        grade_referral_reasons=_load_grade_referrals(db, model_version_id),
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


@router.get("/{model_version_id}/signals/{signal_id}/history")
def get_signal_history(model_version_id: uuid.UUID, signal_id: str,
                       db=Depends(get_db), user=Depends(current_user)):
    submission_id = _resolve_submission(db, model_version_id, user.tenant_id)
    rows = _load_signal_history(db, submission_id, signal_id)
    return [
        {
            "model_version_id": str(r.model_version_id),
            "recorded_at": r.recorded_at.isoformat(),
            "evidence_grade": r.evidence_grade,
            "score": r.score, "category": r.category,
            "evidence_basis": r.evidence_basis,
        }
        for r in rows
    ]
```

## Disclosure packet generator

`signal_architecture/disclosure/packet.py`:

```python
"""V7 Phase 14 — generate a templated underwriter disclosure packet.

Bundles signal + grade + pro/counter/tie-breaker + sources + commitment
digest + cluster symptoms + recalled mechanisms.

Outputs both Markdown (human-readable) and JSON (machine-parseable).
"""
from __future__ import annotations

import json
import uuid
from dataclasses import dataclass
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
    sources: list[dict]
    cluster_symptoms: list[dict]
    recalled_mechanisms: list[dict]
    commitment_digest: str
    reproducibility: str | None


def build_packet(
    *,
    model_version_id: uuid.UUID,
    composite_min_grade: str | None,
    composite_distribution: dict[str, float],
    referral_reasons: list[str],
    sections: list[PacketSection],
) -> tuple[str, dict[str, Any]]:
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "model_version_id": str(model_version_id),
        "composite_min_grade": composite_min_grade,
        "composite_distribution": composite_distribution,
        "referral_reasons": referral_reasons,
        "sections": [s.__dict__ for s in sections],
    }
    md = _env.from_string(MARKDOWN_TEMPLATE).render(p=payload)
    return md, payload
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

## Disclosure route

`infrastructure/api/routes/disclosure.py`:

```python
from __future__ import annotations

import uuid
from fastapi import APIRouter, Depends, Response
from fastapi.responses import JSONResponse

from infrastructure.api.utils import current_user, get_db
from signal_architecture.disclosure.packet import build_packet, PacketSection
# imports of stores for sections elided


router = APIRouter(prefix="/api/v1/model-versions", tags=["disclosure"])


@router.post("/{mv_id}/disclosure-packet")
def generate_packet(mv_id: uuid.UUID, format: str = "json", db=Depends(get_db), user=Depends(current_user)):
    sections = _build_sections(db, mv_id, user.tenant_id)
    md, payload = build_packet(
        model_version_id=mv_id,
        composite_min_grade=...,
        composite_distribution=...,
        referral_reasons=...,
        sections=sections,
    )
    if format == "md":
        return Response(content=md, media_type="text/markdown")
    return JSONResponse(content={"markdown": md, "payload": payload})
```

## Commitment verification route

`infrastructure/api/routes/commitments.py`:

```python
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from infrastructure.api.utils import current_user, get_db
from infrastructure.db.commitment_store import verify, sha3_224


router = APIRouter(prefix="/api/v1/model-versions", tags=["commitments"])


class VerifyIn(BaseModel):
    signal_id: str | None = None
    scope: str
    candidate_payload: dict


@router.post("/{mv_id}/verify-commitment")
def verify_commitment(mv_id: str, body: VerifyIn, db=Depends(get_db), user=Depends(current_user)):
    ok = verify(db, model_version_id=mv_id, signal_id=body.signal_id, scope=body.scope, candidate_payload=body.candidate_payload)
    return {"ok": ok, "digest_computed": sha3_224(body.candidate_payload)}
```

## Frontend types

`frontend/src/types/evidence.ts`:

```typescript
export type EvidenceGrade =
  | 'inferred' | 'observed' | 'corroborated'
  | 'structured_attested' | 'behaviourally_validated';

export type Reproducibility = 'stable' | 'flaky' | 'unstable' | 'unknown';

export interface EvidenceSource {
  source_id: string;
  kind: string;
  ref: string;
  fetched_at: string;
  response_hash?: string | null;
  notes?: string;
}

export interface SignalEvidence {
  signal_id: string;
  score?: number;
  category?: string;
  confidence: number;
  evidence_grade?: EvidenceGrade | null;
  evidence_basis?: string | null;
  evidence_sources: EvidenceSource[];
  evidence_pro?: string | null;
  evidence_counter?: string | null;
  evidence_tie_breaker?: string | null;
  absence_sub_type?: 'absence_failed_fetch' | 'absence_authoritative_empty' | null;
  primitive_type?: string | null;
  reproducibility?: Reproducibility | null;
  variant_of?: string | null;
  cluster_id?: string | null;
}

export interface GradeRollup {
  min_grade: EvidenceGrade | null;
  weighted_mean_grade: number | null;
  distribution: Partial<Record<EvidenceGrade, number>>;
}

export interface CompositeEvidence {
  composite: GradeRollup;
  per_group: Record<string, GradeRollup>;
  per_primitive: Record<string, GradeRollup>;
  grade_referral_reasons: string[];
}
```

## Visual components

`EvidenceBadge.tsx`:

```tsx
import type { EvidenceGrade } from "@/types/evidence";

const COLOURS: Record<EvidenceGrade, string> = {
  inferred:                "bg-zinc-200 text-zinc-700",
  observed:                "bg-blue-200 text-blue-900",
  corroborated:            "bg-teal-200 text-teal-900",
  structured_attested:     "bg-green-300 text-green-900",
  behaviourally_validated: "bg-emerald-400 text-emerald-950",
};

export function EvidenceBadge({ grade }: { grade: EvidenceGrade | null | undefined }) {
  if (!grade) return <span className="text-zinc-400 text-xs">—</span>;
  return (
    <span className={`px-2 py-0.5 rounded-md text-xs font-mono ${COLOURS[grade]}`}>
      {grade.replace(/_/g, " ")}
    </span>
  );
}
```

`ConfidenceBar.tsx`:

```tsx
export function ConfidenceBar({ value }: { value: number }) {
  // Deliberately greyscale — never colour. Forces the user to read grade
  // and confidence as independent axes (Phase 14 D2).
  const pct = Math.round(Math.min(1, Math.max(0, value)) * 100);
  return (
    <div className="w-24 h-2 bg-zinc-100 rounded overflow-hidden" title={`${pct}% confidence`}>
      <div className="h-full bg-zinc-600" style={{ width: `${pct}%` }} />
    </div>
  );
}
```

`ReproducibilityChip.tsx`:

```tsx
import type { Reproducibility } from "@/types/evidence";

const RING: Record<Reproducibility, string> = {
  stable:   "ring-green-500 text-green-700",
  flaky:    "ring-amber-500 text-amber-700",
  unstable: "ring-red-500 text-red-700",
  unknown:  "ring-zinc-400 text-zinc-500",
};

export function ReproducibilityChip({ value }: { value: Reproducibility | null | undefined }) {
  const v = value ?? "unknown";
  return (
    <span className={`px-1.5 py-0.5 text-[10px] uppercase tracking-wide font-semibold rounded-full bg-transparent ring-1 ${RING[v]}`}>
      {v}
    </span>
  );
}
```

`CompositeEvidencePanel.tsx`:

```tsx
import { EvidenceBadge } from "./EvidenceBadge";
import type { CompositeEvidence } from "@/types/evidence";

export function CompositeEvidencePanel({ data }: { data: CompositeEvidence }) {
  const ordered: any[] = ["behaviourally_validated", "structured_attested", "corroborated", "observed", "inferred"];
  return (
    <section className="border rounded-lg p-4 space-y-3">
      <header className="flex items-center justify-between">
        <h3 className="text-sm font-semibold">Composite evidence</h3>
        <EvidenceBadge grade={data.composite.min_grade ?? undefined} />
      </header>
      <div className="space-y-1">
        {ordered.map((g) => {
          const w = (data.composite.distribution[g as keyof typeof data.composite.distribution] ?? 0) * 100;
          if (w <= 0) return null;
          return (
            <div key={g} className="flex items-center gap-2">
              <div className="w-32 text-xs"><EvidenceBadge grade={g} /></div>
              <div className="flex-1 h-3 bg-zinc-100 rounded overflow-hidden">
                <div className="h-full bg-zinc-600" style={{ width: `${w}%` }} />
              </div>
              <div className="w-10 text-right text-xs tabular-nums">{Math.round(w)}%</div>
            </div>
          );
        })}
      </div>
      {data.grade_referral_reasons.length > 0 && (
        <ul className="text-xs text-amber-700 list-disc ml-4">
          {data.grade_referral_reasons.map((r) => <li key={r}>{r}</li>)}
        </ul>
      )}
      {data.composite.weighted_mean_grade != null && (
        <p className="text-[10px] text-zinc-400" title="Cardinal arithmetic over an ordinal taxonomy. Display only.">
          weighted mean (display only): {data.composite.weighted_mean_grade.toFixed(2)}
        </p>
      )}
    </section>
  );
}
```

`ProCounterCard.tsx`:

```tsx
import type { SignalEvidence } from "@/types/evidence";

export function ProCounterCard({ sig }: { sig: SignalEvidence }) {
  if (!sig.evidence_pro && !sig.evidence_counter) return null;
  return (
    <div className="grid grid-cols-2 gap-3 my-3">
      <div className="border border-green-200 rounded-lg p-3 bg-green-50">
        <h4 className="text-xs font-bold text-green-800 uppercase tracking-wide mb-1">Pro</h4>
        <p className="text-sm whitespace-pre-wrap">{sig.evidence_pro ?? "—"}</p>
      </div>
      <div className="border border-red-200 rounded-lg p-3 bg-red-50">
        <h4 className="text-xs font-bold text-red-800 uppercase tracking-wide mb-1">Counter</h4>
        <p className="text-sm whitespace-pre-wrap">{sig.evidence_counter ?? "—"}</p>
      </div>
      {sig.evidence_tie_breaker && (
        <div className="col-span-2 border border-zinc-200 rounded-lg p-3 bg-zinc-50">
          <h4 className="text-xs font-bold text-zinc-700 uppercase tracking-wide mb-1">Tie-breaker</h4>
          <p className="text-sm whitespace-pre-wrap">{sig.evidence_tie_breaker}</p>
        </div>
      )}
    </div>
  );
}
```

## Workbench integration

`WorkbenchView.tsx` extension:
- Add a new `EvidenceTab` after `SummaryTab`.
- Render `CompositeEvidencePanel` in the existing `SummaryTab` header.
- Each row in the signal ledger renders `EvidenceBadge` + `ConfidenceBar` + `ReproducibilityChip` in a single line.
- Clicking a signal opens a drawer with the source list, `ProCounterCard`, `MechanismDrawer`, and a "Verify commitment" button.

## Calibration page

`frontend/src/app/calibration/page.tsx` and `CalibrationQueue.tsx`:
- Fetches `/api/v1/calibration/pending`.
- Renders a card per pending sample with signal_id, extractor_grade, validator_grade, sampling_reason.
- `DecisionForm`: radio (5 grades) + optional note + Submit → `POST /api/v1/calibration/decision`.
- Below the queue: stats card from `/api/v1/calibration/stats`.

## Steps

### 14.1 — Pydantic DTOs
Land schemas under `infrastructure/api/schemas/`. Existing endpoints that return `ModelVersionDTO` etc. extend their response models with the V7 fields.

### 14.2 — Backend routes
Implement `evidence.py`, `disclosure.py`, `mechanism.py`, `entity_events.py`, `commitments.py`. Register in `infrastructure/api/main.py`.

### 14.3 — Disclosure packet generator
Land `signal_architecture/disclosure/packet.py` and `templates.py`. Integration with the existing `referrals` table: when a grade-driven referral fires, the workflow stores the generated packet's JSON payload as `referrals.disclosure_packet` (alembic `029` adds the column).

### 14.4 — Alembic `029` for disclosure packet column
```python
op.add_column("referrals", sa.Column("disclosure_packet", JSONB, nullable=True))
```

### 14.5 — Frontend types + visual primitives
Land `evidence.ts`, `EvidenceBadge`, `ConfidenceBar`, `ReproducibilityChip`.

### 14.6 — Composite panel + signal ledger row
Land `CompositeEvidencePanel`, extend the existing signal-row component to render the three axes side-by-side.

### 14.7 — Pro/counter and mechanism drawer
Land `ProCounterCard`, `MechanismDrawer`. Drawer fetches `/api/v1/model-versions/{mv_id}/signals/{signal_id}/mechanisms`.

### 14.8 — Disclosure button
`DisclosurePacketButton.tsx`: only visible on referred submissions; POSTs to disclosure endpoint, shows Markdown in a modal with copy buttons.

### 14.9 — Calibration page
Land `/calibration` page with queue + decision form + stats.

### 14.10 — Tests
- `tests/api/test_evidence_endpoints.py` — DTOs match ORM, pagination, auth.
- `tests/api/test_disclosure_endpoint.py` — Markdown contains every required section; JSON parses; commitment digest present.
- `frontend` component tests using the project's existing test harness — assert that grade/confidence/reproducibility render as visually distinct elements (different test IDs).

## Test gates

```bash
pytest tests/api/ -v
pytest tests/ -x -q

# Frontend
cd frontend && npm test -- --runInBand
cd frontend && npm run build

# Smoke: seed + GET composite endpoint
python -m seed bench
curl -s -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/v1/model-versions/$MV_ID/evidence | jq .composite.min_grade
```

## Done when

- [ ] Every new V7 field has a Pydantic DTO and an endpoint returning it.
- [ ] Workbench renders grade, confidence, reproducibility as three visually distinct elements.
- [ ] Composite panel displays distribution and min-grade; weighted mean is rendered only in small print with explanatory tooltip.
- [ ] Pro/counter card renders on demand.
- [ ] Disclosure packet generates valid Markdown + JSON; verification endpoint round-trips a stored commitment.
- [ ] Calibration page lists pending samples and accepts decisions.
- [ ] No existing UI tab regresses.
- [ ] Full backend + frontend test suites green.

## Out of scope

- Mobile responsiveness for the new components beyond default flex/grid behaviour.
- Bulk export of disclosure packets across portfolio. → V8.
- A&B testing different visual encodings of grade. → V8.

## Invariants

1. Grade and confidence are never rendered using the same colour ramp or position.
2. Reproducibility is always a separate chip.
3. The weighted mean is rendered only as supplementary detail with a "display only" cue — never as the primary indicator.
4. Disclosure packets are deterministic for a given model_version_id: same data in, same Markdown out.

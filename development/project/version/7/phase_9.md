# V7 Phase 9: Risk Primitive Classification

## Depends on
- Phase 1 (taxonomy).
- Phase 2 (every signal has a grade).

## Blocks
- Phase 12 (mechanism memory clusters by primitive_type).
- Phase 14 (frontend filters/groups by primitive).

## Scope

Add an orthogonal classification axis to every signal: `primitive_type` — the **risk-primitive class** the signal contributes to. Independent of the source taxonomy, coverage, or signal_id. Lets you ask "what's this entity's grade distribution by risk primitive?" — a question DSI cannot answer today.

Primitives (12-item baseline):

1. `counterparty` — credit/financial counterparty risk.
2. `regulatory` — sanctions, licensing, jurisdictional compliance.
3. `operational` — patch cadence, supply chain, fleet age, plant condition.
4. `financial` — leverage, liquidity, profitability.
5. `reputational` — sentiment, litigation, ESG.
6. `cyber` — security posture, breach history.
7. `climate` — natural hazard, ESG-environmental, exposure.
8. `governance` — board composition, director history.
9. `crime` — fraud, money-laundering, organised-crime exposure.
10. `physical_asset` — TIV, asset specifics, location.
11. `behavioural` — patch cadence, hiring patterns, deployment frequency.
12. `human_capital` — workforce, key-person, skills.

Classification rule per signal:
1. **Explicit override**: YAML `signal_registry[<sig>].primitive_type` if set.
2. **Coverage-default map**: per-coverage default primitive for a signal_id.
3. **CWE-equivalent map**: pattern match on signal_id prefix (`sanctions_*` → regulatory, etc.).
4. **LLM fallback**: only when 1–3 produce nothing; rarely invoked.

Stored on `SignalResult.primitive_type`, persisted to `model_version_signals`, used by downstream phases.

## Decisions (locked)

| # | Decision | Choice |
|---|----------|--------|
| D1 | Primitives | 12-item list above (locked; future additions are V8) |
| D2 | Classification cascade | YAML override → coverage map → pattern map → LLM fallback |
| D3 | Mandatory | Yes. Every committed `SignalResult` has a `primitive_type`. `unknown` is permitted only when classification fails outright |
| D4 | Storage | `model_version_signals.primitive_type`, `signal_history.primitive_type` columns |
| D5 | Pattern map | Static dict in `signal_architecture/signals/primitive_classification.py` |
| D6 | LLM fallback | Lazy: only invoked when the cascade returns `unknown` AND the signal has weight ≥ 0.05 |
| D7 | YAML representation | Optional `primitive_type:` field on each `signal_registry` entry — schema additive, no rollout script breaks |
| D8 | Aggregation hooks | `ScoringResult.primitive_grade_rollups: dict[primitive_type, GradeRollup]` |
| D9 | No pricing impact | Primitive type is metadata. Calibration unchanged |

## Files

### Create
- `signal_architecture/signals/primitive_classification.py`
- `tests/unit/test_primitive_classification.py`
- `alembic/versions/027_primitive_type.py`

### Modify
- `signal_architecture/signals/types.py` — `primitive_type: Optional[Literal[...]]` field on `SignalResult`
- `infrastructure/models/config_schema.py` — `SignalDefinition` gains optional `primitive_type`
- `infrastructure/db/models.py` — `primitive_type` column on `ModelVersionSignal` and `SignalHistory`
- `layers/risk/scorer.py` — classify each signal at construction; compute `primitive_grade_rollups`
- `layers/risk/types.py` — add `primitive_grade_rollups: Dict[str, GroupGradeRollup]` to `ScoringResult`

## Module

`signal_architecture/signals/primitive_classification.py`:

```python
"""V7 Phase 9 — risk-primitive classification.

Public API:
    classify(sig_def, signal_id, coverage) -> PrimitiveType
"""
from __future__ import annotations

from typing import Literal, Optional

PrimitiveType = Literal[
    "counterparty",
    "regulatory",
    "operational",
    "financial",
    "reputational",
    "cyber",
    "climate",
    "governance",
    "crime",
    "physical_asset",
    "behavioural",
    "human_capital",
    "unknown",
]

PRIMITIVES: tuple[PrimitiveType, ...] = (
    "counterparty", "regulatory", "operational", "financial",
    "reputational", "cyber", "climate", "governance",
    "crime", "physical_asset", "behavioural", "human_capital",
    "unknown",
)


# Coverage-specific defaults (a few examples; full list in code).
COVERAGE_DEFAULTS: dict[str, PrimitiveType] = {
    "fi": "financial",
    "cyber": "cyber",
    "climate": "climate",
    "marine": "physical_asset",
    "property": "physical_asset",
    "casualty": "operational",
    "do": "governance",
    "pi": "operational",
    "fpr": "counterparty",
    "aerospace": "physical_asset",
    "energy": "physical_asset",
}


# signal_id prefix → primitive. First match wins. Order matters: more
# specific prefixes earlier.
SIGNAL_ID_PREFIX_MAP: list[tuple[str, PrimitiveType]] = [
    ("sanctions_",          "regulatory"),
    ("pep_",                "regulatory"),
    ("ofac_",               "regulatory"),
    ("regulatory_",         "regulatory"),
    ("license_",            "regulatory"),
    ("kyc_",                "regulatory"),
    ("director_litigation", "governance"),
    ("director_",           "governance"),
    ("officer_",            "governance"),
    ("board_",              "governance"),
    ("sec_filing",          "financial"),
    ("credit_rating",       "financial"),
    ("financial_",          "financial"),
    ("leverage_",           "financial"),
    ("liquidity_",          "financial"),
    ("security_",           "cyber"),
    ("vuln_",               "cyber"),
    ("breach_",             "cyber"),
    ("tls_",                "cyber"),
    ("patch_",              "behavioural"),
    ("cert_rotation",       "behavioural"),
    ("hiring_",             "human_capital"),
    ("workforce_",          "human_capital"),
    ("flood_",              "climate"),
    ("wind_",               "climate"),
    ("seismic_",            "climate"),
    ("wildfire_",           "climate"),
    ("crime_",              "crime"),
    ("fraud_",              "crime"),
    ("aml_",                "crime"),
    ("tiv_",                "physical_asset"),
    ("asset_",              "physical_asset"),
    ("location_",           "physical_asset"),
    ("fleet_",              "physical_asset"),
    ("alliance_",           "counterparty"),
    ("counterparty_",       "counterparty"),
    ("supply_chain",        "operational"),
    ("operational_",        "operational"),
    ("plant_",              "operational"),
    ("sentiment_",          "reputational"),
    ("reviews_",            "reputational"),
    ("media_",              "reputational"),
    ("esg_",                "reputational"),
]


def classify(
    *,
    signal_id: str,
    coverage: str,
    yaml_override: Optional[PrimitiveType] = None,
) -> PrimitiveType:
    """Cascade. Returns 'unknown' when no level resolves."""
    if yaml_override is not None and yaml_override in PRIMITIVES:
        return yaml_override
    for prefix, prim in SIGNAL_ID_PREFIX_MAP:
        if signal_id.startswith(prefix):
            return prim
    if coverage in COVERAGE_DEFAULTS:
        return COVERAGE_DEFAULTS[coverage]
    return "unknown"


# LLM fallback wrapper — invoked only when classify(...) returns "unknown" AND signal_weight >= 0.05.
# Implementation kept tiny — the provider, prompt, and JSON parsing are
# stamped in by the existing project LLM client.

_LLM_PROMPT = (
    "Classify this signal into one of: {primitives}. "
    "Return ONLY the primitive name.\n\n"
    "signal_id: {signal_id}\n"
    "coverage: {coverage}\n"
    "evidence_basis: {basis}\n"
)


def llm_fallback(llm_client, *, signal_id: str, coverage: str, evidence_basis: str) -> PrimitiveType:
    text = llm_client.aask_text(
        system="You are a risk-classification expert.",
        user=_LLM_PROMPT.format(
            primitives=", ".join(p for p in PRIMITIVES if p != "unknown"),
            signal_id=signal_id, coverage=coverage,
            basis=evidence_basis or "",
        ),
    ).first_text().strip().lower()
    return text if text in PRIMITIVES else "unknown"
```

## Migration `027`

```python
"""V7 Phase 9 — primitive_type column on signals."""
import sqlalchemy as sa
from alembic import op

revision = "027"
down_revision = "026"


def upgrade():
    op.add_column("model_version_signals", sa.Column("primitive_type", sa.String(32), nullable=True))
    op.add_column("signal_history", sa.Column("primitive_type", sa.String(32), nullable=True))
    op.create_index("ix_mvs_primitive", "model_version_signals", ["primitive_type"])
    op.create_index("ix_history_primitive", "signal_history", ["primitive_type"])


def downgrade():
    op.drop_index("ix_history_primitive", table_name="signal_history")
    op.drop_index("ix_mvs_primitive", table_name="model_version_signals")
    op.drop_column("signal_history", "primitive_type")
    op.drop_column("model_version_signals", "primitive_type")
```

## Steps

### 9.1 — Module
**File**: `signal_architecture/signals/primitive_classification.py` (create).
**Action**: Drop in code.
**Test**: cascade order; unknown for unrecognised; LLM fallback invoked only when first three return unknown.

### 9.2 — Type
**File**: `signal_architecture/signals/types.py`.
**Action**: Add `primitive_type: Optional[Literal[...]]` field on `SignalResult`.

### 9.3 — Migration
**File**: `alembic/versions/027_primitive_type.py`.
**Action**: Apply and round-trip.

### 9.4 — Pydantic schema
**File**: `infrastructure/models/config_schema.py`.
**Action**: Add `primitive_type: Optional[PrimitiveType] = None` to `SignalDefinition`. Existing configs validate unchanged.

### 9.5 — Classify in scorer
**File**: `layers/risk/scorer.py`.
**Action**: After each `SignalResult` is produced by inference functions:
```python
from signal_architecture.signals.primitive_classification import classify, llm_fallback

sig.primitive_type = classify(
    signal_id=sig.signal_id,
    coverage=config.coverage,
    yaml_override=getattr(sig_def, "primitive_type", None),
)
if sig.primitive_type == "unknown" and signal_weight >= 0.05:
    sig.primitive_type = llm_fallback(llm_client, signal_id=sig.signal_id,
                                      coverage=config.coverage,
                                      evidence_basis=sig.evidence_basis or "")
```

### 9.6 — Primitive rollups
**File**: `layers/risk/scorer.py`, `layers/risk/types.py`.
**Action**:
```python
from signal_architecture.signals.aggregators.grade_rollup import rollup

primitive_groups: dict[str, list[tuple[SignalResult, float]]] = {}
for sig, weight in graded_signals_with_weight:
    primitive_groups.setdefault(sig.primitive_type or "unknown", []).append((sig, weight))
scoring_result.primitive_grade_rollups = {
    prim: GroupGradeRollup(
        group_id=f"primitive::{prim}",
        min_grade=r.min_grade,
        weighted_mean_grade=r.weighted_mean_grade,
        distribution=r.distribution,
    )
    for prim, items in primitive_groups.items()
    for r in [rollup(items)]
    if not r.is_empty()
}
```

### 9.7 — Persistence
**File**: `infrastructure/db/evidence_store.py`.
**Action**: Extend `persist_signal_evidence` to write `primitive_type`. Phase 5's `SignalHistory` insertion also writes it.

### 9.8 — Tests
**Files**:
- `tests/unit/test_primitive_classification.py` — cascade, coverage map, prefix map, fallback gating.
- `tests/integration/test_primitive_rollups.py` — given a synthetic scoring result, assert `primitive_grade_rollups` totals to within-rounding of `composite_grade_distribution`.

## Test gates

```bash
alembic upgrade head
alembic downgrade -1
alembic upgrade head

pytest tests/unit/test_primitive_classification.py tests/integration/test_primitive_rollups.py -v
pytest tests/ -x -q

python -m seed bench
psql -c "SELECT primitive_type, COUNT(*) FROM model_version_signals GROUP BY primitive_type"
# every row should have a primitive_type assigned
psql -c "SELECT COUNT(*) FROM model_version_signals WHERE primitive_type IS NULL"
# -> 0
```

## Done when

- [ ] Every committed `model_version_signals` row has a `primitive_type`.
- [ ] `ScoringResult.primitive_grade_rollups` populated.
- [ ] Cascade order respected: YAML override > prefix map > coverage default > LLM fallback.
- [ ] LLM fallback only invoked when first three return unknown AND signal weight ≥ 0.05.
- [ ] Calibration unchanged.
- [ ] Full pytest green.

## Out of scope

- Per-primitive referral rules. → V8 (extend `evidence_grade_policy`).
- Cross-primitive correlation analysis. → out of V7.
- Frontend primitive view. → Phase 14.

## Invariants

1. Every signal is classified before commit; `primitive_type` is non-null in `model_version_signals`.
2. Classification is deterministic for a given (signal_id, coverage, yaml_override) — no LLM call when the deterministic cascade resolves.
3. No pricing impact.

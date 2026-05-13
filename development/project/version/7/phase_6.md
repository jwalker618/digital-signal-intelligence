# V7 Phase 6: Adversarial Validator

## Depends on
- Phase 2 (every signal has a grade).
- Phase 3 (composite rollup exists).
- Phase 5 (commitment + compliance audit stores exist).

## Blocks
- Phase 7 (calibration store reads validator verdicts).
- Phase 14 (frontend renders pro/counter/tie-breaker).

## Scope

Add a 4-axis blind adversarial validator that runs over selected `SignalResult` instances during a cycle. Validator is **independent**: it sees only the signal payload, never the extractor's transcript or chain-of-thought (call sites enforced via Pydantic input contract). It evaluates four axes:

- **MATERIAL** — does this signal actually change the price/tier?
- **CORRECT_ENTITY** — does the underlying data belong to the entity being assessed?
- **OPERATIONALLY_PLAUSIBLE** — is the asserted state consistent with the entity's known operations?
- **GENERALISES_AT_RENEWAL** — would this be re-extracted to the same conclusion at renewal under reasonable variation?

Produces `pro_argument`, `counter_argument`, `tie_breaker`, and `advance: bool`. Bumps `evidence_grade` only if `advance=True`. Populates the `evidence_pro`, `evidence_counter`, `evidence_tie_breaker` fields added in Phase 1. Records verdict in a new `validator_verdicts` table + `compliance_audit_logs`.

Quick-pass vs full-pass: low-grade signals (`inferred`, `observed`) get the cheap 2-axis prompt; high-grade signals (`corroborated`+) get the full 4-axis prompt. Lifted directly from Clearwing's `validator.py:155-169` gate pattern.

End of phase: alembic `024` tightens `model_version_signals.evidence_grade` to NOT NULL, since every signal that reaches commit now has a grade (validator-promoted or extractor-asserted).

## Decisions (locked)

| # | Decision | Choice |
|---|----------|--------|
| D1 | Validator scope | Runs over signals with `evidence_grade >= corroborated` OR signals whose `signal_id` appears in `evidence_grade_policy.expected_grades` |
| D2 | Independence | Validator's input is a `ValidatorInput` Pydantic model that **excludes** `metadata`, `raw_data`, any "reasoning"/"transcript" keys, and any field beginning with `_`. Enforced at construction |
| D3 | Axes | MATERIAL, CORRECT_ENTITY, OPERATIONALLY_PLAUSIBLE, GENERALISES_AT_RENEWAL |
| D4 | Advance rule | All four pass, OR MATERIAL+CORRECT_ENTITY pass and the other two have ≥medium confidence |
| D5 | Quick-pass | Used when `evidence_grade in {"inferred", "observed"}` AND the signal is not in the expected_grades policy. 2 axes: MATERIAL, CORRECT_ENTITY |
| D6 | Grade bump on advance | Validator can bump up to `corroborated` (quick-pass) or `structured_attested` (full-pass), never higher. Higher grades require human attestation (Phase 7) |
| D7 | Persistence | New `validator_verdicts` table — append-only, one row per (model_version_id, signal_id). Verdict also mirrored into compliance audit log |
| D8 | LLM provider | Existing project provider — no new dependency. Validator prompts go in `signal_architecture/validation/prompts.py` |
| D9 | NOT NULL flip | Alembic `024` adds NOT NULL on `model_version_signals.evidence_grade` after Phase 6 has run end-to-end on the seed dataset and confirmed every row has a grade |
| D10 | Disable knob | YAML `evidence_grade_policy.validator: {enabled, max_concurrent, full_pass_floor, advance_bump_cap}` block. Default `enabled: true`, `max_concurrent: 5`, `full_pass_floor: corroborated`, `advance_bump_cap: structured_attested` |

## Files

### Create
- `signal_architecture/validation/__init__.py`
- `signal_architecture/validation/types.py`
- `signal_architecture/validation/validator.py`
- `signal_architecture/validation/prompts.py`
- `infrastructure/db/validator_store.py`
- `alembic/versions/024_validator_verdicts.py`
- `tests/unit/test_validator_input_independence.py`
- `tests/unit/test_validator_advance_rule.py`
- `tests/unit/test_validator_persistence.py`

### Modify
- `infrastructure/models/config_schema.py` — add `ValidatorPolicy` to `EvidenceGradePolicy`
- `layers/risk/workflow.py` — invoke the validator over selected signals after scoring, before commit
- `infrastructure/db/models.py` — `ValidatorVerdict` ORM class
- All 24 coverage configs — script `scripts/add_validator_block.py` injects the default validator block

## Types

`signal_architecture/validation/types.py`:

```python
"""V7 Phase 6 — adversarial validator types.

Designed for independence: ValidatorInput strips reasoning/transcripts.
Only the signal's asserted facts go to the LLM.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

from signal_architecture.signals.evidence import EvidenceGrade, EvidenceSource

Axis = Literal[
    "MATERIAL",
    "CORRECT_ENTITY",
    "OPERATIONALLY_PLAUSIBLE",
    "GENERALISES_AT_RENEWAL",
]

AXES_FULL: tuple[Axis, ...] = (
    "MATERIAL", "CORRECT_ENTITY", "OPERATIONALLY_PLAUSIBLE", "GENERALISES_AT_RENEWAL",
)
AXES_QUICK: tuple[Axis, ...] = ("MATERIAL", "CORRECT_ENTITY")

ValidatorMode = Literal["quick_pass", "full_pass"]
ConfidenceLevel = Literal["high", "medium", "low"]


# ---------------------------------------------------------------------------
# Input contract — STRIPPED of reasoning/transcripts
# ---------------------------------------------------------------------------

class ValidatorInput(BaseModel):
    """The only payload the validator LLM ever sees.

    `model_config` rejects fields starting with `_` and any key in the
    denied list. Caller must construct via `ValidatorInput.from_signal()`
    — direct construction with arbitrary kwargs is also fine but the
    Pydantic schema rejects anything not in the allowed shape.
    """
    model_config = ConfigDict(extra="forbid", frozen=True)

    signal_id: str
    score: Optional[float] = None
    category: Optional[str] = None
    confidence: float
    evidence_grade: EvidenceGrade
    evidence_basis: str
    evidence_sources: list[dict] = Field(default_factory=list)
    absence_sub_type: Optional[str] = None

    entity_id: str
    entity_name: str
    entity_country: Optional[str] = None
    coverage: str

    @classmethod
    def from_signal(
        cls,
        sig,  # SignalResult
        *,
        entity_id: str,
        entity_name: str,
        entity_country: Optional[str],
        coverage: str,
    ) -> "ValidatorInput":
        return cls(
            signal_id=sig.signal_id,
            score=sig.score,
            category=sig.category,
            confidence=sig.confidence,
            evidence_grade=sig.evidence_grade,
            evidence_basis=sig.evidence_basis or "",
            evidence_sources=[s.to_dict() for s in (sig.evidence_sources or [])],
            absence_sub_type=sig.absence_sub_type,
            entity_id=entity_id,
            entity_name=entity_name,
            entity_country=entity_country,
            coverage=coverage,
        )


@dataclass(frozen=True)
class AxisResult:
    axis: Axis
    passed: bool
    confidence: ConfidenceLevel
    rationale: str  # ≤500 chars


@dataclass(frozen=True)
class ValidatorVerdict:
    signal_id: str
    mode: ValidatorMode
    axes: dict[Axis, AxisResult]
    advance: bool
    grade_after_bump: Optional[EvidenceGrade]
    pro_argument: str
    counter_argument: str
    tie_breaker: str
    raw_response: str
    elapsed_seconds: float
    decided_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
```

## Advance rule

`signal_architecture/validation/validator.py` (core logic only — LLM I/O elided for brevity):

```python
from .types import AxisResult, ValidatorVerdict, AXES_FULL, AXES_QUICK


def compute_advance(mode: str, axes: dict[str, AxisResult]) -> bool:
    """Locked rule from Decision D4.

    full_pass:
        All four pass, OR
        MATERIAL+CORRECT_ENTITY pass AND OPERATIONALLY_PLAUSIBLE.confidence>=medium
        AND GENERALISES_AT_RENEWAL.confidence>=medium.
    quick_pass:
        Both MATERIAL and CORRECT_ENTITY pass.
    """
    if mode == "quick_pass":
        return all(axes[a].passed for a in AXES_QUICK if a in axes)
    if mode == "full_pass":
        if all(axes[a].passed for a in AXES_FULL if a in axes):
            return True
        med_or_above = {"high", "medium"}
        material = axes.get("MATERIAL")
        correct = axes.get("CORRECT_ENTITY")
        op_p = axes.get("OPERATIONALLY_PLAUSIBLE")
        gen = axes.get("GENERALISES_AT_RENEWAL")
        if (
            material and correct and op_p and gen
            and material.passed and correct.passed
            and op_p.confidence in med_or_above
            and gen.confidence in med_or_above
        ):
            return True
    return False


def grade_after_bump(
    current: EvidenceGrade,
    advance: bool,
    mode: str,
    cap: EvidenceGrade,
) -> EvidenceGrade:
    """If advance, bump one rung but never above cap; otherwise unchanged."""
    if not advance:
        return current
    from signal_architecture.signals.evidence import (
        bump_evidence, evidence_rank, EVIDENCE_GRADES,
    )
    # Bump by one rung
    cur_rank = evidence_rank(current)
    target_rank = min(cur_rank + 1, evidence_rank(cap))
    target = EVIDENCE_GRADES[target_rank]
    return bump_evidence(current, target)
```

## Prompts

`signal_architecture/validation/prompts.py`:

```python
"""V7 Phase 6 — adversarial-validator prompts.

Independence guarantee: prompts do NOT request the extractor's reasoning or
transcript, only the asserted payload. Output is strict JSON.
"""

FULL_PASS_SYSTEM = """\
You are an INDEPENDENT VALIDATOR for an insurance pricing signal.
You did NOT extract this signal. Your job is to challenge it on FOUR axes.
For each axis, build the STRONGEST possible counter-argument, then decide.

## AXIS 1: MATERIAL
Does this signal meaningfully affect the price or tier for this coverage?
A signal that's correct but has near-zero weight is NOT material.

## AXIS 2: CORRECT_ENTITY
Is the underlying data unambiguously about THIS entity?
Watch for name collisions, subsidiary mix-ups, jurisdiction mismatches.

## AXIS 3: OPERATIONALLY_PLAUSIBLE
Is the asserted state consistent with what we know of the entity's
operations? E.g., a marine cargo signal for a landlocked manufacturer
is implausible regardless of source.

## AXIS 4: GENERALISES_AT_RENEWAL
Would re-extracting this signal in 12 months under reasonable variation
(different IP, different time of day) reach the same conclusion?

## OUTPUT — return ONLY this JSON:
{
  "axes": {
    "MATERIAL":                {"passed": bool, "confidence": "high|medium|low", "rationale": "..."},
    "CORRECT_ENTITY":          {"passed": bool, "confidence": "high|medium|low", "rationale": "..."},
    "OPERATIONALLY_PLAUSIBLE": {"passed": bool, "confidence": "high|medium|low", "rationale": "..."},
    "GENERALISES_AT_RENEWAL":  {"passed": bool, "confidence": "high|medium|low", "rationale": "..."}
  },
  "pro_argument": "max 200 words — strongest case FOR retaining this signal",
  "counter_argument": "max 200 words — strongest case AGAINST",
  "tie_breaker": "the single piece of evidence that resolved it"
}
"""

QUICK_PASS_SYSTEM = """\
You are a quick-pass validator. Check ONLY two axes:

1. MATERIAL — does this signal change price/tier?
2. CORRECT_ENTITY — does this data unambiguously refer to the named entity?

If both pass, the signal advances. If either fails, reject.

Output ONLY this JSON:
{
  "axes": {
    "MATERIAL":       {"passed": bool, "confidence": "high|medium|low", "rationale": "..."},
    "CORRECT_ENTITY": {"passed": bool, "confidence": "high|medium|low", "rationale": "..."}
  },
  "pro_argument": "one paragraph",
  "counter_argument": "one paragraph",
  "tie_breaker": "what evidence resolved it"
}
"""


def build_user_message(payload_json: str) -> str:
    return f"Validate this signal payload (no reasoning available):\n\n{payload_json}\n"
```

## Migration `024`

```python
"""V7 Phase 6 — validator_verdicts table + NOT NULL on evidence_grade.

Revision ID: 024
Revises: 023
"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision = "024"
down_revision = "023"

def upgrade():
    op.create_table(
        "validator_verdicts",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("model_version_id", UUID(as_uuid=True), sa.ForeignKey("model_versions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("signal_id", sa.String(128), nullable=False),
        sa.Column("mode", sa.String(16), nullable=False),
        sa.Column("advance", sa.Boolean, nullable=False),
        sa.Column("grade_before", sa.String(32), nullable=True),
        sa.Column("grade_after", sa.String(32), nullable=True),
        sa.Column("axes", JSONB, server_default=sa.text("'{}'::jsonb")),
        sa.Column("pro_argument", sa.Text, nullable=False),
        sa.Column("counter_argument", sa.Text, nullable=False),
        sa.Column("tie_breaker", sa.Text, nullable=False),
        sa.Column("raw_response", sa.Text, nullable=True),
        sa.Column("elapsed_seconds", sa.Numeric(8, 3), nullable=True),
        sa.Column("decided_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_unique_constraint(
        "uq_validator_verdict_per_mv_signal",
        "validator_verdicts",
        ["model_version_id", "signal_id"],
    )
    op.create_index("ix_validator_verdicts_advance", "validator_verdicts", ["advance"])

    # Backfill any remaining nulls before tightening NOT NULL
    op.execute("UPDATE model_version_signals SET evidence_grade='inferred' WHERE evidence_grade IS NULL")
    op.alter_column("model_version_signals", "evidence_grade", nullable=False)


def downgrade():
    op.alter_column("model_version_signals", "evidence_grade", nullable=True)
    op.drop_index("ix_validator_verdicts_advance", table_name="validator_verdicts")
    op.drop_constraint("uq_validator_verdict_per_mv_signal", "validator_verdicts", type_="unique")
    op.drop_table("validator_verdicts")
```

## Steps

### 6.1 — Validator types
**File**: `signal_architecture/validation/types.py` (create).
**Action**: Drop in code above.
**Test**: `tests/unit/test_validator_input_independence.py`:
```python
def test_validator_input_rejects_extra_fields():
    with pytest.raises(Exception):
        ValidatorInput.model_validate({
            "signal_id": "x", "confidence": 1.0, "evidence_grade": "observed",
            "evidence_basis": "x", "entity_id": "e", "entity_name": "E",
            "coverage": "cyber",
            "reasoning": "this is the LLM's chain of thought",  # FORBIDDEN
        })

def test_validator_input_excludes_metadata_and_raw_data():
    sig = SignalResult(signal_id="x", score=50, confidence=1.0,
                       evidence_grade="observed", evidence_basis="x",
                       raw_data={"secret_transcript": "..."},
                       metadata={"chain_of_thought": "..."})
    vi = ValidatorInput.from_signal(sig, entity_id="e", entity_name="E",
                                    entity_country="UK", coverage="cyber")
    payload = vi.model_dump()
    assert "raw_data" not in payload
    assert "metadata" not in payload
    assert "secret_transcript" not in str(payload)
```

### 6.2 — Advance rule + grade bump
**File**: `signal_architecture/validation/validator.py` (create).
**Action**: Implement `compute_advance` and `grade_after_bump` per the locked rules.
**Test**: `tests/unit/test_validator_advance_rule.py`:
```python
def test_full_pass_all_pass_advances():
    axes = {a: AxisResult(a, passed=True, confidence="high", rationale="x") for a in AXES_FULL}
    assert compute_advance("full_pass", axes) is True

def test_full_pass_two_pass_two_medium_advances():
    axes = {
        "MATERIAL":        AxisResult("MATERIAL", True, "high", ""),
        "CORRECT_ENTITY":  AxisResult("CORRECT_ENTITY", True, "high", ""),
        "OPERATIONALLY_PLAUSIBLE": AxisResult("OPERATIONALLY_PLAUSIBLE", False, "medium", ""),
        "GENERALISES_AT_RENEWAL":  AxisResult("GENERALISES_AT_RENEWAL", False, "medium", ""),
    }
    assert compute_advance("full_pass", axes) is True

def test_full_pass_two_pass_two_low_does_not_advance():
    axes = {
        "MATERIAL":        AxisResult("MATERIAL", True, "high", ""),
        "CORRECT_ENTITY":  AxisResult("CORRECT_ENTITY", True, "high", ""),
        "OPERATIONALLY_PLAUSIBLE": AxisResult("OPERATIONALLY_PLAUSIBLE", False, "low", ""),
        "GENERALISES_AT_RENEWAL":  AxisResult("GENERALISES_AT_RENEWAL", False, "low", ""),
    }
    assert compute_advance("full_pass", axes) is False

def test_grade_bump_caps_at_structured_attested():
    assert grade_after_bump("structured_attested", advance=True, mode="full_pass", cap="structured_attested") == "structured_attested"
    assert grade_after_bump("observed", advance=True, mode="quick_pass", cap="corroborated") == "corroborated"
```

### 6.3 — LLM I/O wrapper
**File**: `signal_architecture/validation/validator.py` (extend).
**Action**: Add `Validator` class that:
1. Picks `quick_pass` or `full_pass` mode based on grade + policy.
2. Constructs `ValidatorInput`.
3. Calls the LLM with appropriate prompt (`prompts.py`).
4. Parses JSON; constructs `ValidatorVerdict`.
5. Computes `advance` and `grade_after_bump`.
6. Returns the verdict.

Failure mode: on LLM error or unparseable JSON, return verdict with `advance=False`, `grade_after_bump=current`, `tie_breaker="validator failure: <reason>"`, log to `compliance_audit_logs` with `event_type="validator_failure"`.

### 6.4 — Persistence
**File**: `infrastructure/db/validator_store.py` (create).
**Action**:
```python
def persist_verdict(db, *, model_version_id, verdict: ValidatorVerdict, grade_before: EvidenceGrade) -> None:
    db.add(ValidatorVerdictRecord(
        model_version_id=model_version_id, signal_id=verdict.signal_id,
        mode=verdict.mode, advance=verdict.advance,
        grade_before=grade_before, grade_after=verdict.grade_after_bump,
        axes={a.axis: {"passed": a.passed, "confidence": a.confidence, "rationale": a.rationale}
              for a in verdict.axes.values()},
        pro_argument=verdict.pro_argument,
        counter_argument=verdict.counter_argument,
        tie_breaker=verdict.tie_breaker,
        raw_response=verdict.raw_response,
        elapsed_seconds=verdict.elapsed_seconds,
        decided_at=verdict.decided_at,
    ))
    log_event(db, event_type="validator_verdict", signal_id=verdict.signal_id,
              model_version_id=model_version_id, payload={...})
```

### 6.5 — Workflow integration
**File**: `layers/risk/workflow.py`.
**Action**: After scoring + before commit:
1. Determine eligible signals (`grade >= corroborated` OR in `expected_grades`).
2. Run validator concurrently with `max_concurrent` from policy.
3. For each verdict:
   - Apply `grade_after_bump` to the `SignalResult` via `bump_evidence`.
   - Populate `evidence_pro`, `evidence_counter`, `evidence_tie_breaker` on the `SignalResult`.
   - Persist via `validator_store.persist_verdict`.
4. Re-run composite rollup so any promotions are reflected in `composite_min_grade`/`composite_grade_distribution`.
5. Re-run `_evaluate_evidence_grade_policy` since promoted signals may resolve referrals.
6. Then commit via Phase 5 stores.

### 6.6 — Migration 024
**File**: `alembic/versions/024_validator_verdicts.py` (create).
**Action**: Apply migration. Run `alembic upgrade head` and `alembic downgrade -1`.

### 6.7 — Per-coverage validator block
**File**: `scripts/add_validator_block.py` (create, modelled on `scripts/add_evidence_grade_policy.py`).
**Action**: Inject default validator block into every coverage's `evidence_grade_policy`. Default:
```yaml
evidence_grade_policy:
  validator:
    enabled: true
    max_concurrent: 5
    full_pass_floor: corroborated
    advance_bump_cap: structured_attested
```

### 6.8 — Pydantic schema for the validator block
**File**: `infrastructure/models/config_schema.py`.
**Action**:
```python
class ValidatorPolicy(StrictModel):
    enabled: bool = True
    max_concurrent: int = Field(default=5, ge=1, le=50)
    full_pass_floor: EvidenceGradeName = "corroborated"
    advance_bump_cap: EvidenceGradeName = "structured_attested"

# Attach to EvidenceGradePolicy:
class EvidenceGradePolicy(StrictModel):
    # ... existing fields ...
    validator: ValidatorPolicy = Field(default_factory=ValidatorPolicy)
```

## Test gates

```bash
pytest tests/unit/test_validator_input_independence.py \
        tests/unit/test_validator_advance_rule.py \
        tests/unit/test_validator_persistence.py -v

# Independence smoke: ensure no production code passes raw_data/metadata to validator
! grep -rn "ValidatorInput(.*raw_data\|ValidatorInput(.*metadata" signal_architecture/ layers/

alembic upgrade head
alembic downgrade -1
alembic upgrade head

# After running one cycle end-to-end on bench, every committed signal has a grade
psql -c "SELECT COUNT(*) FROM model_version_signals WHERE evidence_grade IS NULL"
# -> 0

# Validator must have produced verdicts for eligible signals
psql -c "SELECT COUNT(*) FROM validator_verdicts"
# -> >0

pytest tests/ -x -q

# Calibration unchanged (validator promotes grades but never modifies score)
python -m layers.risk.calibration_harness aerospace cyber casualty fi fpr energy property marine pi do
```

## Done when

- [ ] `ValidatorInput` rejects `raw_data`, `metadata`, `reasoning`, `transcript`, `_*` fields.
- [ ] `compute_advance` matches the locked rule table exactly.
- [ ] `grade_after_bump` caps at `advance_bump_cap`; never exceeds.
- [ ] Workflow runs the validator, persists verdicts, re-rolls up grades, re-evaluates referrals.
- [ ] Alembic 024 applied; `model_version_signals.evidence_grade` is NOT NULL.
- [ ] Validator failure path lands a `validator_failure` entry in `compliance_audit_logs` and leaves the signal's grade unchanged.
- [ ] Calibration unchanged.
- [ ] Full pytest green.

## Out of scope

- Calibration store (extractor / validator / human triple). → Phase 7.
- Re-running the validator post-cycle on demand from the workbench. → Phase 14.
- Validator-driven promotions to `behaviourally_validated`. → out of V7; requires the reproducibility data from Phase 8 + multi-cycle history.

## Invariants

1. Validator input never carries `raw_data`, `metadata`, or any field beginning with `_`.
2. Validator can only **bump** grades — never demote.
3. Validator grade bump never exceeds `advance_bump_cap`.
4. Every validator decision is logged to `compliance_audit_logs` and persisted to `validator_verdicts`.
5. Pricing outputs unchanged: validator promotes audit-grade only, no score modification.

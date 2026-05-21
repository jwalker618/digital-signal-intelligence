"""V7 Phase 6 — persist ValidatorVerdict rows.

Thin store. Caller passes a `ValidatorVerdict` (dataclass from
signal_architecture/validation/types.py) and the originating
`grade_before`. The store builds the ORM row and stages it via
`db.add(...)` — caller commits.

Mirroring into `compliance_audit_logs` is the caller's responsibility;
the canonical event constant for that is
`EVENT_VALIDATOR_VERDICT` in `compliance_audit_store`.
"""
from __future__ import annotations

import uuid
from typing import Optional

from sqlalchemy.orm import Session

from infrastructure.db.models import ValidatorVerdictRecord
from signal_architecture.signals.evidence import EvidenceGrade
from signal_architecture.validation.types import ValidatorVerdict


def persist_verdict(
    db: Session,
    *,
    model_version_id: uuid.UUID,
    verdict: ValidatorVerdict,
    grade_before: Optional[EvidenceGrade],
) -> ValidatorVerdictRecord:
    """Build and stage a ValidatorVerdictRecord. Returns the staged row."""
    axes_payload = {
        axis: {
            "passed": result.passed,
            "confidence": result.confidence,
            "rationale": result.rationale,
        }
        for axis, result in verdict.axes.items()
    }
    row = ValidatorVerdictRecord(
        model_version_id=model_version_id,
        signal_id=verdict.signal_id,
        mode=verdict.mode,
        advance=verdict.advance,
        grade_before=grade_before,
        grade_after=verdict.grade_after_bump,
        axes=axes_payload,
        pro_argument=verdict.pro_argument,
        counter_argument=verdict.counter_argument,
        tie_breaker=verdict.tie_breaker,
        raw_response=verdict.raw_response,
        elapsed_seconds=verdict.elapsed_seconds,
        decided_at=verdict.decided_at,
    )
    db.add(row)
    return row

"""V7 Phase 7 — grade-calibration endpoints.

Three operations:

    POST /api/v1/calibration/decision   submit a human grade verdict
    GET  /api/v1/calibration/stats      rolling-window match-rate stats
    GET  /api/v1/calibration/pending    queue of pending samples

Auth: every endpoint requires ASSESSMENT_REFER permission — same scope
underwriters already use to escalate quotes.
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import List, Literal, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from infrastructure.api.auth.permissions import (
    AuthContext,
    Permission,
    require_permission,
)
from infrastructure.db.compliance_audit_store import (
    EVENT_CALIBRATION_DECISION_RECORDED,
    log_event,
)
from infrastructure.db.config import get_db
from infrastructure.db.grade_calibration_store import (
    record_human_verdict,
    stats as compute_stats,
)
from infrastructure.db.models import GradeCalibrationSample


router = APIRouter(prefix="/calibration", tags=["calibration"])


# ---------------------------------------------------------------------------
# Pydantic DTOs
# ---------------------------------------------------------------------------

EvidenceGradeName = Literal[
    "inferred", "observed", "corroborated",
    "structured_attested", "behaviourally_validated",
]


class DecisionIn(BaseModel):
    sample_id: uuid.UUID
    human_grade: EvidenceGradeName
    note: str = ""


class StatsOut(BaseModel):
    window_days: Optional[int]
    decided: int
    exact_match_extractor_rate: float
    exact_match_validator_rate: Optional[float]
    within_one_extractor_rate: float


class PendingSampleOut(BaseModel):
    id: uuid.UUID
    submission_id: uuid.UUID
    coverage: str
    signal_id: str
    signal_weight: float
    extractor_grade: str
    validator_grade: Optional[str]
    sampling_reason: str
    created_at: datetime


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("/decision", status_code=201)
def submit_decision(
    body: DecisionIn,
    db: Session = Depends(get_db),
    ctx: AuthContext = Depends(require_permission(Permission.ASSESSMENT_REFER)),
):
    """Submit a human-grade verdict for one calibration sample.

    409 if the sample has already been decided. 404 if the sample doesn't
    exist (or is in a different tenant — caller is shown 404 either way).
    """
    try:
        decision = record_human_verdict(
            db,
            sample_id=body.sample_id,
            human_grade=body.human_grade,
            decided_by=uuid.UUID(str(ctx.user_id)),
            note=body.note,
        )
    except LookupError:
        raise HTTPException(status_code=404, detail="sample not found")
    except RuntimeError as e:
        raise HTTPException(status_code=409, detail=str(e))

    log_event(
        db,
        event_type=EVENT_CALIBRATION_DECISION_RECORDED,
        payload={
            "sample_id": str(body.sample_id),
            "human_grade": body.human_grade,
            "exact_match_extractor": decision.exact_match_extractor,
            "within_one_extractor": decision.within_one_extractor,
        },
        actor=str(ctx.user_id),
    )
    db.commit()
    return {"ok": True}


@router.get("/stats", response_model=StatsOut)
def get_stats(
    coverage: Optional[str] = None,
    window_days: Optional[int] = 30,
    db: Session = Depends(get_db),
    ctx: AuthContext = Depends(require_permission(Permission.ASSESSMENT_REFER)),
):
    """Rolling-window match-rate stats. window_days=None for lifetime."""
    s = compute_stats(db, coverage=coverage, window_days=window_days)
    return StatsOut(
        window_days=s.window_days,
        decided=s.decided,
        exact_match_extractor_rate=s.exact_match_extractor_rate,
        exact_match_validator_rate=s.exact_match_validator_rate,
        within_one_extractor_rate=s.within_one_extractor_rate,
    )


@router.get("/pending", response_model=List[PendingSampleOut])
def list_pending(
    coverage: Optional[str] = None,
    limit: int = 50,
    db: Session = Depends(get_db),
    ctx: AuthContext = Depends(require_permission(Permission.ASSESSMENT_REFER)),
):
    """List pending samples scoped to (optional) coverage. Newest first."""
    limit = max(1, min(200, limit))
    q = db.query(GradeCalibrationSample).filter_by(state="pending")
    if coverage:
        q = q.filter_by(coverage=coverage)
    rows = (
        q.order_by(GradeCalibrationSample.created_at.desc())
        .limit(limit)
        .all()
    )
    return [
        PendingSampleOut(
            id=r.id,
            submission_id=r.submission_id,
            coverage=r.coverage,
            signal_id=r.signal_id,
            signal_weight=r.signal_weight,
            extractor_grade=r.extractor_grade,
            validator_grade=r.validator_grade,
            sampling_reason=r.sampling_reason,
            created_at=r.created_at,
        )
        for r in rows
    ]

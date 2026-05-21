"""V7 Phase 14 — evidence read endpoints.

Exposes the persisted V7 evidence fields:
    GET /api/v1/model-versions/{mv_id}/evidence
    GET /api/v1/model-versions/{mv_id}/signals/{signal_id}
    GET /api/v1/model-versions/{mv_id}/signals/{signal_id}/history

All endpoints gated by ASSESSMENT_READ. Tenant scoping is enforced by
the existing auth middleware via the model_version_id lookup.
"""
from __future__ import annotations

import uuid
from typing import Dict, List

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from infrastructure.api.auth.permissions import (
    AuthContext,
    Permission,
    require_permission,
)
from infrastructure.api.schemas.evidence import (
    CompositeEvidenceDTO,
    EvidenceSourceDTO,
    GradeRollupDTO,
    SignalEvidenceDTO,
    SignalHistoryRowDTO,
)
from infrastructure.db.config import get_db
from infrastructure.db.models import (
    ModelVersionRecord,
    ModelVersionSignal,
    SignalHistory,
)


router = APIRouter(prefix="/model-versions", tags=["evidence"])


def _load_mv_or_404(db: Session, mv_id: uuid.UUID) -> ModelVersionRecord:
    mv = db.query(ModelVersionRecord).get(mv_id)
    if mv is None:
        raise HTTPException(status_code=404, detail="model version not found")
    return mv


def _signal_to_dto(row: ModelVersionSignal) -> SignalEvidenceDTO:
    sources = [
        EvidenceSourceDTO(**s) if isinstance(s, dict) else s
        for s in (row.evidence_sources or [])
    ]
    return SignalEvidenceDTO(
        signal_id=str(row.signal_id),
        score=row.score,
        category=None,
        confidence=row.proxy_tier and 1.0 or 1.0,  # confidence isn't on mvs row directly
        evidence_grade=row.evidence_grade,
        evidence_basis=row.evidence_basis,
        evidence_sources=sources,
        evidence_pro=row.evidence_pro,
        evidence_counter=row.evidence_counter,
        evidence_tie_breaker=row.evidence_tie_breaker,
        absence_sub_type=row.absence_sub_type,
        primitive_type=row.primitive_type,
        # reproducibility and variant_of aren't persisted on the mvs row
        # in V7; the workbench reads them from signal_history when
        # surfacing latest state.
        reproducibility=None,
        variant_of=None,
        cluster_id=None,
    )


@router.get(
    "/{model_version_id}/evidence",
    response_model=CompositeEvidenceDTO,
    dependencies=[Depends(require_permission(Permission.ASSESSMENT_READ))],
)
def get_composite_evidence(
    model_version_id: uuid.UUID,
    db: Session = Depends(get_db),
):
    """Composite + per-group + per-primitive grade rollups in one payload."""
    mv = _load_mv_or_404(db, model_version_id)
    composite = GradeRollupDTO(
        min_grade=mv.composite_min_grade,
        weighted_mean_grade=(
            float(mv.composite_weighted_mean_grade)
            if mv.composite_weighted_mean_grade is not None
            else None
        ),
        distribution=mv.composite_grade_distribution or {},
    )
    # Per-group + per-primitive rollups currently live on the workflow's
    # ScoringResult and aren't persisted as separate columns. Surface
    # an empty dict from this endpoint until the workflow follow-up
    # persists them — frontend (Phase 15) tolerates empty dicts.
    return CompositeEvidenceDTO(
        composite=composite,
        per_group={},
        per_primitive={},
        grade_referral_reasons=[],
    )


@router.get(
    "/{model_version_id}/signals/{signal_id}",
    response_model=SignalEvidenceDTO,
    dependencies=[Depends(require_permission(Permission.ASSESSMENT_READ))],
)
def get_signal_evidence(
    model_version_id: uuid.UUID,
    signal_id: str,
    db: Session = Depends(get_db),
):
    """Per-signal evidence payload — grade, basis, pro/counter, sources."""
    row = (
        db.query(ModelVersionSignal)
        .filter(
            ModelVersionSignal.model_version_id == model_version_id,
        )
        .filter(
            # signal_id on mvs is an integer FK; we filter on the
            # ModelVersionRecord side via a separate query in
            # downstream impl. For now match against signal_history's
            # string signal_id, since the workbench identifies by that.
        )
        .first()
    )
    # Fall through to history if mvs doesn't carry a row for this signal_id
    # (handles the in-between state where mvs has integer FKs but history
    # carries the human signal_id string).
    hist = (
        db.query(SignalHistory)
        .filter(
            SignalHistory.model_version_id == model_version_id,
            SignalHistory.signal_id == signal_id,
        )
        .order_by(SignalHistory.recorded_at.desc())
        .first()
    )
    if hist is None:
        raise HTTPException(status_code=404, detail="signal not found")
    sources = [
        EvidenceSourceDTO(**s) if isinstance(s, dict) else s
        for s in (hist.evidence_sources or [])
    ]
    return SignalEvidenceDTO(
        signal_id=hist.signal_id,
        score=hist.score,
        category=hist.category,
        confidence=hist.confidence or 1.0,
        evidence_grade=hist.evidence_grade,
        evidence_basis=hist.evidence_basis,
        evidence_sources=sources,
        evidence_pro=hist.evidence_pro,
        evidence_counter=hist.evidence_counter,
        evidence_tie_breaker=hist.evidence_tie_breaker,
        absence_sub_type=hist.absence_sub_type,
        primitive_type=hist.primitive_type,
        reproducibility=None,
        variant_of=None,
        cluster_id=(hist.history_metadata or {}).get("cluster_id"),
    )


@router.get(
    "/{model_version_id}/signals/{signal_id}/history",
    response_model=List[SignalHistoryRowDTO],
    dependencies=[Depends(require_permission(Permission.ASSESSMENT_READ))],
)
def get_signal_history(
    model_version_id: uuid.UUID,
    signal_id: str,
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    """Longitudinal grade trail for one (submission, signal) pair.

    The endpoint follows the submission_id of `model_version_id` to surface
    history across ALL of that submission's cycles, not just the named
    model_version. This matches the way the workbench shows "evidence
    over time".
    """
    mv = _load_mv_or_404(db, model_version_id)
    rows = (
        db.query(SignalHistory)
        .filter(
            SignalHistory.submission_id == mv.submission_id,
            SignalHistory.signal_id == signal_id,
        )
        .order_by(SignalHistory.recorded_at.desc())
        .limit(limit)
        .all()
    )
    return [
        SignalHistoryRowDTO(
            model_version_id=str(r.model_version_id),
            recorded_at=r.recorded_at,
            evidence_grade=r.evidence_grade,
            score=r.score,
            category=r.category,
            evidence_basis=r.evidence_basis,
        )
        for r in rows
    ]

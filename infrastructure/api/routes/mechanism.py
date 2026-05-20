"""V7 Phase 14 — mechanism inspection endpoints.

GET /api/v1/mechanisms                                  — list (tenant-scoped)
GET /api/v1/model-versions/{mv_id}/signals/{signal_id}/mechanisms
                                                        — Top-K recall

Both endpoints are tenant-scoped via the AuthContext.tenant_id (the
mechanism store uses it as the JSONL subdir, so cross-tenant leakage is
impossible by construction).
"""
from __future__ import annotations

import uuid
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from infrastructure.api.auth.permissions import (
    AuthContext,
    Permission,
    require_permission,
)
from infrastructure.api.schemas.mechanism import MechanismDTO
from infrastructure.db.config import get_db
from infrastructure.db.models import ModelVersionRecord, SignalHistory
from signal_architecture.mechanism import load_all, recall


router = APIRouter(tags=["mechanism"])


def _to_dto(m) -> MechanismDTO:
    return MechanismDTO(
        id=m.id,
        summary=m.summary,
        primitive_type=m.primitive_type,
        sector_tags=list(m.sector_tags),
        tags=list(m.tags),
        what_made_it_high_grade=m.what_made_it_high_grade,
        recall_count=m.recall_count,
    )


@router.get(
    "/mechanisms",
    response_model=List[MechanismDTO],
    dependencies=[Depends(require_permission(Permission.ASSESSMENT_READ))],
)
def list_mechanisms(
    primitive_type: Optional[str] = None,
    coverage: Optional[str] = None,
    limit: int = Query(default=50, ge=1, le=200),
    ctx: AuthContext = Depends(
        require_permission(Permission.ASSESSMENT_READ)
    ),
):
    """Browse mechanisms for the caller's tenant. Optional filters."""
    rows = load_all(str(ctx.tenant_id))
    if primitive_type:
        rows = [m for m in rows if m.primitive_type == primitive_type]
    if coverage:
        rows = [m for m in rows if coverage in m.sector_tags]
    return [_to_dto(m) for m in rows[:limit]]


@router.get(
    "/model-versions/{model_version_id}/signals/{signal_id}/mechanisms",
    response_model=List[MechanismDTO],
    dependencies=[Depends(require_permission(Permission.ASSESSMENT_READ))],
)
def mechanisms_for_signal(
    model_version_id: uuid.UUID,
    signal_id: str,
    db: Session = Depends(get_db),
    ctx: AuthContext = Depends(
        require_permission(Permission.ASSESSMENT_READ)
    ),
):
    """Top-K mechanism priors most relevant to this signal.

    Uses the same recall cascade the validator uses at cycle time
    (chromadb -> tfidf -> keyword).
    """
    mv = db.query(ModelVersionRecord).get(model_version_id)
    if mv is None:
        raise HTTPException(status_code=404, detail="model version not found")
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
    rows = recall(
        str(ctx.tenant_id),
        primitive_type=hist.primitive_type or "unknown",
        coverage=mv.coverage or "",
        query_text=(hist.evidence_basis or ""),
        top_k=3,
    )
    return [_to_dto(m) for m in rows]

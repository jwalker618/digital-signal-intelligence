"""V7 Phase 13 — manual delta-recompute endpoint.

Underwriter / operator triggers a targeted recompute on a submission by
listing signal_ids and/or primitive_types. The endpoint INSERTS an
entity_event with type=manual_recompute and a payload that the worker
uses to compute the blast radius (signal_ids feed `hinted_signal_id`;
primitive_types are translated to signal_ids at dispatch time via the
submission's coverage registry).

Auth: ASSESSMENT_REFER — same scope underwriters already hold.
"""
from __future__ import annotations

import uuid
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from infrastructure.api.auth.permissions import (
    AuthContext,
    Permission,
    require_permission,
)
from infrastructure.db.config import get_db
from infrastructure.recompute.dispatcher import receive_event


router = APIRouter(prefix="/recompute", tags=["recompute"])


class ManualRecomputeRequest(BaseModel):
    submission_id: uuid.UUID
    entity_id: str
    signal_ids: List[str] = []
    primitive_types: List[str] = []
    note: str = ""


@router.post("", status_code=202)
def manual_recompute(
    body: ManualRecomputeRequest,
    db: Session = Depends(get_db),
    ctx: AuthContext = Depends(require_permission(Permission.ASSESSMENT_REFER)),
):
    """Queue a manual recompute. 400 if both filter lists empty."""
    if not body.signal_ids and not body.primitive_types:
        raise HTTPException(
            status_code=400,
            detail="supply signal_ids and/or primitive_types",
        )
    receive_event(
        db,
        event_type="manual_recompute",
        source_feed="manual",
        entity_id=body.entity_id,
        submission_id=body.submission_id,
        payload={
            "signal_ids": body.signal_ids,
            "primitive_types": body.primitive_types,
            "note": body.note,
            "requested_by": str(ctx.user_id),
        },
        hinted_signal_id=(body.signal_ids[0] if body.signal_ids else None),
    )
    db.commit()
    return {"queued": True}

"""V7 Phase 14 — entity-event read endpoint.

`GET /api/v1/submissions/{submission_id}/entity-events`
Lists recent entity events for one submission — what triggered a delta
recompute, when it dispatched, and which signals it touched.

Phase 13 wrote the events; this phase exposes them.
"""
from __future__ import annotations

import uuid
from typing import List

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from infrastructure.api.auth.permissions import Permission, require_permission
from infrastructure.api.schemas.entity_event import EntityEventDTO
from infrastructure.db.config import get_db
from infrastructure.db.models import EntityEvent


router = APIRouter(prefix="/submissions", tags=["events"])


@router.get(
    "/{submission_id}/entity-events",
    response_model=List[EntityEventDTO],
    dependencies=[Depends(require_permission(Permission.ASSESSMENT_READ))],
)
def list_entity_events(
    submission_id: uuid.UUID,
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    rows = (
        db.query(EntityEvent)
        .filter(EntityEvent.submission_id == submission_id)
        .order_by(EntityEvent.received_at.desc())
        .limit(limit)
        .all()
    )
    return [
        EntityEventDTO(
            id=r.id,
            event_type=r.event_type,
            source_feed=r.source_feed,
            received_at=r.received_at,
            dispatched_at=r.dispatched_at,
            blast_radius=list(r.blast_radius or []),
            resulting_model_version_id=r.resulting_model_version_id,
            payload=dict(r.payload or {}),
        )
        for r in rows
    ]

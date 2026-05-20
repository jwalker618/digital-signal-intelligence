"""V7 Phase 14 — commitment verification endpoint.

`POST /api/v1/model-versions/{mv_id}/verify-commitment` accepts a candidate
payload and returns whether its canonical-SHA3-224 matches the stored
commitment. The endpoint always returns the computed digest so the caller
can debug a mismatch.
"""
from __future__ import annotations

import uuid
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from infrastructure.api.auth.permissions import (
    AuthContext,
    Permission,
    require_permission,
)
from infrastructure.db.commitment_store import sha3_224, verify
from infrastructure.db.config import get_db


router = APIRouter(prefix="/model-versions", tags=["commitments"])


class VerifyIn(BaseModel):
    signal_id: Optional[str] = None
    scope: str  # full_payload | value_and_grade | pro_counter | composite
    candidate_payload: Dict[str, Any]


class VerifyOut(BaseModel):
    ok: bool
    digest_computed: str


@router.post(
    "/{model_version_id}/verify-commitment",
    response_model=VerifyOut,
    dependencies=[Depends(require_permission(Permission.ASSESSMENT_READ))],
)
def verify_commitment(
    model_version_id: uuid.UUID,
    body: VerifyIn,
    db: Session = Depends(get_db),
):
    """True iff the stored digest matches sha3_224(candidate_payload)."""
    ok = verify(
        db,
        model_version_id=model_version_id,
        signal_id=body.signal_id,
        scope=body.scope,  # type: ignore[arg-type]
        candidate_payload=body.candidate_payload,
    )
    return VerifyOut(ok=ok, digest_computed=sha3_224(body.candidate_payload))

"""V7 Phase 14 — disclosure packet endpoint.

`POST /api/v1/model-versions/{mv_id}/disclosure-packet`
Returns a templated underwriter disclosure packet.

  format=json (default): returns {markdown, payload}
  format=md            : returns text/markdown body directly

The endpoint prefers a cached packet (stored on referrals.disclosure_packet
when a grade referral fires) over re-generation, since packets are
deterministic for a given model_version_id. Falls back to fresh generation
when no cached payload exists.
"""
from __future__ import annotations

import uuid
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Response
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from infrastructure.api.auth.permissions import (
    AuthContext,
    Permission,
    require_permission,
)
from infrastructure.api.schemas.disclosure import DisclosureResponse
from infrastructure.db.commitment_store import sha3_224
from infrastructure.db.config import get_db
from infrastructure.db.models import (
    ModelVersionRecord,
    Quote,
    Referral,
    SignalHistory,
)
from signal_architecture.disclosure import PacketSection, build_packet


router = APIRouter(prefix="/model-versions", tags=["disclosure"])


def _load_cached_packet(
    db: Session,
    model_version_id: uuid.UUID,
) -> Optional[Dict[str, Any]]:
    """Look for a referral with a stored disclosure_packet for this mv."""
    row = (
        db.query(Referral)
        .join(Quote, Referral.quote_id == Quote.id)
        .filter(Quote.model_version_id == model_version_id)
        .filter(Referral.disclosure_packet.isnot(None))
        .first()
    )
    return row.disclosure_packet if row is not None else None


def _build_sections(
    db: Session,
    model_version_id: uuid.UUID,
) -> List[PacketSection]:
    """One section per signal_history row for this model_version."""
    hist_rows = (
        db.query(SignalHistory)
        .filter(SignalHistory.model_version_id == model_version_id)
        .order_by(SignalHistory.recorded_at.desc())
        .all()
    )
    sections: List[PacketSection] = []
    for h in hist_rows:
        sources = [
            s if isinstance(s, dict) else getattr(s, "__dict__", {})
            for s in (h.evidence_sources or [])
        ]
        sym = (h.history_metadata or {}).get("symptoms") or []
        commitment = sha3_224({
            "signal_id": h.signal_id,
            "score": h.score,
            "category": h.category,
            "evidence_grade": h.evidence_grade,
        })
        sections.append(PacketSection(
            title=h.signal_id.replace("_", " ").title(),
            signal_id=h.signal_id,
            grade=h.evidence_grade or "unknown",
            pro=h.evidence_pro or "",
            counter=h.evidence_counter or "",
            tie_breaker=h.evidence_tie_breaker or "",
            sources=sources,
            cluster_symptoms=sym if isinstance(sym, list) else [],
            recalled_mechanisms=[],  # filled in by route-layer follow-up
            commitment_digest=commitment,
            reproducibility=None,
        ))
    return sections


@router.post(
    "/{model_version_id}/disclosure-packet",
    dependencies=[Depends(require_permission(Permission.ASSESSMENT_READ))],
)
def generate_packet(
    model_version_id: uuid.UUID,
    format: str = "json",  # noqa: A002 — FastAPI convention
    db: Session = Depends(get_db),
):
    """Generate or return the cached disclosure packet."""
    mv = db.query(ModelVersionRecord).get(model_version_id)
    if mv is None:
        raise HTTPException(status_code=404, detail="model version not found")

    cached = _load_cached_packet(db, model_version_id)
    if cached is not None and "markdown" in cached and "payload" in cached:
        md = cached["markdown"]
        payload = cached["payload"]
    else:
        sections = _build_sections(db, model_version_id)
        md, payload = build_packet(
            model_version_id=model_version_id,
            composite_min_grade=mv.composite_min_grade,
            composite_distribution=dict(mv.composite_grade_distribution or {}),
            referral_reasons=[],  # filled in by route-layer follow-up
            sections=sections,
        )

    if format == "md":
        return Response(content=md, media_type="text/markdown")
    return JSONResponse(
        content=DisclosureResponse(markdown=md, payload=payload).model_dump()
    )

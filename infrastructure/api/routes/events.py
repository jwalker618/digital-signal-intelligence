"""V7 Phase 13 — external-feed webhook receivers.

Three endpoints — one per supported feed. Each:
  1. Reads the raw body (so HMAC verification has the exact bytes).
  2. Verifies the per-feed HMAC against an env-stored secret.
  3. Parses the body into receive_event() kwargs via the adapter.
  4. Inserts an entity_events row (dedup-by-key prevents double-fire).

Unsigned or malformed requests get 401. The actual dispatch + recompute
runs out-of-band in the worker (dispatcher.dispatch_due).
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from sqlalchemy.orm import Session

from infrastructure.db.config import get_db
from infrastructure.recompute.adapters import (
    companies_house,
    ofac,
    sec_edgar,
)
from infrastructure.recompute.dispatcher import receive_event


router = APIRouter(prefix="/events/external", tags=["events"])


@router.post("/sec_edgar")
async def sec_edgar_webhook(
    req: Request,
    x_signature: str = Header(default=""),
    db: Session = Depends(get_db),
):
    raw = await req.body()
    if not sec_edgar.verify_hmac(raw, x_signature):
        raise HTTPException(status_code=401, detail="invalid signature")
    receive_event(db, **sec_edgar.parse(raw))
    db.commit()
    return {"ok": True}


@router.post("/companies_house")
async def companies_house_webhook(
    req: Request,
    x_signature: str = Header(default=""),
    db: Session = Depends(get_db),
):
    raw = await req.body()
    if not companies_house.verify_hmac(raw, x_signature):
        raise HTTPException(status_code=401, detail="invalid signature")
    receive_event(db, **companies_house.parse(raw))
    db.commit()
    return {"ok": True}


@router.post("/ofac")
async def ofac_webhook(
    req: Request,
    x_signature: str = Header(default=""),
    db: Session = Depends(get_db),
):
    raw = await req.body()
    if not ofac.verify_hmac(raw, x_signature):
        raise HTTPException(status_code=401, detail="invalid signature")
    receive_event(db, **ofac.parse(raw))
    db.commit()
    return {"ok": True}

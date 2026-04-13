"""A-4d: Push notification API.

Tenant-scoped; all endpoints require an authenticated user.

    GET  /push/vapid-public-key   Public VAPID key for browser subscribe()
    POST /push/subscribe          Register a new subscription
    POST /push/unsubscribe        Remove a subscription (by endpoint)
    GET  /push/preferences        Effective preferences (defaults filled in)
    PUT  /push/preferences        Upsert a batch of preference changes
    POST /push/test               Deliver a test push to self
"""

from __future__ import annotations

import logging
import os
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from infrastructure.api.auth.permissions import AuthContext, get_auth_context
from infrastructure.api.push.categories import NotificationCategory
from infrastructure.api.push.service import PushPayload, PushService
from infrastructure.api.websocket import get_connection_manager
from infrastructure.db.config import get_db

logger = logging.getLogger("dsi.api.push.routes")
router = APIRouter()


def _service(db: Session) -> PushService:
    return PushService(db, connection_manager=get_connection_manager())


# =============================================================================
# Schemas
# =============================================================================


class SubscribeRequest(BaseModel):
    endpoint: str = Field(min_length=1, max_length=2048)
    p256dh_key: str = Field(min_length=1, max_length=1024)
    auth_key: str = Field(min_length=1, max_length=1024)
    user_agent: Optional[str] = Field(default=None, max_length=512)


class UnsubscribeRequest(BaseModel):
    endpoint: str = Field(min_length=1, max_length=2048)


class CategoryToggle(BaseModel):
    push: Optional[bool] = None
    in_app: Optional[bool] = None
    email: Optional[bool] = None


class PreferencesUpdateRequest(BaseModel):
    # category string -> toggles. Unknown categories are ignored.
    updates: dict[str, CategoryToggle]


class SendTestPushRequest(BaseModel):
    title: Optional[str] = None
    body: Optional[str] = None


# =============================================================================
# Routes
# =============================================================================


@router.get("/push/vapid-public-key")
def get_vapid_public_key() -> dict:
    key = os.getenv("VAPID_PUBLIC_KEY", "")
    return {"public_key": key}


@router.post("/push/subscribe", status_code=204)
def subscribe(
    body: SubscribeRequest,
    ctx: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
):
    if not ctx.user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")
    _service(db).register_subscription(
        user_id=ctx.user_id,
        tenant_id=ctx.tenant_id,
        endpoint=body.endpoint,
        p256dh_key=body.p256dh_key,
        auth_key=body.auth_key,
        user_agent=body.user_agent,
    )
    db.commit()
    return None


@router.post("/push/unsubscribe", status_code=204)
def unsubscribe(
    body: UnsubscribeRequest,
    ctx: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
):
    if not ctx.user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")
    _service(db).remove_subscription(user_id=ctx.user_id, endpoint=body.endpoint)
    db.commit()
    return None


@router.get("/push/preferences")
def get_preferences(
    ctx: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
) -> dict:
    if not ctx.user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return {"preferences": _service(db).list_preferences(ctx.user_id)}


@router.put("/push/preferences")
def update_preferences(
    body: PreferencesUpdateRequest,
    ctx: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
) -> dict:
    if not ctx.user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")
    svc = _service(db)
    # Merge client input with current preferences so partial toggles don't
    # overwrite the unspecified flags.
    current = svc.list_preferences(ctx.user_id)
    merged: dict[NotificationCategory, dict[str, bool]] = {}
    for cat_str, toggles in body.updates.items():
        try:
            category = NotificationCategory(cat_str)
        except ValueError:
            continue
        existing = current.get(cat_str, {"push": True, "in_app": True, "email": False})
        merged[category] = {
            "push": toggles.push if toggles.push is not None else existing["push"],
            "in_app": toggles.in_app
            if toggles.in_app is not None
            else existing["in_app"],
            "email": toggles.email
            if toggles.email is not None
            else existing["email"],
        }
    if merged:
        svc.set_preferences(ctx.user_id, ctx.tenant_id, merged)
    db.commit()
    return {"preferences": svc.list_preferences(ctx.user_id)}


@router.post("/push/test")
def send_test(
    body: SendTestPushRequest,
    ctx: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
) -> dict:
    """Deliver a test push to the caller's own subscriptions.

    Bypasses the online/preference checks -- the point is to verify the
    subscription round-trip works end-to-end.
    """
    if not ctx.user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")
    payload = PushPayload(
        category=NotificationCategory.ASSESSMENT_COMPLETE,
        title=body.title or "DSI test notification",
        body=body.body or "Your push subscription is working.",
        url="/profile",
    )
    delivered = _service(db).send(user_id=ctx.user_id, payload=payload)
    return {"delivered": delivered}

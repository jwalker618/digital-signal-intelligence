"""v8 Phase 6: portal-specific FastAPI dependencies.

Two scoping levels:
  - require_portal_user(): require BROKER or CLIENT role
  - scoped_submission(): resolve a submission by submission_code and
    assert the requesting user can see it
      * BROKER: submission.broker_id == user.broker_id
      * CLIENT: submission.created_by_user.tenant_id == user.tenant_id

Carrier-side roles get 403 from require_portal_user so the portal is
never accessible to underwriters or admins under the dev shortcut.
"""
from __future__ import annotations

import uuid
from typing import Optional

from fastapi import Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from infrastructure.api.auth.permissions import AuthContext, get_auth_context
from infrastructure.db.config import get_async_db
from infrastructure.db.models import Submission, User


_PORTAL_ROLES = {"BROKER", "CLIENT"}


async def require_portal_user(
    ctx: AuthContext = Depends(get_auth_context),
) -> AuthContext:
    """Reject any user whose role isn't BROKER or CLIENT.

    Carrier roles (UNDERWRITER, ADMIN, etc.) get 403 even when the dev
    shortcut hands them other permissions -- portal is a separate
    surface intentionally.
    """
    if ctx.role not in _PORTAL_ROLES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Portal access requires BROKER or CLIENT role",
        )
    return ctx


async def get_user_record(
    ctx: AuthContext, db: AsyncSession
) -> Optional[User]:
    """Look up the User row for the auth context. None on missing."""
    if not ctx.user_id:
        return None
    try:
        uid = uuid.UUID(ctx.user_id)
    except (ValueError, TypeError):
        return None
    result = await db.execute(select(User).where(User.id == uid))
    return result.scalar_one_or_none()


async def scoped_submission(
    submission_code: str,
    db: AsyncSession = Depends(get_async_db),
    ctx: AuthContext = Depends(require_portal_user),
) -> Submission:
    """Resolve a submission by submission_code and assert the user can see it.

    Raises 404 on missing, 403 on scope mismatch.

    The dependency itself doesn't return the user record -- routes that
    need both call get_user_record separately. This keeps the dependency
    signature simple.
    """
    q = await db.execute(
        select(Submission).where(Submission.submission_code == submission_code)
    )
    submission = q.scalar_one_or_none()
    if submission is None:
        raise HTTPException(status_code=404, detail="Submission not found")

    if ctx.role == "BROKER":
        user = await get_user_record(ctx, db)
        if user is None or user.broker_id is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Broker identity not configured for this user",
            )
        if submission.broker_id != user.broker_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Submission not in your book of clients",
            )

    elif ctx.role == "CLIENT":
        # Client can see submissions in their own tenant. Determine the
        # submission's tenant via its created_by_user.tenant_id.
        if submission.created_by is None:
            # Legacy submission, no creator; clients can't see it.
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Submission ownership not established",
            )
        creator_q = await db.execute(
            select(User.tenant_id).where(User.id == submission.created_by)
        )
        creator_tenant_id = creator_q.scalar_one_or_none()
        try:
            ctx_tenant = uuid.UUID(ctx.tenant_id) if ctx.tenant_id else None
        except (ValueError, TypeError):
            ctx_tenant = None
        if creator_tenant_id is None or creator_tenant_id != ctx_tenant:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Submission not in your tenant",
            )

    return submission

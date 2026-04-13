"""
B-3d: Admin user + role + permission management endpoints.

All endpoints require admin:users permission EXCEPT /accept-invitation
which is public (listed in tenant_middleware.PUBLIC_PATH_PREFIXES so the
invitee does not need to authenticate to complete registration).

Endpoints:

Users:
    GET  /admin/users                     List tenant users
    GET  /admin/users/{user_id}           User detail
    POST /admin/users                     Create directly (no invite)
    PUT  /admin/users/{user_id}           Update name / role / active
    POST /admin/users/{user_id}/deactivate

Invitations:
    POST /admin/users/invite              Send an invitation
    GET  /admin/users/invitations         List pending invitations
    POST /admin/users/invitations/{id}/cancel
    POST /auth/accept-invitation          PUBLIC: complete registration

Roles:
    GET    /admin/roles
    GET    /admin/roles/{role_id}
    POST   /admin/roles
    PUT    /admin/roles/{role_id}
    DELETE /admin/roles/{role_id}

Permissions:
    GET /admin/permissions                All available permissions
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.orm import Session

from infrastructure.admin import (
    InvitationService,
    RoleService,
    UserService,
)
from infrastructure.api.audit import (
    AuditActionType,
    AuditService,
    audit_from_request,
    push_enabled,
)
from infrastructure.api.auth.permissions import (
    AuthContext,
    Permission,
    get_auth_context,
    get_permission_domains,
    require_permission,
)
from infrastructure.api.websocket import get_connection_manager
from infrastructure.db.config import get_db

logger = logging.getLogger("dsi.api.admin.users")
router = APIRouter()


def _broadcast_svc(db: Session) -> AuditService:
    return AuditService(
        db,
        broadcaster=get_connection_manager(),
        push_enabled=push_enabled(),
    )


# =============================================================================
# Schemas
# =============================================================================


EMAIL_PATTERN = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"


class UserResponse(BaseModel):
    id: str
    email: str
    full_name: Optional[str]
    role_id: Optional[str]
    role_name: Optional[str]
    is_active: bool
    mfa_enabled: bool
    is_locked: bool
    last_login: Optional[datetime]
    created_at: Optional[datetime]


class UserCreateRequest(BaseModel):
    email: str = Field(pattern=EMAIL_PATTERN)
    full_name: str = Field(min_length=1, max_length=255)
    role_id: str
    password: str = Field(min_length=12, max_length=128)


class UserUpdateRequest(BaseModel):
    full_name: Optional[str] = None
    role_id: Optional[str] = None
    is_active: Optional[bool] = None


class InviteRequest(BaseModel):
    email: str = Field(pattern=EMAIL_PATTERN)
    role_id: str


class InvitationResponse(BaseModel):
    invitation_id: str
    email: str
    expires_at: datetime
    # The raw token is only returned on send (shown once).
    token: Optional[str] = None


class AcceptInvitationRequest(BaseModel):
    token: str = Field(min_length=1)
    full_name: str = Field(min_length=1)
    password: str = Field(min_length=12, max_length=128)


class RoleResponse(BaseModel):
    id: str
    name: str
    description: Optional[str]
    permissions: list[str]
    is_system_role: bool
    user_count: int = 0


class RoleCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    description: Optional[str] = None
    permissions: list[str] = Field(default_factory=list)

    @field_validator("name")
    @classmethod
    def _uppercase(cls, v: str) -> str:
        return v.upper()


class RoleUpdateRequest(BaseModel):
    description: Optional[str] = None
    permissions: Optional[list[str]] = None


# =============================================================================
# Helpers
# =============================================================================


def _user_to_response(user, role_name: Optional[str]) -> UserResponse:
    return UserResponse(
        id=str(user.id),
        email=user.email,
        full_name=user.full_name,
        role_id=str(user.role_id) if user.role_id else None,
        role_name=role_name,
        is_active=bool(user.is_active),
        mfa_enabled=bool(user.mfa_enabled),
        is_locked=bool(user.is_locked),
        last_login=user.last_login,
        created_at=user.created_at,
    )


def _role_to_response(role, user_count: int) -> RoleResponse:
    return RoleResponse(
        id=str(role.id),
        name=role.name,
        description=role.description,
        permissions=list(role.permissions or []),
        is_system_role=bool(role.is_system_role),
        user_count=user_count,
    )


# =============================================================================
# User endpoints
# =============================================================================


@router.get(
    "/admin/users",
    response_model=list[UserResponse],
    dependencies=[Depends(require_permission(Permission.ADMIN_USERS))],
)
def list_users(
    role: Optional[str] = None,
    is_active: Optional[bool] = None,
    search: Optional[str] = None,
    limit: int = Query(default=200, ge=1, le=1000),
    ctx: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
) -> list[UserResponse]:
    svc = UserService(db)
    users = svc.list_users(
        tenant_id=ctx.tenant_id,
        role_name=role,
        is_active=is_active,
        search=search,
        limit=limit,
    )
    # Bulk-load role names for the response
    role_names = {}
    from infrastructure.db.models import Role
    from sqlalchemy import select
    role_ids = {u.role_id for u in users if u.role_id is not None}
    if role_ids:
        rows = db.execute(select(Role).where(Role.id.in_(role_ids))).scalars().all()
        role_names = {str(r.id): r.name for r in rows}

    return [
        _user_to_response(
            u, role_names.get(str(u.role_id)) if u.role_id else None
        )
        for u in users
    ]


@router.get(
    "/admin/users/{user_id}",
    response_model=UserResponse,
    dependencies=[Depends(require_permission(Permission.ADMIN_USERS))],
)
def get_user(
    user_id: str,
    ctx: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
) -> UserResponse:
    user = UserService(db).get_user(ctx.tenant_id, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    role_name = None
    if user.role_id:
        from infrastructure.db.models import Role
        role = db.execute(
            __import__("sqlalchemy").select(Role).where(Role.id == user.role_id)
        ).scalar_one_or_none()
        role_name = role.name if role else None
    return _user_to_response(user, role_name)


@router.post(
    "/admin/users",
    response_model=UserResponse,
    status_code=201,
    dependencies=[Depends(require_permission(Permission.ADMIN_USERS))],
)
def create_user(
    body: UserCreateRequest,
    request: Request,
    ctx: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
) -> UserResponse:
    svc = UserService(db)
    try:
        user = svc.create_user(
            tenant_id=ctx.tenant_id,
            email=body.email,
            full_name=body.full_name,
            role_id=body.role_id,
            password=body.password,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    _broadcast_svc(db).record(
        audit_from_request(
            request,
            action_type=AuditActionType.USER_CREATE,
            resource_type="user",
            resource_id=str(user.id),
            after_state={"email": user.email, "role_id": str(user.role_id), "is_active": True},
        )
    )
    db.commit()

    from infrastructure.db.models import Role
    from sqlalchemy import select
    role = db.execute(select(Role).where(Role.id == user.role_id)).scalar_one_or_none()
    return _user_to_response(user, role.name if role else None)


@router.put(
    "/admin/users/{user_id}",
    response_model=UserResponse,
    dependencies=[Depends(require_permission(Permission.ADMIN_USERS))],
)
def update_user(
    user_id: str,
    body: UserUpdateRequest,
    request: Request,
    ctx: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
) -> UserResponse:
    svc = UserService(db)
    before = svc.get_user(ctx.tenant_id, user_id)
    if before is None:
        raise HTTPException(status_code=404, detail="User not found")
    try:
        user = svc.update_user(
            tenant_id=ctx.tenant_id,
            user_id=user_id,
            full_name=body.full_name,
            role_id=body.role_id,
            is_active=body.is_active,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    action = AuditActionType.PERMISSION_CHANGE if body.role_id else AuditActionType.USER_EDIT
    _broadcast_svc(db).record(
        audit_from_request(
            request,
            action_type=action,
            resource_type="user",
            resource_id=str(user.id),
            before_state={
                "full_name": before.full_name,
                "role_id": str(before.role_id) if before.role_id else None,
                "is_active": before.is_active,
            },
            after_state={
                "full_name": user.full_name,
                "role_id": str(user.role_id) if user.role_id else None,
                "is_active": user.is_active,
            },
        )
    )
    db.commit()

    from infrastructure.db.models import Role
    from sqlalchemy import select
    role = db.execute(select(Role).where(Role.id == user.role_id)).scalar_one_or_none() if user.role_id else None
    return _user_to_response(user, role.name if role else None)


@router.post(
    "/admin/users/{user_id}/deactivate",
    dependencies=[Depends(require_permission(Permission.ADMIN_USERS))],
)
def deactivate_user(
    user_id: str,
    request: Request,
    ctx: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
):
    svc = UserService(db)
    try:
        user = svc.deactivate_user(ctx.tenant_id, user_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    _broadcast_svc(db).record(
        audit_from_request(
            request,
            action_type=AuditActionType.USER_DEACTIVATE,
            resource_type="user",
            resource_id=str(user.id),
            after_state={"is_active": False},
        )
    )
    db.commit()
    return {"user_id": str(user.id), "is_active": False}


# =============================================================================
# Invitation endpoints
# =============================================================================


@router.post(
    "/admin/users/invite",
    response_model=InvitationResponse,
    dependencies=[Depends(require_permission(Permission.ADMIN_USERS))],
)
def send_invitation(
    body: InviteRequest,
    request: Request,
    ctx: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
) -> InvitationResponse:
    svc = InvitationService(db)
    try:
        result = svc.send(
            tenant_id=ctx.tenant_id,
            email=body.email,
            role_id=body.role_id,
            inviter_id=ctx.user_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    _broadcast_svc(db).record(
        audit_from_request(
            request,
            action_type=AuditActionType.USER_CREATE,
            resource_type="user_invitation",
            resource_id=result.invitation_id,
            after_state={"email": body.email, "role_id": body.role_id},
        )
    )
    db.commit()
    return InvitationResponse(
        invitation_id=result.invitation_id,
        email=body.email,
        expires_at=result.expires_at,
        token=result.token,
    )


@router.get(
    "/admin/users/invitations",
    dependencies=[Depends(require_permission(Permission.ADMIN_USERS))],
)
def list_invitations(
    ctx: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
):
    invites = InvitationService(db).list_pending(ctx.tenant_id)
    return {
        "invitations": [
            {
                "id": str(inv.id),
                "email": inv.email,
                "role_id": str(inv.role_id) if inv.role_id else None,
                "expires_at": inv.expires_at.isoformat() if inv.expires_at else None,
                "created_at": inv.created_at.isoformat() if inv.created_at else None,
            }
            for inv in invites
        ],
        "count": len(invites),
    }


@router.post(
    "/admin/users/invitations/{invitation_id}/cancel",
    dependencies=[Depends(require_permission(Permission.ADMIN_USERS))],
)
def cancel_invitation(
    invitation_id: str,
    ctx: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
):
    try:
        InvitationService(db).cancel(ctx.tenant_id, invitation_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    db.commit()
    return {"invitation_id": invitation_id, "cancelled": True}


@router.post("/auth/accept-invitation")
def accept_invitation(
    body: AcceptInvitationRequest,
    db: Session = Depends(get_db),
):
    """PUBLIC endpoint: complete registration via invitation token.

    Returns the new user's email + tenant id. The frontend then directs
    the user to log in normally.
    """
    svc = InvitationService(db)
    try:
        user = svc.accept(
            raw_token=body.token,
            full_name=body.full_name,
            password=body.password,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    db.commit()
    return {
        "user_id": str(user.id),
        "email": user.email,
        "tenant_id": str(user.tenant_id),
    }


# =============================================================================
# Role endpoints
# =============================================================================


@router.get(
    "/admin/roles",
    response_model=list[RoleResponse],
    dependencies=[Depends(require_permission(Permission.ADMIN_USERS))],
)
def list_roles(
    ctx: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
) -> list[RoleResponse]:
    svc = RoleService(db)
    roles = svc.list_roles(ctx.tenant_id)
    # User counts per role
    from sqlalchemy import func, select
    from infrastructure.db.models import User
    counts: dict[str, int] = {}
    if roles:
        role_ids = [r.id for r in roles]
        rows = db.execute(
            select(User.role_id, func.count(User.id))
            .where(User.role_id.in_(role_ids))
            .group_by(User.role_id)
        ).all()
        counts = {str(r[0]): int(r[1]) for r in rows}
    return [_role_to_response(r, counts.get(str(r.id), 0)) for r in roles]


@router.get(
    "/admin/roles/{role_id}",
    response_model=RoleResponse,
    dependencies=[Depends(require_permission(Permission.ADMIN_USERS))],
)
def get_role(
    role_id: str,
    ctx: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
) -> RoleResponse:
    svc = RoleService(db)
    role = svc.get_role(ctx.tenant_id, role_id)
    if role is None:
        raise HTTPException(status_code=404, detail="Role not found")

    from sqlalchemy import func, select
    from infrastructure.db.models import User
    user_count = db.execute(
        select(func.count()).select_from(User).where(User.role_id == role.id)
    ).scalar() or 0
    return _role_to_response(role, int(user_count))


@router.post(
    "/admin/roles",
    response_model=RoleResponse,
    status_code=201,
    dependencies=[Depends(require_permission(Permission.ADMIN_USERS))],
)
def create_role(
    body: RoleCreateRequest,
    request: Request,
    ctx: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
) -> RoleResponse:
    svc = RoleService(db)
    try:
        role = svc.create_role(
            tenant_id=ctx.tenant_id,
            name=body.name,
            permissions=body.permissions,
            description=body.description,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    _broadcast_svc(db).record(
        audit_from_request(
            request,
            action_type=AuditActionType.ROLE_CREATE,
            resource_type="role",
            resource_id=str(role.id),
            after_state={"name": role.name, "permissions": role.permissions},
        )
    )
    db.commit()
    return _role_to_response(role, 0)


@router.put(
    "/admin/roles/{role_id}",
    response_model=RoleResponse,
    dependencies=[Depends(require_permission(Permission.ADMIN_USERS))],
)
def update_role(
    role_id: str,
    body: RoleUpdateRequest,
    request: Request,
    ctx: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
) -> RoleResponse:
    svc = RoleService(db)
    before = svc.get_role(ctx.tenant_id, role_id)
    if before is None:
        raise HTTPException(status_code=404, detail="Role not found")

    try:
        role = svc.update_role(
            tenant_id=ctx.tenant_id,
            role_id=role_id,
            permissions=body.permissions,
            description=body.description,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    _broadcast_svc(db).record(
        audit_from_request(
            request,
            action_type=AuditActionType.ROLE_EDIT,
            resource_type="role",
            resource_id=str(role.id),
            before_state={"permissions": list(before.permissions or [])},
            after_state={"permissions": list(role.permissions or [])},
        )
    )
    db.commit()

    from sqlalchemy import func, select
    from infrastructure.db.models import User
    user_count = db.execute(
        select(func.count()).select_from(User).where(User.role_id == role.id)
    ).scalar() or 0
    return _role_to_response(role, int(user_count))


@router.delete(
    "/admin/roles/{role_id}",
    dependencies=[Depends(require_permission(Permission.ADMIN_USERS))],
)
def delete_role(
    role_id: str,
    request: Request,
    ctx: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
):
    svc = RoleService(db)
    before = svc.get_role(ctx.tenant_id, role_id)
    if before is None:
        raise HTTPException(status_code=404, detail="Role not found")
    try:
        svc.delete_role(ctx.tenant_id, role_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    _broadcast_svc(db).record(
        audit_from_request(
            request,
            action_type=AuditActionType.ROLE_EDIT,
            resource_type="role",
            resource_id=role_id,
            before_state={"name": before.name, "permissions": list(before.permissions or [])},
            after_state={"deleted": True},
        )
    )
    db.commit()
    return {"role_id": role_id, "deleted": True}


# =============================================================================
# Permissions (read-only enumeration)
# =============================================================================


@router.get(
    "/admin/permissions",
    dependencies=[Depends(require_permission(Permission.ADMIN_USERS))],
)
def list_permissions() -> dict:
    """All available permissions grouped by domain, for the role editor."""
    return {
        "domains": get_permission_domains(),
        "permissions": [p.value for p in Permission],
    }

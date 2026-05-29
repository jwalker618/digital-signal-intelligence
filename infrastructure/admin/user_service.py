"""
B-3b: UserService + RoleService + InvitationService

Tenant-scoped admin operations for user + role management. All methods
assume a tenant context -- callers (the API routes) pass the acting
user's tenant_id and we enforce scoping here.

Invariants protected at the service layer:
- Cannot deactivate the last active ADMIN in a tenant.
- Cannot delete a role that has users assigned.
- Cannot delete a system role.
- Roles are tenant-scoped -- custom roles live only within their tenant.
"""

from __future__ import annotations

import hashlib
import logging
import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from infrastructure.db.models import Role, Tenant, User, UserInvitation


def _hash_password(plaintext: str) -> str:
    """Lazy import to avoid infrastructure.api -> admin -> api cycle."""
    from infrastructure.api.auth.jwt_auth import hash_password
    return hash_password(plaintext)

logger = logging.getLogger("dsi.admin.user_service")


# Invitation tokens live for 7 days.
INVITATION_TTL_DAYS = 7


@dataclass
class InvitationToken:
    """Result of sending an invitation -- includes the raw token (shown once)."""
    invitation_id: str
    token: str       # raw single-use token (caller emails this)
    expires_at: datetime


# ==========================================================================
# UserService
# ==========================================================================


class UserService:
    """Tenant-scoped CRUD for users."""

    def __init__(self, db: Session):
        self.db = db

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------

    def list_users(
        self,
        tenant_id: str,
        role_name: Optional[str] = None,
        is_active: Optional[bool] = None,
        search: Optional[str] = None,
        limit: int = 200,
    ) -> list[User]:
        stmt = select(User).where(User.tenant_id == UUID(tenant_id))

        if role_name:
            role_subquery = select(Role.id).where(
                Role.tenant_id == UUID(tenant_id), Role.name == role_name
            )
            stmt = stmt.where(User.role_id.in_(role_subquery))
        if is_active is not None:
            stmt = stmt.where(User.is_active == is_active)
        if search:
            pattern = f"%{search.lower()}%"
            stmt = stmt.where(
                (func.lower(User.email).like(pattern))
                | (func.lower(User.full_name).like(pattern))
            )

        stmt = stmt.order_by(User.created_at.desc()).limit(limit)
        return list(self.db.execute(stmt).scalars().all())

    def get_user(self, tenant_id: str, user_id: str) -> Optional[User]:
        return self.db.execute(
            select(User).where(
                User.tenant_id == UUID(tenant_id),
                User.id == UUID(user_id),
            )
        ).scalar_one_or_none()

    def get_user_by_email(self, email: str) -> Optional[User]:
        """Global lookup (invitations cross tenant boundaries)."""
        return self.db.execute(
            select(User).where(User.email == email.lower())
        ).scalar_one_or_none()

    # ------------------------------------------------------------------
    # Create / update
    # ------------------------------------------------------------------

    def create_user(
        self,
        tenant_id: str,
        email: str,
        full_name: str,
        role_id: str,
        password: str,
        is_active: bool = True,
        broker_id: Optional[str] = None,
    ) -> User:
        """Create a user directly (no invitation flow).

        Validates the role exists in the tenant + enforces unique email.
        Pass `broker_id` for BROKER-role users so they pass the
        broker-portal joins on `users.broker_id`.
        """
        email = email.lower().strip()
        if self.get_user_by_email(email):
            raise ValueError(f"A user with email {email} already exists")
        role = self._load_role(tenant_id, role_id)
        if role is None:
            raise ValueError(f"Role {role_id} not found in tenant")

        user = User(
            email=email,
            full_name=full_name,
            hashed_password=_hash_password(password),
            tenant_id=UUID(tenant_id),
            role_id=role.id,
            broker_id=UUID(broker_id) if broker_id else None,
            is_active=is_active,
        )
        self.db.add(user)
        self.db.flush()
        logger.info("UserService: created user %s in tenant %s", email, tenant_id)
        return user

    def update_user(
        self,
        tenant_id: str,
        user_id: str,
        full_name: Optional[str] = None,
        role_id: Optional[str] = None,
        is_active: Optional[bool] = None,
        broker_id: Optional[str] = None,
        clear_broker_id: bool = False,
    ) -> User:
        user = self.get_user(tenant_id, user_id)
        if user is None:
            raise ValueError(f"User {user_id} not found")

        if role_id is not None:
            role = self._load_role(tenant_id, role_id)
            if role is None:
                raise ValueError(f"Role {role_id} not found in tenant")
            user.role_id = role.id

        if full_name is not None:
            user.full_name = full_name

        if is_active is not None and is_active != user.is_active:
            if not is_active:
                self._assert_not_last_active_admin(tenant_id, user)
            user.is_active = is_active

        # broker_id backfill for existing broker users that pre-date the
        # invitation-side fix. `clear_broker_id=True` explicitly unsets
        # the link (used when a broker leaves a firm).
        if clear_broker_id:
            user.broker_id = None
        elif broker_id is not None:
            user.broker_id = UUID(broker_id)

        self.db.flush()
        return user

    def deactivate_user(self, tenant_id: str, user_id: str) -> User:
        return self.update_user(tenant_id, user_id, is_active=False)

    # ------------------------------------------------------------------
    # Invariants
    # ------------------------------------------------------------------

    def _assert_not_last_active_admin(self, tenant_id: str, user: User) -> None:
        """Refuse to deactivate the only active ADMIN in a tenant."""
        admin_role = self.db.execute(
            select(Role).where(
                Role.tenant_id == UUID(tenant_id), Role.name == "ADMIN"
            )
        ).scalar_one_or_none()
        if admin_role is None or user.role_id != admin_role.id:
            return
        count = self.db.execute(
            select(func.count()).select_from(User).where(
                User.tenant_id == UUID(tenant_id),
                User.role_id == admin_role.id,
                User.is_active == True,  # noqa: E712
                User.id != user.id,
            )
        ).scalar() or 0
        if count == 0:
            raise ValueError(
                "Cannot deactivate the last active ADMIN in the tenant"
            )

    def _load_role(self, tenant_id: str, role_id: str) -> Optional[Role]:
        try:
            return self.db.execute(
                select(Role).where(
                    Role.tenant_id == UUID(tenant_id),
                    Role.id == UUID(role_id),
                )
            ).scalar_one_or_none()
        except (ValueError, TypeError):
            return None


# ==========================================================================
# RoleService
# ==========================================================================


class RoleService:
    """Tenant-scoped CRUD for roles."""

    def __init__(self, db: Session):
        self.db = db

    def list_roles(self, tenant_id: str) -> list[Role]:
        rows = self.db.execute(
            select(Role).where(Role.tenant_id == UUID(tenant_id)).order_by(Role.name)
        ).scalars().all()
        return list(rows)

    def get_role(self, tenant_id: str, role_id: str) -> Optional[Role]:
        try:
            return self.db.execute(
                select(Role).where(
                    Role.tenant_id == UUID(tenant_id),
                    Role.id == UUID(role_id),
                )
            ).scalar_one_or_none()
        except (ValueError, TypeError):
            return None

    def create_role(
        self,
        tenant_id: str,
        name: str,
        permissions: list[str],
        description: Optional[str] = None,
    ) -> Role:
        existing = self.db.execute(
            select(Role).where(
                Role.tenant_id == UUID(tenant_id), Role.name == name
            )
        ).scalar_one_or_none()
        if existing:
            raise ValueError(f"Role '{name}' already exists in tenant")

        self._validate_permissions(permissions)

        role = Role(
            tenant_id=UUID(tenant_id),
            name=name,
            permissions=list(permissions),
            description=description,
            is_system_role=False,
        )
        self.db.add(role)
        self.db.flush()
        logger.info("RoleService: created role %s in tenant %s", name, tenant_id)
        return role

    def update_role(
        self,
        tenant_id: str,
        role_id: str,
        permissions: Optional[list[str]] = None,
        description: Optional[str] = None,
    ) -> Role:
        role = self.get_role(tenant_id, role_id)
        if role is None:
            raise ValueError(f"Role {role_id} not found")
        if role.is_system_role:
            raise ValueError(f"System role '{role.name}' cannot be modified")

        if permissions is not None:
            self._validate_permissions(permissions)
            role.permissions = list(permissions)
        if description is not None:
            role.description = description

        self.db.flush()
        return role

    def delete_role(self, tenant_id: str, role_id: str) -> None:
        role = self.get_role(tenant_id, role_id)
        if role is None:
            raise ValueError(f"Role {role_id} not found")
        if role.is_system_role:
            raise ValueError(f"System role '{role.name}' cannot be deleted")

        # Refuse if any user is assigned this role
        user_count = self.db.execute(
            select(func.count()).select_from(User).where(User.role_id == role.id)
        ).scalar() or 0
        if user_count > 0:
            raise ValueError(
                f"Role '{role.name}' is assigned to {user_count} user(s); "
                "reassign them before deletion"
            )

        self.db.delete(role)
        self.db.flush()
        logger.info("RoleService: deleted role %s in tenant %s", role.name, tenant_id)

    @staticmethod
    def _validate_permissions(permissions: list[str]) -> None:
        """Every permission must be a known value from Permission enum."""
        from infrastructure.api.auth.permissions import Permission

        valid = {p.value for p in Permission}
        unknown = [p for p in permissions if p not in valid]
        if unknown:
            raise ValueError(f"Unknown permissions: {unknown}")


# ==========================================================================
# InvitationService
# ==========================================================================


class InvitationService:
    """Handles the user invitation flow (send + accept)."""

    def __init__(self, db: Session):
        self.db = db

    def send(
        self,
        tenant_id: str,
        email: str,
        role_id: str,
        inviter_id: Optional[str] = None,
        broker_id: Optional[str] = None,
    ) -> InvitationToken:
        """Create a pending invitation. Returns the raw token once; caller
        is responsible for delivering it (email TBD)."""
        email = email.lower().strip()
        if not email:
            raise ValueError("Email is required")

        # Validate role exists in tenant
        role = self.db.execute(
            select(Role).where(
                Role.tenant_id == UUID(tenant_id),
                Role.id == UUID(role_id),
            )
        ).scalar_one_or_none()
        if role is None:
            raise ValueError(f"Role {role_id} not found in tenant")

        # Refuse if a user with this email already exists
        existing_user = self.db.execute(
            select(User).where(User.email == email)
        ).scalar_one_or_none()
        if existing_user:
            raise ValueError(f"A user with email {email} already exists")

        # Cancel any prior pending invitations for the same email+tenant
        self.db.execute(
            UserInvitation.__table__.update()
            .where(
                UserInvitation.email == email,
                UserInvitation.tenant_id == UUID(tenant_id),
                UserInvitation.accepted_at.is_(None),
                UserInvitation.cancelled_at.is_(None),
            )
            .values(cancelled_at=datetime.now(timezone.utc))
        )

        raw_token = secrets.token_urlsafe(32)
        token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
        expires_at = datetime.now(timezone.utc) + timedelta(days=INVITATION_TTL_DAYS)

        invitation = UserInvitation(
            email=email,
            tenant_id=UUID(tenant_id),
            role_id=role.id,
            inviter_id=UUID(inviter_id) if inviter_id else None,
            broker_id=UUID(broker_id) if broker_id else None,
            token_hash=token_hash,
            expires_at=expires_at,
        )
        self.db.add(invitation)
        self.db.flush()

        logger.info(
            "InvitationService: invited %s to tenant %s with role %s",
            email, tenant_id, role.name,
        )
        return InvitationToken(
            invitation_id=str(invitation.id),
            token=raw_token,
            expires_at=expires_at,
        )

    def accept(
        self,
        raw_token: str,
        full_name: str,
        password: str,
    ) -> User:
        """Complete registration via a valid invitation token."""
        token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
        invitation = self.db.execute(
            select(UserInvitation).where(UserInvitation.token_hash == token_hash)
        ).scalar_one_or_none()
        if invitation is None:
            raise ValueError("Invalid invitation token")

        now = datetime.now(timezone.utc)
        if invitation.cancelled_at is not None:
            raise ValueError("Invitation cancelled")
        if invitation.accepted_at is not None:
            raise ValueError("Invitation already accepted")
        expiry = invitation.expires_at
        if expiry.tzinfo is None:
            expiry = expiry.replace(tzinfo=timezone.utc)
        if expiry < now:
            raise ValueError("Invitation expired")

        # Check user still doesn't exist (race-condition guard)
        if self.db.execute(
            select(User).where(User.email == invitation.email)
        ).scalar_one_or_none():
            raise ValueError("User with this email already exists")

        user = User(
            email=invitation.email,
            full_name=full_name,
            hashed_password=_hash_password(password),
            tenant_id=invitation.tenant_id,
            role_id=invitation.role_id,
            # Propagate the broker stamp from the invitation so broker
            # users land with users.broker_id set and pass the
            # `Submission.broker_id == user.broker_id` join used by every
            # broker-portal endpoint.
            broker_id=invitation.broker_id,
            is_active=True,
        )
        self.db.add(user)
        invitation.accepted_at = now
        self.db.flush()

        logger.info("InvitationService: accepted invite for %s", invitation.email)
        return user

    def list_pending(self, tenant_id: str) -> list[UserInvitation]:
        rows = self.db.execute(
            select(UserInvitation).where(
                UserInvitation.tenant_id == UUID(tenant_id),
                UserInvitation.accepted_at.is_(None),
                UserInvitation.cancelled_at.is_(None),
            ).order_by(UserInvitation.created_at.desc())
        ).scalars().all()
        return list(rows)

    def cancel(self, tenant_id: str, invitation_id: str) -> None:
        invitation = self.db.execute(
            select(UserInvitation).where(
                UserInvitation.tenant_id == UUID(tenant_id),
                UserInvitation.id == UUID(invitation_id),
            )
        ).scalar_one_or_none()
        if invitation is None:
            raise ValueError(f"Invitation {invitation_id} not found")
        if invitation.accepted_at is not None:
            raise ValueError("Invitation already accepted")
        invitation.cancelled_at = datetime.now(timezone.utc)
        self.db.flush()

"""
A-1d: JWT Session Management

Tenant-aware JWT handling using python-jose and proper HS256/HS384 signing.
Access tokens are short-lived (15 min default, configurable per tenant).
Refresh tokens are longer-lived (7 days default) and rotate on use -- each
refresh invalidates the previous refresh token via user_sessions table.

Backwards compatibility: the legacy Permission enum and decorator-style
`requires_permission` are preserved for existing endpoints. New endpoints
should use infrastructure.api.auth.permissions.Permission and
require_permission() instead.
"""

from __future__ import annotations

import hashlib
import logging
import os
import secrets
from datetime import datetime, timedelta, timezone
from enum import Enum
from functools import wraps
from typing import Any, Callable, List, Optional

import bcrypt
import jwt
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt.exceptions import InvalidTokenError
from pydantic import BaseModel

logger = logging.getLogger("dsi.api.auth")


# =============================================================================
# CONFIG
# =============================================================================

# Secret must be set via env in production. Generated fallback lets tests run
# but emits a warning if debug is not set.
SECRET_KEY = os.getenv("DSI_JWT_SECRET_KEY", "dev-only-secret-CHANGE-IN-PRODUCTION-or-set-DSI_JWT_SECRET_KEY")
if SECRET_KEY.startswith("dev-only") and os.getenv("DSI_ENV", "development") == "production":
    raise RuntimeError("DSI_JWT_SECRET_KEY must be set in production")

ALGORITHM = os.getenv("DSI_JWT_ALGORITHM", "HS256")

# Default durations -- can be overridden per-tenant via Tenant.settings
DEFAULT_ACCESS_TOKEN_MINUTES = int(os.getenv("DSI_ACCESS_TOKEN_MINUTES", "15"))
DEFAULT_REFRESH_TOKEN_DAYS = int(os.getenv("DSI_REFRESH_TOKEN_DAYS", "7"))


# =============================================================================
# PASSWORD HASHING
# =============================================================================


def hash_password(plaintext: str) -> str:
    """Return a bcrypt hash of the plaintext password.

    bcrypt has a 72-byte ceiling; passwords beyond are silently truncated by
    the library. We enforce a policy limit of 128 chars which is well below
    that and above any sensible human password.
    """
    if len(plaintext.encode()) > 72:
        # Truncate to avoid bcrypt 5.x raising. Callers should validate
        # policy limits before calling; this is a safety net.
        plaintext = plaintext.encode()[:72].decode(errors="ignore")
    return bcrypt.hashpw(plaintext.encode(), bcrypt.gensalt()).decode()


def verify_password(plaintext: str, hashed: str) -> bool:
    """Verify plaintext against a stored bcrypt hash."""
    if not hashed:
        return False
    if len(plaintext.encode()) > 72:
        plaintext = plaintext.encode()[:72].decode(errors="ignore")
    try:
        return bcrypt.checkpw(plaintext.encode(), hashed.encode())
    except (ValueError, TypeError):
        return False


# =============================================================================
# TOKEN PAYLOAD
# =============================================================================


class TokenPayload(BaseModel):
    """JWT payload for access tokens."""

    sub: str  # user_id (UUID)
    tenant_id: str
    role: Optional[str] = None
    permissions: list[str] = []
    email: Optional[str] = None
    exp: int  # unix timestamp
    iat: int  # unix timestamp
    jti: str  # unique token id
    type: str  # "access" | "refresh"


# =============================================================================
# TOKEN CREATION / VALIDATION
# =============================================================================


def create_access_token(
    user_id: str,
    tenant_id: str,
    role: Optional[str] = None,
    permissions: Optional[List[str]] = None,
    email: Optional[str] = None,
    expires_minutes: Optional[int] = None,
) -> str:
    """Create a signed access JWT with tenant and permission claims."""
    now = datetime.now(timezone.utc)
    expires = now + timedelta(minutes=expires_minutes or DEFAULT_ACCESS_TOKEN_MINUTES)
    payload = {
        "sub": str(user_id),
        "tenant_id": str(tenant_id),
        "role": role,
        "permissions": permissions or [],
        "email": email,
        "iat": int(now.timestamp()),
        "exp": int(expires.timestamp()),
        "jti": secrets.token_urlsafe(16),
        "type": "access",
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def create_refresh_token(user_id: str, tenant_id: str, expires_days: Optional[int] = None) -> tuple[str, str]:
    """Create a signed refresh JWT. Returns (token, token_hash).

    The hash is stored in user_sessions.refresh_token_hash. On refresh, we
    look up by hash, mint a new access + refresh pair, and rotate the hash.
    """
    now = datetime.now(timezone.utc)
    expires = now + timedelta(days=expires_days or DEFAULT_REFRESH_TOKEN_DAYS)
    payload = {
        "sub": str(user_id),
        "tenant_id": str(tenant_id),
        "iat": int(now.timestamp()),
        "exp": int(expires.timestamp()),
        "jti": secrets.token_urlsafe(16),
        "type": "refresh",
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    return token, hash_token(token)


def hash_token(token: str) -> str:
    """SHA-256 hash of a token for DB storage (refresh tokens + reset tokens)."""
    return hashlib.sha256(token.encode()).hexdigest()


def decode_token(token: str, expected_type: Optional[str] = None) -> Optional[TokenPayload]:
    """Decode and validate a JWT. Returns None if invalid/expired.

    If expected_type is provided, the token's `type` claim must match.
    """
    try:
        data = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except InvalidTokenError as exc:
        logger.debug("JWT decode failed: %s", exc)
        return None

    if expected_type and data.get("type") != expected_type:
        return None

    try:
        return TokenPayload(**data)
    except Exception as exc:  # pydantic validation
        logger.debug("JWT payload invalid: %s", exc)
        return None


# =============================================================================
# LEGACY -- kept for backwards compatibility with existing decorator usage
# =============================================================================


class Permission(str, Enum):
    """Legacy coarse-grained permissions. New code should use
    infrastructure.api.auth.permissions.Permission instead."""

    SUBMIT = "submit"
    QUOTE = "quote"
    REFERRAL = "referral"
    ANALYTICS = "analytics"
    ADMIN = "admin"


class User:
    """Legacy authenticated user (in-memory). Used by existing decorators.

    New endpoints should use AuthContext from permissions.py instead.
    """

    def __init__(
        self,
        user_id: str,
        username: str,
        permissions: List[Permission],
        roles: Optional[List[str]] = None,
        tenant_id: Optional[str] = None,
    ):
        self.user_id = user_id
        self.username = username
        self.permissions = permissions
        self.roles = roles or []
        self.tenant_id = tenant_id

    def has_permission(self, permission: Permission) -> bool:
        return permission in self.permissions or Permission.ADMIN in self.permissions


security = HTTPBearer(auto_error=False)


class JWTAuth:
    """Legacy FastAPI auth dependency. Preserved for backwards compat."""

    def __init__(self, required: bool = True):
        self.required = required

    async def __call__(
        self,
        request: Request,
        credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    ) -> Optional[User]:
        if credentials is None:
            if self.required:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            return None

        payload = decode_token(credentials.credentials, expected_type="access")
        if payload is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Map granular permissions back to the legacy set for decorator compat.
        legacy_perms: list[Permission] = []
        for p in payload.permissions:
            if p.startswith("admin:"):
                legacy_perms.append(Permission.ADMIN)
            elif p == "assessment:write":
                legacy_perms.append(Permission.SUBMIT)
            elif p == "assessment:refer":
                legacy_perms.append(Permission.REFERRAL)

        return User(
            user_id=payload.sub,
            username=payload.email or payload.sub,
            permissions=legacy_perms,
            tenant_id=payload.tenant_id,
        )


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> Optional[User]:
    """Legacy helper -- returns User or None without raising."""
    if credentials is None:
        return None

    payload = decode_token(credentials.credentials, expected_type="access")
    if payload is None:
        return None

    return User(
        user_id=payload.sub,
        username=payload.email or payload.sub,
        permissions=[],
        tenant_id=payload.tenant_id,
    )


def requires_permission(*permissions: Permission):
    """Legacy decorator. Prefer permissions.require_permission in new code."""

    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            request = kwargs.get("request")
            if request is None:
                for arg in args:
                    if isinstance(arg, Request):
                        request = arg
                        break
            if request is None:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Request not found in handler",
                )
            user = getattr(request.state, "user", None)
            if user is None:
                auth_header = request.headers.get("Authorization")
                if auth_header and auth_header.startswith("Bearer "):
                    payload = decode_token(auth_header[7:], expected_type="access")
                    if payload:
                        legacy_perms: list[Permission] = []
                        for p in payload.permissions:
                            if p.startswith("admin:"):
                                legacy_perms.append(Permission.ADMIN)
                        user = User(
                            user_id=payload.sub,
                            username=payload.email or payload.sub,
                            permissions=legacy_perms,
                            tenant_id=payload.tenant_id,
                        )
            if user is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required",
                )
            for perm in permissions:
                if not user.has_permission(perm):
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=f"Permission denied: {perm.value}",
                    )
            return await func(*args, **kwargs)

        return wrapper

    return decorator

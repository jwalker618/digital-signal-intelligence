"""
DSI JWT Authentication (Phase 11)

JWT-based authentication for the API.
"""

import logging
from datetime import datetime, timedelta
from enum import Enum
from functools import wraps
from typing import Callable, List, Optional

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

# Note: In production, use python-jose or similar
# For demonstration, using simplified token handling


logger = logging.getLogger("dsi.api.auth")


# =============================================================================
# PERMISSIONS
# =============================================================================

class Permission(str, Enum):
    """API permissions."""
    SUBMIT = "submit"
    QUOTE = "quote"
    REFERRAL = "referral"
    ANALYTICS = "analytics"
    ADMIN = "admin"


# =============================================================================
# USER MODEL
# =============================================================================

class User:
    """Authenticated user."""

    def __init__(
        self,
        user_id: str,
        username: str,
        permissions: List[Permission],
        roles: List[str] = None,
    ):
        self.user_id = user_id
        self.username = username
        self.permissions = permissions
        self.roles = roles or []

    def has_permission(self, permission: Permission) -> bool:
        """Check if user has a permission."""
        return permission in self.permissions or Permission.ADMIN in self.permissions


# =============================================================================
# JWT HANDLING
# =============================================================================

# Secret key (in production, use environment variable)
SECRET_KEY = "dsi-secret-key-change-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60


def create_access_token(
    user_id: str,
    username: str,
    permissions: List[str],
    expires_delta: Optional[timedelta] = None,
) -> str:
    """
    Create a JWT access token.

    In production, use python-jose:
    from jose import jwt
    """
    import base64
    import json
    import hashlib

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    payload = {
        "sub": user_id,
        "username": username,
        "permissions": permissions,
        "exp": expire.isoformat(),
        "iat": datetime.utcnow().isoformat(),
    }

    # Simplified token encoding (use proper JWT library in production)
    header = base64.urlsafe_b64encode(
        json.dumps({"alg": ALGORITHM, "typ": "JWT"}).encode()
    ).decode().rstrip("=")

    payload_encoded = base64.urlsafe_b64encode(
        json.dumps(payload).encode()
    ).decode().rstrip("=")

    signature = hashlib.sha256(
        f"{header}.{payload_encoded}.{SECRET_KEY}".encode()
    ).hexdigest()[:32]

    return f"{header}.{payload_encoded}.{signature}"


def decode_token(token: str) -> Optional[dict]:
    """
    Decode and validate a JWT token.

    In production, use python-jose:
    from jose import jwt, JWTError
    """
    import base64
    import json
    import hashlib

    try:
        parts = token.split(".")
        if len(parts) != 3:
            return None

        header, payload_encoded, signature = parts

        # Verify signature
        expected_sig = hashlib.sha256(
            f"{header}.{payload_encoded}.{SECRET_KEY}".encode()
        ).hexdigest()[:32]

        if signature != expected_sig:
            return None

        # Decode payload
        # Add padding if needed
        padding = 4 - len(payload_encoded) % 4
        if padding != 4:
            payload_encoded += "=" * padding

        payload = json.loads(base64.urlsafe_b64decode(payload_encoded))

        # Check expiration
        exp = datetime.fromisoformat(payload["exp"])
        if exp < datetime.utcnow():
            return None

        return payload

    except Exception as e:
        logger.warning(f"Token decode error: {e}")
        return None


# =============================================================================
# AUTHENTICATION DEPENDENCIES
# =============================================================================

security = HTTPBearer(auto_error=False)


class JWTAuth:
    """JWT authentication handler."""

    def __init__(self, required: bool = True):
        self.required = required

    async def __call__(
        self,
        request: Request,
        credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    ) -> Optional[User]:
        """Authenticate request."""
        if credentials is None:
            if self.required:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            return None

        token = credentials.credentials
        payload = decode_token(token)

        if payload is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token",
                headers={"WWW-Authenticate": "Bearer"},
            )

        return User(
            user_id=payload["sub"],
            username=payload["username"],
            permissions=[Permission(p) for p in payload.get("permissions", [])],
        )


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> Optional[User]:
    """Get current authenticated user."""
    if credentials is None:
        return None

    payload = decode_token(credentials.credentials)

    if payload is None:
        return None

    return User(
        user_id=payload["sub"],
        username=payload["username"],
        permissions=[Permission(p) for p in payload.get("permissions", [])],
    )


# =============================================================================
# PERMISSION DECORATOR
# =============================================================================

def requires_permission(*permissions: Permission):
    """
    Decorator to require specific permissions.

    Usage:
        @requires_permission(Permission.REFERRAL)
        async def process_referral(...):
            pass
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Get user from request
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

            # Get user from dependency injection or header
            user = getattr(request.state, "user", None)

            if user is None:
                # Try to get from authorization header
                auth_header = request.headers.get("Authorization")
                if auth_header and auth_header.startswith("Bearer "):
                    token = auth_header[7:]
                    payload = decode_token(token)
                    if payload:
                        user = User(
                            user_id=payload["sub"],
                            username=payload["username"],
                            permissions=[Permission(p) for p in payload.get("permissions", [])],
                        )

            if user is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required",
                )

            # Check permissions
            for perm in permissions:
                if not user.has_permission(perm):
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=f"Permission denied: {perm.value}",
                    )

            return await func(*args, **kwargs)

        return wrapper
    return decorator

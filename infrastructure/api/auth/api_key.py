"""
DSI API Key Authentication (Phase 11)

API key-based authentication for system integrations.
"""

import hashlib
import logging
import secrets
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional

from fastapi import Depends, HTTPException, Request, Security, status
from fastapi.security import APIKeyHeader


logger = logging.getLogger("dsi.api.auth.apikey")


# =============================================================================
# API KEY MODELS
# =============================================================================

@dataclass
class APIKey:
    """API key record."""
    key_id: str
    client_id: str
    client_name: str
    key_hash: str  # Store hash, not plaintext
    permissions: List[str]
    rate_limit_tier: str = "standard"
    active: bool = True
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_used: Optional[datetime] = None
    expires_at: Optional[datetime] = None


@dataclass
class APIKeyValidation:
    """Result of API key validation."""
    valid: bool
    client_id: Optional[str] = None
    client_name: Optional[str] = None
    permissions: List[str] = field(default_factory=list)
    rate_limit_tier: str = "standard"
    error: Optional[str] = None


# =============================================================================
# API KEY STORAGE (Replace with database in production)
# =============================================================================

_api_keys: Dict[str, APIKey] = {}


def _hash_key(key: str) -> str:
    """Hash an API key for storage."""
    return hashlib.sha256(key.encode()).hexdigest()


def create_api_key(
    client_id: str,
    client_name: str,
    permissions: List[str],
    rate_limit_tier: str = "standard",
) -> tuple[str, APIKey]:
    """
    Create a new API key.

    Returns the raw key (show once) and the key record.
    """
    # Generate key
    raw_key = f"dsi_{secrets.token_urlsafe(32)}"
    key_id = f"key_{secrets.token_urlsafe(8)}"
    key_hash = _hash_key(raw_key)

    key_record = APIKey(
        key_id=key_id,
        client_id=client_id,
        client_name=client_name,
        key_hash=key_hash,
        permissions=permissions,
        rate_limit_tier=rate_limit_tier,
    )

    _api_keys[key_hash] = key_record

    return raw_key, key_record


def revoke_api_key(key_id: str) -> bool:
    """Revoke an API key."""
    for key_hash, key_record in _api_keys.items():
        if key_record.key_id == key_id:
            key_record.active = False
            return True
    return False


# =============================================================================
# VALIDATION
# =============================================================================

def validate_api_key(api_key: str) -> APIKeyValidation:
    """
    Validate an API key.

    Returns validation result with client info if valid.
    """
    if not api_key:
        return APIKeyValidation(valid=False, error="No API key provided")

    # Handle demo key
    if api_key == "demo_key":
        return APIKeyValidation(
            valid=True,
            client_id="demo",
            client_name="Demo Client",
            permissions=["submit", "quote"],
            rate_limit_tier="standard",
        )

    # Hash and lookup
    key_hash = _hash_key(api_key)
    key_record = _api_keys.get(key_hash)

    if key_record is None:
        return APIKeyValidation(valid=False, error="Invalid API key")

    if not key_record.active:
        return APIKeyValidation(valid=False, error="API key has been revoked")

    if key_record.expires_at and key_record.expires_at < datetime.utcnow():
        return APIKeyValidation(valid=False, error="API key has expired")

    # Update last used
    key_record.last_used = datetime.utcnow()

    return APIKeyValidation(
        valid=True,
        client_id=key_record.client_id,
        client_name=key_record.client_name,
        permissions=key_record.permissions,
        rate_limit_tier=key_record.rate_limit_tier,
    )


# =============================================================================
# FASTAPI DEPENDENCIES
# =============================================================================

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


class APIKeyAuth:
    """API key authentication handler."""

    def __init__(self, required: bool = True):
        self.required = required

    async def __call__(
        self,
        request: Request,
        api_key: Optional[str] = Security(api_key_header),
    ) -> Optional[APIKeyValidation]:
        """Authenticate request via API key."""
        if api_key is None:
            if self.required:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="API key required",
                    headers={"WWW-Authenticate": "X-API-Key"},
                )
            return None

        validation = validate_api_key(api_key)

        if not validation.valid:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=validation.error or "Invalid API key",
            )

        # Store validation in request state
        request.state.api_key_validation = validation

        return validation


async def get_api_key_client(
    api_key: Optional[str] = Security(api_key_header),
) -> Optional[APIKeyValidation]:
    """Get API key client info."""
    if api_key is None:
        return None

    return validate_api_key(api_key)


# =============================================================================
# INITIALIZATION (Create demo keys)
# =============================================================================

def init_demo_keys():
    """Initialize demo API keys for testing."""
    # Create a demo integration key
    raw_key, _ = create_api_key(
        client_id="integration_test",
        client_name="Integration Test Client",
        permissions=["submit", "quote", "referral", "analytics"],
        rate_limit_tier="premium",
    )
    logger.info(f"Demo API key created: {raw_key[:20]}...")

    return raw_key


# Create demo keys on module load
_demo_key = None
try:
    _demo_key = init_demo_keys()
except Exception:
    pass  # Ignore if already initialized

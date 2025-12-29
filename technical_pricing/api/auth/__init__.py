"""
DSI API Authentication (Phase 11)

Authentication and authorization for the API.
"""

from .jwt_auth import (
    JWTAuth,
    create_access_token,
    decode_token,
    get_current_user,
    requires_permission,
    Permission,
)

from .api_key import (
    APIKeyAuth,
    validate_api_key,
)

__all__ = [
    "JWTAuth",
    "create_access_token",
    "decode_token",
    "get_current_user",
    "requires_permission",
    "Permission",
    "APIKeyAuth",
    "validate_api_key",
]

"""
API Authentication & Authorization
====================================

API key-based authentication for DSI API.
"""

import os
import hashlib
import secrets
from functools import wraps
from flask import request, jsonify
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)


class APIKeyManager:
    """Manages API key authentication."""

    def __init__(self):
        # In production, these would come from a secure database
        # For now, use environment variables
        self.api_keys = self._load_api_keys()

    def _load_api_keys(self) -> Dict[str, Dict[str, Any]]:
        """Load API keys from environment or configuration."""
        keys = {}

        # Default development key
        dev_key = os.environ.get('DSI_API_KEY', 'dev-key-12345')
        keys[dev_key] = {
            'name': 'Development Key',
            'tier': 'unlimited',
            'rate_limit': 1000,
            'active': True
        }

        # Load additional keys from environment
        # Format: DSI_API_KEY_1=key:name:tier:rate_limit
        i = 1
        while True:
            env_var = f'DSI_API_KEY_{i}'
            key_config = os.environ.get(env_var)
            if not key_config:
                break

            parts = key_config.split(':')
            if len(parts) >= 4:
                key, name, tier, rate_limit = parts[0], parts[1], parts[2], int(parts[3])
                keys[key] = {
                    'name': name,
                    'tier': tier,
                    'rate_limit': rate_limit,
                    'active': True
                }
            i += 1

        return keys

    def validate_key(self, api_key: str) -> Optional[Dict[str, Any]]:
        """Validate an API key and return its metadata."""
        if not api_key:
            return None

        key_info = self.api_keys.get(api_key)
        if not key_info or not key_info.get('active'):
            return None

        return key_info

    @staticmethod
    def generate_key() -> str:
        """Generate a new API key."""
        return f"dsi_{secrets.token_urlsafe(32)}"


# Global API key manager
api_key_manager = APIKeyManager()


def require_api_key(f):
    """Decorator to require API key authentication."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Check if authentication is enabled
        auth_enabled = os.environ.get('DSI_AUTH_ENABLED', 'false').lower() == 'true'

        if not auth_enabled:
            # Auth disabled for development
            return f(*args, **kwargs)

        # Get API key from header
        api_key = request.headers.get('X-API-Key')

        if not api_key:
            # Try Authorization header
            auth_header = request.headers.get('Authorization', '')
            if auth_header.startswith('Bearer '):
                api_key = auth_header[7:]

        # Validate key
        key_info = api_key_manager.validate_key(api_key)

        if not key_info:
            logger.warning(f"Invalid API key attempt from {request.remote_addr}")
            return jsonify({
                'success': False,
                'error': 'Invalid or missing API key',
                'message': 'Please provide a valid API key in X-API-Key header or Authorization: Bearer <key>'
            }), 401

        # Add key info to request context
        request.api_key_info = key_info

        return f(*args, **kwargs)

    return decorated_function


def get_current_key_info() -> Optional[Dict[str, Any]]:
    """Get information about the current API key."""
    return getattr(request, 'api_key_info', None)

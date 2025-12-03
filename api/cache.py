"""
Caching Layer
=============

Redis-based caching for API responses.
"""

import json
import logging
import hashlib
from typing import Optional, Any, Dict
from functools import wraps
from flask import request
import os

logger = logging.getLogger(__name__)

# Try to import Redis
try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    logger.warning("Redis not available - caching disabled")


class CacheManager:
    """Manages caching of API responses."""

    def __init__(self):
        """Initialize cache manager."""
        self.enabled = os.environ.get('CACHE_ENABLED', 'false').lower() == 'true'
        self.redis_client = None

        if self.enabled and REDIS_AVAILABLE:
            try:
                redis_host = os.environ.get('REDIS_HOST', 'localhost')
                redis_port = int(os.environ.get('REDIS_PORT', 6379))
                redis_db = int(os.environ.get('REDIS_DB', 0))

                self.redis_client = redis.Redis(
                    host=redis_host,
                    port=redis_port,
                    db=redis_db,
                    decode_responses=True,
                    socket_connect_timeout=2,
                    socket_timeout=2
                )

                # Test connection
                self.redis_client.ping()
                logger.info(f"Connected to Redis at {redis_host}:{redis_port}")

            except Exception as e:
                logger.error(f"Failed to connect to Redis: {str(e)}")
                self.enabled = False
                self.redis_client = None

    def _generate_cache_key(self, prefix: str, data: Dict[str, Any]) -> str:
        """
        Generate cache key from request data.

        Args:
            prefix: Key prefix (e.g., 'cyber_quote')
            data: Request data

        Returns:
            Cache key string
        """
        # Sort data to ensure consistent hashing
        data_str = json.dumps(data, sort_keys=True)
        data_hash = hashlib.sha256(data_str.encode()).hexdigest()[:16]
        return f"dsi:{prefix}:{data_hash}"

    def get(self, key: str) -> Optional[Dict[str, Any]]:
        """
        Get value from cache.

        Args:
            key: Cache key

        Returns:
            Cached value or None
        """
        if not self.enabled or not self.redis_client:
            return None

        try:
            value = self.redis_client.get(key)
            if value:
                logger.debug(f"Cache hit: {key}")
                return json.loads(value)
            else:
                logger.debug(f"Cache miss: {key}")
                return None
        except Exception as e:
            logger.error(f"Cache get error: {str(e)}")
            return None

    def set(self, key: str, value: Dict[str, Any], ttl: int = 3600) -> bool:
        """
        Set value in cache.

        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds (default 1 hour)

        Returns:
            True if successful
        """
        if not self.enabled or not self.redis_client:
            return False

        try:
            value_str = json.dumps(value)
            self.redis_client.setex(key, ttl, value_str)
            logger.debug(f"Cached: {key} (TTL: {ttl}s)")
            return True
        except Exception as e:
            logger.error(f"Cache set error: {str(e)}")
            return False

    def delete(self, key: str) -> bool:
        """
        Delete value from cache.

        Args:
            key: Cache key

        Returns:
            True if successful
        """
        if not self.enabled or not self.redis_client:
            return False

        try:
            self.redis_client.delete(key)
            logger.debug(f"Cache deleted: {key}")
            return True
        except Exception as e:
            logger.error(f"Cache delete error: {str(e)}")
            return False

    def clear_pattern(self, pattern: str) -> int:
        """
        Clear all keys matching pattern.

        Args:
            pattern: Key pattern (e.g., 'dsi:cyber:*')

        Returns:
            Number of keys deleted
        """
        if not self.enabled or not self.redis_client:
            return 0

        try:
            keys = self.redis_client.keys(pattern)
            if keys:
                count = self.redis_client.delete(*keys)
                logger.info(f"Cleared {count} cache keys matching {pattern}")
                return count
            return 0
        except Exception as e:
            logger.error(f"Cache clear error: {str(e)}")
            return 0


# Global cache manager
cache_manager = CacheManager()


def cache_response(prefix: str, ttl: int = 3600):
    """
    Decorator to cache API responses.

    Args:
        prefix: Cache key prefix
        ttl: Time to live in seconds
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Only cache GET requests with query params or POST with body
            if request.method == 'POST':
                cache_data = request.json
            elif request.method == 'GET':
                cache_data = dict(request.args)
            else:
                return f(*args, **kwargs)

            # Generate cache key
            cache_key = cache_manager._generate_cache_key(prefix, cache_data)

            # Try to get from cache
            cached_value = cache_manager.get(cache_key)
            if cached_value:
                cached_value['cached'] = True
                return cached_value, 200

            # Execute function
            result = f(*args, **kwargs)

            # Cache the result
            if isinstance(result, tuple):
                response_data, status_code = result[0], result[1]
            else:
                response_data, status_code = result, 200

            # Only cache successful responses
            if status_code == 200 and isinstance(response_data, dict):
                cache_manager.set(cache_key, response_data, ttl)

            return result

        return decorated_function
    return decorator

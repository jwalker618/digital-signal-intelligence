"""
DSI Rate Limiting Middleware

Sliding-window rate limiter per API key using in-memory storage
with optional Redis backend for distributed deployments.
"""

import logging
import os
import time
from collections import defaultdict
from typing import Optional, Tuple

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger("dsi.rate_limiter")

# Rate limit tiers: requests per minute
RATE_LIMIT_TIERS = {
    "unlimited": 0,       # No limit (internal)
    "enterprise": 300,    # 300/min
    "standard": 60,       # 60/min
    "basic": 20,          # 20/min
    "demo": 10,           # 10/min
}

# Default from env
DEFAULT_LIMIT = int(os.getenv("RATE_LIMIT_PER_MINUTE", "60"))
WINDOW_SECONDS = 60


class InMemoryRateLimiter:
    """Sliding-window rate limiter using in-memory storage."""

    def __init__(self):
        # client_id -> list of request timestamps
        self._windows: dict[str, list[float]] = defaultdict(list)

    def check(self, client_id: str, limit: int) -> Tuple[bool, int, int]:
        """
        Check if request is allowed.

        Returns:
            (allowed, remaining, reset_seconds)
        """
        if limit <= 0:
            return True, 999, 0

        now = time.time()
        window_start = now - WINDOW_SECONDS

        # Prune old entries
        timestamps = self._windows[client_id]
        self._windows[client_id] = [t for t in timestamps if t > window_start]

        count = len(self._windows[client_id])
        remaining = max(0, limit - count)

        if count >= limit:
            # Calculate when oldest request in window expires
            oldest = min(self._windows[client_id]) if self._windows[client_id] else now
            reset = int(oldest + WINDOW_SECONDS - now) + 1
            return False, 0, reset

        # Allow and record
        self._windows[client_id].append(now)
        return True, remaining - 1, WINDOW_SECONDS


class RedisRateLimiter:
    """Sliding-window rate limiter using Redis for distributed state."""

    def __init__(self, redis_client):
        self._redis = redis_client

    async def check(self, client_id: str, limit: int) -> Tuple[bool, int, int]:
        """Check if request is allowed using Redis sorted sets."""
        if limit <= 0:
            return True, 999, 0

        now = time.time()
        window_start = now - WINDOW_SECONDS
        key = f"dsi:ratelimit:{client_id}"

        pipe = self._redis.pipeline()
        # Remove expired entries
        pipe.zremrangebyscore(key, 0, window_start)
        # Count current window
        pipe.zcard(key)
        # Add current request (optimistic)
        pipe.zadd(key, {str(now): now})
        # Set expiry on key
        pipe.expire(key, WINDOW_SECONDS + 1)
        results = await pipe.execute()

        count = results[1]  # zcard result
        remaining = max(0, limit - count)

        if count >= limit:
            # Over limit - remove the optimistic add
            await self._redis.zrem(key, str(now))
            # Calculate reset
            oldest_scores = await self._redis.zrange(key, 0, 0, withscores=True)
            if oldest_scores:
                reset = int(oldest_scores[0][1] + WINDOW_SECONDS - now) + 1
            else:
                reset = WINDOW_SECONDS
            return False, 0, max(1, reset)

        return True, remaining - 1, WINDOW_SECONDS


# Module-level limiter instance
_limiter: Optional[InMemoryRateLimiter] = None
_redis_limiter: Optional[RedisRateLimiter] = None


def get_limiter() -> InMemoryRateLimiter:
    """Get or create the in-memory rate limiter."""
    global _limiter
    if _limiter is None:
        _limiter = InMemoryRateLimiter()
    return _limiter


def set_redis_limiter(redis_client) -> None:
    """Configure Redis-backed rate limiting."""
    global _redis_limiter
    _redis_limiter = RedisRateLimiter(redis_client)
    logger.info("Rate limiter upgraded to Redis backend")


class RateLimitMiddleware(BaseHTTPMiddleware):
    """FastAPI middleware that enforces per-client rate limits."""

    # Paths exempt from rate limiting
    EXEMPT_PATHS = {
        "/api/v1/health",
        "/api/v1/health/live",
        "/api/v1/health/ready",
        "/metrics",
        "/",
        "/api/docs",
        "/api/redoc",
        "/api/openapi.json",
    }

    async def dispatch(self, request: Request, call_next):
        # Skip rate limiting for exempt paths
        if request.url.path in self.EXEMPT_PATHS:
            return await call_next(request)

        # Extract client identity
        client_id, rate_tier = self._get_client_info(request)
        limit = RATE_LIMIT_TIERS.get(rate_tier, DEFAULT_LIMIT)

        # Check rate limit
        if _redis_limiter is not None:
            allowed, remaining, reset = await _redis_limiter.check(client_id, limit)
        else:
            allowed, remaining, reset = get_limiter().check(client_id, limit)

        if not allowed:
            logger.warning(
                f"Rate limit exceeded for {client_id} (tier={rate_tier}, limit={limit}/min)"
            )
            return JSONResponse(
                status_code=429,
                content={
                    "error": "Rate limit exceeded",
                    "retry_after": reset,
                    "limit": limit,
                },
                headers={
                    "X-RateLimit-Limit": str(limit),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(reset),
                    "Retry-After": str(reset),
                },
            )

        # Process request
        response = await call_next(request)

        # Add rate limit headers
        response.headers["X-RateLimit-Limit"] = str(limit)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(reset)

        return response

    @staticmethod
    def _get_client_info(request: Request) -> Tuple[str, str]:
        """Extract client ID and rate limit tier from request."""
        # Check if auth middleware has set client info
        if hasattr(request.state, "client_id"):
            client_id = request.state.client_id
            rate_tier = getattr(request.state, "rate_limit_tier", "standard")
            return client_id, rate_tier

        # Fall back to API key header
        api_key = request.headers.get("X-API-Key", "")
        if api_key:
            return f"key:{api_key[:8]}", "standard"

        # Fall back to IP
        client_host = request.client.host if request.client else "unknown"
        return f"ip:{client_host}", "basic"

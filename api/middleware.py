"""
API Middleware
==============

Rate limiting, logging, and request tracking middleware.
"""

import time
import logging
from functools import wraps
from flask import request, jsonify, g
from typing import Dict, Any, Optional
from collections import defaultdict
from datetime import datetime, timedelta
import threading

logger = logging.getLogger(__name__)


class RateLimiter:
    """Token bucket rate limiter."""

    def __init__(self):
        self.buckets = defaultdict(lambda: {'tokens': 0, 'last_update': time.time()})
        self.lock = threading.Lock()

    def is_allowed(self, key: str, max_requests: int, window_seconds: int = 3600) -> tuple[bool, Dict[str, Any]]:
        """
        Check if request is allowed under rate limit.

        Args:
            key: Unique identifier (API key, IP address, etc.)
            max_requests: Maximum requests allowed in window
            window_seconds: Time window in seconds (default 1 hour)

        Returns:
            (allowed, info_dict)
        """
        with self.lock:
            now = time.time()
            bucket = self.buckets[key]

            # Calculate tokens to add based on time elapsed
            time_passed = now - bucket['last_update']
            tokens_to_add = (time_passed / window_seconds) * max_requests

            # Update bucket
            bucket['tokens'] = min(max_requests, bucket['tokens'] + tokens_to_add)
            bucket['last_update'] = now

            # Check if request allowed
            if bucket['tokens'] >= 1:
                bucket['tokens'] -= 1
                return True, {
                    'limit': max_requests,
                    'remaining': int(bucket['tokens']),
                    'reset': int(now + window_seconds)
                }
            else:
                return False, {
                    'limit': max_requests,
                    'remaining': 0,
                    'reset': int(now + window_seconds),
                    'retry_after': int((1 - bucket['tokens']) / max_requests * window_seconds)
                }


# Global rate limiter
rate_limiter = RateLimiter()


def rate_limit(max_requests: int = 100, window: int = 3600):
    """
    Rate limiting decorator.

    Args:
        max_requests: Maximum requests allowed
        window: Time window in seconds (default 1 hour)
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Get rate limit key (API key or IP)
            key_info = getattr(request, 'api_key_info', None)

            if key_info:
                rate_limit_key = key_info.get('name', 'unknown')
                max_req = key_info.get('rate_limit', max_requests)
            else:
                # Fallback to IP-based rate limiting
                rate_limit_key = request.remote_addr
                max_req = max_requests

            # Check rate limit
            allowed, info = rate_limiter.is_allowed(rate_limit_key, max_req, window)

            # Add rate limit headers
            response_headers = {
                'X-RateLimit-Limit': str(info['limit']),
                'X-RateLimit-Remaining': str(info['remaining']),
                'X-RateLimit-Reset': str(info['reset'])
            }

            if not allowed:
                logger.warning(f"Rate limit exceeded for {rate_limit_key}")
                response = jsonify({
                    'success': False,
                    'error': 'Rate limit exceeded',
                    'retry_after': info['retry_after']
                })
                response.status_code = 429
                for header, value in response_headers.items():
                    response.headers[header] = value
                response.headers['Retry-After'] = str(info['retry_after'])
                return response

            # Execute request
            result = f(*args, **kwargs)

            # Add headers to response
            if isinstance(result, tuple):
                response, status_code = result[0], result[1] if len(result) > 1 else 200
                for header, value in response_headers.items():
                    if hasattr(response, 'headers'):
                        response.headers[header] = value
                return response, status_code
            else:
                for header, value in response_headers.items():
                    if hasattr(result, 'headers'):
                        result.headers[header] = value
                return result

        return decorated_function
    return decorator


class RequestLogger:
    """Log API requests and responses."""

    @staticmethod
    def log_request():
        """Log incoming request."""
        g.start_time = time.time()
        g.request_id = f"{int(time.time() * 1000)}-{request.remote_addr}"

        logger.info(f"[{g.request_id}] {request.method} {request.path} from {request.remote_addr}")

    @staticmethod
    def log_response(response):
        """Log response."""
        if hasattr(g, 'start_time'):
            duration = time.time() - g.start_time
            logger.info(f"[{g.request_id}] Response {response.status_code} in {duration:.3f}s")

        return response


def request_logging():
    """Decorator for request logging."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            RequestLogger.log_request()
            result = f(*args, **kwargs)
            return result
        return decorated_function
    return decorator

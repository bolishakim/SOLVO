"""
Rate Limiting Middleware

Implements token bucket rate limiting for API endpoints.
"""

import time
from collections import defaultdict
from dataclasses import dataclass
from typing import Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response


@dataclass
class RateLimitConfig:
    """Configuration for rate limiting."""

    requests_per_minute: int = 60
    burst_size: int = 10
    # Specific endpoint limits (path prefix -> requests per minute)
    endpoint_limits: dict[str, int] | None = None


@dataclass
class TokenBucket:
    """Token bucket for rate limiting."""

    tokens: float
    last_update: float
    requests_per_minute: int

    def consume(self) -> bool:
        """Try to consume a token. Returns True if successful."""
        now = time.time()
        # Refill tokens based on time elapsed
        time_passed = now - self.last_update
        tokens_to_add = time_passed * (self.requests_per_minute / 60.0)
        self.tokens = min(self.requests_per_minute, self.tokens + tokens_to_add)
        self.last_update = now

        if self.tokens >= 1:
            self.tokens -= 1
            return True
        return False

    def time_until_available(self) -> float:
        """Returns seconds until a token will be available."""
        if self.tokens >= 1:
            return 0
        tokens_needed = 1 - self.tokens
        seconds_per_token = 60.0 / self.requests_per_minute
        return tokens_needed * seconds_per_token


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Middleware that implements rate limiting using token bucket algorithm.

    Features:
    - Per-IP rate limiting
    - Configurable limits per endpoint
    - Burst handling
    - Rate limit headers in response
    """

    # Paths to exclude from rate limiting
    EXCLUDED_PATHS = {"/health", "/metrics", "/docs", "/redoc", "/openapi.json"}

    # Paths with stricter rate limits (authentication endpoints)
    AUTH_PATHS = {"/api/v1/auth/login", "/api/v1/auth/register", "/api/v1/auth/forgot-password"}

    def __init__(
        self,
        app,
        requests_per_minute: int = 60,
        auth_requests_per_minute: int = 10,
        burst_size: int = 10,
    ):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.auth_requests_per_minute = auth_requests_per_minute
        self.burst_size = burst_size

        # Store buckets per IP and endpoint type
        self.buckets: dict[str, TokenBucket] = defaultdict(
            lambda: TokenBucket(
                tokens=self.requests_per_minute,
                last_update=time.time(),
                requests_per_minute=self.requests_per_minute,
            )
        )
        self.auth_buckets: dict[str, TokenBucket] = defaultdict(
            lambda: TokenBucket(
                tokens=self.auth_requests_per_minute,
                last_update=time.time(),
                requests_per_minute=self.auth_requests_per_minute,
            )
        )

        # Cleanup old entries periodically
        self._last_cleanup = time.time()
        self._cleanup_interval = 300  # 5 minutes

    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP from request, considering proxies."""
        # Check for forwarded headers (when behind proxy/load balancer)
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            # Get the first IP in the chain (original client)
            return forwarded.split(",")[0].strip()

        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip

        # Fall back to direct connection IP
        if request.client:
            return request.client.host

        return "unknown"

    def _is_auth_path(self, path: str) -> bool:
        """Check if the path is an authentication endpoint."""
        return any(path.startswith(auth_path) for auth_path in self.AUTH_PATHS)

    def _cleanup_old_buckets(self) -> None:
        """Remove stale bucket entries to prevent memory growth."""
        now = time.time()
        if now - self._last_cleanup < self._cleanup_interval:
            return

        cutoff = now - 600  # Remove entries not accessed in 10 minutes

        # Clean general buckets
        stale_keys = [
            key for key, bucket in self.buckets.items() if bucket.last_update < cutoff
        ]
        for key in stale_keys:
            del self.buckets[key]

        # Clean auth buckets
        stale_auth_keys = [
            key for key, bucket in self.auth_buckets.items() if bucket.last_update < cutoff
        ]
        for key in stale_auth_keys:
            del self.auth_buckets[key]

        self._last_cleanup = now

    async def dispatch(
        self,
        request: Request,
        call_next: Callable,
    ) -> Response:
        # Skip rate limiting for excluded paths
        if request.url.path in self.EXCLUDED_PATHS:
            return await call_next(request)

        # Cleanup stale entries
        self._cleanup_old_buckets()

        client_ip = self._get_client_ip(request)
        is_auth = self._is_auth_path(request.url.path)

        # Select appropriate bucket
        if is_auth:
            bucket_key = f"{client_ip}:auth"
            bucket = self.auth_buckets[bucket_key]
            limit = self.auth_requests_per_minute
        else:
            bucket_key = client_ip
            bucket = self.buckets[bucket_key]
            limit = self.requests_per_minute

        # Try to consume a token
        if not bucket.consume():
            retry_after = int(bucket.time_until_available()) + 1
            return JSONResponse(
                status_code=429,
                content={
                    "detail": "Too many requests. Please try again later.",
                    "retry_after": retry_after,
                },
                headers={
                    "Retry-After": str(retry_after),
                    "X-RateLimit-Limit": str(limit),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(int(time.time()) + retry_after),
                },
            )

        # Process the request
        response = await call_next(request)

        # Add rate limit headers
        remaining = max(0, int(bucket.tokens))
        response.headers["X-RateLimit-Limit"] = str(limit)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(int(time.time()) + 60)

        return response

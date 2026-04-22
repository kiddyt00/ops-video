"""
Rate Limiting middleware using Redis
"""
import time
from typing import Callable, Optional
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from ..core.redis import get_redis


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Rate limiting middleware using Redis

    Limits requests based on IP address or user ID
    """

    def __init__(
        self,
        app,
        requests_per_second: float = 10.0,
        burst: int = 20,
        key_prefix: str = "ratelimit",
    ):
        super().__init__(app)
        self.requests_per_second = requests_per_second
        self.burst = burst
        self.key_prefix = key_prefix
        # Minimum time between requests in milliseconds
        self.min_time = int(1000 / requests_per_second)

    async def get_client_key(self, request: Request) -> str:
        """Generate rate limit key for client"""
        # Try to get user ID from request state (set by auth middleware)
        user_id = getattr(request.state, "user_id", None)

        if user_id:
            return f"{self.key_prefix}:user:{user_id}"

        # Fallback to IP address
        client_ip = request.client.host if request.client else "unknown"
        return f"{self.key_prefix}:ip:{client_ip}"

    async def is_rate_limited(self, key: str) -> bool:
        """Check if client is rate limited using sliding window"""
        redis_client = get_redis()

        if not redis_client.is_connected:
            return False  # Skip rate limiting if Redis is not available

        now = int(time.time() * 1000)  # Current time in milliseconds
        window_start = now - 60000  # 1 minute window

        # Use Redis sorted set for sliding window
        pipe = redis_client._client.pipeline()

        # Remove old entries outside the window
        pipe.zremrangebyscore(key, 0, window_start)

        # Count requests in current window
        pipe.zcard(key)

        # Add current request
        pipe.zadd(key, {str(now): now})

        # Set expiry on the key
        pipe.expire(key, 60)

        # Execute pipeline
        results = await pipe.execute()
        request_count = results[1]

        # Check if over limit (60 requests per minute by default)
        return request_count >= self.burst

    async def dispatch(self, request: Request, call_next: Callable) -> Request:
        client_key = await self.get_client_key(request)

        if await self.is_rate_limited(client_key):
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "detail": "Too many requests",
                    "retry_after": 60,
                },
                headers={
                    "Retry-After": "60",
                    "X-RateLimit-Limit": str(self.burst),
                    "X-RateLimit-Remaining": "0",
                }
            )

        response = await call_next(request)

        # Add rate limit headers to response
        redis_client = get_redis()
        if redis_client.is_connected:
            try:
                now = int(time.time() * 1000)
                window_start = now - 60000
                count = await redis_client._client.zcount(client_key, window_start, now)
                remaining = max(0, self.burst - count)

                response.headers["X-RateLimit-Limit"] = str(self.burst)
                response.headers["X-RateLimit-Remaining"] = str(remaining)
                response.headers["X-RateLimit-Reset"] = str(int(time.time()) + 60)
            except Exception:
                pass  # Don't fail if Redis operations fail

        return response


def setup_rate_limiting(app, requests_per_minute: int = 60, burst: int = 20):
    """Setup rate limiting for FastAPI app"""
    app.add_middleware(
        RateLimitMiddleware,
        requests_per_second=requests_per_minute / 60,
        burst=burst,
    )

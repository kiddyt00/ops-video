"""
Redis client and cache utilities
"""
import json
import asyncio
from typing import Any, Optional
from redis import asyncio as aioredis
from functools import wraps
import hashlib

from ..config import settings


class RedisClient:
    """Redis client wrapper with connection management"""

    def __init__(self):
        self._client: Optional[aioredis.Redis] = None
        self._enabled = False

    async def connect(self) -> bool:
        """Connect to Redis server"""
        redis_url = getattr(settings, 'REDIS_URL', None)
        if not redis_url:
            return False

        try:
            self._client = aioredis.from_url(
                redis_url,
                encoding="utf-8",
                decode_responses=True,
                socket_connect_timeout=5,
            )
            await self._client.ping()
            self._enabled = True
            return True
        except Exception:
            self._enabled = False
            return False

    async def disconnect(self):
        """Disconnect from Redis"""
        if self._client:
            await self._client.close()
            self._client = None
            self._enabled = False

    @property
    def is_connected(self) -> bool:
        """Check if Redis is connected"""
        return self._enabled and self._client is not None

    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        if not self.is_connected:
            return None

        try:
            value = await self._client.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception:
            return None

    async def set(
        self,
        key: str,
        value: Any,
        expire: Optional[int] = None
    ) -> bool:
        """Set value in cache"""
        if not self.is_connected:
            return False

        try:
            serialized = json.dumps(value)
            if expire:
                await self._client.setex(key, expire, serialized)
            else:
                await self._client.set(key, serialized)
            return True
        except Exception:
            return False

    async def delete(self, key: str) -> bool:
        """Delete key from cache"""
        if not self.is_connected:
            return False

        try:
            await self._client.delete(key)
            return True
        except Exception:
            return False

    async def exists(self, key: str) -> bool:
        """Check if key exists"""
        if not self.is_connected:
            return False

        try:
            return await self._client.exists(key)
        except Exception:
            return False

    async def clear_pattern(self, pattern: str) -> int:
        """Clear all keys matching pattern"""
        if not self.is_connected:
            return 0

        try:
            keys = await self._client.keys(pattern)
            if keys:
                return await self._client.delete(*keys)
            return 0
        except Exception:
            return 0


def cache_result(expire: int = 300, prefix: str = "cache"):
    """
    Decorator to cache function results

    Args:
        expire: Cache expiration time in seconds
        prefix: Key prefix for namespacing
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            redis_client = get_redis()

            # Generate cache key from arguments
            key_data = f"{func.__name__}:{args}:{sorted(kwargs.items())}"
            key_hash = hashlib.md5(key_data.encode()).hexdigest()[:16]
            cache_key = f"{prefix}:{func.__module__}:{key_hash}"

            # Try to get from cache
            if redis_client.is_connected:
                cached = await redis_client.get(cache_key)
                if cached is not None:
                    return cached

            # Execute function
            result = await func(*args, **kwargs) if asyncio.iscoroutinefunction(func) else func(*args, **kwargs)

            # Store in cache
            if redis_client.is_connected:
                await redis_client.set(cache_key, result, expire=expire)

            return result

        return wrapper
    return decorator


# Global Redis client instance
_redis_client: Optional[RedisClient] = None


def get_redis() -> RedisClient:
    """Get or create Redis client instance"""
    global _redis_client
    if _redis_client is None:
        _redis_client = RedisClient()
    return _redis_client


async def init_redis() -> bool:
    """Initialize Redis connection"""
    redis_client = get_redis()
    return await redis_client.connect()


async def close_redis():
    """Close Redis connection"""
    redis_client = get_redis()
    await redis_client.disconnect()

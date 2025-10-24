"""Caching service for performance optimization"""

import json
import time
from typing import Any, Optional, Dict
from functools import wraps
import logging

logger = logging.getLogger(__name__)


class MemoryCache:
    """Simple in-memory cache with TTL support"""

    def __init__(self):
        self._cache: Dict[str, Dict[str, Any]] = {}

    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        if key not in self._cache:
            return None

        entry = self._cache[key]
        if time.time() > entry["expires"]:
            del self._cache[key]
            return None

        logger.debug(f"Cache hit for key: {key}")
        return entry["value"]

    def set(self, key: str, value: Any, ttl: int = 300) -> None:
        """Set value in cache with TTL in seconds"""
        self._cache[key] = {"value": value, "expires": time.time() + ttl}
        logger.debug(f"Cache set for key: {key}, TTL: {ttl}s")

    def delete(self, key: str) -> None:
        """Delete key from cache"""
        if key in self._cache:
            del self._cache[key]
            logger.debug(f"Cache deleted for key: {key}")

    def clear(self) -> None:
        """Clear all cache entries"""
        self._cache.clear()
        logger.debug("Cache cleared")

    def cleanup_expired(self) -> None:
        """Remove expired entries"""
        current_time = time.time()
        expired_keys = [
            key for key, entry in self._cache.items() if current_time > entry["expires"]
        ]

        for key in expired_keys:
            del self._cache[key]

        if expired_keys:
            logger.debug(f"Cleaned up {len(expired_keys)} expired cache entries")


# Global cache instance
cache = MemoryCache()


def cached(ttl: int = 300, key_prefix: str = ""):
    """Decorator for caching function results"""

    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = f"{key_prefix}{func.__name__}:{hash(str(args) + str(kwargs))}"

            # Try to get from cache
            result = cache.get(cache_key)
            if result is not None:
                return result

            # Execute function and cache result
            result = await func(*args, **kwargs)
            cache.set(cache_key, result, ttl)
            return result

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = f"{key_prefix}{func.__name__}:{hash(str(args) + str(kwargs))}"

            # Try to get from cache
            result = cache.get(cache_key)
            if result is not None:
                return result

            # Execute function and cache result
            result = func(*args, **kwargs)
            cache.set(cache_key, result, ttl)
            return result

        # Return appropriate wrapper based on function type
        import asyncio

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


# Cache management functions
def invalidate_cache_pattern(pattern: str) -> None:
    """Invalidate all cache keys matching pattern"""
    keys_to_delete = [key for key in cache._cache.keys() if pattern in key]
    for key in keys_to_delete:
        cache.delete(key)
    logger.info(
        f"Invalidated {len(keys_to_delete)} cache entries matching pattern: {pattern}"
    )


def get_cache_stats() -> Dict[str, Any]:
    """Get cache statistics"""
    current_time = time.time()
    total_entries = len(cache._cache)
    expired_entries = sum(
        1 for entry in cache._cache.values() if current_time > entry["expires"]
    )

    return {
        "total_entries": total_entries,
        "active_entries": total_entries - expired_entries,
        "expired_entries": expired_entries,
        "memory_usage_mb": len(str(cache._cache)) / (1024 * 1024),
    }

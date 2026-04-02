"""Cache manager with support for in-memory and Redis backends."""

from typing import Any, Optional, Dict, Tuple
from datetime import datetime, timedelta
import json
import hashlib
import os


class CacheManager:
    """Cache manager with TTL support for both in-memory and Redis backends."""
    
    def __init__(self, backend: str = "memory"):
        """
        Initialize cache manager.
        
        Args:
            backend: Cache backend ('memory' or 'redis')
        """
        self.backend = backend
        if backend == "redis":
            import redis.asyncio as redis
            self.redis = redis.Redis(
                host=os.getenv("REDIS_HOST", "localhost"),
                port=int(os.getenv("REDIS_PORT", "6379")),
                decode_responses=True
            )
        else:
            self._memory_cache: Dict[str, Tuple[Any, datetime]] = {}
    
    async def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found or expired
        """
        if self.backend == "redis":
            value = await self.redis.get(key)
            return json.loads(value) if value else None
        else:
            if key in self._memory_cache:
                value, expires_at = self._memory_cache[key]
                if datetime.now() < expires_at:
                    return value
                else:
                    del self._memory_cache[key]
            return None
    
    async def set(
        self,
        key: str,
        value: Any,
        ttl: int = 300
    ) -> None:
        """
        Set value in cache with TTL.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds (default: 300 = 5 minutes)
        """
        if self.backend == "redis":
            await self.redis.setex(
                key,
                ttl,
                json.dumps(value, default=str)
            )
        else:
            expires_at = datetime.now() + timedelta(seconds=ttl)
            self._memory_cache[key] = (value, expires_at)
    
    async def delete(self, key: str) -> None:
        """
        Delete key from cache.
        
        Args:
            key: Cache key to delete
        """
        if self.backend == "redis":
            await self.redis.delete(key)
        else:
            self._memory_cache.pop(key, None)
    
    async def invalidate_pattern(self, pattern: str) -> None:
        """
        Invalidate all keys matching pattern.
        
        Args:
            pattern: Pattern to match (e.g., "products:*")
        """
        if self.backend == "redis":
            keys = await self.redis.keys(pattern)
            if keys:
                await self.redis.delete(*keys)
        else:
            keys_to_delete = [
                key for key in self._memory_cache.keys()
                if self._match_pattern(key, pattern)
            ]
            for key in keys_to_delete:
                del self._memory_cache[key]
    
    @staticmethod
    def _match_pattern(key: str, pattern: str) -> bool:
        """
        Simple pattern matching for cache keys.
        
        Args:
            key: Cache key to test
            pattern: Pattern with optional wildcard (*)
            
        Returns:
            True if key matches pattern
        """
        if pattern.endswith("*"):
            prefix = pattern[:-1]
            return key.startswith(prefix)
        return key == pattern
    
    @staticmethod
    def generate_key(*args: Any, **kwargs: Any) -> str:
        """
        Generate cache key from arguments.
        
        Args:
            *args: Positional arguments
            **kwargs: Keyword arguments
            
        Returns:
            MD5 hash of arguments as cache key
        """
        key_data = f"{args}:{sorted(kwargs.items())}"
        return hashlib.md5(key_data.encode()).hexdigest()

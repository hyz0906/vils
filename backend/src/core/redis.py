"""
Redis configuration and connection
"""

import redis.asyncio as redis
from typing import Optional

from .config import settings


class RedisManager:
    """Redis connection manager"""
    
    def __init__(self):
        self.redis: Optional[redis.Redis] = None
        
    async def init_redis(self):
        """Initialize Redis connection"""
        self.redis = redis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
            max_connections=20,
            retry_on_timeout=True
        )
        
        # Test connection
        try:
            await self.redis.ping()
            print("✅ Connected to Redis")
        except Exception as e:
            print(f"❌ Failed to connect to Redis: {e}")
            raise
            
    async def close_redis(self):
        """Close Redis connection"""
        if self.redis:
            await self.redis.close()
            
    async def get(self, key: str) -> Optional[str]:
        """Get value from Redis"""
        if not self.redis:
            return None
        return await self.redis.get(key)
        
    async def set(self, key: str, value: str, expire: Optional[int] = None):
        """Set value in Redis"""
        if not self.redis:
            return
        await self.redis.set(key, value, ex=expire)
        
    async def delete(self, key: str):
        """Delete key from Redis"""
        if not self.redis:
            return
        await self.redis.delete(key)
        
    async def exists(self, key: str) -> bool:
        """Check if key exists"""
        if not self.redis:
            return False
        return bool(await self.redis.exists(key))
        
    async def expire(self, key: str, seconds: int):
        """Set expiration for key"""
        if not self.redis:
            return
        await self.redis.expire(key, seconds)
        
    async def incr(self, key: str) -> int:
        """Increment counter"""
        if not self.redis:
            return 0
        return await self.redis.incr(key)
        
    async def cache_get(self, key: str):
        """Get cached value with JSON parsing"""
        if not self.redis:
            return None
            
        import json
        value = await self.redis.get(key)
        if value:
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return value
        return None
        
    async def cache_set(self, key: str, value, expire: int = 3600):
        """Cache value with JSON serialization"""
        if not self.redis:
            return
            
        import json
        if isinstance(value, (dict, list)):
            value = json.dumps(value)
        
        await self.redis.set(key, value, ex=expire)


# Global Redis manager instance
redis_manager = RedisManager()
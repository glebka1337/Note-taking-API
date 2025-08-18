from redis.asyncio import ConnectionPool, Redis
from api.config import settings
import asyncio

_lock = asyncio.Lock()
_redis_pool: ConnectionPool | None = None

async def create_redis_pool() -> ConnectionPool:
    global _redis_pool
    async with _lock:
        if _redis_pool is None:
            _redis_pool = ConnectionPool.from_url(settings.redis_url)
    return _redis_pool
    
        
async def get_redis_pool() -> ConnectionPool:
    """
    Get the Redis connection pool

    Returns:
        ConnectionPool: The Redis connection pool
        Exampe usage:
            from redis.asyncio import Redis
            
            redis_pool = await get_redis_pool()
            async with Redis(connection_pool=redis_pool) as redis_client:
                await redis_client.set("key", "value")
        
    """
    global _redis_pool
    if _redis_pool is None:
        _redis_pool = await create_redis_pool()
    return _redis_pool
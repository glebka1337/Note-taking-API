from typing import AsyncGenerator
from redis.asyncio import Redis, ConnectionPool
from api.core.config import settings

_redis_pool: ConnectionPool | None = None

async def get_redis_pool() -> ConnectionPool:
    global _redis_pool
    if _redis_pool is None:
        _redis_pool = ConnectionPool.from_url(
            settings.redis_url,
            max_connections=20,  
            decode_responses=True
        )
    return _redis_pool


async def get_redis() -> Redis:
    return await Redis(connection_pool= await get_redis_pool())


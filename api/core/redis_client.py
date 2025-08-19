from typing import AsyncGenerator
from redis.asyncio import Redis, ConnectionPool
from api.config import settings
from contextlib import asynccontextmanager
from fastapi import Depends

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

@asynccontextmanager
async def get_redis() -> AsyncGenerator[Redis, None]:
    pool = await get_redis_pool()
    client = Redis(connection_pool=pool)
    try:
        yield client
    finally:
        await client.close()


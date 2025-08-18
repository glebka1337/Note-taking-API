from fastapi import HTTPException, status
from redis.asyncio import ConnectionPool, Redis
from uuid import uuid4
import jwt
from typing import Annotated
from datetime import datetime, timedelta, timezone
from api.config import settings 

def create_token(
    user_id: Annotated[int, "User ID to include in token"],
    expires_delta: Annotated[timedelta, "Time delta for expiration"] = timedelta(minutes=15)
) -> tuple[str, dict[str, int | str]]:
    """
    Create a JWT token with user ID and expiration.
    Automatically converts timedelta to seconds since epoch

    Args:
        user_id (Annotated[int, &quot;User ID to include in token&quot;])
        db (Annotated[AsyncSession, &quot;Database session&quot;])
        expires_delta (Annotated[timedelta, &quot;Time delta for expiration&quot;], optional)

    Returns:
        tuple: A tuple containing the token and payload
        Example payload:
        {
            'jti': str(uuid4()),
            'iat': int(datetime.now(timezone.utc).timestamp()),
            'exp': int(expires_at.timestamp()),
            'user_id': user_id
        }
    """
    
    expires_at = datetime.now(timezone.utc) + expires_delta
    payload = {
        'jti': str(uuid4()), # for unique token
        'iat': int(datetime.now(timezone.utc).timestamp()),
        'exp': int(expires_at.timestamp()),
        'user_id': str(user_id)
    }
    token = jwt.encode(
        payload,
        settings.secret_key,
        algorithm=settings.algorithm
    )
    return token, payload

async def validate_refresh_token(
    token: Annotated[str, "Token to validate"],    
    redis_client: Annotated[Redis, "Redis client"]
) -> Annotated[dict, "Payload of the token"]:
    """
    Validate a refresh token by checking if it exists in Redis and with jwt.decode
    """
    
    try:
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=settings.algorithm
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials"
        )
    
    # check passed, check redis
    
    redis_token = await redis_client.get(f"token:{payload['user_id']}:{payload['jti']}")
    if redis_token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials"
        )
    
    return payload

async def add_refresh_token_to_redis(
    redis_client: Redis,
    user_id: int,
    jti: str,
    expires_delta: timedelta
):
    """
    Adds a refresh token's JTI to Redis with an expiration time.
    """
    await redis_client.set(
        f"token:{user_id}:{jti}", # Use a unique key
        "valid",                  # Store a simple value to mark it as valid
        ex=int(expires_delta.total_seconds()) # Set the expiration time
    )

async def remove_refresh_token_from_redis(
    redis_client: Redis,
    user_id: int,
    jti: str
):
    """
    Removes a refresh token's JTI from Redis, invalidating it.
    """
    await redis_client.delete(f"token:{user_id}:{jti}")
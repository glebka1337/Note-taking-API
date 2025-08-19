from datetime import timedelta
from fastapi import APIRouter, HTTPException, Header, status, Depends
from api.auth.schemas import UserCreate, UserLogin, UserOut
from api.auth.services.auth_service import create_new_user, get_current_user, login_user
from api.core.db import get_session
from sqlalchemy.ext.asyncio import AsyncSession
from api.auth.services.jwt_service import (
    create_token,
    remove_refresh_token_from_redis,
    validate_refresh_token,
    add_refresh_token_to_redis,
)
from api.core.config import settings
from api.core.redis_client import get_redis
from redis.asyncio import Redis

router = APIRouter(
    
    prefix="/auth",
    tags=["auth"],
)


@router.post("/register", response_model=UserOut)
async def register(
    user_in: UserCreate,
    db : AsyncSession = Depends(get_session)
):
    return await create_new_user(db, user_in)

@router.post("/login")
async def login(
    user_in: UserLogin,
    db : AsyncSession = Depends(get_session),
    redis_client = Depends(get_redis)
):
    user_in_db: UserOut = await login_user(
        user_in,
        db
    )
    
    # ? Create tokens
    
    refresh_token, refresh_payload = create_token(
        user_id=user_in_db.id,
        expires_delta=timedelta(days=30)
    )
    
    access_token, access_payload = create_token(
        user_id=user_in_db.id,
        expires_delta=timedelta(minutes=15)
    )
    
    # ? Add refresh token to redis for later logout or refresh
    
    await add_refresh_token_to_redis(
        redis_client=redis_client,
        user_id=user_in_db.id,
        jti=refresh_payload["jti"],
        expires_delta=timedelta(days=30)
    )
    
    return dict(
        access_token=access_token,
        access_token_expires=access_payload["exp"],
        refresh_token=refresh_token,
        refresh_token_expires=refresh_payload["exp"]
    )
    
@router.post("/logout")    
async def logout(
    redis_client = Depends(get_redis), 
    refresh_token: str = Header(..., alias="Authorization")
):
    if not refresh_token.startswith("Bearer "):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid token format")

    token = refresh_token.split(" ")[1]
    try:
        payload = await validate_refresh_token(token, redis_client)
    except HTTPException:
        return {"message": "Token already invalid"}

    await remove_refresh_token_from_redis(redis_client, payload['user_id'], payload['jti'])
    return {"message": "Logged out"}

@router.post("/refresh")
async def refresh_access_token(
    refresh_token: str = Header(..., alias="Authorization"),
    redis_client: Redis = Depends(get_redis)
):
    payload = await validate_refresh_token(refresh_token, redis_client)
    new_access, _ = create_token(payload['user_id'], timedelta(minutes=15))
    return {"access_token": new_access}

@router.get(
    '/protected',
)
async def protected(
    user: UserOut = Depends(get_current_user)
):
    return {"message": "Protected route"}
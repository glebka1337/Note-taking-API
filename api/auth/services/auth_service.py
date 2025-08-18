"""
Here will be auth service
"""
from fastapi import Depends, HTTPException, Header, status
from api.auth.schemas import UserCreate, UserLogin, UserOut
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from api.auth.security import get_password_hash, verify_password
from api.db import get_session
from api.models import User
from redis.asyncio import Redis
from typing import Annotated
from api.auth.services.jwt_service import validate_refresh_token
from api.redis_client import get_redis

async def create_new_user(
    db: AsyncSession,
    user_in: UserCreate
) -> User:
    """
    Create new user

    Args:
        db (AsyncSession): connect to database
        user_in (UserCreate): user to create

    Raises:
        HTTPException: _description_
        HTTPException: _description_

    Returns:
        User: _description_
    """
    user_in_db = await db.execute(
        select(User).where(
            or_(
                User.email == user_in.email,
                User.username == user_in.username
            )
        )
    )
    if user_in_db := user_in_db.scalar_one_or_none():
        if user_in_db.email == user_in.email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        if user_in_db.username == user_in.username:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already registered"
            )
    user = User(**user_in.model_dump())
    user.hashed_password = get_password_hash(user_in.password)
    
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user

async def login_user(
    user_login: UserLogin,
    db: AsyncSession
) -> UserOut:
    """
    Login user

    Args:
        user_login (UserLogin): user to login
        db (AsyncSession): connect to database

    Raises:
        HTTPException: if email or password is incorrect

    Returns:
        UserOut: pydantic model of user
    """    
    user_in_db = await db.execute(
        select(User).where(
            User.email == user_login.email
        )
    )
    
    user = user_in_db.scalar_one_or_none()
    detail="Incorrect email or password"
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail
        )
    if not verify_password(
        plain_password=user_login.password,
        hashed_password=user.hashed_password
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail
        )
    return UserOut(**user.model_dump())

async def get_current_user(
    refresh_token: Annotated[str, "Token to validate"] = Header(..., alias="Authorization"),
    redis_client: Annotated[Redis, "Redis client"] = Depends(get_redis),
    db: AsyncSession = Depends(get_session)
) -> UserOut:
    """
    Returns current user by refresh token

    Args:
        refresh_token (Annotated[str, &quot;Token to validate&quot;]): jwt token 
        redis_client (Annotated[Redis, &quot;Redis client&quot;]): redis client

    Returns:
        UserOut: pydantic model of user
    """
    
    # Validate token 
    
    if not refresh_token.startswith("Bearer "):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid token format, use 'Bearer your_token' instead")
    
    payload = await validate_refresh_token(
        refresh_token=refresh_token,
        redis_client=redis_client
    )
    
    # If token is valid, search for user profile in redis
    
    user_in_redis = await redis_client.get(f"user:{payload['user_id']}")
    
    # If user profile is in redis, return it
    if user_in_redis:
       return UserOut.model_validate_json(user_in_redis)
   
    # if user not found in redis, search for user in database
    
    user_in_db = await db.execute(
        select(User).where(
            User.id == int(payload["user_id"])
        )
    )
    
    # if user not found in database, raise error
    
    if user_in_db := user_in_db.scalar_one_or_none() == None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No such user"
        )
    
    # if user found in database, save it in redis and return it
    
    await redis_client.set(
        name=f"user:{payload['user_id']}",
        value=user_in_db.model_dump_json()
    )
    
    
    return UserOut.model_validate(user_in_db)